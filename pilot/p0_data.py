"""P0 pilot data: TPC-H-style customer/nation table with ground-truth entity identity.

Every surface value carries the id of the real-world entity it denotes, so the
oracle O_A(a, b) = [entity(a) == entity(b)] is known exactly (stand-in for an
ER ground truth / human / LLM judge).

Traps built in (RESEARCH_DIRECTION.md section 1):
  - look-alike distinct nations with different currencies/capitals
    (IRAN/IRAQ, NIGER/NIGERIA, MALI/MALAWI, AUSTRIA/AUSTRALIA,
     SWEDEN/SWITZERLAND, NORTH/SOUTH KOREA, DOMINICA/DOMINICAN REPUBLIC,
     GUINEA/GUINEA-BISSAU)
  - real aliases that syntactic similarity cannot link (USA ~ United States,
    Deutschland ~ Germany, Persia ~ Iran)
  - typos / drops that embeddings cannot link (E6b)
"""

import random

import numpy as np
import pandas as pd

# nation: (region, currency, capital, nation aliases, capital aliases)
NATIONS = {
    "IRAN": ("MIDDLE EAST", "IRR", "Tehran", ["Islamic Republic of Iran", "Persia"], ["Teheran"]),
    "IRAQ": ("MIDDLE EAST", "IQD", "Baghdad", ["Republic of Iraq"], []),
    "EGYPT": ("MIDDLE EAST", "EGP", "Cairo", ["Arab Republic of Egypt"], []),
    "NIGER": ("AFRICA", "XOF", "Niamey", ["Republic of the Niger"], []),
    "NIGERIA": ("AFRICA", "NGN", "Abuja", ["Federal Republic of Nigeria"], []),
    "MALI": ("AFRICA", "XOF", "Bamako", ["Republic of Mali"], []),
    "MALAWI": ("AFRICA", "MWK", "Lilongwe", ["Republic of Malawi"], []),
    "GUINEA": ("AFRICA", "GNF", "Conakry", ["Republic of Guinea"], []),
    "GUINEA-BISSAU": ("AFRICA", "XOF", "Bissau", ["Guinea Bissau"], []),
    "MOROCCO": ("AFRICA", "MAD", "Rabat", ["Kingdom of Morocco"], []),
    "ALGERIA": ("AFRICA", "DZD", "Algiers", [], ["Alger"]),
    "AUSTRIA": ("EUROPE", "EUR", "Vienna", ["Osterreich", "Republic of Austria"], ["Wien"]),
    "AUSTRALIA": ("OCEANIA", "AUD", "Canberra", ["Commonwealth of Australia"], []),
    "SWEDEN": ("EUROPE", "SEK", "Stockholm", ["Sverige", "Kingdom of Sweden"], []),
    "SWITZERLAND": ("EUROPE", "CHF", "Bern", ["Swiss Confederation", "Schweiz"], ["Berne"]),
    "SLOVAKIA": ("EUROPE", "EUR", "Bratislava", ["Slovak Republic"], []),
    "SLOVENIA": ("EUROPE", "EUR", "Ljubljana", ["Republic of Slovenia"], []),
    "GERMANY": ("EUROPE", "EUR", "Berlin", ["Deutschland", "Federal Republic of Germany"], []),
    "FRANCE": ("EUROPE", "EUR", "Paris", ["French Republic"], []),
    "NETHERLANDS": ("EUROPE", "EUR", "Amsterdam", ["Holland", "The Netherlands"], []),
    "UNITED KINGDOM": ("EUROPE", "GBP", "London", ["UK", "Great Britain", "Britain"], []),
    "RUSSIA": ("EUROPE", "RUB", "Moscow", ["Russian Federation"], ["Moskva"]),
    "CHINA": ("ASIA", "CNY", "Beijing", ["PRC", "People's Republic of China"], ["Peking"]),
    "JAPAN": ("ASIA", "JPY", "Tokyo", ["Nippon"], []),
    "INDIA": ("ASIA", "INR", "New Delhi", ["Bharat", "Republic of India"], []),
    "INDONESIA": ("ASIA", "IDR", "Jakarta", ["Republic of Indonesia"], []),
    "SOUTH KOREA": ("ASIA", "KRW", "Seoul", ["Republic of Korea", "ROK"], []),
    "NORTH KOREA": ("ASIA", "KPW", "Pyongyang", ["DPRK", "Democratic People's Republic of Korea"], []),
    "UNITED STATES": ("AMERICA", "USD", "Washington", ["USA", "US", "United States of America"], ["Washington DC"]),
    "CANADA": ("AMERICA", "CAD", "Ottawa", [], []),
    "BRAZIL": ("AMERICA", "BRL", "Brasilia", ["Brasil"], []),
    "ARGENTINA": ("AMERICA", "ARS", "Buenos Aires", ["Argentine Republic"], []),
    "CHILE": ("AMERICA", "CLP", "Santiago", ["Republic of Chile"], []),
    "PERU": ("AMERICA", "PEN", "Lima", ["Republic of Peru"], []),
    "DOMINICA": ("AMERICA", "XCD", "Roseau", ["Commonwealth of Dominica"], []),
    "DOMINICAN REPUBLIC": ("AMERICA", "DOP", "Santo Domingo", ["Dominican Rep"], []),
}
REGION_ALIASES = {"MIDDLE EAST": ["Mideast", "Near East"], "AMERICA": ["Americas"],
                  "ASIA": [], "EUROPE": [], "AFRICA": [], "OCEANIA": []}
