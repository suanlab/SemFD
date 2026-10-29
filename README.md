# Certifying Functional Dependencies over Latent Entity Identity

SemFD: code and reproduction package for the ICDE 2027 submission *Certifying Functional Dependencies over Latent Entity
Identity* by Wookey Lee (Inha University) and Suan Lee (Semyung University).

Repository: https://github.com/suanlab/SemFD. Full proofs and the LLM-oracle protocol are in the technical report,
[`docs/techreport.pdf`](docs/techreport.pdf).

## The idea

A functional dependency X → Y is evaluated over entity identity. An oracle `f_A` maps each attribute value to an
entity; it can be entity-resolution ground truth, a knowledge base, or an LLM canonicalizer. Cheap proxies (edit
distance, character n-gram TF-IDF, sentence embeddings) are used only to build a *repair witness*. Sampled tuples are
then audited against the oracle, which yields a one-sided (1−α) upper bound on the g3 error of the FD over the
entity-resolved instance. That instance is never materialized.

## Layout

| Path | Contents |
|---|---|
| `semfd/` | The SemFD library |
| `exp/` | One script per experiment, plus `make_tables.py` / `make_figures.py`, which regenerate every number, table and figure of the paper from `results/icde27/*.json` |
| `results/icde27/` | Result JSONs used in the paper, `TABLES.md`, `PAPER_NUMBERS.md` (every number quoted in the paper), `DATA_SNAPSHOTS.txt` (sha256 of the input data) |
| `paper/tables/`, `paper/fig_*.pdf` | Generated tables and figures, as included in the paper |
| `docs/techreport.pdf` | Technical report: full proofs, LLM prompt and protocol |
| `pilot/` | GeoNames and Tax table generators, imported by `semfd/data.py` |
| `tests/` | Unit tests |
| `scripts/fetch_data.sh` | Downloads the datasets |
| `baselines/` | How to build FastRFD; Desbordante comes from pip |

Modules in `semfd/`:
- `oracle.py`: canonicalizer oracle with call accounting and inverse (alias) access.
- `proxy.py`: proxy index, neighbors and partitions.
- `certify.py`: repair-witness certificate and confidence sequence.
- `closure.py`: certified closure.
- `maintain.py`: bound propagation under updates.
- `composite.py`: two-attribute left-hand sides.
- `planner.py`: the per-candidate cap (E1b variant) and the run-level extrapolating planner (E13), evaluated in the paper and not used by the system; the pre-registered run-wide budget is in `exp/e18_variants.py`.
- `baselines.py`: the baselines.
- `data.py`: dataset loaders and probe injection.

Experiments in `exp/`:

