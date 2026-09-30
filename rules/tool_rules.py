#!/usr/bin/env python3
"""Collect the rules VTK's tools enforce, and the clang-tidy checks VTK leaves off.

Sources, all read from the VTK clone at --ref and the MR mirror:
  clang-tidy    every check clang-tidy knows, marked enabled when VTK's .clang-tidy turns it on (listed by
                the clang-tidy binary), each stated as a rule by the model; plus the functions VTK bans
                through bugprone-unsafe-functions, with their VTK replacements
  clang-format  the settings in .clang-format that decide how code looks
  ghostflow     the checks the GitLab robot (kwrobot) runs on every MR, counted from its messages
  codespell and editorconfig

Writes data/tool_rules.json.

Usage:
  python rules/tool_rules.py
"""

import argparse
import glob
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "rules"))
from doc_rules import ask  # noqa: E402

BLOB = "https://gitlab.kitware.com/vtk/vtk/-/blob/master/"
CLANG_TIDY = str(Path.home() / ".local/bin/clang-tidy")
BATCH = 25

TIDY_PROMPT = """Each line below is a clang-tidy check name. For each, state in one imperative sentence the
coding rule the check enforces, as a C++ reviewer would say it. Use what you know of the check; if you do
not know a check, give your best reading of its name.

Reply with JSON only: {{"rules": {{"<check name>": "<rule>", ...}}}}

{names}"""

FORMAT_RULES = {
    "BreakBeforeBraces": {"Allman": "Put opening braces on their own line, below the statement (Allman style)."},
    "ColumnLimit": lambda v: f"Keep lines to {v} columns or fewer.",
    "BasedOnStyle": {"Mozilla": "Indent with two spaces (Mozilla base style)."},
    "AlignAfterOpenBracket": {"DontAlign": "Do not align arguments after an open bracket; use continuation indent."},
    "AlwaysBreakAfterReturnType": {"None": "Keep the return type on the same line as the function name."},
    "AlwaysBreakAfterDefinitionReturnType": {"None": "Keep the return type on the same line as the function name "
                                                     "in definitions."},
    "BinPackArguments": {True: "Pack function call arguments onto as few lines as fit."},
    "BinPackParameters": {True: "Pack function parameters onto as few lines as fit."},
    "SpaceAfterTemplateKeyword": {True: "Put a space after the template keyword."},
    "Standard": lambda v: f"Format for the {v} standard.",
}

GHOSTFLOW = [
    ("changelog", r"consider adding a changelog entry",
     "Add a release note (changelog entry) under Documentation/release/dev for user-visible changes."),
    ("format", r"not formatted according to the '[\w-]+' check",
     "Format every changed file with the project's clang-format (and other formatters) before pushing."),
    ("whitespace", r"adds bad whitespace", "Do not add trailing whitespace, tabs, or whitespace errors."),
    ("wip", r"marked as a work-in-progress", "Remove the work-in-progress (draft) status before merging."),
    ("fixup", r"marked as a fixup commit", "Squash fixup commits before merging."),
    ("root", r"it is a root commit", "Do not push root commits; base the branch on master."),
    ("maintained", r"file is maintained", "Do not edit third-party files that are maintained upstream; update them "
                                           "through their import scripts."),
    ("subject", r"first line must be no longer than", "Keep the commit subject line to 78 characters or fewer."),
    ("author", r"has no space in it", "Commit under your full name."),
]

OTHER = [
    ("codespell", ".codespellrc", "Spell words in code, comments, and docs correctly (codespell)."),
    ("editorconfig", ".editorconfig", "End every file with a newline and use UTF-8."),
    ("editorconfig", ".editorconfig", "Do not leave trailing whitespace (except in Markdown)."),
    ("editorconfig", ".editorconfig", "Indent with spaces: two per level, four in Python."),
]


def show(repo, ref, path):
    return subprocess.check_output(["git", "-C", repo, "show", f"{ref}:{path}"], text=True)


def list_checks(config=None):
    Path("/tmp/tool_rules_empty.cxx").write_text("int main() {}\n")
    args = [CLANG_TIDY, "--list-checks", "/tmp/tool_rules_empty.cxx", "--"]
    args[1:1] = [f"--config-file={config}"] if config else ["--checks=*"]
    out = subprocess.run(args, capture_output=True, text=True).stdout
    return [line.strip() for line in out.splitlines()[1:] if line.strip()]


