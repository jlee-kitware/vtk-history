#!/usr/bin/env python3
"""VTK review history explorer (trame v4, React client with MUI).

Views:
  Review        an MR revision's diff with the agent's comments and the reviewers' comments on the lines
                they concern; rate each agent comment valid, wrong, or unsure (saved to ratings/ratings.jsonl);
                run the agent on any revision
  Rules         review rules ranked by confidence (reviewers, follow-through, objections, consistency,
                deprecated APIs), with the comments behind each;
                accept, edit, or reject each (saved to rules/curated.json)
  Deprecations  every API VTK has deprecated, with reason and the MRs that deprecated and removed it
  Trends        emerging, past, and fading terms, code areas, themes, and GitLab labels, with per-quarter charts
  Labels        area label suggestions for unlabeled issues: what a backfill would add, how accurate the
                suggestions were on issues maintainers already labeled, and a lookup for one issue
  Search        review threads, MRs, issues, forum posts, docs, release notes, and class docs, filterable by
                GitLab label

Usage:
  python app/main.py --server --port 8080
"""

import asyncio
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from trame.app import asynchronous, get_server
from trame.ui.mui import MuiLayout
from trame.widgets import html, mui, react

sys.path.insert(0, str(Path(__file__).resolve().parent))
from charts import line_svg  # noqa: E402
import topics  # noqa: E402
from data import DECISIONS, Store  # noqa: E402
from review_data import Reviews, comment_key  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "people"))
from expertise import Expertise, reason  # noqa: E402
from briefing import Briefing  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agent"))
import tool_checks  # noqa: E402

B, C = react.Bind, react.Callback
server = get_server(client_type="react")
state, ctrl = server.state, server.controller
store = Store()
reviews = Reviews()
expertise = Expertise()

CANVAS, SURFACE, INK, MUTED, LINE = "#F3F5F8", "#FFFFFF", "#172033", "#5A6474", "#DCE1E8"
ACCENT, ACCENT_TINT, REVIEWER = "#0A7C8C", "#E3F2F4", "#8A94A6"
SANS = "'IBM Plex Sans', system-ui, -apple-system, 'Segoe UI', sans-serif"
MONO = "'IBM Plex Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
FONTS = ("https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500"
         "&family=IBM+Plex+Sans:wght@400;500;600&display=swap")
THEME = {
    "palette": {"mode": "light", "primary": {"main": ACCENT}, "secondary": {"main": "#6E56CF"},
                "success": {"main": "#1F883D"}, "error": {"main": "#C4314B"}, "warning": {"main": "#B35900"},
                "background": {"default": CANVAS, "paper": SURFACE}, "text": {"primary": INK, "secondary": MUTED},
                "divider": LINE},
    "typography": {"fontFamily": SANS, "fontSize": 13, "button": {"textTransform": "none", "fontWeight": 500}},
    "shape": {"borderRadius": 6},
    "components": {
        "MuiButton": {"defaultProps": {"disableElevation": True}},
        "MuiButtonGroup": {"defaultProps": {"disableElevation": True}},
        "MuiTableCell": {"styleOverrides": {
            "root": {"borderColor": LINE, "fontSize": "0.84rem"},
            "head": {"backgroundColor": "#F7F9FB", "color": MUTED, "fontWeight": 600, "fontSize": "0.78rem"}}},
        "MuiTableRow": {"styleOverrides": {"root": {"&.Mui-selected, &.Mui-selected:hover": {
            "backgroundColor": ACCENT_TINT}}}},
        "MuiPaper": {"styleOverrides": {"outlined": {"borderColor": LINE}}},
        "MuiChip": {"styleOverrides": {"root": {"borderRadius": "6px", "fontWeight": 500},
                                       "sizeSmall": {"height": "22px"}}},
        "MuiOutlinedInput": {"styleOverrides": {"root": {"backgroundColor": SURFACE},
                                                "notchedOutline": {"borderColor": LINE}}},
        "MuiListItemButton": {"styleOverrides": {"root": {"borderRadius": "6px", "&.Mui-selected": {
            "backgroundColor": ACCENT_TINT}}}},
    },
}
LEVEL_FG = "({high: '#1A7F37', documented: '#0B5C75', medium: '#8A5A00', low: '#B42339'})"
LEVEL_BG = "({high: '#E6F4EA', documented: '#E1F0F6', medium: '#FFF3D6', low: '#FCE8EC'})"
TONE = "({good: '#1A7F37', bad: '#B42339', neutral: '" + MUTED + "'})"
DECISION_COLOR = {"accepted": "success", "edited": "primary", "rejected": "error", "undecided": "default"}
TABS = [
    ("briefing", "Briefing", "What VTK's history says about one merge request: related work, reviewers, conventions, "
                             "deprecated APIs, and recent changes to its files"),
    ("review", "Review", "A merge request's diff with the real reviewers' comments and the review agent's comments; "
                         "rate the agent's comments"),
    ("rules", "Rules", "Review conventions distilled from past reviewer comments, with how often authors act on "
                       "them; accept, edit or reject each"),
    ("deprecations", "Deprecations", "VTK APIs that were deprecated, in which version, and whether they were removed"),
    ("trends", "Trends", "Terms, code areas, themes and GitLab labels whose share of merge requests, issues or "
                         "forum topics rose or fell"),
    ("labels", "Labels", "Suggested area labels for issues that have none, and how accurate the suggestions were on "
                         "issues maintainers already labeled"),
    ("search", "Search", "Search merge requests, issues, review threads, forum topics, blog posts and docs"),
]
MAX_ROWS = 400


def options(values):
    return [{"title": str(x), "value": x} for x in values]


state.update({
    "tab": "briefing",
    "rule_rows": [], "rule_search": "", "rule_topic": "", "rule_decision": "", "rule_level": "",
    "topics": options(sorted({r["topic"] for r in store.rules})),
    "decisions": options(["undecided", *DECISIONS]),
    "levels": [{"title": "High", "value": "high"}, {"title": "Medium", "value": "medium"},
               {"title": "Low", "value": "low"}, {"title": "Conflicts with the guide or tools", "value": "conflict"},
               {"title": "Enforced by a tool", "value": "automated"},
               {"title": "Could be automated", "value": "automatable"},
               {"title": "Documented only", "value": "documented"}],
    "rule_key": None, "rule": None, "rule_text": "", "rule_note": "", "rule_counts": "", "rule_shown": "",
    "dep_rows": [], "dep_search": "", "dep_outcome": "", "dep_shown": "",
    "outcomes": options(["present", "removed", "undeprecated"]),
    "trend_what": "terms", "trend_source": "mr", "trend_kind": "emerging", "trend_common": False,
    "trend_rows": [], "trend_name": None, "trend_row": None, "trend_chart": "", "trend_title": "",
    "q": "", "q_kind": "", "q_since": "", "q_until": "", "q_label": "", "search_rows": [], "searching": False,
    "search_error": "", "label_options": store.label_options(),
    "kinds": options(["thread", "mr", "issue", "post", "blog", "doc", "note", "class"]),
    "topic": None, "topic_error": "", "search_more": [],
})


def text(expr):
    return B(expr)


def link(text_expr, url_expr):
    return html.A([B(text_expr)], href=B(url_expr), target="_blank",
                  style={"color": ACCENT, "textDecoration": "none", "fontWeight": 500})


def tipped(text, placement="top"):
    return mui.Tooltip(title=text, arrow=True, enter_delay=400, placement=placement)


def select(label, key, items, width=200, numeric=False, empty=True, tip=None):
    """Native select (MUI cannot map a dynamic option list onto its own menu)."""
    if tip:
        with tipped(tip):
            with html.Span(style={"display": "inline-flex"}):
                return select(label, key, items, width, numeric, empty)
    value = f"{key} === null || {key} === undefined ? '' : {key}"
    assign = f"{key} = $event.target.value === '' ? null : Number($event.target.value)" if numeric \
        else f"{key} = $event.target.value"
    with mui.TextField(select=True, label=label, size="small", value=B(value), on_change=C(assign),
                       style={"minWidth": f"{width}px", "maxWidth": f"{width}px"},
                       slot_props={"select": {"native": True}, "inputLabel": {"shrink": True}}):
        if empty:
            html.Option("", value="")
        with react.For(items=items, name="o"):
            html.Option([B("o.title")], value=B("o.value"), key=B("String(o.value)"))


def field(label, key, width=None, on_enter=None, tip=None, **kwargs):
    if tip:
        with tipped(tip):
            with html.Span(style={"display": "flex", "flex": "1" if not width else "none"}):
                return field(label, key, width, on_enter, **kwargs)
    style = {"minWidth": f"{width}px", "maxWidth": f"{width}px"} if width else {"flex": "1", "minWidth": "220px"}
    extra = {"on_key_up": C(on_enter, "[$event.key, $event.target.value]")} if on_enter else {}
    return mui.TextField(label=label, size="small", value=B(key), on_change=C(f"{key} = $event.target.value"),
                         style=style, **extra, **kwargs)


def caption(children, **style):
    return html.Div(children, style={"fontSize": "0.8rem", "color": MUTED, **style})


def bar(**style):
    return mui.Box(style={"display": "flex", "flexWrap": "wrap", "gap": "8px", "alignItems": "center",
                          "marginBottom": "8px", **style})


def toggle(key, choices):
    with mui.ButtonGroup(size="small", color="primary"):
        for label, value, tip in choices:
            with tipped(tip):
                mui.Button(label, variant=B(f"{key} === '{value}' ? 'contained' : 'outlined'"),
                           on_click=C(f"{key} = '{value}'"))


def head(*columns):
    with mui.TableHead(), mui.TableRow():
        for title, width, *tip in columns:
            with mui.TableCell(style={"width": f"{width}px"} if width else {}, key=title):
                if tip:
                    with tipped(tip[0]):
                        html.Span(title, style={"borderBottom": f"1px dotted {MUTED}", "cursor": "help"})
                else:
                    html.Span(title)


def table(height):
    return mui.TableContainer(style={"maxHeight": f"calc(100vh - {height}px)", "border": f"1px solid {LINE}",
                                     "borderRadius": "8px", "background": SURFACE})


# ----------------------------------------------------------------------------- Rules


