"""Dataset interface for experiments.

A Dataset is a table plus, per attribute, a type tag (exact or tolerant) and a
ground-truth oracle table {Layer-1 value -> entity id} (missing => the
attribute is compared by Layer-1 equality, i.e. f = identity), and a list of
candidate FDs (lhs, rhs) with single attributes on each side. Truth of a
candidate is computed from the oracle, never hand-labelled.
"""

import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from .certify import g3_codes
from .oracle import Canonicalizer
from .proxy import Attr, layer1

ROOT = Path(__file__).resolve().parents[1]


@dataclass
class Dataset:
    name: str
    df: object                       # pandas DataFrame
    exact: dict                      # attr -> bool
    oracle: dict                     # attr -> {layer1 value: entity id}
    fds: list = field(default_factory=list)
    meta: dict = field(default_factory=dict)
    exclude: set = field(default_factory=set)   # candidate pairs true by construction of the oracle (not evaluated)

    def attrs(self, proxy="hybrid", k=5):
        return {a: Attr(a, self.df[a], exact=self.exact[a], proxy=proxy, k=k) for a in self.exact}

    def oracles(self, inverse=False):
        """One Canonicalizer per distinct oracle table: probe copies (_e2, _src8)
        share their source attribute's table and therefore its cache and cost."""
        out, by_table = {}, {}
        for a in self.exact:
            if a in self.oracle:
                key = id(self.oracle[a])
                if key not in by_table:
                    by_table[key] = Canonicalizer.from_table(self.oracle[a], inverse=inverse, name=a)
                out[a] = by_table[key]
            else:
                out[a] = Canonicalizer(lambda v: v, (lambda e: [e]) if inverse else None, name=a,
                                       free=self.exact[a])
        return out

    def entity_codes(self, attrs):
        """Per value code, an integer entity id (evaluation only)."""
        out = {}
        for a, at in attrs.items():
            tab = self.oracle.get(a)
            ents = [tab[v] if tab else v for v in at.vals]
            eid = {e: i for i, e in enumerate(dict.fromkeys(ents))}
            out[a] = np.array([eid[e] for e in ents])
        return out

    def canon_all_cost(self, attrs, names=None):
        """Canonicalize-all cost: distinct values per distinct oracle table
        (probe copies draw their values from the source domain)."""
        vals = {}
        for a in (names or attrs):
            if self.exact[a] or a not in self.oracle:
                continue
            vals.setdefault(id(self.oracle[a]), set()).update(attrs[a].vals)
        return int(sum(len(v) for v in vals.values()))

    def truth(self, attrs, ent):
        return {(x, y): g3_codes(ent[x][attrs[x].codes], ent[y][attrs[y].codes])
                for x, y in self.fds}


def all_pairs(attrs, skip=()):
    return [(x, y) for x in attrs for y in attrs if x != y and (x, y) not in skip]


# ---------------------------------------------------------------- loaders
def inject_errors(df, oracle, src, rate, seed, name=None):
    """Copy attribute `src` into `name` and replace a `rate` fraction of cells by
    a surface value of a DIFFERENT entity drawn from the column itself. Errors
    are spread over many small X-groups: the regime where sample-only g3
    estimates are biased low (near-miss FDs; paper Sec. VI)."""
    rng = np.random.default_rng(seed)
    name = name or f"{src}_e{int(round(rate * 100))}"
    col = df[src].to_numpy(dtype=object).copy()
    ent = np.array([oracle[src][layer1(v)] for v in col], dtype=object)
    hit = np.flatnonzero(rng.random(len(col)) < rate)
    for i in hit:
        for _ in range(50):
            j = rng.integers(len(col))
            if ent[j] != ent[i]:
                col[i] = col[j]
                break
    df[name] = col
    oracle[name] = oracle[src]
    return name


