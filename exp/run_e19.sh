#!/bin/bash
set -euo pipefail
# E19 run order fixed in literature/prereg_e19_2026-10-23.md
cd "$(dirname "$0")/.." || exit 1
mkdir -p logs
PY=${PYTHON:-.venv/bin/python}
export OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16
for step in "certify --seed 0" "resolve" "certify --seed 1" "certify --seed 2"; do
  set -- $step
  tag=$1${3:+_s$3}
  nice -n 10 $PY exp/e19_end_to_end.py --arm $step --threads 16 > logs/e19_$tag.log 2>&1
  if [ "$tag" != "$1" ]; then
    mv "results/icde27/e19_$1.json" "results/icde27/e19_$tag.json"
  fi
done
