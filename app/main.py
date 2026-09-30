#!/usr/bin/env python3
"""VTK review history explorer.

Views:
  Rules         draft review rules with evidence, counter-evidence, and deprecation flags;
                accept, edit, or reject each (saved to rules/curated.json)
  Deprecations  every API VTK has deprecated, with reason and the MRs that deprecated and removed it
  Trends        emerging, past, and fading terms, code areas, and themes, with per-quarter charts
  Search        review threads, MRs, issues, and forum posts (keyword and meaning)

Usage:
  python app/main.py --port 8080
"""

import sys
from pathlib import Path

import plotly.graph_objects as go
from trame.app import get_server
from trame.ui.vuetify3 import SinglePageLayout
from trame.widgets import html, plotly
from trame.widgets import vuetify3 as v

sys.path.insert(0, str(Path(__file__).resolve().parent))
from data import DECISIONS, Store  # noqa: E402

server = get_server(client_type="vue3")
state, ctrl = server.state, server.controller
store = Store()

MONO = "font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 0.85em"
DECISION_COLOR = {"accepted": "green", "edited": "blue", "rejected": "red", "undecided": "grey"}
RULE_HEADERS = [{"title": "Id", "key": "id", "width": 70}, {"title": "Rule", "key": "rule"},
                {"title": "Topic", "key": "topic", "width": 150}, {"title": "MRs", "key": "mrs", "width": 70},
                {"title": "Last seen", "key": "last", "width": 110}, {"title": "Flags", "key": "flags", "width": 110},
                {"title": "Decision", "key": "decision", "width": 110}]
DEP_HEADERS = [{"title": "API", "key": "api"}, {"title": "Version", "key": "version", "width": 90},
               {"title": "Outcome", "key": "outcome", "width": 110},
               {"title": "Deprecated", "key": "deprecated_mr", "width": 150},
               {"title": "Removed", "key": "removed_mr", "width": 150}, {"title": "Reason", "key": "reason"}]
TREND_HEADERS = [{"title": "Term, code area, or theme", "key": "name"}, {"title": "Ratio", "key": "ratio", "width": 80},
                 {"title": "Docs", "key": "docs", "width": 80}, {"title": "First seen", "key": "first_seen", "width": 100},
                 {"title": "Peak", "key": "peak", "width": 90}]
SEARCH_HEADERS = [{"title": "Kind", "key": "kind", "width": 80}, {"title": "Ref", "key": "ref", "width": 110},
                  {"title": "Date", "key": "date", "width": 110}, {"title": "Author", "key": "author", "width": 140},
                  {"title": "Title and excerpt", "key": "title"}]

state.update({
    "tab": "rules",
    "rule_rows": [], "rule_search": "", "rule_topic": None, "rule_decision": None, "rule_flag": None,
    "topics": sorted({r["topic"] for r in store.rules}), "decisions": ["undecided", *DECISIONS],
    "rule_key": None, "rule": None, "rule_text": "", "rule_note": "", "rule_counts": "",
    "dep_rows": store.deprecation_rows(), "dep_search": "", "dep_outcome": None,
    "trend_what": "terms", "trend_source": "mr", "trend_kind": "emerging", "trend_common": False,
    "trend_rows": [], "trend_name": None, "trend_row": None,
    "q": "", "q_kind": None, "q_since": "", "q_until": "", "search_rows": [], "searching": False, "search_error": "",
})


def refresh_rules():
    rows = store.rule_rows()
    counts = {d: sum(r["decision"] == d for r in rows) for d in state.decisions}
    state.rule_counts = " · ".join(f"{n} {d}" for d, n in counts.items())
    if state.rule_topic:
        rows = [r for r in rows if r["topic"] == state.rule_topic]
    if state.rule_decision:
        rows = [r for r in rows if r["decision"] == state.rule_decision]
    if state.rule_flag == "deprecated API":
        rows = [r for r in rows if r["deprecated"]]
    elif state.rule_flag == "mixed evidence":
        rows = [r for r in rows if r["mixed"]]
    state.rule_rows = rows


