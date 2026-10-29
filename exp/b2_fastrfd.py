"""B2 (paper Sec. VI): FastRFD (Li et al., PVLDB 18(7) 2025; github.com/YukinoMR/FastRFD,
built locally with a completed pom.xml, JDK 21) as the relaxed-FD discovery baseline.

NOTE: FastRFD silently defaults to the first 1000 tuples although its README
says -r defaults to -1; we pass -r -1 and assert the tuple count it reports.
FastRFD discovers minimal RFDs X(<=d_X) -> Y(<=d_Y) whose g1 error (violating
tuple pairs) is <= t, with per-column edit-distance thresholds from a file. We
give tolerant columns thresholds {0,1,2,3} (or, with --thr d, the single threshold d) and exact columns {0}, run a grid of
t, and count X -> Y as accepted if any discovered RFD has LHS = {X} and RHS = Y.
Scored against oracle truth on the same candidate set as E1b.
Output: results/icde27/b2_fastrfd_<dataset><tag>.json
"""

import argparse
import gzip
import hashlib
import json
import os
import re
import shutil
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

PAT = re.compile(r"^\[(.*)\] --> \[(\w+)\(<=([\d.]+)\)\]$")
EMPTY = re.compile(r"^--> \[(\w+)\(<=([\d.]+)\)\]$")   # empty left-hand side: printed as " --> [Y(<=d)]"


def java_cmd():
    """FASTRFD_JAVA, else the JDK the paper used (~/opt/jdk-21*), else `java` on PATH; resolved at run time so that
    the module imports (and --help works) without a JDK. FASTRFD_JAR and FASTRFD_XMX (default 200g) likewise."""
    java = os.environ.get("FASTRFD_JAVA")
    if not java:
        jdks = sorted((Path.home() / "opt").glob("jdk-21*"))
        java = str(jdks[-1] / "bin/java") if jdks else shutil.which("java")
    if not java or not Path(java).exists():
        raise RuntimeError("no Java found: set FASTRFD_JAVA to a JDK >= 18 java executable (baselines/README.md)")
    jar = Path(os.environ.get("FASTRFD_JAR", Path.home() / "opt/src/FastRFD/target/FastRFD.jar"))
    if not jar.exists():
        raise RuntimeError(f"{jar} not found: build FastRFD per baselines/README.md or set FASTRFD_JAR")
    return [java, f"-Xmx{os.environ.get('FASTRFD_XMX', '200g')}", "-jar", str(jar)]


def parse_output(stdout):
    """Unary RFDs X -> Y as (X, Y) pairs, and the Y of every RFD with an empty left-hand side. The latter makes
    every X -> Y (same RHS threshold) non-minimal, so FastRFD does not print it; callers count it as accepted."""
    found, empty = set(), set()
    for line in stdout.splitlines():
        line = line.strip()
        m = EMPTY.match(line)
        if m:
            empty.add(m.group(1))
            continue
        m = PAT.match(line)
        if not m:
            continue
        lhs = [x.split("(")[0].strip() for x in m.group(1).split(",") if x.strip()]
        if len(lhs) == 1:
            found.add((lhs[0], m.group(2)))
    return found, empty


def run_fastrfd(df, exact, t, timeout, thr="0,1,2,3", log=None):
    """FastRFD's CSV reader splits lines on every comma and has no quoting (RelationalInput.java), so commas inside
    values are replaced by spaces after Layer-1 normalization; the same normalized strings are what TANE sees.
    Returns (found, empty_lhs_rhs, sec, input_sha256), or (None, None, timeout, sha) on timeout. With log, the full
    stdout/stderr are saved there (gzip). A non-zero exit raises."""
    with tempfile.TemporaryDirectory() as d:
        cols = list(df.columns)
        out = df.map(lambda v: layer1(v).replace(",", " "))
        out.columns = [f"{c}(String)" for c in cols]
        out.to_csv(f"{d}/t.csv", index=False)
        Path(f"{d}/thr.txt").write_text("\n".join("0" if exact[c] else thr for c in cols))
        sha = hashlib.sha256(Path(f"{d}/t.csv").read_bytes() + b"\0" + Path(f"{d}/thr.txt").read_bytes()).hexdigest()
        t0 = time.perf_counter()
        try:
            p = subprocess.run(java_cmd() + ["-f", f"{d}/t.csv", "-s", f"{d}/thr.txt",
                                "-t", str(t), "-r", "-1", "-o"], capture_output=True, text=True, timeout=timeout, cwd=d)
        except subprocess.TimeoutExpired:
            return None, None, timeout, sha
        sec = time.perf_counter() - t0
    if log:
        Path(log).parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(log, "wt") as fh:
            fh.write(f"# exit {p.returncode}\n# stdout\n{p.stdout}\n# stderr\n{p.stderr}")
    if p.returncode != 0:
        raise RuntimeError(f"FastRFD exited with {p.returncode}: {p.stderr[-500:]}")
    m = re.search(r"# of Tuples: (\d+)", p.stdout)
    assert m and int(m.group(1)) == len(df), f"FastRFD read {m and m.group(1)} tuples, expected {len(df)}"
    found, empty = parse_output(p.stdout)
    return found, empty, sec, sha


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="geonames")
    ap.add_argument("--kw", default="{}")
    ap.add_argument("--ts", type=float, nargs="+", default=[0.0, 0.001, 0.01, 0.05])
    ap.add_argument("--delta", type=float, default=0.05)
    ap.add_argument("--rows", type=int, default=0, help="row sample (0 = all)")
    ap.add_argument("--timeout", type=int, default=7200)
    ap.add_argument("--tag", default="")
    ap.add_argument("--thr", default="0,1,2,3", help="edit-distance thresholds of tolerant columns: the grid (default) "
                    "or one value chosen without the oracle (review v7 X4)")
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
    cands = [(x, y) for x in df.columns for y in df.columns if x != y and base(x) != base(y) and (x, y) not in ds.exclude]
    truth = {c: g3_codes(ent[c[0]][attrs[c[0]].codes], ent[c[1]][attrs[c[1]].codes]) for c in cands}
    T = {c for c in cands if truth[c] <= a.delta}
    res = {"dataset": ds.name, "rows": len(df), "n_cands": len(cands), "n_true": len(T), "thr": a.thr, "runs": []}
    for t in a.ts:
        found, empty, sec, sha = run_fastrfd(df, ds.exact, t, a.timeout, a.thr,
                                             log=ROOT / f"results/icde27/logs/b2_fastrfd_{a.dataset}{a.tag}_t{t}.out.gz")
        if found is None:
            res["runs"].append({"t": t, "timeout": True, "sec": sec, "input_sha256": sha})
            print(f"t={t} TIMEOUT", flush=True)
            continue
        acc = (found | {(x, y) for x, y in cands if y in empty}) & set(cands)
        res["runs"].append({"t": t, "sec": sec, "n": len(acc), "false": len(acc - T), "missed_true": len(T - acc),
                            "false_list": sorted(f"{x}->{y}" for x, y in acc - T), "empty_lhs_rhs": sorted(empty),
                            "input_sha256": sha})
        print(f"t={t} sec={sec:.1f} found={len(acc)} false={len(acc - T)} missed={len(T - acc)}", flush=True)
    outp = ROOT / f"results/icde27/b2_fastrfd_{a.dataset}{a.tag}.json"
    outp.write_text(json.dumps(res, indent=1))
