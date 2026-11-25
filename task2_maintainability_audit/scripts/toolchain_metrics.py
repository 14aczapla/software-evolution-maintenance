#!/usr/bin/env python3
"""Stage 1: run the assignment's RECOMMENDED Python toolchain (metric tools)
on the full scope.

Tools run (assignment's recommended list, Python column):
  - Radon (radon raw, radon cc, radon hal)   - size + complexity + Halstead
  - Pygount (pygount CLI)                     - size
  - Xenon (xenon CLI)                         - CCN ranking
  - mccabe (flake8's C901 engine, via API)    - cyclomatic complexity

Outputs:
  output/tools/radon_raw.json, radon_cc.json, radon_hal.json
  output/tools/pygount.txt, xenon_blocks.csv, mccabe_c901.csv
"""
import json
import re
import subprocess
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
Z = ROOT / "zulip"
OUT = ROOT / "output"
TOOLS = OUT / "tools"
TOOLS.mkdir(exist_ok=True)
SCOPES = ["zerver", "zproject", "zilencer", "analytics", "confirmation",
          "corporate"]
PY = ROOT / ".venv" / "Scripts"


def run(cmd, timeout=3600):
    print("RUN:", " ".join(str(c) for c in cmd[:5]), "...", flush=True)
    p = subprocess.run([str(c) for c in cmd], cwd=str(Z),
                       capture_output=True, text=True, timeout=timeout)
    print(f"  rc={p.returncode} stdout={len(p.stdout)}B stderr={len(p.stderr)}B",
          flush=True)
    return p


def main():
    import ast as _ast
    import os as _os
    import re as _re

    from mccabe import McCabeChecker

    # ---- 1) radon raw -------------------------------------------------------
    out = TOOLS / "radon_raw.json"
    if not out.exists():
        p = run([PY / "radon.exe", "raw", *SCOPES, "-j"])
        out.write_text(p.stdout, encoding="utf-8")
    print("radon_raw.json:", out.stat().st_size, "bytes", flush=True)

    # ---- 2) radon cc --------------------------------------------------------
    out = TOOLS / "radon_cc.json"
    if not out.exists():
        p = run([PY / "radon.exe", "cc", *SCOPES, "-j"])
        out.write_text(p.stdout, encoding="utf-8")
    print("radon_cc.json:", out.stat().st_size, "bytes", flush=True)

    # ---- 3) radon hal -------------------------------------------------------
    out = TOOLS / "radon_hal.json"
    if not out.exists():
        p = run([PY / "radon.exe", "hal", *SCOPES, "-j"])
        out.write_text(p.stdout, encoding="utf-8")
    print("radon_hal.json:", out.stat().st_size, "bytes", flush=True)

    # ---- 4) pygount ---------------------------------------------------------
    out = TOOLS / "pygount.txt"
    if not out.exists():
        p = run([PY / "pygount.exe", *SCOPES])
        out.write_text(p.stdout + p.stderr, encoding="utf-8")
    print("pygount.txt:", out.stat().st_size, "bytes", flush=True)

    # ---- 5) xenon (high thresholds => enumerate all blocks with ranks) ------
    out = TOOLS / "xenon_blocks.csv"
    if not out.exists():
        p = run([PY / "xenon.exe", "-m", "100", "-b", "100", *SCOPES])
        rows = []
        for line in p.stderr.splitlines():
            m = re.search(r'block "([^"]+):(\d+) ([^"]+)" has a rank of ([A-F])',
                          line)
            if m:
                rows.append({"file": m.group(1), "line": int(m.group(2)),
                             "block": m.group(3), "rank": m.group(4)})
                continue
            m2 = re.search(r"module '([^']+)' has a rank of ([A-F])", line)
            if m2:
                rows.append({"file": m2.group(1), "line": 0,
                             "block": "<module>", "rank": m2.group(2)})
        pd.DataFrame(rows).to_csv(out, index=False)
    xen = pd.read_csv(out)
    print("xenon blocks:", len(xen), flush=True)

    # ---- 6) mccabe (flake8's C901 complexity engine, driven via its API;
    #         the flake8 CLI in this venv does not emit C901) ------------------
    out = TOOLS / "mccabe_c901.csv"
    if not out.exists():
        rows = []
        pat = _re.compile(r"C901 '([^']+)' is too complex \((\d+)\)")
        for scope in SCOPES:
            for dirpath, _dirs, files in _os.walk(Z / scope):
                for fn in files:
                    if not fn.endswith(".py"):
                        continue
                    fp = Path(dirpath) / fn
                    try:
                        src = fp.read_text(encoding="utf-8",
                                           errors="ignore")
                        tree = _ast.parse(src)
                    except SyntaxError:
                        continue
                    McCabeChecker.max_complexity = 0
                    for lineno, _col, text, _chk in McCabeChecker(
                            tree, str(fp)).run():
                        m = pat.search(text)
                        if m:
                            rows.append({
                                "file": fp.relative_to(Z).as_posix(),
                                "line": lineno, "function": m.group(1),
                                "mccabe_ccn": int(m.group(2))})
        pd.DataFrame(rows).to_csv(out, index=False)
    mcc = pd.read_csv(out)
    print("mccabe functions:", len(mcc),
          " (CCN > 10:", int((mcc.mccabe_ccn > 10).sum()), ")",
          flush=True)



if __name__ == "__main__":
    main()