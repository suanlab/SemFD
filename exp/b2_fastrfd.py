"""B2 (paper Sec. VI): FastRFD (Li et al., PVLDB 18(7) 2025; github.com/YukinoMR/FastRFD,
built locally with a completed pom.xml, JDK 21) as the relaxed-FD discovery baseline.

NOTE: FastRFD silently defaults to the first 1000 tuples although its README
says -r defaults to -1; we pass -r -1 and assert the tuple count it reports.
FastRFD discovers minimal RFDs X(<=d_X) -> Y(<=d_Y) whose g1 error (violating
tuple pairs) is <= t, with per-column edit-distance thresholds from a file. We
give tolerant columns thresholds {0,1,2,3} and exact columns {0}, run a grid of
t, and count X -> Y as accepted if any discovered RFD has LHS = {X} and RHS = Y.
Scored against oracle truth on the same candidate set as E1b.
Output: results/icde27/b2_fastrfd_<dataset><tag>.json
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from semfd.certify import g3_codes  # noqa: E402
from semfd.data import LOADERS  # noqa: E402
from semfd.probes import base_attr as base  # noqa: E402
from semfd.proxy import Attr, layer1  # noqa: E402

JAR = Path(os.environ.get("FASTRFD_JAR", Path.home() / "opt/src/FastRFD/target/FastRFD.jar"))
JAVA = Path(os.environ.get("FASTRFD_JAVA", sorted((Path.home() / "opt").glob("jdk-21*"))[-1] / "bin/java"))
PAT = re.compile(r"^\[(.*)\] --> \[(\w+)\(<=([\d.]+)\)\]$")


def run_fastrfd(df, exact, t, timeout):
    with tempfile.TemporaryDirectory() as d:
        cols = list(df.columns)
        out = df.map(lambda v: layer1(v).replace(",", " "))
        out.columns = [f"{c}(String)" for c in cols]
        out.to_csv(f"{d}/t.csv", index=False)
        Path(f"{d}/thr.txt").write_text("\n".join("0" if exact[c] else "0,1,2,3" for c in cols))
        t0 = time.perf_counter()
        try:
            p = subprocess.run([str(JAVA), "-Xmx200g", "-jar", str(JAR), "-f", f"{d}/t.csv", "-s", f"{d}/thr.txt",
                                "-t", str(t), "-r", "-1", "-o"], capture_output=True, text=True, timeout=timeout, cwd=d)
        except subprocess.TimeoutExpired:
            return None, timeout
        sec = time.perf_counter() - t0
    m = re.search(r"# of Tuples: (\d+)", p.stdout)
    assert m and int(m.group(1)) == len(df), f"FastRFD read {m and m.group(1)} tuples, expected {len(df)}"
    found = set()
    for line in p.stdout.splitlines():
        m = PAT.match(line.strip())
        if not m:
            continue
        lhs = [x.split("(")[0].strip() for x in m.group(1).split(",") if x.strip()]
        if len(lhs) == 1:
            found.add((lhs[0], m.group(2)))
    return found, sec


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="geonames")
    ap.add_argument("--kw", default="{}")
    ap.add_argument("--ts", type=float, nargs="+", default=[0.0, 0.001, 0.01, 0.05])
    ap.add_argument("--delta", type=float, default=0.05)
    ap.add_argument("--rows", type=int, default=0, help="row sample (0 = all)")
    ap.add_argument("--timeout", type=int, default=7200)
    ap.add_argument("--tag", default="")
    a = ap.parse_args()
    ds = LOADERS[a.dataset](seed=0, **json.loads(a.kw))
    df = ds.df[list(ds.exact)]
    if a.rows:
        df = df.sample(a.rows, random_state=0)
    attrs = {c: Attr(c, df[c], exact=True) for c in df.columns}
    ent = {}
    for c, at in attrs.items():
        tab = ds.oracle.get(c)
        e = [tab[v] if tab else v for v in at.vals]
        eid = {x: i for i, x in enumerate(dict.fromkeys(e))}
        ent[c] = [eid[x] for x in e]
    import numpy as np
    ent = {c: np.array(v) for c, v in ent.items()}
    cands = [(x, y) for x in df.columns for y in df.columns if x != y and base(x) != base(y)]
    truth = {c: g3_codes(ent[c[0]][attrs[c[0]].codes], ent[c[1]][attrs[c[1]].codes]) for c in cands}
    T = {c for c in cands if truth[c] <= a.delta}
    res = {"dataset": ds.name, "rows": len(df), "n_cands": len(cands), "n_true": len(T), "runs": []}
    for t in a.ts:
        found, sec = run_fastrfd(df, ds.exact, t, a.timeout)
        if found is None:
            res["runs"].append({"t": t, "timeout": True, "sec": sec})
            print(f"t={t} TIMEOUT", flush=True)
            continue
        acc = found & set(cands)
        res["runs"].append({"t": t, "sec": sec, "n": len(acc), "false": len(acc - T), "missed_true": len(T - acc),
                            "false_list": sorted(f"{x}->{y}" for x, y in acc - T)})
        print(f"t={t} sec={sec:.1f} found={len(acc)} false={len(acc - T)} missed={len(T - acc)}", flush=True)
    outp = ROOT / f"results/icde27/b2_fastrfd_{a.dataset}{a.tag}.json"
    outp.write_text(json.dumps(res, indent=1))