def refresh_rules():
    rows = store.rule_rows()
    levels = {lv: sum(r["level"] == lv for r in rows) for lv in ("high", "medium", "low")}
    documented = sum(r["level"] == "documented" for r in rows)
    counts = {d: sum(r["decision"] == d for r in rows) for d in ["undecided", *DECISIONS]}
    state.rule_counts = (", ".join(f"{n} {lv}" for lv, n in levels.items())
                         + f" confidence, {documented} from the developer guide only; "
                         + ", ".join(f"{n} {d}" for d, n in counts.items()))
    if state.rule_topic:
        rows = [r for r in rows if r["topic"] == state.rule_topic]
    if state.rule_decision:
        rows = [r for r in rows if r["decision"] == state.rule_decision]
    if state.rule_level == "conflict":
        rows = [r for r in rows if r["guide_conflict"]]
    elif state.rule_level in ("automated", "automatable"):
        rows = [r for r in rows if r[state.rule_level]]
    elif state.rule_level:
        rows = [r for r in rows if r["level"] == state.rule_level]
    needle = (state.rule_search or "").lower().strip()
    if needle:
        rows = [r for r in rows if needle in f"{r['id']} {r['rule']} {r['topic']}".lower()]
    state.rule_shown = f"{len(rows)} shown"
    state.rule_rows = [dict(r, color=DECISION_COLOR.get(r["decision"], "default")) for r in rows]


@state.change("rule_topic", "rule_decision", "rule_level", "rule_search")
def on_rule_filters(**_):
    refresh_rules()


@state.change("rule_key")
def on_rule_key(rule_key, **_):
    rule = store.rule_detail(rule_key) if rule_key else None
    state.rule = dict(rule, color=DECISION_COLOR.get(rule["decision"], "default")) if rule else None
    state.rule_text = rule["rule"] if rule else ""
    state.rule_note = rule["note"] if rule else ""


def decide(decision):
    if state.rule_key:
        store.decide(state.rule_key, decision, state.rule_text, state.rule_note)
        on_rule_key(state.rule_key)
        refresh_rules()


def rules_view():
    with mui.Box(style={"display": "flex", "gap": "12px"}):
        with mui.Box(style={"flex": "7", "minWidth": 0}):
            with bar():
                field("Filter rules", "rule_search", tip="Show rules whose text contains these words")
                select("Topic", "rule_topic", "topics", 200, tip="The area of VTK practice a rule covers")
                select("Decision", "rule_decision", "decisions", 150,
                       tip="Your curation decision: accepted, edited, rejected, or not yet decided")
                select("Confidence", "rule_level", "levels", 150,
                       tip="How reliably authors act on a rule when a reviewer raises it, and whether a tool "
                           "or the developer guide covers it")
            caption([B("rule_counts + ' (' + rule_shown + ')'")], marginBottom="4px")
            with table(250), mui.Table(size="small", sticky_header=True):
                head(("Id", 60, "Rule number; click a row for its evidence"),
                     ("Confidence", 100, "High: authors act on it more often than the comment alone predicts. "
                                         "Low: less often, or a tool or the developer guide disagrees with it"),
                     ("Rule", None, "The convention, with the reason for its confidence level"),
                     ("Topic", 130), ("MRs", 50, "Merge requests where a reviewer raised this rule"),
                     ("Last seen", 96, "When a reviewer last raised it"),
                     ("Decision", 100, "Your curation decision"))
                with mui.TableBody():
                    with react.For(items="rule_rows", name="r"):
                        with mui.TableRow(key=B("r.key"), hover=True, selected=B("r.key === rule_key"),
                                          on_click=C("rule_key = r.key"), style={"cursor": "pointer"}):
                            mui.TableCell([B("r.id")], style={"color": ACCENT, "fontWeight": 500})
                            with mui.TableCell():
                                level_pill("r.level")
                                with react.If(value="r.guide_conflict"):
                                    html.Div("conflicts", style={"fontSize": "0.7rem", "color": "#B42339",
                                                                 "marginTop": "4px"})
                                with react.If(value="r.automated"):
                                    html.Div("automated", style={"fontSize": "0.7rem", "color": "#0B5C75",
                                                                 "marginTop": "4px"})
                                with react.If(value="!r.automated && r.automatable"):
                                    html.Div("could automate", style={"fontSize": "0.7rem", "color": "#6E56CF",
                                                                      "marginTop": "4px"})
                            with mui.TableCell():
                                html.Div([B("r.rule")])
                                html.Div([B("r.reason")], style={"color": MUTED, "fontSize": "0.76rem",
                                                                 "marginTop": "2px"})
                            mui.TableCell([B("r.topic")])
                            mui.TableCell([B("r.mrs")])
                            mui.TableCell([B("r.last")])
                            with mui.TableCell():
                                mui.Chip(label=B("r.decision"), size="small", color=B("r.color"),
                                         variant="outlined")
        with mui.Box(style={"flex": "5", "minWidth": 0}):
            rule_detail()


def level_pill(expr):
    html.Span([B(f"{expr}.charAt(0).toUpperCase() + {expr}.slice(1)")], style={
        "display": "inline-block", "padding": "1px 8px", "borderRadius": "10px", "fontSize": "0.76rem",
        "fontWeight": 600, "whiteSpace": "nowrap", "color": B(f"{LEVEL_FG}[{expr}]"),
        "background": B(f"{LEVEL_BG}[{expr}]")})


def confidence_panel():
    with html.Div(style={"margin": "12px 0", "padding": "10px 12px", "borderRadius": "8px",
                         "border": f"1px solid {LINE}", "background": "#FAFBFC"}):
        with html.Div(style={"display": "flex", "alignItems": "center", "gap": "8px", "marginBottom": "6px"}):
            html.Span("Confidence", style={"fontWeight": 600})
            level_pill("rule.level")
            html.Div(style={"flex": "1"})
            with react.If(value="rule.doc_url"):
                link("'Open ' + rule.doc_file", "rule.doc_url")
        with react.For(items="rule.confidence", name="f"):
            with html.Div(key=B("f.name"), style={"display": "flex", "gap": "10px", "padding": "3px 0",
                                                  "borderTop": f"1px solid {LINE}"}):
                html.Span(style={"width": "8px", "height": "8px", "borderRadius": "4px", "flex": "none",
                                 "marginTop": "7px", "background": B(f"f.tone === 'neutral' ? '{LINE}' : {TONE}[f.tone]")})
                html.Span([B("f.name")], style={"width": "110px", "flex": "none", "color": MUTED})
                html.Span([B("f.detail")], style={"flex": "1"})


def evidence_list(field_name, title, color="inherit"):
    with react.If(value=f"rule.{field_name}.length"):
        with html.Div(style={"marginTop": "12px"}):
            html.Div(title, style={"fontWeight": 600, "color": color})
            with react.For(items=f"rule.{field_name}", name="e"):
                with html.Div(key=B("e.mr + e.date + e.text.slice(0, 20)"), style={"margin": "8px 0"}):
                    link("'!' + e.mr", "e.url")
                    html.Span([" ", B("e.reviewer"), ", ", B("e.date")], style={"color": MUTED})
                    html.Div([B("e.text")], style={"paddingLeft": "10px", "borderLeft": f"3px solid {LINE}",
                                                   "whiteSpace": "pre-wrap"})


def rule_detail():
    box = {"padding": "12px", "height": "calc(100vh - 150px)", "overflowY": "auto", "fontSize": "0.9rem"}
    with react.If(value="rule"):
        with mui.Paper(variant="outlined", style=box):
            with mui.Stack(direction="row", spacing=1, style={"alignItems": "center", "marginBottom": "8px"}):
                mui.Typography([B("rule.id")], variant="h6")
                mui.Chip(label=B("rule.topic"), size="small")
                mui.Chip(label=B("rule.decision"), size="small", color=B("rule.color"), variant="outlined")
                mui.Box(style={"flex": "1"})
                caption([B("rule.decided_by ? rule.decided_by + ', ' + rule.decided_at : ''")])
            confidence_panel()
            field("Rule (edit before accepting to record an edited rule)", "rule_text", multiline=True,
                  min_rows=2, full_width=True, tip="Change the wording here, then Accept to record it as edited")
            with react.If(value="rule_text !== rule.draft"):
                caption(["Draft: ", B("rule.draft")], marginTop="4px")
            with html.Div(style={"marginTop": "8px", "display": "flex"}):
                field("Note (why, or what should change)", "rule_note", tip="Saved with your decision")
            with mui.Stack(direction="row", spacing=1, style={"marginTop": "8px"}):
                with tipped("Record this rule as accepted, or as edited if you changed the wording"):
                    mui.Button("Accept", color="success", variant="contained", size="small",
                               on_click=C(decide, "['accepted']"))
                with tipped("Record this rule as rejected"):
                    mui.Button("Reject", color="error", variant="contained", size="small",
                               on_click=C(decide, "['rejected']"))
                with tipped("Remove your decision on this rule"):
                    mui.Button("Clear decision", size="small", on_click=C(decide, "['undecided']"))
            with react.If(value="rule.rationale"):
                html.Div(["Rationale: ", B("rule.rationale")], style={"marginTop": "12px"})
            html.Div(["Scope: ", B("rule.scope")])
            html.Div(["Support: ", B("rule.support")])
            html.Div(["Reviewers: ", B("rule.reviewers")])
            with react.If(value="rule.conflicts.length"):
                with html.Div(style={"marginTop": "12px"}):
                    html.Div("Names APIs VTK has since deprecated or removed",
                             style={"fontWeight": 600, "color": "#bc4c00"})
                    with react.For(items="rule.conflicts", name="d"):
                        with html.Div(key=B("d.api + d.version"), style={"margin": "4px 0"}):
                            html.Span([B("d.api")], style={"fontFamily": MONO})
                            html.Span([" deprecated in ", B("d.version"), " (", B("d.deprecated_on")])
                            with react.If(value="d.deprecated_mr"):
                                html.Span(", ")
                                link("'!' + d.deprecated_mr", "d.deprecated_url")
                            html.Span(")")
                            with react.If(value="d.reason"):
                                html.Span([": ", B("d.reason")])
            evidence_list("examples", "Reviewers asking for this")
            evidence_list("counter", "Reviewers disagreeing", "#B42339")
    with react.If(value="!rule"):
        with mui.Paper(variant="outlined", style={"padding": "24px", "color": MUTED}):
            html.Div("Select a rule to see its evidence and record a decision.")