@state.change("rule_topic", "rule_decision", "rule_flag")
def on_rule_filters(**_):
    refresh_rules()


@state.change("rule_key")
def on_rule_key(rule_key, **_):
    state.rule = store.rule_detail(rule_key) if rule_key else None
    state.rule_text = state.rule["rule"] if state.rule else ""
    state.rule_note = state.rule["note"] if state.rule else ""


def decide(decision):
    if state.rule_key:
        store.decide(state.rule_key, decision, state.rule_text, state.rule_note)
        on_rule_key(state.rule_key)
        refresh_rules()


ctrl.accept = lambda: decide("accepted")
ctrl.reject = lambda: decide("rejected")
ctrl.clear = lambda: decide("undecided")


@state.change("dep_outcome")
def on_dep_outcome(dep_outcome, **_):
    rows = store.deprecation_rows()
    state.dep_rows = [r for r in rows if r["outcome"] == dep_outcome] if dep_outcome else rows


TREND = {"quarters": [], "docs": [], "rows": {}}


@state.change("trend_what", "trend_source", "trend_kind", "trend_common")
def on_trend_filters(trend_what, trend_source, trend_kind, trend_common, **_):
    rows, quarters, docs = store.trend_rows(trend_what, trend_source, trend_kind, trend_common and trend_what == "terms")
    TREND.update(quarters=quarters, docs=docs, rows={r["name"]: r for r in rows})
    state.trend_rows = [{k: r[k] for k in ("name", "ratio", "docs", "first_seen", "peak")} for r in rows]
    state.trend_name = rows[0]["name"] if rows else None


@state.change("trend_name")
def on_trend_name(trend_name, **_):
    row = TREND["rows"].get(trend_name)
    if not row:
        state.trend_row = None
        ctrl.trend_chart_update(go.Figure())
        return
    state.trend_row = {"name": row["name"], "description": row.get("description", ""), "examples": [
        dict(e, url=store.example_url(e["source"], e["id"])) for e in row["examples"]]}
    share = [100 * c / n if n else 0 for c, n in zip(row["series"], TREND["docs"])]
    label = "merge requests" if state.trend_source == "mr" else "forum topics"
    fig = go.Figure(go.Scatter(x=TREND["quarters"][:len(share)], y=share, mode="lines+markers",
                               line={"color": "#1f6feb", "width": 2}, marker={"size": 4},
                               hovertemplate="%{x}: %{y:.1f}%<extra></extra>"))
    fig.update_layout(margin={"l": 50, "r": 20, "t": 30, "b": 40}, height=280,
                      title={"text": f"Share of {label} mentioning {row['name']}", "font": {"size": 14}},
                      yaxis={"title": "% of documents", "rangemode": "tozero", "gridcolor": "#e5e7eb"},
                      xaxis={"tickangle": -45, "nticks": 16}, plot_bgcolor="white", paper_bgcolor="white")
    ctrl.trend_chart_update(fig)


def run_search(q=None):
    state.q = q if q is not None else state.q
    if not (state.q or "").strip():
        return
    state.searching, state.search_error = True, ""
    state.flush()
    try:
        state.search_rows = store.search(state.q, state.q_kind, state.q_since, state.q_until)
    except OSError as e:
        state.search_error = f"Search needs the DGX Spark for meaning-based matching and could not reach it: {e}"
        state.search_rows = []
    finally:
        state.searching = False


ctrl.search = run_search


def link(text, url):
    return html.A(text, href=(url,), target="_blank", classes="text-decoration-none")


