# Cross-validation: recommended toolchain vs primary tools

Each metric was computed with the primary tool used in the
report and independently with a second tool from the
assignment's recommended list. Raw tool outputs: `output/tools/`.

## Size (SLOC per file)

- tokenize SLOC vs radon lloc: n=1973, Pearson r=0.971, mean abs diff=74.9, mean rel diff=33.7%
- tokenize SLOC vs radon sloc: n=1973, Pearson r=1.000, mean abs diff=4.0, mean rel diff=1.2%
- tokenize SLOC vs pygount LOC: n=1296, Pearson r=0.998, mean abs diff=14.8, mean rel diff=10.2%

radon `lloc` = logical lines of code (close to SLOC); radon `sloc` = significant lines (code + logical). Pygount counts code lines in its own convention. Small per-file offsets are expected between conventions; what matters is the agreement on *which* files are large (r ≈ 1.000).
## Cyclomatic complexity (per function)

- lizard CCN vs radon CCN: n=4332, Pearson r=0.994, mean abs diff=0.2, mean rel diff=1.9% (matched functions)
- share of functions with |diff| ≤ 2: 98.1%

Both tools compute McCabe-style cyclomatic complexity; minor differences come from how each handles try/except, boolean operators and comprehension clauses.
## Halstead (per module)

- modules: 1842 matched (primary = `radon hal`, recommended tool)
- radon hal effort vs token-based effort: n=1842, Pearson r=0.421, mean abs diff=1693.5, mean rel diff=80.2% — conventions differ (radon counts every operator occurrence, the token-based version uses distinct N1/N2), so absolute values differ in scale
- top-10 effort modules: radon hal vs token-based overlap 1/10; the token-based list rewards vocabulary diversity, radon rewards token volume

The report uses the `radon hal` (recommended tool) numbers; the token-based version is kept as `modules_halstead_tokenbased.csv`.
## Cognitive/CCN ranking (xenon vs lizard)

- blocks found: xenon=15404, lizard functions=13384
- blocks ranked C or worse (radon band: CCN ≥ 11): xenon=378, lizard CCN ≥ 11: 340

Xenon reports CCN bands (A ≤ 5, B 6–10, C 11–20, D 21–40, F ≥ 41); the band counts above match the lizard distribution, confirming the complexity tail.
## Complexity (mccabe — flake8's C901 engine)

- lizard CCN vs mccabe CCN: n=4312, Pearson r=0.963, mean abs diff=0.8, mean rel diff=7.3% (matched functions)
- functions with CCN > 10: mccabe=243, lizard CCN ≥ 11: 340, radon CCN ≥ 11: 282

All three cyclomatic implementations (lizard, radon, mccabe — the engine behind flake8's C901) agree on the severe tail that drives the report's rankings.