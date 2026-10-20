"""E8: an LLM as the oracle (case study on NDC labeler names).

A local instruct model (Qwen2.5-7B-Instruct, Q4_K_M GGUF via llama-cpp-python,
CPU only) is used as a CANONICALIZER: given one labeler name it returns the
canonical firm name; f(v) = Layer-1 normalisation of that output. Being a
function, it is transitive by construction (Prop D) -- no pairwise judging.

The model sees the most frequent raw spelling of each Layer-1 value.
Step 1 (`--canon`): canonicalize every distinct labeler value once, in
parallel worker processes, caching outputs and per-call latency to
results/icde27/e8_llm_canon.json (so the experiment can count, for any method,
how many LLM calls it would make, without re-running the model).
Step 2 (default): compare the LLM oracle with the labeler-code oracle
(pairwise precision/recall of the induced equivalences, B-cubed), then certify
the NDC FDs with the LLM oracle (ANN-only blocking, declared nu_bar; the LLM has
no inverse) and score decisions against both oracles.
"""

import argparse
import json
import os
import sys
import time
import zlib
from multiprocessing import Pool
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "results/icde27/e8_llm_canon.json"
MODEL = Path(os.environ.get("E8_MODEL", Path.home() / "models/qwen2.5-7b-instruct-q4_k_m.gguf"))
SYSTEM = ("You normalize the names of companies that label drug products. Given one labeler name exactly as written "
          "in a product listing, reply with the canonical name of the company only: fix spelling and capitalization, "
          "drop legal suffixes (Inc, LLC, Ltd, Corp, Co), punctuation, store or division numbers, and 'dba'/'see also' "
          "remarks; if the listing names a store brand together with its owner, reply with the owner. "
          "Reply with the name only, no explanation.")
FEWSHOT = [("Acme Pharmaceuticals, Inc.", "Acme Pharmaceuticals"), ("ACME PHARMACUETICALS LLC", "Acme Pharmaceuticals"),
           ("Bestway Drug Co. (dba BestCare)", "Bestway Drug"), ("Northwind Health 220, LLC", "Northwind Health")]

_llm = None


def _init(threads):
    global _llm
    from llama_cpp import Llama
    from llama_cpp import LlamaRAMCache
    _llm = Llama(model_path=str(MODEL), n_ctx=512, n_threads=threads, n_threads_batch=threads, verbose=False, seed=0)
    _llm.set_cache(LlamaRAMCache(capacity_bytes=1 << 30))     # reuse the shared system/few-shot prefix


def _canon(item):
    v, shown = item
    msgs = [{"role": "system", "content": SYSTEM}]
    for a, b in FEWSHOT:
        msgs += [{"role": "user", "content": a}, {"role": "assistant", "content": b}]
    msgs.append({"role": "user", "content": shown})
    t0 = time.perf_counter()
    r = _llm.create_chat_completion(messages=msgs, max_tokens=24, temperature=0.0)
    return v, r["choices"][0]["message"]["content"].strip().split("\n")[0], time.perf_counter() - t0


def canonicalize_all(vals, procs, threads, surface):
    done = json.loads(OUT.read_text()) if OUT.exists() else {"model": MODEL.name, "out": {}, "sec": {}}
    todo = [v for v in vals if v not in done["out"]]
    print(f"{len(todo)} values to canonicalize with {procs} procs x {threads} threads", flush=True)
    with Pool(procs, initializer=_init, initargs=(threads,)) as pool:
        for i, (v, o, sec) in enumerate(pool.imap_unordered(_canon, [(v, surface[v]) for v in todo], chunksize=4)):
            done["out"][v], done["sec"][v] = o, sec
            if i % 200 == 0:
                OUT.write_text(json.dumps(done))
                print(i, repr(v), "->", repr(o), f"{sec:.2f}s", flush=True)
    OUT.write_text(json.dumps(done))
    return done