| Script | Paper section |
|---|---|
| `e1_main.py` | correctness and baselines |
| `e1b_discovery.py` | discovery vs. TANE |
| `e2_scale.py` | scaling |
| `e3_coverage.py` | coverage and power |
| `e3_ideal_witness.py` | witness-slack diagnostic |
| `e4_closure.py` | derived dependencies |
| `e7_noise.py` | oracle noise |
| `e8_llm_oracle.py` | LLM oracle |
| `e9_multi.py` | two-attribute LHS |
| `b2_fastrfd.py` | FastRFD baseline |
| `canon_variant_only.py` | fairer resolution baselines |
| `ndc_example.py` | running example |
| `mb_probe.py` | MusicBrainz feasibility check |
| `e10_updates.py` | certificates under updates |
| `e11_partial_inverse.py` | incomplete inverse access and the audit split |
| `e12_hidden_alias.py` | hidden aliases: neighbor-only mode fails where the inverse rejects |
| `e13_planner.py` | run-level extrapolating planner (not used by the system) |
| `e14_llm_tax_city.py` | second LLM oracle attribute (Tax city names; needs the GGUF model, cached answers included) |
| `e15_slack.py` | witness-slack decomposition |
| `e16_gleif.py` | GLEIF as a real alias registry for NDC labelers; LEI as an independent oracle |
| `e17_gpg_registry.py` | UK gender pay gap reports: natural aliases and the Companies House register as alias service |
| `e18_variants.py` | pre-registered variants over all unary candidates: alias-only and TF-IDF audits, self-refining witness, run-wide budget rule |
| `e18_diag_gpg.py`, `e18_diag_sim.py` | diagnostic: exact witness means of GPG name->sic (from the truth, never an algorithm input) and a simulation of certifying a frozen refined witness |
| `e19_end_to_end.py`, `run_e19.sh`, `e19_proxy_cold.py` | pre-registered end-to-end wall clock with a live local LLM oracle: certify vs canonicalize-all on NDC (several hours; needs the GGUF model) |
| `e22_fixed_oracle_replay.py` | pre-registered replay of the E19 certify arm (seeds 0–9) against the resolve run's saved answers as one fixed oracle (no LLM call; minutes) |
| `e20_scaling.py` | pre-registered scaling with rows, domain size and candidate count varied separately (GeoNames) |
| `e23_scaling_tax.py` | the same three sweeps repeated on Tax (pre-registered, 2 seeds) |
| `n1_probe_wa.py` | probe for a natural table where the audit could change a decision (Walmart–Amazon brands): entry criterion g3 under the oracle ≤ 2δ with the audit moving the mean across δ; failed (all 12 natural candidates have g3 ≥ 0.153), so the follow-up was not run |
| `e21_natural_audit.py` | pre-registered check whether the audit changes a decision on natural data (GPG names, NDC labelers; exact means from the truth) |
| `e3_refine.py` | self-refining witness (power) |

## Reproduce

Requires Python 3.12, CPU only. The paper's runs used a shared server with two Intel Xeon Gold 6258R CPUs and 502 GB RAM.

```bash
uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python -r requirements.lock \
    --extra-index-url https://download.pytorch.org/whl/cpu --index-strategy unsafe-best-match   # torch==...+cpu is on the PyTorch index only
./scripts/fetch_data.sh                       # downloads data; exits 1 on a mismatch with results/icde27/DATA_SNAPSHOTS.txt
.venv/bin/python -m pytest -q tests/          # unit tests (< 1 min)
SEMFD_OVERWRITE=1 JOBS=8 ./exp/run_all.sh     # non-LLM experiments, rewriting results/icde27 in place; WITH_E8=1 adds E8/E14 (hours)
./exp/run_e19.sh                              # separate live LLM timing study (hours)
.venv/bin/python -I exp/e19_proxy_cold.py      # proxy build with empty caches
.venv/bin/python -I exp/make_tables.py && .venv/bin/python -I exp/make_figures.py
```

- **FastRFD baseline.** `exp/b2_fastrfd.py` needs FastRFD built as described in `baselines/README.md` (JDK ≥ 18,
  Maven). Point to the jar and the JDK with `FASTRFD_JAR` and `FASTRFD_JAVA` (otherwise `java` on `PATH`); `FASTRFD_XMX` sets the heap (default 200g).
- **LLM oracle (E8).** Needs `llama-cpp-python` and the Qwen2.5-7B-Instruct Q4_K_M GGUF file; give its path in
  `E8_MODEL`. `requirements.lock` lists its sha256. All 6,653 cached LLM answers are included in
  `results/icde27/e8_llm_canon.json`, so `exp/e8_llm_oracle.py --offline` reproduces the certification results without
  running the model.
- **Determinism and drift.** Random streams are seeded per FD with `zlib.crc32`; exact replay also requires the same
  proxy/model versions, caches and execution environment. GeoNames and the FDA NDC directory change upstream, so `fetch_data.sh` stops when a fresh
  download differs from the snapshot used in the paper (`SEMFD_ALLOW_DRIFT=1` continues; numbers then differ). `run_all.sh` rewrites the committed
  JSON in place and asks for `SEMFD_OVERWRITE=1`; compare with `git diff results/icde27`. `JOBS` (default 8) limits concurrent jobs and `THREADS` caps
  library threads per job. A full rerun on 2026-10-21 of the 54 jobs then in
  `run_all.sh`, on the paper's snapshots, reproduced every decision, oracle-call count and bound (wall-clock times vary
  with server load); experiments added after that date were run once. `exp/make_tables.py` regenerates every table and
  number byte-identically from the committed JSON.