def inject_source_conflict(df, oracle, x, ysrc, target, seed, name=None):
    """Two-source integration conflict: for randomly chosen entities of X, every
    tuple whose X surface is NOT the entity's majority surface gets one
    alternative Y value (consistent per (entity, surface)). Each proxy cluster
    of a variant surface is then internally consistent, so a modal-rep
    estimator without the cross-cluster audit (B9) cannot see the violation;
    the true g3 is the conflicting fraction (~target)."""
    rng = np.random.default_rng(seed)
    name = name or f"{ysrc}_src{int(round(target * 100))}"
    xs = df[x].map(layer1).to_numpy(dtype=object)
    xe = np.array([oracle[x][v] for v in xs], dtype=object)
    col = df[ysrc].to_numpy(dtype=object).copy()
    yo = oracle.get(ysrc)                       # None: exact attribute (identity)
    ye = np.array([yo[layer1(v)] if yo else layer1(v) for v in col], dtype=object)
    import pandas as pd
    maj = pd.Series(xs).groupby(xe).agg(lambda s: s.value_counts().index[0]).to_dict()
    variant = np.array([xs[i] != maj[xe[i]] for i in range(len(xs))])
    ents = list(dict.fromkeys(xe[variant]))
    rng.shuffle(ents)
    budget, chosen = target * len(col), set()
    cnt = pd.Series(variant).groupby(xe).sum().to_dict()
    for e in ents:
        if budget <= 0:
            break
        chosen.add(e)
        budget -= cnt[e]
    alt = {}
    for i in np.flatnonzero(variant):
        if xe[i] in chosen:
            key = (xe[i], xs[i])
            if key not in alt:
                while True:
                    j = rng.integers(len(col))
                    if ye[j] != ye[i]:
                        alt[key] = col[j]
                        break
            col[i] = alt[key]
    df[name] = col
    if yo:
        oracle[name] = yo
    return name


def geonames(n_cities=1000, rho=0.2, seed=0, near_miss=(0.02, 0.08), conflict=(0.08,),
             conflict_exact=(0.08,), source="cities15000.txt"):
    sys.path[:0] = [str(ROOT), str(ROOT / "pilot")]
    import p0b_geonames
    from p0b_geonames import FDS, TYPES, make_table
    p0b_geonames.CITIES = source
    df, oracle = make_table(n_cities, rho=rho, seed=seed)
    oracle = {a: {layer1(k): v for k, v in t.items()} for a, t in oracle.items()}
    exact, fds = dict(TYPES), list(FDS)
    for r in near_miss:
        a = inject_errors(df, oracle, "country", r, seed + 1000)
        exact[a] = False
        fds.append(("city", a))
    for r in conflict:
        a = inject_source_conflict(df, oracle, "city", "country", r, seed + 2000)
        exact[a] = False
        fds.append(("city", a))
    for r in conflict_exact:                    # exact RHS: raw methods can no longer see it
        a = inject_source_conflict(df, oracle, "city", "tz", r, seed + 3000)
        exact[a] = True
        fds.append(("city", a))
    fds.append(("city", "tz"))
    return Dataset(f"geonames{n_cities}", df, exact, oracle, fds,
                   {"n_cities": n_cities, "rho": rho, "seed": seed, "near_miss": list(near_miss),
                    "conflict": list(conflict),
                    "conflict_exact": list(conflict_exact)})


# ---------------------------------------------------------------- Raha Tax
CITY_ABBR = [("SAINT", "ST"), ("FORT", "FT"), ("MOUNT", "MT"), ("NORTH", "N"), ("SOUTH", "S"),
             ("EAST", "E"), ("WEST", "W"), ("PORT", "PT"), ("LAKE", "LK"), ("SPRINGS", "SPGS"),
             ("HEIGHTS", "HTS"), ("CENTER", "CTR"), ("VILLAGE", "VLG"), ("BEACH", "BCH")]


def _abbr_variants(city):
    toks, out = city.split(), []
    for i, t in enumerate(toks):
        for full, ab in CITY_ABBR:
            if t == full:
                out.append(" ".join(toks[:i] + [ab] + toks[i + 1:]))
            elif t == ab:
                out.append(" ".join(toks[:i] + [full] + toks[i + 1:]))
    return out


