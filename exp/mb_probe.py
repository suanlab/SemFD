"""Feasibility probe for MusicBrainz (Leipzig DAPO 200K) as a fourth dataset (paper Sec. VI, threats to validity).
Records why it is not used: after dropping nulls most artist groups are tiny and the only alias-rich
attribute (language) has no candidate FD near the tolerance. Output: results/icde27/mb_probe.json"""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from semfd.certify import g3_codes  # noqa: E402
from semfd.data import MB_NULL  # noqa: E402
from semfd.proxy import layer1  # noqa: E402

m = pd.read_csv(ROOT / "data/musicbrainz/mb200k.csv.dapo", dtype=str, keep_default_na=False)
for a in ("artist", "language", "album", "year"):
    m[a] = m[a].map(layer1)
d = m[~m[["artist", "language"]].isin(MB_NULL).any(axis=1)].reset_index(drop=True)
gs = d.groupby("artist").size()
codes = lambda s: pd.factorize(s)[0]
out = {"rows_total": len(m), "rows_artist_language_nonnull": len(d), "artists": int(d.artist.nunique()),
       "artist_singleton_share": float((gs == 1).sum() / len(gs)),
       "languages_distinct": int(d.language.nunique()),
       "g3_raw_artist_to_language": float(g3_codes(codes(d.artist), codes(d.language))),
       "g3_raw_album_to_artist": float(g3_codes(codes(m[m.album != ''].album), codes(m[m.album != ''].artist)))}
(ROOT / "results/icde27/mb_probe.json").write_text(json.dumps(out, indent=1))
print(out)