def rules_view():
    with v.VRow(dense=True):
        with v.VCol(cols=7):
            with v.VRow(dense=True, classes="mb-2"):
                v.VTextField(v_model=("rule_search",), label="Filter rules", density="compact", hide_details=True,
                             prepend_inner_icon="mdi-magnify", clearable=True)
                v.VSelect(v_model=("rule_topic",), items=("topics",), label="Topic", density="compact",
                          hide_details=True, clearable=True, style="max-width: 200px")
                v.VSelect(v_model=("rule_decision",), items=("decisions",), label="Decision", density="compact",
                          hide_details=True, clearable=True, style="max-width: 160px")
                v.VSelect(v_model=("rule_flag",), items=(["deprecated API", "mixed evidence"],), label="Flag",
                          density="compact", hide_details=True, clearable=True, style="max-width: 180px")
            html.Div("{{ rule_counts }}", classes="text-caption text-medium-emphasis mb-1")
            with v.VDataTable(headers=("rule_headers", RULE_HEADERS), items=("rule_rows",), search=("rule_search",),
                              density="compact", items_per_page=25, hover=True, height="calc(100vh - 250px)",
                              fixed_header=True):
                with v.Template(raw_attrs=['v-slot:item.id="{ item }"']):
                    html.A("{{ item.id }}", click="rule_key = item.key", style="cursor: pointer",
                           classes=("item.key === rule_key ? 'font-weight-bold text-primary' : 'text-primary'",))
                with v.Template(raw_attrs=['v-slot:item.rule="{ item }"']):
                    html.Div("{{ item.rule }}", click="rule_key = item.key", style="cursor: pointer",
                             classes=("item.key === rule_key ? 'font-weight-bold' : ''",))
                with v.Template(raw_attrs=['v-slot:item.flags="{ item }"']):
                    v.VChip("deprecated API", v_if="item.deprecated", size="x-small", color="orange", classes="mr-1")
                    v.VChip("mixed", v_if="item.mixed", size="x-small", color="purple")
                with v.Template(raw_attrs=['v-slot:item.decision="{ item }"']):
                    v.VChip("{{ item.decision }}", size="small", variant="tonal",
                            color=(f"({DECISION_COLOR})[item.decision]",))
        with v.VCol(cols=5):
            rule_detail()


def evidence_list(field, title, color=None):
    with html.Div(v_if=f"rule.{field}.length", classes="mt-3"):
        html.Div(title, classes=f"text-subtitle-2 {color or ''}")
        with html.Div(v_for=f"e in rule.{field}", key="e.mr + e.date", classes="text-body-2 my-2"):
            link("!{{ e.mr }}", "e.url")
            html.Span(" {{ e.reviewer }}, {{ e.date }}", classes="text-medium-emphasis")
            html.Div("{{ e.text }}", classes="pl-3", style="border-left: 3px solid #d0d7de")


def rule_detail():
    with v.VCard(v_if="rule", variant="outlined", classes="pa-3", style="height: calc(100vh - 140px); overflow-y: auto"):
        with html.Div(classes="d-flex align-center mb-2"):
            html.Span("{{ rule.id }}", classes="text-h6 mr-2")
            v.VChip("{{ rule.topic }}", size="small", classes="mr-2")
            v.VChip("{{ rule.decision }}", size="small", variant="tonal", color=(f"({DECISION_COLOR})[rule.decision]",))
            v.VSpacer()
            html.Span("{{ rule.decided_by ? rule.decided_by + ', ' + rule.decided_at : '' }}",
                      classes="text-caption text-medium-emphasis")
        v.VTextarea(v_model=("rule_text",), label="Rule (edit before accepting to record an edited rule)",
                    auto_grow=True, rows=2, density="compact", hide_details=True)
        html.Div("Draft: {{ rule.draft }}", v_if="rule_text !== rule.draft",
                 classes="text-caption text-medium-emphasis mt-1")
        v.VTextField(v_model=("rule_note",), label="Note (why, or what should change)", density="compact",
                     hide_details=True, classes="mt-2")
        with html.Div(classes="d-flex mt-2"):
            v.VBtn("Accept", color="green", variant="flat", size="small", click=ctrl.accept, classes="mr-2",
                   prepend_icon="mdi-check")
            v.VBtn("Reject", color="red", variant="flat", size="small", click=ctrl.reject, classes="mr-2",
                   prepend_icon="mdi-close")
            v.VBtn("Clear decision", variant="text", size="small", click=ctrl.clear)
        html.Div("Rationale: {{ rule.rationale }}", v_if="rule.rationale", classes="text-body-2 mt-3")
        html.Div("Scope: {{ rule.scope }}", classes="text-body-2")
        html.Div("Support: {{ rule.support }}", classes="text-body-2")
        html.Div("Reviewers: {{ rule.reviewers }}", classes="text-body-2")
        with html.Div(v_if="rule.conflicts.length", classes="mt-3"):
            html.Div("Names APIs VTK has since deprecated or removed", classes="text-subtitle-2 text-orange-darken-3")
            with html.Div(v_for="d in rule.conflicts", key="d.api + d.version", classes="text-body-2 my-1"):
                html.Span("{{ d.api }}", style=MONO)
                html.Span(" deprecated in {{ d.version }} ({{ d.deprecated_on }}")
                with html.Span(v_if="d.deprecated_mr"):
                    html.Span(", ")
                    link("!{{ d.deprecated_mr }}", "d.deprecated_url")
                html.Span(")")
                html.Span(": {{ d.reason }}", v_if="d.reason")
        evidence_list("examples", "Supporting comments")
        evidence_list("counter", "Counter-evidence", "text-purple")
    with v.VCard(v_else=True, variant="outlined", classes="pa-6 text-medium-emphasis"):
        html.Div("Select a rule to see its evidence and record a decision.")


