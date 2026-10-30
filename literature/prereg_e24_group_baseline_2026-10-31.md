# Pre-registration: E24, entity-group (modal) estimator under a complete inverse (2026-10-31)

Written and committed before any run. Trigger: `REVIEW_SIMULATION_ICDE.md` R2 (reviewers A and C): with a complete
inverse, a simpler certifier needs no proxy witness.

## Estimator
For a uniformly sampled tuple t with X-value a: e = f_X(a) (one forward call, cached), S = f_X^{-1}(e) ∩ dom(X) (one
inverse call per entity, cached; for an identifier-like X, S = {a} and no call), G = all tuples whose X-value is in S.
Canonicalize every distinct Y-value occurring in G (one forward call each, cached; free for an identifier-like Y) and set
B_grp(t) = 1 − (largest Y-entity count in G)/|G|. The tuple-weighted mean of B_grp is exactly g3 (no witness slack, ν = 0).
Same confidence sequence (`eb_cs`), one-sided α/|C|, batch 100, at most 20,000 samples, same stopping rule (certify iff
U < δ; stop for futility when L ≥ δ) and the same per-candidate random stream as E1b/E18 (`e1b|seed|x|y`).

## Design
- Script `exp/e24_group_baseline.py`; variants `plain` (the system, must reproduce E18 `plain` / E1b exactly) and
  `group`; both start each run with empty caches, and caches are shared across candidates within a run as in E18.
- Datasets and seeds as E18: GeoNames-16k, Tax, NDC, GPG, 3 seeds each; also GeoNames 640k rows (2 seeds, as E1b).
- Reported per dataset and seed: false certifications, missed true FDs, total calls (forward + inverse), and for `group`
  the number of Y-calls; the ratio group/plain of total calls.
- Sanity: an exhaustive average of B_grp over all tuples equals `g3_codes` (unit test); `plain` equals E18 `plain`.

## Expectation (not a decision criterion)
`group` has no slack, so it should be at least as powerful. Its cost per sampled entity grows with the number of distinct
Y-values in the entity's rows, so it should be cheaper for high-cardinality X and more expensive for low-cardinality X
(e.g. country, state), where one group can cover most of dom(Y). We do not predict the sign of the total.

## Reporting rule (either outcome)
- One sentence in Section VI next to the E18 alias-only result, numbers via `make_tables.py` → PAPER_NUMBERS, plus the
  rebuttal FAQ and READMEs. The default system is not changed.
- If `group` costs less in total on a dataset without missing more true FDs, the paper says that under a complete
  inverse this simpler estimator is cheaper there, and that the witness is needed for the neighbour-only mode (no inverse).
- If it costs more, the paper states by how much and why (Y-values per entity group).
- Any false certification by either variant is reported. No parameter is changed after seeing results; a crash or
  timeout is reported, not rerun with other settings.