def tidy_rules(repo, ref, model):
    config = Path("/tmp/vtk.clang-tidy")
    text = show(repo, ref, ".clang-tidy")
    config.write_text(text)
    enabled, every = set(list_checks(config)), list_checks()
    stated = {}
    for i in range(0, len(every), BATCH):
        names = every[i:i + BATCH]
        stated.update((ask(model, TIDY_PROMPT.format(names="\n".join(names))) or {}).get("rules") or {})
        print(f"  stated {min(i + BATCH, len(every))}/{len(every)} checks", flush=True)
    rules = [{"tool": "clang-tidy", "check": c, "enabled": c in enabled, "rule": stated.get(c) or c,
              "evidence": ".clang-tidy enables it" if c in enabled else "not enabled in .clang-tidy",
              "url": f"https://clang.llvm.org/extra/clang-tidy/checks/{c.split('-', 1)[0]}/{c.split('-', 1)[1]}.html"}
             for c in every]
    options = yaml.safe_load(text).get("CheckOptions") or []
    custom = next((o["value"] for o in options if o["key"].endswith("unsafe-functions.CustomFunctions")), "")
    for line in custom.splitlines():
        parts = [p.strip() for p in line.rstrip(";").split(",")]
        if len(parts) >= 3:
            functions = parts[0].strip("^$()").replace("|", ", ")
            rules.append({"tool": "clang-tidy", "check": "bugprone-unsafe-functions", "enabled": True,
                          "rule": f"Use {parts[1]} instead of {functions}; they {parts[2].replace('is ', '', 1)}.",
                          "evidence": f".clang-tidy CheckOptions: {line.strip()}", "url": BLOB + ".clang-tidy"})
    return rules


def format_rules(repo, ref):
    config = yaml.safe_load(show(repo, ref, ".clang-format"))
    rules = []
    for key, spec in FORMAT_RULES.items():
        if key not in config:
            continue
        value = config[key]
        rule = spec(value) if callable(spec) else spec.get(value)
        if rule:
            rules.append({"tool": "clang-format", "check": key, "enabled": True, "rule": rule,
                          "evidence": f".clang-format: {key}: {value}", "url": BLOB + ".clang-format"})
    return rules


def ghostflow_rules():
    counts = Counter()
    for f in glob.glob(str(ROOT / "data/vtk-history/merge_requests/*.json")):
        for d in json.load(open(f)).get("discussions") or []:
            for n in d["notes"]:
                if n["author"]["username"] != "kwrobot":
                    continue
                for name, pattern, _ in GHOSTFLOW:
                    if re.search(pattern, n["body"]):
                        counts[name] += 1
    return [{"tool": "ghostflow", "check": name, "enabled": True, "rule": rule, "flagged": counts[name],
             "evidence": f"the GitLab robot flagged this on {counts[name]} MR comments",
             "url": "https://gitlab.kitware.com/utils/ghostflow-director"} for name, _, rule in GHOSTFLOW]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="/home/jlee/gitsync/vtk")
    ap.add_argument("--ref", default="upstream/master")
    ap.add_argument("--model", default="qwen3-coder-next:q4_K_M")
    args = ap.parse_args()
    rules = format_rules(args.repo, args.ref) + ghostflow_rules()
    rules += [{"tool": t, "check": t, "enabled": True, "rule": r, "evidence": f"{src} in the VTK repository",
               "url": BLOB + src} for t, src, r in OTHER]
    rules += tidy_rules(args.repo, args.ref, args.model)
    for i, r in enumerate(rules, 1):
        r["id"] = f"T{i:03d}"
    (ROOT / "data/tool_rules.json").write_text(json.dumps({"rules": rules}, indent=1))
    by_tool = Counter((r["tool"], r["enabled"]) for r in rules)
    print(f"{len(rules)} tool rules: " + ", ".join(f"{t} {'on' if e else 'off'}: {n}" for (t, e), n in sorted(by_tool.items())))


if __name__ == "__main__":
    main()