def pair_metrics(vals, f_ref, f_llm):
    """Precision/recall of the LLM's equivalence w.r.t. the reference, over all
    value pairs (computed from cluster sizes), plus B-cubed F1."""
    from collections import Counter
    ref = Counter(f_ref[v] for v in vals)
    llm = Counter(f_llm[v] for v in vals)
    both = Counter((f_ref[v], f_llm[v]) for v in vals)
    pairs = lambda c: sum(n * (n - 1) // 2 for n in c.values())
    tp, pr, pl = pairs(both), pairs(ref), pairs(llm)
    bp = np.mean([both[(f_ref[v], f_llm[v])] / llm[f_llm[v]] for v in vals])
    br = np.mean([both[(f_ref[v], f_llm[v])] / ref[f_ref[v]] for v in vals])
    return {"pair_precision": tp / max(pl, 1), "pair_recall": tp / max(pr, 1),
            "bcubed_precision": float(bp), "bcubed_recall": float(br),
            "bcubed_f1": float(2 * bp * br / (bp + br)), "ref_entities": len(ref), "llm_entities": len(llm)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--canon", action="store_true")
    ap.add_argument("--procs", type=int, default=14)
    ap.add_argument("--threads", type=int, default=8)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--certify", action="store_true", help="end-to-end: certify NDC natural FDs with the LLM oracle "
                    "(lazy calls, neighbour-only blocking: heuristic, no inverse)")
    ap.add_argument("--offline", action="store_true", help="after --canon on ALL values: exact LLM-oracle truth, full-"
                    "domain agreement, and certification replayed from the cache (calls counted, no model time)")
    ap.add_argument("--tokens", action="store_true", help="after --canon on ALL values: count prompt tokens (GGUF "
                    "tokenizer only, no inference) for full canonicalization and for each replayed certification run")
    ap.add_argument("--transfer", action="store_true", help="after --canon on ALL values: oracle-transfer lemma, "
                    "smallest tuple mass on which the LLM and labeler-code oracles disagree, and transferred bounds")
    ap.add_argument("--replay-check", type=int, default=0, help="re-query N cached values live and compare")
    ap.add_argument("--timing", type=int, default=0, help="time N single-process calls on values outside the sample")
    ap.add_argument("--sample", type=int, default=0, help="stratified sample: all values of the largest "
                    "multi-variant firms (reference oracle) up to N-100, plus 100 random values")
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--delta", type=float, default=0.05)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--nu-bar", type=float, default=0.01)
    a = ap.parse_args()
    from semfd.data import ndc
    from semfd.proxy import layer1
    ds = ndc(seed=0, near_miss=())
    vals = sorted(ds.oracle["labeler"])
    raw = ds.df["labeler"]
    surface = raw.groupby(raw.map(layer1)).agg(lambda s: s.value_counts().index[0]).to_dict()  # most common spelling
    if a.sample:
        from collections import Counter
        size = Counter(ds.oracle["labeler"][v] for v in vals)
        big = [e for e, n in size.most_common() if n > 1]
        pick, rng = [], np.random.default_rng(0)
        for e in big:
            members = [v for v in vals if ds.oracle["labeler"][v] == e]
            if len(pick) + len(members) > a.sample - 100:
                break
            pick += members
        rest = [v for v in vals if v not in set(pick)]
        pick += list(rng.choice(rest, 100, replace=False))
        vals = sorted(pick)
    if a.transfer:                             # Sec. IV oracle-transfer lemma: |g3_llm - g3_code| <= disagreement mass
        import re
        from semfd.oracle import disagreement_mass
        c = json.loads(OUT.read_text())
        f_llm = {v: "llm:" + re.sub(r"[^a-z0-9]", "", layer1(c["out"][v])) for v in vals}
        lab1 = list(raw.map(layer1))
        m = disagreement_mass(lab1, f_llm.__getitem__, ds.oracle["labeler"].__getitem__)
        off = json.loads((ROOT / "results/icde27/e8_llm_offline.json").read_text())
        rows = [{"fd": f["fd"], "seed": f["seed"], "certified": f["certified"], "ub": f["ub"], "g3_llm": f["g3_llm"],
                 "g3_code": f["g3_code"], "transferred_bound": min(1.0, f["ub"] + a.nu_bar + m)}
                for f in off["fds"] if "labeler" in f["fd"].split("->")]
        viol = sum(r["g3_code"] > r["transferred_bound"] + 1e-12 for r in rows)
        gaps = [abs(r["g3_llm"] - r["g3_code"]) for r in rows]
        res = {"disagreement_mass": m, "max_abs_g3_gap": max(gaps), "transferred_bound_violations": viol,
               "n_bounds": len(rows), "rows": rows}
        (ROOT / "results/icde27/e8_transfer.json").write_text(json.dumps(res, indent=1))
        print(json.dumps({k: v for k, v in res.items() if k != "rows"}), flush=True)
        sys.exit(0)
    if a.tokens:                               # token cost, API-equivalent (prefix caching ignored)
        import re
        from llama_cpp import Llama
        from semfd.certify import certify
        tok = Llama(model_path=str(MODEL), vocab_only=True, verbose=False)
        c = json.loads(OUT.read_text())

        def chatml(v):                         # Qwen2.5 chat template (ChatML) for the messages _canon sends
            m = f"<|im_start|>system\n{SYSTEM}<|im_end|>\n"
            for x, y in FEWSHOT:
                m += f"<|im_start|>user\n{x}<|im_end|>\n<|im_start|>assistant\n{y}<|im_end|>\n"
            return m + f"<|im_start|>user\n{surface[v]}<|im_end|>\n<|im_start|>assistant\n"
        n_in = {v: len(tok.tokenize(chatml(v).encode(), add_bos=False, special=True)) for v in vals}
        n_out = {v: len(tok.tokenize(c["out"][v].encode(), add_bos=False, special=False)) + 1 for v in vals}  # + <|im_end|>
        f_llm = {v: "llm:" + re.sub(r"[^a-z0-9]", "", layer1(c["out"][v])) for v in vals}
        llm_ds = type(ds)(ds.name, ds.df, ds.exact, {"labeler": f_llm}, ds.fds, ds.meta)
        attrs = ds.attrs()
        af = a.alpha / len(ds.fds)
        runs = []
        for s_ in range(a.seeds):              # identical replay to --offline (same seeds), recording the queried names
            orcs = llm_ds.oracles()
            for x, y in ds.fds:
                certify(attrs[x], attrs[y], orcs[x], orcs[y], 0.9, a.delta, af,
                        np.random.default_rng(zlib.crc32(f"e8o|{s_}|{x}|{y}".encode())), nu_bar=a.nu_bar)
            q = list(orcs["labeler"].cache)
            runs.append({"seed": s_, "calls": len(q), "input_tokens": sum(n_in[v] for v in q),
                         "output_tokens_stored": sum(n_out[v] for v in q)})
        res = {"model": c["model"], "template": "ChatML (Qwen2.5), system + 4 few-shot pairs + name",
               "max_tokens_per_call": 24, "output_note": "stored answers are the first line of each reply",
               "canon_all": {"calls": len(vals), "input_tokens": sum(n_in.values()),
                             "output_tokens_stored": sum(n_out.values())},
               "input_tokens_per_call": {"min": min(n_in.values()), "mean": float(np.mean(list(n_in.values()))),
                                         "max": max(n_in.values())},
               "runs": runs}
        (ROOT / "results/icde27/e8_tokens.json").write_text(json.dumps(res, indent=1))
        print(json.dumps(res, indent=1), flush=True)
        sys.exit(0)
    if a.offline:
        import re
        from semfd.certify import certify, g3_codes
        from semfd.oracle import Canonicalizer, total_calls
        c = json.loads(OUT.read_text())
        missing = [v for v in vals if v not in c["out"]]
        assert not missing, f"{len(missing)} labeler values not canonicalized yet"
        f_llm = {v: "llm:" + re.sub(r"[^a-z0-9]", "", layer1(c["out"][v])) for v in vals}
        res = {"model": c["model"], "n_values": len(vals),
               "agreement_full": pair_metrics(vals, ds.oracle["labeler"], f_llm),
               "agreement_layer1_full": pair_metrics(vals, ds.oracle["labeler"], {v: v for v in vals}),
               "sec_mean_all_calls": float(np.mean(list(c["sec"].values()))), "fds": []}
        attrs = ds.attrs()
        ent_code = ds.entity_codes(attrs)
        llm_ds = type(ds)(ds.name, ds.df, ds.exact, {"labeler": f_llm}, ds.fds, ds.meta)
        ent_llm = llm_ds.entity_codes(attrs)
        af = a.alpha / len(ds.fds)
        for s_ in range(a.seeds):
            orcs = llm_ds.oracles()
            for x, y in ds.fds:
                r = certify(attrs[x], attrs[y], orcs[x], orcs[y], 0.9, a.delta, af,
                            np.random.default_rng(zlib.crc32(f"e8o|{s_}|{x}|{y}".encode())), nu_bar=a.nu_bar)
                gl = g3_codes(ent_llm[x][attrs[x].codes], ent_llm[y][attrs[y].codes])
                gc = g3_codes(ent_code[x][attrs[x].codes], ent_code[y][attrs[y].codes])
                from semfd.certify import miss_mass
                nu = miss_mass(attrs[x], attrs[y], ent_llm[x], ent_llm[y], 0.9)
                res["fds"].append({"seed": s_, "fd": f"{x}->{y}", "certified": r["certified"], "ub": r["ub"],
                                   "calls": r["calls"], "g3_llm": float(gl), "g3_code": float(gc), "nu_llm": float(nu)})
            res.setdefault("run_calls", []).append(total_calls(orcs))
        res["canon_all_labeler"] = len(vals)
        (ROOT / "results/icde27/e8_llm_offline.json").write_text(json.dumps(res, indent=1))
        print(json.dumps(res["agreement_full"]), res["run_calls"], flush=True)
        for f in res["fds"]:
            print(f, flush=True)
        sys.exit(0)
    if a.certify:
        from semfd.certify import certify, g3_codes
        from semfd.oracle import Canonicalizer
        import re
        cache = json.loads(OUT.read_text()) if OUT.exists() else {"model": MODEL.name, "out": {}, "sec": {}}
        _init(a.threads)
        fresh = {"n": 0, "sec": 0.0}

        def llm_f(v):
            if v not in cache["out"]:
                _, o, sec = _canon((v, surface[v]))
                cache["out"][v], cache["sec"][v] = o, sec
                fresh["n"] += 1
                fresh["sec"] += sec
                if fresh["n"] % 20 == 0:
                    OUT.write_text(json.dumps(cache))
            return "llm:" + re.sub(r"[^a-z0-9]", "", layer1(cache["out"][v]))
        attrs = ds.attrs()
        ent = ds.entity_codes(attrs)
        orcs = ds.oracles()
        orcs["labeler"] = Canonicalizer(llm_f, name="labeler-llm")
        af = a.alpha / len(ds.fds)
        res = {"model": MODEL.name, "mode": "neighbour-only (heuristic), nu_bar=%g" % a.nu_bar, "fds": []}
        t0 = time.perf_counter()
        for x, y in ds.fds:
            c0 = orcs[x].calls + (orcs[y].calls if orcs[y] is not orcs[x] else 0)
            r = certify(attrs[x], attrs[y], orcs[x], orcs[y], 0.9, a.delta, af,
                        np.random.default_rng(zlib.crc32(f"e8c|{x}|{y}".encode())), nu_bar=a.nu_bar)
            g_code = g3_codes(ent[x][attrs[x].codes], ent[y][attrs[y].codes])
            res["fds"].append({"fd": f"{x}->{y}", "certified": r["certified"], "ub": r["ub"], "samples": r["samples"],
                               "calls": r["calls"], "g3_code_oracle": float(g_code)})
            print(x, y, "C" if r["certified"] else "-", f"U={r['ub']:.3f} calls={r['calls']} g3(code)={g_code:.3f}",
                  f"llm_new={fresh['n']} llm_sec={fresh['sec']:.0f}", flush=True)
            OUT.write_text(json.dumps(cache))
        res["labeler_calls"] = orcs["labeler"].calls
        res["llm_new_calls"], res["llm_new_sec"] = fresh["n"], fresh["sec"]
        res["wall_sec"] = time.perf_counter() - t0
        res["canon_all_labeler"] = len(attrs["labeler"].vals)
        (ROOT / "results/icde27/e8_llm_certify.json").write_text(json.dumps(res, indent=1))
        sys.exit(0)
    if a.replay_check:                         # re-query cached values live; replay is valid iff answers repeat
        import re
        c = json.loads(OUT.read_text())
        pick = list(np.random.default_rng(7).choice(sorted(c["out"]), a.replay_check, replace=False))
        _init(a.threads)
        norm = lambda o: re.sub(r"[^a-z0-9]", "", layer1(o))
        same_raw = same_norm = 0
        diffs = []
        for v in pick:
            _, o, _sec = _canon((v, surface[v]))
            same_raw += o == c["out"][v]
            same_norm += norm(o) == norm(c["out"][v])
            if norm(o) != norm(c["out"][v]):
                diffs.append([v, c["out"][v], o])
        res = {"n": len(pick), "identical_raw": same_raw, "identical_label": same_norm, "differences": diffs[:20]}
        (ROOT / "results/icde27/e8_replay_check.json").write_text(json.dumps(res, indent=1))
        print(res["n"], "raw identical", same_raw, "label identical", same_norm, flush=True)
        sys.exit(0)
    if a.timing:                               # clean single-process latency (record load average)
        allv = sorted(ds.oracle["labeler"])
        rest = [v for v in allv if v not in set(vals)]
        pick = list(np.random.default_rng(1).choice(rest, a.timing, replace=False))
        _init(a.threads)
        lat = []
        for v in pick:
            _, o, sec = _canon((v, surface[v]))
            lat.append(sec)
        tp = ROOT / "results/icde27/e8_latency.json"
        tp.write_text(json.dumps({"model": MODEL.name, "threads": a.threads, "n": len(lat), "sec": lat,
                                  "mean": float(np.mean(lat)), "p50": float(np.median(lat)),
                                  "loadavg_after": os.getloadavg()}, indent=1))
        print("latency mean", np.mean(lat), "p50", np.median(lat), "load", os.getloadavg(), flush=True)
        sys.exit(0)
    if a.canon:
        canonicalize_all(vals[: a.limit] if a.limit else vals, a.procs, a.threads, surface)
        sys.exit(0)
    from semfd.certify import certify, g3_codes, miss_mass
    from semfd.oracle import Canonicalizer
    c = json.loads(OUT.read_text())
    vals = [v for v in vals if v in c["out"]]
    f_llm = {v: "llm:" + layer1(c["out"][v]) for v in vals}
    import re
    f_llm_n = {v: "llmn:" + re.sub(r"[^a-z0-9]", "", layer1(c["out"][v])) for v in vals}
    res = {"model": c["model"], "n_values": len(vals),
           "sec_per_call": {"mean": float(np.mean(list(c["sec"].values()))),
                            "p50": float(np.median(list(c["sec"].values())))},
           "agreement": pair_metrics(vals, ds.oracle["labeler"], f_llm),
           "agreement_alnum_normalized": pair_metrics(vals, ds.oracle["labeler"], f_llm_n),
           "agreement_layer1_baseline": pair_metrics(vals, ds.oracle["labeler"], {v: v for v in vals}),
           "fds": []}
    for k in ("agreement", "agreement_alnum_normalized", "agreement_layer1_baseline"):
        print(k, {m: round(x, 3) for m, x in res[k].items()}, flush=True)
    print(res["sec_per_call"], flush=True)
    if len(vals) < len(ds.oracle["labeler"]):           # sample mode: agreement + latency only
        res["sample_mode"] = True
        (ROOT / "results/icde27/e8_llm.json").write_text(json.dumps(res, indent=1))
        sys.exit(0)
    attrs = ds.attrs()
    ent_code = ds.entity_codes(attrs)
    llm_ds = type(ds)(ds.name, ds.df, ds.exact, {"labeler": f_llm}, ds.fds, ds.meta)
    ent_llm = llm_ds.entity_codes(attrs)
    af = a.alpha / len(ds.fds)
    for s in range(a.seeds):
        orcs = llm_ds.oracles()
        for x, y in ds.fds:
            ax, ay = attrs[x], attrs[y]
            g_code = g3_codes(ent_code[x][ax.codes], ent_code[y][ay.codes])
            g_llm = g3_codes(ent_llm[x][ax.codes], ent_llm[y][ay.codes])
            r = certify(ax, ay, orcs[x], orcs[y], 0.9, a.delta, af,
                        np.random.default_rng(zlib.crc32(f"e8|{s}|{x}|{y}".encode())), nu_bar=a.nu_bar)
            nu = miss_mass(ax, ay, ent_llm[x], ent_llm[y], 0.9)
            res["fds"].append({"seed": s, "fd": f"{x}->{y}", "g3_code": float(g_code), "g3_llm": float(g_llm),
                               "certified": r["certified"], "ub": r["ub"], "calls": r["calls"], "nu_llm": nu})
            print(s, x, y, f"g3 code={g_code:.3f} llm={g_llm:.3f}", "C" if r["certified"] else "-",
                  f"U={r['ub']:.3f} calls={r['calls']} nu={nu:.3f}", flush=True)
    (ROOT / "results/icde27/e8_llm.json").write_text(json.dumps(res, indent=1))
