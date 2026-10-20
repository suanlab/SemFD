"""Facts quoted in the paper's running example (Table I) from the NDC snapshot.
Output: results/icde27/ndc_example.json"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from semfd.data import ndc  # noqa: E402
from semfd.proxy import layer1  # noqa: E402

ds = ndc(seed=0, near_miss=())
df = ds.df
o = ds.oracle["labeler"]
sub = df[df["labcode"] == "49035"]
firm = {o[layer1(v)] for v in sub["labeler"]}
codes_of_firm = sorted(set(df[df["labeler"].map(lambda v: o[layer1(v)]).isin(firm)]["labcode"]))
out = {"labcode": "49035", "distinct_raw_spellings": int(sub["labeler"].nunique()),
       "distinct_layer1_spellings": int(sub["labeler"].map(layer1).nunique()),
       "n_tuples": int(len(sub)), "oracle_entities_of_49035": sorted(firm),
       "labcodes_of_same_firm": codes_of_firm}
# rows shown in Table I must exist verbatim in the snapshot (labcode, raw labeler, marketing category)
import pandas as pd  # noqa: E402
raw = pd.read_csv(ROOT / "data/ndc/x/product.txt", sep="\t", dtype=str, keep_default_na=False,
                  encoding="latin-1", quoting=3)
raw["labcode"] = raw["PRODUCTNDC"].str.split("-").str[0]
shown = [("49035", "Wal-Mart Stores Inc", "OTC MONOGRAPH DRUG"),
         ("49035", "EQUATE (Wal-Mart Stores, Inc.) (see also WAL-MART INC)", "OTC MONOGRAPH DRUG"),
         ("49035", "WalMart", "OTC MONOGRAPH DRUG"),
         ("49035", "Wal-Mart Stores Inc", "ANDA"),
         ("79903", "WALMART INC.", "OTC MONOGRAPH DRUG")]
out["table1_rows_present"] = {f"{c}|{n}|{m}": int(((raw.labcode == c) & (raw.LABELERNAME == n) &
                                                   (raw.MARKETINGCATEGORYNAME == m)).sum()) for c, n, m in shown}
(ROOT / "results/icde27/ndc_example.json").write_text(json.dumps(out, indent=1))
print(out)
