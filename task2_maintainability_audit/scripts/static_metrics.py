#!/usr/bin/env python3
"""Step 1.1: static code metrics for the Zulip audit.

Outputs (into <root>/output/):
  files_size.csv          - per file: SLOC, LOC, n_classes, n_functions (pygount)
  functions_complexity.csv- per function: LOC, cyclomatic, cognitive (lizard)
  modules_halstead.csv    - per module: Halstead metrics (radon hal, recommended)
  modules_halstead_tokenbased.csv - per module: token-based Halstead (cross-check)
  classes_metrics.csv     - per class: LOC, methods, DIT, CBO (AST-based)
  modules_coupling.csv    - per module: in-repo modules it imports (efferent)

Usage:
  python static_metrics.py --root C:\\...\\zulip [--scope zerver ...]
  python static_metrics.py --list     # just print candidate top-level packages
"""
import ast
import json
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd


def find_packages(root: Path):
    """Top-level dirs that are Python packages (have __init__.py) or contain .py."""
    skip = {".git", "node_modules", "static", "docs", ".github", ".venv",
            "venv", "locale", "output"}
    pkgs = []
    for d in sorted(root.iterdir()):
        if not d.is_dir() or d.name in skip:
            continue
        if (d / "__init__.py").exists() or any(d.glob("*.py")):
            pkgs.append(d.name)
    return pkgs


def iter_py_files(paths):
    for p in paths:
        if not p.is_dir():
            if p.suffix == ".py":
                yield p
            continue
        yield from sorted(p.rglob("*.py"))


