
import datetime, json, sys
from collections import Counter
from pydriller import Repository

repo = Repository(r"C:\Users\kinga\maintainability-audit\zulip", since=datetime.datetime(2024, 11, 15))
counts = Counter()
n = skipped = 0
for c in repo.traverse_commits():
    n += 1
    if n % 1000 == 0:
        print("commits:", n, "skipped:", skipped, flush=True)
    try:
        mods = c.modified_files
    except Exception:
        # shallow clone: the first commit(s) have pruned parents ->
        # diff-tree cannot resolve them; skip those boundary commits
        skipped += 1
        continue
    for f in mods:
        if f.filename.startswith("zerver/lib/"):
            counts[f.filename] += 1
print("total commits:", n, "skipped (shallow boundary):", skipped)
with open(r"C:\Users\kinga\maintainability-audit\output\tools\pydriller_churn.json", "w") as fh:
    json.dump(dict(counts), fh, indent=1)
print("pydriller files:", len(counts))
