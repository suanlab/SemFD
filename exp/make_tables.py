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
    big_names = ds_names + [("geonames_640k", "GeoNames-640k")]   # all unary candidates at 640k rows (2 seeds)
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
            cells.append(f"{fa:.0f} / {mi:.0f}" if fa == int(fa) else f"{fa:.1f} / {mi:.0f}")
        b2 = R / f"b2_fastrfd_{key}.json"
        if b2.exists():
            e = load(b2)
            cells.insert(1, " ".join(f"{r['false']}/{r['missed_true']}" if not r.get("timeout") else "t/o"
                                     for r in e["runs"] if r["t"] in (0.0, 0.001)))
        else:
            cells.insert(1, "n/r")
        rows.append(f"{nice} ({runs[0]['n_cands']}/{runs[0]['n_true']}) & " + " & ".join(cells) + " \\\\")
    (T / "e1b.tex").write_text(
        "\\begin{table}[t]\\centering\\small\\caption{Discovery over all unary candidates: false accepted / true "
        "missed per run (mean over 3 seeds, 2 at 640k rows; candidates/true in parentheses; n/r: not run). FastRFD (deterministic, one run on the seed-0 "
        "table) at $g_1$ tolerance 0 and 0.001. Generated by exp/make\\_tables.py from results/icde27/e1b\\_*.json, b2\\_*.json.}\\label{tab:e1b}\n"
        "\\setlength{\\tabcolsep}{3pt}\\begin{tabular}{lccccc}\\toprule\n"
        "data & Tane ($g_3$) & FastRFD & quotient & no audit & ours \\\\\\midrule\n" + "\n".join(rows) +
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
        ia = load(cvp)[key]["canon_inverse_aware"] if cvp.exists() and key in load(cvp) else None
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
        + " per run on GeoNames, Tax, NDC and GeoNames at 640k rows; ours) vs.\\ "
        "canonicalizing every distinct value; ``fwd + inv'' splits our calls into forward canonicalizations and inverse "
        "(alias-list) lookups; the ratio gives the mean and the min--max over seeds; ``inv.-aware'' lets canonicalize-all also use inverse lookups (one forward and one inverse call "
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
                cells.append("\\todo{} & \\todo{}")
                continue
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
        "setting & F/M & calls & F/M & calls \\\\\\midrule\n" + "\n".join(rows) +
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
        "instance and on the raw strings, certifications over 3 seeds, final bound $U$ and oracle calls of the "
        "certificate (inverse access; with a cache shared across candidates, per-FD calls are marginal and depend on order). $\\delta=0.05$. Generated by exp/make\\_tables.py.}"
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
    for p in sorted(R.glob("e1_*.json")):
        runs = load(p)
        if "ann_nubar" not in runs[0]["fds"][0]["ours"]:
            continue
        add(f"nu max (ANN-only) {p.stem}", f"{max(x['ours']['ann_nubar']['nu'] for r in runs for x in r['fds']):.3f}")
    for key in ("geonames_16k", "tax", "ndc"):
        p = R / f"e1b_{key}.json"
        if p.exists():
            runs = load(p)
            add(f"E1b seconds {key}", {k: round(float(np.mean([r['sec'][k] for r in runs])), 1) for k in runs[0]["sec"]})
            add(f"E1b planner vs ours calls {key}", f"{np.mean([r['planner_calls_total'] for r in runs]):.0f} vs "
                                                   f"{np.mean([r['ours_calls_total'] for r in runs]):.0f}")
            add(f"E1b planner resolved / candidates {key}", f"{[r['planner_resolved'] for r in runs]} / {runs[0]['n_cands']}; "
                                                          f"planner F/M {[(r['planner']['false'], r['planner']['missed_true']) for r in runs]}")
    for p in sorted(R.glob("b2_fastrfd_*.json")):
        e = load(p)
        add(f"FastRFD seconds {p.stem}", [(r["t"], round(r["sec"])) for r in e["runs"]])
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
    # lower-bound value at the evaluated scale (Thm lower: q >= sqrt((beta-alpha) D (D-1) / m))
    p = R / "e1_geonames_16k.json"
    if p.exists():
        import math
        D = int(np.mean([r["distinct"]["city"] for r in load(p)]))
        m = int(0.05 * D) + 1
        add("Lower bound at GeoNames-16k city domain", f"D={D}, delta=0.05, m={m}, beta-alpha=0.5: "
                                                        f"q >= {math.sqrt(0.5 * D * (D - 1) / m):.0f}")
    shares = []
    for key in ("geonames_16k", "tax", "ndc"):
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
        add("Inverse share of our calls (cost table rows)", f"{min(shares):.2f}-{max(shares):.2f}")
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
    for d in ("geonames_16k", "tax", "ndc"):
        runs_all = []
        for f in sorted(R.glob(f"b2_fastrfd_{d}*.json")):
            runs_all += [r for r in load(f)["runs"] if not r.get("timeout")]
        if runs_all:
            pts = sorted((r["t"], r["false"], r["missed_true"]) for r in runs_all)
            add(f"FastRFD all tolerances {d} (t, false, missed)", pts)
            add(f"FastRFD {d}: any tolerance with 0 false and 0 missed?", any(f == 0 and m == 0 for _, f, m in pts))
    be = {}
    for key in ("geonames_16k", "tax", "ndc", "geonames_640k"):
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
                f"calls proxy={f['proxy']['calls_mean']:.0f} refine={f['refine']['calls_mean']:.0f}")
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
            f"canon/cold initial {init['canon'] / init['cold']:.2f}x; slack cost maintain/cold initial {init['maintain'] / init['cold']:.2f}x; maintain/canon cumulative {cum['maintain'] / cum['canon']:.2f}x")
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
            f"calls {min(ours('ann_nubar', 'calls'))}-{max(ours('ann_nubar', 'calls'))}; "
            f"inverse certified {sum(ours('inverse', 'certified'))}/{len(rr)}, U {min(ours('inverse', 'ub')):.3f}-{max(ours('inverse', 'ub')):.3f}, "
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
        oc, ca = np.mean([r["calls"] for r in runs]), runs[0]["canon_all"]
        fi = (f"{np.mean([r['calls_fwd_inv'][0] for r in runs]):,.0f} + {np.mean([r['calls_fwd_inv'][1] for r in runs]):,.0f}"
              if "calls_fwd_inv" in runs[0] else "--")
        rows.append(f"{nice} & {runs[0]['n_cands']}/{runs[0]['n_true']} & {mf('tane', 'false'):.0f} / {mf('tane', 'missed'):.0f} & "
                    f"{mf('ours', 'false'):.0f} / {mf('ours', 'missed'):.1f} & {oc:,.0f} ({fi}) & {ca:,} \\\\")
    (ROOT / "paper/tables/e9.tex").write_text(
        "\\begin{table}[t]\\centering\\small\\caption{Two-attribute left-hand sides $\\{A,B\\}\\rightarrow Y$: false accepted / true "
        "missed per run (mean over 3 seeds; candidates/true in parentheses), our oracle calls per run (forward + inverse) and the cost of "
        "canonicalizing every value. Tane runs with $g_3$ and up to two left-hand attributes. Generated by exp/make\\_tables.py.}"
        "\\label{tab:e9}\n\\setlength{\\tabcolsep}{3pt}\\begin{tabular}{lccccr}\\toprule\n"
        "data & cand./true & Tane & ours & calls & canon.-all \\\\\\midrule\n" + "\n".join(rows) +
        "\n\\bottomrule\\end{tabular}\\end{table}\n")


latex_e9()
paper_numbers()


def fit_tables(names=("e1b", "sensitivity", "e9")):
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