# ----------------------------------------------------------------------------- Deprecations


@state.change("dep_outcome", "dep_search")
def on_dep_filters(dep_outcome, dep_search, **_):
    rows = store.deprecation_rows()
    if dep_outcome:
        rows = [r for r in rows if r["outcome"] == dep_outcome]
    needle = (dep_search or "").lower().strip()
    if needle:
        rows = [r for r in rows if needle in f"{r['api']} {r['version']} {r.get('reason') or ''}".lower()]
    state.dep_shown = (f"{len(rows)} deprecated APIs" + (f", first {MAX_ROWS} shown" if len(rows) > MAX_ROWS else "")
                       + ". 'present' means still deprecated in the current tree.")
    state.dep_rows = rows[:MAX_ROWS]


def deprecations_view():
    with bar():
        field("Search APIs, reasons, versions", "dep_search", tip="Filter by API name, reason or VTK version")
        select("Status", "dep_outcome", "outcomes", 180,
               tip="present: still deprecated. removed: deleted from VTK. undeprecated: the deprecation was reversed")
    caption([B("dep_shown")], marginBottom="4px")
    with table(220), mui.Table(size="small", sticky_header=True):
        head(("API", None, "The deprecated class, method or macro; hover a name for its declaration"),
             ("Version", 80, "The VTK version that deprecated it"),
             ("Outcome", 100, "present: still deprecated. removed: deleted from VTK. undeprecated: reversed"),
             ("Deprecated", 160, "When it was deprecated"), ("Removed", 160, "When it was removed, if it was"),
             ("Reason", None, "The reason given in the deprecation"))
        with mui.TableBody():
            with react.For(items="dep_rows", name="d"):
                with mui.TableRow(key=B("d.api + d.version"), hover=True):
                    mui.TableCell([B("d.api")], title=B("d.declaration"), style={"fontFamily": MONO})
                    mui.TableCell([B("d.version")])
                    mui.TableCell([B("d.outcome")])
                    with mui.TableCell():
                        html.Span([B("d.deprecated_on"), " "], style={"whiteSpace": "nowrap"})
                        with react.If(value="d.deprecated_mr"):
                            link("'!' + d.deprecated_mr", "d.deprecated_url")
                    with mui.TableCell():
                        html.Span([B("d.removed_on || ''"), " "], style={"whiteSpace": "nowrap"})
                        with react.If(value="d.removed_mr"):
                            link("'!' + d.removed_mr", "d.removed_url")
                    mui.TableCell([B("d.reason")])


# ----------------------------------------------------------------------------- Trends

TREND = {"quarters": [], "docs": [], "rows": {}}


@state.change("trend_what", "trend_source", "trend_kind", "trend_common")
def on_trend_filters(trend_what, trend_source, trend_kind, trend_common, **_):
    if trend_what == "labels" and trend_source == "discourse":
        state.trend_source = trend_source = "issue"
    if trend_what != "labels" and trend_source == "issue":
        state.trend_source = trend_source = "mr"
    if trend_what != "labels" and trend_kind == "all":
        state.trend_kind = trend_kind = "emerging"
    rows, quarters, docs = store.trend_rows(trend_what, trend_source, trend_kind, trend_common and trend_what == "terms")
    TREND.update(quarters=quarters, docs=docs, rows={r["name"]: r for r in rows})
    state.trend_rows = [{k: r[k] for k in ("name", "ratio", "docs", "first_seen", "peak")} for r in rows]
    state.trend_name = rows[0]["name"] if rows else None
    on_trend_name(state.trend_name)


@state.change("trend_name")
def on_trend_name(trend_name, **_):
    row = TREND["rows"].get(trend_name)
    if not row:
        state.trend_row, state.trend_chart, state.trend_title = None, "", ""
        return
    state.trend_row = {"name": row["name"], "description": row.get("description", ""), "examples": [
        dict(e, url=store.example_url(e["source"], e["id"])) for e in row["examples"]]}
    share = [100 * c / n if n else 0 for c, n in zip(row["series"], TREND["docs"])]
    label = {"mr": "merge requests", "issue": "issues"}.get(state.trend_source, "forum topics")
    if state.trend_what == "labels":
        state.trend_title = f"Share of labeled {label} carrying {row['name']}, by quarter"
    else:
        state.trend_title = f"Share of {label} mentioning {row['name']}, by quarter"
    state.trend_chart = "data:image/svg+xml;utf8," + quote(line_svg(TREND["quarters"][:len(share)], share, "%"))


def trends_view():
    with bar():
        toggle("trend_what", [
            ("Terms and code areas", "terms", "Single words, identifiers, and code directories (shown as dir:...)"),
            ("Themes", "themes", "Groups of related merge requests or topics, found by clustering their text"),
            ("GitLab labels", "labels", "The area: and lang: labels maintainers put on issues and merge requests. "
                                        "Shares are of the items that carry at least one such label, since 2015")])
        with react.If(value="trend_what !== 'labels'"):
            toggle("trend_source", [
                ("Merge requests", "mr", "Count merge requests: title, description, and the directories they changed"),
                ("Forum", "discourse", "Count Discourse forum topics: title and first post")])
        with react.If(value="trend_what === 'labels'"):
            toggle("trend_source", [
                ("Merge requests", "mr", "Count labeled merge requests"),
                ("Issues", "issue", "Count labeled issues")])
            toggle("trend_kind", [("All labels", "all", "Every label used at least 8 times, most used first")])
        toggle("trend_kind", [
            ("Emerging", "emerging", "Ratio = share in the last 2 years / share in the 4 years before"),
            ("Past bursts", "past", "Ratio = share at its peak (4-quarter average) / share in the years around "
                                    "the peak, for peaks that have ended"),
            ("Fading", "fading", "Ratio = share in the first 3 years of the record / share in the last 2 years")])
        with react.If(value="trend_what === 'terms'"):
            with tipped("Also list ordinary English words, which are left out by default"), \
                    html.Label(style={"display": "flex", "alignItems": "center", "fontSize": "0.9rem"}):
                mui.Checkbox(checked=B("trend_common"), size="small",
                             on_change=C("trend_common = $event.target.checked"))
                html.Span("Common English words")
    with mui.Box(style={"display": "flex", "gap": "12px"}):
        with mui.Box(style={"flex": "5", "minWidth": 0}):
            with table(220), mui.Table(size="small", sticky_header=True):
                head(("Term, code area, or theme", None, "Click a row to see its share by quarter and examples"),
                     ("Ratio", 70, "How many times larger its share of documents is in one period than in "
                                   "the other; the Emerging, Past bursts and Fading buttons say which periods. "
                                   "Rows are ranked by ratio and document count together"),
                     ("Docs", 70, "Merge requests or forum topics that mention it"),
                     ("First seen", 90, "Quarter it first appeared"),
                     ("Peak", 80, "Quarter its share was highest"))
                with mui.TableBody():
                    with react.For(items="trend_rows", name="t"):
                        with mui.TableRow(key=B("t.name"), hover=True, selected=B("t.name === trend_name"),
                                          on_click=C("trend_name = t.name"), style={"cursor": "pointer"}):
                            mui.TableCell([B("t.name")], style={"color": ACCENT, "fontWeight": 500})
                            mui.TableCell([B("t.ratio")])
                            mui.TableCell([B("t.docs")])
                            mui.TableCell([B("t.first_seen")])
                            mui.TableCell([B("t.peak")])
        with mui.Box(style={"flex": "7", "minWidth": 0}):
            with react.If(value="trend_chart"):
                with mui.Paper(variant="outlined", style={"padding": "8px"}):
                    html.Div([B("trend_title")], style={"fontWeight": 600, "fontSize": "0.9rem"})
                    html.Img(src=B("trend_chart"), alt=B("trend_title"), style={"width": "100%"})
            with react.If(value="trend_row"):
                with mui.Paper(variant="outlined", style={"padding": "12px", "marginTop": "8px",
                                                          "fontSize": "0.9rem"}):
                    with react.If(value="trend_row.description"):
                        html.Div([B("trend_row.description")], style={"marginBottom": "8px"})
                    html.Div("Examples across the record", style={"fontWeight": 600})
                    with react.For(items="trend_row.examples", name="e"):
                        with html.Div(key=B("e.source + e.id"), style={"margin": "4px 0"}):
                            html.Span([B("e.q"), " "], style={"color": MUTED})
                            link("e.source === 'mr' ? '!' + e.id : e.source === 'issue' ? '#' + e.id : 'topic ' + e.id",
                                 "e.url")
                            html.Span([" ", B("e.title")])


# ----------------------------------------------------------------------------- Search


def run_search(q=None):
    state.q = q if q is not None else state.q
    if not (state.q or "").strip():
        return
    state.searching, state.search_error = True, ""
    state.flush()
    try:
        found = store.search(state.q, state.q_kind or None, state.q_since, state.q_until, state.q_label or None)
        state.search_rows = [r for r in found if not r["other_kind"]]
        state.search_more = [r for r in found if r["other_kind"]]
    except OSError as e:
        state.search_error = f"Search needs the DGX Spark for meaning-based matching and could not reach it: {e}"
        state.search_rows, state.search_more = [], []
    finally:
        state.searching = False


def search_key(key, value):
    if key == "Enter":
        run_search(value)


def open_topic(tid):
    found = topics.topic(tid) if tid else None
    state.topic_error = "" if found else f"Topic {tid} is not in the forum mirror."
    state.topic = found