def tax(rho=0.2, seed=0, n_rows=None, near_miss=(0.02, 0.08)):
    """Raha Tax (200k x 15, BART-generated; github.com/BigDaMa/raha). Truth =
    the clean file (cell-aligned). Its own errors are syntactic only, so we
    inject REAL alias conventions at rate rho per cell: state code <-> full name
    (GeoNames admin1 names) and city-name abbreviations
    (SAINT<->ST, FORT<->FT, ...), plus typos/drops. Variants that collide with
    another entity's surface are rendered clean (oracle stays a function)."""
    import random
    import pandas as pd
    sys.path[:0] = [str(ROOT / "pilot")]
    from p0_data import _drop, _typo
    rng = random.Random(seed)
    d = pd.read_csv(ROOT / "data/tax/dirty.csv", dtype=str, keep_default_na=False)
    c = pd.read_csv(ROOT / "data/tax/clean.csv", dtype=str, keep_default_na=False)
    if n_rows:
        idx = np.random.default_rng(seed).choice(len(d), n_rows, replace=False)
        d, c = d.iloc[idx].reset_index(drop=True), c.iloc[idx].reset_index(drop=True)
    d["zip"] = d["zip"].str.lstrip("0")
    c["zip"] = c["zip"].str.lstrip("0")
    sname = {}
    for line in (ROOT / "data/geonames/admin1CodesASCII.txt").read_text(encoding="utf-8").splitlines():
        f = line.split("\t")
        if f[0].startswith("US."):
            sname[f[0][3:]] = f[2]
    cols = ["f_name", "gender", "area_code", "city", "state", "zip"]
    exact = {"f_name": False, "gender": True, "area_code": True, "city": False, "state": False, "zip": True}
    oracle = {a: {} for a in cols if not exact[a]}
    owner = {a: {layer1(v): layer1(v) for v in c[a].unique()} for a in oracle}   # clean surfaces
    out = {a: d[a].tolist() for a in cols}
    for a in oracle:
        for i, (dv, cv) in enumerate(zip(d[a], c[a])):
            ent = layer1(cv)
            v = dv
            if rng.random() < rho:
                alias = []
                if a == "state" and cv in sname:
                    alias = [sname[cv]]
                elif a == "city":
                    alias = _abbr_variants(cv)
                kinds = ["typo", "drop"] + (["alias"] * 3 if alias else [])
                k = rng.choice(kinds)
                v = rng.choice(alias) if k == "alias" else (_typo(cv, rng) if k == "typo" else _drop(cv, rng))
            key = layer1(v)
            if owner[a].get(key, ent) != ent or oracle[a].setdefault(key, ent) != ent:
                v, key = cv, ent                       # ambiguous variant -> render clean
                oracle[a].setdefault(key, ent)
            out[a][i] = v
    df = pd.DataFrame(out)
    fds = [("zip", "city"), ("zip", "state"), ("area_code", "state"), ("f_name", "gender"),
           ("city", "state"), ("state", "area_code"), ("city", "zip"), ("city", "area_code")]
    ds = Dataset(f"tax{len(df)}", df, exact, oracle, fds,
                 {"rho": rho, "seed": seed, "near_miss": list(near_miss)})
    for r in near_miss:
        a = inject_errors(df, oracle, "city", r, seed + 1000)
        exact[a] = False
        fds.append(("zip", a))
    return ds


# ---------------------------------------------------------------- MusicBrainz
MB_NULL = {"", "null", "unknown", "[multiple languages]", "n/a", "-"}


def cluster_majority_oracle(vals, cids, min_support=3):
    """Value-level oracle from record clusters, as a FUNCTION (not graph
    components, which over-merge): each cluster gets its most frequent surface
    as canonical; a surface v maps to the canonical it co-occurs with most
    often if that happens in >= min_support clusters, else to itself."""
    import pandas as pd
    t = pd.DataFrame({"v": vals, "c": cids})
    canon = t.groupby("c")["v"].agg(lambda s: s.value_counts().index[0])
    t["k"] = t["c"].map(canon)
    cnt = t[t.v != t.k].groupby(["v", "k"]).size().reset_index(name="n")
    cnt = cnt[cnt.n >= min_support].sort_values("n", ascending=False).drop_duplicates("v")
    f = {v: v for v in t.v.unique()}
    f.update(dict(zip(cnt.v, cnt.k)))
    return {v: f.get(f[v], f[v]) for v in f}          # one hop of idempotence


