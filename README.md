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
| `e20_scaling.py` | pre-registered scaling with rows, domain size and candidate count varied separately (GeoNames) |
| `e21_natural_audit.py` | pre-registered check whether the audit changes a decision on natural data (GPG names, NDC labelers; exact means from the truth) |
| `e3_refine.py` | self-refining witness (power) |

## Reproduce

Requires Python 3.12, CPU only. The paper's runs used a shared server with two Intel Xeon Gold 6258R CPUs and 502 GB RAM.

```bash
uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python -r requirements.lock
./scripts/fetch_data.sh                       # downloads data and checks it against results/icde27/DATA_SNAPSHOTS.txt
.venv/bin/python -m pytest -q tests/          # unit tests (< 1 min)
./exp/run_all.sh                              # all experiments, in parallel; WITH_E8=1 also reruns the LLM study (hours)
.venv/bin/python -I exp/make_tables.py && .venv/bin/python -I exp/make_figures.py
```

- **FastRFD baseline.** `exp/b2_fastrfd.py` needs FastRFD built as described in `baselines/README.md` (JDK ≥ 18,
  Maven). Point to the jar and the JDK with `FASTRFD_JAR` and `FASTRFD_JAVA`.
- **LLM oracle (E8).** Needs `llama-cpp-python` and the Qwen2.5-7B-Instruct Q4_K_M GGUF file; give its path in
  `E8_MODEL`. `requirements.lock` lists its sha256. All 6,653 cached LLM answers are included in
  `results/icde27/e8_llm_canon.json`, so `exp/e8_llm_oracle.py --offline` reproduces the certification results without
  running the model.
- **Determinism and drift.** Random streams are seeded per FD with `zlib.crc32`, so a given data snapshot reproduces
  the numbers exactly. GeoNames and the FDA NDC directory change upstream, so `fetch_data.sh` warns when a fresh
  download differs from the snapshot used in the paper. A full rerun on 2026-10-21 of the 54 jobs then in
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
