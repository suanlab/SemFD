"""Build results/icde27/TABLES.md from results/icde27/*.json (paper numbers
must come from here). Usage: .venv/bin/python -I exp/make_tables.py"""

import json
import sys
from collections import defaultdict
from pathlib import Path

import re

import numpy as np



sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from semfd.probes import is_probe_fd as is_probe  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "results/icde27"
out = []


def load(p):
    return json.loads(p.read_text())


# ------------------------------------------------------------------ E1
for p in sorted(R.glob("e1_*.json")):
    runs = load(p)
    d = runs[0]["delta"]
    out.append(f"## E1 {p.stem}: {runs[0]['dataset']} ({len(runs)} seeds, δ={d}, "
               f"α per FD={runs[0].get('alpha_per_fd', runs[0]['alpha']):.4g}, rows={runs[0]['rows']})\n")
    out.append("| method | true acc. (all) | **false acc. (all)** | true acc. natural | false acc. natural | "
               "true acc. probe | false acc. probe | oracle calls / run | note |")
    out.append("|---|---|---|---|---|---|---|---|---|")
    fds = [f for r in runs for f in r["fds"]]
    nt = sum(f["truth"] for f in fds)
    nf = len(fds) - nt

    nat = [not is_probe(f["fd"]) for f in fds]
    ntn = sum(f["truth"] and n for f, n in zip(fds, nat))
    nfn = sum((not f["truth"]) and n for f, n in zip(fds, nat))

    def row(name, acc, calls="–", note=""):
        ta = sum(a and f["truth"] for a, f in zip(acc, fds))
        fa = sum(a and not f["truth"] for a, f in zip(acc, fds))
        tan = sum(a and f["truth"] and n for a, f, n in zip(acc, fds, nat))
        fan = sum(a and not f["truth"] and n for a, f, n in zip(acc, fds, nat))
        out.append(f"| {name} | {ta}/{nt} | {fa}/{nf} | {tan}/{ntn} | {fan}/{nfn} | {ta - tan}/{nt - ntn} | "
                   f"{fa - fan}/{nf - nfn} | {calls} | {note} |")
    row("B0 exact strings (g3 ≤ δ)", [f["b0_exact_g3"] <= d for f in fds])
    th = str(runs[0]["theta0"])
    row(f"B1 proxy quotient θ={th}", [f["b1_quot_g3"][th] <= d for f in fds])
    for th2 in sorted(fds[0]["b1_quot_g3"]):
        if th2 != th:
            row(f"B1 proxy quotient θ={th2}", [f["b1_quot_g3"][th2] <= d for f in fds])
    for f in fds:
        # B7 at s = our own sample count 
        f["_b7"] = next(z for z in f["b7_sample"] if z["m"] == f["ours"]["inverse"]["samples"])
    row("B7 sample-only (m = our n)", [f["_b7"]["g3"] <= d for f in fds],
        f"{np.mean([sum(f['_b7']['calls'] for f in r['fds']) for r in runs]):.0f}", "no guarantee")
    row("B4 canonicalize-all", [f["b4_canon_all"]["g3"] <= d for f in fds],
        f"{np.mean([r['canon_all'] for r in runs]):.0f}", "exact; shared over FDs")
    row("B5 pairwise blocked self-join", [f["b5_pairwise"]["g3"] <= d for f in fds],
        f"{np.mean([sum(f['b5_pairwise']['calls'] for f in r['fds']) for r in runs]):.0f}",
        "pair judgments; recall-limited")
    for v in fds[0]["ours"]:
        row(f"ours [{v}]", [f["ours"][v]["certified"] for f in fds],
            f"{np.mean([r['run_calls_' + v] for r in runs]):.0f}",
            {"inverse": "primary, ν=0 (Cor A2)", "grid_inverse": "θ grid, α/|grid|",
             "ann_nubar": "ANN only, U+ν̄<δ", "b9_noaudit": "B9: no audit (unsound)"}.get(v, ""))
    out.append("\nPer FD (mean over seeds): oracle g3, raw g3, ours[inverse] U and calls\n")
    out.append("| FD | g3 oracle | g3 raw | truth | ours U | ours certified | ours calls | B9 certified | B7 g3 |")
    out.append("|---|---|---|---|---|---|---|---|---|")
    by = defaultdict(list)
    for f in fds:
        by[f["fd"]].append(f)
    for k, fs in by.items():
        out.append(f"| {k} | {np.mean([f['g3'] for f in fs]):.3f} | {np.mean([f['b0_exact_g3'] for f in fs]):.3f} | "
                   f"{fs[0]['truth']} | {np.mean([min(1.0, f['ours']['inverse']['ub']) for f in fs]):.3f} | "
                   f"{sum(f['ours']['inverse']['certified'] for f in fs)}/{len(fs)} | "
                   f"{np.mean([f['ours']['inverse']['calls'] for f in fs]):.0f} | "
                   f"{sum(f['ours']['b9_noaudit']['certified'] for f in fs)}/{len(fs)} | "
                   f"{np.mean([f['_b7']['g3'] for f in fs]):.3f} |")
    out.append("")

# ------------------------------------------------------------------ E1b
for p in sorted(R.glob("e1b_*.json")):
    runs = load(p)
    out.append(f"## E1b {p.stem}: discovery over all unary candidates ({len(runs)} seeds)\n")
    out.append(f"candidates={runs[0]['n_cands']}, true={runs[0]['n_true']}, rows={runs[0]['rows']}\n")
    out.append("| method | found | **false** | missed true | oracle calls |")
    out.append("|---|---|---|---|---|")
    for m, calls in (("b3_tane_raw", None), ("b3_tane_norm", None), ("b1_quotient", None),
                     ("b9_noaudit", "b9_calls_total"), ("ours", "ours_calls_total"), ("planner", "planner_calls_total")):
        if m not in runs[0]:
            continue
        c = f"{np.mean([r[calls] for r in runs]):.0f}" if calls else "0"
        out.append(f"| {m} | {np.mean([r[m]['n'] for r in runs]):.1f} | {sum(r[m]['false'] for r in runs)} | "
                   f"{np.mean([r[m]['missed_true'] for r in runs]):.1f} | {c} |")
    out.append(f"| canonicalize-all | – | – | – | {np.mean([r['canon_all'] for r in runs]):.0f} |")
    out.append(f"\nCertified closure: base certified {np.mean([r['derived']['n_certified_base'] for r in runs]):.1f}, "
               f"derived FDs (|LHS|≤2, bound ≤ δ) {np.mean([r['derived']['n_derived_total'] for r in runs]):.1f}, "
               f"derived bound violated by truth: {sum(r['derived']['n_violating_bound'] for r in runs)}\n")
    out.append("False acceptances: " + "; ".join(f"seed {r['seed']}: {r['false_lists']}" for r in runs) + "\n")
    if "missed_lists" in runs[0]:
        for m in runs[0]["missed_lists"]:
            miss = [x for r in runs for x in r["missed_lists"][m]]
            out.append(f"- missed true by {m}: natural {sum(not is_probe(x) for x in miss)}, "
                       f"probe {sum(is_probe(x) for x in miss)} (over seeds)")
        out.append("")

# ------------------------------------------------------------------ E3
for p in sorted(q for q in R.glob("e3_*.json") if not q.name.startswith(("e3_refine", "e3_ideal"))):
    e = load(p)
    if "alpha" not in e:          # e3_ideal_witness.json (diagnostic, reported in PAPER_NUMBERS)
        continue
    out.append(f"## E3 {p.stem}: coverage, {e['reps']} sampler repetitions per FD (α={e['alpha']}, δ={e['delta']})\n")
    out.append("| FD | g3 oracle | E[B] | P[U < E[B]] | certified rate | false-cert rate | mean samples |")
    out.append("|---|---|---|---|---|---|---|")
    for f in e["fds"]:
        out.append(f"| {f['fd']} | {f['g3']:.4f} | {f['EB']:.4f} | {f['miscover_EB']:.3f} | {f['cert_rate']:.3f} | "
                   f"{f['false_cert_rate']:.3f} | {f['samples_mean']:.0f} |")
    out.append("")

# ------------------------------------------------------------------ E2
for p in sorted(R.glob("e2_*.json")):
    runs = load(p)
    out.append(f"## E2 {p.stem}: oracle cost vs size (GeoNames, {runs[0]['source']})\n")
    out.append("| cities | rows | distinct city | proxy build s | ours calls / run | canonicalize-all | ratio | "
               "B5 pair judgments | correct decisions | false certified |")
    out.append("|---|---|---|---|---|---|---|---|---|---|")
    by = defaultdict(list)
    for r in runs:
        by[r["n_cities"]].append(r)
    for C, rs in sorted(by.items()):
        ok = sum(f["ours"]["certified"] == f["truth"] for r in rs for f in r["fds"])
        tot = sum(len(r["fds"]) for r in rs)
        fc = sum(f["ours"]["certified"] and not f["truth"] for r in rs for f in r["fds"])
        oc, ca = np.mean([r["run_calls"] for r in rs]), np.mean([r["canon_all"] for r in rs])
        b5 = np.mean([sum(f["b5_pairwise"]["calls"] for f in r["fds"]) for r in rs])
        out.append(f"| {C} | {rs[0]['rows']} | {np.mean([r['distinct']['city'] for r in rs]):.0f} | "
                   f"{np.mean([r['sec']['proxy'] for r in rs]):.0f} | {oc:.0f} | {ca:.0f} | {ca / oc:.1f}× | {b5:.0f} | "
                   f"{ok}/{tot} | {fc} |")
    out.append("")

# ------------------------------------------------------------------ E4
for p in sorted(R.glob("e4_*.json")):
    e = load(p)
    sp = e["splits"]
    out.append(f"## E4 {p.stem}: certified closure as a workload ({len(sp)} random half-splits; "
               f"{e['n_cands']} candidates, {e['n_true']} true)\n")
    out.append("| split | certified half S @δ/2: calls | held-out true FDs | covered free by closure | "
               "direct certification of H: calls, true certified | derived bound violated | false covered |")
    out.append("|---|---|---|---|---|---|---|")
    for r in sp:
        out.append(f"| {r['split']} | {r['calls_S_half_delta']} | {r['H_true']} | {r['H_covered_by_closure']} | "
                   f"{r['calls_H_direct']}, {r['H_direct_certified_true']} | {r['derived_violations']} | {r['H_false_covered']} |")
    out.append("")

# ------------------------------------------------------------------ E7
for p in sorted(R.glob("e7_*.json")):
    e = load(p)
    out.append(f"## E7 {p.stem}: oracle noise (split/merge errors at rate p)\n")
    out.append("| p | false certified vs noisy truth | false certified vs clean truth | true (clean) missed | calls |")
    out.append("|---|---|---|---|---|")
    by = defaultdict(list)
    for r in e["runs"]:
        by[r["p"]].append(r)
    for pp, rs in sorted(by.items()):
        out.append(f"| {pp} | {sum(r['false_vs_noisy'] for r in rs)} | {sum(r['false_vs_clean'] for r in rs)} | "
                   f"{np.mean([r['missed_vs_clean'] for r in rs]):.1f} | {np.mean([r['calls'] for r in rs]):.0f} |")
    out.append("")