def topic_view():
    with html.Div(style={"display": "flex", "alignItems": "center", "gap": "12px", "marginBottom": "10px"}):
        with tipped("Return to the search results"):
            mui.Button("Back to results", size="small", variant="outlined", on_click=C("topic = null"))
        html.Span([B("topic.title")], style={"fontWeight": 600, "fontSize": "1.05rem"})
        html.Div(style={"flex": "1"})
        link("'Open on discourse.vtk.org'", "topic.url")
    with mui.Box(style={"display": "flex", "gap": "12px"}):
        with html.Div(style={"flex": "3", "minWidth": 0, "maxHeight": "calc(100vh - 190px)", "overflowY": "auto"}):
            caption([B("'Started ' + topic.created + ', ' + topic.posts.length + ' posts'")], marginBottom="6px")
            with react.For(items="topic.posts", name="p"):
                with html.Div(key=B("p.n"), style={
                        "margin": "0 0 8px", "padding": "10px 12px", "background": SURFACE, "borderRadius": "8px",
                        "border": B(f"p.accepted ? '2px solid #1A7F37' : '1px solid {LINE}'"), "fontSize": "0.88rem"}):
                    with html.Div(style={"display": "flex", "alignItems": "center", "gap": "8px", "marginBottom": "6px"}):
                        badge([B("p.author.slice(0, 1).toUpperCase()")], "#E4E8EE", INK)
                        html.Span([B("p.author")], style={"fontWeight": 600})
                        with react.If(value="p.staff"):
                            html.Span("Kitware", style={"fontSize": "0.72rem", "color": ACCENT, "background": ACCENT_TINT,
                                                         "borderRadius": "8px", "padding": "0 6px"})
                        html.Span([B("p.date")], style={"color": MUTED, "fontSize": "0.8rem"})
                        with react.If(value="p.reply_to"):
                            html.Span([B("'replying to #' + p.reply_to")], style={"color": MUTED, "fontSize": "0.8rem"})
                        html.Div(style={"flex": "1"})
                        with react.If(value="p.accepted"):
                            html.Span("Accepted answer", style={"fontSize": "0.75rem", "fontWeight": 600,
                                                                 "color": "#1A7F37"})
                        html.Span([B("'#' + p.n")], style={"color": MUTED, "fontSize": "0.8rem"})
                    html.Div([B("p.text")], style={"whiteSpace": "pre-wrap", "paddingLeft": "32px",
                                                   "overflowWrap": "anywhere"})
        with html.Div(style={"flex": "1", "minWidth": "240px"}):
            with mui.Paper(variant="outlined", style={"padding": "10px 12px", "fontSize": "0.85rem"}):
                html.Div("Cited by", style={"fontWeight": 600, "marginBottom": "4px"})
                with react.If(value="!topic.incoming.length"):
                    caption("Nothing in the mirrored MRs, issues, review threads, or blog posts cites this topic.")
                with react.For(items="topic.incoming", name="i"):
                    with html.Div(key=B("i.kind + i.label"), style={"margin": "6px 0"}):
                        link("i.label", "i.url")
                        html.Span([" ", B("i.kind"), ", ", B("i.date")], style={"color": MUTED, "fontSize": "0.78rem"})
                        with react.If(value="i.title && i.title !== i.label"):
                            caption([B("i.title")])
                html.Div("Links to", style={"fontWeight": 600, "margin": "12px 0 4px"})
                with react.If(value="!topic.outgoing.length"):
                    caption("The topic links to no MRs, issues, or other topics.")
                with react.For(items="topic.outgoing", name="o"):
                    with html.Div(key=B("o.label"), style={"margin": "6px 0"}):
                        with react.If(value="o.topic"):
                            html.A([B("o.label")], href="#", style={"color": ACCENT, "fontWeight": 500},
                                   on_click=C(open_topic, "[o.topic]", modifiers=["prevent"]))
                        with react.If(value="!o.topic"):
                            link("o.label", "o.url")
                        html.Span([" ", B("o.kind")], style={"color": MUTED, "fontSize": "0.78rem"})
                        with react.If(value="o.title"):
                            caption([B("o.title")])


def search_view():
    with react.If(value="topic"):
        topic_view()
    with react.If(value="!topic"):
        search_results()


def search_results():
    with bar():
        field("Ask about VTK history: an API, a design question, a bug", "q", on_enter=search_key,
              tip="Matches by keyword and by meaning; press Enter to search")
        select("Kind", "q_kind", "kinds", 120,
               tip="Limit to one kind: review thread, merge request, issue, forum post, blog, doc, note or class")
        select("GitLab label", "q_label", "label_options", 220,
               tip="Only issues and merge requests carrying this label, and review threads and release notes of "
                   "such merge requests. The number is how many issues and MRs carry it")
        field("Since (YYYY-MM-DD)", "q_since", 170, tip="Only items on or after this date")
        field("Before (YYYY-MM-DD)", "q_until", 170, tip="Only items before this date")
        with tipped("Run the search"):
            mui.Button("Search", variant="contained", size="small", loading=B("searching"),
                       on_click=C(run_search, "[q]"))
    with react.If(value="search_error"):
        mui.Alert([B("search_error")], severity="warning", style={"marginBottom": "8px"})
    with react.If(value="topic_error"):
        mui.Alert([B("topic_error")], severity="warning", style={"marginBottom": "8px"})
    with html.Div(style={"maxHeight": "calc(100vh - 220px)", "overflowY": "auto"}):
        result_table("search_rows")
        with react.If(value="search_more.length"):
            html.Div("Also matching in other sources", style={"fontWeight": 600, "fontSize": "0.85rem",
                                                              "margin": "14px 0 6px"})
            caption("The best matches of each kind that did not make the list above. Choose a Kind to see more.",
                    marginBottom="6px")
            result_table("search_more")


def label_pills(expr):
    with react.If(value=f"{expr} && {expr}.length"):
        with html.Div(style={"display": "flex", "flexWrap": "wrap", "gap": "4px", "margin": "2px 0"}):
            with react.For(items=expr, name="lb"):
                html.Span([B("lb")], key=B("lb"), style={
                    "fontSize": "0.7rem", "borderRadius": "8px", "padding": "0 6px", "whiteSpace": "nowrap",
                    "color": B(f"lb.startsWith('area:') ? '{ACCENT}' : '{MUTED}'"),
                    "background": B(f"lb.startsWith('area:') ? '{ACCENT_TINT}' : '#EEF1F5'")})


def result_table(items):
    cell = {"overflow": "hidden", "overflowWrap": "anywhere", "verticalAlign": "top"}
    with mui.TableContainer(style={"border": f"1px solid {LINE}", "borderRadius": "8px", "background": SURFACE,
                                   "overflowX": "hidden"}):
        with mui.Table(size="small", style={"tableLayout": "fixed", "width": "100%"}):
            head(("Kind", 70, "thread: a review discussion; mr: merge request; post: forum topic"),
                 ("Ref", 110, "Opens the item on GitLab, Discourse or the web"), ("Date", 100), ("Author", 130),
                 ("Title and excerpt", None, "The part of the item that best matches the search"))
            with mui.TableBody():
                with react.For(items=items, name="s"):
                    with mui.TableRow(key=B("s.kind + s.ref + (s.path || '') + s.title"), hover=True):
                        mui.TableCell([B("s.kind")], style={**cell, "whiteSpace": "nowrap", "overflowWrap": "normal"})
                        with mui.TableCell(style=cell, title=B("s.ref")):
                            link("s.label", "s.url")
                        mui.TableCell([B("s.date")], style={**cell, "whiteSpace": "nowrap"})
                        mui.TableCell([B("s.author")], style=cell)
                        with mui.TableCell(style=cell):
                            html.Div([B("s.title")], style={"fontWeight": 500})
                            with react.If(value="s.path"):
                                caption([B("s.path")])
                            label_pills("s.labels")
                            caption([B("s.snippet")])
                            with react.If(value="s.topic"):
                                with tipped("Read the whole forum topic, with the MRs, issues and topics it "
                                            "links to and what in the history cites it"):
                                    mui.Button("Read topic", size="small", variant="text",
                                               on_click=C(open_topic, "[s.topic]"),
                                               style={"padding": "0 4px", "minWidth": 0, "marginTop": "2px"})


# ----------------------------------------------------------------------------- Review

REV = {"record": None, "revs": [], "files": [], "runs": [], "reviewers": []}
ROW_BG = {"add": "#E7F6EC", "del": "#FCEBEC", "hunk": "#EEF3FB", "ctx": SURFACE}
state.update({"rv_iid": "", "rv_mr": None, "rv_revisions": [], "rv_rev": None, "rv_runs": [], "rv_run": None,
              "rv_files": [], "rv_file": None, "rv_rows": [], "rv_outside": [], "rv_findings": [], "rv_trace": [],
              "rv_models": options(["qwen3-coder-next:q4_K_M", "gpt-oss:120b"]),
              "rv_model": "qwen3-coder-next:q4_K_M", "rv_running": False, "rv_status": "",
              "rv_summary": reviews.summary(), "rv_note": "", "rv_queue": reviews.reviewed_mrs(), "rv_pick": None, "rv_suggest": [],
              "rv_suggest_note": "", "rv_tools": []})


@state.change("rv_pick")
def on_pick(rv_pick, **_):
    if rv_pick:
        state.rv_iid = str(rv_pick)
        load_mr(rv_pick)


def current_predictions():
    run = REV["runs"][state.rv_run] if state.rv_run is not None and state.rv_run < len(REV["runs"]) else None
    return (run["predictions"] if run else []), (run["label"] if run else "")


def load_mr(iid=None):
    iid = str(iid if iid is not None else state.rv_iid).strip().lstrip("!")
    record = reviews.mr(iid) if iid.isdigit() else None
    if not record:
        state.rv_status = f"MR !{iid} is not in the mirror."
        return
    mr = record["merge_request"]
    REV["record"] = record
    REV["revs"] = reviews.revisions(record)
    state.rv_mr = {"iid": mr["iid"], "title": mr["title"], "author": mr["author"]["username"], "state": mr["state"],
                   "url": mr["web_url"], "created": mr["created_at"][:10]}
    state.rv_revisions = [{"title": r["label"], "value": i} for i, r in enumerate(REV["revs"])]
    bench_head = reviews.benchmark_heads.get(mr["iid"])
    pick = next((i for i, r in enumerate(REV["revs"]) if r["head"] == bench_head), 0 if REV["revs"] else None)
    state.rv_status = "" if REV["revs"] else "No revision found for this MR."
    state.rv_rev = pick
    on_revision(pick)


def mr_key(key, value):
    if key == "Enter":
        load_mr(value)