def musicbrainz(size="200", seed=0, near_miss=(0.02, 0.08), min_support=3):
    """Leipzig/Saeedi MusicBrainz DAPO benchmark (CC BY 4.0). Real abbreviation
    aliases (Eng./English) and format variants; oracle per attribute from the
    record clusters (cluster_majority_oracle). Rows with a null in any used
    attribute are dropped."""
    import pandas as pd
    m = pd.read_csv(ROOT / f"data/musicbrainz/mb{size}k.csv.dapo", dtype=str, keep_default_na=False)
    cols = ["artist", "album", "language", "year", "title"]
    for a in cols:
        m[a] = m[a].map(layer1)
    m = m[~m[cols].isin(MB_NULL).any(axis=1)].reset_index(drop=True)
    exact = {"artist": False, "album": False, "language": False, "year": False, "title": False}
    oracle = {a: cluster_majority_oracle(m[a].tolist(), m["CID"].tolist(), min_support) for a in cols}
    df = m[cols].copy()
    fds = [("album", "artist"), ("artist", "language"), ("album", "language"), ("album", "year"),
           ("title", "artist"), ("artist", "album"), ("year", "language"), ("language", "artist"),
           ("title", "album")]
    ds = Dataset(f"musicbrainz{size}k", df, exact, oracle, fds,
                 {"seed": seed, "min_support": min_support, "near_miss": list(near_miss)})
    for r in near_miss:
        a = inject_errors(df, oracle, "artist", r, seed + 1000)
        exact[a] = False
        fds.append(("album", a))
    return ds


# ---------------------------------------------------------------- FDA NDC
def ndc(seed=0, near_miss=(0.02, 0.08)):
    """FDA NDC product directory (data/ndc/x/product.txt from
    accessdata.fda.gov/cder/ndctext.zip). Real labeler-name aliases
    (Wal-Mart/Walmart/Equate, Cardinal Health/Leader, misspellings).
    Oracle for the labeler name = connected component of the labeler-code /
    name bipartite graph, i.e. 'the business that owns these labeler codes'.
    This makes labcode->labeler true BY CONSTRUCTION of the oracle (report as
    such) and can over-merge (repackagers sharing a code); audit required."""
    import pandas as pd
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    p = pd.read_csv(ROOT / "data/ndc/x/product.txt", sep="\t", dtype=str, keep_default_na=False,
                    encoding="latin-1", quoting=3)
    p["labcode"] = p["PRODUCTNDC"].str.split("-").str[0]
    p["labeler"] = p["LABELERNAME"]
    lab = p["labeler"].map(layer1)
    codes = sorted(set(p["labcode"]))
    names = sorted(set(lab))
    ci = {c: i for i, c in enumerate(codes)}
    ni = {n: i + len(codes) for i, n in enumerate(names)}
    e = pd.DataFrame({"c": p["labcode"], "n": lab}).drop_duplicates()
    A = coo_matrix((np.ones(len(e)), (e["c"].map(ci), e["n"].map(ni))), shape=(len(codes) + len(names),) * 2)
    comp = connected_components(A, directed=False)[1]
    oracle = {"labeler": {n: f"firm{comp[ni[n]]}" for n in names}}
    p = p.rename(columns={"APPLICATIONNUMBER": "appno", "PROPRIETARYNAME": "brand",
                          "NONPROPRIETARYNAME": "generic", "MARKETINGCATEGORYNAME": "mktcat",
                          "PRODUCTTYPENAME": "ptype"})
    cols = ["labcode", "labeler", "appno", "brand", "generic", "mktcat", "ptype"]
    df = p[cols].copy()
    exact = {a: a != "labeler" for a in cols}
    fds = [("labcode", "labeler"), ("labeler", "ptype"), ("labeler", "labcode"), ("labeler", "mktcat"),
           ("appno", "labeler"), ("brand", "labeler"), ("generic", "labeler")]
    ds = Dataset(f"ndc{len(df)}", df, exact, oracle, fds, {"seed": seed, "near_miss": list(near_miss)})
    for r in near_miss:
        a = inject_errors(df, oracle, "labeler", r, seed + 1000)
        exact[a] = False
        fds.append(("labcode", a))
    return ds


