# Pre-registration: R-B full run, SEC EDGAR filer names (2026-11-03)

The entry probe passed (`literature/prereg_rb_sec_probe_2026-11-03.md`, result `results/rebuttal27/rb_sec_probe.json`,
commit a9e6fa9). This document fixes the full run before it starts. Code: `exp/rb_sec_discovery.py` (loader and
runner; `semfd/` is not changed). Result: `results/rebuttal27/rb_sec_discovery.json`. Run after the manuscript
freeze; the submitted paper, `results/icde27/` and its tables do not change.

## Table
SEC sub.txt 2015q1–2024q4 as in the probe (one row per submission). Columns: `name` (tolerant; oracle = cik),
`cik`, `sic`, `countryba`, `stprba`, `cityba`, `fye` (exact, Layer-1). Names filed under two or more ciks are dropped
(homonyms; 61 names, 1,617 rows in the probe). `name`↔`cik` hold by construction and are excluded, as for GPG.
Unary candidates: all ordered pairs of the seven columns except those two (40).

## Methods (unchanged code, default settings of the paper)
- **Ours, complete inverse:** `exp/e1b_discovery.run_one` (δ = 0.05, α = 0.05 split over the candidates, θ = 0.9,
  k = 5, hybrid proxy, shared caches), which also runs TANE on raw and Layer-1 strings, the proxy quotient (B1), the
  estimator without the audit (B9), the planner, certified closure and canonicalize-all. Seeds 0–2.
- **Incomplete inverse:** the E11 procedure (inverse returns each in-data spelling with probability p, fixed hash),
  p ∈ {0.5, 0.0}; p = 0 is neighbour-only. As in E11 the certificate runs unchanged (ν̄ = 0); measured ν per
  candidate. Seeds 0–2.

## Recorded
False certifications and missed true FDs (truth: g3 under the cik oracle ≤ δ) for every method; our oracle calls
(forward + inverse) against canonicalize-all; derived FDs violating their bound; ν per candidate for p < 1;
the list of candidates whose decision differs between strings and the oracle (from the probe: name→stprba).

## Pre-stated expectations and criteria
- **Primary:** no false certification by ours with the complete inverse (3 seeds). Each one is reported.
- **Secondary:** missed true FDs; calls vs canonicalize-all (16.4k names: the domain is mid-sized, so a cost win is
  not expected and none is claimed if it is absent); whether TANE on raw or normalized strings accepts name→stprba
  (false under the oracle, true on strings in the probe), and whether ours rejects it; behaviour at p = 0.5 and 0.
- **Whatever the outcome**, the result is reported as run after the freeze, not in the submitted paper.
- Time box: two days of compute from this commit; on timeout, report what finished.

## Deviation (recorded 2026-11-03, after the run)
After seeing that the E11 neighbour-only setting (ν̄ = 0) certified name→stprba in every seed, a sensitivity run with
the paper's declared ν̄ = 0.01 was added (`exp/e25_sec_nubar.py`, `results/icde27/e25_sec_nubar.json`). It was not
pre-registered and is labelled post hoc wherever it is reported. By the authors' decision of 11-03 (superseding "not in the submitted paper" above), the experiment is reported in the paper as E25
(results moved from `results/rebuttal27/` to `results/icde27/e25_sec_*.json`, numbers through `make_tables.py`).