@state.change("rv_rev")
def on_revision(rv_rev, **_):
    if rv_rev is None or rv_rev >= len(REV["revs"]):
        return
    rev = REV["revs"][rv_rev]
    state.rv_status = "Loading diff..."
    state.flush()
    files = reviews.diff(rev["base"], rev["head"])
    if files is None:
        state.rv_status = "Could not fetch this revision from GitLab."
        return
    REV["files"] = files
    REV["reviewers"] = reviews.reviewer_comments(REV["record"], rev["head"])
    suggest_reviewers()
    run_tool_checks(rev)
    load_runs()
    state.rv_status = ""


def run_tool_checks(rev):
    try:
        found = tool_checks.check(reviews.repo, rev["base"], rev["head"])
    except Exception as e:  # show why instead of failing the page
        found = [{"tool": "tool checks", "path": None, "line": None, "message": f"not run: {e}"}]
    state.rv_tools = [dict(f, key=f"{f['tool']}{f['path']}{f['line']}{i}",
                           where=(f"{f['path'].split('/')[-1]}:{f['line']} " if f["line"] else ""))
                      for i, f in enumerate(found)]


def suggest_reviewers():
    mr = REV["record"]["merge_request"]
    is_open = mr["state"] == "opened"
    at = datetime.now().isoformat()[:19] if is_open else mr["created_at"][:19]
    actual = {n["author"]["username"] for d in REV["record"].get("discussions") or [] for n in d["notes"]}
    picks = expertise.suggest([f["path"] for f in REV["files"]], at, exclude={mr["author"]["username"]}, top=5)
    state.rv_suggest = [{"user": s["user"], "reason": reason(s), "reviewed": s["user"] in actual} for s in picks]
    state.rv_suggest_note = ("Ranked from who reviewed and wrote these files, weighted to recent work; only people "
                             "active in the last six months. " + ("" if is_open else
                             "Uses history up to when this MR was opened; \u201creviewed it\u201d marks who did."))


def load_runs(select_file=None):
    rev = REV["revs"][state.rv_rev]
    REV["runs"] = reviews.saved_runs(state.rv_mr["iid"], rev["head"])
    held = lambda r: f", {len(r['held_back'])} held back by the checker" if r.get("held_back") else ""
    state.rv_runs = [{"title": f"{r['label']} ({len(r['predictions'])} comments{held(r)})", "value": i}
                     for i, r in enumerate(REV["runs"])]
    state.rv_run = len(REV["runs"]) - 1 if REV["runs"] else None
    on_run(state.rv_run, select_file)


@state.change("rv_run")
def on_run(rv_run, select_file=None, **_):
    predictions, _label = current_predictions()
    run = REV["runs"][rv_run] if rv_run is not None and rv_run < len(REV["runs"]) else None
    state.rv_findings = [dict(f, name=f["path"].split("/")[-1]) for f in (run["findings"] if run else [])]
    state.rv_trace = [f"{t['step']}: {t['tool']}({', '.join(f'{k}={v}' for k, v in (t['args'] or {}).items())})"[:200]
                      for t in (run["trace"] if run else [])]
    files = []
    for f in REV["files"]:
        agent = sum(p["path"] == f["path"] for p in predictions)
        people = sum(c["path"] == f["path"] for c in REV["reviewers"])
        files.append({"path": f["path"], "name": f["path"].split("/")[-1], "agent": agent, "reviewer": people,
                      "stats": f"+{f['added']} -{f['removed']}" + (f", agent {agent}" if agent else "")
                      + (f", reviewers {people}" if people else "")})
    state.rv_files = files
    paths = [f["path"] for f in files]
    commented = [f["path"] for f in files if f["agent"] or f["reviewer"]]
    state.rv_file = select_file or (state.rv_file if state.rv_file in paths else (commented or paths or [None])[0])
    render_file(state.rv_file)


@state.change("rv_file")
def render_file(rv_file, **_):
    predictions, _label = current_predictions()
    head_sha = REV["revs"][state.rv_rev]["head"] if state.rv_rev is not None else ""
    rated = reviews.ratings()
    iid = state.rv_mr["iid"] if state.rv_mr else None
    agent = [dict(p, key=comment_key(iid, head_sha, p), check_why=(p.get("check") or {}).get("why", ""),
                  verdict=rated.get(comment_key(iid, head_sha, p), {}).get("verdict"))
             for p in predictions if p["path"] == rv_file]
    people = [dict(c, key=f"{c['author']}{c['date']}{c['body'][:20]}") for c in REV["reviewers"]
              if c["path"] == rv_file]
    f = next((x for x in REV["files"] if x["path"] == rv_file), None)
    rows, placed = [], set()
    for i, r in enumerate(f["rows"] if f else []):
        sign = "+" if r["kind"] == "add" else "-" if r["kind"] == "del" else " "
        row = dict(r, i=i, bg=ROW_BG[r["kind"]], line=sign + r["text"], agent=[], people=[])
        if r["new"] != "":
            row["agent"] = [c for c in agent if c["line"] == r["new"]]
            row["people"] = [c for c in people if c["line"] == r["new"]]
        elif r["old"] != "":
            row["people"] = [c for c in people if c["line"] is None and c["old_line"] == r["old"]]
        placed.update(c["key"] for c in row["agent"] + row["people"])
        rows.append(row)
    state.rv_rows = rows
    outside = [c for c in agent + people if c["key"] not in placed]
    state.rv_outside = {"agent": [c for c in outside if c.get("comment")],
                        "people": [c for c in outside if c.get("body")]}


def rate(key, verdict):
    predictions, label = current_predictions()
    head_sha = REV["revs"][state.rv_rev]["head"]
    comment = next((p for p in predictions if comment_key(state.rv_mr["iid"], head_sha, p) == key), None)
    if comment:
        reviews.rate(state.rv_mr["iid"], head_sha, comment, verdict, state.rv_note, label)
        state.rv_note = ""
        state.rv_summary = reviews.summary()
        state.rv_queue = reviews.reviewed_mrs()
        render_file(state.rv_file)


def run_agent():
    """Start the review as a background task. wslink awaits a callback before it reads the next websocket
    message, so awaiting a minute-long review here would stop pong replies and the browser would disconnect."""
    if not state.rv_mr or state.rv_rev is None or state.rv_running:
        return
    asynchronous.create_task(agent_task(REV["revs"][state.rv_rev], state.rv_mr, state.rv_model))


async def agent_task(rev, mr, model):
    with state:
        state.rv_running, state.rv_status = True, f"Reviewing with {model}; this takes one to five minutes..."
    start = time.monotonic()
    try:
        job = asyncio.get_running_loop().run_in_executor(
            None, reviews.run_agent, mr["iid"], rev["base"], rev["head"], mr["title"], mr["created"], model)
        while not job.done():
            await asyncio.wait({job}, timeout=5)
            if not job.done():
                with state:
                    state.rv_status = (f"Reviewing with {model}: {time.monotonic() - start:.0f} s so far; "
                                       "usually one to five minutes")
        job.result()
        with state:
            state.rv_status = ""
            state.rv_queue = reviews.reviewed_mrs()
            load_runs()
    except Exception as e:  # show the failure in the page rather than losing it in the server log
        with state:
            state.rv_status = f"Review failed: {e}"
    finally:
        with state:
            state.rv_running = False


def badge(children, background, color="white"):
    return html.Span(children, style={
        "width": "24px", "height": "24px", "borderRadius": "50%", "flex": "none", "display": "inline-flex",
        "alignItems": "center", "justifyContent": "center", "fontSize": "0.7rem", "fontWeight": 600,
        "background": background, "color": color, "fontFamily": SANS})


CARD = {"margin": "6px 10px", "padding": "10px 12px", "background": SURFACE, "border": f"1px solid {LINE}",
        "borderRadius": "8px", "fontFamily": SANS, "fontSize": "0.86rem", "lineHeight": "1.5"}


def agent_cards(items):
    with react.For(items=items, name="c"):
        with html.Div(key=B("c.key"), style={**CARD, "borderLeft": f"3px solid {ACCENT}"}):
            with html.Div(style={"display": "flex", "alignItems": "center", "gap": "8px", "marginBottom": "6px"}):
                badge("AI", ACCENT)
                html.Span("Review agent", style={"fontWeight": 600})
                with react.If(value="c.severity"):
                    mui.Chip(label=B("c.severity"), size="small", variant="outlined")
                with react.If(value="c.basis"):
                    html.Span([B("c.basis")], style={"color": MUTED, "fontSize": "0.8rem"})
                html.Div(style={"flex": "1"})
                with mui.ButtonGroup(size="small"):
                    for verdict, color, tip in (
                            ("valid", "success", "The comment is correct and worth posting"),
                            ("wrong", "error", "The comment is incorrect, or not worth a reviewer's time"),
                            ("unsure", "inherit", "Can't tell without more context")):
                        with tipped(tip):
                            mui.Button(verdict.capitalize(), color=color,
                                       variant=B(f"c.verdict === '{verdict}' ? 'contained' : 'outlined'"),
                                       on_click=C(rate, f"[c.key, '{verdict}']"),
                                       style={"padding": "0 10px", "minWidth": 0, "fontSize": "0.78rem"})
            html.Div([B("c.comment")], style={"whiteSpace": "pre-wrap", "paddingLeft": "32px"})
            with react.If(value="c.check_why"):
                html.Div([B("'Checked: ' + c.check_why")],
                         style={"paddingLeft": "32px", "marginTop": "4px", "color": MUTED, "fontSize": "0.8rem"})


def people_cards(items):
    with react.For(items=items, name="c"):
        with html.Div(key=B("c.key"), style={**CARD, "borderLeft": f"3px solid {REVIEWER}"}):
            with html.Div(style={"display": "flex", "alignItems": "center", "gap": "8px", "marginBottom": "6px"}):
                badge([B("c.author.slice(0, 1).toUpperCase()")], "#E4E8EE", INK)
                html.Span([B("c.author")], style={"fontWeight": 600})
                html.Span([B("c.date")], style={"color": MUTED, "fontSize": "0.8rem"})
            html.Div([B("c.body")], style={"whiteSpace": "pre-wrap", "paddingLeft": "32px"})
            with react.For(items="c.replies", name="r"):
                with html.Div(key=B("r.author + r.body.slice(0, 20)"),
                              style={"display": "flex", "gap": "8px", "marginTop": "8px", "paddingLeft": "32px"}):
                    badge([B("r.author.slice(0, 1).toUpperCase()")], "#EEF1F5", MUTED)
                    with html.Div():
                        html.Span([B("r.author")], style={"fontWeight": 600, "marginRight": "6px"})
                        html.Span([B("r.body")], style={"whiteSpace": "pre-wrap", "color": "#2E3A4F"})


