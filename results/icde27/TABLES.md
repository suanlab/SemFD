## E1 e1_geonames_16k: geonames16000 (3 seeds, δ=0.05, α per FD=0.003846, rows=80000)

| method | true acc. (all) | **false acc. (all)** | true acc. natural | false acc. natural | true acc. probe | false acc. probe | oracle calls / run | note |
|---|---|---|---|---|---|---|---|---|
| B0 exact strings (g3 ≤ δ) | 3/18 | 3/21 | 3/15 | 0/12 | 0/3 | 3/9 | – |  |
| B1 proxy quotient θ=0.9 | 3/18 | 3/21 | 3/15 | 0/12 | 0/3 | 3/9 | – |  |
| B1 proxy quotient θ=0.85 | 3/18 | 3/21 | 3/15 | 0/12 | 0/3 | 3/9 | – |  |
| B1 proxy quotient θ=0.95 | 3/18 | 3/21 | 3/15 | 0/12 | 0/3 | 3/9 | – |  |
| B7 sample-only (m = our n) | 18/18 | 9/21 | 15/15 | 0/12 | 3/3 | 9/9 | 7275 | no guarantee |
| B4 canonicalize-all | 18/18 | 0/21 | 15/15 | 0/12 | 3/3 | 0/9 | 42453 | exact; shared over FDs |
| B5 pairwise blocked self-join | 18/18 | 0/21 | 15/15 | 0/12 | 3/3 | 0/9 | 1812068 | pair judgments; recall-limited |
| ours [inverse] | 18/18 | 0/21 | 15/15 | 0/12 | 3/3 | 0/9 | 15045 | primary, ν=0 (Cor A2) |
| ours [alias_only] | 18/18 | 0/21 | 15/15 | 0/12 | 3/3 | 0/9 | 10041 |  |
| ours [grid_inverse] | 18/18 | 0/21 | 15/15 | 0/12 | 3/3 | 0/9 | 33786 | θ grid, α/|grid| |
| ours [ann_nubar] | 18/18 | 0/21 | 15/15 | 0/12 | 3/3 | 0/9 | 12568 | ANN only, U+ν̄<δ |
| ours [b9_noaudit] | 18/18 | 6/21 | 15/15 | 0/12 | 3/3 | 6/9 | 1232 | B9: no audit (unsound) |

Per FD (mean over seeds): oracle g3, raw g3, ours[inverse] U and calls

| FD | g3 oracle | g3 raw | truth | ours U | ours certified | ours calls | B9 certified | B7 g3 |
|---|---|---|---|---|---|---|---|---|
| city->country | 0.000 | 0.155 | True | 0.038 | 3/3 | 1212 | 3/3 | 0.000 |
| city->admin1 | 0.000 | 0.155 | True | 0.039 | 3/3 | 1416 | 3/3 | 0.000 |
| admin1->country | 0.000 | 0.183 | True | 0.038 | 3/3 | 581 | 3/3 | 0.000 |
| country->admin1 | 0.784 | 0.811 | False | 0.996 | 0/3 | 106 | 0/3 | 0.510 |
| fcode->country | 0.823 | 0.859 | False | 0.965 | 0/3 | 16 | 0/3 | 0.773 |
| admin1->city | 0.738 | 0.714 | False | 0.938 | 0/3 | 229 | 0/3 | 0.123 |
| tz->country | 0.005 | 0.203 | True | 0.041 | 3/3 | 48 | 3/3 | 0.006 |
| country->tz | 0.121 | 0.120 | False | 0.192 | 0/3 | 160 | 0/3 | 0.104 |
| city->country_e2 | 0.020 | 0.167 | True | 0.048 | 3/3 | 3264 | 3/3 | 0.002 |
| city->country_e8 | 0.079 | 0.204 | False | 0.129 | 0/3 | 2555 | 0/3 | 0.011 |
| city->country_src8 | 0.080 | 0.153 | False | 0.124 | 0/3 | 2915 | 3/3 | 0.008 |
| city->tz_src8 | 0.080 | 0.000 | False | 0.132 | 0/3 | 1977 | 3/3 | 0.008 |
| city->tz | 0.000 | 0.000 | True | 0.039 | 3/3 | 565 | 3/3 | 0.000 |

## E1 e1_geonames_16k_edit: geonames16000 (3 seeds, δ=0.05, α per FD=0.003846, rows=80000)

| method | true acc. (all) | **false acc. (all)** | true acc. natural | false acc. natural | true acc. probe | false acc. probe | oracle calls / run | note |
|---|---|---|---|---|---|---|---|---|
| B0 exact strings (g3 ≤ δ) | 3/18 | 3/21 | 3/15 | 0/12 | 0/3 | 3/9 | – |  |
| B1 proxy quotient θ=0.9 | 6/18 | 3/21 | 6/15 | 0/12 | 0/3 | 3/9 | – |  |
| B1 proxy quotient θ=0.85 | 3/18 | 0/21 | 3/15 | 0/12 | 0/3 | 0/9 | – |  |
| B1 proxy quotient θ=0.95 | 3/18 | 3/21 | 3/15 | 0/12 | 0/3 | 3/9 | – |  |
| B7 sample-only (m = our n) | 18/18 | 9/21 | 15/15 | 0/12 | 3/3 | 9/9 | 12280 | no guarantee |
| B4 canonicalize-all | 18/18 | 0/21 | 15/15 | 0/12 | 3/3 | 0/9 | 42453 | exact; shared over FDs |
| B5 pairwise blocked self-join | 18/18 | 0/21 | 15/15 | 0/12 | 3/3 | 0/9 | 1059964 | pair judgments; recall-limited |
| ours [inverse] | 18/18 | 0/21 | 15/15 | 0/12 | 3/3 | 0/9 | 20777 | primary, ν=0 (Cor A2) |
| ours [alias_only] | 18/18 | 0/21 | 15/15 | 0/12 | 3/3 | 0/9 | 16161 |  |
| ours [grid_inverse] | 18/18 | 0/21 | 15/15 | 0/12 | 3/3 | 0/9 | 45054 | θ grid, α/|grid| |
| ours [ann_nubar] | 17/18 | 0/21 | 15/15 | 0/12 | 2/3 | 0/9 | 16460 | ANN only, U+ν̄<δ |
| ours [b9_noaudit] | 18/18 | 1/21 | 15/15 | 0/12 | 3/3 | 1/9 | 1933 | B9: no audit (unsound) |

Per FD (mean over seeds): oracle g3, raw g3, ours[inverse] U and calls

| FD | g3 oracle | g3 raw | truth | ours U | ours certified | ours calls | B9 certified | B7 g3 |
|---|---|---|---|---|---|---|---|---|
| city->country | 0.000 | 0.155 | True | 0.042 | 3/3 | 1635 | 3/3 | 0.000 |
| city->admin1 | 0.000 | 0.155 | True | 0.048 | 3/3 | 3435 | 3/3 | 0.000 |
| admin1->country | 0.000 | 0.183 | True | 0.043 | 3/3 | 596 | 3/3 | 0.000 |
| country->admin1 | 0.784 | 0.811 | False | 0.986 | 0/3 | 82 | 0/3 | 0.510 |
| fcode->country | 0.823 | 0.859 | False | 0.965 | 0/3 | 14 | 0/3 | 0.773 |
| admin1->city | 0.738 | 0.714 | False | 0.933 | 0/3 | 185 | 0/3 | 0.123 |
| tz->country | 0.005 | 0.203 | True | 0.041 | 3/3 | 43 | 3/3 | 0.006 |
| country->tz | 0.121 | 0.120 | False | 0.201 | 0/3 | 139 | 0/3 | 0.111 |
| city->country_e2 | 0.020 | 0.167 | True | 0.050 | 3/3 | 11087 | 3/3 | 0.007 |
| city->country_e8 | 0.079 | 0.204 | False | 0.146 | 0/3 | 979 | 0/3 | 0.006 |
| city->country_src8 | 0.080 | 0.153 | False | 0.151 | 0/3 | 989 | 0/3 | 0.005 |
| city->tz_src8 | 0.080 | 0.000 | False | 0.150 | 0/3 | 810 | 1/3 | 0.006 |
| city->tz | 0.000 | 0.000 | True | 0.045 | 3/3 | 783 | 3/3 | 0.000 |

## E1 e1_geonames_16k_emb: geonames16000 (3 seeds, δ=0.05, α per FD=0.003846, rows=80000)

| method | true acc. (all) | **false acc. (all)** | true acc. natural | false acc. natural | true acc. probe | false acc. probe | oracle calls / run | note |
|---|---|---|---|---|---|---|---|---|
| B0 exact strings (g3 ≤ δ) | 3/18 | 3/21 | 3/15 | 0/12 | 0/3 | 3/9 | – |  |
| B1 proxy quotient θ=0.9 | 3/18 | 3/21 | 3/15 | 0/12 | 0/3 | 3/9 | – |  |
| B1 proxy quotient θ=0.85 | 3/18 | 3/21 | 3/15 | 0/12 | 0/3 | 3/9 | – |  |
| B1 proxy quotient θ=0.95 | 3/18 | 3/21 | 3/15 | 0/12 | 0/3 | 3/9 | – |  |
| B7 sample-only (m = our n) | 18/18 | 9/21 | 15/15 | 0/12 | 3/3 | 9/9 | 7175 | no guarantee |
| B4 canonicalize-all | 18/18 | 0/21 | 15/15 | 0/12 | 3/3 | 0/9 | 42453 | exact; shared over FDs |
| B5 pairwise blocked self-join | 3/18 | 3/21 | 3/15 | 0/12 | 0/3 | 3/9 | 1061993 | pair judgments; recall-limited |
| ours [inverse] | 18/18 | 0/21 | 15/15 | 0/12 | 3/3 | 0/9 | 12967 | primary, ν=0 (Cor A2) |
| ours [alias_only] | 18/18 | 0/21 | 15/15 | 0/12 | 3/3 | 0/9 | 9949 |  |
| ours [grid_inverse] | 18/18 | 0/21 | 15/15 | 0/12 | 3/3 | 0/9 | 42434 | θ grid, α/|grid| |
| ours [ann_nubar] | 18/18 | 0/21 | 15/15 | 0/12 | 3/3 | 0/9 | 22366 | ANN only, U+ν̄<δ |
| ours [b9_noaudit] | 18/18 | 6/21 | 15/15 | 0/12 | 3/3 | 6/9 | 1222 | B9: no audit (unsound) |

Per FD (mean over seeds): oracle g3, raw g3, ours[inverse] U and calls

