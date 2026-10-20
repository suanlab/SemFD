"""E14: a second LLM oracle attribute (Tax city names, 10k-row sample of the Raha Tax table).

Same model and protocol as E8 (Qwen2.5-7B-Instruct Q4_K_M, llama-cpp-python, CPU, temperature 0): the LLM is a
CANONICALIZER of one city name as written; f(v) = alphanumeric Layer-1 normalisation of its output, so the oracle is
a function and transitive by construction. Tax's own oracle maps every spelling (state-style abbreviations
SAINT/ST, FORT/FT, ..., typos, drops) to the clean city string.
  --canon    canonicalize every distinct city value once (cache: results/icde27/e14_llm_canon.json)
  (default)  agreement with the Tax oracle (pairwise and B-cubed), then certify the Tax FDs that involve city with
             the LLM as the city oracle (neighbor sets only, declared nu_bar; the LLM lists no spellings), replayed
             from the cache with each distinct value the certificate queries counted as one call; decisions are scored
             against the LLM's own g3 and the Tax oracle's g3, with the measured miss mass under the LLM's equivalence.
Output: results/icde27/e14_llm_tax_city.json
"""

import argparse
import json
import os
import re
import sys
import time
import zlib
from multiprocessing import Pool
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "results/icde27/e14_llm_canon.json"
MODEL = Path(os.environ.get("E8_MODEL", Path.home() / "models/qwen2.5-7b-instruct-q4_k_m.gguf"))
SYSTEM = ("You normalize United States city names taken from address records. Given one city name exactly as written, "
          "reply with the standard name of that city only: fix spelling, restore dropped letters, and write abbreviated "
          "words in full (ST = Saint, FT = Fort, MT = Mount, N = North, S = South, E = East, W = West, PT = Port, "
          "LK = Lake, SPGS = Springs, HTS = Heights, CTR = Center, VLG = Village, BCH = Beach). Reply in capital "
          "letters with the name only, no state and no explanation.")
FEWSHOT = [("FT LAUDERDLE", "FORT LAUDERDALE"), ("Saint Paul", "SAINT PAUL"), ("CLRWATER BCH", "CLEARWATER BEACH"),
           ("N LITTLE ROCK", "NORTH LITTLE ROCK")]
N_ROWS = 10000

_llm = None


def _init(threads):
    global _llm
    from llama_cpp import Llama, LlamaRAMCache
    _llm = Llama(model_path=str(MODEL), n_ctx=512, n_threads=threads, n_threads_batch=threads, verbose=False, seed=0)
    _llm.set_cache(LlamaRAMCache(capacity_bytes=1 << 30))


def _canon(item):
    v, shown = item
    msgs = [{"role": "system", "content": SYSTEM}]
    for a, b in FEWSHOT:
        msgs += [{"role": "user", "content": a}, {"role": "assistant", "content": b}]
    msgs.append({"role": "user", "content": shown})
    t0 = time.perf_counter()
    r = _llm.create_chat_completion(messages=msgs, max_tokens=16, temperature=0.0)
    return v, r["choices"][0]["message"]["content"].strip().split("\n")[0], time.perf_counter() - t0


def label(o):
    from semfd.proxy import layer1
    return "llm:" + re.sub(r"[^a-z0-9]", "", layer1(o))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--canon", action="store_true")
    ap.add_argument("--procs", type=int, default=4)
    ap.add_argument("--threads", type=int, default=6)
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--delta", type=float, default=0.05)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--nu-bar", type=float, default=0.01)
    a = ap.parse_args()
    from semfd.data import tax
    from semfd.proxy import layer1
    ds = tax(seed=0, n_rows=N_ROWS, near_miss=())
    raw = ds.df["city"]
    surface = raw.groupby(raw.map(layer1)).agg(lambda s: s.value_counts().index[0]).to_dict()
    vals = sorted(surface)
    if a.canon:
        done = json.loads(OUT.read_text()) if OUT.exists() else {"model": MODEL.name, "out": {}, "sec": {}}
        todo = [v for v in vals if v not in done["out"]]
        print(f"{len(todo)} of {len(vals)} values to canonicalize, {a.procs} procs x {a.threads} threads", flush=True)
        with Pool(a.procs, initializer=_init, initargs=(a.threads,)) as pool:
            for i, (v, o, sec) in enumerate(pool.imap_unordered(_canon, [(v, surface[v]) for v in todo], chunksize=4)):
                done["out"][v], done["sec"][v] = o, sec
                if i % 200 == 0:
                    OUT.write_text(json.dumps(done))
                    print(i, repr(v), "->", repr(o), f"{sec:.2f}s", flush=True)
        OUT.write_text(json.dumps(done))
        sys.exit(0)
    sys.path.insert(0, str(ROOT / "exp"))
    from e8_llm_oracle import pair_metrics
    from semfd.certify import certify, g3_codes, miss_mass
    from semfd.oracle import total_calls
    c = json.loads(OUT.read_text())
    assert all(v in c["out"] for v in vals), "run --canon first"
    f_llm = {v: label(c["out"][v]) for v in vals}
    ref = {v: ds.oracle["city"][v] for v in vals}
    res = {"model": c["model"], "rows": len(ds.df), "n_values": len(vals), "n_entities": len(set(ref.values())),
           "sec_per_call": {"mean": float(np.mean([c["sec"][v] for v in vals])),
                            "p50": float(np.median([c["sec"][v] for v in vals]))},
           "agreement": pair_metrics(vals, ref, f_llm),
           "agreement_layer1_baseline": pair_metrics(vals, ref, {v: v for v in vals}), "fds": []}
    fds = [(x, y) for x, y in ds.fds if "city" in (x, y)]
    attrs = ds.attrs()
    ent_code = ds.entity_codes(attrs)
    oracle_llm = dict(ds.oracle)
    oracle_llm["city"] = f_llm
    llm_ds = type(ds)(ds.name, ds.df, ds.exact, oracle_llm, fds, ds.meta)
    ent_llm = llm_ds.entity_codes(attrs)
    af = a.alpha / len(fds)
    for s in range(a.seeds):
        orcs = llm_ds.oracles()
        for x, y in fds:
            c0 = orcs["city"].calls
            r = certify(attrs[x], attrs[y], orcs[x], orcs[y], 0.9, a.delta, af,
                        np.random.default_rng(zlib.crc32(f"e14|{s}|{x}|{y}".encode())), nu_bar=a.nu_bar)
            gl = g3_codes(ent_llm[x][attrs[x].codes], ent_llm[y][attrs[y].codes])
            gc = g3_codes(ent_code[x][attrs[x].codes], ent_code[y][attrs[y].codes])
            nu = miss_mass(attrs[x], attrs[y], ent_llm[x], ent_llm[y], 0.9)
            res["fds"].append({"seed": s, "fd": f"{x}->{y}", "certified": r["certified"], "ub": r["ub"],
                               "city_calls": orcs["city"].calls - c0, "g3_llm": float(gl), "g3_code": float(gc),
                               "nu_llm": float(nu)})
        res.setdefault("run_city_calls", []).append(orcs["city"].calls)
        res.setdefault("run_calls", []).append(total_calls(orcs))
    res["canon_all_city"] = len(vals)
    (ROOT / "results/icde27/e14_llm_tax_city.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res["agreement"]), res["run_city_calls"], flush=True)
    for f in res["fds"]:
        print(f, flush=True)