def reviewer_panel():
    with react.If(value="rv_suggest.length"):
        with html.Details(open=True, style={"marginBottom": "8px", "padding": "8px 10px", "background": SURFACE,
                                            "border": f"1px solid {LINE}", "borderRadius": "8px", "fontSize": "0.84rem"}):
            html.Summary("Suggested reviewers", style={"cursor": "pointer", "fontWeight": 600},
                         title="Ranked by recent reviews and commits on these files; an actual reviewer was in "
                               "the top 3 for 76% of past MRs")
            with react.For(items="rv_suggest", name="s"):
                with html.Div(key=B("s.user"), style={"marginTop": "6px"}):
                    with html.Div(style={"display": "flex", "alignItems": "center", "gap": "6px"}):
                        html.Span([B("s.user")], style={"fontWeight": 600})
                        with react.If(value="s.reviewed"):
                            html.Span("reviewed it", style={"fontSize": "0.72rem", "color": "#1A7F37",
                                                            "background": "#E6F4EA", "borderRadius": "8px",
                                                            "padding": "0 6px"})
                    html.Div([B("s.reason")], style={"color": MUTED, "fontSize": "0.76rem"})
            html.Div([B("rv_suggest_note")], style={"color": MUTED, "fontSize": "0.72rem", "marginTop": "6px"})


def review_view():
    with bar():
        field("MR number", "rv_iid", 120, on_enter=mr_key, tip="Type a merge request number and press Enter")
        with tipped("Load the MR's diff, its reviewers' comments, and any saved agent reviews"):
            mui.Button("Load", size="small", variant="outlined", on_click=C(load_mr, "[rv_iid]"))
        select("Or pick an MR the agent reviewed", "rv_pick", "rv_queue", 360, numeric=True,
               tip="MRs with saved agent reviews; those with comments you have not rated come first")
        with react.If(value="rv_revisions.length"):
            select("Revision", "rv_rev", "rv_revisions", 340, numeric=True, empty=False,
                   tip="Which pushed version of the MR to show; reviewer comments appear on the version they were made on")
        with react.If(value="rv_mr"):
            select("Agent review", "rv_run", "rv_runs", 340, numeric=True, empty=False,
                   tip="Saved agent reviews of this revision, from the benchmark or from Run agent")
            select("Model", "rv_model", "rv_models", 210, empty=False, tip="The model Run agent uses")
            with tipped("Review this revision now with the selected model; it takes a few minutes, and a second "
                        "model checks each comment before it is shown"):
                mui.Button("Run agent", variant="contained", size="small", loading=B("rv_running"),
                           on_click=C(run_agent))
    with react.If(value="rv_mr"):
        with html.Div(style={"display": "flex", "alignItems": "center", "fontSize": "0.9rem",
                             "marginBottom": "4px"}):
            link("'!' + rv_mr.iid", "rv_mr.url")
            html.Span([" ", B("rv_mr.title"), " (", B("rv_mr.author"), ", ", B("rv_mr.state"), ")"],
                      style={"marginLeft": "4px"})
            html.Div(style={"flex": "1"})
            caption(["Your ratings: ", B("rv_summary")])
        with react.If(value="rv_mr && !rv_runs.length"):
            caption("No saved agent review for this revision. Run the agent to make one.", marginBottom="4px")
    with react.If(value="rv_status"):
        html.Div([B("rv_status")], style={"color": "#bc4c00", "fontSize": "0.9rem", "marginBottom": "4px"})
    with react.If(value="rv_mr"):
        with mui.Box(style={"display": "flex", "gap": "12px"}):
            with mui.Box(style={"width": "25%", "minWidth": 0}):
                reviewer_panel()
                with mui.List(dense=True, style={"maxHeight": "calc(100vh - 360px)", "overflowY": "auto"}):
                    with react.For(items="rv_files", name="f"):
                        with mui.ListItemButton(key=B("f.path"), selected=B("f.path === rv_file"),
                                                on_click=C("rv_file = f.path"), title=B("f.path")):
                            mui.ListItemText(primary=B("f.name"), secondary=B("f.stats"))
                with html.Div(style={"display": "flex", "marginTop": "8px"}):
                    field("Note for your next rating (optional)", "rv_note",
                          tip="Saved with the next Valid, Wrong or Unsure you click")
                with react.If(value="rv_tools.length"):
                    with html.Details(open=True, style={"marginTop": "8px", "fontSize": "0.8rem"}):
                        html.Summary([B("'Tool checks (' + rv_tools.length + ')'")],
                                     title="What VTK's formatter, spell checker and GitLab robot flag on this revision",
                                     style={"cursor": "pointer", "fontSize": "0.9rem"})
                        html.Div("What VTK's formatter, spell checker, and GitLab robot will flag on this revision.",
                                 style={"color": MUTED, "margin": "2px 0 4px"})
                        with react.For(items="rv_tools", name="t"):
                            with html.Div(key=B("t.key"), style={"margin": "4px 0"}):
                                html.Span([B("t.tool")], style={"fontWeight": 600, "marginRight": "6px"})
                                html.Span([B("t.where"), B("t.message")])
                with react.If(value="rv_findings.length"):
                    with html.Details(style={"marginTop": "8px", "fontSize": "0.8rem"}):
                        html.Summary([B("'Static checks (' + rv_findings.length + ')'")],
                                     title="Facts the agent was given from static checks of the head commit",
                                     style={"cursor": "pointer", "fontSize": "0.9rem"})
                        with react.For(items="rv_findings", name="f"):
                            html.Div([B("f.kind"), ": ", B("f.name"), ":", B("f.line"), " ", B("f.fact")],
                                     key=B("f.path + f.line + f.kind"), style={"margin": "4px 0"})
                with react.If(value="rv_trace.length"):
                    with html.Details(style={"marginTop": "8px", "fontSize": "0.8rem"}):
                        html.Summary([B("'Agent steps (' + rv_trace.length + ')'")],
                                     title="Each tool the agent called while reviewing, in order",
                                     style={"cursor": "pointer", "fontSize": "0.9rem"})
                        with react.For(items="rv_trace", name="t"):
                            html.Div([B("t")], key=B("t"), style={"fontFamily": MONO})
            with mui.Box(style={"width": "75%", "minWidth": 0, "maxHeight": "calc(100vh - 250px)",
                                "overflow": "auto", "border": f"1px solid {LINE}", "borderRadius": "8px",
                                "background": SURFACE}):
                with react.If(value="rv_outside.agent.length || rv_outside.people.length"):
                    with html.Div(style={"background": "#FFF7E0", "padding": "6px 4px",
                                         "borderBottom": f"1px solid {LINE}"}):
                        caption("Comments on lines outside the diff", padding="0 8px")
                        agent_cards("rv_outside.agent")
                        people_cards("rv_outside.people")
                number = {"width": "46px", "flex": "none", "textAlign": "right", "color": "#98A2B3",
                          "padding": "0 8px", "userSelect": "none", "background": B("row.kind === 'hunk' ? "
                          "'transparent' : 'rgba(23, 32, 51, 0.03)'")}
                with html.Div(style={"fontFamily": MONO, "fontSize": "0.78rem", "lineHeight": "1.6",
                                     "minWidth": "fit-content"}):
                    with react.For(items="rv_rows", name="row"):
                        with html.Div(key=B("'r' + row.i")):
                            with html.Div(style={"display": "flex", "background": B("row.bg")}):
                                html.Span([B("row.old")], style=number)
                                html.Span([B("row.new")], style=number)
                                html.Span([B("row.line")], style={
                                    "whiteSpace": "pre", "padding": "0 10px",
                                    "color": B("row.kind === 'hunk' ? '#4A5A78' : '" + INK + "'")})
                            with react.If(value="row.agent.length || row.people.length"):
                                with html.Div(style={"background": CANVAS, "position": "sticky", "left": 0,
                                                     "maxWidth": "calc(75vw - 40px)", "padding": "4px 0",
                                                     "borderTop": f"1px solid {LINE}",
                                                     "borderBottom": f"1px solid {LINE}"}):
                                    agent_cards("row.agent")
                                    people_cards("row.people")


# ----------------------------------------------------------------------------- Briefing

briefing = Briefing(reviews, expertise, store.index)
state.update({"br_iid": "", "br_mr": None, "br": None, "br_status": "", "br_pick": None})


def load_brief(iid=None):
    iid = str(iid if iid is not None else state.br_iid).strip().lstrip("!")
    record = reviews.mr(iid) if iid.isdigit() else None
    if not record:
        state.br_status = f"MR !{iid} is not in the mirror."
        return
    revs = reviews.revisions(record)
    if not revs:
        state.br_status = "No revision found for this MR."
        return
    mr = record["merge_request"]
    state.br_mr = {"iid": mr["iid"], "title": mr["title"], "author": mr["author"]["username"],
                   "state": mr["state"], "url": mr["web_url"], "created": mr["created_at"][:10]}
    state.br, state.br_status = None, "Gathering history..."
    state.flush()
    rev = revs[-1]
    files = reviews.diff(rev["base"], rev["head"])
    if files is None:
        state.br_status = "Could not fetch this MR's changes from GitLab."
        return
    brief = briefing.build(record, rev, files)
    for f in brief["files"]:
        f["name"] = f["path"].split("/")[-1]
        for c in f["commits"]:
            c["url"] = f"https://gitlab.kitware.com/vtk/vtk/-/commit/{c['sha']}"
    brief["history_note"] = ("Uses history up to when this MR was opened, so it shows what was knowable then."
                             if mr["state"] != "opened" else "Uses all history up to today.")
    state.br, state.br_status = brief, ""


