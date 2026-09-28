#!/usr/bin/env python3
"""Build the code-entity layer of the VTK ontology from a VTK source tree.

Writes ontology/entities.json with:

  modules   name -> directory, description, kit, groups, depends, private_depends,
            third_party, classes
  classes   name -> module, header, base, ancestors (nearest first)

Classes are found by VTK's one-class-per-header convention: a header vtkFoo.h that
declares class vtkFoo. Use module_for_path() to map a source path to its module.

Usage:
  python ontology/build_entities.py --vtk /home/jlee/gitsync/vtk
"""

import argparse
import json
import re
import subprocess
from pathlib import Path

LIST_KEYS = {"GROUPS", "DEPENDS", "PRIVATE_DEPENDS", "OPTIONAL_DEPENDS", "TEST_DEPENDS", "KIT"}
CLASS_DECL = re.compile(r"^\s*class\s+(?:[A-Z0-9_]+\s+)*(vtk\w+)\b[^;{]*?(?::\s*public\s+([\w:]+))?\s*(?:\{|$)", re.M)


def parse_module_file(path):
    fields, key = {}, None
    for line in path.read_text(errors="replace").splitlines():
        if not line.strip():
            continue
        if not line[0].isspace():
            key = line.strip()
            fields[key] = []
        elif key:
            fields[key].append(line.strip())
    return fields


def header_class(header):
    text = header.read_text(errors="replace")
    for m in CLASS_DECL.finditer(text):
        if m[1] == header.stem:
            base = m[2]
            if base is None:
                after = text[m.end():m.end() + 200]
                b = re.match(r"\s*:\s*public\s+([\w:]+)", after)
                base = b[1] if b else None
            return base.split("::")[-1] if base else None, True
    return None, False


def tracked_files(vtk):
    out = subprocess.run(["git", "-C", str(vtk), "ls-files"], capture_output=True, text=True, check=True).stdout
    return out.splitlines()


def build(vtk):
    files = tracked_files(vtk)
    module_files = [f for f in files if f.endswith("/vtk.module")]
    modules, dir_to_module = {}, {}
    for mf in module_files:
        fields = parse_module_file(vtk / mf)
        name = (fields.get("NAME") or [None])[0]
        if not name:
            continue
        directory = str(Path(mf).parent)
        modules[name] = {
            "directory": directory,
            "description": " ".join(fields.get("DESCRIPTION", [])),
            "kit": (fields.get("KIT") or [None])[0],
            "groups": fields.get("GROUPS", []),
            "depends": fields.get("DEPENDS", []),
            "private_depends": fields.get("PRIVATE_DEPENDS", []),
            "third_party": directory.startswith("ThirdParty/") or "THIRD_PARTY" in fields,
            "classes": [],
        }
        dir_to_module[directory] = name

    classes = {}
    for f in files:
        if not (f.endswith(".h") and Path(f).name.startswith("vtk")) or "/Testing/" in f:
            continue
        module = module_for_path(f, dir_to_module)
        if not module or modules[module]["third_party"]:
            continue
        base, found = header_class(vtk / f)
        if found:
            classes[Path(f).stem] = {"module": module, "header": f, "base": base}
            modules[module]["classes"].append(Path(f).stem)

    for name, c in classes.items():
        chain, seen, cur = [], {name}, c["base"]
        while cur and cur not in seen:
            chain.append(cur)
            seen.add(cur)
            cur = classes.get(cur, {}).get("base")
        c["ancestors"] = chain

    for m in modules.values():
        m["classes"].sort()
    return {"source_commit": subprocess.run(["git", "-C", str(vtk), "rev-parse", "HEAD"], capture_output=True,
                                            text=True).stdout.strip(),
            "modules": modules, "classes": classes, "directories": dir_to_module}


def module_for_path(path, dir_to_module):
    parts = Path(path).parts
    for i in range(len(parts) - 1, 0, -1):
        module = dir_to_module.get(str(Path(*parts[:i])))
        if module:
            return module
    return None


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--vtk", default="/home/jlee/gitsync/vtk")
    p.add_argument("--out", default="ontology/entities.json")
    args = p.parse_args()

    entities = build(Path(args.vtk))
    Path(args.out).write_text(json.dumps(entities, indent=1, sort_keys=True) + "\n")
    own = [m for m in entities["modules"].values() if not m["third_party"]]
    print(f"{len(entities['modules'])} modules ({len(own)} VTK, {len(entities['modules']) - len(own)} third-party), "
          f"{len(entities['classes'])} classes -> {args.out}")
    for name in ("vtkContourFilter", "vtkPolyData", "vtkSMPTools", "vtkOpenGLPolyDataMapper"):
        c = entities["classes"].get(name)
        print(f"  {name}: {c['module'] if c else 'not found'}  {' > '.join(c['ancestors'][:5]) if c else ''}")


if __name__ == "__main__":
    main()
