#!/usr/bin/env python3
"""Collect all numbers needed for the Stage-1 report. Prints markdown tables."""
from pathlib import Path
import subprocess

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output"
pd.set_option("display.width", 200)


def is_test(f: str) -> bool:
    parts = f.split("/")
    return "tests" in parts or parts[-1].startswith("test_")


def git(*args):
    return subprocess.run(
        ["git", "-C", str(ROOT / "zulip"), *args],
        capture_output=True, text=True).stdout.strip()


sz = pd.read_csv(OUT / "files_size.csv")
fn = pd.read_csv(OUT / "functions_complexity.csv")
cl = pd.read_csv(OUT / "classes_metrics.csv")
hal = pd.read_csv(OUT / "modules_halstead.csv")
mc = pd.read_csv(OUT / "modules_coupling.csv")
churn = pd.read_csv(OUT / "churn_per_file.csv")
own = pd.read_csv(OUT / "ownership_per_file.csv")
authors = pd.read_csv(OUT / "author_activity.csv")
monthly = pd.read_csv(OUT / "monthly_activity.csv")
sm = pd.read_csv(OUT / "smells_pylint_top.csv")
god = pd.read_csv(OUT / "god_classes.csv")
lm = pd.read_csv(OUT / "long_methods.csv")
hot = pd.read_csv(OUT / "hotspots.csv")

print("== STATIC ==")
prod = sz[~sz.file.map(is_test)]
print(f"files all={len(sz)} product={len(prod)} sloc_all={sz.sloc.sum()} sloc_prod={prod.sloc.sum()}")
print(f"functions={len(fn)} classes={len(cl)}")
print(fn[["cyclomatic", "cognitive"]].describe().loc[["min", "50%", "mean", "75%", "max"]]
      .round(1).to_string())
print("fn cog>=50:", (fn.cognitive >= 50).sum(), " cog>=100:", (fn.cognitive >= 100).sum(),
      " cyc>=30:", (fn.cyclomatic >= 30).sum())
print("\nTOP 10 FUNCTIONS BY COGNITIVE:")
print(fn.sort_values("cognitive", ascending=False)
      [["file", "function", "loc", "cyclomatic", "cognitive"]].head(10).to_string(index=False))
print("\nDIT dist:", cl.dit.value_counts().sort_index().to_dict())
print("classes DIT>=3:", (cl.dit >= 3).sum())
print("\nTOP 10 CLASSES BY CBO:")
print(cl.sort_values("cbo", ascending=False)
      [["file", "class", "loc", "methods", "dit", "cbo"]].head(10).to_string(index=False))
print("\nTOP 10 CLASSES BY LOC:")
print(cl.sort_values("loc", ascending=False)
      [["file", "class", "loc", "methods", "dit", "cbo"]].head(10).to_string(index=False))
print("\nHALSTEAD: effort mean/median/max:",
      hal.effort.mean().round(1), hal.effort.median().round(1), hal.effort.max().round(1))
print("TOP 5 MODULES BY HALSTEAD EFFORT:")
print(hal.sort_values("effort", ascending=False)
      [["file", "h1", "h2", "volume", "effort", "difficulty"]].head(5).to_string(index=False))
print("\nCOUPLING: modules with in-repo imports:", len(mc))
imp_counts = mc.imports.fillna("").apply(lambda s: len([i for i in s.split("|") if i]))
print("avg in-repo imports/module: %.1f" % imp_counts.mean(), " max:", imp_counts.max())

print("\n== SMELLS ==")
print("PYLINT TOP 15:")
print(sm.head(15).to_string(index=False))
ruff = pd.read_csv(OUT / "smells_ruff_top.csv")
print("\nRUFF BY RULE (top 15):")
print(ruff.head(15).to_string(index=False))
print("\nGOD CLASSES:", len(god), " TOP 10:")
print(god.head(10)[["file", "class", "loc", "methods", "dit", "cbo", "god_score"]]
      .to_string(index=False))
print("\nLONG METHODS:", len(lm), " TOP 10:")
print(lm.sort_values("cognitive", ascending=False)
      .head(10)[["file", "function", "loc", "cyclomatic", "cognitive"]].to_string(index=False))

print("\n== EVOLUTION ==")
ch = churn.copy()
ch["is_test"] = ch.file.map(is_test)
prodch = ch[~ch.is_test].sort_values("n_commits", ascending=False)
print(f"files with churn: {len(ch)} (product: {len(prodch)}), total commits in window: {git('rev-list','--count','HEAD')}")
print("TOP 10 PRODUCT FILES BY CHURN:")
print(prodch.head(10).to_string(index=False))
ow = own.copy()
ow = ow.merge(churn[["file", "n_commits"]], on="file", how="left")
ow["is_test"] = ow.file.map(is_test)
owprod = ow[~ow.is_test]
print("\nfiles with >=5 distinct authors:", (owprod.n_authors >= 5).sum(),
      " single-author product files:", (owprod.n_authors == 1).sum())
print("TOP 10 FILES BY #AUTHORS:")
print(owprod.sort_values("n_authors", ascending=False)
      .head(10)[["file", "n_commits", "n_authors", "top_author", "top_author_pct"]].to_string(index=False))
print("\nTOP 10 AUTHORS (all files in scope):")
print(authors.sort_values("n_commits", ascending=False)
      .head(10).to_string(index=False))
print("total authors:", len(authors))
print("monthly commits: months=%d avg=%.0f" % (len(monthly), monthly.n_commits.mean()))

cc = pd.read_csv(OUT / "cochange_pairs.csv")
print("\nCO-CHANGE: raw pairs:", len(cc), " shared>=10:", (cc.shared_commits >= 10).sum(),
      " shared>=20:", (cc.shared_commits >= 20).sum())
topcc = cc.sort_values("shared_commits", ascending=False)
print("TOP 10 CO-CHANGE PAIRS (product only):")
def both_prod(r):
    return not is_test(r.file_a) and not is_test(r.file_b)
print(topcc[topcc.apply(both_prod, axis=1)].head(10)
      [["file_a", "file_b", "shared_commits"]].to_string(index=False))

print("\n== STAGE 2 SUMMARY ==")
print("hotspot score>0 files:", (hot.hotspot_score > 0).sum())
hc = pd.read_csv(OUT / "hidden_couples.csv")
print("hidden couples total:", len(hc[hc.direct_import == False]))
bf = pd.read_csv(OUT / "bus_factor_risks.csv")
print("bus factor risks:", len(bf))
print("bf single-author files:", (bf.n_authors == 1).sum())