@state.change("br_pick")
def on_br_pick(br_pick, **_):
    if br_pick:
        state.br_iid = str(br_pick)
        load_brief(br_pick)


def br_key(key, value):
    if key == "Enter":
        load_brief(value)


def section(title, items, measured):
    with html.Div(style={**CARD, "margin": 0}):
        html.Div([title, " ", B(f"'(' + {items}.length + ')'")], style={"fontWeight": 600, "fontSize": "0.95rem"})
        html.Div([B(measured)], style={"color": MUTED, "fontSize": "0.76rem", "margin": "2px 0 8px",
                                       "paddingBottom": "6px", "borderBottom": f"1px solid {LINE}"})
        yield


def pill(text_expr, fg, bg):
    return html.Span([B(text_expr)], style={"fontSize": "0.72rem", "color": fg, "background": bg,
                                            "borderRadius": "8px", "padding": "0 6px", "whiteSpace": "nowrap"})


ROW = {"marginTop": "6px", "lineHeight": "1.45"}
SMALL = {"color": MUTED, "fontSize": "0.76rem"}


def briefing_view():
    with bar():
        field("MR number", "br_iid", 120, on_enter=br_key, tip="Type a merge request number and press Enter")
        with tipped("Gather what the history says about this MR; takes a few seconds"):
            mui.Button("Brief me", size="small", variant="contained", on_click=C(load_brief, "[br_iid]"))
        select("Or pick a past MR", "br_pick", "rv_queue", 360, numeric=True,
               tip="Past MRs to try; for a closed MR the briefing uses only history from before it was opened")
    caption("What VTK's GitLab and Discourse history says about a merge request. Each section states how "
            "well it held up when measured on past merge requests.", marginBottom="8px")
    with react.If(value="br_status"):
        html.Div([B("br_status")], style={"color": "#bc4c00", "fontSize": "0.9rem", "marginBottom": "4px"})
    with react.If(value="br_mr"):
        with html.Div(style={"fontSize": "0.95rem", "marginBottom": "4px"}):
            link("'!' + br_mr.iid", "br_mr.url")
            html.Span([" ", B("br_mr.title"), " (", B("br_mr.author"), ", ", B("br_mr.state"), ", opened ",
                       B("br_mr.created"), ")"])
    with react.If(value="br"):
        caption([B("br.history_note")], marginBottom="10px")
        with html.Div(style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(460px, 1fr))",
                             "gap": "12px", "alignItems": "start"}):
            with html.Div(style={"display": "flex", "flexDirection": "column", "gap": "12px"}):
                for _ in section("Related history", "br.related", "br.measured.related"):
                    with react.For(items="br.related", name="h"):
                        with html.Div(key=B("h.key"), style=ROW):
                            with html.Div(style={"display": "flex", "gap": "6px", "alignItems": "baseline"}):
                                pill("h.kind", MUTED, "#EEF1F5")
                                link("h.ref", "h.url")
                                html.Span([B("h.title")])
                                with react.If(value="h.linked"):
                                    pill("'linked in the description'", "#1A7F37", "#E6F4EA")
                            html.Div([B("h.date"), B("h.topic ? ' \u00b7 ' + h.topic : ''")],
                                     style={**SMALL, "paddingLeft": "4px"})
                            label_pills("h.labels")
                for _ in section("Deprecated APIs in the added code", "br.deprecated", "br.measured.deprecated"):
                    with react.If(value="!br.deprecated.length"):
                        html.Div("None found.", style=SMALL)
                    with react.For(items="br.deprecated", name="d"):
                        with html.Div(key=B("d.key"), style=ROW):
                            html.Span([B("d.where")], style={"fontFamily": MONO, "marginRight": "6px"})
                            html.Span([B("d.fact")])
            with html.Div(style={"display": "flex", "flexDirection": "column", "gap": "12px"}):
                for _ in section("Suggested reviewers", "br.reviewers", "br.measured.reviewers"):
                    with react.For(items="br.reviewers", name="s"):
                        with html.Div(key=B("s.user"), style=ROW):
                            with html.Div(style={"display": "flex", "gap": "6px", "alignItems": "center"}):
                                html.Span([B("s.user")], style={"fontWeight": 600})
                                with react.If(value="s.reviewed"):
                                    pill("'reviewed it'", "#1A7F37", "#E6F4EA")
                            html.Div([B("s.reason")], style=SMALL)
                for _ in section("Conventions reviewers asked for on these files", "br.conventions",
                                 "br.measured.conventions"):
                    with react.If(value="!br.conventions.length"):
                        html.Div("No earlier review comments on these files or directories.", style=SMALL)
                    with react.For(items="br.conventions", name="r"):
                        with html.Div(key=B("r.key"), style=ROW):
                            with html.Div(style={"display": "flex", "gap": "6px", "alignItems": "baseline"}):
                                html.Span([B("r.level")], style={
                                    "fontSize": "0.72rem", "borderRadius": "8px", "padding": "0 6px",
                                    "color": B(f"{LEVEL_FG}[r.level] || '{MUTED}'"),
                                    "background": B(f"{LEVEL_BG}[r.level] || '#EEF1F5'")})
                                html.Span([B("r.rule")])
                            html.Div([B("r.id + ': ' + r.detail")], style=SMALL)
                for _ in section("Recent changes to the most-changed files", "br.files", "br.measured.files"):
                    with react.For(items="br.files", name="f"):
                        with html.Div(key=B("f.key"), style=ROW):
                            html.Div([B("f.name")], title=B("f.path"), style={"fontFamily": MONO, "fontWeight": 500})
                            with react.If(value="!f.commits.length"):
                                html.Div("New file.", style={**SMALL, "paddingLeft": "12px"})
                            with react.For(items="f.commits", name="c"):
                                with html.Div(key=B("c.sha"), style={**SMALL, "paddingLeft": "12px"}):
                                    link("c.sha", "c.url")
                                    html.Span([" ", B("c.date"), " ", B("c.who"), ": ", B("c.subject")])


# ----------------------------------------------------------------------------- Labels

NO_FIT = "no label fits"


def label_summary():
    ev = store.area_eval or {}
    b = ev.get("backfill")
    if not b:
        return {}
    split = {x["confidence_at_least"]: x for x in ev["time_split"]["by_confidence"]}
    pct = lambda x: f"{x:.0%}" if x is not None else ""
    accuracy = [{"conf": f"{x['confidence_at_least']:.1f}", "cutoff": x["confidence_at_least"] == ev["cutoff"],
                 "backfill": f"{pct(x['precision'])} of {x['issues']}",
                 "new": f"{pct(split[x['confidence_at_least']]['precision'])} of "
                        f"{split[x['confidence_at_least']]['issues']}"} for x in ev["by_confidence"]]
    dirs = [{"dir": d, "mrs": v["mrs"], "share": f"{v['with_area_label'] / v['mrs']:.0%}"}
            for d, v in ev["directories"].items()]
    after, open_after = b["labeled_now"] + b["added"], b["open_labeled_now"] + b["open_added"]
    return {
        "now": f"{b['labeled_now']:,} of {b['issues']:,} issues ({b['labeled_now'] / b['issues']:.0%}) carry an area "
               f"label; {b['open_labeled_now']} of {b['open']:,} open issues ({b['open_labeled_now'] / b['open']:.0%}).",
        "after": f"Applying every suggestion at or above the cutoff ({ev['cutoff']}) adds {b['added']:,} labels: "
                 f"{after:,} issues ({after / b['issues']:.0%}) and {open_after} open issues "
                 f"({open_after / b['open']:.0%}) would carry one.",
        "wrong": f"From the accuracy measured at each confidence level, about {b['expected_wrong']} of the added labels "
                 f"would be wrong. {ev['suggestions']['no_fit']:,} issues ({ev['suggestions']['open_no_fit']} open) "
                 f"stay unlabeled as “{NO_FIT}”.",
        "by_label": b["by_label"], "accuracy": accuracy, "dirs": dirs,
        "cutoff": ev["cutoff"], "target": f"{ev['target']:.0%}", "split": ev["time_split"]["split"][:4],
    }


state.update({"lb_state": "opened", "lb_label": "", "lb_min": "", "lb_search": "", "lb_rows": [], "lb_shown": "",
              "lb_summary": label_summary(), "lb_states": [{"title": "Open", "value": "opened"},
                                                          {"title": "Closed", "value": "closed"}],
              "lb_labels": options([NO_FIT] + sorted({r["suggested"] for r in store.area_rows} - {NO_FIT})),
              "lb_iid": "", "lb_lookup": None, "lb_busy": False, "lb_error": ""})


@state.change("lb_state", "lb_label", "lb_min", "lb_search")
def refresh_labels(**_):
    try:
        low = float(state.lb_min) if (state.lb_min or "").strip() else 0.0
    except ValueError:
        low = 0.0
    needle = (state.lb_search or "").lower().strip()
    rows = [r for r in store.area_rows
            if (not state.lb_state or r["state"] == state.lb_state)
            and (not state.lb_label or r["suggested"] == state.lb_label)
            and r["confidence"] >= low and (not needle or needle in r["title"].lower())]
    state.lb_rows = [dict(r, key=r["issue"], fits=r["suggested"] != NO_FIT,
                          expected=f"{r['expected_precision']:.0%}") for r in rows[:MAX_ROWS]]
    state.lb_shown = f"{len(rows):,} issues" + (f", the first {MAX_ROWS} shown" if len(rows) > MAX_ROWS else "")


def lookup_label(ref=None):
    ref = str(ref if ref is not None else state.lb_iid).strip()
    if not ref.lstrip("#!").isdigit() or state.lb_busy:
        return
    asynchronous.create_task(lookup_task(ref))


async def lookup_task(iid):
    with state:
        state.lb_busy, state.lb_error = True, ""
    try:
        found = await asyncio.get_running_loop().run_in_executor(None, store.suggest_labels, iid)
        with state:
            state.lb_lookup, state.lb_error = (None, found["error"]) if "error" in found else (found, "")
    except OSError as e:
        with state:
            state.lb_error = f"The suggestion needs the DGX Spark for issues outside the index and could not reach it: {e}"
    finally:
        with state:
            state.lb_busy = False


def lookup_key(key, value):
    if key == "Enter":
        lookup_label(value)


