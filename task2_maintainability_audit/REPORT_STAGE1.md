# Maintainability Audit — Stage 1: Zulip

**Repo:** `zulip/zulip` @ `main`, HEAD `0d59088` (2026-11-14), history since 2024-11-15 (10,685 commits, 25 months).
**Scope:** `zerver zproject zilencer analytics confirmation corporate` → **1,973 Python files**.
All results: `output/*.csv` · reproduction: `README.md`.

## 1. Method

| Metric | Tool |
|---|---|
| SLOC, DIT, CBO | Python `tokenize`/`ast` |
| Cyclomatic + cognitive complexity | **lizard** 1.26 (per function) |
| Halstead (h1, h2, N1, N2, volume, effort, difficulty) | **radon hal** (per module) |
| Smells | **pylint** 4, **ruff**, **vulture** |
| Churn, ownership, co-change | **git log** CLI |
| Cross-checks (§5) | Radon, Pygount, Xenon, mccabe (Flake8 C901 engine), Pydeps, Pyreverse, Import-linter |

Thresholds: *god class* = class LOC ≥ 400 and methods ≥ 12 · *long method* = LOC ≥ 80 or cognitive ≥ 40 · *hotspot* = min-max(log churn) × min-max(max cognitive), test files excluded · *hidden coupling* = pair with >70% shared commits in both directions, ≥5 each, no import edge.

## 2. Task 1.1 — Static metrics

329,889 SLOC · 13,384 functions · 2,920 classes. Complexity is healthy at the median (cyclomatic 1 / cognitive 0) but has a severe tail (max **368** / **955**). Top-5 functions by cognitive complexity:

| File | Function | LOC | CCN | Cognitive |
|---|---|---|---|---|
| `zerver/lib/events.py` | `apply_event` | 857 | 368 | **955** |
| `zerver/views/registration.py` | `registration_helper` | 480 | 82 | 181 |
| `zerver/lib/events.py` | `fetch_initial_state_data` | 557 | 124 | 172 |
| `zerver/lib/import_realm.py` | `do_import_realm` | 593 | 81 | 107 |
| `zerver/views/realm.py` | `update_realm` | 402 | 82 | 107 |

* **Halstead** (`radon hal`): product mean effort 1,569; highest `corporate/lib/stripe.py` (478,271, difficulty 17.5), `zerver/lib/markdown/__init__.py` (133,013), `zerver/lib/events.py` (123,353) — the same files that top size/complexity.
* **DIT**: max depth 5 (mostly Django test-case hierarchies); 229 classes at DIT ≥ 3.
* **CBO**: top `S3Destination`/`LocalDestination` (55) in `import_realm.py` — the import/export subsystem couples to nearly every model.
* Largest product class: `BillingSession` (`stripe.py`, 3,603 LOC, 102 methods).

## 3. Task 1.2 — Smells

pylint 33,834 messages · ruff 2,170 · vulture 255 dead-code candidates.

| Smell (pylint) | Count | Note |
|---|---|---|
| missing-docstring (3×) | 14,829 | style |
| import-error | 4,944 | analysis-venv artifact, not code |
| **duplicate-code** | **783** | high signal (webhooks, fixtures) |
| **cyclic-import** | **524** | high signal — module boundaries |
| too-many-locals / -arguments | 426 / 327 | design |

Structural: **104 god classes** (e.g. `BillingSession`, `Config` in export.py), **448 long methods**, 783 duplicate-code blocks, 524 cyclic imports, 255 dead-code candidates. Ruff agrees (C901: 228, too-many-statements: 267).

## 4. Task 1.3 — Evolution & hotspots (25 months)

10,685 commits · 277 contributors · 2,019 files with churn. Top churn: `integrations.py` (135), `streams.py` lib (116), `event_types.py` (115), `stripe.py` (114), `events.py` (98). Top contributor: Aman Agrawal (1,073).

* **Ownership**: 1,198 product files touched by exactly one author; the hot core is well distributed (`events.py`: 25 authors) — bus-factor risk sits in specialized modules, not the core.
* **Temporal coupling**: 1,406,491 co-changed pairs; 140 pairs >70% in both directions. Strongest: `event_schema.py` ↔ `event_types.py` (45 shared commits). Strongest *lockstep*: `upload/local.py` ↔ `upload/s3.py` (20 shared, 90.9%/76.9%) — shotgun-surgery candidate (no import edge; bound via factory).
* **Hotspots** (complexity × churn):

| File | Max cognitive | Commits | Score |
|---|---|---|---|
| `zerver/lib/events.py` | 955 | 98 | **0.94** |
| `zerver/views/registration.py` | 181 | 77 | 0.17 |
| `zerver/lib/import_realm.py` | 107 | 70 | 0.10 |
| `zerver/actions/message_send.py` | 102 | 70 | 0.09 |
| `zerver/views/realm.py` | 107 | 55 | 0.09 |

## 5. Cross-validation with the recommended toolchain

Every metric above was re-computed with an independent tool from the recommended Python toolchain (`scripts/toolchain_metrics.py`, `scripts/toolchain_graphs.py`; raw outputs `output/tools/`, details `output/cross_validation.md`):

| Metric | Cross-check | Result |
|---|---|---|
| SLOC | Radon `raw`, Pygount | r = 1.000 / 0.998 — identical ranking |
| Cyclomatic | Radon `cc`, mccabe (Flake8 C901) | r = 0.994 (98.1% within ±2) / 0.963 |
| CCN bands | Xenon | 340 vs 378 blocks at CCN ≥ 11 |
| Halstead | token-based textbook formula | r = 0.42 — counting conventions differ; both kept |
| Dependencies | Pydeps, Pyreverse | one merged `zerver` core closure (766 views + 1,143 actions) |
| **Layering** | **Import-linter** (3 contracts) | **all BROKEN — 105 illegal chains** (lib→actions: 54, webhooks→views: 33, models→views: 6; zilencer/confirmation/corporate stay independent) |

The layering result is the strongest new finding: the intended layer separation is systematically violated (e.g. `zerver.lib` → `zerver.actions`), pointing at the same coupled `lib ↔ actions` core Pydeps shows and pylint's 524 cyclic imports flag.

## 6. Conclusions

1. **`apply_event` (`events.py`) is the audit's top hotspot** — cognitive 955, CCN 368, 98 commits: an order of magnitude beyond any guideline, and the epicenter of the event subsystem.
2. **Architecture**: `zerver/` is one coupled closure; layering is violated (Import-linter) and 524 cyclic imports confirm it. Refactoring candidates: the `lib ↔ actions` boundary, and webhook views that embed full message parsers.
3. **Size/complexity**: medians are healthy; risk is concentrated in a short tail (top-10 functions, 104 god classes).
4. **Process**: event + stream subsystems are the most tightly interwoven; `local.py`/`s3.py` lockstep is a shotgun-surgery target; 1,198 single-author files feed the Stage-2 bus-factor analysis.

*Limitations: shallow clone (25 months); pylint without Zulip's runtime deps (import-error artifact); DIT/CBO ignore external Django bases; PyDriller churn cross-check not completed — PyDriller 2.12's `modified_files` exposes basenames only, not paths (library limitation; the script is fixed for future runs).*