| FD | g3 oracle | g3 raw | truth | ours U | ours certified | ours calls | B9 certified | B7 g3 |
|---|---|---|---|---|---|---|---|---|
| city->country | 0.000 | 0.155 | True | 0.042 | 3/3 | 1190 | 3/3 | 0.000 |
| city->admin1 | 0.000 | 0.155 | True | 0.045 | 3/3 | 1171 | 3/3 | 0.000 |
| admin1->country | 0.000 | 0.183 | True | 0.039 | 3/3 | 526 | 3/3 | 0.000 |
| country->admin1 | 0.784 | 0.811 | False | 0.996 | 0/3 | 103 | 0/3 | 0.510 |
| fcode->country | 0.823 | 0.859 | False | 0.965 | 0/3 | 15 | 0/3 | 0.773 |
| admin1->city | 0.738 | 0.714 | False | 0.939 | 0/3 | 221 | 0/3 | 0.123 |
| tz->country | 0.005 | 0.203 | True | 0.041 | 3/3 | 46 | 3/3 | 0.006 |
| country->tz | 0.121 | 0.120 | False | 0.193 | 0/3 | 147 | 0/3 | 0.104 |
| city->country_e2 | 0.020 | 0.167 | True | 0.050 | 3/3 | 3465 | 3/3 | 0.003 |
| city->country_e8 | 0.079 | 0.204 | False | 0.142 | 0/3 | 1637 | 0/3 | 0.005 |
| city->country_src8 | 0.080 | 0.153 | False | 0.126 | 0/3 | 2472 | 3/3 | 0.009 |
| city->tz_src8 | 0.080 | 0.000 | False | 0.143 | 0/3 | 1417 | 3/3 | 0.008 |
| city->tz | 0.000 | 0.000 | True | 0.041 | 3/3 | 558 | 3/3 | 0.000 |

## E1 e1_geonames_16k_k10: geonames16000 (3 seeds, δ=0.05, α per FD=0.003846, rows=80000)

| method | true acc. (all) | **false acc. (all)** | true acc. natural | false acc. natural | true acc. probe | false acc. probe | oracle calls / run | note |
|---|---|---|---|---|---|---|---|---|
| B0 exact strings (g3 ≤ δ) | 3/18 | 3/21 | 3/15 | 0/12 | 0/3 | 3/9 | – |  |
| B1 proxy quotient θ=0.9 | 3/18 | 3/21 | 3/15 | 0/12 | 0/3 | 3/9 | – |  |
| B1 proxy quotient θ=0.85 | 3/18 | 3/21 | 3/15 | 0/12 | 0/3 | 3/9 | – |  |
| B1 proxy quotient θ=0.95 | 3/18 | 3/21 | 3/15 | 0/12 | 0/3 | 3/9 | – |  |
| B7 sample-only (m = our n) | 18/18 | 9/21 | 15/15 | 0/12 | 3/3 | 9/9 | 7275 | no guarantee |
| B4 canonicalize-all | 18/18 | 0/21 | 15/15 | 0/12 | 3/3 | 0/9 | 42453 | exact; shared over FDs |
| B5 pairwise blocked self-join | 18/18 | 0/21 | 15/15 | 0/12 | 3/3 | 0/9 | 3625531 | pair judgments; recall-limited |
| ours [inverse] | 18/18 | 0/21 | 15/15 | 0/12 | 3/3 | 0/9 | 18953 | primary, ν=0 (Cor A2) |
| ours [alias_only] | 18/18 | 0/21 | 15/15 | 0/12 | 3/3 | 0/9 | 10041 |  |
| ours [grid_inverse] | 18/18 | 0/21 | 15/15 | 0/12 | 3/3 | 0/9 | 37673 | θ grid, α/|grid| |
| ours [ann_nubar] | 18/18 | 0/21 | 15/15 | 0/12 | 3/3 | 0/9 | 16929 | ANN only, U+ν̄<δ |
| ours [b9_noaudit] | 18/18 | 6/21 | 15/15 | 0/12 | 3/3 | 6/9 | 1232 | B9: no audit (unsound) |

Per FD (mean over seeds): oracle g3, raw g3, ours[inverse] U and calls

| FD | g3 oracle | g3 raw | truth | ours U | ours certified | ours calls | B9 certified | B7 g3 |
|---|---|---|---|---|---|---|---|---|
| city->country | 0.000 | 0.155 | True | 0.038 | 3/3 | 1754 | 3/3 | 0.000 |
| city->admin1 | 0.000 | 0.155 | True | 0.039 | 3/3 | 1954 | 3/3 | 0.000 |
| admin1->country | 0.000 | 0.183 | True | 0.038 | 3/3 | 791 | 3/3 | 0.000 |
| country->admin1 | 0.784 | 0.811 | False | 0.996 | 0/3 | 110 | 0/3 | 0.510 |
| fcode->country | 0.823 | 0.859 | False | 0.965 | 0/3 | 16 | 0/3 | 0.773 |
| admin1->city | 0.738 | 0.714 | False | 0.938 | 0/3 | 255 | 0/3 | 0.123 |
| tz->country | 0.005 | 0.203 | True | 0.041 | 3/3 | 47 | 3/3 | 0.006 |
| country->tz | 0.121 | 0.120 | False | 0.192 | 0/3 | 220 | 0/3 | 0.104 |
| city->country_e2 | 0.020 | 0.167 | True | 0.048 | 3/3 | 4262 | 3/3 | 0.002 |
| city->country_e8 | 0.079 | 0.204 | False | 0.129 | 0/3 | 3270 | 0/3 | 0.011 |
| city->country_src8 | 0.080 | 0.153 | False | 0.124 | 0/3 | 3443 | 3/3 | 0.008 |
| city->tz_src8 | 0.080 | 0.000 | False | 0.132 | 0/3 | 2200 | 3/3 | 0.008 |
| city->tz | 0.000 | 0.000 | True | 0.039 | 3/3 | 630 | 3/3 | 0.000 |

## E1 e1_geonames_16k_k3: geonames16000 (3 seeds, δ=0.05, α per FD=0.003846, rows=80000)

| method | true acc. (all) | **false acc. (all)** | true acc. natural | false acc. natural | true acc. probe | false acc. probe | oracle calls / run | note |
|---|---|---|---|---|---|---|---|---|
| B0 exact strings (g3 ≤ δ) | 3/18 | 3/21 | 3/15 | 0/12 | 0/3 | 3/9 | – |  |
| B1 proxy quotient θ=0.9 | 3/18 | 3/21 | 3/15 | 0/12 | 0/3 | 3/9 | – |  |
| B1 proxy quotient θ=0.85 | 3/18 | 3/21 | 3/15 | 0/12 | 0/3 | 3/9 | – |  |
| B1 proxy quotient θ=0.95 | 3/18 | 3/21 | 3/15 | 0/12 | 0/3 | 3/9 | – |  |
| B7 sample-only (m = our n) | 18/18 | 9/21 | 15/15 | 0/12 | 3/3 | 9/9 | 7275 | no guarantee |
| B4 canonicalize-all | 18/18 | 0/21 | 15/15 | 0/12 | 3/3 | 0/9 | 42453 | exact; shared over FDs |
| B5 pairwise blocked self-join | 18/18 | 0/21 | 15/15 | 0/12 | 3/3 | 0/9 | 1086807 | pair judgments; recall-limited |
| ours [inverse] | 18/18 | 0/21 | 15/15 | 0/12 | 3/3 | 0/9 | 13097 | primary, ν=0 (Cor A2) |
| ours [alias_only] | 18/18 | 0/21 | 15/15 | 0/12 | 3/3 | 0/9 | 10041 |  |
| ours [grid_inverse] | 18/18 | 0/21 | 15/15 | 0/12 | 3/3 | 0/9 | 31128 | θ grid, α/|grid| |
| ours [ann_nubar] | 18/18 | 0/21 | 15/15 | 0/12 | 3/3 | 0/9 | 10125 | ANN only, U+ν̄<δ |
| ours [b9_noaudit] | 18/18 | 6/21 | 15/15 | 0/12 | 3/3 | 6/9 | 1232 | B9: no audit (unsound) |

Per FD (mean over seeds): oracle g3, raw g3, ours[inverse] U and calls

| FD | g3 oracle | g3 raw | truth | ours U | ours certified | ours calls | B9 certified | B7 g3 |
|---|---|---|---|---|---|---|---|---|
| city->country | 0.000 | 0.155 | True | 0.038 | 3/3 | 1007 | 3/3 | 0.000 |
| city->admin1 | 0.000 | 0.155 | True | 0.039 | 3/3 | 1187 | 3/3 | 0.000 |
| admin1->country | 0.000 | 0.183 | True | 0.038 | 3/3 | 514 | 3/3 | 0.000 |
| country->admin1 | 0.784 | 0.811 | False | 0.996 | 0/3 | 105 | 0/3 | 0.510 |
| fcode->country | 0.823 | 0.859 | False | 0.965 | 0/3 | 16 | 0/3 | 0.773 |
| admin1->city | 0.738 | 0.714 | False | 0.938 | 0/3 | 218 | 0/3 | 0.123 |
| tz->country | 0.005 | 0.203 | True | 0.041 | 3/3 | 48 | 3/3 | 0.006 |
| country->tz | 0.121 | 0.120 | False | 0.192 | 0/3 | 142 | 0/3 | 0.104 |
| city->country_e2 | 0.020 | 0.167 | True | 0.048 | 3/3 | 2764 | 3/3 | 0.002 |
| city->country_e8 | 0.079 | 0.204 | False | 0.129 | 0/3 | 2174 | 0/3 | 0.011 |
| city->country_src8 | 0.080 | 0.153 | False | 0.124 | 0/3 | 2594 | 3/3 | 0.008 |
| city->tz_src8 | 0.080 | 0.000 | False | 0.132 | 0/3 | 1817 | 3/3 | 0.008 |
| city->tz | 0.000 | 0.000 | True | 0.039 | 3/3 | 510 | 3/3 | 0.000 |

## E1 e1_geonames_16k_rho0.05: geonames16000 (3 seeds, δ=0.05, α per FD=0.003846, rows=80000)

| method | true acc. (all) | **false acc. (all)** | true acc. natural | false acc. natural | true acc. probe | false acc. probe | oracle calls / run | note |
|---|---|---|---|---|---|---|---|---|
| B0 exact strings (g3 ≤ δ) | 18/24 | 0/15 | 12/15 | 0/12 | 6/9 | 0/3 | – |  |
| B1 proxy quotient θ=0.9 | 17/24 | 0/15 | 12/15 | 0/12 | 5/9 | 0/3 | – |  |
| B1 proxy quotient θ=0.85 | 17/24 | 0/15 | 14/15 | 0/12 | 3/9 | 0/3 | – |  |
| B1 proxy quotient θ=0.95 | 18/24 | 0/15 | 12/15 | 0/12 | 6/9 | 0/3 | – |  |
| B7 sample-only (m = our n) | 24/24 | 3/15 | 15/15 | 0/12 | 9/9 | 3/3 | 25236 | no guarantee |
| B4 canonicalize-all | 24/24 | 0/15 | 15/15 | 0/12 | 9/9 | 0/3 | 25665 | exact; shared over FDs |
| B5 pairwise blocked self-join | 24/24 | 0/15 | 15/15 | 0/12 | 9/9 | 0/3 | 1157846 | pair judgments; recall-limited |
| ours [inverse] | 18/24 | 0/15 | 15/15 | 0/12 | 3/9 | 0/3 | 30385 | primary, ν=0 (Cor A2) |
| ours [alias_only] | 18/24 | 0/15 | 15/15 | 0/12 | 3/9 | 0/3 | 28212 |  |
| ours [grid_inverse] | 18/24 | 0/15 | 15/15 | 0/12 | 3/9 | 0/3 | 35941 | θ grid, α/|grid| |
| ours [ann_nubar] | 18/24 | 0/15 | 15/15 | 0/12 | 3/9 | 0/3 | 17085 | ANN only, U+ν̄<δ |
| ours [b9_noaudit] | 24/24 | 0/15 | 15/15 | 0/12 | 9/9 | 0/3 | 775 | B9: no audit (unsound) |