def main():
    args = sys.argv[1:]
    if "--list" in args:
        root = Path(args[args.index("--root") + 1])
        print("candidates:", find_packages(root))
        return

    root = Path(args[args.index("--root") + 1])
    # scope = everything after --scope
    scope = args[args.index("--scope") + 1:]
    out = (root.parent / "output").resolve()
    out.mkdir(exist_ok=True)

    paths = [root / s for s in scope]
    files = [f for f in iter_py_files(paths) if "test" not in f.name]
    files_all = [f for f in iter_py_files(paths)]
    print(f"scope: {scope}")
    print(f"python files (all): {len(files_all)}, (non-test): {len(files)}")

    rel = lambda f: f.relative_to(root).as_posix()

    # ---- 1) size metrics (tokenize + AST; pygount 2.x API changed) --------
    import io
    import tokenize

    def size_of(path: Path) -> dict:
        src = path.read_bytes()
        try:
            toks = list(tokenize.tokenize(io.BytesIO(src).readline))
            comments = sum(1 for t in toks if t.type == tokenize.COMMENT)
        except (tokenize.TokenizeError, IndentationError):
            comments = 0
        lines = src.decode("utf-8", "replace").splitlines()
        total = len(lines)
        blank = sum(1 for l in lines if not l.strip())
        sloc = max(0, total - blank - comments)
        classes = functions = 0
        try:
            tree = ast.parse(src)
            for n in ast.walk(tree):
                if isinstance(n, ast.ClassDef):
                    classes += 1
                elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    functions += 1
        except SyntaxError:
            pass
        return {"file": rel(path), "sloc": sloc, "comments": comments,
                "blank": blank, "classes": classes, "functions": functions}

    size_rows = [size_of(f) for f in files_all]
    files_df = pd.DataFrame(size_rows)
    files_df.to_csv(out / "files_size.csv", index=False)
    print(f"files_size.csv: {len(files_df)} rows")

    # ---- 2) lizard CLI: cognitive + cyclomatic complexity -----------------
    # (lizard 1.26 moved cognitive complexity to a CLI extension, -Ecognitive)
    import subprocess
    lizard_exe = Path(__file__).resolve().parent.parent / ".venv" / "Scripts" / "lizard.exe"
    filelist = out / "_filelist.txt"
    filelist.write_text("\n".join(str(x.relative_to(root)) for x in files_all) + "\n")
    proc = subprocess.run(
        [str(lizard_exe), "-Ecognitive", "-V",
         "-o", str(out / "_lizard_full.csv"),
         "-f", str(filelist)],
        cwd=str(root), capture_output=True, text=True)
    if proc.returncode != 0:
        print(f"lizard FAILED: {proc.stderr[:500]}")
        sys.exit(1)
    func_df = pd.read_csv(out / "_lizard_full.csv")
    func_df["file"] = func_df["file"].str.replace("\\", "/", regex=False)
    func_df = func_df.rename(columns={
        "file": "file", "NLOC": "loc", "CCN": "cyclomatic",
        " CogC ": "cognitive", "PARAM": "params", "function": "function"})
    func_df["module"] = func_df["file"].str.replace("/", ".", regex=False)
    func_df["is_method"] = ""  # not exposed by lizard CLI; unused downstream
    func_df = func_df[["file", "function", "module", "loc", "cyclomatic",
                       "cognitive", "params", "is_method"]]
    func_df.to_csv(out / "functions_complexity.csv", index=False)
    print(f"functions_complexity.csv: {len(func_df)} rows")

    # ---- 3) Halstead (module level, classic `radon hal` convention) -------
    import keyword
    import math
    LOGIC = {"and", "or", "not", "in", "is"}
    hal_rows = []
    for f in files_all:
        try:
            toks = list(tokenize.tokenize(io.BytesIO(f.read_bytes()).readline))
        except (tokenize.TokenizeError, IndentationError):
            continue
        ops, datas = set(), set()
        N1 = N2 = 0
        for t in toks:
            if t.type == tokenize.OP:
                ops.add(t.string); N1 += 1
            elif t.type == tokenize.NAME:
                if t.string in LOGIC or keyword.iskeyword(t.string):
                    ops.add(t.string); N1 += 1
                else:
                    datas.add(t.string); N2 += 1
            elif t.type in (tokenize.NUMBER, tokenize.STRING):
                datas.add(t.string[:20]); N2 += 1
        if N1 == 0 or N2 == 0:
            continue
        n1, n2 = len(ops), len(datas)
        V = n1 * math.log2(n1) + n2 * math.log2(n2)
        E = n1 * math.log2(n1) * (N2 / n2)
        hal_rows.append({"file": rel(f), "n1": n1, "n2": n2, "N1": N1,
                         "N2": N2, "volume": round(V, 1), "effort": round(E, 1),
                         "time_s": round(E / 18, 2),
                         "difficulty": round(E / (n2 * math.log2(n1 + n2)), 2)})
    pd.DataFrame(hal_rows).to_csv(
        out / "modules_halstead_tokenbased.csv", index=False)
    print(f"modules_halstead_tokenbased.csv: {len(hal_rows)} rows")

    # ---- 3b) Halstead via the recommended tool: `radon hal` ----------------
    radon_exe = Path(__file__).resolve().parent.parent / ".venv" / "Scripts" / "radon.exe"
    r = subprocess.run([str(radon_exe), "hal", *scope, "-j"],
                       cwd=str(root), capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"radon hal failed: {r.stderr[:400]}")
    hal_raw = json.loads(r.stdout)
    hrows = []
    for k, v in hal_raw.items():
        t = v["total"]
        hrows.append({"file": k.replace("\\", "/"), "h1": t["h1"],
                      "h2": t["h2"], "N1": t["N1"], "N2": t["N2"],
                      "volume": round(t["volume"], 1),
                      "difficulty": round(t["difficulty"], 4),
                      "effort": round(t["effort"], 1),
                      "time_s": round(t["time"], 2),
                      "bugs": round(t["bugs"], 4)})
    hrows.sort(key=lambda d: d["file"])
    pd.DataFrame(hrows).to_csv(out / "modules_halstead.csv", index=False)
    print(f"modules_halstead.csv (radon hal): {len(hrows)} rows")

    # ---- 4) classes: LOC, DIT, CBO (AST) ---------------------------------
    class_registry = {}   # (module, name) -> (bases, file, nodes)
    module_of = {}

    for f in files_all:
        src = f.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(src)
        except SyntaxError as e:
            print(f"SYNTAX-ERROR: {rel(f)}: {e}")
            continue
        mod = f.relative_to(root).with_suffix("").as_posix().replace("\\", "/")
        mod = mod[:-3] if mod.endswith(".py") else mod
        module_of[mod] = f
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                bases = []
                for b in node.bases:
                    if isinstance(b, ast.Name):
                        bases.append(b.id)
                    elif isinstance(b, ast.Attribute):
                        bases.append(b.attr)
                    elif isinstance(b, ast.Subscript):
                        bases.append(getattr(b.value, "id", ""))
                class_registry[(mod, node.name)] = (
                    bases, f, len(node.body), src.splitlines())

    def class_loc(f, node):
        # approximate: from line start to end line
        try:
            lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
            return max(0, (node.end_lineno or node.lineno) - node.lineno + 1)
        except Exception:
            return 0

    # pre-resolve: build simple name -> set of modules
    by_name = defaultdict(set)
    for (m, n) in class_registry:
        by_name[n].add(m)

    def resolve_base(mod, b):
        mods = by_name.get(b, set())
        if not mods:
            return None
        if mod in mods:
            return (mod, b)
        if len(mods) == 1:
            return (next(iter(mods)), b)
        return None  # ambiguous across modules -> unresolvable, skip

    def dit_of(mod, name):
        def rec(mod, name, seen):
            entry = class_registry.get((mod, name))
            if entry is None:
                return 0
            best = 0
            for b in entry[0]:
                r = resolve_base(mod, b)
                if r is not None and r != (mod, name) and r not in seen:
                    best = max(best, 1 + rec(r[0], r[1], seen | {r}))
            return best
        return rec(mod, name, {(mod, name)})

    class_rows = []
    for f in files_all:
        src = f.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        mod = str(f.relative_to(root)).replace("\\", "/")
        if mod.endswith(".py"):
            mod = mod[:-3]
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    imported.add(a.asname or a.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.level and node.module:
                    imported.add(node.module)
                elif node.module:
                    imported.add(node.module)
                for a in node.names:
                    imported.add(a.name)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # CBO: distinct external class names referenced in body
                names = set()
                for sub in ast.walk(node):
                    if isinstance(sub, ast.Name) and sub.id in by_name:
                        names.add(sub.id)
                    elif isinstance(sub, ast.Attribute) and sub.attr in by_name:
                        names.add(sub.attr)
                names.discard(node.name)
                entry_bases = [
                    x.id if isinstance(x, ast.Name) else getattr(x, "attr", None)
                    for x in node.bases if isinstance(x, (ast.Name, ast.Attribute))
                ]
                for b in entry_bases:
                    if b in by_name:
                        names.add(b)
                # imported classes (best effort: imported names that are classes in repo)
                for i in imported:
                    if i in by_name:
                        names.add(i)
                class_rows.append({
                    "file": f.relative_to(root).as_posix(),
                    "class": node.name,
                    "loc": class_loc(f, node),
                    "methods": len([s for s in node.body
                                    if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef))]),
                    "dit": dit_of(mod, node.name),
                    "cbo": len(names),
                })
    class_df = pd.DataFrame(class_rows)
    class_df.to_csv(out / "classes_metrics.csv", index=False)
    print(f"classes_metrics.csv: {len(class_df)} rows")

    # ---- 5) module coupling (in-repo imports) ----------------------------
    # map: dotted module path -> file
    file_by_dotted = {}
    for f in files_all:
        relp = f.relative_to(root).as_posix().replace("\\", "/")
        dotted = relp[:-3] if relp.endswith(".py") else relp
        dotted = dotted.replace("/", ".")
        if dotted.endswith(".__init__"):
            dotted = dotted[:-9]
        file_by_dotted[dotted] = f

    coupling = defaultdict(set)
    for f in files_all:
        relp = f.relative_to(root).as_posix().replace("\\", "/")
        src = f.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        top = relp.split("/")[0]
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith(top + "."):
                    coupling[relp].add(node.module.replace(".", "/"))
                elif node.level:
                    # relative import within package
                    base = relp.rsplit("/", 1)[0]
                    tgt = base + ("/" + node.module if node.module else "")
                    coupling[relp].add(tgt)
            elif isinstance(node, ast.Import):
                for a in node.names:
                    if a.name.startswith(top + "."):
                        coupling[relp].add(a.name.replace(".", "/"))
    coup_rows = [{"file": k, "efferent_inrepo": len(v),
                  "imports": "|".join(sorted(v))} for k, v in sorted(coupling.items())]
    pd.DataFrame(coup_rows).to_csv(out / "modules_coupling.csv", index=False)
    print(f"modules_coupling.csv: {len(coup_rows)} rows")
    print("DONE")


if __name__ == "__main__":
    main()