def gpg(seed=0, years=range(2017, 2026)):
    """UK gender pay gap reports 2017-2025 (gender-pay-gap.service.gov.uk, Open Government Licence;
    data/gpg/gpg<year>.csv). Employer names are recorded by reporting year; the official service sources private/voluntary-sector names from Companies House. One company appears under
    several spellings and, after renames, under different names (natural aliases). Oracle for the
    employer name = its Companies House company number, an identifier assigned outside this data.
    Kept: reports with a company number; names that occur with more than one company number
    (homonyms) are dropped. name<->cn candidates hold by construction and are excluded.
    seed only affects sampling in the experiments (the table is fixed)."""
    import pandas as pd
    fr = []
    for y in years:
        d = pd.read_csv(ROOT / f"data/gpg/gpg{y}.csv", dtype=str, keep_default_na=False)
        d["year"] = str(y)
        fr.append(d)
    d = pd.concat(fr, ignore_index=True)
    d["cn"] = d["CompanyNumber"].str.strip().str.upper()
    d = d[d["cn"] != ""].copy()
    d["name"] = d["EmployerName"]
    key = d["name"].map(layer1)
    homonym = d.groupby(key)["cn"].transform("nunique") > 1
    d = d[~homonym.to_numpy()].copy()
    d["empid"] = d["EmployerId"].str.strip()
    d["postcode"] = d["PostCode"].str.upper().str.replace(" ", "", regex=False)
    d["sic"] = d["SicCodes"].map(lambda s: ",".join(sorted(x.strip() for x in s.replace("\n", ",").split(",") if x.strip())))
    d["size"] = d["EmployerSize"]
    cols = ["name", "cn", "empid", "postcode", "sic", "size", "year"]
    df = d[cols].reset_index(drop=True)
    oracle = {"name": dict(zip(df["name"].map(layer1), df["cn"]))}
    exact = {a: a != "name" for a in cols}
    fds = [("empid", "name"), ("name", "empid"), ("name", "sic"), ("name", "size"), ("name", "postcode"),
           ("postcode", "name"), ("sic", "name")]
    return Dataset(f"gpg{len(df)}", df, exact, oracle, fds, {"seed": seed, "years": [min(years), max(years)],
                                                             "homonym_rows_dropped": int(homonym.sum())},
                   exclude={("name", "cn"), ("cn", "name")})


def companies_house_names():
    """Registered names per company number from the Companies House Free Company Data Product (public register data,
    no licence stated, not redistributed; data/companieshouse/BasicCompanyDataAsOneFile-*.csv): current name and up to ten previous
    names, Layer-1 normalized. A real alias registry whose omissions we do not control."""
    import pandas as pd
    f = sorted((ROOT / "data/companieshouse").glob("BasicCompanyDataAsOneFile-*.csv"))[-1]
    want = {"CompanyName", "CompanyNumber"} | {f"PreviousName_{i}.CompanyName" for i in range(1, 11)}
    out = {}
    for ch in pd.read_csv(f, usecols=lambda c: c.strip() in want, dtype=str, keep_default_na=False, chunksize=500_000):
        ch.columns = [c.strip() for c in ch.columns]
        num = ch["CompanyNumber"].str.strip().str.upper()
        names = [ch[c] for c in ch.columns if c != "CompanyNumber"]
        for i, n in enumerate(num):
            out[n] = {layer1(x.iat[i]) for x in names if x.iat[i]}
    return out, f.name


LOADERS = {"geonames": geonames, "tax": tax, "musicbrainz": musicbrainz, "ndc": ndc, "gpg": gpg}