def small_table(columns, items, name, cells):
    with mui.Table(size="small"):
        head(*columns)
        with mui.TableBody():
            with react.For(items=items, name=name):
                with mui.TableRow(key=B(cells[0][0])):
                    for expr, style in cells:
                        mui.TableCell([B(expr)], style=style)


def labels_view():
    caption("Suggested area labels for VTK issues that have none, from the most similar labeled issues and "
            "merge requests, the files changed by merge requests that link the issue, and the issue template's "
            "Language and Graphics backend lines. The lookup also takes a merge request, using the directories it "
            "changes. Nothing is applied on GitLab from here.", marginBottom="10px")
    with react.If(value="!lb_summary.now"):
        mui.Alert("Run python triage/area_labels.py to create the suggestions.", severity="info")
    with react.If(value="lb_summary.now"):
        with html.Div(style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(420px, 1fr))",
                             "gap": "12px", "alignItems": "start", "marginBottom": "12px"}):
            for _ in section("Backfill simulation", "lb_summary.by_label",
                             "'What the issue tracker would look like with the suggestions applied'"):
                for key in ("now", "after", "wrong"):
                    html.Div([B(f"lb_summary.{key}")], style={"margin": "4px 0", "fontSize": "0.88rem"})
                with html.Div(style={"maxHeight": "260px", "overflowY": "auto", "marginTop": "6px"}):
                    small_table([("Label", None), ("Now", 60, "Issues carrying it today"),
                                 ("Added", 70, "Issues the backfill would label with it"),
                                 ("After", 60)], "lb_summary.by_label", "b",
                                [("b.label", {"fontFamily": MONO}), ("b.now", {}),
                                 ("b.added", {"color": ACCENT, "fontWeight": 500}), ("b.after", {})])
            with html.Div(style={"display": "flex", "flexDirection": "column", "gap": "12px"}):
                for _ in section("How accurate the suggestions were", "lb_summary.accuracy",
                                 "'Tested on issues maintainers already labeled. Backfill: each labeled issue treated "
                                 "as unlabeled. New issues: only labels from before ' + lb_summary.split + ', tested on "
                                 "issues filed since. The cutoff is the lowest confidence where both reach ' + "
                                 "lb_summary.target + '.'"):
                    with mui.Table(size="small"):
                        head(("Confidence at least", None), ("Backfill test: right", None),
                             ("New-issue test: right", None))
                        with mui.TableBody():
                            with react.For(items="lb_summary.accuracy", name="a"):
                                with mui.TableRow(key=B("a.conf"), selected=B("a.cutoff")):
                                    mui.TableCell([B("a.conf"), B("a.cutoff ? ' (cutoff)' : ''")])
                                    mui.TableCell([B("a.backfill")])
                                    mui.TableCell([B("a.new")])
                for _ in section("Code areas without a label", "lb_summary.dirs",
                                 "'Merge requests that changed each top-level directory, and the share carrying any "
                                 "area label. Issues in the low-share areas often end up as “no label fits”.'"):
                    with html.Div(style={"maxHeight": "200px", "overflowY": "auto"}):
                        small_table([("Directory", None), ("MRs", 70), ("With an area label", 130)],
                                    "lb_summary.dirs", "d", [("d.dir", {"fontFamily": MONO}), ("d.mrs", {}),
                                                             ("d.share", {})])
    with bar():
        field("Issue or MR", "lb_iid", 130, on_enter=lookup_key,
              tip="An issue (#123, or just 123) or a merge request (!123); press Enter to see its suggested labels. "
                  "A plain number that is not an issue is looked up as a merge request")
        with tipped("Suggest labels for this issue; the first lookup takes a few seconds to load the history"):
            mui.Button("Suggest", size="small", variant="contained", loading=B("lb_busy"),
                       on_click=C(lookup_label, "[lb_iid]"))
        with react.If(value="lb_error"):
            html.Span([B("lb_error")], style={"color": "#bc4c00", "fontSize": "0.85rem"})
    with react.If(value="lb_lookup"):
        with html.Div(style={**CARD, "margin": "0 0 12px"}):
            with html.Div(style={"display": "flex", "gap": "8px", "alignItems": "baseline", "flexWrap": "wrap"}):
                link("lb_lookup.ref", "lb_lookup.url")
                html.Span([B("lb_lookup.title")], style={"fontWeight": 500})
                html.Span([B("lb_lookup.kind + ', ' + lb_lookup.state")], style=SMALL)
            html.Div([B("'Suggested: ' + lb_lookup.suggested + ' (confidence ' + lb_lookup.confidence + ', cutoff ' "
                        "+ lb_lookup.cutoff + ')'")], style={"marginTop": "6px", "fontWeight": 600})
            html.Div([B("'Ranked: ' + lb_lookup.ranked.map(r => r.label + ' ' + r.share).join(', ')")], style=SMALL)
            with react.If(value="lb_lookup.lang.length"):
                html.Div([B("'From the template: ' + lb_lookup.lang.join(', ')")], style=SMALL)
            with react.If(value="lb_lookup.linked.length"):
                html.Div([B("'Linked MRs: ' + lb_lookup.linked.join(' ')")], style=SMALL)
            with react.If(value="lb_lookup.dirs.length"):
                html.Div([B("'Changes: ' + lb_lookup.dirs.join(', ')")], style=SMALL)
            html.Div([B("'Labels on GitLab now: ' + (lb_lookup.labels.join(', ') || 'none')")], style=SMALL)
    with bar():
        select("State", "lb_state", "lb_states", 110, tip="Open or closed issues; empty shows both")
        select("Suggested label", "lb_label", "lb_labels", 200,
               tip="Only issues with this suggestion, or the ones marked “no label fits”")
        field("Min confidence", "lb_min", 130, tip="Only suggestions at or above this confidence, from 0 to 1")
        field("Filter titles", "lb_search", tip="Show issues whose title contains these words")
        html.Span([B("lb_shown")], style={"color": MUTED, "fontSize": "0.85rem"})
    cell = {"verticalAlign": "top"}
    with table(330), mui.Table(size="small", sticky_header=True):
        head(("Issue", 70), ("Title", None), ("State", 70), ("Created", 95),
             ("Suggested", 170, "The closest label when its confidence reaches the cutoff; otherwise "
                                "“no label fits” with the best guess below it"),
             ("Confidence", 90, "Share of the evidence's votes that went to the top label"),
             ("Measured", 85, "How often suggestions at this confidence were right on labeled issues"),
             ("Evidence", 110, "text: similar labeled issues and MRs; files: files changed by linked MRs; "
                              "mr: labels on linked MRs; field: the issue template"),
             ("Linked MRs", 110))
        with mui.TableBody():
            with react.For(items="lb_rows", name="r"):
                with mui.TableRow(key=B("r.key"), hover=True):
                    with mui.TableCell(style=cell):
                        link("'#' + r.issue", "r.url")
                    mui.TableCell([B("r.title")], style=cell)
                    mui.TableCell([B("r.state")], style=cell)
                    mui.TableCell([B("r.created")], style={**cell, "whiteSpace": "nowrap"})
                    with mui.TableCell(style=cell):
                        with react.If(value="r.fits"):
                            pill("r.suggested", ACCENT, ACCENT_TINT)
                        with react.If(value="!r.fits"):
                            pill("r.suggested", MUTED, "#EEF1F5")
                            html.Div([B("'best guess ' + r.best_guess")], style=SMALL)
                    mui.TableCell([B("r.confidence")], style=cell)
                    mui.TableCell([B("r.expected")], style=cell)
                    mui.TableCell([B("r.evidence")], style={**cell, **SMALL})
                    mui.TableCell([B("r.linked_mrs")], style={**cell, **SMALL})


# ----------------------------------------------------------------------------- Layout

with MuiLayout(server, theme=THEME) as layout:
    mui.GlobalStyles(styles=f"@import url('{FONTS}'); body {{ background: {CANVAS}; }}")
    with html.Div(style={"display": "flex", "flexDirection": "column", "height": "100vh", "background": CANVAS}):
        with html.Header(style={"background": SURFACE, "borderBottom": f"1px solid {LINE}", "position": "relative"}):
            with html.Div(style={"display": "flex", "alignItems": "center", "height": "52px",
                                 "padding": "0 20px", "gap": "28px"}):
                with html.Div(style={"display": "flex", "alignItems": "baseline", "gap": "8px"}):
                    html.Span("VTK review history", style={"fontWeight": 600, "fontSize": "1.05rem",
                                                           "color": INK, "letterSpacing": "-0.01em"})
                    html.Span("from GitLab and Discourse", style={"color": MUTED, "fontSize": "0.8rem"})
                with html.Nav(style={"display": "flex", "gap": "4px", "height": "100%"}):
                    for value, label, tip in TABS:
                        with tipped(tip, "bottom"):
                          html.Button(label, on_click=C(f"tab = '{value}'"), style={
                            "border": "none", "background": "none", "cursor": "pointer", "fontFamily": SANS,
                            "fontSize": "0.9rem", "padding": "0 12px", "height": "100%",
                            "fontWeight": B(f"tab === '{value}' ? 600 : 500"),
                            "color": B(f"tab === '{value}' ? '{INK}' : '{MUTED}'"),
                            "borderBottom": B(f"tab === '{value}' ? '2px solid {ACCENT}' : '2px solid transparent'"),
                        })
            mui.LinearProgress(style={"position": "absolute", "left": 0, "right": 0, "bottom": "-1px", "height": "2px",
                                      "visibility": B("trame__busy ? 'visible' : 'hidden'")})
        with html.Main(style={"flex": "1", "overflow": "auto", "padding": "16px 20px"}):
            for value, view in (("briefing", briefing_view), ("review", review_view), ("rules", rules_view),
                                ("deprecations", deprecations_view), ("trends", trends_view),
                                ("labels", labels_view), ("search", search_view)):
                with react.If(value=f"tab === '{value}'"):
                    view()

refresh_rules()
refresh_labels()
on_dep_filters(state.dep_outcome, state.dep_search)
on_trend_filters(state.trend_what, state.trend_source, state.trend_kind, state.trend_common)

if __name__ == "__main__":
    server.start(timeout=0)