Per FD (mean over seeds): oracle g3, raw g3, ours[inverse] U and calls

| FD | g3 oracle | g3 raw | truth | ours U | ours certified | ours calls | B9 certified | B7 g3 |
|---|---|---|---|---|---|---|---|---|
| city->country | 0.000 | 0.045 | True | 0.039 | 3/3 | 1164 | 3/3 | 0.000 |
| city->admin1 | 0.000 | 0.046 | True | 0.038 | 3/3 | 1346 | 3/3 | 0.000 |
| admin1->country | 0.000 | 0.047 | True | 0.038 | 3/3 | 524 | 3/3 | 0.000 |
| country->admin1 | 0.784 | 0.785 | False | 0.994 | 0/3 | 85 | 0/3 | 0.510 |
| fcode->country | 0.823 | 0.832 | False | 0.965 | 0/3 | 9 | 0/3 | 0.773 |
| admin1->city | 0.738 | 0.723 | False | 0.924 | 0/3 | 198 | 0/3 | 0.123 |
| tz->country | 0.005 | 0.054 | True | 0.041 | 3/3 | 21 | 3/3 | 0.006 |
| country->tz | 0.121 | 0.120 | False | 0.188 | 0/3 | 137 | 0/3 | 0.103 |
| city->country_e2 | 0.020 | 0.063 | True | 0.044 | 3/3 | 1618 | 3/3 | 0.001 |
| city->country_e8 | 0.079 | 0.116 | False | 0.114 | 0/3 | 3324 | 0/3 | 0.011 |
| city->country_src8 | 0.047 | 0.045 | True | 0.056 | 0/3 | 17162 | 3/3 | 0.033 |
| city->tz_src8 | 0.047 | 0.000 | True | 0.057 | 0/3 | 4745 | 3/3 | 0.033 |
| city->tz | 0.000 | 0.000 | True | 0.039 | 3/3 | 51 | 3/3 | 0.000 |

## E1 e1_geonames_16k_rho0.5: geonames16000 (3 seeds, δ=0.05, α per FD=0.003846, rows=80000)

| method | true acc. (all) | **false acc. (all)** | true acc. natural | false acc. natural | true acc. probe | false acc. probe | oracle calls / run | note |
|---|---|---|---|---|---|---|---|---|
| B0 exact strings (g3 ≤ δ) | 3/18 | 3/21 | 3/15 | 0/12 | 0/3 | 3/9 | – |  |
| B1 proxy quotient θ=0.9 | 3/18 | 3/21 | 3/15 | 0/12 | 0/3 | 3/9 | – |  |
| B1 proxy quotient θ=0.85 | 3/18 | 3/21 | 3/15 | 0/12 | 0/3 | 3/9 | – |  |
| B1 proxy quotient θ=0.95 | 3/18 | 3/21 | 3/15 | 0/12 | 0/3 | 3/9 | – |  |
| B7 sample-only (m = our n) | 18/18 | 9/21 | 15/15 | 0/12 | 3/3 | 9/9 | 15088 | no guarantee |
| B4 canonicalize-all | 18/18 | 0/21 | 15/15 | 0/12 | 3/3 | 0/9 | 66975 | exact; shared over FDs |
| B5 pairwise blocked self-join | 18/18 | 0/21 | 15/15 | 0/12 | 3/3 | 0/9 | 3097749 | pair judgments; recall-limited |
| ours [inverse] | 17/18 | 0/21 | 15/15 | 0/12 | 2/3 | 0/9 | 33031 | primary, ν=0 (Cor A2) |
| ours [alias_only] | 17/18 | 0/21 | 15/15 | 0/12 | 2/3 | 0/9 | 20803 |  |
| ours [grid_inverse] | 18/18 | 0/21 | 15/15 | 0/12 | 3/3 | 0/9 | 63251 | θ grid, α/|grid| |
| ours [ann_nubar] | 18/18 | 0/21 | 15/15 | 0/12 | 3/3 | 0/9 | 27524 | ANN only, U+ν̄<δ |
| ours [b9_noaudit] | 18/18 | 6/21 | 15/15 | 0/12 | 3/3 | 6/9 | 2202 | B9: no audit (unsound) |

Per FD (mean over seeds): oracle g3, raw g3, ours[inverse] U and calls

| FD | g3 oracle | g3 raw | truth | ours U | ours certified | ours calls | B9 certified | B7 g3 |
|---|---|---|---|---|---|---|---|---|
| city->country | 0.000 | 0.244 | True | 0.042 | 3/3 | 1568 | 3/3 | 0.000 |
| city->admin1 | 0.000 | 0.250 | True | 0.043 | 3/3 | 2185 | 3/3 | 0.000 |
| admin1->country | 0.000 | 0.423 | True | 0.039 | 3/3 | 677 | 3/3 | 0.000 |
| country->admin1 | 0.784 | 0.870 | False | 1.000 | 0/3 | 127 | 0/3 | 0.510 |
| fcode->country | 0.823 | 0.911 | False | 0.965 | 0/3 | 26 | 0/3 | 0.773 |
| admin1->city | 0.738 | 0.720 | False | 0.964 | 0/3 | 265 | 0/3 | 0.123 |
| tz->country | 0.005 | 0.498 | True | 0.041 | 3/3 | 79 | 3/3 | 0.006 |
| country->tz | 0.121 | 0.120 | False | 0.197 | 0/3 | 181 | 0/3 | 0.111 |
| city->country_e2 | 0.020 | 0.249 | True | 0.051 | 2/3 | 24010 | 3/3 | 0.009 |
| city->country_e8 | 0.079 | 0.263 | False | 0.223 | 0/3 | 542 | 0/3 | 0.000 |
| city->country_src8 | 0.079 | 0.238 | False | 0.141 | 0/3 | 1516 | 3/3 | 0.004 |
| city->tz_src8 | 0.079 | 0.000 | False | 0.131 | 0/3 | 1435 | 3/3 | 0.007 |
| city->tz | 0.000 | 0.000 | True | 0.045 | 3/3 | 422 | 3/3 | 0.000 |

## E1 e1_geonames_16k_tfidf: geonames16000 (3 seeds, δ=0.05, α per FD=0.003846, rows=80000)

| method | true acc. (all) | **false acc. (all)** | true acc. natural | false acc. natural | true acc. probe | false acc. probe | oracle calls / run | note |
|---|---|---|---|---|---|---|---|---|
| B0 exact strings (g3 ≤ δ) | 3/18 | 3/21 | 3/15 | 0/12 | 0/3 | 3/9 | – |  |
| B1 proxy quotient θ=0.9 | 3/18 | 3/21 | 3/15 | 0/12 | 0/3 | 3/9 | – |  |
| B1 proxy quotient θ=0.85 | 3/18 | 3/21 | 3/15 | 0/12 | 0/3 | 3/9 | – |  |
| B1 proxy quotient θ=0.95 | 3/18 | 3/21 | 3/15 | 0/12 | 0/3 | 3/9 | – |  |
| B7 sample-only (m = our n) | 18/18 | 9/21 | 15/15 | 0/12 | 3/3 | 9/9 | 7482 | no guarantee |
| B4 canonicalize-all | 18/18 | 0/21 | 15/15 | 0/12 | 3/3 | 0/9 | 42453 | exact; shared over FDs |
| B5 pairwise blocked self-join | 18/18 | 0/21 | 15/15 | 0/12 | 3/3 | 0/9 | 1059964 | pair judgments; recall-limited |
| ours [inverse] | 18/18 | 0/21 | 15/15 | 0/12 | 3/3 | 0/9 | 13188 | primary, ν=0 (Cor A2) |
| ours [alias_only] | 18/18 | 0/21 | 15/15 | 0/12 | 3/3 | 0/9 | 10333 |  |
| ours [grid_inverse] | 18/18 | 0/21 | 15/15 | 0/12 | 3/3 | 0/9 | 26679 | θ grid, α/|grid| |
| ours [ann_nubar] | 18/18 | 0/21 | 15/15 | 0/12 | 3/3 | 0/9 | 10941 | ANN only, U+ν̄<δ |
| ours [b9_noaudit] | 18/18 | 6/21 | 15/15 | 0/12 | 3/3 | 6/9 | 1286 | B9: no audit (unsound) |

Per FD (mean over seeds): oracle g3, raw g3, ours[inverse] U and calls

| FD | g3 oracle | g3 raw | truth | ours U | ours certified | ours calls | B9 certified | B7 g3 |
|---|---|---|---|---|---|---|---|---|
| city->country | 0.000 | 0.155 | True | 0.038 | 3/3 | 986 | 3/3 | 0.000 |
| city->admin1 | 0.000 | 0.155 | True | 0.038 | 3/3 | 1167 | 3/3 | 0.000 |
| admin1->country | 0.000 | 0.183 | True | 0.038 | 3/3 | 506 | 3/3 | 0.000 |
| country->admin1 | 0.784 | 0.811 | False | 0.996 | 0/3 | 107 | 0/3 | 0.510 |
| fcode->country | 0.823 | 0.859 | False | 0.965 | 0/3 | 16 | 0/3 | 0.773 |
| admin1->city | 0.738 | 0.714 | False | 0.936 | 0/3 | 219 | 0/3 | 0.123 |
| tz->country | 0.005 | 0.203 | True | 0.041 | 3/3 | 48 | 3/3 | 0.006 |
| country->tz | 0.121 | 0.120 | False | 0.193 | 0/3 | 137 | 0/3 | 0.104 |
| city->country_e2 | 0.020 | 0.167 | True | 0.049 | 3/3 | 2578 | 3/3 | 0.002 |
| city->country_e8 | 0.079 | 0.204 | False | 0.130 | 0/3 | 2052 | 0/3 | 0.009 |
| city->country_src8 | 0.080 | 0.153 | False | 0.118 | 0/3 | 2870 | 3/3 | 0.009 |
| city->tz_src8 | 0.080 | 0.000 | False | 0.128 | 0/3 | 2015 | 3/3 | 0.009 |
| city->tz | 0.000 | 0.000 | True | 0.039 | 3/3 | 488 | 3/3 | 0.000 |

## E1 e1_geonames_16k_th0.8: geonames16000 (3 seeds, δ=0.05, α per FD=0.003846, rows=80000)

