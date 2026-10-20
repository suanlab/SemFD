#!/usr/bin/env bash
# Download every dataset used by exp/ into data/ (not redistributed; see each source's license).
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p data/geonames data/tax data/ndc/x data/musicbrainz
G=https://download.geonames.org/export/dump
for f in cities15000.zip cities500.zip; do curl -sSfL -o data/geonames/$f $G/$f; unzip -o -q data/geonames/$f -d data/geonames; done
curl -sSfL -o data/geonames/countryInfo.txt $G/countryInfo.txt            # CC BY 4.0
curl -sSfL -o data/geonames/admin1CodesASCII.txt $G/admin1CodesASCII.txt
R=https://raw.githubusercontent.com/BigDaMa/raha/master/datasets/tax          # Raha (Apache-2.0 repo)
curl -sSfL -o data/tax/clean.csv $R/clean.csv
curl -sSfL -o data/tax/dirty.csv $R/dirty.csv
curl -sSfL -o data/ndc/ndctext.zip https://www.accessdata.fda.gov/cder/ndctext.zip   # US Gov
unzip -o -q data/ndc/ndctext.zip -d data/ndc/x
curl -sSfL -o data/musicbrainz/mb200k.csv.dapo \
  https://dbs.uni-leipzig.de/files/datasets/saeedi/musicbrainz-200-A01.csv.dapo      # CC BY 4.0
# verify against the snapshot used for the paper (upstream GeoNames/NDC change over time: a mismatch means drift)
if sha256sum --quiet -c <(grep -v '^#' results/icde27/DATA_SNAPSHOTS.txt); then
  echo "done: all files match results/icde27/DATA_SNAPSHOTS.txt"
else
  echo "WARNING: some files differ from the paper's snapshot (upstream drift); numbers may differ slightly" >&2
fi