SEGMENTS = ["AUTOMOBILE", "BUILDING", "FURNITURE", "HOUSEHOLD", "MACHINERY"]
# sales territories: most cover one nation, some cover a look-alike pair
PAIRED = [("IRAN", "IRAQ"), ("NIGER", "NIGERIA"), ("MALI", "MALAWI"),
          ("SLOVAKIA", "SLOVENIA"), ("SOUTH KOREA", "NORTH KOREA"),
          ("GUINEA", "GUINEA-BISSAU")]

# attribute -> type tag (Def 1): exact attributes are never similarity-merged
TYPES = {"nation": "tolerance", "region": "tolerance", "capital": "tolerance",
         "currency": "exact", "territory": "exact", "segment": "exact"}

# candidate FDs with oracle-level truth
CANDIDATES = [
    ("nation", "region", True),
    ("nation", "currency", True),
    ("nation", "capital", True),
    ("capital", "nation", True),
    ("currency", "region", True),
    ("territory", "nation", False),
    ("currency", "nation", False),
    ("region", "currency", False),
    ("segment", "nation", False),
]


def _territories():
    terr, k = {}, 0
    paired = {n for p in PAIRED for n in p}
    for a, b in PAIRED:
        terr[a] = terr[b] = f"T{k:02d}"
        k += 1
    for n in NATIONS:
        if n not in paired:
            terr[n] = f"T{k:02d}"
            k += 1
    return terr


def _typo(s, rng):
    if len(s) < 4:
        return s
    i = rng.randrange(len(s) - 1)
    return s[:i] + s[i + 1] + s[i] + s[i + 2:]


def _drop(s, rng):
    if len(s) < 4:
        return s
    i = rng.randrange(len(s))
    return s[:i] + s[i + 1:]


def _surface(clean, aliases, rho, rng):
    """Render a clean value with probability rho of a variant: alias, typo,
    drop, or pure formatting noise (removed by Layer-1 normalization)."""
    if rng.random() >= rho:
        v = clean
    else:
        kinds = ["typo", "drop", "format"] + (["alias", "alias"] if aliases else [])
        k = rng.choice(kinds)
        if k == "alias":
            v = rng.choice(aliases)
        elif k == "typo":
            v = _typo(clean, rng)
        elif k == "drop":
            v = _drop(clean, rng)
        else:
            v = clean
    style = rng.random()
    if style < 0.15:
        v = v.lower()
    elif style < 0.25:
        v = v.title()
    elif style < 0.30:
        v = " " + v + "."
    return v


def make_table(n_rows=3000, rho=0.2, err=0.01, seed=0):
    """Returns (df of surface values, oracle: attr -> {layer1(surface): entity})."""
    rng = random.Random(seed)
    nprng = np.random.default_rng(seed)
    names = list(NATIONS)
    p = 1.0 / np.arange(1, len(names) + 1) ** 0.6       # mild Zipf popularity
    nprng.shuffle(p)
    p /= p.sum()
    terr = _territories()
    oracle = {a: {} for a in TYPES}
    rows = []
    for _ in range(n_rows):
        n = names[nprng.choice(len(names), p=p)]
        region, cur, cap, n_al, c_al = NATIONS[n]
        if rng.random() < err:                      # genuine dependency error
            cur = rng.choice([c for c in {v[1] for v in NATIONS.values()} if c != cur])
        row = {
            "nation": (_surface(n, n_al, rho, rng), n),
            "region": (_surface(region, REGION_ALIASES[region], rho, rng), region),
            "capital": (_surface(cap, c_al, rho, rng), cap),
            "currency": (cur, cur),
            "territory": (terr[n], terr[n]),
            "segment": (rng.choice(SEGMENTS), None),
        }
        row["segment"] = (row["segment"][0], row["segment"][0])
        out = {}
        for a, (surf, ent) in row.items():
            # oracle is keyed by the Layer-1 form; if a variant collides with
            # another entity's value it is genuinely ambiguous -- render clean
            if oracle[a].setdefault(layer1(surf), ent) != ent:
                surf = ent
            out[a] = surf
        rows.append(out)
    return pd.DataFrame(rows), oracle


def layer1(v):
    return " ".join(str(v).strip().lower().strip(".").split())
