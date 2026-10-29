# Pre-registration: B2 recheck, FastRFD rules with an empty left-hand side (2026-10-29)

Written before any run. Trigger: `CHECK.md` H05 (audit of 10-29).

## Why
FastRFD prints a rule with an empty left-hand side as ` --> [Y(<=d)]` (`PredicatesBuilder.printRFD`). The B2 wrapper's
pattern required a leading `[`, so such lines were dropped. A minimal RFD ∅ → Y(≤d) makes every X → Y(≤d) non-minimal,
so FastRFD does not print it, and the old wrapper scored X → Y as not accepted. This matters only if some column is
nearly constant within a threshold: e.g. Tax `state` is tolerant, its values are 2-letter codes, and the grid {0,1,2,3}
puts every pair within distance 2. On the GeoNames 1k table (rerun 10-29 with the new wrapper) no empty-LHS rule
appeared and every count matched the saved file.

## Design
- Wrapper `exp/b2_fastrfd.py` as of 10-29: Java resolved at run time; a non-zero exit raises; full stdout/stderr
  saved under `results/icde27/logs/`; input hash recorded; an empty-LHS rule ∅ → Y counts every candidate X → Y as
  accepted (scoring rule unchanged otherwise: X → Y accepted if FastRFD reports it with any RHS threshold).
- Rerun every saved B2 configuration of `exp/run_all.sh` (GeoNames 16k: grid, thr 1, thr 2; GeoNames 1k; Tax: grid,
  fine grid; NDC: grid, thr 1, thr 2, fine grid; GPG) with the same arguments and tag suffix `_recheck`, so the saved
  files are not overwritten. Heap 100g instead of 200g (runs in parallel); an out-of-memory exit is reported, not
  hidden.

## Decision rule
- For each configuration and t: compare accepted / false / missed with the saved file.
- If all equal: the saved tables stand; record that no empty-LHS rule changed a decision.
- If any differ: the old wrapper was wrong for that table. The `_recheck` numbers replace the saved ones (file renamed
  over the old one, old file kept in git history), Tables/PN are regenerated, and every changed sentence is listed in
  the plan log. Either outcome is reported.