| method | true acc. (all) | **false acc. (all)** | true acc. natural | false acc. natural | true acc. probe | false acc. probe | oracle calls / run | note |
|---|---|---|---|---|---|---|---|---|
| B0 exact strings (g3 ≤ δ) | 3/18 | 3/21 | 3/15 | 0/12 | 0/3 | 3/9 | – |  |
| B1 proxy quotient θ=0.8 | 0/18 | 0/21 | 0/15 | 0/12 | 0/3 | 0/9 | – |  |
| B1 proxy quotient θ=0.85 | 3/18 | 3/21 | 3/15 | 0/12 | 0/3 | 3/9 | – |  |
| B1 proxy quotient θ=0.9 | 3/18 | 3/21 | 3/15 | 0/12 | 0/3 | 3/9 | – |  |
| B1 proxy quotient θ=0.95 | 3/18 | 3/21 | 3/15 | 0/12 | 0/3 | 3/9 | – |  |
| B7 sample-only (m = our n) | 18/18 | 9/21 | 15/15 | 0/12 | 3/3 | 9/9 | 10063 | no guarantee |
| B4 canonicalize-all | 18/18 | 0/21 | 15/15 | 0/12 | 3/3 | 0/9 | 42453 | exact; shared over FDs |
| B5 pairwise blocked self-join | 18/18 | 0/21 | 15/15 | 0/12 | 3/3 | 0/9 | 1812068 | pair judgments; recall-limited |
| ours [inverse] | 3/18 | 0/21 | 3/15 | 0/12 | 0/3 | 0/9 | 19289 | primary, ν=0 (Cor A2) |
| ours [alias_only] | 3/18 | 0/21 | 3/15 | 0/12 | 0/3 | 0/9 | 12340 |  |
| ours [grid_inverse] | 18/18 | 0/21 | 15/15 | 0/12 | 3/3 | 0/9 | 33786 | θ grid, α/|grid| |
| ours [ann_nubar] | 3/18 | 0/21 | 3/15 | 0/12 | 0/3 | 0/9 | 15297 | ANN only, U+ν̄<δ |
| ours [b9_noaudit] | 6/18 | 0/21 | 6/15 | 0/12 | 0/3 | 0/9 | 2085 | B9: no audit (unsound) |

Per FD (mean over seeds): oracle g3, raw g3, ours[inverse] U and calls

| FD | g3 oracle | g3 raw | truth | ours U | ours certified | ours calls | B9 certified | B7 g3 |
|---|---|---|---|---|---|---|---|---|
| city->country | 0.000 | 0.155 | True | 0.168 | 0/3 | 2243 | 0/3 | 0.000 |
| city->admin1 | 0.000 | 0.155 | True | 0.240 | 0/3 | 1493 | 0/3 | 0.000 |
| admin1->country | 0.000 | 0.183 | True | 0.060 | 0/3 | 9218 | 3/3 | 0.000 |
| country->admin1 | 0.784 | 0.811 | False | 0.983 | 0/3 | 27 | 0/3 | 0.510 |
| fcode->country | 0.823 | 0.859 | False | 0.978 | 0/3 | 1 | 0/3 | 0.773 |
| admin1->city | 0.738 | 0.714 | False | 0.959 | 0/3 | 152 | 0/3 | 0.123 |
| tz->country | 0.005 | 0.203 | True | 0.041 | 3/3 | 5 | 3/3 | 0.006 |
| country->tz | 0.121 | 0.120 | False | 0.221 | 0/3 | 91 | 0/3 | 0.112 |
| city->country_e2 | 0.020 | 0.167 | True | 0.170 | 0/3 | 1833 | 0/3 | 0.002 |
| city->country_e8 | 0.079 | 0.204 | False | 0.262 | 0/3 | 633 | 0/3 | 0.001 |
| city->country_src8 | 0.080 | 0.153 | False | 0.255 | 0/3 | 764 | 0/3 | 0.000 |
| city->tz_src8 | 0.080 | 0.000 | False | 0.249 | 0/3 | 760 | 0/3 | 0.001 |
| city->tz | 0.000 | 0.000 | True | 0.146 | 0/3 | 2070 | 0/3 | 0.000 |

## E1 e1_geonames_16k_th0.95: geonames16000 (3 seeds, δ=0.05, α per FD=0.003846, rows=80000)

| method | true acc. (all) | **false acc. (all)** | true acc. natural | false acc. natural | true acc. probe | false acc. probe | oracle calls / run | note |
|---|---|---|---|---|---|---|---|---|
| B0 exact strings (g3 ≤ δ) | 3/18 | 3/21 | 3/15 | 0/12 | 0/3 | 3/9 | – |  |
| B1 proxy quotient θ=0.95 | 3/18 | 3/21 | 3/15 | 0/12 | 0/3 | 3/9 | – |  |
| B1 proxy quotient θ=0.85 | 3/18 | 3/21 | 3/15 | 0/12 | 0/3 | 3/9 | – |  |
| B1 proxy quotient θ=0.9 | 3/18 | 3/21 | 3/15 | 0/12 | 0/3 | 3/9 | – |  |
| B7 sample-only (m = our n) | 18/18 | 9/21 | 15/15 | 0/12 | 3/3 | 9/9 | 9669 | no guarantee |
| B4 canonicalize-all | 18/18 | 0/21 | 15/15 | 0/12 | 3/3 | 0/9 | 42453 | exact; shared over FDs |
| B5 pairwise blocked self-join | 18/18 | 0/21 | 15/15 | 0/12 | 3/3 | 0/9 | 1812068 | pair judgments; recall-limited |
| ours [inverse] | 18/18 | 0/21 | 15/15 | 0/12 | 3/3 | 0/9 | 18795 | primary, ν=0 (Cor A2) |
| ours [alias_only] | 18/18 | 0/21 | 15/15 | 0/12 | 3/3 | 0/9 | 13242 |  |
| ours [grid_inverse] | 18/18 | 0/21 | 15/15 | 0/12 | 3/3 | 0/9 | 33786 | θ grid, α/|grid| |
| ours [ann_nubar] | 18/18 | 0/21 | 15/15 | 0/12 | 3/3 | 0/9 | 14433 | ANN only, U+ν̄<δ |
| ours [b9_noaudit] | 18/18 | 6/21 | 15/15 | 0/12 | 3/3 | 6/9 | 1475 | B9: no audit (unsound) |

Per FD (mean over seeds): oracle g3, raw g3, ours[inverse] U and calls

| FD | g3 oracle | g3 raw | truth | ours U | ours certified | ours calls | B9 certified | B7 g3 |
|---|---|---|---|---|---|---|---|---|
| city->country | 0.000 | 0.155 | True | 0.038 | 3/3 | 1224 | 3/3 | 0.000 |
| city->admin1 | 0.000 | 0.155 | True | 0.038 | 3/3 | 1413 | 3/3 | 0.000 |
| admin1->country | 0.000 | 0.183 | True | 0.038 | 3/3 | 613 | 3/3 | 0.000 |
| country->admin1 | 0.784 | 0.811 | False | 0.991 | 0/3 | 100 | 0/3 | 0.510 |
| fcode->country | 0.823 | 0.859 | False | 0.972 | 0/3 | 15 | 0/3 | 0.773 |
| admin1->city | 0.738 | 0.714 | False | 0.997 | 0/3 | 212 | 0/3 | 0.123 |
| tz->country | 0.005 | 0.203 | True | 0.045 | 3/3 | 52 | 3/3 | 0.006 |
| country->tz | 0.121 | 0.120 | False | 0.177 | 0/3 | 180 | 0/3 | 0.115 |
| city->country_e2 | 0.020 | 0.167 | True | 0.048 | 3/3 | 2765 | 3/3 | 0.002 |
| city->country_e8 | 0.079 | 0.204 | False | 0.112 | 0/3 | 3564 | 0/3 | 0.012 |
| city->country_src8 | 0.080 | 0.153 | False | 0.109 | 0/3 | 3795 | 3/3 | 0.011 |
| city->tz_src8 | 0.080 | 0.000 | False | 0.096 | 0/3 | 4448 | 3/3 | 0.017 |
| city->tz | 0.000 | 0.000 | True | 0.038 | 3/3 | 414 | 3/3 | 0.000 |

## E1 e1_ndc: ndc116620 (3 seeds, δ=0.05, α per FD=0.005556, rows=116620)

| method | true acc. (all) | **false acc. (all)** | true acc. natural | false acc. natural | true acc. probe | false acc. probe | oracle calls / run | note |
|---|---|---|---|---|---|---|---|---|
| B0 exact strings (g3 ≤ δ) | 3/9 | 0/18 | 3/6 | 0/15 | 0/3 | 0/3 | – |  |
| B1 proxy quotient θ=0.9 | 6/9 | 0/18 | 6/6 | 0/15 | 0/3 | 0/3 | – |  |
| B1 proxy quotient θ=0.85 | 9/9 | 0/18 | 6/6 | 0/15 | 3/3 | 0/3 | – |  |
| B1 proxy quotient θ=0.95 | 3/9 | 0/18 | 3/6 | 0/15 | 0/3 | 0/3 | – |  |
| B7 sample-only (m = our n) | 9/9 | 5/18 | 6/6 | 4/15 | 3/3 | 1/3 | 2723 | no guarantee |
| B4 canonicalize-all | 9/9 | 0/18 | 6/6 | 0/15 | 3/3 | 0/3 | 6653 | exact; shared over FDs |
| B5 pairwise blocked self-join | 9/9 | 0/18 | 6/6 | 0/15 | 3/3 | 0/3 | 390239 | pair judgments; recall-limited |
| ours [inverse] | 9/9 | 0/18 | 6/6 | 0/15 | 3/3 | 0/3 | 2659 | primary, ν=0 (Cor A2) |
| ours [grid_inverse] | 9/9 | 0/18 | 6/6 | 0/15 | 3/3 | 0/3 | 4057 | θ grid, α/|grid| |
| ours [ann_nubar] | 9/9 | 0/18 | 6/6 | 0/15 | 3/3 | 0/3 | 1889 | ANN only, U+ν̄<δ |
| ours [b9_noaudit] | 9/9 | 0/18 | 6/6 | 0/15 | 3/3 | 0/3 | 994 | B9: no audit (unsound) |

Per FD (mean over seeds): oracle g3, raw g3, ours[inverse] U and calls

| FD | g3 oracle | g3 raw | truth | ours U | ours certified | ours calls | B9 certified | B7 g3 |
|---|---|---|---|---|---|---|---|---|
| labcode->labeler | 0.000 | 0.107 | True | 0.035 | 3/3 | 220 | 3/3 | 0.000 |
| labeler->ptype | 0.026 | 0.025 | True | 0.049 | 3/3 | 1452 | 3/3 | 0.019 |
| labeler->labcode | 0.128 | 0.108 | False | 0.225 | 0/3 | 262 | 0/3 | 0.092 |
| labeler->mktcat | 0.100 | 0.095 | False | 0.152 | 0/3 | 320 | 0/3 | 0.051 |
| appno->labeler | 0.653 | 0.660 | False | 0.876 | 0/3 | 22 | 0/3 | 0.243 |
| brand->labeler | 0.458 | 0.468 | False | 0.641 | 0/3 | 23 | 0/3 | 0.033 |
| generic->labeler | 0.659 | 0.665 | False | 0.847 | 0/3 | 25 | 0/3 | 0.057 |
| labcode->labeler_e2 | 0.020 | 0.125 | True | 0.045 | 3/3 | 84 | 3/3 | 0.011 |
| labcode->labeler_e8 | 0.080 | 0.178 | False | 0.109 | 0/3 | 252 | 0/3 | 0.054 |

## E1 e1_ndc_edit: ndc116620 (3 seeds, δ=0.05, α per FD=0.005556, rows=116620)