def deprecations_view():
    with v.VRow(dense=True, classes="mb-2"):
        v.VTextField(v_model=("dep_search",), label="Search APIs, reasons, versions", density="compact",
                     hide_details=True, prepend_inner_icon="mdi-magnify", clearable=True)
        v.VSelect(v_model=("dep_outcome",), items=(["present", "removed", "undeprecated"],), label="Status",
                  density="compact", hide_details=True, clearable=True, style="max-width: 200px")
    html.Div("{{ dep_rows.length }} deprecated APIs. 'present' means still deprecated in the current tree.",
             classes="text-caption text-medium-emphasis mb-1")
    with v.VDataTable(headers=("dep_headers", DEP_HEADERS), items=("dep_rows",), search=("dep_search",),
                      density="compact", items_per_page=50, hover=True, height="calc(100vh - 230px)",
                      fixed_header=True):
        with v.Template(raw_attrs=['v-slot:item.api="{ item }"']):
            html.Span("{{ item.api }}", title=("item.declaration",), style=MONO)
        with v.Template(raw_attrs=['v-slot:item.deprecated_mr="{ item }"']):
            html.Span("{{ item.deprecated_on }} ")
            with html.Span(v_if="item.deprecated_mr"):
                link("!{{ item.deprecated_mr }}", "item.deprecated_url")
        with v.Template(raw_attrs=['v-slot:item.removed_mr="{ item }"']):
            html.Span("{{ item.removed_on }} ")
            with html.Span(v_if="item.removed_mr"):
                link("!{{ item.removed_mr }}", "item.removed_url")


