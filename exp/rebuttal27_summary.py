"""Summarize the post-freeze (rebuttal) experiments: results/rebuttal27/*.json -> results/rebuttal27/NUMBERS.md.
Kept apart from exp/make_tables.py so that the submitted paper's PAPER_NUMBERS.md and tables do not change."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "results/rebuttal27"


def ra(lines):
    d = json.loads((R / "ra_llm14b.json").read_text())
    s, f = d["summary"], lambda x: f"{x:.3f}"
    miss = [r["seed"] for r in d["runs"] if r["missed_true"]]
    missed_fd = sorted({x["fd"] for r in d["runs"] for x in r["fds"] if x["reference_true"] and not x["certified"]})
    tb = lambda to: min(t["bound"] for t in d["transfer"] if t["to"] == to)
    off = {o["fd"]: o for o in d["offline"]}
    lines += [
        "## R-A: second LLM oracle (Qwen2.5-14B-Instruct Q4_K_S; literature/prereg_ra_llm14b_2026-11-03.md)", "",
        f"- **Model sha256**: {d['model_sha256']}",
        f"- **Resolve (all labeler names)**: {d['n_values']:,} calls, mean {d['sec_mean']:.2f} s, median {d['sec_median']:.2f} s per call (4 processes x 14 threads, shared server), empty answers {d['empty_answers']}",
        f"- **B-cubed F1 vs labeler-code oracle**: 14B {f(d['agreement_14b_vs_code']['bcubed_f1'])}, 7B {f(d['agreement_7b_vs_code']['bcubed_f1'])}; pair precision/recall 14B {f(d['agreement_14b_vs_code']['pair_precision'])}/{f(d['agreement_14b_vs_code']['pair_recall'])}, 7B {f(d['agreement_7b_vs_code']['pair_precision'])}/{f(d['agreement_7b_vs_code']['pair_recall'])}",
        f"- **14B vs 7B labels**: B-cubed F1 {f(d['agreement_14b_vs_7b']['bcubed_f1'])}; disagreement mass {f(d['disagreement_mass_14b_7b'])} (14B vs code {f(d['disagreement_mass_14b_code'])})",
        f"- **True candidates**: 14B {d['true_sets']['14b']}; 7B {d['true_sets']['7b']}; code {d['true_sets']['code']}",
        f"- **g3 of labcode->labeler**: 14B {off['labcode->labeler']['g3_14b']:.4f}, 7B {off['labcode->labeler']['g3_7b']:.4f}, code {off['labcode->labeler']['g3_code']:.4f}; max nu (neighbour-only) {s['max_nu']:.4f} (declared 0.01)",
        f"- **Replay, seeds 0-9 x 7 candidates**: false certifications {s['false_cert']}/70; missed {s['missed_true']} of {s['true_opportunities']} true-FD opportunities ({', '.join(missed_fd)}; seeds {miss}); calls {s['calls_min']:,}-{s['calls_max']:,} per run vs {s['resolve_calls']:,} to resolve ({s['resolve_calls']/s['calls_max']:.1f}-{s['resolve_calls']/s['calls_min']:.1f}x fewer)",
        f"- **Oracle transfer**: {s['transfer_violations']} of {s['n_transferred']} transferred bounds violated; smallest transferred bound {tb('code'):.3f} (to code), {tb('7b'):.3f} (to 7B)",
        "- **Limitation**: same model family as the 7B oracle; NDC labeler names only; replay of one saved answer set.", ""]


def rb(lines):
    pr = json.loads((ROOT / "results/icde27/e25_sec_probe.json").read_text())
    d = json.loads((ROOT / "results/icde27/e25_sec_discovery.json").read_text())
    C = d["complete"]
    rng = lambda xs, fmt="{:,}": fmt.format(min(xs)) + ("" if min(xs) == max(xs) else "-" + fmt.format(max(xs)))
    od = lambda fd, k: [r["ours_detail"][fd][k] for r in C]
    tr = C[0]["truth"]
    sc = lambda m: (sum(r[m]["false"] for r in C), sum(r[m]["missed_true"] for r in C))
    P = lambda p: [q for q in d["partial"] if q["p"] == p]
    lines += [
        "## R-B: SEC EDGAR filer names, cik oracle (literature/prereg_rb_sec_probe_2026-11-03.md, prereg_rb_sec_full_2026-11-03.md)", "",
        f"- **Table**: sub.txt {pr['quarters'][0]}-{pr['quarters'][1]}, {pr['rows']:,} rows after dropping {pr['rows_dropped_ambiguous_name']:,} rows of {pr['ambiguous_names']} names shared by several ciks; {pr['ciks']:,} ciks, {pr['names']:,} names",
        f"- **Natural aliases**: {pr['multi_name_ciks']:,} ciks filed under several names ({pr['multi_name_tuple_share']:.1%} of tuples); {pr['multi_name_pairs_lev_below_0.9']:,} of {pr['multi_name_pairs']:,} name pairs of such ciks have Levenshtein ratio < 0.9",
        f"- **Truth (cik oracle)**: {C[0]['n_true']} of {C[0]['n_cands']} unary candidates true; name->stprba g3 {tr['name->stprba']:.3f} under the oracle vs "
        f"{next(c['g3_strings'] for c in pr['candidates'] if c['fd'] == 'name->stprba'):.3f} on strings (true on strings, false on entities); name->sic g3 {tr['name->sic']:.3f}",
        f"- **Ours, complete inverse (3 seeds)**: false {sc('ours')[0]}, missed {sc('ours')[1]} ({', '.join(sorted({m for r in C for m in r['missed_lists']['ours']}))}: U {rng(od('name->sic','ub'),'{:.3f}')} at the 20,000-sample cap); "
        f"calls {rng([r['ours_calls_total'] for r in C])} vs canonicalize-all {C[0]['canon_all']:,} ({min(r['ours_calls_total'] for r in C)/C[0]['canon_all']:.2f}-{max(r['ours_calls_total'] for r in C)/C[0]['canon_all']:.2f}x); name->sic alone {rng(od('name->sic','calls'))} calls",
        f"- **name->stprba (false)**: rejected by ours in 3/3 (U {rng(od('name->stprba','ub'),'{:.3f}')}); accepted by TANE on raw and on normalized strings, the proxy quotient and the estimator without the audit in every seed",
        f"- **Baselines, false/missed summed over 3 seeds**: TANE raw {sc('b3_tane_raw')}, TANE normalized {sc('b3_tane_norm')}, quotient {sc('b1_quotient')}, no audit {sc('b9_noaudit')}, planner {sc('planner')} at {rng([r['planner_calls_total'] for r in C])} calls",
        f"- **Certified closure**: {sum(r['derived']['n_violating_bound'] for r in C)} of {sum(r['derived']['n_derived_total'] for r in C)} derived bounds violated",
        f"- **Incomplete inverse (E11 procedure, nu_bar = 0)**: p = 0.5: false {sum(len(q['false']) for q in P(0.5))}, missed {sum(len(q['missed']) for q in P(0.5))}, max nu {max(q['nu_max'] for q in P(0.5)):.3f}; "
        f"p = 0 (neighbours only): false {sum(len(q['false']) for q in P(0.0))} ({', '.join(sorted({f for q in P(0.0) for f in q['false']}))} in every seed), max nu {max(q['nu_max'] for q in P(0.0)):.3f}",
        (lambda n: f"- **Post-hoc sensitivity (added after seeing the result, not pre-registered)**: neighbours only with the paper's declared nu_bar = 0.01: false {sum(len(r['false']) for r in n['runs'])}; "
         f"name->stprba rejected in 3/3 with U {min(r['fds']['name->stprba']['ub'] for r in n['runs']):.3f}-{max(r['fds']['name->stprba']['ub'] for r in n['runs']):.3f} (U + 0.01 >= 0.05: rejected by the declared margin, while the measured nu at p = 0 is {max(q['nu_max'] for q in P(0.0)):.3f}); "
         f"missed {sum(len(r['missed']) for r in n['runs'])} ({', '.join(sorted({m for r in n['runs'] for m in r['missed']}))}); calls {min(r['calls'] for r in n['runs']):,}-{max(r['calls'] for r in n['runs']):,}")(json.loads((ROOT / "results/icde27/e25_sec_nubar.json").read_text())),
        "- **Limitation**: the aliases are mostly renames, not spelling variants; name->stprba fails on entities because the state recorded for one filer varies across its filings over the decade (moves or inconsistent entries); one table, 3 seeds.", ""]


if __name__ == "__main__":
    lines = ["# Post-freeze experiments (not in the submitted paper)", "",
             "Generated by `exp/rebuttal27_summary.py`. Run after the manuscript freeze `icde27-freeze`.", ""]
    ra(lines)
    lines += ["R-B (SEC EDGAR) moved into the paper as E25 on 2026-11-03: see results/icde27/PAPER_NUMBERS.md.", ""]
    (R / "NUMBERS.md").write_text("\n".join(lines))
    print("\n".join(lines))
