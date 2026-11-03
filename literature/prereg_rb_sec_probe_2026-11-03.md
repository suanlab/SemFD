# Pre-registration: R-B entry probe, SEC EDGAR filer names as a natural-alias table (2026-11-03)

This document fixes the probe before any SEC data is downloaded. Plan: `literature/rebuttal_experiments_plan_2026-11.md`
(R-B). Code: `exp/rb_sec_probe.py`. Result: `results/rebuttal27/rb_sec_probe.json`. Run after the manuscript freeze;
the submitted paper, `results/icde27/` and its tables do not change.

## Why
Two of the paper's four datasets inject real alias vocabularies; reviewers asked for more natural-alias evidence (FAQ
E1) and for a natural workload where entity identity changes a decision (FAQ G3; E21 found none in 18 candidates, N1
failed its probe). A probe decides whether a full experiment on SEC filings is worth running.

## Data
- SEC DERA Financial Statement Data Sets (U.S. Government work), `sub.txt` of the quarterly files 2015q1–2024q4
  (40 files; one row per submission). Downloaded with a contact User-Agent as SEC requires; the contact address is
  passed through the environment (`SEC_UA`) and is not stored in the repository or the results. Zips are deleted
  after `sub.txt` is extracted; sha256 of each `sub.txt` is recorded.
- Columns used: `cik`, `name`, `former`, `sic`, `countryba`, `stprba`, `cityba`, `fye`, `form`.
- Value level: Layer-1 normalization of `name` (as for NDC/GPG). Oracle for `name`: the filer's `cik`. A Layer-1
  name filed under two or more ciks has no single entity; its rows are dropped and counted.
- Inverse (for a later full run): the names a cik filed under in the table, plus its `former` names.
- Other columns are exact (string equality after Layer-1), as in the paper.

## Probe measurements (all exact, no sampling, no oracle-call accounting)
For the fixed candidate list below: g3 on the Layer-1 strings and g3 under the cik oracle; the share of tuples whose
cik appears under two or more Layer-1 names; the number of such ciks; and, for those ciks, the share of name pairs
with Levenshtein ratio < 0.9 (aliases a string proxy would not link).

**Candidates (fixed):** name→sic, name→stprba, name→countryba, name→cityba, name→fye, sic→name, stprba→name,
cityba→name (X→name ones are expected false; they test condition (ii)).

## Pass criterion (all three)
1. At least one candidate is true under the oracle (g3 < δ = 0.05) and has `name` on the left;
2. at least one candidate has |g3_strings − g3_oracle| ≥ δ/2 = 0.025, or flips across δ;
3. tuples of multi-name ciks are at least 1% of the table.

Pass → a separate pre-registration of the full run (3 seeds, all unary candidates, inverse and neighbour-only
modes, TANE and canonicalize-all). Fail → stop, record which criterion failed, and answer FAQ E1/G3 without it.
Time box: two days from this commit.