# ------------------------------------------------------------------ B2
for p in sorted(R.glob("b2_fastrfd_*.json")):
    e = load(p)
    out.append(f"## B2 {p.stem}: FastRFD (rows={e['rows']}, {e['n_cands']} candidates, {e['n_true']} true)\n")
    out.append("| g1 tolerance t | found | false | missed true | seconds |")
    out.append("|---|---|---|---|---|")
    for r in e["runs"]:
        if r.get("timeout"):
            out.append(f"| {r['t']} | timeout | | | {r['sec']} |")
        else:
            out.append(f"| {r['t']} | {r['n']} | {r['false']} | {r['missed_true']} | {r['sec']:.0f} |")
    out.append("")

(R / "TABLES.md").write_text("\n".join(out) + "\n")
print("\n".join(out))


# ------------------------------------------------------------------ LaTeX snippets for paper/
def latex():
    T = ROOT / "paper/tables"
    T.mkdir(exist_ok=True)
    ds_names = [("geonames_16k", "GeoNames"), ("tax", "Tax"), ("ndc", "NDC")]
    big_names = ds_names + [("gpg", "GPG"), ("geonames_640k", "GeoNames-640k")]   # GPG: second natural-alias dataset; 640k: 2 seeds
    # Table: discovery over all unary candidates (E1b) + FastRFD
    rows = []
    for key, nice in big_names:
        p = R / f"e1b_{key}.json"
        if not p.exists():
            continue
        runs = load(p)
        S = len(runs)
        f = lambda m: (np.mean([r[m]["n"] for r in runs]), sum(r[m]["false"] for r in runs) / S,
                       np.mean([r[m]["missed_true"] for r in runs]))
        cells = []
        for m in ("b3_tane_raw", "b1_quotient", "b9_noaudit", "ours"):
            n, fa, mi = f(m)
            fmt = lambda v: f"{v:.0f}" if abs(v - round(v)) < 1e-9 else f"{v:.1f}"
            cells.append(f"{fmt(fa)} / {fmt(mi)}")
        b2 = R / f"b2_fastrfd_{key}.json"
        if b2.exists():
            e = load(b2)
            for i, t in enumerate((0.0, 0.001)):
                r = next(r for r in e["runs"] if r["t"] == t)
                cells.insert(1 + i, f"{r['false']} / {r['missed_true']}" if not r.get("timeout") else "t/o")
        else:
            cells[1:1] = ["n/r", "n/r"]
        rows.append(f"{nice} ({runs[0]['n_cands']}/{runs[0]['n_true']}) & " + " & ".join(cells) + " \\\\")
    (T / "e1b.tex").write_text(
        "\\begin{table}[t]\\centering\\small\\caption{Discovery over all unary candidates: false accepted / true "
        "missed per run (mean over 3 seeds, 2 at 640k rows; candidates/true in parentheses; n/r: FastRFD not run at 640k rows). FastRFD (deterministic, one run on the seed-0 "
        "table) at $g_1$ tolerance $t$. Generated by exp/make\\_tables.py from results/icde27/e1b\\_*.json, b2\\_*.json.}\\label{tab:e1b}\n"
        "\\setlength{\\tabcolsep}{3pt}\\begin{tabular}{lcccccc}\\toprule\n"
        "data & TANE ($g_3$) & \\multicolumn{2}{c}{FastRFD, $t=0$ / $10^{-3}$} & quotient & no audit & ours \\\\\\midrule\n" + "\n".join(rows) +
        "\n\\bottomrule\\end{tabular}\\end{table}\n")
    # Table: oracle cost
    rows = []
    for key, nice in big_names:
        p = R / f"e1b_{key}.json"
        if not p.exists():
            continue
        runs = load(p)
        oc, ca = np.mean([r["ours_calls_total"] for r in runs]), np.mean([r["canon_all"] for r in runs])
        fi = (f"{np.mean([r['ours_calls_fwd_inv'][0] for r in runs]):,.0f} + {np.mean([r['ours_calls_fwd_inv'][1] for r in runs]):,.0f}"
              if "ours_calls_fwd_inv" in runs[0] else "--")
        cvp = R / "canon_variant_only.json"
        ckey = "geonames_128k" if key == "geonames_640k" else key      # same generator, sizes and attributes
        ia = load(cvp)[ckey]["canon_inverse_aware"] if cvp.exists() and ckey in load(cvp) else None
        if ia and ckey != key:
            assert abs(load(cvp)[ckey]["canon_all"] - ca) < 1, "inverse-aware cost from a different domain"
        iat = f"{ia:,.0f} ({ia / oc:.1f}$\\times$)" if ia else "--"
        rat = [r["canon_all"] / r["ours_calls_total"] for r in runs]
        rows.append(f"{nice} & {runs[0]['rows']:,} & {oc:,.0f} & {fi} & {ca:,.0f} & {ca / oc:.1f}$\\times$ "
                    f"({min(rat):.1f}--{max(rat):.1f}) & {iat} \\\\")
    if (R / "e2_geonames.json").exists():
        e2 = load(R / "e2_geonames.json")
        big = [r for r in e2 if r["n_cities"] == max(x["n_cities"] for x in e2)]
        oc, ca = np.mean([r["run_calls"] for r in big]), np.mean([r["canon_all"] for r in big])
        fi = (f"{np.mean([r['run_calls_fwd_inv'][0] for r in big]):,.0f} + {np.mean([r['run_calls_fwd_inv'][1] for r in big]):,.0f}"
              if "run_calls_fwd_inv" in big[0] else "--")
        cvp = R / "canon_variant_only.json"
        ia = load(cvp).get("geonames_128k", {}).get("canon_inverse_aware") if cvp.exists() else None
        ia128 = f"{ia:,.0f} ({ia / oc:.1f}$\\times$)" if ia else "--"
        rat = [r["canon_all"] / r["run_calls"] for r in big]
        rows.append(f"GeoNames-{big[0]['rows'] // 1000}k, 8 FDs$^\\dagger$ & {big[0]['rows']:,} & {oc:,.0f} & {fi} & {ca:,.0f} & "
                    f"{ca / oc:.1f}$\\times$ ({min(rat):.1f}--{max(rat):.1f}) & {ia128} \\\\")
    (T / "cost.tex").write_text(
        "\\begin{table*}[t]\\centering\\small\\caption{Oracle calls per run: certifying all unary candidates ("
        + ", ".join(str(load(R / f"e1b_{k}.json")[0]["n_cands"]) for k, _ in big_names if (R / f"e1b_{k}.json").exists())
        + " per run on " + ", ".join(n for k, n in big_names if (R / f"e1b_{k}.json").exists()).replace("GeoNames-640k", "GeoNames at 640k rows") + "; ours) vs.\\ "
        "canonicalizing every distinct value; ``fwd + inv'' splits our calls into forward canonicalizations and inverse "
        "(alias-list) lookups; the ratio divides mean calls (parentheses: min--max of per-seed ratios); components are rounded separately; ``inv.-aware'' lets canonicalize-all also use inverse lookups (one forward and one inverse call "
        "per entity, if cheaper than per value). $^\\dagger$8 FDs, scaling experiment. Generated by exp/make\\_tables.py.}"
        "\\label{tab:cost}\n\\setlength{\\tabcolsep}{6pt}\\begin{tabular}{lrrrrrr}\\toprule\n"
        "data & rows & ours & fwd + inv & canon.-all & ratio & inv.-aware \\\\\\midrule\n" + "\n".join(rows) +
        "\n\\bottomrule\\end{tabular}\\end{table*}\n")


    # Table: sensitivity (proxy, k, theta) for the primary (inverse) certificate
    rows = []
    settings = [("", "hybrid, $k$=5, $\\theta$=0.9 (default)"), ("_tfidf", "TF-IDF only"), ("_emb", "embedding only"),
                ("_edit", "TF-IDF nbrs, edit score"), ("_k3", "$k$=3"), ("_k10", "$k$=10"),
                ("_th0.8", "$\\theta$=0.8"), ("_th0.95", "$\\theta$=0.95"),
                ("_rho0.05", "variant rate $\\rho$=0.05"), ("_rho0.5", "variant rate $\\rho$=0.5")]
    for suf, nice in settings:
        cells = []
        for key in ("geonames_16k", "ndc"):
            pth = R / f"e1_{key}{suf}.json"
            if key == "ndc" and suf.startswith("_rho"):
                cells.append("n/a & n/a")              # NDC aliases are natural: no injection rate
                continue
            if not pth.exists():
                raise FileNotFoundError(f"Missing sensitivity result: {pth}")
            runs = load(pth)
            fds = [f for r in runs for f in r["fds"]]
            fc = sum(f["ours"]["inverse"]["certified"] and not f["truth"] for f in fds)
            mt = sum((not f["ours"]["inverse"]["certified"]) and f["truth"] for f in fds)
            cells.append(f"{fc}/{mt} & {np.mean([r['run_calls_inverse'] for r in runs]):,.0f} "
                         f"({np.mean([r['canon_all'] for r in runs]) / np.mean([r['run_calls_inverse'] for r in runs]):.1f}$\\times$)")
        rows.append(f"{nice} & " + " & ".join(cells) + " \\\\")
    (T / "sensitivity.tex").write_text(
        "\\begin{table}[t]\\centering\\small\\caption{Sensitivity of the certificate (inverse access) to the proxy, the "
        "number of neighbors $k$, the partition threshold $\\theta$ and the variant rate $\\rho$: false certified / true "
        "missed summed over 3 seeds (not per run) on the curated candidate lists ("
        + " and ".join(str(len(load(R / f"e1_{k}.json")[0]["fds"])) for k in ("geonames_16k", "ndc"))
        + " FDs per run), oracle calls per run and (in parentheses) canonicalize-all calls divided by ours. Generated by exp/make\\_tables.py.}\\label{tab:sens}\n"
        "\\setlength{\\tabcolsep}{3pt}\\begin{tabular}{lrrrr}\\toprule\n"
        "& \\multicolumn{2}{c}{GeoNames-16k} & \\multicolumn{2}{c}{NDC}\\\\\n"
        "setting & F/M (3 seeds) & calls & F/M (3 seeds) & calls \\\\\\midrule\n" + "\n".join(rows) +
        "\n\\bottomrule\\end{tabular}\\end{table}\n")

    # Table: natural FDs (no probes), per FD, E1 default runs
    rows = []
    for key, nice in ds_names:
        pth = R / f"e1_{key}.json"
        if not pth.exists():
            continue
        runs = load(pth)
        by = defaultdict(list)
        for r in runs:
            for f in r["fds"]:
                if not is_probe(f["fd"]):
                    by[f["fd"]].append(f)
        for k, fs in by.items():
            x, y = k.split("->")
            ok = sum(f["ours"]["inverse"]["certified"] for f in fs)
            rows.append(f"{nice} & {x.replace('_', chr(92) + '_')}$\\rightarrow${y.replace('_', chr(92) + '_')} & "
                        f"{np.mean([f['g3'] for f in fs]):.3f} & {np.mean([f['b0_exact_g3'] for f in fs]):.3f} & "
                        f"{ok}/{len(fs)} & {np.mean([min(1.0, f['ours']['inverse']['ub']) for f in fs]):.3f} & "
                        f"{np.mean([f['ours']['inverse']['calls'] for f in fs]):,.0f} \\\\")
    (T / "natural.tex").write_text(
        "\\begin{table}[t]\\centering\\footnotesize\\caption{Natural (non-injected) candidate FDs: $g_3$ on the canonical "
        "instance and on the raw strings, certifications over 3 seeds, mean final bound $U$ and mean oracle calls of the "
        "certificate (inverse access; with a cache shared across candidates, per-FD calls are marginal and depend on order). $\\delta=0.05$. GPG's natural FDs are discussed in the text. Generated by exp/make\\_tables.py.}"
        "\\label{tab:natural}\n\\setlength{\\tabcolsep}{2.5pt}\\begin{tabular}{llrrcrr}\\toprule\n"
        "data & FD & $g_3^{\\hat r}$ & $g_3^{\\mathrm{raw}}$ & cert. & $U$ & calls \\\\\\midrule\n" + "\n".join(rows) +
        "\n\\bottomrule\\end{tabular}\\end{table}\n")