| method | true acc. (all) | **false acc. (all)** | true acc. natural | false acc. natural | true acc. probe | false acc. probe | oracle calls / run | note |
|---|---|---|---|---|---|---|---|---|
| B0 exact strings (g3 ≤ δ) | 3/9 | 0/18 | 3/6 | 0/15 | 0/3 | 0/3 | – |  |
| B1 proxy quotient θ=0.9 | 6/9 | 0/18 | 6/6 | 0/15 | 0/3 | 0/3 | – |  |
| B1 proxy quotient θ=0.85 | 6/9 | 0/18 | 6/6 | 0/15 | 0/3 | 0/3 | – |  |
| B1 proxy quotient θ=0.95 | 3/9 | 0/18 | 3/6 | 0/15 | 0/3 | 0/3 | – |  |
| B7 sample-only (m = our n) | 9/9 | 5/18 | 6/6 | 4/15 | 3/3 | 1/3 | 2748 | no guarantee |
| B4 canonicalize-all | 9/9 | 0/18 | 6/6 | 0/15 | 3/3 | 0/3 | 6653 | exact; shared over FDs |
| B5 pairwise blocked self-join | 9/9 | 0/18 | 6/6 | 0/15 | 3/3 | 0/3 | 229716 | pair judgments; recall-limited |
| ours [inverse] | 9/9 | 0/18 | 6/6 | 0/15 | 3/3 | 0/3 | 2627 | primary, ν=0 (Cor A2) |
| ours [grid_inverse] | 9/9 | 0/18 | 6/6 | 0/15 | 3/3 | 0/3 | 5997 | θ grid, α/|grid| |
| ours [ann_nubar] | 9/9 | 0/18 | 6/6 | 0/15 | 3/3 | 0/3 | 1642 | ANN only, U+ν̄<δ |
| ours [b9_noaudit] | 9/9 | 0/18 | 6/6 | 0/15 | 3/3 | 0/3 | 994 | B9: no audit (unsound) |

Per FD (mean over seeds): oracle g3, raw g3, ours[inverse] U and calls

| FD | g3 oracle | g3 raw | truth | ours U | ours certified | ours calls | B9 certified | B7 g3 |
|---|---|---|---|---|---|---|---|---|
| labcode->labeler | 0.000 | 0.107 | True | 0.035 | 3/3 | 220 | 3/3 | 0.000 |
| labeler->ptype | 0.026 | 0.025 | True | 0.049 | 3/3 | 1590 | 3/3 | 0.020 |
| labeler->labcode | 0.128 | 0.108 | False | 0.287 | 0/3 | 143 | 0/3 | 0.087 |
| labeler->mktcat | 0.100 | 0.095 | False | 0.157 | 0/3 | 249 | 0/3 | 0.055 |
| appno->labeler | 0.653 | 0.660 | False | 0.876 | 0/3 | 24 | 0/3 | 0.243 |
| brand->labeler | 0.458 | 0.468 | False | 0.641 | 0/3 | 24 | 0/3 | 0.033 |
| generic->labeler | 0.659 | 0.665 | False | 0.847 | 0/3 | 28 | 0/3 | 0.057 |
| labcode->labeler_e2 | 0.020 | 0.125 | True | 0.045 | 3/3 | 89 | 3/3 | 0.011 |
| labcode->labeler_e8 | 0.080 | 0.178 | False | 0.109 | 0/3 | 261 | 0/3 | 0.054 |

## E1 e1_ndc_emb: ndc116620 (3 seeds, δ=0.05, α per FD=0.005556, rows=116620)

| method | true acc. (all) | **false acc. (all)** | true acc. natural | false acc. natural | true acc. probe | false acc. probe | oracle calls / run | note |
|---|---|---|---|---|---|---|---|---|
| B0 exact strings (g3 ≤ δ) | 3/9 | 0/18 | 3/6 | 0/15 | 0/3 | 0/3 | – |  |
| B1 proxy quotient θ=0.9 | 9/9 | 0/18 | 6/6 | 0/15 | 3/3 | 0/3 | – |  |
| B1 proxy quotient θ=0.85 | 9/9 | 0/18 | 6/6 | 0/15 | 3/3 | 0/3 | – |  |
| B1 proxy quotient θ=0.95 | 6/9 | 0/18 | 6/6 | 0/15 | 0/3 | 0/3 | – |  |
| B7 sample-only (m = our n) | 9/9 | 4/18 | 6/6 | 3/15 | 3/3 | 1/3 | 2744 | no guarantee |
| B4 canonicalize-all | 9/9 | 0/18 | 6/6 | 0/15 | 3/3 | 0/3 | 6653 | exact; shared over FDs |
| B5 pairwise blocked self-join | 9/9 | 0/18 | 6/6 | 0/15 | 3/3 | 0/3 | 224731 | pair judgments; recall-limited |
| ours [inverse] | 9/9 | 0/18 | 6/6 | 0/15 | 3/3 | 0/3 | 2562 | primary, ν=0 (Cor A2) |
| ours [grid_inverse] | 9/9 | 0/18 | 6/6 | 0/15 | 3/3 | 0/3 | 4490 | θ grid, α/|grid| |
| ours [ann_nubar] | 9/9 | 0/18 | 6/6 | 0/15 | 3/3 | 0/3 | 1569 | ANN only, U+ν̄<δ |
| ours [b9_noaudit] | 9/9 | 0/18 | 6/6 | 0/15 | 3/3 | 0/3 | 994 | B9: no audit (unsound) |

Per FD (mean over seeds): oracle g3, raw g3, ours[inverse] U and calls

| FD | g3 oracle | g3 raw | truth | ours U | ours certified | ours calls | B9 certified | B7 g3 |
|---|---|---|---|---|---|---|---|---|
| labcode->labeler | 0.000 | 0.107 | True | 0.035 | 3/3 | 220 | 3/3 | 0.000 |
| labeler->ptype | 0.026 | 0.025 | True | 0.049 | 3/3 | 1437 | 3/3 | 0.019 |
| labeler->labcode | 0.128 | 0.108 | False | 0.231 | 0/3 | 179 | 0/3 | 0.083 |
| labeler->mktcat | 0.100 | 0.095 | False | 0.152 | 0/3 | 293 | 0/3 | 0.062 |
| appno->labeler | 0.653 | 0.660 | False | 0.876 | 0/3 | 25 | 0/3 | 0.243 |
| brand->labeler | 0.458 | 0.468 | False | 0.641 | 0/3 | 24 | 0/3 | 0.033 |
| generic->labeler | 0.659 | 0.665 | False | 0.847 | 0/3 | 28 | 0/3 | 0.057 |
| labcode->labeler_e2 | 0.020 | 0.125 | True | 0.045 | 3/3 | 91 | 3/3 | 0.011 |
| labcode->labeler_e8 | 0.080 | 0.178 | False | 0.109 | 0/3 | 265 | 0/3 | 0.054 |

## E1 e1_ndc_k10: ndc116620 (3 seeds, δ=0.05, α per FD=0.005556, rows=116620)

| method | true acc. (all) | **false acc. (all)** | true acc. natural | false acc. natural | true acc. probe | false acc. probe | oracle calls / run | note |
|---|---|---|---|---|---|---|---|---|
| B0 exact strings (g3 ≤ δ) | 3/9 | 0/18 | 3/6 | 0/15 | 0/3 | 0/3 | – |  |
| B1 proxy quotient θ=0.9 | 6/9 | 0/18 | 6/6 | 0/15 | 0/3 | 0/3 | – |  |
| B1 proxy quotient θ=0.85 | 9/9 | 0/18 | 6/6 | 0/15 | 3/3 | 0/3 | – |  |
| B1 proxy quotient θ=0.95 | 3/9 | 0/18 | 3/6 | 0/15 | 0/3 | 0/3 | – |  |
| B7 sample-only (m = our n) | 9/9 | 5/18 | 6/6 | 4/15 | 3/3 | 1/3 | 2723 | no guarantee |
| B4 canonicalize-all | 9/9 | 0/18 | 6/6 | 0/15 | 3/3 | 0/3 | 6653 | exact; shared over FDs |
| B5 pairwise blocked self-join | 9/9 | 0/18 | 6/6 | 0/15 | 3/3 | 0/3 | 785961 | pair judgments; recall-limited |
| ours [inverse] | 9/9 | 0/18 | 6/6 | 0/15 | 3/3 | 0/3 | 2937 | primary, ν=0 (Cor A2) |
| ours [grid_inverse] | 9/9 | 0/18 | 6/6 | 0/15 | 3/3 | 0/3 | 4437 | θ grid, α/|grid| |
| ours [ann_nubar] | 8/9 | 0/18 | 5/6 | 0/15 | 3/3 | 0/3 | 2899 | ANN only, U+ν̄<δ |
| ours [b9_noaudit] | 9/9 | 0/18 | 6/6 | 0/15 | 3/3 | 0/3 | 994 | B9: no audit (unsound) |

Per FD (mean over seeds): oracle g3, raw g3, ours[inverse] U and calls

| FD | g3 oracle | g3 raw | truth | ours U | ours certified | ours calls | B9 certified | B7 g3 |
|---|---|---|---|---|---|---|---|---|
| labcode->labeler | 0.000 | 0.107 | True | 0.035 | 3/3 | 220 | 3/3 | 0.000 |
| labeler->ptype | 0.026 | 0.025 | True | 0.049 | 3/3 | 1628 | 3/3 | 0.019 |
| labeler->labcode | 0.128 | 0.108 | False | 0.225 | 0/3 | 376 | 0/3 | 0.092 |
| labeler->mktcat | 0.100 | 0.095 | False | 0.152 | 0/3 | 356 | 0/3 | 0.051 |
| appno->labeler | 0.653 | 0.660 | False | 0.876 | 0/3 | 20 | 0/3 | 0.243 |
| brand->labeler | 0.458 | 0.468 | False | 0.641 | 0/3 | 19 | 0/3 | 0.033 |
| generic->labeler | 0.659 | 0.665 | False | 0.847 | 0/3 | 22 | 0/3 | 0.057 |
| labcode->labeler_e2 | 0.020 | 0.125 | True | 0.045 | 3/3 | 74 | 3/3 | 0.011 |
| labcode->labeler_e8 | 0.080 | 0.178 | False | 0.109 | 0/3 | 222 | 0/3 | 0.054 |

## E1 e1_ndc_k3: ndc116620 (3 seeds, δ=0.05, α per FD=0.005556, rows=116620)

