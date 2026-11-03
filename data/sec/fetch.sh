#!/usr/bin/env bash
# Fetch sub.txt of the SEC Financial Statement Data Sets 2015q1-2024q4. SEC requires a contact User-Agent:
#   SEC_UA="<name> <email>" data/sec/fetch.sh
set -euo pipefail
: "${SEC_UA:?set SEC_UA to '<name> <email>'}"
cd "$(dirname "$0")"
for y in $(seq 2015 2024); do for q in 1 2 3 4; do
  f=${y}q${q}; [ -s "sub_$f.txt" ] && continue
  curl -fsSL -A "$SEC_UA" -o "$f.zip" "https://www.sec.gov/files/dera/data/financial-statement-data-sets/$f.zip"
  unzip -p "$f.zip" sub.txt > "sub_$f.txt" && rm -f "$f.zip"; echo "$f $(wc -l < sub_$f.txt)"; sleep 1
done; done
sha256sum sub_*.txt > SHA256.txt