latex()


# ------------------------------------------------------------------ every scalar quoted in the paper
def paper_numbers():
    L = ["# Numbers quoted in paper/main.tex (generated; do not edit)\n"]
    add = lambda k, v: L.append(f"- **{k}**: {v}")
    # E2 growth
    if (R / "e2_geonames.json").exists():
        e2 = load(R / "e2_geonames.json")
        by = defaultdict(list)
        for r in e2:
            by[r["n_cities"]].append(r)
        lo, hi = min(by), max(by)
        oc = lambda c: np.mean([r["run_calls"] for r in by[c]])
        ca = lambda c: np.mean([r["canon_all"] for r in by[c]])
        add("E2 rows growth", f"{by[hi][0]['rows'] / by[lo][0]['rows']:.0f}x ({by[lo][0]['rows']} -> {by[hi][0]['rows']})")
        add("E2 ours calls growth", f"{oc(hi) / oc(lo):.1f}x ({oc(lo):.0f} -> {oc(hi):.0f})")
        add("E2 canonicalize-all growth", f"{ca(hi) / ca(lo):.1f}x ({ca(lo):.0f} -> {ca(hi):.0f})")
        add("E2 ratio at largest", f"{ca(hi) / oc(hi):.1f}x")
    # E3
    m, f = [], []
    for d in ("geonames", "tax"):
        p = R / f"e3_{d}.json"
        if p.exists():
            e = load(p)
            m += [x["miscover_EB"] for x in e["fds"]]
            f += [x["false_cert_rate"] for x in e["fds"]]
            add(f"E3 {d} setting", f"{e['meta']} reps={e['reps']}")
            for x in e["fds"]:
                if 0.03 < x["g3"] < 0.05:
                    add(f"E3 {d} near-threshold {x['fd']}", f"g3={x['g3']:.4f} E[B]={x['EB']:.4f} cert rate={x['cert_rate']:.3f}")
    if m:
        from math import sqrt
        n_ = load(R / "e3_geonames.json")["reps"]
        k = round(max(m) * n_)
        z = 1.96
        ph = k / n_
        c = (ph + z * z / (2 * n_)) / (1 + z * z / n_)
        h = z * sqrt(ph * (1 - ph) / n_ + z * z / (4 * n_ * n_)) / (1 + z * z / n_)
        add("E3 worst miscoverage Wilson 95% CI", f"{k}/{n_}: [{c - h:.3f}, {c + h:.3f}]")
        add("E3 max miscoverage", f"{max(m):.3f}")
        add("E3 max false-cert rate", f"{max(f):.3f}")
    # B7 at larger m, nu per setting, compute time
    for key in ("geonames_16k", "tax", "ndc"):
        p = R / f"e1_{key}.json"
        if not p.exists():
            continue
        runs = load(p)
        fds = [x for r in runs for x in r["fds"]]
        for mm in (1000, 5000):
            acc = [(next(z for z in x["b7_sample"] if z["m"] == mm)["g3"] <= x.get("delta", 0.05), x["truth"]) for x in fds]
            calls = np.mean([sum(next(z for z in x["b7_sample"] if z["m"] == mm)["calls"] for x in r["fds"]) for r in runs])
            add(f"B7 {key} m={mm}", f"false accepted {sum(a and not t for a, t in acc)}/{sum(not t for a, t in acc)}, "
                                   f"calls/run {calls:.0f}, canon-all {np.mean([r['canon_all'] for r in runs]):.0f}")
        mm_calls = np.mean([sum(next(z for z in x["b7_sample"] if z["m"] == 5000)["calls"] for x in r["fds"]) for r in runs])
        add(f"B7 {key} m=5000 calls / ours (inverse) on the same curated candidates",
            f"{mm_calls:,.0f} / {np.mean([r['run_calls_inverse'] for r in runs]):,.0f} = {mm_calls / np.mean([r['run_calls_inverse'] for r in runs]):.2f}x")
    for p in sorted(R.glob("e1_*.json")):
        runs = load(p)
        if "ann_nubar" not in runs[0]["fds"][0]["ours"]:
            continue
        add(f"nu max (ANN-only) {p.stem}", f"{max(x['ours']['ann_nubar']['nu'] for r in runs for x in r['fds']):.3f}")
    for key in ("geonames_16k", "tax", "ndc", "gpg"):
        p = R / f"e1b_{key}.json"
        if p.exists():
            runs = load(p)
            add(f"E1b seconds {key}", {k: round(float(np.mean([r['sec'][k] for r in runs])), 1) for k in runs[0]["sec"]})
            add(f"E1b planner vs ours calls {key}", f"{np.mean([r['planner_calls_total'] for r in runs]):.0f} vs "
                                                   f"{np.mean([r['ours_calls_total'] for r in runs]):.0f}")
            add(f"E1b ours calls / canon-all {key}",
                f"{np.mean([r['ours_calls_total'] for r in runs]) / np.mean([r['canon_all'] for r in runs]):.2f}x")
            add(f"E1b planner (per-candidate cap) vs ours, change in calls {key}",
                f"{100 * (np.mean([r['planner_calls_total'] for r in runs]) / np.mean([r['ours_calls_total'] for r in runs]) - 1):+.1f}%")
            add(f"E1b planner (per-candidate cap) calls / canon-all {key}",
                f"{np.mean([r['planner_calls_total'] for r in runs]) / np.mean([r['canon_all'] for r in runs]):.2f}x")
            rej = [d["samples"] for r in runs for d in r["ours_detail"].values() if not d["certified"]]
            add(f"E1b rejected candidate-runs stopping at the first batch of 100 samples {key}",
                f"{sum(n <= 100 for n in rej)}/{len(rej)}; median samples {np.median(rej):.0f}")
            add(f"E1b planner resolved / candidates {key}", f"{[r['planner_resolved'] for r in runs]} / {runs[0]['n_cands']}; "
                                                          f"planner F/M {[(r['planner']['false'], r['planner']['missed_true']) for r in runs]}")
    for p in sorted(R.glob("b2_fastrfd_*.json")):
        e = load(p)
        add(f"FastRFD seconds {p.stem}", [(r["t"], round(r["sec"])) for r in e["runs"]])
    _fr = [(p.stem, r["sec"]) for k in ("geonames_16k", "tax", "ndc", "gpg") for p in sorted(R.glob(f"b2_fastrfd_{k}*.json"))
           for r in load(p)["runs"]]
    if _fr:                                                    # paper, timing sentence ("on the same tables")
        add("FastRFD minutes on the evaluated tables (all runs incl. thresholds and fine grids)",
            f"{min(x for _, x in _fr) / 60:.1f}-{max(x for _, x in _fr) / 60:.1f} min over {len(_fr)} runs")
    # LLM
    if (R / "e8_llm.json").exists():
        e = load(R / "e8_llm.json")
        add("E8 n values", e["n_values"])
        for k in ("agreement", "agreement_alnum_normalized", "agreement_layer1_baseline"):
            add(f"E8 {k}", {a: round(b, 3) for a, b in e[k].items()})
        add("E8 sec/call (parallel, loaded)", e["sec_per_call"])
    if (R / "e8_llm_offline.json").exists():
        e = load(R / "e8_llm_offline.json")
        add("E8 offline full-domain agreement", {k: round(v, 3) for k, v in e["agreement_full"].items()})
        add("E8 offline layer1 baseline agreement", {k: round(v, 3) for k, v in e["agreement_layer1_full"].items()})
        add("E8 offline run calls (LLM)", f"{e['run_calls']} vs canonicalize-all {e['canon_all_labeler']}")
        by = defaultdict(list)
        for f in e["fds"]:
            by[f["fd"]].append(f)
        for k, fs in by.items():
            add(f"E8 offline {k}", f"g3_llm={fs[0]['g3_llm']:.3f} g3_code={fs[0]['g3_code']:.3f} certified "
                                   f"{sum(x['certified'] for x in fs)}/{len(fs)} nu_llm={fs[0]['nu_llm']:.4f} "
                                   f"calls={[x['calls'] for x in fs]}")
        add("E8 offline max nu_llm", f"{max(f['nu_llm'] for f in e['fds']):.4f}")
        c = load(R / "e8_llm_canon.json")
        sec = np.array(list(c["sec"].values()))
        add("E8 all canonicalization calls latency", f"n={len(sec)} median {np.median(sec):.1f}s mean {sec.mean():.1f}s "
                                                       f"(varied with server load; single-process measurement below)")
    if (R / "e8_latency.json").exists():
        e = load(R / "e8_latency.json")
        add("E8 single-process latency", f"mean {e['mean']:.1f}s p50 {e['p50']:.1f}s over {e['n']} calls, load {e['loadavg_after']}")
    if (R / "ndc_example.json").exists():
        add("NDC running example", load(R / "ndc_example.json"))
    # E9
    for p in sorted(R.glob("e9_*.json")):
        runs = load(p)
        add(f"E9 {p.stem}", f"seeds={len(runs)} cands={runs[0]['n_cands']} true={runs[0]['n_true']} "
                             f"tane F/M={[ (r['tane']['false'], r['tane']['missed']) for r in runs]} "
                             f"ours F/M={[ (r['ours']['false'], r['ours']['missed']) for r in runs]} "
                             f"calls={[r['calls'] for r in runs]} canon_all={runs[0]['canon_all']}")
        add(f"E9 {p.stem} calls / canon-all (mean over seeds)",
            f"{np.mean([r['calls'] for r in runs]):,.0f} / {np.mean([r['canon_all'] for r in runs]):,.0f} = "
            f"{np.mean([r['calls'] for r in runs]) / np.mean([r['canon_all'] for r in runs]):.2f}x")
    # lower-bound value at the evaluated scale (Thm lower: q >= sqrt((beta-alpha) D (D-1) / m))
    p = R / "e1_geonames_16k.json"
    if p.exists():
        import math
        D = int(np.mean([r["distinct"]["city"] for r in load(p)]))
        m = int(0.05 * D) + 1
        add("Lower bound at GeoNames-16k city domain", f"D={D}, delta=0.05, m={m}, beta-alpha=0.5: "
                                                        f"q >= {math.sqrt(0.5 * D * (D - 1) / m):.0f}")
    shares = []
    for key in ("geonames_16k", "tax", "ndc", "gpg", "geonames_640k"):
        pp = R / f"e1b_{key}.json"
        if pp.exists() and "ours_calls_fwd_inv" in load(pp)[0]:
            rr = load(pp)
            f_, i_ = np.mean([r["ours_calls_fwd_inv"][0] for r in rr]), np.mean([r["ours_calls_fwd_inv"][1] for r in rr])
            shares.append(i_ / (f_ + i_))
    if (R / "e2_geonames.json").exists():
        big = [r for r in load(R / "e2_geonames.json") if r["n_cities"] == 128000 and "run_calls_fwd_inv" in r]
        if big:
            f_, i_ = np.mean([r["run_calls_fwd_inv"][0] for r in big]), np.mean([r["run_calls_fwd_inv"][1] for r in big])
            shares.append(i_ / (f_ + i_))
    if shares:
        add("Inverse share of our calls (cost table rows)", f"{min(shares):.3f}-{max(shares):.3f}")
    for key in ("geonames_16k", "tax", "ndc"):
        pp = R / f"e9_{key}.json"
        if pp.exists():
            rr = load(pp)
            f_, i_ = np.mean([r["calls_fwd_inv"][0] for r in rr]), np.mean([r["calls_fwd_inv"][1] for r in rr])
            shares.append(i_ / (f_ + i_))
    if shares:
        add("Inverse share of our calls (Tables III and VI rows)", f"{min(shares):.3f}-{max(shares):.3f}")
    # code-level constants quoted in the paper
    import inspect
    sys.path[:0] = [str(ROOT), str(ROOT / "pilot")]
    from semfd.certify import certify as _cert
    add("certify sample cap (max_n default)", inspect.signature(_cert).parameters["max_n"].default)
    add("semfd/ lines of Python", sum(len(open(f).read().splitlines()) for f in (ROOT / "semfd").glob("*.py")))
    import p0b_geonames
    add("GeoNames country alias list entries", len(p0b_geonames.COUNTRY_ALIASES))
    add("GeoNames rows per city (make_table default)", inspect.signature(p0b_geonames.make_table).parameters["rows_per_city"].default)
    if (R / "e2_geonames.json").exists():
        add("E2 FDs per run", len(load(R / "e2_geonames.json")[0]["fds"]))
    if (R / "e8_llm.json").exists():
        e8 = load(R / "e8_llm.json")
        add("E8 sample composition", f"{e8['n_values']} names = {e8['n_values'] - 100} spellings of the largest multi-spelling "
                                     f"firms + 100 random (exp/e8_llm_oracle.py --sample 400)")
    if (R / "e9_ndc.json").exists():
        miss = [f["g3"] for r in load(R / "e9_ndc.json") for f in r["fds"] if f["truth"] and not f["certified"]]
        if miss:
            add("E9 NDC missed true FDs: g3 range / max gap to delta", f"{min(miss):.3f}-{max(miss):.3f} / {0.05 - min(miss):.3f}")
    if (R / "e1b_ndc.json").exists():
        add("planner V0 (as run, e1b)", load(R / "e1b_ndc.json")[0]["v_thresh"])
    for key in ("geonames_16k", "tax", "ndc"):
        if (R / f"e1_{key}.json").exists():
            add(f"E1 {key} candidates per run", len(load(R / f"e1_{key}.json")[0]["fds"]))
    if (R / "e8_llm_offline.json").exists():
        e = load(R / "e8_llm_offline.json")
        rc = e["run_calls"]
        add("E8 calls ratio canon-all / ours", f"{e['canon_all_labeler'] / max(rc):.1f}-{e['canon_all_labeler'] / min(rc):.1f}x")
        add("E8 true NDC FDs certified (runs)", sum(f["certified"] for f in e["fds"] if f["g3_llm"] <= 0.05))
    for key in ("geonames_16k", "tax", "ndc"):
        pp = R / f"e1_{key}.json"
        if pp.exists():
            fds = [f for r in load(pp) for f in r["fds"]]
            nat = sum(next(z for z in f["b7_sample"] if z["m"] == 5000)["g3"] <= 0.05 and not f["truth"] and not is_probe(f["fd"]) for f in fds)
            pro = sum(next(z for z in f["b7_sample"] if z["m"] == 5000)["g3"] <= 0.05 and not f["truth"] and is_probe(f["fd"]) for f in fds)
            add(f"B7 s=5000 false accepts natural/probe {key}", f"{nat}/{pro}")
    for key in ("geonames_16k", "tax", "ndc"):
        pp = R / f"e1_{key}.json"
        if pp.exists():
            fds = [f for r in load(pp) for f in r["fds"]]
            b7 = [(next(z for z in f["b7_sample"] if z["m"] == f["ours"]["inverse"]["samples"])["g3"] <= 0.05, f) for f in fds]
            nat_false = [(a_, f) for a_, f in b7 if not f["truth"] and not is_probe(f["fd"])]
            add(f"B7 s=our n: natural false accepted {key}", f"{sum(a_ for a_, _ in nat_false)}/{len(nat_false)}")
    for key in ("geonames_16k", "tax", "ndc"):
        pp = R / f"e1_{key}.json"
        if pp.exists():
            nat = [f for r in load(pp) for f in r["fds"] if not is_probe(f["fd"])]
            add(f"Curated natural {key}: max true g3 / min false g3",
                f"{max(f['g3'] for f in nat if f['truth']):.4f} / {min(f['g3'] for f in nat if not f['truth']):.4f}")
    pp = R / "e1b_ndc.json"
    if pp.exists():
        rr = load(pp)
        near = {k: g for k, g in rr[0]["truth"].items() if not is_probe(k) and 0.03 < g < 0.10}
        add("NDC natural candidates with 0.03<g3<0.10 (certified runs / runs)",
            {k: (round(g, 3), f"{sum(r['ours_detail'][k]['certified'] for r in rr)}/{len(rr)}") for k, g in near.items()})
    for d in ("geonames_16k", "tax", "ndc", "gpg"):
        runs_all = []
        for f in sorted(R.glob(f"b2_fastrfd_{d}*.json")):
            if "_thr" in f.stem:                     # single-threshold runs: reported separately below
                continue
            runs_all += [r for r in load(f)["runs"] if not r.get("timeout")]
        if runs_all:
            pts = sorted((r["t"], r["false"], r["missed_true"]) for r in runs_all)
            add(f"FastRFD all tolerances {d} (t, false, missed)", pts)
            add(f"FastRFD {d}: any tolerance with 0 false and 0 missed?", any(f == 0 and m == 0 for _, f, m in pts))
        for f in sorted(R.glob(f"b2_fastrfd_{d}_thr*.json")):
            e = load(f)
            pts = [(r["t"], r["false"], r["missed_true"]) for r in e["runs"] if not r.get("timeout")]
            add(f"FastRFD {d}, one threshold d={e['thr']} on tolerant columns (t, false, missed)",
                f"{pts}; any tolerance with 0 false and 0 missed: {any(x == 0 and y == 0 for _, x, y in pts)}")
    be = {}
    for key in ("geonames_16k", "tax", "ndc", "gpg", "geonames_640k"):
        p_ = R / f"e1b_{key}.json"
        if p_.exists():
            runs = load(p_)
            fw = np.mean([r["ours_calls_fwd_inv"][0] for r in runs])
            iv = np.mean([r["ours_calls_fwd_inv"][1] for r in runs])
            be[key] = round(float((np.mean([r["canon_all"] for r in runs]) - fw) / iv), 1)
    if (R / "e2_geonames.json").exists():
        e2 = load(R / "e2_geonames.json")
        big = [r for r in e2 if r["n_cities"] == max(x["n_cities"] for x in e2)]
        fw = np.mean([r["run_calls_fwd_inv"][0] for r in big])
        iv = np.mean([r["run_calls_fwd_inv"][1] for r in big])
        be["geonames_640k_8fds"] = round(float((np.mean([r["canon_all"] for r in big]) - fw) / iv), 1)
    if be:
        add("Break-even price of an inverse lookup, in forward calls (ours = canon-all when fwd + price*inv = canon)", be)
    if (R / "e8_llm_offline.json").exists():
        e = load(R / "e8_llm_offline.json")
        sec = e["sec_mean_all_calls"]
        rc = e["run_calls"]
        add("E8 LLM time at the measured mean latency (calls x mean s/call): certification runs / canonicalize-all",
            f"{min(rc) * sec / 3600:.1f}-{max(rc) * sec / 3600:.1f} h / {e['canon_all_labeler'] * sec / 3600:.1f} h "
            f"(mean {sec:.1f} s/call over all canonicalization calls)")
    if (R / "e8_transfer.json").exists():
        tr = load(R / "e8_transfer.json")
        add("E8 oracle transfer (LLM vs labeler-code oracle, labeler attribute)",
            f"disagreement mass {tr['disagreement_mass']:.3f}; max |g3 gap| over labeler FDs {tr['max_abs_g3_gap']:.3f}; "
            f"transferred bounds violated {tr['transferred_bound_violations']}/{tr['n_bounds']}")
        cert = [x["transferred_bound"] for x in tr["rows"] if x["certified"]]
        add("E8 transferred bounds of LLM-certified FDs (min-max; any <= delta 0.05?)",
            f"{min(cert):.3f}-{max(cert):.3f} over {len(cert)} certificates; "
            f"{any(t <= 0.05 for t in cert)}; smallest over all 21: {min(x['transferred_bound'] for x in tr['rows']):.3f}")
    if (R / "e8_tokens.json").exists():
        tk = load(R / "e8_tokens.json")
        ins = [r["input_tokens"] for r in tk["runs"]]
        add("E8 input tokens: certification runs (min-max) / canonicalize-all",
            f"{min(ins) / 1e3:.0f}k-{max(ins) / 1e3:.0f}k / {tk['canon_all']['input_tokens'] / 1e6:.2f}M "
            f"(per call {tk['input_tokens_per_call']['min']}-{tk['input_tokens_per_call']['max']}, "
            f"mean {tk['input_tokens_per_call']['mean']:.0f}; output <= {tk['max_tokens_per_call']}/call; "
            f"calls {[r['calls'] for r in tk['runs']]} = E8 offline run_calls)")
    if (R / "e8_replay_check.json").exists():
        rc = load(R / "e8_replay_check.json")
        add("E8 live replay check", f"{rc['identical_label']}/{rc['n']} labels identical, {rc['identical_raw']}/{rc['n']} raw answers identical")
    if (R / "canon_variant_only.json").exists():
        cv = load(R / "canon_variant_only.json")
        add("Variant-only canonicalize-all vs full", {k: (v["canon_variant_only"], v["canon_all"], v["attrs_seed0"]) for k, v in cv.items()})
    miss = []
    for key in ("geonames_16k", "tax", "ndc"):
        pp = R / f"e1b_{key}.json"
        if pp.exists():
            rr = load(pp)
            miss.append(np.mean([r["b3_tane_raw"]["missed_true"] / r["n_true"] for r in rr]))
    if miss:
        add("Tane missed share of true unary FDs (min-max over datasets)", f"{min(miss):.2f}-{max(miss):.2f}")
    nat_miss = {}
    for key in ("geonames_16k", "tax", "ndc", "geonames_640k"):
        pp = R / f"e1b_{key}.json"
        if pp.exists():
            rr = load(pp)
            per_run = {(sum(not is_probe(x) for x in r["missed_lists"]["b3_raw"]),
                        sum(g <= r["delta"] and not is_probe(f) for f, g in r["truth"].items())) for r in rr}
            nat_miss[key] = (per_run, sorted({x for r in rr for x in r["missed_lists"]["b3_raw"] if not is_probe(x)}))
    nb = {}
    for key in ("geonames_16k", "tax", "ndc"):
        pp = R / f"e1b_{key}.json"
        if pp.exists():
            rr = load(pp)
            o, b9 = np.mean([r["ours_calls_total"] for r in rr]), np.mean([r["b9_calls_total"] for r in rr])
            nb[key] = (round(float(b9)), round(float(o)), round(float(o / b9), 1),
                       sum(not is_probe(x) for r in rr for x in r["false_lists"]["b9"]))
    if nb:
        add("E1b no-audit (B9) vs certificate calls per run, ratio, B9 natural false certifications (over seeds)", nb)
    ao = []
    for pp in sorted(R.glob("e1_geonames_16k*.json")):
        rr = load(pp)
        if "run_calls_alias_only" not in rr[0]:
            continue
        same = all(f["ours"]["inverse"]["certified"] == f["ours"]["alias_only"]["certified"] for r in rr for f in r["fds"])
        ao.append((pp.stem, float(round(np.mean([r["run_calls_inverse"] for r in rr]) / np.mean([r["run_calls_alias_only"] for r in rr]), 2)), same))
    if ao:
        add("E1 GeoNames default (kNN + alias) / alias-only calls per run, decisions identical (per config)", ao)
    if nat_miss:
        add("Tane missed natural true FDs per run (missed, natural true) and which", nat_miss)
        shares = [m / n for k, (pr, _) in nat_miss.items() if k != "geonames_640k" for m, n in pr]
        add("Tane missed share of natural true unary FDs (min-max over datasets, %)", f"{100 * min(shares):g}-{100 * max(shares):g}")
        inj = [m / n for k, (pr, _) in nat_miss.items() if k in ("geonames_16k", "tax") for m, n in pr]
        add("Tane missed share of natural true unary FDs on GeoNames and Tax (injected real aliases, %)",
            f"{100 * min(inj):.0f}-{100 * max(inj):.0f}")
    pp = R / "e1_geonames_16k_rho0.05.json"
    if pp.exists():
        rr = load(pp)
        add("rho=0.05 ours vs canon-all", f"{np.mean([r['run_calls_inverse'] for r in rr]) / np.mean([r['canon_all'] for r in rr]):.2f}x")
        gaps = [0.05 - f["g3"] for r in rr for f in r["fds"] if f["truth"] and not f["ours"]["inverse"]["certified"]]
        if gaps:
            add("rho=0.05 missed true FDs: max gap to delta", f"{max(gaps):.4f}")
    if (R / "e3_ideal_witness.json").exists():
        iw = load(R / "e3_ideal_witness.json")
        for f in iw["fds"]:
            add(f"Ideal-witness diagnostic {f['fd']} (reps={iw['reps']})",
                f"g3={f['g3']:.4f} proxy E[B]={f['proxy']['EB']:.4f} cert={f['proxy']['cert_rate']:.3f} | "
                f"ideal E[B]={f['ideal']['EB']:.4f} cert={f['ideal']['cert_rate']:.3f} falsecert={f['ideal']['false_cert_rate']:.3f}")
    if (R / "e3_refine_geonames.json").exists():
        rf = load(R / "e3_refine_geonames.json")
        for f in rf["fds"]:
            add(f"Self-refining witness {f['fd']} (reps={rf['reps']})",
                f"g3={f['g3']:.4f} cert proxy={f['proxy']['cert_rate']:.3f} refine={f['refine']['cert_rate']:.3f} | "
                f"falsecert proxy={f['proxy']['false_cert_rate']:.3f} refine={f['refine']['false_cert_rate']:.3f} | "
                f"calls proxy={f['proxy']['calls_mean']:.0f} refine={f['refine']['calls_mean']:.0f} "
                f"(refine/proxy - 1 = {f['refine']['calls_mean'] / f['proxy']['calls_mean'] - 1:+.0%})")
    if (R / "e3_refine_geonames.json").exists():
        rf = load(R / "e3_refine_geonames.json")
        rej = [f for f in rf["fds"] if f["refine"]["cert_rate"] < 0.5]
        add("Self-refining witness: call change on mostly rejected FDs (refine/proxy - 1, min-max)",
            f"{min(f['refine']['calls_mean'] / f['proxy']['calls_mean'] - 1 for f in rej):+.0%} to "
            f"{max(f['refine']['calls_mean'] / f['proxy']['calls_mean'] - 1 for f in rej):+.0%} over {len(rej)} FDs")
    for tag in ("small", "large", "small128k"):
        pp = R / f"e10_updates_{tag}.json"
        if not pp.exists():
            continue
        e10 = load(pp)
        runs = e10["runs"]
        last = [r["versions"][-1] for r in runs]
        v0 = [r["versions"][0] for r in runs]
        later = [v for r in runs for v in r["versions"][1:]]
        pol = ("cold", "warm", "maintain", "canon")
        cum = {k: float(np.mean([x["cum_calls"][k] for x in last])) for k in pol}
        init = {k: float(np.mean([x["cum_calls"][k] for x in v0])) for k in pol}
        marg = {k: (cum[k] - init[k]) / max(1, len(runs[0]["versions"]) - 1) for k in pol}
        fc = {k: sum(v["false_cert"][k] for r in runs for v in r["versions"]) for k in ("cold", "warm", "maintain")}
        ms = {k: sum(v["missed_true"][k] for r in runs for v in r["versions"]) for k in ("cold", "warm", "maintain")}
        a_ = e10["args"]
        add(f"E10 updates {tag} ({a_['n_cities']} cities, r0={runs[0]['n0']} rows, +{a_['ins']}/-{a_['dele']} of r0 per version, "
            f"{a_['versions']} versions, {len(runs)} seeds, stop_at={a_['stop_at']})",
            f"initial calls {{{', '.join(f'{k}: {init[k]:,.0f}' for k in pol)}}}; mean per-version calls after v0 "
            f"{{{', '.join(f'{k}: {marg[k]:,.0f}' for k in pol)}}}; cumulative {{{', '.join(f'{k}: {cum[k]:,.0f}' for k in pol)}}}; "
            f"FDs kept at zero calls per later version: mean {np.mean([v['kept_free'] for v in later]):.1f} of "
            f"{runs[0]['candidates']} (max {max(v['kept_free'] for v in later)}); false certifications {fc}; missed true {ms}; "
            f"propagated bounds below truth {sum(v['bound_below_truth'] for r in runs for v in r['versions'])}; "
            f"canon/cold initial {init['canon'] / init['cold']:.2f}x; slack cost maintain/cold initial {init['maintain'] / init['cold']:.2f}x; maintain/canon cumulative {cum['maintain'] / cum['canon']:.2f}x; "
            f"maintain vs warm cumulative {100 * (cum['maintain'] / cum['warm'] - 1):+.1f}%")
    for key in ("geonames_16k", "tax", "ndc"):
        pp = R / f"e11_partial_inverse_{key}.json"
        if not pp.exists():
            continue
        e11 = load(pp)
        ps = sorted({r["p"] for r in e11["runs"]}, reverse=True)
        rows = []
        for p_ in ps:
            rr = [r for r in e11["runs"] if r["p"] == p_]
            rows.append(f"p={p_}: false {sum(len(r['false']) for r in rr)}, missed {sum(len(r['missed']) for r in rr)}, "
                        f"calls {np.mean([r['calls'] for r in rr]):,.0f}, max nu {max(r['nu_max'] for r in rr):.3f}, "
                        f"candidates with nu>0.01 {np.mean([r['nu_over_0.01'] for r in rr]):.1f}")
        add(f"E11 partial inverse {key} ({len({r['seed'] for r in e11['runs']})} seeds; totals over seeds)", "; ".join(rows))
        _c1 = np.mean([r["calls"] for r in e11["runs"] if r["p"] == 1.0])
        add(f"E11 partial inverse {key}: calls / complete inverse (p<1)",
            ", ".join(f"p={p_}: {np.mean([r['calls'] for r in e11['runs'] if r['p'] == p_]) / _c1:.2f}x" for p_ in ps if p_ != 1.0))
        add(f"E11 missed true FDs {key} (seed, p, fd)", [(r["seed"], r["p"], m) for r in e11["runs"] for m in r["missed"]])
        nat = [f for f in e11["audit_split"] if not f["probe"]]
        fired = [f for f in nat if f["mass_ii_only"] > 0]
        add(f"E11 audit split {key} (natural candidates with tolerant LHS, seed 0)",
            f"{len(fired)} of {len(nat)} have mass caught only by condition (ii) > 0; max {max((f['mass_ii_only'] for f in nat), default=0):.4f}"
            + "; top: " + ", ".join(f"{f['fd']} g3={f['g3']:.3f} str={f['g3_string']:.3f} ii={f['mass_ii_only']:.4f}"
                                    for f in sorted(nat, key=lambda f: -f["mass_ii_only"])[:3]))
        under = [f for f in nat if f["mass_i"] < f["g3"]]
        add(f"E11 no-audit mean (condition (i) mass) below oracle g3 {key} (natural, tolerant LHS, seed 0)",
            f"{len(under)} of {len(nat)}; max shortfall {max((f['g3'] - f['mass_i'] for f in under), default=0):.3f}; "
            f"true FDs among them {sum(f['g3'] <= 0.05 for f in under)}; crossing delta=0.05 {sum(f['mass_i'] <= 0.05 < f['g3'] for f in under)}")
    for key in ("geonames_16k", "tax"):
        pp, pf = R / f"e11_partial_inverse_{key}_official.json", R / f"e11_partial_inverse_{key}.json"
        if pp.exists() and pf.exists():
            e, full = load(pp), [r for r in load(pf)["runs"] if r["p"] == 1.0]
            cov = {x: (min(c[x] for c in e["coverage"]), max(c[x] for c in e["coverage"])) for x in e["coverage"][0] if x != "seed"}
            add(f"E11 registered-names inverse {key} ({len(e['runs'])} seeds)",
                f"false {sum(len(r['false']) for r in e['runs'])}, missed {sum(len(r['missed']) for r in e['runs'])}; "
                f"calls {np.mean([r['calls'] for r in e['runs']]):,.0f} vs complete inverse {np.mean([r['calls'] for r in full]):,.0f}; "
                f"max nu {max(r['nu_max'] for r in e['runs']):.3f}; candidates with nu>0.01 {np.mean([r['nu_over_0.01'] for r in e['runs']]):.1f}; "
                "tuple mass covered by registered names " + ", ".join(f"{x} {lo:.2f}-{hi:.2f}" for x, (lo, hi) in cov.items()))
    pp, pf = R / "e11_partial_inverse_geonames_16k_preferred.json", R / "e11_partial_inverse_geonames_16k.json"
    if pp.exists() and pf.exists():
        e, full = load(pp), [r for r in load(pf)["runs"] if r["p"] == 1.0]
        miss = {x: (min(c["alias_tuples_missing"][x] for c in e["coverage"]), max(c["alias_tuples_missing"][x] for c in e["coverage"]))
                for x in e["coverage"][0]["alias_tuples_missing"]}
        add(f"E11 preferred-names inverse geonames_16k ({len(e['runs'])} seeds; registry = ASCII name + alternateNamesV2 preferred/English, "
            "not historic/colloquial; injection unchanged)",
            f"false {sum(len(r['false']) for r in e['runs'])}, missed {sum(len(r['missed']) for r in e['runs'])}; "
            f"calls {np.mean([r['calls'] for r in e['runs']]):,.0f} vs complete inverse {np.mean([r['calls'] for r in full]):,.0f}; "
            f"max nu {max(r['nu_max'] for r in e['runs']):.3f}; injected alias tuples missing from the registry "
            + ", ".join(f"{x} {lo:.2f}-{hi:.2f}" for x, (lo, hi) in miss.items()))
    pp, pe = R / "e7_geonames.json", R / "e1_geonames_16k.json"
    if pp.exists() and pe.exists():
        e7, e1 = load(pp), load(pe)
        ca = next(r["canon_all"] for r in e1 if r["seed"] == 0)        # E7 uses the seed-0 table
        c5 = np.mean([r["calls"] for r in e7["runs"] if r["p"] == 0.05])
        add("E7 GeoNames calls per run at 5% noise vs canonicalize-all of the same (seed-0) table", f"{c5:,.0f} vs {ca:,}")
    pp = R / "e1b_gpg.json"
    if pp.exists():
        rr = load(pp)
        tr = rr[0]["truth"]
        if (R / "e17_gpg_registry.json").exists() and "homonym_rows_dropped" in load(R / "e17_gpg_registry.json"):
            add("GPG rows dropped as homonyms (a name with several company numbers)", load(R / "e17_gpg_registry.json")["homonym_rows_dropped"])
        add(f"E1b gpg (UK gender pay gap 2017-2025, {rr[0]['rows']:,} rows; {rr[0]['n_cands']} candidates, {rr[0]['n_true']} true; {len(rr)} seeds)",
            f"ours false {sum(r['ours']['false'] for r in rr)}, missed {sum(r['ours']['missed_true'] for r in rr)}, calls/run "
            f"{np.mean([r['ours_calls_total'] for r in rr]):,.0f} ({np.mean([r['ours_calls_fwd_inv'][0] for r in rr]):,.0f} + "
            f"{np.mean([r['ours_calls_fwd_inv'][1] for r in rr]):,.0f}) vs canonicalize-all {rr[0]['canon_all']:,}; "
            f"TANE raw false/missed per run {rr[0]['b3_tane_raw']['false']}/{rr[0]['b3_tane_raw']['missed_true']}; "
            f"no audit false {sum(r['b9_noaudit']['false'] for r in rr)}, calls/run {np.mean([r['b9_calls_total'] for r in rr]):,.0f}; "
            f"true FDs and g3: {sorted((k, round(g, 4)) for k, g in tr.items() if g <= 0.05)}; false FDs below 0.1: "
            f"{sorted((k, round(g, 4)) for k, g in tr.items() if 0.05 < g < 0.1)}")
        miss = sorted({x for r in rr for x in r["missed_lists"]["ours"]})
        add("E1b gpg certificate misses: U at the cap, calls on that FD per run, share of run calls",
            {m: (f"U {min(r['ours_detail'][m]['ub'] for r in rr):.3f}-{max(r['ours_detail'][m]['ub'] for r in rr):.3f}",
                 f"samples {max(r['ours_detail'][m]['samples'] for r in rr)}",
                 f"calls {min(r['ours_detail'][m]['calls'] for r in rr):,}-{max(r['ours_detail'][m]['calls'] for r in rr):,}",
                 f"{min(r['ours_detail'][m]['calls'] / r['ours_calls_total'] for r in rr):.2f}-{max(r['ours_detail'][m]['calls'] / r['ours_calls_total'] for r in rr):.2f}")
             for m in miss})
        add("E1b gpg audited mean of name->sic (seeds) and cn->sic certified runs",
            f"mean {min(r['ours_detail']['name->sic']['mean'] for r in rr):.4f}-{max(r['ours_detail']['name->sic']['mean'] for r in rr):.4f}; "
            f"cn->sic certified {sum(r['ours_detail']['cn->sic']['certified'] for r in rr)}/{len(rr)}, empid->sic certified "
            f"{sum(r['ours_detail']['empid->sic']['certified'] for r in rr)}/{len(rr)}")
        add("E1b gpg TANE raw / normalized misses", f"{sorted({x for r in rr for x in r['missed_lists']['b3_raw']})} / normalized missed {rr[0]['b3_tane_norm']['missed_true']}")
    pp = R / "e17_gpg_registry.json"
    if pp.exists():
        g = load(pp)
        add("E17 gpg natural aliases and Companies House register",
            f"{g['multi_spelling_companies']:,} of {g['companies']:,} companies with several spellings ({g['multi_spelling_rows']:,} of "
            f"{g['rows']:,} rows); {g['spellings_without_proxy_edge_multi']:,} of their {g['spellings_multi']:,} spellings have no proxy "
            f"edge to another spelling of the company ({100 * g['tuple_mass_without_proxy_edge']:.1f}% of tuples); register lists "
            f"{100 * g['share_spellings_registered_multi']:.0f}% of those companies' spellings and covers "
            f"{100 * g['tuple_mass_registered']:.1f}% of tuples; {g['companies_in_register']:,} companies found in the register")
    for tag in ("", "_companieshouse"):
        pp = R / f"e11_partial_inverse_gpg{tag}.json"
        if pp.exists():
            e = load(pp)
            ps = sorted({r["p"] for r in e["runs"]}, key=str, reverse=True)
            add(f"E11 gpg{tag or ' (random omission)'} ({len({r['seed'] for r in e['runs']})} seeds)",
                "; ".join(f"p={p_}: false {sum(len(r['false']) for r in e['runs'] if r['p'] == p_)}, missed "
                          f"{sum(len(r['missed']) for r in e['runs'] if r['p'] == p_)}, calls "
                          f"{np.mean([r['calls'] for r in e['runs'] if r['p'] == p_]):,.0f}, max nu "
                          f"{max(r['nu_max'] for r in e['runs'] if r['p'] == p_):.3f}" for p_ in ps)
                + ("; registry coverage of tuples " + ", ".join(f"{c['name']:.3f}" for c in e.get("coverage", [])) if e.get("coverage") else ""))
    pp = R / "e16_gleif.json"
    if pp.exists():
        g = load(pp)
        lo = g["lei_oracle"]
        add("E16 GLEIF as alias registry for NDC labeler names (exact alphanumeric match, ambiguous keys dropped)",
            f"{g['values_matching_one_lei']:,} of {g['labeler_values']:,} values match one LEI ({g['values_ambiguous']} ambiguous); "
            f"{g['entities_linked']:,} of {g['entities']:,} entities linked ({100 * g['tuple_mass_linked_entities']:.1f}% of tuples); "
            f"spellings returned cover {100 * g['tuple_mass_returned']:.1f}% of tuples; linked entities with several spellings: "
            f"{g['multi_spelling_linked_entities']}, of whose spellings GLEIF returns {100 * g['spellings_returned_share_multi']:.0f}% on average")
        add("E16 LEI as an independent oracle for labcode -> labeler (tuples whose spelling matches one LEI)",
            f"{lo['tuples']:,} tuples ({100 * lo['tuple_share']:.1f}%); g3 labcode->LEI {lo['g3_labcode_to_lei']:.4f}, "
            f"code-graph oracle {lo['g3_labcode_to_codegraph']:.4f}, raw strings {lo['g3_labcode_to_string']:.4f}")
    pp, pf = R / "e11_partial_inverse_ndc_gleif.json", R / "e11_partial_inverse_ndc.json"
    if pp.exists() and pf.exists():
        e, full = load(pp), [r for r in load(pf)["runs"] if r["p"] == 1.0]
        add(f"E11 GLEIF inverse ndc ({len(e['runs'])} seeds, all unary candidates)",
            f"false {sum(len(r['false']) for r in e['runs'])}, missed {sum(len(r['missed']) for r in e['runs'])} "
            f"{[(r['seed'], m) for r in e['runs'] for m in r['missed']]}; calls {np.mean([r['calls'] for r in e['runs']]):,.0f} "
            f"vs complete inverse {np.mean([r['calls'] for r in full]):,.0f}; max nu {max(r['nu_max'] for r in e['runs']):.3f}; "
            f"candidates with nu>0.01 {np.mean([r['nu_over_0.01'] for r in e['runs']]):.1f}")
    from scipy.stats import beta as _beta                # 20-seed repeats of the incomplete-inverse runs (review E2)
    for name, f in (("GeoNames registered names", "geonames_16k_s20_official"), ("GeoNames preferred names", "geonames_16k_s20_preferred"),
                    ("Tax registered names", "tax_s20_official"), ("NDC GLEIF", "ndc_s20_gleif"),
                    ("GPG Companies House", "gpg_s20_companieshouse")):
        pp = R / f"e11_partial_inverse_{f}.json"
        if pp.exists():
            rr = load(pp)["runs"]
            n, k = len(rr), sum(bool(r["false"]) for r in rr)
            ub = 1 - 0.05 ** (1 / n) if k == 0 else float(_beta.ppf(0.95, k + 1, n - k))
            add(f"E11 repeated incomplete inverse, {name} ({n} seeds; seeds 0-2 are the runs above)",
                f"runs with a false certification {k}/{n} (false FDs {sum(len(r['false']) for r in rr)}); missed {sum(len(r['missed']) for r in rr)}; "
                f"max nu {max(r['nu_max'] for r in rr):.3f}; exact one-sided 95% upper bound on the per-run false-certification probability {ub:.3f}; "
                f"calls/run {np.mean([r['calls'] for r in rr]):,.0f}")
    _sc = {suf: np.mean([r["run_calls_inverse"] for r in load(R / f"e1_geonames_16k{suf}.json")])
           for suf in ("", "_edit") if (R / f"e1_geonames_16k{suf}.json").exists()}
    if len(_sc) == 2:                                          # paper, "Proxies and the miss mass" (hybrid rationale)
        add("E1 GeoNames TF-IDF nbrs + edit score vs hybrid: calls/run (ratio)",
            f"{_sc['_edit']:,.0f} vs {_sc['']:,.0f} ({_sc['_edit'] / _sc['']:.2f}x)")
    for key in ("geonames_16k", "tax", "ndc", "gpg"):          # E18 variants (pre-registered, literature/prereg_e18_2026-10-23.md)
        pp = R / f"e18_variants_{key}.json"
        if not pp.exists():
            continue
        e18 = load(pp)
        runs = e18["runs"]
        names = list(runs[0]["variants"])
        plain = [r["variants"]["plain"]["calls"] for r in runs]
        for v in names:
            rr = [r["variants"][v] for r in runs if v in r["variants"]]
            from collections import Counter as _C
            miss = _C(m for x in rr for m in x["missed"])
            line = (f"false {sum(len(x['false']) for x in rr)}, missed {sum(len(x['missed']) for x in rr)} {dict(miss)}; "
                    f"calls/run {np.mean([x['calls'] for x in rr]):,.0f} (fwd {np.mean([x['calls_fwd_inv'][0] for x in rr]):,.0f}, "
                    f"inv {np.mean([x['calls_fwd_inv'][1] for x in rr]):,.0f}); vs plain {np.mean([x['calls'] / p for x, p in zip(rr, plain)]):.3f}x; "
                    f"canon-all {np.mean([x['canon_all'] for x in rr]):,.0f}; decision sec/run {np.mean([x['sec'] for x in rr]):.1f}; proxy sec {np.mean([x['proxy_sec'] for x in rr]):.1f}")
            if rr[0]["gamma"] is not None:
                fb = [x["fallback"] for x in rr]
                line += (f"; fallback in {sum(f is not None for f in fb)}/{len(rr)} runs"
                         + (f" (at candidate {[f['at_candidate'] for f in fb if f]} of {runs[0]['n_cands']})" if any(fb) else "")
                         + f"; within (1+gamma)C_full + overshoot in all runs: {all(x['within_bound'] for x in rr)}; "
                         f"max overshoot {max((x['overshoot'] or 0) for x in rr):.0f}; calls/C_full max {max(x['calls'] / x['canon_all'] for x in rr):.3f}, "
                         f"mean {np.mean([x['calls'] / x['canon_all'] for x in rr]):.3f}"
                         + (f"; first exactly decided candidate (1-based) {[f['at_candidate'] + 1 for f in fb if f]}" if any(fb) else ""))
            add(f"E18 {key} {v} ({len(rr)} seeds, all unary candidates, complete inverse)", line)
        add(f"E18 {key} peak RSS of the run (MB, one process, all variants)", f"{e18['peak_rss_mb']:.0f}")
    e18s = {k: load(R / f"e18_variants_{k}.json") for k in ("geonames_16k", "tax", "ndc", "gpg") if (R / f"e18_variants_{k}.json").exists()}
    if e18s:                                                   # E18 ranges over the four datasets (paired with plain per run)
        def _rat(v, f):
            return [np.mean([f(r["variants"][v]) / f(r["variants"]["plain"]) for r in e["runs"]]) for e in e18s.values()]
        for v in next(iter(e18s.values()))["runs"][0]["variants"]:
            if v == "plain":
                continue
            c, t = _rat(v, lambda x: x["calls"]), _rat(v, lambda x: x["sec"])
            add(f"E18 range over {len(e18s)} datasets: {v} vs plain",
                f"calls {min(c):.3f}-{max(c):.3f}x (i.e. {100 * (1 - max(c)):.0f}-{100 * (1 - min(c)):.0f}% fewer if positive); "
                f"decision time {min(t):.1f}-{max(t):.1f}x; per dataset calls " + ", ".join(f"{k} {x:.3f}" for k, x in zip(e18s, c)))
        add("E18 peak RSS range (MB, one process per dataset, all variants)",
            f"{min(e['peak_rss_mb'] for e in e18s.values()):.0f}-{max(e['peak_rss_mb'] for e in e18s.values()):.0f}")
    if (R / "e18_diag_gpg.json").exists():                  # MODIFY.md H1/H2: exact witness means (diagnostic only)
        dg = load(R / "e18_diag_gpg.json")["rows"]
        for v in ("plain", "refine", "refine_warm"):
            rr = [r for r in dg if r["variant"] == v]
            add(f"E18 diagnostic GPG name->sic {v} ({len(rr)} seeds)",
                f"g3 {rr[0]['g3']:.4f}; exact mean of initial witness {np.mean([r['mu_initial'] for r in rr]):.4f}"
                + (f"; of final refined witness {min(r['mu_final'] for r in rr):.4f}-{max(r['mu_final'] for r in rr):.4f}"
                   if "mu_final" in rr[0] else "")
                + f"; running mean of B {min(r['mean_B'] for r in rr):.4f}-{max(r['mean_B'] for r in rr):.4f}; "
                f"U {min(r['ub'] for r in rr):.4f}-{max(r['ub'] for r in rr):.4f}; certified {sum(r['certified'] for r in rr)}/{len(rr)}; "
                f"samples {sorted({r['samples'] for r in rr})}; calls on this candidate {min(r['calls'] for r in rr):,}-{max(r['calls'] for r in rr):,}")
    if (R / "e18_diag_sim.json").exists():
        ds_ = load(R / "e18_diag_sim.json")
        for k in ("initial_witness", "refine_running_mean", "refine_final_witness_frozen", "refine_warm_final_witness_frozen"):
            x = ds_[k]
            add(f"E18 diagnostic simulation, fresh i.i.d. samples, mean of {k.replace('_', ' ')}",
                f"mu {x['mu']:.4f}: certified within 20,000 samples in {100 * x['p_certify_within_cap']:.0f}% of 500 runs"
                + (f", median {x['median_samples']:,.0f} samples" if x["median_samples"] else ""))
    if (R / "e20_scaling.json").exists():                    # E20 (pre-registered): N, D, |C| varied separately
        e20 = load(R / "e20_scaling.json")
        tags = list(dict.fromkeys(r["tag"] for r in e20))
        for t in tags:
            rr = [r for r in e20 if r["tag"] == t]
            tf = [f for r in rr for f in r["fds"] if f["g3"] <= 0.05]
            add(f"E20 {t} ({len(rr)} seeds)",
                f"rows {rr[0]['rows']:,}; distinct city {', '.join(f'{r['distinct']['city']:,}' for r in rr)}; candidates {rr[0]['n_cands']}; "
                f"calls {', '.join(f'{r['calls']:,}' for r in rr)} (canon-all {', '.join(f'{r['canon_all']:,}' for r in rr)}; "
                f"ratio {', '.join(f'{r['calls'] / r['canon_all']:.2f}' for r in rr)}); samples {', '.join(f'{r['samples']:,}' for r in rr)}; "
                f"false {sum(len(r['false']) for r in rr)}, missed {sum(len(r['missed']) for r in rr)}; "
                f"samples per true FD {min(f['samples'] for f in tf)}-{max(f['samples'] for f in tf)}; "
                f"false-FD g3 {min(f['g3'] for r in rr for f in r['fds'] if f['g3'] > 0.05):.3f}-"
                f"{max(f['g3'] for r in rr for f in r['fds'] if 0.05 < f['g3'] < 0.2):.3f} (probes below 0.2); "
                f"max alias class (city) {max(r['alias_class']['city']['max'] for r in rr)}")
    e19c = [load(R / f"e19_certify_s{s}.json") for s in range(3) if (R / f"e19_certify_s{s}.json").exists()]
    if (R / "e19_resolve.json").exists() and e19c:          # E19 (pre-registered): live LLM, end to end
        rv = load(R / "e19_resolve.json")
        exact = {f["fd"]: f["certified"] for f in rv["fds"]}
        add("E19 resolve arm (live LLM, one process)",
            f"wall {rv['wall_sec'] / 60:.1f} min (model load {rv['model_load_sec']:.0f} s, separate); LLM calls {rv['llm_calls']:,}; "
            f"summed call latency {rv['llm_sec_sum'] / 60:.1f} min, median {rv['llm_sec_p50']:.2f} s; exact decisions "
            f"{sum(exact.values())} true of {len(exact)}; load avg {min(x[1] for x in rv['loadavg_1m']):.0f}-{max(x[1] for x in rv['loadavg_1m']):.0f}")
        e8c = load(R / "e8_llm_canon.json")["out"] if (R / "e8_llm_canon.json").exists() else {}
        e8t = load(R / "e8_tokens.json")["runs"] if (R / "e8_tokens.json").exists() else []
        for c in e19c:
            dec = {f["fd"]: f["certified"] for f in c["fds"]}
            fp = sum(dec[k] and not exact[k] for k in dec)
            fn = sum(exact[k] and not dec[k] for k in dec)
            same = sum(e8c.get(v) == o for v, o in c["answers"].items())
            rep = next((r["calls"] for r in e8t if r["seed"] == c["seed"]), None)
            norm_label = lambda x: re.sub(r"[^a-z0-9]", "", x.lower())
            disagreements = sum(norm_label(o) != norm_label(rv["answers"][v]) for v, o in c["answers"].items())
            add(f"E19 seed {c['seed']} normalized-label differences vs resolve",
                f"{disagreements}/{len(c['answers'])}; oracle mapping differs across arms")
            add(f"E19 certify arm seed {c['seed']} (live LLM, neighbour-only, declared nu_bar 0.01)",
                f"wall {c['wall_sec'] / 60:.1f} min (proxy {c['phases']['proxy_sec']:.0f} s); LLM calls {c['llm_calls']:,} "
                f"(E8 replay {rep}); summed call latency {c['llm_sec_sum'] / 60:.1f} min, median {c['llm_sec_p50']:.2f} s; "
                f"false certifications vs resolve arm {fp}, true FDs not certified {fn}; answers identical to the E8 cache "
                f"{same}/{len(c['answers'])}; load avg {min(x[1] for x in c['loadavg_1m']):.0f}-{max(x[1] for x in c['loadavg_1m']):.0f}")
        w = [c["wall_sec"] for c in e19c]
        add("E19 resolve wall / certify wall (mean over seeds)",
            f"{rv['wall_sec'] / np.mean(w):.2f}x (per seed {min(rv['wall_sec'] / x for x in w):.2f}-{max(rv['wall_sec'] / x for x in w):.2f}x); "
            f"summed latency {rv['llm_sec_sum'] / np.mean([c['llm_sec_sum'] for c in e19c]):.2f}x; "
            f"calls {rv['llm_calls'] / np.mean([c['llm_calls'] for c in e19c]):.2f}x")
    if (R / "e19_proxy_cold.json").exists():
        pc = load(R / "e19_proxy_cold.json")
        add("E19 NDC proxy-index build, empty vs cached embedding cache (s)",
            f"cold {min(pc['cold_sec']):.0f}-{max(pc['cold_sec']):.0f}, cached {min(pc['cached_sec']):.1f}-{max(pc['cached_sec']):.1f}")
    if (R / "e21_natural_audit.json").exists():              # E21 (pre-registered): audit on natural data
        e21 = load(R / "e21_natural_audit.json")
        rows = [r for d in e21["datasets"].values() for r in d["candidates"]]
        sizes = ", ".join(f"{k} {len(d['candidates'])}" for k, d in e21["datasets"].items())
        add(f"E21 natural candidates ({sizes})",
            f"audit-decisive (mu_i < delta <= mu) {sum(r['audit_decisive'] for r in rows)}; raw strings hide a violation "
            f"(g3_raw <= delta < g3_oracle) {sum(r['raw_hides_violation'] for r in rows)}; audit mass mu - mu_i "
            f"{min(r['mu'] - r['mu_i'] for r in rows):.3f}-{max(r['mu'] - r['mu_i'] for r in rows):.3f}; g3_oracle - g3_raw "
            f"{min(r['g3_oracle'] - r['g3_raw'] for r in rows):.3f}-{max(r['g3_oracle'] - r['g3_raw'] for r in rows):.3f}; "
            f"true (g3_oracle <= delta) {sum(r['g3_oracle'] <= e21['delta'] for r in rows)}")
    if (R / "e1b_ndc.json").exists():                       # the NDC probe missed in E11 (paper, "Incomplete inverse")
        add("NDC probe labeler_e2->ptype: oracle g3 per seed (E1b truth)",
            ", ".join(f"{r['truth']['labeler_e2->ptype']:.4f}" for r in load(R / "e1b_ndc.json")))
    add("Exact one-sided 95% upper bound on a per-run failure probability after 0 failures in 3 runs", f"{1 - 0.05 ** (1 / 3):.3f}")
    for key in ("geonames_16k", "tax", "ndc"):
        for mode, base_file, base_key in (("unary", f"e1b_{key}.json", "ours_calls_total"), ("pairs", f"e9_{key}.json", "calls")):
            pp = R / f"e13_planner_{key}_{mode}.json"
            if pp.exists() and (R / base_file).exists():
                rr, bb = load(pp), load(R / base_file)
                pc, bc = np.mean([r["calls"] for r in rr]), np.mean([r[base_key] for r in bb])
                per = [r["calls"] / next(q[base_key] for q in bb if q["seed"] == r["seed"]) for r in rr]
                add(f"E13 run-level planner {key} {mode} ({len(rr)} seeds)",
                    f"calls {pc:,.0f} vs certificate only {bc:,.0f} ({pc / bc:.2f}x; per seed {min(per):.2f}-{max(per):.2f}x), canon-all {np.mean([r['canon_all'] for r in rr]):,.0f}; "
                    f"resolved candidates {[r['resolved_cands'] for r in rr]} of {rr[0]['n_cands']}; resolved oracles {rr[0]['resolved_oracles']}; "
                    f"false {sum(len(r['false']) for r in rr)}, missed {sum(len(r['missed']) for r in rr)} (certificate only: "
                    + (f"false {sum(r['ours']['false'] for r in bb)}, missed {sum(r['ours']['missed'] if mode == 'pairs' else r['ours']['missed_true'] for r in bb)})"))
    pp = R / "e2_geonames.json"
    if pp.exists():
        rr = load(pp)
        by = {}
        for r in rr:
            by.setdefault(r["n_cities"], []).append((sum(f["ours"]["samples"] for f in r["fds"]), r["run_calls"]))
        add("E2 samples per run (sum over FDs) and calls per sample, by cities",
            "; ".join(f"{k}: {np.mean([a for a, _ in v]):,.0f} samples, {np.mean([c / a for a, c in v]):.2f} calls/sample"
                      for k, v in sorted(by.items())))
    pp = R / "e14_llm_tax_city.json"
    if pp.exists():
        e = load(pp)
        ag, l1 = e["agreement"], e["agreement_layer1_baseline"]
        add(f"E14 LLM oracle on Tax city ({e['rows']:,} rows, {e['n_values']:,} values, {e['n_entities']:,} entities)",
            f"B-cubed F1 {ag['bcubed_f1']:.2f} (Layer-1 strings {l1['bcubed_f1']:.2f}); pair precision {ag['pair_precision']:.2f}, "
            f"pair recall {ag['pair_recall']:.2f}; LLM entities {ag['llm_entities']:,}; mean s/call {e['sec_per_call']['mean']:.2f}")
        rc = e["run_city_calls"]
        add("E14 city calls per run vs canonicalize-all",
            f"{min(rc):,}-{max(rc):,} vs {e['canon_all_city']:,} ({e['canon_all_city'] / max(rc):.1f}-{e['canon_all_city'] / min(rc):.1f}x)")
        fds = sorted({f["fd"] for f in e["fds"]})
        for fd in fds:
            rr = [f for f in e["fds"] if f["fd"] == fd]
            add(f"E14 {fd}", f"certified {sum(f['certified'] for f in rr)}/{len(rr)}; g3 LLM {rr[0]['g3_llm']:.3f}, "
                f"g3 Tax oracle {rr[0]['g3_code']:.3f}; nu under LLM {max(f['nu_llm'] for f in rr):.4f}; "
                f"U {min(f['ub'] for f in rr):.3f}-{max(f['ub'] for f in rr):.3f}")
        tl = [f for f in e["fds"] if f["g3_llm"] <= 0.05]
        fl = [f for f in e["fds"] if f["g3_llm"] > 0.05]
        add("E14 decisions vs LLM truth (over seeds)",
            f"true certified {sum(f['certified'] for f in tl)}/{len(tl)}, false certified {sum(f['certified'] for f in fl)}/{len(fl)}; "
            f"max nu {max(f['nu_llm'] for f in e['fds']):.4f} vs declared 0.01")
    pp = R / "e15_slack.json"
    if pp.exists():
        rows = load(pp)
        ns = [r for r in rows if r["dataset"] == "gpg" and r["fd"] == "name->sic"]
        if ns:
            add("E15 gpg name->sic: mu - g3 / eps_pi + eps_rep", f"{ns[0]['mu'] - ns[0]['g3']:.4f} / {ns[0]['eps_pi'] + ns[0]['eps_rep']:.4f}")
        add("E15 witness-slack bound g3 <= mu <= g3 + eps_pi + eps_rep (E1 lists, tolerant LHS, seed 0)",
            f"holds on {sum(r['holds'] for r in rows)} of {len(rows)} candidates")
        for d in dict.fromkeys(r["dataset"] for r in rows):
            tn = [r for r in rows if r["dataset"] == d and not r["probe"] and r["g3"] <= 0.05]
            if tn:
                add(f"E15 true natural FDs {d}: max mu-g3 / max eps_pi+eps_rep",
                    f"{max(r['mu'] - r['g3'] for r in tn):.3f} / {max(r['eps_pi'] + r['eps_rep'] for r in tn):.3f} "
                    f"({', '.join(r['fd'] for r in tn)})")
    pp = R / "e12_hidden_alias.json"
    if pp.exists():
        e12 = load(pp)
        rr, cf = e12["runs"], e12["config"]
        def ours(v, key):
            return [r["ours"][v][key] for r in rr]
        add(f"E12 hidden aliases (GeoNames {cf['n_cities']} cities, rho={cf['rho']}, {len(rr)} seeds)",
            f"injected mass {min(r['injected_mass'] for r in rr):.3f}-{max(r['injected_mass'] for r in rr):.3f} "
            f"(available {min(r['hidden_alias_mass_available'] for r in rr):.3f}-{max(r['hidden_alias_mass_available'] for r in rr):.3f}); "
            f"g3 {min(r['g3'] for r in rr):.3f}-{max(r['g3'] for r in rr):.3f} (false at delta={cf['delta']}: {sum(not r['truth'] for r in rr)}/{len(rr)}); "
            f"string g3 {min(r['g3_string'] for r in rr):.3f}-{max(r['g3_string'] for r in rr):.3f}; "
            f"neighbor-only (nu_bar={cf['nu_bar']}) certified {sum(ours('ann_nubar', 'certified'))}/{len(rr)}, "
            f"U {min(ours('ann_nubar', 'ub')):.3f}-{max(ours('ann_nubar', 'ub')):.3f}, measured nu {min(ours('ann_nubar', 'nu')):.3f}-{max(ours('ann_nubar', 'nu')):.3f}, "
            f"calls {min(ours('ann_nubar', 'calls'))}-{max(ours('ann_nubar', 'calls'))}, "
            f"audited sample mean {min(ours('ann_nubar', 'mean')):.3f}-{max(ours('ann_nubar', 'mean')):.3f}; "
            f"inverse certified {sum(ours('inverse', 'certified'))}/{len(rr)}, U {min(ours('inverse', 'ub')):.3f}-{max(ours('inverse', 'ub')):.3f}, "
            f"audited sample mean {min(ours('inverse', 'mean')):.3f}-{max(ours('inverse', 'mean')):.3f}, "
            f"calls {min(ours('inverse', 'calls'))}-{max(ours('inverse', 'calls'))}")
    pp = R / "e1b_geonames_640k.json"
    if pp.exists():
        rr = load(pp)
        rat = [r["canon_all"] / r["ours_calls_total"] for r in rr]
        add(f"E1b all unary candidates at {rr[0]['rows']:,} rows ({rr[0]['n_cands']} candidates, {len(rr)} seeds)",
            f"ours {np.mean([r['ours_calls_total'] for r in rr]):,.0f} (fwd+inv {np.mean([r['ours_calls_fwd_inv'][0] for r in rr]):,.0f}+"
            f"{np.mean([r['ours_calls_fwd_inv'][1] for r in rr]):,.0f}) vs canon-all {np.mean([r['canon_all'] for r in rr]):,.0f}: "
            f"{np.mean(rat):.1f}x ({min(rat):.1f}-{max(rat):.1f}); false {[r['ours']['false'] for r in rr]}, "
            f"missed {[r['ours']['missed_true'] for r in rr]}; TANE raw false/missed {[(r['b3_tane_raw']['false'], r['b3_tane_raw']['missed_true']) for r in rr]}")
    if (R / "mb_probe.json").exists():
        add("MusicBrainz probe (not used)", load(R / "mb_probe.json"))
    (R / "PAPER_NUMBERS.md").write_text("\n".join(L) + "\n")


