"""
embedding_backend.py — sentence-embedding loader used by semfd.proxy (embed(), set_model()).

HISTORICAL NOTE (2026-10-15): the "Week-6 gate" hypothesis below was tested in E6/E6b and REFUTED
(embeddings are a poor definition of equality; results/e6/). The project now treats similarities only as
proxies; this module is kept for its embed() cache and the --selftest harness. The original header follows.

embedding_backend.py — Week-6 hypothesis-gate harness (GPU office machine).

THE HYPOTHESIS (working doc, Wk-6 gate):
  An embedding similarity backend can SIMULTANEOUSLY
    (P) merge true synonyms:        sim("NYC", "New York")     >= 1 - eps
    (S) separate distinct entities:  sim("IRAN", "IRAQ")       <  1 - eps
  whereas the edit-distance backend provably cannot (Theorem/Prop 3:
  edit-sim(IRAN,IRNA)=edit-sim(IRAN,IRAQ)=0.75 — no threshold separates).

This script is the drop-in semantic backend for semantic_fd_toy.py /
semantic_fd_tpch.py. It replaces the SequenceMatcher similarity inside
canonicalize() with sentence-embedding cosine.

RUN ORDER ON THE GPU BOX (see GPU_EXPERIMENT_GUIDE.md):
  1. python embedding_backend.py --selftest      # P/S gate, no FD logic
  2. patch canonicalize() to import sim_embed     # one-line seam
  3. rerun semantic_fd_tpch.py                    # full FD accuracy
"""

import argparse
import numpy as np

# ---- model loaded lazily so --help works without torch installed ----------
_MODEL = None
_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
_CACHE = {}


def set_model(model_name):
    """Select the embedding model; resets the loaded model and the cache."""
    global _MODEL, _MODEL_NAME
    if model_name != _MODEL_NAME:
        _MODEL, _MODEL_NAME = None, model_name
        _CACHE.clear()


def _load(model_name):
    global _MODEL
    set_model(model_name)
    if _MODEL is None:
        from sentence_transformers import SentenceTransformer  # GPU box only
        import torch
        dev = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[embedding_backend] loading {model_name} on {dev}")
        _MODEL = SentenceTransformer(model_name, device=dev)
    return _MODEL


def embed(texts, model_name=None):
    m = _load(model_name or _MODEL_NAME)
    todo = [t for t in texts if t not in _CACHE]
    if todo:
        vecs = m.encode(todo, normalize_embeddings=True,
                        convert_to_numpy=True, batch_size=256)
        _CACHE.update(dict(zip(todo, vecs)))
    return np.array([_CACHE[t] for t in texts])


def sim_embed(a: str, b: str) -> float:
    """Cosine of normalized embeddings -> [−1,1]; clamp to [0,1].
    Drop-in replacement for SequenceMatcher(None,a,b).ratio()."""
    if a == b:
        return 1.0
    va, vb = embed([a, b])
    return float(max(0.0, np.dot(va, vb)))


# ----------------------------------------------------------------- self-test
SYNONYM_PAIRS = [          # must MERGE  (high sim)
    ("NYC", "New York"), ("NYC", "New York City"),
    ("USA", "United States"), ("UK", "United Kingdom"),
    ("LA", "Los Angeles"), ("SF", "San Francisco"),
]
DISTINCT_PAIRS = [         # must SEPARATE (low sim) — the edit-distance trap
    ("IRAN", "IRAQ"), ("Austria", "Australia"),
    ("Slovakia", "Slovenia"), ("Niger", "Nigeria"),
    ("Sweden", "Switzerland"), ("Chile", "China"),
]


def selftest(model_name, eps_grid=(0.2, 0.3, 0.4, 0.5)):
    set_model(model_name)
    syn = [(a, b, sim_embed(a, b)) for a, b in SYNONYM_PAIRS]
    dis = [(a, b, sim_embed(a, b)) for a, b in DISTINCT_PAIRS]
    print("\n--- synonym pairs (want HIGH sim) ---")
    for a, b, s in syn:
        print(f"  {a:>6} ~ {b:<16} sim={s:.3f}")
    print("--- distinct pairs (want LOW sim) ---")
    for a, b, s in dis:
        print(f"  {a:>9} ~ {b:<13} sim={s:.3f}")

    syn_min = min(s for *_, s in syn)
    dis_max = max(s for *_, s in dis)
    print(f"\nmin synonym sim = {syn_min:.3f}   "
          f"max distinct sim = {dis_max:.3f}")
    separable = syn_min > dis_max
    print(f"GLOBAL SEPARABILITY (a single eps splits all): "
          f"{'YES' if separable else 'NO'}  "
          f"(gap = {syn_min - dis_max:+.3f})")

    print("\nPer-eps confusion (merge if sim >= 1-eps):")
    print(f"{'eps':>5} | {'thr':>5} | {'syn merged':>10} | {'dis WRONGLY merged':>18}")
    for eps in eps_grid:
        thr = 1 - eps
        sm = sum(s >= thr for *_, s in syn)
        dm = sum(s >= thr for *_, s in dis)
        print(f"{eps:>5} | {thr:>5.2f} | {sm:>3}/{len(syn):<6} | {dm:>3}/{len(dis):<14}")

    print("\nHYPOTHESIS GATE:")
    if separable:
        print("  PASS — embeddings achieve P and S together. "
              "Core thesis (C1) empirically supported.")
    else:
        print("  PARTIAL/FAIL — no global threshold separates. "
              "Escalate to context-aware equivalence (Def 8, working doc) "
              "and report the per-eps tradeoff curve as the finding.")
    return separable


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2")
    args = ap.parse_args()
    if args.selftest:
        selftest(args.model)
    else:
        print("Use --selftest, or import sim_embed into canonicalize().")
