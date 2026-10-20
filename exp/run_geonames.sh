#!/usr/bin/env bash
# Re-run every GeoNames experiment (used after the 2026-10-19 oracle collision-guard fix). Niced, 4 threads per job.
set -u
cd "$(dirname "$0")/.."
export OMP_NUM_THREADS=4
P="nice -n 10 .venv/bin/python -I"; L=results/icde27/logs; mkdir -p $L
run() { local log=$1; shift; setsid nohup $P "$@" > $L/$log.log 2>&1 < /dev/null & }
G16='{"n_cities":16000}'
run e1_geonames16k exp/e1_main.py --dataset geonames --kw "$G16" --seeds 3 --tag _16k
run e1b_geonames16k exp/e1b_discovery.py --dataset geonames --kw "$G16" --seeds 3 --tag _16k
for px in tfidf emb edit; do run e5_geo_$px exp/e1_main.py --dataset geonames --kw "$G16" --seeds 3 --proxy $px --tag _16k_$px; done
for k in 3 10; do run e6_geo_k$k exp/e1_main.py --dataset geonames --kw "$G16" --seeds 3 --k $k --tag _16k_k$k; done
for th in 0.8 0.95; do run e6_geo_th$th exp/e1_main.py --dataset geonames --kw "$G16" --seeds 3 --theta0 $th --tag _16k_th$th; done
for rho in 0.05 0.5; do run e6_geo_rho$rho exp/e1_main.py --dataset geonames --kw "{\"n_cities\":16000,\"rho\":$rho}" --seeds 3 --tag _16k_rho$rho; done
run e9_geonames16k exp/e9_multi.py --dataset geonames --kw "$G16" --tag _16k
run e4_geonames exp/e4_closure.py
run e7_geonames exp/e7_noise.py
run e3_geonames exp/e3_coverage.py --reps 500
run e3_ideal exp/e3_ideal_witness.py
run e2 exp/e2_scale.py --sizes 1000 4000 16000 64000 128000 --seeds 2
run b2_geonames_16k exp/b2_fastrfd.py --dataset geonames --kw "$G16" --tag _16k --timeout 7200
run b2_geonames_1k exp/b2_fastrfd.py --dataset geonames --kw '{"n_cities":1000}' --tag _1k
run canon_variant_only exp/canon_variant_only.py
wait
