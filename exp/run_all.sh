#!/usr/bin/env bash
# Reproduce every number in results/icde27 (ICDE 2027 submission). Needs scripts/fetch_data.sh first,
# and FastRFD built per baselines/README.md for b2_fastrfd.py. Runs jobs in parallel; ~hours on 100+ cores.
set -u
cd "$(dirname "$0")/.."
P=".venv/bin/python -I"; L=results/icde27/logs; mkdir -p $L
run() { local log=$1; shift; setsid nohup $P "$@" > $L/$log.log 2>&1 < /dev/null & }
G16='{"n_cities":16000}'
for d in tax ndc; do
  run e1_$d exp/e1_main.py --dataset $d --seeds 3
  run e1b_$d exp/e1b_discovery.py --dataset $d --seeds 3
  run e4_$d exp/e4_closure.py --dataset $d --kw '{}'
done
run e1_geonames16k exp/e1_main.py --dataset geonames --kw "$G16" --seeds 3 --tag _16k
run e1b_geonames16k exp/e1b_discovery.py --dataset geonames --kw "$G16" --seeds 3 --tag _16k
run e4_geonames exp/e4_closure.py
run e2 exp/e2_scale.py --sizes 1000 4000 16000 64000 128000 --seeds 2
run e3_geonames exp/e3_coverage.py --reps 500
run e3_tax exp/e3_coverage.py --dataset tax --kw '{"near_miss": [0.03, 0.04, 0.05, 0.06, 0.07]}' --reps 500
run e7_geonames exp/e7_noise.py
run e7_ndc exp/e7_noise.py --dataset ndc --kw '{}'
for px in tfidf emb edit; do
  run e5_geonames16k_$px exp/e1_main.py --dataset geonames --kw "$G16" --seeds 3 --proxy $px --tag _16k_$px
  run e5_ndc_$px exp/e1_main.py --dataset ndc --seeds 3 --proxy $px --tag _$px
done
# sensitivity (proxy, k, theta, rho) and the witness-slack diagnostic
for k in 3 10; do run e6_geo_k$k exp/e1_main.py --dataset geonames --kw "$G16" --seeds 3 --k $k --tag _16k_k$k
  run e6_ndc_k$k exp/e1_main.py --dataset ndc --seeds 3 --k $k --tag _k$k; done
for th in 0.8 0.95; do run e6_geo_th$th exp/e1_main.py --dataset geonames --kw "$G16" --seeds 3 --theta0 $th --tag _16k_th$th
  run e6_ndc_th$th exp/e1_main.py --dataset ndc --seeds 3 --theta0 $th --tag _th$th; done
for rho in 0.05 0.5; do run e6_geo_rho$rho exp/e1_main.py --dataset geonames --kw "{\"n_cities\":16000,\"rho\":$rho}" --seeds 3 --tag _16k_rho$rho; done
run e3_ideal exp/e3_ideal_witness.py
# two-attribute LHS (E9), FastRFD baseline (B2; needs the jar), fairness baseline, running example, MusicBrainz probe
for spec in "geonames|{\"n_cities\":16000}|_16k" "tax|{}|" "ndc|{}|"; do IFS='|' read d kw tag <<< "$spec"
  run e9_$d$tag exp/e9_multi.py --dataset $d --kw "$kw" --tag "$tag"
  run b2_$d$tag exp/b2_fastrfd.py --dataset $d --kw "$kw" --tag "$tag" --timeout 7200
done
run b2_geonames_1k exp/b2_fastrfd.py --dataset geonames --kw '{"n_cities":1000}' --tag _1k
for d in ndc tax; do run b2_${d}_finegrid exp/b2_fastrfd.py --dataset $d --ts 0.0001 0.0005 --tag _finegrid --timeout 10800; done
run canon_variant_only exp/canon_variant_only.py
run ndc_example exp/ndc_example.py
run mb_probe exp/mb_probe.py
# review-v5 additions: all candidates at 640k rows, incomplete inverse, updates, self-refining witness
run e1b_geonames640k exp/e1b_discovery.py --dataset geonames --kw '{"n_cities":128000,"source":"cities500.txt"}' --seeds 2 --tag _640k
run e11_geonames exp/e11_partial_inverse.py --dataset geonames --kw "$G16" --tag _16k
run e11_tax exp/e11_partial_inverse.py --dataset tax
run e11_ndc exp/e11_partial_inverse.py --dataset ndc
run e10_small exp/e10_updates.py --ins 0.004 --dele 0.002 --seeds 3 --tag _small
run e10_large exp/e10_updates.py --ins 0.02 --dele 0.01 --seeds 3 --tag _large
run e10_small128k exp/e10_updates.py --ins 0.004 --dele 0.002 --n-cities 128000 --seeds 1 --tag _small128k
run e3_refine exp/e3_refine.py --reps 200
# review-v6 addition: hidden aliases (neighbor-only mode fails, inverse rejects)
run e12_hidden_alias exp/e12_hidden_alias.py --seeds 3
run e11_geonames_official exp/e11_partial_inverse.py --dataset geonames --kw "$G16" --tag _16k --official
run e11_tax_official exp/e11_partial_inverse.py --dataset tax --official
for m in unary pairs; do
  run e13_geonames_$m exp/e13_planner.py --dataset geonames --kw "$G16" --tag _16k --mode $m
  run e13_tax_$m exp/e13_planner.py --dataset tax --mode $m
  run e13_ndc_$m exp/e13_planner.py --dataset ndc --mode $m; done
# E8 (LLM oracle; needs llama-cpp-python and the GGUF in $E8_MODEL). Sequential and long: run separately:
#   OMP_NUM_THREADS=1 nice -n 15 .venv/bin/python -I exp/e8_llm_oracle.py --canon --procs 4 --threads 6
#   .venv/bin/python -I exp/e8_llm_oracle.py --offline --seeds 3
#   .venv/bin/python -I exp/e8_llm_oracle.py --tokens --seeds 3      # prompt tokens (tokenizer only, no inference)
#   .venv/bin/python -I exp/e8_llm_oracle.py --sample 400 --timing 20 --threads 16   # latency measurement
wait
if [ "${WITH_E8:-0}" = "1" ]; then   # LLM oracle (hours on CPU; needs llama-cpp-python and $E8_MODEL)
  OMP_NUM_THREADS=1 $P exp/e8_llm_oracle.py --canon --procs 4 --threads 6 > $L/e8_canon_all.log 2>&1
  $P exp/e8_llm_oracle.py --offline --seeds 3 > $L/e8_offline.log 2>&1
  OMP_NUM_THREADS=1 $P exp/e14_llm_tax_city.py --canon --procs 4 --threads 6 > $L/e14_canon.log 2>&1
  $P exp/e14_llm_tax_city.py --seeds 3 > $L/e14_offline.log 2>&1
  $P exp/e8_llm_oracle.py --tokens --seeds 3 > $L/e8_tokens.log 2>&1
  $P exp/e8_llm_oracle.py --sample 400 > $L/e8_sample.log 2>&1
  $P exp/e8_llm_oracle.py --sample 400 --timing 20 --threads 16 > $L/e8_latency.log 2>&1
  $P exp/e8_llm_oracle.py --replay-check 200 --threads 12 > $L/e8_replay_check.log 2>&1
fi
echo "done; now: $P exp/make_tables.py && $P exp/make_figures.py"
