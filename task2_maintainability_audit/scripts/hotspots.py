#!/usr/bin/env python3
"""Stage 2: hotspot identification, hidden logical coupling, bus-factor risk.

Inputs (from Stage 1, in output/):
  functions_complexity.csv, files_size.csv, churn_per_file.csv,
  ownership_per_file.csv, cochange_pairs.csv, author_activity.csv,
  modules_coupling.csv
Outputs (output/):
  hotspots.csv, hidden_couples.csv, bus_factor_risks.csv
"""
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent.parent / "output"


def main():
    fn = pd.read_csv(OUT / "functions_complexity.csv")
    size = pd.read_csv(OUT / "files_size.csv")
    churn = pd.read_csv(OUT / "churn_per_file.csv")
    own = pd.read_csv(OUT / "ownership_per_file.csv")
    cochange = pd.read_csv(OUT / "cochange_pairs.csv")
    authors = pd.read_csv(OUT / "author_activity.csv")
    coup = pd.read_csv(OUT / "modules_coupling.csv")

    # ---- file-level complexity --------------------------------------------
    file_cog = fn.groupby("file").agg(
        max_cognitive=("cognitive", "max"),
        avg_cognitive=("cognitive", "mean"),
        sum_cognitive=("cognitive", "sum"),
        n_functions=("function", "count"),
    ).reset_index()
    hf = size.merge(file_cog, on="file", how="left")
    hf = hf.merge(churn[["file", "n_commits"]], on="file", how="left")
    hf["n_commits"] = hf["n_commits"].fillna(0).astype(int)
    for c in ["max_cognitive", "avg_cognitive", "sum_cognitive"]:
        hf[c] = hf[c].fillna(0)

    def is_test(f: str) -> bool:
        parts = f.split("/")
        return "tests" in parts or parts[-1].startswith("test_")

    hf_all = hf.copy()
    hf = hf[~hf["file"].map(is_test)]  # product code only for hotspot ranking

    # ---- 2.1 hotspots -------------------------------------------------------
    def norm(s):
        s = s.astype(float)
        return (s - s.min()) / (s.max() - s.min() + 1e-9)

    hf["churn_n"] = norm(np.log1p(hf["n_commits"]))
    hf["cog_n"] = norm(hf["max_cognitive"])
    hf["hotspot_score"] = hf["churn_n"] * hf["cog_n"]
    hot = hf.sort_values("hotspot_score", ascending=False)
    hot.to_csv(OUT / "hotspots.csv", index=False)
    print("TOP 10 HOTSPOTS (score = minmax(log churn) * minmax(max cognitive)):")
    cols = ["file", "sloc", "n_commits", "max_cognitive", "avg_cognitive",
            "sum_cognitive", "hotspot_score"]
    print(hot[cols].head(10).to_string(index=False, float_format=lambda v: f"{v:.2f}"))

    # ---- 2.2 hidden logical coupling ---------------------------------------
    # direct import edges (either direction)
    edges = set()
    for row in coup.itertuples():
        for imp in str(row.imports).split("|"):
            if imp:
                # normalize to file-ish path for matching
                edges.add((row.file, imp + ".py"))
                edges.add((imp + ".py", row.file))
                edges.add((row.file, imp.replace("/", ".") + ".py"))
    # also dotted form of row.file
    def dotted(p):
        return p.replace("/", ".")

    edges2 = set()
    for (a, b) in edges:
        edges2.add((dotted(a), b))
        edges2.add((a, dotted(b)))
        edges2.add((dotted(a), dotted(b)))
        edges2.add((b, a)) if a != b else None
    # build normalized set over both dotted and slash forms
    def linked(x, y):
        x2, y2 = x.replace("/", "."), y.replace("/", ".")
        return any({a, b} == {x2, y2} or {a, b} == {x, y} or
                   {a, b} == {x2, y} or {a, b} == {x, y2}
                   for a, b in edges2)

    minc = 5
    cc = cochange[(cochange["pct_a"] > 70) & (cochange["pct_b"] > 70)].copy()
    cc = cc[cc["file_a"].isin(set(hf.file)) & cc["file_b"].isin(set(hf.file))]
    # filter pairs where either file had < min commits
    churn_map = dict(zip(churn.file, churn.n_commits))
    cc["commits_a"] = cc.file_a.map(churn_map).fillna(0)
    cc["commits_b"] = cc.file_b.map(churn_map).fillna(0)
    cc = cc[(cc["commits_a"] >= minc) & (cc["commits_b"] >= minc)]
    cc["direct_import"] = [linked(a, b) for a, b in zip(cc.file_a, cc.file_b)]
    hidden = cc[~cc["direct_import"]].sort_values("shared_commits", ascending=False)
    cc.to_csv(OUT / "hidden_couples.csv", index=False)
    print(f"\nco-change pairs >70% both ways (min {minc} commits): {len(cc)}; "
          f"without direct import edge: {len(hidden)}")
    print(hidden[["file_a", "file_b", "shared_commits", "pct_a", "pct_b"]]
          .head(15).to_string(index=False))

    # ---- 2.3 bus factor ------------------------------------------------------
    top_cog = hf["sum_cognitive"].quantile(0.90)
    core = hf[hf["sum_cognitive"] >= top_cog].copy()
    core = core.merge(own, on="file", how="left")
    risky = core[(core["n_authors"] == 1) | (core["top_author_pct"] >= 80)].copy()
    last = dict(zip(authors.author, authors.last_commit))
    risky["top_author_last_active"] = risky.top_author.map(last)
    risky = risky.sort_values("sum_cognitive", ascending=False)
    risky.to_csv(OUT / "bus_factor_risks.csv", index=False)
    print(f"\nbus-factor risks (top-decile complexity, 1 author or >=80% share): "
          f"{len(risky)}")
    print(risky[["file", "sum_cognitive", "top_author", "top_author_pct",
                 "top_author_last_active"]].head(15).to_string(index=False))
    print("DONE")


if __name__ == "__main__":
    main()