def latex_e9():
    rows = []
    for key, nice in (("geonames_16k", "GeoNames"), ("tax", "Tax"), ("ndc", "NDC")):
        p = R / f"e9_{key}.json"
        if not p.exists():
            continue
        runs = load(p)
        mf = lambda k, w: np.mean([r[k][w] for r in runs])
        oc, ca = np.mean([r["calls"] for r in runs]), np.mean([r["canon_all"] for r in runs])
        fi = (f"{np.mean([r['calls_fwd_inv'][0] for r in runs]):,.0f} + {np.mean([r['calls_fwd_inv'][1] for r in runs]):,.0f}"
              if "calls_fwd_inv" in runs[0] else "--")
        rows.append(f"{nice} & {runs[0]['n_cands']}/{runs[0]['n_true']} & {mf('tane', 'false'):.0f} / {mf('tane', 'missed'):.0f} & "
                    f"{mf('ours', 'false'):.0f} / {mf('ours', 'missed'):.1f} & {oc:,.0f} ({fi}) & {ca:,.0f} \\\\")
    (ROOT / "paper/tables/e9.tex").write_text(
        "\\begin{table}[t]\\centering\\small\\caption{Two-attribute left-hand sides $\\{A,B\\}\\rightarrow Y$: false accepted / true "
        "missed per run (mean over 3 seeds; candidates/true in parentheses), our oracle calls per run (forward + inverse) and the cost of "
        "canonicalizing every value. TANE runs with $g_3$ and up to two left-hand attributes. Generated by exp/make\\_tables.py.}"
        "\\label{tab:e9}\n\\setlength{\\tabcolsep}{3pt}\\begin{tabular}{lccccr}\\toprule\n"
        "data & cand./true & TANE & ours & calls & canon.-all \\\\\\midrule\n" + "\n".join(rows) +
        "\n\\bottomrule\\end{tabular}\\end{table}\n")



