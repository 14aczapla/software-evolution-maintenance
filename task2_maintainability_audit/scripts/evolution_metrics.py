#!/usr/bin/env python3
"""Step 1.3: repository evolution metrics for the Zulip audit (last 24 months).

Uses a single `git log --numstat` pass over the shallow clone.

Outputs (into <root>/output/):
  churn_per_file.csv     - file, n_commits, lines_added, lines_deleted
  ownership_per_file.csv - file, n_authors, top_author, top_author_commits, top_author_pct
  cochange_pairs.csv     - file_a, file_b, shared_commits, pct_a, pct_b
  author_activity.csv    - author, email, n_commits, first_commit, last_commit
  monthly_activity.csv   - month, n_commits, n_authors

Usage:
  python evolution_metrics.py --root C:\\...\\zulip [--since 2024-11-15] [--prefix zerver/ ...]
"""
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

PREFIX = "COMMIT|||"


def main():
    args = sys.argv[1:]
    root = Path(args[args.index("--root") + 1])
    since = "2024-11-15"
    if "--since" in args:
        since = args[args.index("--since") + 1]
    prefixes = args[args.index("--prefix") + 1:] if "--prefix" in args else []

    out = root.parent / "output"
    out.mkdir(exist_ok=True)

    fmt = PREFIX + "%H|%an|%ae|%cd"
    cmd = ["git", "-C", str(root), "log", f"--since={since}", "--date=iso",
           f"--pretty=format:{fmt}", "--numstat"]
    print("running git log ...")
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        sys.exit(f"git log failed: {proc.stderr[:500]}")
    print(f"parsed {proc.stdout.count(PREFIX)} commits")

    def in_scope(path: str) -> bool:
        if not path.endswith(".py"):
            return False
        if not prefixes:
            return True
        return any(path.startswith(p.rstrip("/") + "/") or path == p.rstrip("/")
                   for p in prefixes)

    commits = []  # (sha, author, email, date, [files])
    sha = author = email = date = None
    files = []
    for line in proc.stdout.splitlines():
        if line.startswith(PREFIX):
            if sha:
                commits.append((sha, author, email, date, files))
            rest = line[len(PREFIX):]
            sha, author, email, date = rest.split("|", 3)
            files = []
        elif line.strip():
            parts = line.split("\t")
            if len(parts) == 3:
                p = parts[2].strip()
                # rename: "old => new" or braces form in numstat? numstat keeps target path
                files.append(p)
    if sha:
        commits.append((sha, author, email, date, files))

    print(f"total commits in window: {len(commits)}")

    # ---- scope filter -----------------------------------------------------
    scoped = []
    for sha, author, email, date, files in commits:
        sf = [f for f in files if in_scope(f)]
        scoped.append((sha, author, email, date, sf))
    active = [c for c in scoped if c[4]]
    print(f"commits touching scope .py files: {len(active)}")

    # ---- churn ------------------------------------------------------------
    churn = Counter()
    added = Counter()
    deleted = Counter()
    for sha, author, email, date, files in active:
        for f in set(files):
            churn[f] += 1
    # re-scan for +/- lines (numstat per commit)
    added = Counter()
    deleted = Counter()
    for line in proc.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) == 3 and parts[0] != "COMMIT|||":
            try:
                a, d = int(parts[0]), int(parts[1])
            except ValueError:
                continue
            p = parts[2].strip()
            if in_scope(p):
                added[p] += a
                deleted[p] += d
    churn_rows = [{"file": f, "n_commits": n,
                   "lines_added": added.get(f, 0), "lines_deleted": deleted.get(f, 0)}
                  for f, n in churn.most_common()]
    pd.DataFrame(churn_rows).to_csv(out / "churn_per_file.csv", index=False)
    print(f"churn_per_file.csv: {len(churn_rows)} rows")

    # ---- ownership --------------------------------------------------------
    file_authors = defaultdict(Counter)
    for sha, author, email, date, files in active:
        for f in set(files):
            file_authors[f][author] += 1
    own_rows = []
    for f, ac in file_authors.items():
        top, top_n = ac.most_common(1)[0]
        total = sum(ac.values())
        own_rows.append({"file": f, "n_authors": len(ac), "top_author": top,
                         "top_author_commits": top_n,
                         "top_author_pct": round(100.0 * top_n / total, 1)})
    pd.DataFrame(own_rows).to_csv(out / "ownership_per_file.csv", index=False)
    print(f"ownership_per_file.csv: {len(own_rows)} rows")

    # ---- co-change pairs ---------------------------------------------------
    pair = Counter()
    for sha, author, email, date, files in active:
        fs = sorted(set(files))
        for i in range(len(fs)):
            for j in range(i + 1, len(fs)):
                pair[(fs[i], fs[j])] += 1
    pair_rows = []
    for (a, b), n in pair.most_common():
        ca, cb = churn[a], churn[b]
        pair_rows.append({"file_a": a, "file_b": b, "shared_commits": n,
                          "pct_a": round(100.0 * n / ca, 1),
                          "pct_b": round(100.0 * n / cb, 1)})
    pd.DataFrame(pair_rows).to_csv(out / "cochange_pairs.csv", index=False)
    print(f"cochange_pairs.csv: {len(pair_rows)} pairs (raw)")

    # ---- author activity --------------------------------------------------
    act = {}
    for sha, author, email, date, files in commits:
        d = date.split(" ")[0]
        if author in act:
            rec = act[author]
            rec["n_commits"] += 1
            rec["last_commit"] = max(rec["last_commit"], d)
            rec["first_commit"] = min(rec["first_commit"], d)
        else:
            act[author] = {"author": author, "email": email, "n_commits": 1,
                           "first_commit": d, "last_commit": d}
    pd.DataFrame(sorted(act.values(), key=lambda r: -r["n_commits"])
                 ).to_csv(out / "author_activity.csv", index=False)
    print(f"author_activity.csv: {len(act)} authors")

    # ---- monthly activity -------------------------------------------------
    monthly = Counter()
    monthly_authors = defaultdict(set)
    for sha, author, email, date, files in commits:
        m = date[:7]
        monthly[m] += 1
        monthly_authors[m].add(author)
    mrows = [{"month": m, "n_commits": n, "n_authors": len(monthly_authors[m])}
             for m, n in sorted(monthly.items())]
    pd.DataFrame(mrows).to_csv(out / "monthly_activity.csv", index=False)
    print(f"monthly_activity.csv: {len(mrows)} months")
    print("DONE")


if __name__ == "__main__":
    main()
