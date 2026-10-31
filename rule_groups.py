"""Mined rules that ask for the same thing (data/rule_groups.json, from rules/merge_rules.py).

Each group lists its rule ids with the one raised in the most merge requests first; that one is canonical.
"""

import json
from pathlib import Path

GROUPS = Path(__file__).resolve().parent / "data/rule_groups.json"


def canonical_ids(path=GROUPS):
    """Map each grouped rule id to its group's canonical id."""
    if not path.exists():
        return {}
    return {rid: group[0] for group in json.loads(path.read_text())["groups"] for rid in group}
