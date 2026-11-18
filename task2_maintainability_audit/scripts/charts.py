#!/usr/bin/env python3
"""Charts for the final audit report (matplotlib -> output/charts/*.png)."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

OUT = Path(__file__).resolve().parent.parent / "output"
CH = OUT / "charts"
CH.mkdir(exist_ok=True)

plt.rcParams.update({"figure.dpi": 110, "font.size": 9,
                     "axes.grid": True, "grid.alpha": 0.3})


def short(p: str, n=55):
    return p if len(p) <= n else "…" + p[-(n - 1):]


# ---- 1) hotspot matrix ------------------------------------------------------
hot = pd.read_csv(OUT / "hotspots.csv")
top5 = hot.head(5)
fig, ax = plt.subplots(figsize=(9, 6))
ax.scatter(hot["n_commits"], hot["max_cognitive"],
           s=np.sqrt(hot["sloc"]) * 6, alpha=0.4, c="steelblue")
ax.set_xscale("log")
ax.set_xlabel("Change frequency (commits, last 24 months, log scale)")
ax.set_ylabel("Max cognitive complexity in file")
ax.set_title("Hotspot matrix: complexity vs. change frequency (Zulip, 2024-11→2026-11)")
for _, r in top5.iterrows():
    ax.annotate(short(r["file"], 40), (r["n_commits"], r["max_cognitive"]),
                textcoords="offset points", xytext=(6, 4), fontsize=7)
plt.tight_layout()
plt.savefig(CH / "hotspot_matrix.png")
plt.close()

# ---- 2) smell distribution ---------------------------------------------------
sm = pd.read_csv(OUT / "smells_pylint_top.csv")
sm = sm.head(15)
fig, ax = plt.subplots(figsize=(9, 5.5))
ax.barh(range(len(sm))[::-1], sm["count"], color="darkorange")
ax.set_yticks(range(len(sm))[::-1])
ax.set_yticklabels([short(s, 40) for s in sm["symbol"]])
ax.set_xlabel("Message count (pylint, default rules + DCM)")
ax.set_title("Most frequent code smell categories")
plt.tight_layout()
plt.savefig(CH / "smell_distribution.png")
plt.close()

# ---- 3) monthly commits -------------------------------------------------------
ma = pd.read_csv(OUT / "monthly_activity.csv")
fig, ax = plt.subplots(figsize=(9, 4))
ax.bar(ma["month"], ma["n_commits"], color="seagreen", width=22)
ax2 = ax.twinx()
ax2.plot(ma["month"], ma["n_authors"], color="crimson", marker=".", lw=1)
ax2.set_ylabel("distinct authors", color="crimson")
ax.set_ylabel("commits (scoped .py files)")
ax.set_title("Commit activity, 24 months")
plt.xticks(rotation=60, fontsize=7)
plt.tight_layout()
plt.savefig(CH / "monthly_activity.png")
plt.close()

# ---- 4) hidden co-change pairs -------------------------------------------------
hc = pd.read_csv(OUT / "hidden_couples.csv")
hidden = hc[~hc.get("direct_import", False)] if "direct_import" in hc else hc
hidden = hidden.sort_values("shared_commits", ascending=False).head(10)
if len(hidden):
    labels = [f"{short(a, 26)}\n↔ {short(b, 26)}" for a, b in
              zip(hidden.file_a, hidden.file_b)]
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.barh(range(len(hidden))[::-1], hidden["shared_commits"], color="slateblue")
    ax.set_yticks(range(len(hidden))[::-1])
    ax.set_yticklabels(labels, fontsize=7)
    ax.set_xlabel("shared commits (last 24 months)")
    ax.set_title("Hidden logical coupling: high co-change, no direct import")
    plt.tight_layout()
    plt.savefig(CH / "hidden_couples.png")
    plt.close()

print("charts written to", CH)
for f in sorted(CH.glob("*.png")):
    print(" -", f.name)
