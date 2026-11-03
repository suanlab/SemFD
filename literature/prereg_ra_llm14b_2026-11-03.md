# Pre-registration: R-A, a second LLM oracle (Qwen2.5-14B) for the NDC labeler names (2026-11-03)

This document fixes the design before any run. Code: `exp/ra_llm14b.py`. Results: `results/rebuttal27/ra_canon_14b.json`
(answers) and `results/rebuttal27/ra_llm14b.json` (analysis). Plan: `literature/rebuttal_experiments_plan_2026-11.md`
(R-A). The run is after the manuscript freeze (`icde27-freeze`) and does **not** change the submitted paper, its
tables or `results/icde27/PAPER_NUMBERS.md`. It is for the rebuttal (if new results are allowed) and a later venue.

## Why
Mock reviewers asked whether the LLM-oracle results depend on the single 7B model (FAQ E3). The paper's LLM oracle is
Qwen2.5-7B-Instruct Q4_K_M (E8: B-cubed F1 0.948 against the labeler-code oracle; certification replayed in 3 seeds).

## Question
With a larger model as the oracle under the same protocol, (a) how close is its equivalence on the labeler names to
the labeler-code oracle and to the 7B oracle, and (b) does certification, replayed against its answers as one fixed
oracle, make false certifications or misses relative to the exact decisions under that oracle, at what call count?

## Fixed design
- **Model:** `/data2/llbench/models/Qwen2.5-14B-Instruct-Q4_K_S.gguf` (sha256 1350a659484c31b4d7123211733cc0deb4ab56e47ca8e2fc04b6a0c3b2e2c999,
  computed before the run; also stored in the result file). Same family as the 7B model; this limits the conclusion and is stated with the result.
- **Protocol (unchanged from E8):** `SYSTEM` and the 4 few-shot pairs of `exp/e8_llm_oracle.py`, ChatML template
  (from the GGUF), temperature 0, `max_tokens` 24, `n_ctx` 512, first line of the reply; the model sees the most
  frequent raw spelling of each Layer-1 value; label = `"llm:" + [a-z0-9] of layer1(answer)`.
- **Step 1 (resolve):** canonicalize all 6,653 labeler values once (4 processes × 14 threads, `nice`), saving every
  answer and per-call latency. Only this step calls the model.
- **Step 2 (replay, no model calls):** the seven natural NDC candidates (`ndc(seed=0, near_miss=())`), δ = 0.05,
  α = 0.05 split over the seven, θ = 0.9, ν̄ = 0.01, neighbour-only (heuristic) mode, Algorithm 1 as in E8/E22, random
  streams `e8o|seed|X|Y` (the E22 keys), answer cache shared across the candidates of one run. Seeds 0–9.
- **Reference decisions:** exact g3 under the 14B labels < δ.
- **Recorded:**
  - per seed: decisions, U, samples, distinct oracle calls (against 6,653 for resolving every name);
  - offline (evaluation only): exact g3 of each candidate under the 14B labels, the 7B labels
    (`results/icde27/e8_llm_canon.json`) and the labeler-code oracle; miss mass ν of the neighbour-only witness;
  - agreement (pair precision/recall, B-cubed) of the 14B labels with the code oracle and with the 7B labels;
  - disagreement mass m (oracle-transfer proposition) between 14B and code, and between 14B and 7B; transferred
    bounds U + ν̄ + m for every certified decision, and how many are below the g3 of the other oracle (violations);
  - mean and median per-call latency of step 1.

## Pre-stated expectations and criteria
- **Primary:** number of false certifications over 10 seeds × 7 candidates relative to the 14B reference. Expected 0;
  α is per run, so a false certification can occur at a rate up to about 0.05 per run. Each one is reported.
- **Secondary:** missed reference-true candidates (and which seeds); calls per run against 6,653; ν against ν̄ = 0.01.
- **Descriptive (no threshold):** B-cubed F1 against the code oracle (7B: 0.948); whether the set of true candidates
  under 14B equals that under 7B and under the code oracle; transfer violations (the proposition says 0).
- **Whatever the outcome**, the result is reported as run after the manuscript freeze (not in the submitted paper), with the same-family limitation. If the
  model output is malformed for some names (empty first line), those names keep their (empty) label and are counted.

## Not changed by this experiment
The manuscript, system defaults, `results/icde27/` and every table of the submitted paper.

## Smoke test before registration (not part of the results)
Five hand-typed names, one process, 14 threads, 1.4–4.9 s per call (first call includes loading), e.g.
"WAL-MART STORES INC" → "Walmart", "Equate (Wal-Mart Stores, Inc.)" → "Wal-Mart Stores". No NDC values were sent.
