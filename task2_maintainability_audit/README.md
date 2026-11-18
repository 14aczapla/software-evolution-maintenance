# Maintainability Audit — Stage 1 (Zulip, Python)

Stage 1 data collection for `zulip/zulip` (branch `main`): static metrics,
code smells, and repository-evolution metrics, with every metric
cross-validated against the recommended Python toolchain.

* **Report:** `REPORT_STAGE1.md` (read this first)
* **Data:** `output/*.csv` (+ `output/charts/`), tool raw outputs in `output/tools/`
* **Scripts:** `scripts/*.py` (one script per metric group)

## Reproduce (Windows)

```bat
git clone --shallow-since=2024-11-15 https://github.com/zulip/zulip.git zulip
python -m venv .venv
.venv\Scripts\pip install radon lizard pylint ruff vulture pydriller pydeps networkx pandas matplotlib pygount xenon mccabe flake8 import-linter
.venv\Scripts\python scripts\static_metrics.py --root zulip --scope zerver zproject zilencer analytics confirmation corporate
.venv\Scripts\python scripts\evolution_metrics.py --root zulip --prefix zerver/ zproject/ zilencer/ analytics/ confirmation/ corporate/
.venv\Scripts\python scripts\smells_aggregate.py --pylint output\pylint_raw.json --ruff output\ruff_raw.json --vulture output\vulture_raw.txt
.venv\Scripts\python scripts\hotspots.py
.venv\Scripts\python scripts\charts.py
.venv\Scripts\python scripts\toolchain_metrics.py
.venv\Scripts\python scripts\toolchain_graphs.py
```

`toolchain_graphs.py` runs Pydeps/Pyreverse/Import-linter/PyDriller and is the
slow step (PyDriller re-walks 10k commits).

## Main outputs

| File | Contents |
|---|---|
| `output/files_size.csv` | SLOC/comments/blank per file |
| `output/functions_complexity.csv` | cyclomatic + cognitive per function (lizard) |
| `output/modules_halstead.csv` | Halstead per module (`radon hal`) |
| `output/classes_metrics.csv` | LOC/methods/DIT/CBO per class |
| `output/modules_coupling.csv` | per-module import graph |
| `output/smells_pylint_top.csv`, `smells_ruff_top.csv`, `god_classes.csv`, `long_methods.csv`, `dead_code_candidates.csv` | smell tallies |
| `output/churn_per_file.csv`, `author_activity.csv`, `cochange_pairs.csv`, `hidden_couples.csv`, `monthly_activity.csv`, `ownership_per_file.csv` | evolution metrics |
| `output/hotspots.csv`, `bus_factor_risks.csv` | hotspot + bus-factor ranking |
| `output/tools/*` | raw outputs of the recommended toolchain (radon, pygount, xenon, mccabe, pydeps/pyreverse DOT, import-linter) |

## Known limitations

* Shallow clone: history only since 2024-11-15 (25 months).
* pylint/ruff ran without Zulip's runtime deps → 4,944 `import-error` pylint
  messages are environment artifacts, not code smells.
* DIT/CBO are computed over the in-repo class graph only (external Django
  bases unresolved).
* Test files are included in metrics but excluded from hotspot ranking.
* `output/cochange_pairs.csv` (139 MB raw pair list) stays local and is not
  pushed; the derived `hidden_couples.csv` contains all flagged pairs.
* PyDriller churn cross-check not completed: PyDriller 2.12's
  `modified_files` exposes basenames only, not paths (library limitation;
  the script is fixed for future runs). Churn numbers come from `git log`.
