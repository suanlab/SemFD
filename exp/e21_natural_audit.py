"""E21 (pre-registered, literature/prereg_e21_2026-10-24.md): does the cross-cluster audit change a decision on
NATURAL data? (MODIFY.md P1: "자연 데이터에서 audit가 중요한 결정 또는 검증 작업을 확인").

Natural-alias attributes only, no injected probes: GPG employer names (oracle: company number) and NDC labeler
names (oracle: labeler-code graph). Left-hand side = the alias-bearing attribute; right-hand sides = every other
per-row attribute listed below, fixed before looking at any result. For each candidate, exactly (from the truth):
  g3_oracle, g3_raw (Layer-1 strings), mu_i (condition (i) only = the no-audit estimator's mean) and
  mu = mu_i + mu_ii (Algorithm 1 with a complete inverse), with the hybrid proxy at theta = 0.9.
A candidate is AUDIT-DECISIVE if mu_i < delta <= mu (the no-audit estimator would tend to certify, the audit not).
For every audit-decisive candidate, and for every candidate with g3_raw <= delta < g3_oracle, both certifiers are
run for 3 seeds (alpha split over all candidates of the dataset) and their decisions are scored against g3_oracle.
Output: results/icde27/e21_natural_audit.json
"""

import json
import sys
import zlib
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "exp"))
from semfd.certify import certify, g3_codes  # noqa: E402
from semfd.data import Dataset, ndc  # noqa: E402
from semfd.proxy import layer1  # noqa: E402
from e11_partial_inverse import b_split  # noqa: E402

DELTA, ALPHA, THETA = 0.05, 0.05, 0.9


def gpg_ext():
    fr = []
    for y in range(2017, 2026):
        d = pd.read_csv(ROOT / f"data/gpg/gpg{y}.csv", dtype=str, keep_default_na=False)
        d["year"] = str(y)
        fr.append(d)
    d = pd.concat(fr, ignore_index=True)
    d["cn"] = d["CompanyNumber"].str.strip().str.upper()
    d = d[d["cn"] != ""].copy()
    d["name"] = d["EmployerName"]
    key = d["name"].map(layer1)
    d = d[~(d.groupby(key)["cn"].transform("nunique") > 1).to_numpy()].copy()     # homonyms dropped, as in E17
    d["empid"] = d["EmployerId"].str.strip()
    d["postcode"] = d["PostCode"].str.upper().str.replace(" ", "", regex=False)
    d["sic"] = d["SicCodes"].map(lambda s: ",".join(sorted(x.strip() for x in s.replace("\n", ",").split(",") if x.strip())))
    d["size"] = d["EmployerSize"]
    d["address"] = d["Address"]
    d["person"] = d["ResponsiblePerson"]
    d["curname"] = d["CurrentName"]
    d["link"] = d["CompanyLinkToGPGInfo"]
    cols = ["name", "empid", "postcode", "sic", "size", "year", "address", "person", "curname", "link"]
    df = d[cols].reset_index(drop=True)
    oracle = {"name": dict(zip(d["name"].map(layer1), d["cn"]))}
    return Dataset("gpg_ext", df, {a: a != "name" for a in cols}, oracle), "name"


def ndc_ext():
    ds = ndc(seed=0, near_miss=())
    p = pd.read_csv(ROOT / "data/ndc/x/product.txt", sep="\t", dtype=str, keep_default_na=False,
                    encoding="latin-1", quoting=3)
    df = ds.df.copy()
    df["dosage"], df["route"], df["substance"] = p["DOSAGEFORMNAME"], p["ROUTENAME"], p["SUBSTANCENAME"]
    exact = {**ds.exact, "dosage": True, "route": True, "substance": True}
    return Dataset("ndc_ext", df, exact, ds.oracle), "labeler"


def main(seeds=3):
    out = {"delta": DELTA, "theta": THETA, "datasets": {}}
    for make in (gpg_ext, ndc_ext):
        ds, X = make()
        attrs = ds.attrs()
        ent = ds.entity_codes(attrs)
        raw = {a: np.arange(len(attrs[a].vals)) for a in attrs}
        ys = [y for y in attrs if y != X]
        rows = []
        for y in ys:
            ax, ay = attrs[X], attrs[y]
            g_or = float(g3_codes(ent[X][ax.codes], ent[y][ay.codes]))
            g_raw = float(g3_codes(raw[X][ax.codes], raw[y][ay.codes]))
            ci, cii = b_split(ax, ay, ent[X], ent[y], THETA)
            rows.append({"fd": f"{X}->{y}", "g3_oracle": g_or, "g3_raw": g_raw, "mu_i": ci, "mu": ci + cii,
                         "audit_decisive": bool(ci < DELTA <= ci + cii),
                         "raw_hides_violation": bool(g_raw <= DELTA < g_or)})
        af = ALPHA / len(ys)
        for r in rows:
            if not (r["audit_decisive"] or r["raw_hides_violation"]):
                continue
            y = r["fd"].split("->")[1]
            runs = []
            for s in range(seeds):
                rng = lambda tag: np.random.default_rng(zlib.crc32(f"e21|{tag}|{s}|{X}|{y}".encode()))
                o1 = ds.oracles(inverse=True)
                a1 = certify(attrs[X], attrs[y], o1[X], o1[y], THETA, DELTA, af, rng("audit"), inverse=True)
                o0 = ds.oracles(inverse=False)
                a0 = certify(attrs[X], attrs[y], o0[X], o0[y], THETA, DELTA, af, rng("noaudit"), audit=False)
                runs.append({"seed": s, "audit": {"certified": bool(a1["certified"]), "ub": a1["ub"], "calls": a1["calls"]},
                             "noaudit": {"certified": bool(a0["certified"]), "ub": a0["ub"], "calls": a0["calls"]}})
            r["runs"] = runs
        out["datasets"][ds.name] = {"rows": len(ds.df), "lhs": X, "distinct_lhs": len(attrs[X].vals),
                                    "candidates": rows}
        for r in rows:
            print(ds.name, r["fd"], {k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()
                                     if k not in ("fd", "runs")},
                  [(x["audit"]["certified"], x["noaudit"]["certified"]) for x in r.get("runs", [])], flush=True)
        (ROOT / "results/icde27/e21_natural_audit.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