| method | true acc. (all) | **false acc. (all)** | true acc. natural | false acc. natural | true acc. probe | false acc. probe | oracle calls / run | note |
|---|---|---|---|---|---|---|---|---|
| B0 exact strings (g3 ≤ δ) | 3/9 | 0/18 | 3/6 | 0/15 | 0/3 | 0/3 | – |  |
| B1 proxy quotient θ=0.9 | 6/9 | 0/18 | 6/6 | 0/15 | 0/3 | 0/3 | – |  |
| B1 proxy quotient θ=0.85 | 9/9 | 0/18 | 6/6 | 0/15 | 3/3 | 0/3 | – |  |
| B1 proxy quotient θ=0.95 | 3/9 | 0/18 | 3/6 | 0/15 | 0/3 | 0/3 | – |  |
| B7 sample-only (m = our n) | 9/9 | 5/18 | 6/6 | 4/15 | 3/3 | 1/3 | 2723 | no guarantee |
| B4 canonicalize-all | 9/9 | 0/18 | 6/6 | 0/15 | 3/3 | 0/3 | 6653 | exact; shared over FDs |
| B5 pairwise blocked self-join | 9/9 | 0/18 | 6/6 | 0/15 | 3/3 | 0/3 | 232162 | pair judgments; recall-limited |
| ours [inverse] | 9/9 | 0/18 | 6/6 | 0/15 | 3/3 | 0/3 | 2530 | primary, ν=0 (Cor A2) |
| ours [grid_inverse] | 9/9 | 0/18 | 6/6 | 0/15 | 3/3 | 0/3 | 3880 | θ grid, α/|grid| |
| ours [ann_nubar] | 9/9 | 0/18 | 6/6 | 0/15 | 3/3 | 0/3 | 1461 | ANN only, U+ν̄<δ |
| ours [b9_noaudit] | 9/9 | 0/18 | 6/6 | 0/15 | 3/3 | 0/3 | 994 | B9: no audit (unsound) |

Per FD (mean over seeds): oracle g3, raw g3, ours[inverse] U and calls

| FD | g3 oracle | g3 raw | truth | ours U | ours certified | ours calls | B9 certified | B7 g3 |
|---|---|---|---|---|---|---|---|---|
| labcode->labeler | 0.000 | 0.107 | True | 0.035 | 3/3 | 220 | 3/3 | 0.000 |
| labeler->ptype | 0.026 | 0.025 | True | 0.049 | 3/3 | 1378 | 3/3 | 0.019 |
| labeler->labcode | 0.128 | 0.108 | False | 0.225 | 0/3 | 214 | 0/3 | 0.092 |
| labeler->mktcat | 0.100 | 0.095 | False | 0.152 | 0/3 | 288 | 0/3 | 0.051 |
| appno->labeler | 0.653 | 0.660 | False | 0.876 | 0/3 | 24 | 0/3 | 0.243 |
| brand->labeler | 0.458 | 0.468 | False | 0.641 | 0/3 | 25 | 0/3 | 0.033 |
| generic->labeler | 0.659 | 0.665 | False | 0.847 | 0/3 | 27 | 0/3 | 0.057 |
| labcode->labeler_e2 | 0.020 | 0.125 | True | 0.045 | 3/3 | 89 | 3/3 | 0.011 |
| labcode->labeler_e8 | 0.080 | 0.178 | False | 0.109 | 0/3 | 267 | 0/3 | 0.054 |

## E1 e1_ndc_tfidf: ndc116620 (3 seeds, δ=0.05, α per FD=0.005556, rows=116620)

| method | true acc. (all) | **false acc. (all)** | true acc. natural | false acc. natural | true acc. probe | false acc. probe | oracle calls / run | note |
|---|---|---|---|---|---|---|---|---|
| B0 exact strings (g3 ≤ δ) | 3/9 | 0/18 | 3/6 | 0/15 | 0/3 | 0/3 | – |  |
| B1 proxy quotient θ=0.9 | 3/9 | 0/18 | 3/6 | 0/15 | 0/3 | 0/3 | – |  |
| B1 proxy quotient θ=0.85 | 3/9 | 0/18 | 3/6 | 0/15 | 0/3 | 0/3 | – |  |
| B1 proxy quotient θ=0.95 | 3/9 | 0/18 | 3/6 | 0/15 | 0/3 | 0/3 | – |  |
| B7 sample-only (m = our n) | 9/9 | 4/18 | 6/6 | 3/15 | 3/3 | 1/3 | 2494 | no guarantee |
| B4 canonicalize-all | 9/9 | 0/18 | 6/6 | 0/15 | 3/3 | 0/3 | 6653 | exact; shared over FDs |
| B5 pairwise blocked self-join | 9/9 | 0/18 | 6/6 | 0/15 | 3/3 | 0/3 | 229716 | pair judgments; recall-limited |
| ours [inverse] | 9/9 | 0/18 | 6/6 | 0/15 | 3/3 | 0/3 | 2183 | primary, ν=0 (Cor A2) |
| ours [grid_inverse] | 9/9 | 0/18 | 6/6 | 0/15 | 3/3 | 0/3 | 3783 | θ grid, α/|grid| |
| ours [ann_nubar] | 9/9 | 0/18 | 6/6 | 0/15 | 3/3 | 0/3 | 1354 | ANN only, U+ν̄<δ |
| ours [b9_noaudit] | 9/9 | 0/18 | 6/6 | 0/15 | 3/3 | 0/3 | 994 | B9: no audit (unsound) |

Per FD (mean over seeds): oracle g3, raw g3, ours[inverse] U and calls

| FD | g3 oracle | g3 raw | truth | ours U | ours certified | ours calls | B9 certified | B7 g3 |
|---|---|---|---|---|---|---|---|---|
| labcode->labeler | 0.000 | 0.107 | True | 0.035 | 3/3 | 220 | 3/3 | 0.000 |
| labeler->ptype | 0.026 | 0.025 | True | 0.049 | 3/3 | 795 | 3/3 | 0.016 |
| labeler->labcode | 0.128 | 0.108 | False | 0.202 | 0/3 | 311 | 0/3 | 0.086 |
| labeler->mktcat | 0.100 | 0.095 | False | 0.144 | 0/3 | 380 | 0/3 | 0.063 |
| appno->labeler | 0.653 | 0.660 | False | 0.876 | 0/3 | 27 | 0/3 | 0.243 |
| brand->labeler | 0.458 | 0.468 | False | 0.641 | 0/3 | 25 | 0/3 | 0.033 |
| generic->labeler | 0.659 | 0.665 | False | 0.847 | 0/3 | 31 | 0/3 | 0.057 |
| labcode->labeler_e2 | 0.020 | 0.125 | True | 0.045 | 3/3 | 98 | 3/3 | 0.011 |
| labcode->labeler_e8 | 0.080 | 0.178 | False | 0.109 | 0/3 | 296 | 0/3 | 0.054 |

## E1 e1_ndc_th0.8: ndc116620 (3 seeds, δ=0.05, α per FD=0.005556, rows=116620)

| method | true acc. (all) | **false acc. (all)** | true acc. natural | false acc. natural | true acc. probe | false acc. probe | oracle calls / run | note |
|---|---|---|---|---|---|---|---|---|
| B0 exact strings (g3 ≤ δ) | 3/9 | 0/18 | 3/6 | 0/15 | 0/3 | 0/3 | – |  |
| B1 proxy quotient θ=0.8 | 6/9 | 0/18 | 3/6 | 0/15 | 3/3 | 0/3 | – |  |
| B1 proxy quotient θ=0.85 | 9/9 | 0/18 | 6/6 | 0/15 | 3/3 | 0/3 | – |  |
| B1 proxy quotient θ=0.9 | 6/9 | 0/18 | 6/6 | 0/15 | 0/3 | 0/3 | – |  |
| B1 proxy quotient θ=0.95 | 3/9 | 0/18 | 3/6 | 0/15 | 0/3 | 0/3 | – |  |
| B7 sample-only (m = our n) | 9/9 | 4/18 | 6/6 | 4/15 | 3/3 | 0/3 | 3453 | no guarantee |
| B4 canonicalize-all | 9/9 | 0/18 | 6/6 | 0/15 | 3/3 | 0/3 | 6653 | exact; shared over FDs |
| B5 pairwise blocked self-join | 9/9 | 0/18 | 6/6 | 0/15 | 3/3 | 0/3 | 390239 | pair judgments; recall-limited |
| ours [inverse] | 6/9 | 0/18 | 3/6 | 0/15 | 3/3 | 0/3 | 4113 | primary, ν=0 (Cor A2) |
| ours [grid_inverse] | 9/9 | 0/18 | 6/6 | 0/15 | 3/3 | 0/3 | 4057 | θ grid, α/|grid| |
| ours [ann_nubar] | 6/9 | 0/18 | 3/6 | 0/15 | 3/3 | 0/3 | 1408 | ANN only, U+ν̄<δ |
| ours [b9_noaudit] | 6/9 | 0/18 | 3/6 | 0/15 | 3/3 | 0/3 | 1016 | B9: no audit (unsound) |

Per FD (mean over seeds): oracle g3, raw g3, ours[inverse] U and calls

| FD | g3 oracle | g3 raw | truth | ours U | ours certified | ours calls | B9 certified | B7 g3 |
|---|---|---|---|---|---|---|---|---|
| labcode->labeler | 0.000 | 0.107 | True | 0.035 | 3/3 | 224 | 3/3 | 0.000 |
| labeler->ptype | 0.026 | 0.025 | True | 0.086 | 0/3 | 3473 | 0/3 | 0.020 |
| labeler->labcode | 0.128 | 0.108 | False | 0.488 | 0/3 | 60 | 0/3 | 0.070 |
| labeler->mktcat | 0.100 | 0.095 | False | 0.230 | 0/3 | 82 | 0/3 | 0.041 |
| appno->labeler | 0.653 | 0.660 | False | 0.834 | 0/3 | 14 | 0/3 | 0.243 |
| brand->labeler | 0.458 | 0.468 | False | 0.671 | 0/3 | 13 | 0/3 | 0.033 |
| generic->labeler | 0.659 | 0.665 | False | 0.852 | 0/3 | 18 | 0/3 | 0.057 |
| labcode->labeler_e2 | 0.020 | 0.125 | True | 0.046 | 3/3 | 39 | 3/3 | 0.010 |
| labcode->labeler_e8 | 0.080 | 0.178 | False | 0.109 | 0/3 | 189 | 0/3 | 0.062 |

## E1 e1_ndc_th0.95: ndc116620 (3 seeds, δ=0.05, α per FD=0.005556, rows=116620)

| method | true acc. (all) | **false acc. (all)** | true acc. natural | false acc. natural | true acc. probe | false acc. probe | oracle calls / run | note |
|---|---|---|---|---|---|---|---|---|
| B0 exact strings (g3 ≤ δ) | 3/9 | 0/18 | 3/6 | 0/15 | 0/3 | 0/3 | – |  |
| B1 proxy quotient θ=0.95 | 3/9 | 0/18 | 3/6 | 0/15 | 0/3 | 0/3 | – |  |
| B1 proxy quotient θ=0.85 | 9/9 | 0/18 | 6/6 | 0/15 | 3/3 | 0/3 | – |  |
| B1 proxy quotient θ=0.9 | 6/9 | 0/18 | 6/6 | 0/15 | 0/3 | 0/3 | – |  |
| B7 sample-only (m = our n) | 9/9 | 3/18 | 6/6 | 3/15 | 3/3 | 0/3 | 2852 | no guarantee |
| B4 canonicalize-all | 9/9 | 0/18 | 6/6 | 0/15 | 3/3 | 0/3 | 6653 | exact; shared over FDs |
| B5 pairwise blocked self-join | 9/9 | 0/18 | 6/6 | 0/15 | 3/3 | 0/3 | 390239 | pair judgments; recall-limited |
| ours [inverse] | 9/9 | 0/18 | 6/6 | 0/15 | 3/3 | 0/3 | 2493 | primary, ν=0 (Cor A2) |
| ours [grid_inverse] | 9/9 | 0/18 | 6/6 | 0/15 | 3/3 | 0/3 | 4057 | θ grid, α/|grid| |
| ours [ann_nubar] | 9/9 | 0/18 | 6/6 | 0/15 | 3/3 | 0/3 | 1665 | ANN only, U+ν̄<δ |
| ours [b9_noaudit] | 9/9 | 0/18 | 6/6 | 0/15 | 3/3 | 0/3 | 1288 | B9: no audit (unsound) |