## Data sources and licenses

Datasets are not redistributed. `scripts/fetch_data.sh` downloads them from:

| Dataset | Source | License |
|---|---|---|
| GeoNames | download.geonames.org | CC BY 4.0 |
| GLEIF LEI Golden Copy | goldencopy.gleif.org | CC0 1.0 |
| UK gender pay gap reports | gender-pay-gap.service.gov.uk | Open Government Licence v3.0 |
| Companies House Free Company Data Product | download.companieshouse.gov.uk | no licence on the download page; Companies House places no restriction on use of register information (s.47 CDPA approvals, GOV.UK "Public task, copyright and Crown copyright"); credited as source; not redistributed |
| Raha Tax | github.com/BigDaMa/raha | repository Apache-2.0 |
| FDA NDC directory | accessdata.fda.gov | U.S. Government work |
| MusicBrainz benchmark | Leipzig DAPO | CC BY 4.0 |

Desbordante (AGPL-3.0) is used as a library. FastRFD is built from its upstream repository and is not redistributed.

The code in this repository is released under the MIT license (`LICENSE`).

## Known limitations of the evidence

- E19 live LLM answers differ slightly across runs (10–13 normalized labels per certification seed differ from the resolve run): the live E19 decisions are not tests against one fixed mapping. E22 replays the certify arm (seeds 0–9) against the resolve run's saved answers as one fixed oracle: none of the ten runs made a false certification (70 decisions that share a table, oracle and cache per run, so the run is the statistical unit), and one of the twenty true-FD opportunities was missed. An offline check over all 6,653 saved labels (evaluation only) gives a miss mass of at most 0.0051 for this mapping, below the declared 0.01; this does not carry over to another mapping or service.
- GPG employer names and company numbers both come from Companies House for private and voluntary-sector employers, so the register study tests alias coverage, not independent identity truth.
- The embedding model is loaded at a pinned revision; the cache key contains the model name and the values, and `results/cache/emb/manifest.json` records the revision and device per model, so vectors from another revision or device are refused. Embeddings run on CPU unless `SEMFD_DEVICE` says otherwise. FAISS HNSW (domains above 30k values) uses all cores by default, as in the paper's runs; `THREADS=n` caps it but may change neighbour sets and therefore calls.
- FastRFD reads CSV by splitting every line on commas (no quoting), so `b2_fastrfd.py` replaces commas inside values by spaces after Layer-1 normalization. It prints a rule with an empty left-hand side as ` --> [Y(<=d)]`; wrappers before 2026-10-29 dropped those lines, which can hide X → Y for every X. A pre-registered rerun of all 40 saved configuration × t runs with the corrected wrapper (`literature/prereg_b2_recheck_2026-10-29.md`, `results/icde27/b2_recheck/`) printed no such rule and reproduced every count, so the saved B2 results stand. The wrapper now counts them, checks FastRFD's exit code and saves its full output under `results/icde27/logs/`.
- E23 repeats E20's sweeps on Tax (2 seeds): repeating rows 4× or 16× changed calls by at most 3.7% relative to the unrepeated table, but the domain and candidate sweeps were not monotone, because one injected probe within 0.012 of δ (`zip->city_e8`) took up to 70% of a run's calls and its g3 moves with resampling (0.024–0.060). E23 therefore does not confirm E20's domain and candidate trends on a second dataset. No run made a false certification (0 of 20), but the true probe (g3 0.044–0.048) stopped at the sample cap uncertified in 8 of the 20 runs. The run's random streams start with `e20|e23|` (prereg said `e23`), a naming difference only.
- A replay of NDC E1b reproduced decisions, samples and calls; stored historical bounds were unclipped while the current code reports bounds clipped to [0, 1].

