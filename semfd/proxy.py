"""Cheap proxies for one attribute: Layer-1 normalisation, ANN-style top-k
neighbours (char-3gram TF-IDF and/or sentence embedding), rapidfuzz edge
rescoring and threshold partitions pi(theta). Proxies never define truth;
they only build the repair witness (pi, rep, N)."""

import hashlib
import time
from pathlib import Path

import numpy as np
from rapidfuzz.distance import Indel
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from sklearn.feature_extraction.text import TfidfVectorizer

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "results/cache/emb"
EMB_MODEL = "BAAI/bge-small-en-v1.5"


def layer1(v):
    return " ".join(str(v).strip().lower().strip(".").split())


def embed(vals, model=EMB_MODEL):
    """Normalised embeddings with an on-disk cache keyed by (model, values)."""
    key = hashlib.sha1((model + "\x00" + "\x00".join(vals)).encode()).hexdigest()[:20]
    f = CACHE / f"{key}.npy"
    if f.exists():
        return np.load(f)
    import sys
    sys.path.insert(0, str(ROOT))
    from embedding_backend import embed as _embed, set_model
    set_model(model)
    E = np.asarray(_embed(list(vals)), dtype=np.float32)
    CACHE.mkdir(parents=True, exist_ok=True)
    np.save(f, E)
    return E


def topk_dense(E, k, batch=4096):
    n = len(E)
    out = np.empty((n, k), dtype=np.int64)
    for s in range(0, n, batch):
        S = E[s:s + batch] @ E.T
        S[np.arange(len(S)), np.arange(s, s + len(S))] = -np.inf
        out[s:s + batch] = np.argpartition(-S, k, axis=1)[:, :k]
    return out


def topk_tfidf(vals, k, batch=4096):
    M = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 3)).fit_transform(vals)
    n = M.shape[0]
    out = np.empty((n, k), dtype=np.int64)
    MT = M.T.tocsr()
    for s in range(0, n, batch):
        S = (M[s:s + batch] @ MT).toarray()
        S[np.arange(len(S)), np.arange(s, s + len(S))] = -np.inf
        out[s:s + batch] = np.argpartition(-S, k, axis=1)[:, :k]
    return out


SCALE_N = 30000      # above this many distinct values, use approximate (HNSW) top-k


def topk_ann(E, k):
    """Approximate inner-product top-k with a faiss HNSW index (falls back to
    exact batched matmul if faiss is unavailable)."""
    try:
        import faiss
    except ImportError:
        return topk_dense(E, k)
    E = np.ascontiguousarray(E, dtype=np.float32)
    idx = faiss.IndexHNSWFlat(E.shape[1], 32, faiss.METRIC_INNER_PRODUCT)
    idx.hnsw.efConstruction, idx.hnsw.efSearch = 80, 64
    idx.add(E)
    _, I = idx.search(E, k + 1)
    out = np.empty((len(E), k), dtype=np.int64)
    for i, row in enumerate(I):
        row = row[(row != i) & (row >= 0)][:k]
        out[i, :len(row)] = row
        out[i, len(row):] = row[0] if len(row) else i
    return out


def tfidf_dense(vals, dim=128, seed=0):
    """char-3gram TF-IDF reduced by truncated SVD, L2-normalised (for ANN)."""
    from sklearn.decomposition import TruncatedSVD
    M = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 3)).fit_transform(vals)
    Z = TruncatedSVD(dim, random_state=seed).fit_transform(M).astype(np.float32)
    return Z / np.maximum(np.linalg.norm(Z, axis=1, keepdims=True), 1e-9)


class Attr:
    """One attribute of a table.

    vals   distinct Layer-1 values (index = value code)
    codes  per-tuple value code
    nbrs   per value code, candidate neighbour codes N(x)
    edges  (src, dst, score) proxy edges for partitions
    proxy  'tfidf' | 'emb' | 'hybrid' (neighbours from both; score = mean of
           Indel ratio and cosine) | 'edit' (TF-IDF neighbours, Indel score)
    exact  type tag: identifier-like attribute, compared by Layer-1 equality
    """

    def __init__(self, name, series, exact=False, proxy="hybrid", k=5):
        t0 = time.perf_counter()
        self.name, self.exact, self.proxy = name, exact, proxy
        surf = [layer1(v) for v in series]
        self.vals = sorted(set(surf))
        idx = {v: i for i, v in enumerate(self.vals)}
        self.codes = np.fromiter((idx[v] for v in surf), np.int64, len(surf))
        n = len(self.vals)
        self.nbrs = [np.array([], np.int64)] * n
        self.edges = (np.array([], np.int64),) * 2 + (np.array([]),)
        if not exact and n >= 3:
            kk = min(k, n - 1)
            parts, E = [], None
            big = n > SCALE_N
            if proxy in ("tfidf", "hybrid", "edit"):
                parts.append(topk_ann(tfidf_dense(self.vals), kk) if big else topk_tfidf(self.vals, kk))
            if proxy in ("emb", "hybrid"):
                E = embed(self.vals)
                parts.append(topk_ann(E, kk) if big else topk_dense(E, kk))
            nb = np.concatenate(parts, 1)
            self.nbrs = [np.unique(r) for r in nb]
            src = np.repeat(np.arange(n), nb.shape[1])
            dst = nb.ravel()
            if proxy == "emb":
                score = np.clip((E[src] * E[dst]).sum(1), 0, 1)
            elif proxy == "tfidf":                      # char-3gram TF-IDF cosine on the edges
                M = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 3)).fit_transform(self.vals)
                score = np.asarray(M[src].multiply(M[dst]).sum(1)).ravel()
            else:
                ratio = np.fromiter((Indel.normalized_similarity(self.vals[a], self.vals[b])
                                     for a, b in zip(src, dst)), float, len(src))
                score = ratio if E is None else (ratio + np.clip((E[src] * E[dst]).sum(1), 0, 1)) / 2
            self.edges = (src, dst, score)
        self.build_sec = time.perf_counter() - t0

    def partition(self, theta):
        n = len(self.vals)
        if self.exact or len(self.edges[0]) == 0:
            return np.arange(n)
        s, d, h = self.edges
        m = h >= theta
        A = coo_matrix((np.ones(m.sum()), (s[m], d[m])), shape=(n, n))
        return connected_components(A, directed=False)[1]