Per FD (mean over seeds): oracle g3, raw g3, ours[inverse] U and calls

| FD | g3 oracle | g3 raw | truth | ours U | ours certified | ours calls | B9 certified | B7 g3 |
|---|---|---|---|---|---|---|---|---|
| labcode->labeler | 0.000 | 0.107 | True | 0.035 | 3/3 | 222 | 3/3 | 0.000 |
| labeler->ptype | 0.026 | 0.025 | True | 0.049 | 3/3 | 1020 | 3/3 | 0.020 |
| labeler->labcode | 0.128 | 0.108 | False | 0.210 | 0/3 | 324 | 0/3 | 0.089 |
| labeler->mktcat | 0.100 | 0.095 | False | 0.187 | 0/3 | 273 | 0/3 | 0.058 |
| appno->labeler | 0.653 | 0.660 | False | 0.852 | 0/3 | 24 | 0/3 | 0.243 |
| brand->labeler | 0.458 | 0.468 | False | 0.575 | 0/3 | 23 | 0/3 | 0.033 |
| generic->labeler | 0.659 | 0.665 | False | 0.877 | 0/3 | 29 | 0/3 | 0.057 |
| labcode->labeler_e2 | 0.020 | 0.125 | True | 0.048 | 3/3 | 95 | 3/3 | 0.014 |
| labcode->labeler_e8 | 0.080 | 0.178 | False | 0.092 | 0/3 | 483 | 0/3 | 0.064 |

## E1 e1_tax: tax200000 (3 seeds, δ=0.05, α per FD=0.005, rows=200000)

| method | true acc. (all) | **false acc. (all)** | true acc. natural | false acc. natural | true acc. probe | false acc. probe | oracle calls / run | note |
|---|---|---|---|---|---|---|---|---|
| B0 exact strings (g3 ≤ δ) | 3/15 | 0/15 | 3/12 | 0/12 | 0/3 | 0/3 | – |  |
| B1 proxy quotient θ=0.9 | 3/15 | 0/15 | 3/12 | 0/12 | 0/3 | 0/3 | – |  |
| B1 proxy quotient θ=0.85 | 0/15 | 0/15 | 0/12 | 0/12 | 0/3 | 0/3 | – |  |
| B1 proxy quotient θ=0.95 | 3/15 | 0/15 | 3/12 | 0/12 | 0/3 | 0/3 | – |  |
| B7 sample-only (m = our n) | 15/15 | 12/15 | 12/12 | 9/12 | 3/3 | 3/3 | 3265 | no guarantee |
| B4 canonicalize-all | 15/15 | 0/15 | 12/12 | 0/12 | 3/3 | 0/3 | 84575 | exact; shared over FDs |
| B5 pairwise blocked self-join | 12/15 | 0/15 | 12/12 | 0/12 | 0/3 | 0/3 | 2120516 | pair judgments; recall-limited |
| ours [inverse] | 15/15 | 0/15 | 12/12 | 0/12 | 3/3 | 0/3 | 5213 | primary, ν=0 (Cor A2) |
| ours [grid_inverse] | 15/15 | 0/15 | 12/12 | 0/12 | 3/3 | 0/3 | 10107 | θ grid, α/|grid| |
| ours [ann_nubar] | 15/15 | 0/15 | 12/12 | 0/12 | 3/3 | 0/3 | 3717 | ANN only, U+ν̄<δ |
| ours [b9_noaudit] | 15/15 | 0/15 | 12/12 | 0/12 | 3/3 | 0/3 | 2102 | B9: no audit (unsound) |

Per FD (mean over seeds): oracle g3, raw g3, ours[inverse] U and calls

| FD | g3 oracle | g3 raw | truth | ours U | ours certified | ours calls | B9 certified | B7 g3 |
|---|---|---|---|---|---|---|---|---|
| zip->city | 0.002 | 0.188 | True | 0.041 | 3/3 | 341 | 3/3 | 0.001 |
| zip->state | 0.002 | 0.114 | True | 0.037 | 3/3 | 74 | 3/3 | 0.001 |
| area_code->state | 0.000 | 0.119 | True | 0.036 | 3/3 | 15 | 3/3 | 0.000 |
| f_name->gender | 0.000 | 0.000 | True | 0.048 | 3/3 | 2388 | 3/3 | 0.000 |
| city->state | 0.228 | 0.276 | False | 0.423 | 0/3 | 358 | 0/3 | 0.007 |
| state->area_code | 0.547 | 0.545 | False | 0.723 | 0/3 | 30 | 0/3 | 0.263 |
| city->zip | 0.458 | 0.409 | False | 0.692 | 0/3 | 225 | 0/3 | 0.023 |
| city->area_code | 0.530 | 0.451 | False | 0.698 | 0/3 | 177 | 0/3 | 0.023 |
| zip->city_e2 | 0.022 | 0.203 | True | 0.049 | 3/3 | 640 | 3/3 | 0.002 |
| zip->city_e8 | 0.080 | 0.250 | False | 0.126 | 0/3 | 966 | 0/3 | 0.005 |

## E1b e1b_geonames_16k: discovery over all unary candidates (3 seeds)

candidates=58, true=10, rows=80000

| method | found | **false** | missed true | oracle calls |
|---|---|---|---|---|
| b3_tane_raw | 4.0 | 3 | 7.0 | 0 |
| b3_tane_norm | 4.0 | 3 | 7.0 | 0 |
| b1_quotient | 4.0 | 3 | 7.0 | 0 |
| b9_noaudit | 12.0 | 6 | 0.0 | 2885 |
| ours | 10.0 | 0 | 0.0 | 21759 |
| planner | 10.0 | 0 | 0.0 | 22449 |
| canonicalize-all | – | – | – | 42453 |

Certified closure: base certified 10.0, derived FDs (|LHS|≤2, bound ≤ δ) 73.0, derived bound violated by truth: 0

False acceptances: seed 0: {'b3_raw': ['city->tz_src8'], 'b3_norm': ['city->tz_src8'], 'b1': ['city->tz_src8'], 'ours': [], 'planner': [], 'b9': ['city->country_src8', 'city->tz_src8']}; seed 1: {'b3_raw': ['city->tz_src8'], 'b3_norm': ['city->tz_src8'], 'b1': ['city->tz_src8'], 'ours': [], 'planner': [], 'b9': ['city->country_src8', 'city->tz_src8']}; seed 2: {'b3_raw': ['city->tz_src8'], 'b3_norm': ['city->tz_src8'], 'b1': ['city->tz_src8'], 'ours': [], 'planner': [], 'b9': ['city->country_src8', 'city->tz_src8']}

- missed true by b3_raw: natural 12, probe 9 (over seeds)
- missed true by b1: natural 12, probe 9 (over seeds)
- missed true by ours: natural 0, probe 0 (over seeds)
- missed true by b9: natural 0, probe 0 (over seeds)

## E1b e1b_geonames_640k: discovery over all unary candidates (2 seeds)

candidates=58, true=10, rows=640000

| method | found | **false** | missed true | oracle calls |
|---|---|---|---|---|
| b3_tane_raw | 4.0 | 2 | 7.0 | 0 |
| b3_tane_norm | 4.0 | 2 | 7.0 | 0 |
| b1_quotient | 4.0 | 2 | 7.0 | 0 |
| b9_noaudit | 12.0 | 4 | 0.0 | 3014 |
| ours | 10.0 | 0 | 0.0 | 31188 |
| planner | 10.0 | 0 | 0.0 | 31188 |
| canonicalize-all | – | – | – | 246493 |

Certified closure: base certified 10.0, derived FDs (|LHS|≤2, bound ≤ δ) 73.0, derived bound violated by truth: 0

False acceptances: seed 0: {'b3_raw': ['city->tz_src8'], 'b3_norm': ['city->tz_src8'], 'b1': ['city->tz_src8'], 'ours': [], 'planner': [], 'b9': ['city->country_src8', 'city->tz_src8']}; seed 1: {'b3_raw': ['city->tz_src8'], 'b3_norm': ['city->tz_src8'], 'b1': ['city->tz_src8'], 'ours': [], 'planner': [], 'b9': ['city->country_src8', 'city->tz_src8']}

- missed true by b3_raw: natural 8, probe 6 (over seeds)
- missed true by b1: natural 8, probe 6 (over seeds)
- missed true by ours: natural 0, probe 0 (over seeds)
- missed true by b9: natural 0, probe 0 (over seeds)

## E1b e1b_ndc: discovery over all unary candidates (3 seeds)

candidates=66, true=10, rows=116620

| method | found | **false** | missed true | oracle calls |
|---|---|---|---|---|
| b3_tane_raw | 8.0 | 0 | 2.0 | 0 |
| b3_tane_norm | 8.0 | 0 | 2.0 | 0 |
| b1_quotient | 9.0 | 0 | 1.0 | 0 |
| b9_noaudit | 10.0 | 0 | 0.0 | 1446 |
| ours | 10.0 | 0 | 0.0 | 6305 |
| planner | 10.0 | 0 | 0.0 | 6305 |
| canonicalize-all | – | – | – | 6653 |

Certified closure: base certified 10.0, derived FDs (|LHS|≤2, bound ≤ δ) 64.0, derived bound violated by truth: 0

False acceptances: seed 0: {'b3_raw': [], 'b3_norm': [], 'b1': [], 'ours': [], 'planner': [], 'b9': []}; seed 1: {'b3_raw': [], 'b3_norm': [], 'b1': [], 'ours': [], 'planner': [], 'b9': []}; seed 2: {'b3_raw': [], 'b3_norm': [], 'b1': [], 'ours': [], 'planner': [], 'b9': []}

- missed true by b3_raw: natural 3, probe 3 (over seeds)
- missed true by b1: natural 0, probe 3 (over seeds)
- missed true by ours: natural 0, probe 0 (over seeds)
- missed true by b9: natural 0, probe 0 (over seeds)

## E1b e1b_tax: discovery over all unary candidates (3 seeds)

candidates=50, true=5, rows=200000

| method | found | **false** | missed true | oracle calls |
|---|---|---|---|---|
| b3_tane_raw | 1.0 | 0 | 4.0 | 0 |
| b3_tane_norm | 1.0 | 0 | 4.0 | 0 |
| b1_quotient | 1.0 | 0 | 4.0 | 0 |
| b9_noaudit | 5.0 | 0 | 0.0 | 4953 |
| ours | 5.0 | 0 | 0.0 | 12297 |
| planner | 5.0 | 0 | 0.0 | 12275 |
| canonicalize-all | – | – | – | 84575 |

Certified closure: base certified 5.0, derived FDs (|LHS|≤2, bound ≤ δ) 34.0, derived bound violated by truth: 0

