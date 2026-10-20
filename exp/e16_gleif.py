"""E16 (paper Sec. VI, "A real alias registry"): GLEIF as the inverse oracle for NDC labeler names.

GLEIF's LEI Golden Copy (CC0; snapshot 2026-10-20) lists, per legal entity (LEI), its legal name and up to five other
and five transliterated names (previous legal names, trading names, ...). We match NDC labeler spellings to GLEIF names
by exact equality of the alphanumeric lowercase form (no fuzzy matching, so the matching is not itself a proxy); a
key shared by several LEIs is ambiguous and dropped.
  --prep   stream the 5 GB CSV once, keep the GLEIF names whose key equals some NDC labeler key, and the full name set
           of every LEI so matched: results/icde27/e16_gleif_links.json
  (default)
  (a) Inverse from a real registry. The forward oracle stays the NDC code-graph oracle. For an entity e, the alias
      service returns the in-data spellings of e whose key is a GLEIF name of an LEI linked to e (an LEI is linked to
      e if some spelling of e matches it). Its omissions are GLEIF's, not ours. Coverage is recorded, and all unary
      NDC candidates are certified with this inverse as if it were complete (exp/e11_partial_inverse.py --registry
      gleif); see e11_partial_inverse_ndc_gleif.json.
  (b) An independent oracle for labcode -> labeler. On the tuples whose labeler spelling matches exactly one LEI, the
      LEI is an oracle that does not use the labeler codes; g3(labcode -> LEI) is computed exactly next to the
      code-graph and string-level g3 on the same tuples.
Output: results/icde27/e16_gleif.json
"""

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
LINKS = ROOT / "results/icde27/e16_gleif_links.json"
CSV = sorted((ROOT / "data/gleif").glob("*lei2-golden-copy.csv"))


def key(v):
    from semfd.proxy import layer1
    return re.sub(r"[^a-z0-9]", "", layer1(v))


NAME_COLS = (["Entity.LegalName"] + [f"Entity.OtherEntityNames.OtherEntityName.{i}" for i in range(1, 6)]
             + [f"Entity.TransliteratedOtherEntityNames.TransliteratedOtherEntityName.{i}" for i in range(1, 6)])


def prep(ndc_keys):
    import pandas as pd
    hit = {}                                   # key -> set of LEIs having it as a name
    names = {}                                 # LEI -> all name keys (only for LEIs with a hit)
    for ch in pd.read_csv(CSV[-1], usecols=["LEI"] + NAME_COLS, dtype=str, keep_default_na=False, chunksize=500_000):
        ks = {c: ch[c].map(lambda s: key(s) if s else "") for c in NAME_COLS}
        for c in NAME_COLS:
            m = ks[c].isin(ndc_keys)
            for lei, k in zip(ch["LEI"][m], ks[c][m]):
                hit.setdefault(k, set()).add(lei)
        leis = set(l for s in hit.values() for l in s)
        sel = ch["LEI"].isin(leis)
        for i in np.flatnonzero(sel.to_numpy()):
            lei = ch["LEI"].iat[i]
            names.setdefault(lei, set()).update(k for k in (ks[c].iat[i] for c in NAME_COLS) if k)
    LINKS.write_text(json.dumps({"csv": CSV[-1].name, "hit": {k: sorted(v) for k, v in hit.items()},
                                 "names": {l: sorted(v) for l, v in names.items()}}))


def registry_values(ds):
    """In-data labeler spellings the GLEIF alias service returns (see (a))."""
    lk = json.loads(LINKS.read_text())
    unique = {k: v[0] for k, v in lk["hit"].items() if len(v) == 1}
    tab = ds.oracle["labeler"]
    by_ent = {}
    for v, e in tab.items():
        by_ent.setdefault(e, []).append(v)
    kept = set()
    for e, vs in by_ent.items():
        leis = {unique[key(v)] for v in vs if key(v) in unique}
        if not leis:
            continue
        gnames = set().union(*(set(lk["names"].get(l, ())) for l in leis))
        kept |= {v for v in vs if key(v) in gnames}
    return kept, unique


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--prep", action="store_true")
    a = ap.parse_args()
    from semfd.certify import g3_codes
    from semfd.data import ndc
    ds = ndc(seed=0, near_miss=())
    vals = sorted(ds.oracle["labeler"])
    if a.prep:
        prep({key(v) for v in vals})
        sys.exit(0)
    from semfd.proxy import layer1
    kept, unique = registry_values(ds)
    lab = ds.df["labeler"].map(layer1)
    tab = ds.oracle["labeler"]
    ents = {tab[v] for v in vals}
    linked_ents = {tab[v] for v in vals if key(v) in unique}
    ent_vals = {}
    for v in vals:
        ent_vals.setdefault(tab[v], []).append(v)
    multi = [e for e in linked_ents if len(ent_vals[e]) > 1]
    res = {"gleif_file": json.loads(LINKS.read_text())["csv"], "labeler_values": len(vals), "entities": len(ents),
           "values_matching_one_lei": sum(key(v) in unique for v in vals),
           "values_ambiguous": sum(key(v) in json.loads(LINKS.read_text())["hit"] and key(v) not in unique for v in vals),
           "entities_linked": len(linked_ents),
           "tuple_mass_linked_entities": float(lab.map(lambda v: tab[v] in linked_ents).mean()),
           "tuple_mass_returned": float(lab.isin(kept).mean()),
           "multi_spelling_linked_entities": len(multi),
           "spellings_returned_share_multi": float(np.mean([sum(v in kept for v in ent_vals[e]) / len(ent_vals[e]) for e in multi]))
           if multi else None}
    # (b) independent LEI oracle on matched tuples
    m = lab.map(lambda v: key(v) in unique).to_numpy()
    lei = lab[m].map(lambda v: unique[key(v)])
    code = ds.df["labcode"][m].map(layer1)
    cid = {c: i for i, c in enumerate(dict.fromkeys(code))}
    lid = {c: i for i, c in enumerate(dict.fromkeys(lei))}
    gid = {e: i for i, e in enumerate(dict.fromkeys(lab[m].map(tab.get)))}
    sid = {s: i for i, s in enumerate(dict.fromkeys(lab[m]))}
    xc = np.array([cid[c] for c in code])
    res["lei_oracle"] = {"tuples": int(m.sum()), "tuple_share": float(m.mean()), "labcodes": len(cid), "leis": len(lid),
                         "g3_labcode_to_lei": g3_codes(xc, np.array([lid[x] for x in lei])),
                         "g3_labcode_to_codegraph": g3_codes(xc, np.array([gid[tab[v]] for v in lab[m]])),
                         "g3_labcode_to_string": g3_codes(xc, np.array([sid[v] for v in lab[m]]))}
    (ROOT / "results/icde27/e16_gleif.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1), flush=True)
