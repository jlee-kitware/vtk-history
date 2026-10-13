"""Data the app shows: review rules with curation, deprecations, trends, and search.

Curation decisions live in rules/curated.json, which is tracked in git so every accept,
edit, or reject is reviewable. A rule is keyed by a hash of its supporting threads, so a
decision stays attached to the same evidence when rules are regenerated and renumbered.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402
import getpass
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "deprecations"))
sys.path.insert(0, str(ROOT / "index"))
from check_rules import conflicts, load_index  # noqa: E402

GITLAB = "https://gitlab.kitware.com/vtk/vtk/-"
DISCOURSE = "https://discourse.vtk.org/t"
CURATED = ROOT / "rules" / "curated.json"
DECISIONS = ("accepted", "edited", "rejected")


def mr_url(iid):
    return f"{GITLAB}/merge_requests/{iid}" if iid else None


def rule_key(rule):
    return hashlib.sha1("|".join(sorted(rule["members"])).encode()).hexdigest()[:12]


class Store:
    def __init__(self, repo=config.VTK_REPO):
        self.repo = repo
        self.rules = json.loads((ROOT / "data/rules_verified.json").read_text())["rules"]
        self.by_symbol = load_index(ROOT / "data/deprecations/index.jsonl")
        self.deprecations = [r for recs in self.by_symbol.values() for r in recs]
        self.curated = json.loads(CURATED.read_text()) if CURATED.exists() else {}
        for i, r in enumerate(self.rules, 1):
            r.setdefault("id", f"R{i:03d}")
            r["key"] = rule_key(r)
            r["conflicts"] = conflicts(r, self.by_symbol, repo)
        confidence = self._json("data/rules_confidence.json") or {"rules": {}}
        self.confidence = confidence["rules"]
        self.baseline_follow = confidence.get("baseline_follow")
        docs = (self._json("data/doc_rules.json") or {"rules": []})["rules"]
        doc_only = set((self._json("data/doc_match.json") or {"doc_only": []})["doc_only"])
        self.doc_rules = [dict(d, key=f"doc-{d['id']}") for d in docs if d["id"] in doc_only]
        self.terms = self._json("data/trends/terms-v2/terms.json")
        self.themes = self._json("data/trends/k250/themes.json")
        self._index = None

    def _json(self, rel):
        path = ROOT / rel
        return json.loads(path.read_text()) if path.exists() else None

    @property
    def index(self):
        if self._index is None:
            from search import Index
            self._index = Index(str(ROOT / "data/index"))
        return self._index

    def rule_rows(self):
        rows = []
        for r in self.rules:
            c = self.curated.get(r["key"], {})
            conf = self.confidence.get(r["key"], {})
            rows.append({"id": r["id"], "key": r["key"], "rule": c.get("rule") or r["rule"] or "", "topic": r["topic"],
                         "mrs": r["support_mrs"], "reviewers": len(r["reviewers"]), "last": r["last_seen"],
                         "decision": c.get("decision", "undecided"), "mixed": bool(r.get("counter_examples")),
                         "deprecated": bool(r["conflicts"]), "level": conf.get("level", "medium"),
                         "score": conf.get("score", 0), "reason": conf.get("reason", ""),
                         "guide_conflict": (conf.get("doc") or {}).get("verdict") == "contradicts"
                         or (conf.get("tool") or {}).get("verdict") == "contradicts",
                         "automated": conf.get("automated", False),
                         "automatable": bool(conf.get("automatable"))})
        for d in self.doc_rules:
            c = self.curated.get(d["key"], {})
            rows.append({"id": d["id"], "key": d["key"], "rule": c.get("rule") or d["rule"], "topic": "developer guide",
                         "mrs": 0, "reviewers": 0, "last": "", "decision": c.get("decision", "undecided"),
                         "mixed": False, "deprecated": False, "level": "documented", "score": 0,
                         "guide_conflict": False, "automated": False, "automatable": False,
                         "reason": f"Stated in the developer guide ({d['file']}, {d['section'] or 'top'}); "
                                   "not raised in the reviews we mined"})
        rank = {"high": 0, "medium": 1, "low": 2, "documented": 3}
        return sorted(rows, key=lambda x: (rank[x["level"]], -x["score"], -x["mrs"]))

    def doc_detail(self, d):
        c = self.curated.get(d["key"], {})
        return {
            "confidence": [{"name": "Developer guide", "detail": f"\u201c{d['quote']}\u201d", "points": "",
                            "tone": "good"}],
            "level": "documented", "reason": "", "id": d["id"], "key": d["key"], "draft": d["rule"],
            "rule": c.get("rule") or d["rule"], "rationale": "", "topic": "developer guide",
            "scope": f"{d['file']}, {d['section'] or 'top'} ({'required' if d['strength'] == 'must' else 'preferred'})",
            "support": "Stated in the VTK developer guide; no review comments found for it",
            "reviewers": "", "examples": [], "counter": [], "conflicts": [], "doc_url": d["url"],
            "doc_file": d["file"], "decision": c.get("decision", "undecided"), "note": c.get("note", ""),
            "decided_by": c.get("by", ""), "decided_at": c.get("at", ""),
        }

    def rule_detail(self, key):
        d = next((x for x in self.doc_rules if x["key"] == key), None)
        if d:
            return self.doc_detail(d)
        r = next((x for x in self.rules if x["key"] == key), None)
        if not r:
            return None
        c = self.curated.get(key, {})
        evidence = lambda es: [{"mr": e["mr"], "url": e.get("url") or mr_url(e["mr"]), "reviewer": e["reviewer"],
                                "date": e["date"], "text": " ".join(e["evidence"].split())[:600]} for e in es]
        conf = self.confidence.get(key, {})
        return {
            "confidence": self.factors(conf),
            "level": conf.get("level", "medium"), "reason": conf.get("reason", ""),
            "id": r["id"], "key": key, "draft": r["rule"] or "", "rule": c.get("rule") or r["rule"] or "",
            "rationale": r.get("rationale") or "", "scope": r.get("scope") or "", "topic": r["topic"],
            "support": f"{r['support_mrs']} MRs, {r['support_threads']} threads, {r['first_seen']} to {r['last_seen']}",
            "reviewers": ", ".join(f"{n} ({k})" for n, k in r["reviewers"][:6]),
            "examples": evidence(r["examples"]), "counter": evidence(r.get("counter_examples") or []),
            "conflicts": [self.deprecation_row(d) for d in r["conflicts"]],
            "doc_url": (conf.get("doc") or {}).get("url"), "doc_file": (conf.get("doc") or {}).get("file"),
            "decision": c.get("decision", "undecided"), "note": c.get("note", ""),
            "decided_by": c.get("by", ""), "decided_at": c.get("at", ""),
        }

    def factors(self, conf):
        if not conf:
            return []
        e, a = conf.get("estimate"), conf.get("adjusted")
        if a:
            follow = (f"Authors acted on {a['k']} of {a['n']} line comments. Comments of the same form from the same "
                      f"reviewers are acted on {a['expected']:.0%} of the time; this rule's comments, adjusted for "
                      f"that, {a['adjusted']:.0%} (90% range {a['lo']:.0%} to {a['hi']:.0%}). "
                      f"{a['p_above']:.0%} chance the rule itself raises follow-through. Unadjusted estimate: "
                      f"{e['mean']:.0%} ({e['lo']:.0%} to {e['hi']:.0%}).")
        elif e and e["n"]:
            follow = (f"Authors acted on an estimated {e['mean']:.0%} (90% range {e['lo']:.0%} to {e['hi']:.0%}), "
                      f"from {e['k']} of {e['n']} line comments; {e['p_above']:.0%} chance this beats the "
                      f"{self.baseline_follow:.0%} average for all line comments")
        elif e:
            follow = (f"No line comments to measure, so the estimate is the {e['mean']:.0%} typical for rules, "
                      f"with a wide range ({e['lo']:.0%} to {e['hi']:.0%})")
        else:
            follow = "Not estimated"
        tone = {"high": 1, "low": -1}.get(conf.get("level"), 0)
        rows = [
            ("Follow-through", follow, tone),
            ("Reviewers", f"{conf['reviewers']} different reviewers asked for this", None),
            ("Objections", f"{conf['objections']} ({conf['objection_share']:.0%} of the discussion)"
             + (", including one newer than the latest support" if conf["newer_objection"] else ""),
             -1 if conf["objections"] else None),
            ("Consistency", "Supporting comments agree" if conf["consistent"]
             else "Verification found some supporting comments that differ", None if conf["consistent"] else -1),
        ]
        doc = conf.get("doc")
        if doc and doc["verdict"] == "same":
            rows.append(("Developer guide", f"Stated in {doc['file']}: \u201c{doc['quote']}\u201d", 1))
        elif doc:
            rows.append(("Developer guide", f"Conflicts with {doc['file']}: \u201c{doc['quote']}\u201d "
                                            f"({doc['why']}) Decide whether the rule is wrong or stated too broadly.",
                         -1))
        tool, auto = conf.get("tool"), conf.get("automatable")
        if tool and tool["verdict"] == "same":
            rows.append(("Tools", f"Enforced by {tool['tool']} ({tool['check']}): {tool['evidence']}. The agent "
                                  "leaves this to the tool.", 1))
        elif tool:
            rows.append(("Tools", f"Conflicts with {tool['tool']} ({tool['check']}: {tool['evidence']}): "
                                  f"{tool['why']} The agent follows the tool and does not use this rule, "
                                  "and the level is low.", -1))
        if auto:
            rows.append(("Could automate", f"clang-tidy check {auto['check']} would enforce this; VTK has it off. "
                                           f"{auto['rule']}", None))
        if conf["deprecated_api"]:
            rows.append(("Deprecated APIs", "Names an API VTK has deprecated or removed, so the level is low", None))
        return [{"name": n, "detail": d, "points": "",
                 "tone": "neutral" if not v else "good" if v > 0 else "bad"} for n, d, v in rows]

    def decide(self, key, decision, rule_text, note, who=None):
        r = next((x for x in self.rules if x["key"] == key), None) or next(
            dict(x, topic="developer guide", scope=x["file"], support_mrs=0) for x in self.doc_rules if x["key"] == key)
        if decision == "undecided":
            self.curated.pop(key, None)
        else:
            edited = rule_text.strip() != (r["rule"] or "").strip()
            self.curated[key] = {
                "decision": "edited" if decision == "accepted" and edited else decision,
                "rule": rule_text.strip() if edited else None, "draft": r["rule"], "note": note.strip(),
                "topic": r["topic"], "scope": r.get("scope"), "support_mrs": r["support_mrs"],
                "by": who or getpass.getuser(), "at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            }
        CURATED.parent.mkdir(exist_ok=True)
        CURATED.write_text(json.dumps(self.curated, indent=1, ensure_ascii=False, sort_keys=True) + "\n")
        return self.curated.get(key, {}).get("decision", "undecided")

    @staticmethod
    def deprecation_row(d):
        dep, rem = d["deprecated"], d["removed"]
        return {"api": f"{d['class']}::{d['symbol']}", "version": d["version"], "outcome": d["outcome"],
                "reason": d["reason"] or "", "file": d["file"], "declaration": d["declaration"][:160],
                "deprecated_on": dep["date"], "deprecated_mr": dep["mr"], "deprecated_url": mr_url(dep["mr"]),
                "removed_on": rem["date"] if rem else "", "removed_mr": rem["mr"] if rem else None,
                "removed_url": mr_url(rem["mr"]) if rem else None}

    def deprecation_rows(self):
        rows = [self.deprecation_row(d) for d in self.deprecations]
        return sorted(rows, key=lambda r: r["deprecated_on"], reverse=True)

    @staticmethod
    def example_url(source, doc_id):
        return mr_url(doc_id) if source == "mr" else f"{DISCOURSE}/{doc_id}"

    def trend_rows(self, what, source, kind, common=False):
        if what == "terms":
            data = (self.terms or {}).get(source)
            if not data:
                return [], [], []
            ranked = data["ranked"].get(kind + (" (common English words)" if common else ""), [])
            rows = [{"name": r["token"], "ratio": r["ratio"], "docs": r["docs"], "first_seen": r["first_seen"],
                     "peak": r["peak"], "series": r["series"], "examples": r.get("examples", [])} for r in ranked]
            return rows, data["quarters"], data["documents_per_quarter"]
        data = (self.themes or {}).get("sources", {}).get(source)
        if not data:
            return [], [], []
        scores = sorted((s for s in data["scores"].values() if s["kind"] == kind), key=lambda s: -s["score"])[:40]
        rows = []
        for s in scores:
            theme = self.themes["themes"][s["token"].split(":")[1]]
            rows.append({"name": theme["name"] or f"theme {theme['id']}", "ratio": s["ratio"], "docs": s["docs"],
                         "first_seen": s["first_seen"], "peak": s["peak"], "series": s["series"],
                         "description": theme.get("description") or "",
                         "examples": [dict(e, source=source) for e in theme["examples"][source]]})
        return rows, data["quarters"], data["documents_per_quarter"]

    def search(self, query, kind=None, since=None, until=None, k=25):
        rows = []
        for h in self.index.search_mixed(query, k=k, kind=kind or None, since=since or None, until=until or None):
            ref = h["ref"]
            if ref.startswith("!"):
                url = mr_url(ref[1:])
            elif ref.startswith("#"):
                url = f"{GITLAB}/issues/{ref[1:]}"
            else:
                url = h["url"]
            label = ("blog post" if h["kind"] == "blog" else ref.rsplit("/", 1)[-1] if "/" in ref else ref)
            rows.append({"kind": h["kind"], "ref": ref, "label": label, "date": h["date"], "author": h["author"] or "",
                         "title": h["title"] or "", "path": h["path"] or "", "url": url,
                         "snippet": " ".join((h["text"] or "").split())[:400],
                         "topic": int(ref.split()[1]) if h["kind"] == "post" and ref.startswith("topic ") else None,
                         "other_kind": bool(h.get("other_kind"))})
        return rows
