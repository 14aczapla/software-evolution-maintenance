#!/usr/bin/env python3
"""Step 1.2: aggregate pylint JSON + ruff + vulture output into smell tables.

Usage:
  python smells_aggregate.py --pylint output/pylint_raw.json \
      --ruff output/ruff_raw.json --vulture output/vulture_raw.json \
      --classes output/classes_metrics.csv --functions output/functions_complexity.csv
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

SMELL_MAP = {
    "R0901": "too-many-arguments", "R0902": "too-many-branches",
    "R0903": "too-many-statements (Long Method)",
    "R0904": "too-many-public-methods (God Class signal)",
    "R0911": "too-many-return-statements", "R0912": "too-many-branches",
    "R0913": "too-many-arguments", "R0914": "too-many-locals",
    "R0915": "too-many-statements (Long Method)",
    "R0916": "too-many-boolean-expressions", "R0917": "too-many-positional-arguments",
    "R0921": "too-many-nested-blocks", "R0902": "too-many-branches",
    "R0801": "duplicated-code (DCM)",
    "R0912": "too-many-branches",
    "W0212": "protected-access", "W0108": "unnecessary-lambda",
    "C0302": "too-many-function-args", "R1702": "too-many-inconsistent-returns",
    "R1720": "useless-else-on-loop", "W0221": "arguments-differ",
    "W0237": "assignments-from-none", "R0903": "too-many-statements",
    "W0613": "unused-argument (dead param)", "W0612": "unused-variable",
    "C0103": "invalid-name", "C0303": "trailing-whitespace",
}


def main():
    args = sys.argv[1:]
    out = Path(args[args.index("--out") + 1]) if "--out" in args else Path("output")

    # ---- pylint -----------------------------------------------------------
    py_path = args[args.index("--pylint") + 1]
    msgs = json.loads(Path(py_path).read_text(encoding="utf-8"))
    counts = Counter()
    by_symbol = defaultdict(list)
    for m in msgs:
        sym = m["symbol"]
        counts[sym] += 1
        by_symbol[sym].append((m["path"], m.get("line", 0), m.get("message", "")[:80]))
    top = [{"symbol": s, "count": n} for s, n in counts.most_common(30)]
    pd.DataFrame(top).to_csv(out / "smells_pylint_top.csv", index=False)
    # per-file top offenders for the key smells
    key = {"too-many-statements", "too-many-public-methods", "duplicated-code",
           "too-many-arguments", "too-many-instance-attributes", "too-many-locals"}
    per_file = Counter()
    for m in msgs:
        if m["symbol"] in key:
            per_file[Path(m["path"]).name] += 1
    pd.DataFrame([{"file": f, "key_smell_msgs": n} for f, n in per_file.most_common(50)]
                 ).to_csv(out / "smells_pylint_top_files.csv", index=False)
    print(f"pylint messages: {len(msgs)}, distinct symbols: {len(counts)}")

    # ---- god class / long method from our metrics -------------------------
    if (out / "classes_metrics.csv").exists():
        cl = pd.read_csv(out / "classes_metrics.csv")
        god = cl[(cl["loc"] >= 400) & (cl.methods >= 12)].copy()
        god["god_score"] = god["loc"] / 400 * 0.5 + god.methods / 12 * 0.5
        god.sort_values("god_score", ascending=False).to_csv(
            out / "god_classes.csv", index=False)
        print(f"god_classes.csv: {len(god)} candidates (LOC>=400 & methods>=12)")
    if (out / "functions_complexity.csv").exists():
        fn = pd.read_csv(out / "functions_complexity.csv")
        longm = fn[(fn["loc"] >= 80) | (fn.cognitive >= 40)].sort_values(
            "cognitive", ascending=False)
        longm.to_csv(out / "long_methods.csv", index=False)
        print(f"long_methods.csv: {len(longm)} candidates (LOC>=80 or cognitive>=40)")

    # ---- ruff -------------------------------------------------------------
    if "--ruff" in args:
        rj = Path(args[args.index("--ruff") + 1])
        if rj.exists():
            rmsg = json.loads(rj.read_text(encoding="utf-8"))
            rcounts = Counter(r["code"] for r in rmsg)
            pd.DataFrame([{"code": c, "count": n} for c, n in rcounts.most_common(30)]
                         ).to_csv(out / "smells_ruff_top.csv", index=False)
            print(f"ruff diagnostics: {len(rmsg)}")

    # ---- vulture -----------------------------------------------------------
    if "--vulture" in args:
        vp = Path(args[args.index("--vulture") + 1])
        if vp.exists():
            vlines = [l for l in vp.read_text(encoding="utf-8", errors="replace").splitlines()
                      if l.strip() and "confidence" in l.lower()]
            vdf = pd.DataFrame([{"line": l} for l in vlines])
            vdf.to_csv(out / "dead_code_candidates.csv", index=False)
            print(f"dead_code_candidates.csv: {len(vdf)} candidates")

    print("DONE")


if __name__ == "__main__":
    main()
