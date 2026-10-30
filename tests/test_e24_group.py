"""E24 sanity (prereg_e24_group_baseline_2026-10-31.md): the entity-group estimator's tuple average is exactly g3."""
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "exp"))

from e24_group_baseline import Groups  # noqa: E402
from semfd.certify import g3_codes  # noqa: E402
from semfd.oracle import Canonicalizer  # noqa: E402


def _attr(vals, codes):
    return SimpleNamespace(vals=vals, codes=np.asarray(codes))


@pytest.mark.parametrize("seed", range(5))
def test_group_mean_equals_g3(seed):
    rng = np.random.default_rng(seed)
    xv = [f"x{i}" for i in range(30)]
    yv = [f"y{i}" for i in range(12)]
    xent = {v: f"E{rng.integers(0, 8)}" for v in xv}           # 30 spellings of 8 entities
    yent = {v: f"F{rng.integers(0, 4)}" for v in yv}
    n = 400
    xc, yc = rng.integers(0, len(xv), n), rng.integers(0, len(yv), n)
    ax, ay = _attr(xv, xc), _attr(yv, yc)
    fx = Canonicalizer.from_table(xent, inverse=True)
    fy = Canonicalizer.from_table(yent, inverse=True)
    grp = Groups(ax, ay)
    mean = np.mean([grp.b_value(int(c), fx, fy) for c in xc])
    xe = np.array([int(xent[v][1:]) for v in xv])[xc]
    ye = np.array([int(yent[v][1:]) for v in yv])[yc]
    assert mean == pytest.approx(g3_codes(xe, ye), abs=1e-12)
    assert fx.calls_inverse <= 8 and fy.calls_forward <= len(yv)