False acceptances: seed 0: {'b3_raw': [], 'b3_norm': [], 'b1': [], 'ours': [], 'planner': [], 'b9': []}; seed 1: {'b3_raw': [], 'b3_norm': [], 'b1': [], 'ours': [], 'planner': [], 'b9': []}; seed 2: {'b3_raw': [], 'b3_norm': [], 'b1': [], 'ours': [], 'planner': [], 'b9': []}

- missed true by b3_raw: natural 9, probe 3 (over seeds)
- missed true by b1: natural 9, probe 3 (over seeds)
- missed true by ours: natural 0, probe 0 (over seeds)
- missed true by b9: natural 0, probe 0 (over seeds)

## E3 e3_geonames: coverage, 500 sampler repetitions per FD (α=0.05, δ=0.05)

| FD | g3 oracle | E[B] | P[U < E[B]] | certified rate | false-cert rate | mean samples |
|---|---|---|---|---|---|---|
| city->country | 0.0000 | 0.0008 | 0.000 | 1.000 | 0.000 | 200 |
| city->admin1 | 0.0000 | 0.0009 | 0.000 | 1.000 | 0.000 | 200 |
| admin1->country | 0.0000 | 0.0001 | 0.000 | 1.000 | 0.000 | 200 |
| country->admin1 | 0.7503 | 0.7812 | 0.002 | 0.000 | 0.000 | 100 |
| fcode->country | 0.8232 | 0.8232 | 0.000 | 0.000 | 0.000 | 100 |
| admin1->city | 0.5417 | 0.5736 | 0.004 | 0.000 | 0.000 | 100 |
| tz->country | 0.0036 | 0.0036 | 0.000 | 1.000 | 0.000 | 204 |
| country->tz | 0.1158 | 0.1201 | 0.024 | 0.000 | 0.000 | 272 |
| city->country_e3 | 0.0296 | 0.0367 | 0.004 | 1.000 | 0.000 | 2696 |
| city->country_e4 | 0.0394 | 0.0471 | 0.016 | 0.126 | 0.000 | 18335 |
| city->country_e5 | 0.0486 | 0.0580 | 0.024 | 0.008 | 0.000 | 12262 |
| city->country_e6 | 0.0579 | 0.0694 | 0.032 | 0.000 | 0.000 | 2201 |
| city->country_e7 | 0.0680 | 0.0818 | 0.022 | 0.000 | 0.000 | 888 |
| city->country_src4 | 0.0401 | 0.0404 | 0.002 | 0.950 | 0.000 | 6682 |
| city->country_src6 | 0.0597 | 0.0604 | 0.038 | 0.006 | 0.006 | 7776 |
| city->country_src7 | 0.0699 | 0.0707 | 0.036 | 0.000 | 0.000 | 1986 |
| city->tz_src8 | 0.0799 | 0.0803 | 0.040 | 0.000 | 0.000 | 1004 |
| city->tz | 0.0000 | 0.0004 | 0.000 | 1.000 | 0.000 | 200 |

## E3 e3_tax: coverage, 500 sampler repetitions per FD (α=0.05, δ=0.05)

| FD | g3 oracle | E[B] | P[U < E[B]] | certified rate | false-cert rate | mean samples |
|---|---|---|---|---|---|---|
| zip->city | 0.0020 | 0.0020 | 0.000 | 1.000 | 0.000 | 200 |
| zip->state | 0.0020 | 0.0020 | 0.000 | 1.000 | 0.000 | 200 |
| area_code->state | 0.0000 | 0.0000 | 0.000 | 1.000 | 0.000 | 200 |
| f_name->gender | 0.0002 | 0.0261 | 0.000 | 1.000 | 0.000 | 594 |
| city->state | 0.2279 | 0.2605 | 0.012 | 0.000 | 0.000 | 101 |
| state->area_code | 0.5469 | 0.5586 | 0.006 | 0.000 | 0.000 | 100 |
| city->zip | 0.4585 | 0.4917 | 0.006 | 0.000 | 0.000 | 100 |
| city->area_code | 0.5302 | 0.5621 | 0.008 | 0.000 | 0.000 | 100 |
| zip->city_e3 | 0.0313 | 0.0321 | 0.000 | 1.000 | 0.000 | 1115 |
| zip->city_e4 | 0.0411 | 0.0421 | 0.006 | 0.866 | 0.000 | 8981 |
| zip->city_e5 | 0.0509 | 0.0522 | 0.028 | 0.018 | 0.018 | 19519 |
| zip->city_e6 | 0.0606 | 0.0622 | 0.032 | 0.004 | 0.004 | 6029 |
| zip->city_e7 | 0.0706 | 0.0723 | 0.046 | 0.000 | 0.000 | 1815 |

## E2 e2_geonames: oracle cost vs size (GeoNames, cities500.txt)

| cities | rows | distinct city | proxy build s | ours calls / run | canonicalize-all | ratio | B5 pair judgments | correct decisions | false certified |
|---|---|---|---|---|---|---|---|---|---|
| 1000 | 5000 | 1702 | 0 | 3408 | 3585 | 1.1× | 102064 | 16/16 | 0 |
| 4000 | 20000 | 6724 | 7 | 7349 | 11807 | 1.6× | 363638 | 16/16 | 0 |
| 16000 | 80000 | 26805 | 28 | 11130 | 38927 | 3.5× | 1336664 | 16/16 | 0 |
| 64000 | 320000 | 106641 | 54 | 12087 | 131836 | 10.9× | 5700468 | 16/16 | 0 |
| 128000 | 640000 | 212426 | 86 | 14140 | 246493 | 17.4× | 11256863 | 16/16 | 0 |

## E4 e4_geonames: certified closure as a workload (5 random half-splits; 58 candidates, 10 true)

| split | certified half S @δ/2: calls | held-out true FDs | covered free by closure | direct certification of H: calls, true certified | derived bound violated | false covered |
|---|---|---|---|---|---|---|
| 0 | 40248 | 4 | 0 | 13614, 4 | 0 | 0 |
| 1 | 16684 | 3 | 0 | 10235, 3 | 0 | 0 |
| 2 | 10877 | 6 | 0 | 8626, 6 | 0 | 0 |
| 3 | 40158 | 2 | 0 | 19809, 2 | 0 | 0 |
| 4 | 9276 | 8 | 0 | 16761, 8 | 0 | 0 |

## E4 e4_ndc: certified closure as a workload (5 random half-splits; 66 candidates, 10 true)

| split | certified half S @δ/2: calls | held-out true FDs | covered free by closure | direct certification of H: calls, true certified | derived bound violated | false covered |
|---|---|---|---|---|---|---|
| 0 | 1729 | 6 | 0 | 4199, 6 | 0 | 0 |
| 1 | 3231 | 5 | 0 | 5281, 5 | 0 | 0 |
| 2 | 5559 | 3 | 0 | 3160, 3 | 0 | 0 |
| 3 | 2169 | 7 | 0 | 5171, 7 | 0 | 0 |
| 4 | 6174 | 4 | 0 | 4778, 4 | 0 | 0 |

## E4 e4_tax: certified closure as a workload (5 random half-splits; 50 candidates, 5 true)

| split | certified half S @δ/2: calls | held-out true FDs | covered free by closure | direct certification of H: calls, true certified | derived bound violated | false covered |
|---|---|---|---|---|---|---|
| 0 | 13882 | 2 | 0 | 6239, 2 | 0 | 0 |
| 1 | 26802 | 2 | 0 | 5646, 2 | 0 | 0 |
| 2 | 37623 | 3 | 0 | 3238, 3 | 0 | 0 |
| 3 | 3191 | 3 | 0 | 6210, 3 | 0 | 0 |
| 4 | 14035 | 2 | 0 | 7235, 2 | 0 | 0 |

## E7 e7_geonames: oracle noise (split/merge errors at rate p)

| p | false certified vs noisy truth | false certified vs clean truth | true (clean) missed | calls |
|---|---|---|---|---|
| 0.0 | 0 | 0 | 0.0 | 14418 |
| 0.01 | 0 | 0 | 0.0 | 19199 |
| 0.02 | 0 | 0 | 0.0 | 20784 |
| 0.05 | 0 | 0 | 3.0 | 46918 |
| 0.1 | 0 | 0 | 4.7 | 31978 |

## E7 e7_ndc: oracle noise (split/merge errors at rate p)

| p | false certified vs noisy truth | false certified vs clean truth | true (clean) missed | calls |
|---|---|---|---|---|
| 0.0 | 0 | 0 | 0.0 | 2062 |
| 0.01 | 0 | 0 | 0.0 | 2924 |
| 0.02 | 0 | 0 | 0.0 | 2763 |
| 0.05 | 0 | 0 | 0.0 | 2692 |
| 0.1 | 0 | 0 | 0.3 | 3525 |

## B2 b2_fastrfd_geonames_16k: FastRFD (rows=80000, 58 candidates, 10 true)

| g1 tolerance t | found | false | missed true | seconds |
|---|---|---|---|---|
| 0.0 | 3 | 1 | 8 | 421 |
| 0.001 | 15 | 7 | 2 | 449 |
| 0.01 | 29 | 19 | 0 | 377 |
| 0.05 | 50 | 40 | 0 | 380 |

## B2 b2_fastrfd_geonames_1k: FastRFD (rows=5000, 58 candidates, 10 true)

| g1 tolerance t | found | false | missed true | seconds |
|---|---|---|---|---|
| 0.0 | 3 | 1 | 8 | 5 |
| 0.001 | 15 | 7 | 2 | 6 |
| 0.01 | 28 | 18 | 0 | 7 |
| 0.05 | 50 | 40 | 0 | 6 |

## B2 b2_fastrfd_ndc: FastRFD (rows=116620, 66 candidates, 10 true)

| g1 tolerance t | found | false | missed true | seconds |
|---|---|---|---|---|
| 0.0 | 0 | 0 | 10 | 236 |
| 0.001 | 21 | 13 | 2 | 262 |
| 0.01 | 44 | 34 | 0 | 344 |
| 0.05 | 51 | 41 | 0 | 437 |

## B2 b2_fastrfd_ndc_finegrid: FastRFD (rows=116620, 66 candidates, 10 true)

| g1 tolerance t | found | false | missed true | seconds |
|---|---|---|---|---|
| 0.0001 | 3 | 1 | 8 | 251 |
| 0.0005 | 11 | 3 | 2 | 298 |

## B2 b2_fastrfd_tax: FastRFD (rows=200000, 50 candidates, 5 true)

| g1 tolerance t | found | false | missed true | seconds |
|---|---|---|---|---|
| 0.0 | 0 | 0 | 5 | 4293 |
| 0.001 | 29 | 25 | 1 | 6388 |
| 0.01 | 38 | 33 | 0 | 4461 |
| 0.05 | 43 | 38 | 0 | 3871 |

## B2 b2_fastrfd_tax_finegrid: FastRFD (rows=200000, 50 candidates, 5 true)

| g1 tolerance t | found | false | missed true | seconds |
|---|---|---|---|---|
| 0.0001 | 14 | 10 | 1 | 4110 |
| 0.0005 | 28 | 24 | 1 | 4400 |