def latex_e18():
    """E18 (pre-registered): plain vs alias-only audits over all unary candidates, complete inverse."""
    rows = []
    for key, nice in (("geonames_16k", "GeoNames"), ("tax", "Tax"), ("ndc", "NDC"), ("gpg", "GPG")):
        p = R / f"e18_variants_{key}.json"
        if not p.exists():
            continue
        runs = load(p)["runs"]
        m = lambda v: np.mean([r["variants"][v]["calls"] for r in runs])
        miss = lambda v: np.mean([len(r["variants"][v]["missed"]) + len(r["variants"][v]["false"]) for r in runs])
        same = all(r["variants"][v]["missed"] == r["variants"]["plain"]["missed"]
                   and r["variants"][v]["false"] == r["variants"]["plain"]["false"]
                   for r in runs for v in ("hybrid_aliasonly", "tfidf_aliasonly"))
        assert same, key                                       # the table claims identical decisions
        rows.append(f"{nice} & {runs[0]['n_cands']}/{runs[0]['n_true']} & {m('plain'):,.0f} & {m('hybrid_aliasonly'):,.0f} & "
                    f"{m('tfidf_aliasonly'):,.0f} & {np.mean([r['variants']['plain']['canon_all'] for r in runs]):,.0f} & "
                    f"{miss('plain'):.0f} \\\\")
    if rows:
        (ROOT / "paper/tables/e18.tex").write_text(
            "\\begin{table}[t]\\centering\\small\\caption{All unary candidates under a complete inverse (E18, pre-registered): "
            "oracle calls per run (mean over 3 seeds) for the audit of Algorithm~\\ref{alg:cert} (proxy neighbors and aliases, used in all "
            "other tables), the audit of aliases only (same hybrid proxy, or TF-IDF), and canonicalizing every value. All three audits made "
            "identical decisions; wrong decisions per run in the last column. Candidates include injected probes. Generated by exp/make\\_tables.py.}"
            "\\label{tab:e18}\n\\setlength{\\tabcolsep}{3pt}\\begin{tabular}{lcrrrrc}\\toprule\n"
            "data & cand./true & default & aliases & TF-IDF al. & canon.-all & wrong \\\\\\midrule\n" + "\n".join(rows) +
            "\n\\bottomrule\\end{tabular}\\end{table}\n")


latex_e9()
latex_e18()
paper_numbers()


def fit_tables(names=("e1b", "sensitivity", "e9", "e18")):
    """Scale the tabulars that exceed the column width (measured overfull) to the column width."""
    for n in names:
        f = ROOT / f"paper/tables/{n}.tex"
        if not f.exists():
            continue
        t = f.read_text()
        if "resizebox" in t:
            continue
        t = t.replace("\\begin{tabular}", "\\resizebox{\\columnwidth}{!}{\\begin{tabular}", 1)
        t = t.replace("\\end{tabular}", "\\end{tabular}}", 1)
        f.write_text(t)


fit_tables()