def trends_view():
    with v.VRow(dense=True, classes="mb-2"):
        for model, choices in (("trend_what", [("Terms and code areas", "terms"), ("Themes", "themes")]),
                               ("trend_source", [("Merge requests", "mr"), ("Forum", "discourse")]),
                               ("trend_kind", [("Emerging", "emerging"), ("Past bursts", "past"), ("Fading", "fading")])):
            with v.VBtnToggle(v_model=(model,), mandatory=True, density="compact", color="primary", variant="outlined",
                              classes="mr-3 mb-1"):
                for label, value in choices:
                    v.VBtn(label, value=value)
        v.VCheckbox(v_model=("trend_common",), label="Common English words", density="compact", hide_details=True,
                    v_if="trend_what === 'terms'")
    with v.VRow(dense=True):
        with v.VCol(cols=5):
            with v.VDataTable(headers=("trend_headers", TREND_HEADERS), items=("trend_rows",), density="compact",
                              items_per_page=40, hover=True, height="calc(100vh - 220px)", fixed_header=True):
                with v.Template(raw_attrs=['v-slot:item.name="{ item }"']):
                    html.Div("{{ item.name }}", click="trend_name = item.name", style="cursor: pointer",
                             classes=("item.name === trend_name ? 'font-weight-bold text-primary' : 'text-primary'",))
        with v.VCol(cols=7):
            with v.VCard(variant="outlined", classes="pa-2"):
                figure = plotly.Figure(display_logo=False, display_mode_bar=False, style="height: 290px")
                ctrl.trend_chart_update = figure.update
            with v.VCard(v_if="trend_row", variant="outlined", classes="pa-3 mt-2"):
                html.Div("{{ trend_row.description }}", v_if="trend_row.description", classes="text-body-2 mb-2")
                html.Div("Examples across the record", classes="text-subtitle-2")
                with html.Div(v_for="e in trend_row.examples", key="e.id", classes="text-body-2 my-1"):
                    html.Span("{{ e.q }} ", classes="text-medium-emphasis")
                    link("{{ e.source === 'mr' ? '!' + e.id : 'topic ' + e.id }}", "e.url")
                    html.Span(" {{ e.title }}")


def search_view():
    with v.VRow(dense=True, classes="mb-2"):
        v.VTextField(v_model=("q",), label="Ask about VTK history: an API, a design question, a bug",
                     density="compact", hide_details=True, prepend_inner_icon="mdi-magnify", clearable=True,
                     __events=[("keyup_enter", "keyup.enter")], keyup_enter=(ctrl.search, "[$event.target.value]"))
        v.VSelect(v_model=("q_kind",), items=(["thread", "mr", "issue", "post"],), label="Kind", density="compact",
                  hide_details=True, clearable=True, style="max-width: 130px")
        v.VTextField(v_model=("q_since",), label="Since (YYYY-MM-DD)", density="compact", hide_details=True,
                     style="max-width: 170px")
        v.VTextField(v_model=("q_until",), label="Before (YYYY-MM-DD)", density="compact", hide_details=True,
                     style="max-width: 170px")
        v.VBtn("Search", color="primary", click=(ctrl.search, "[q]"), loading=("searching",))
    v.VAlert("{{ search_error }}", v_if="search_error", type="warning", density="compact", classes="mb-2")
    with v.VDataTable(headers=("search_headers", SEARCH_HEADERS), items=("search_rows",), density="compact",
                      items_per_page=25, height="calc(100vh - 220px)", fixed_header=True):
        with v.Template(raw_attrs=['v-slot:item.ref="{ item }"']):
            link("{{ item.ref }}", "item.url")
        with v.Template(raw_attrs=['v-slot:item.title="{ item }"']):
            html.Div("{{ item.title }}", classes="font-weight-medium")
            html.Div("{{ item.path }}", v_if="item.path", classes="text-caption text-medium-emphasis")
            html.Div("{{ item.snippet }}", classes="text-body-2 text-medium-emphasis mb-1")


with SinglePageLayout(server) as layout:
    layout.title.set_text("VTK review history")
    with layout.toolbar:
        v.VSpacer()
        with v.VTabs(v_model=("tab",), density="compact"):
            v.VTab("Rules", value="rules")
            v.VTab("Deprecations", value="deprecations")
            v.VTab("Trends", value="trends")
            v.VTab("Search", value="search")
    with layout.content:
        with v.VContainer(fluid=True, classes="pa-3"):
            with v.VWindow(v_model=("tab",)):
                with v.VWindowItem(value="rules"):
                    rules_view()
                with v.VWindowItem(value="deprecations"):
                    deprecations_view()
                with v.VWindowItem(value="trends"):
                    trends_view()
                with v.VWindowItem(value="search"):
                    search_view()

refresh_rules()
on_trend_filters(state.trend_what, state.trend_source, state.trend_kind, state.trend_common)

if __name__ == "__main__":
    server.start()
