"""Regressions for the 10-29 audit (CHECK.md H01, H05, M03, L01, L02): FastRFD wrapper, embedding cache
manifest, empty relations, composite separator."""
import importlib
import json
import os
import stat
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "exp"))


def _b2(monkeypatch, tmp_path, java=None):
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "nohome")      # no ~/opt/jdk-21* here
    if java:
        monkeypatch.setenv("FASTRFD_JAVA", str(java))
    else:
        monkeypatch.delenv("FASTRFD_JAVA", raising=False)
    import b2_fastrfd
    return importlib.reload(b2_fastrfd)


def test_fastrfd_imports_without_local_jdk(monkeypatch, tmp_path):
    m = _b2(monkeypatch, tmp_path, java=tmp_path / "java")              # H01: override, no ~/opt: import must work
    assert callable(m.java_cmd)


def test_fastrfd_nonzero_exit_raises(monkeypatch, tmp_path):
    java = tmp_path / "java"
    java.write_text("#!/bin/sh\necho boom >&2\nexit 3\n")
    java.chmod(java.stat().st_mode | stat.S_IEXEC)
    jar = tmp_path / "FastRFD.jar"
    jar.write_text("")
    monkeypatch.setenv("FASTRFD_JAR", str(jar))
    m = _b2(monkeypatch, tmp_path, java=java)
    df = pd.DataFrame({"a": ["x", "y"], "b": ["1", "2"]})
    with pytest.raises(RuntimeError, match="exited with 3"):
        m.run_fastrfd(df, {"a": True, "b": True}, 0.0, 60, log=tmp_path / "out.gz")
    assert (tmp_path / "out.gz").exists()


def test_fastrfd_parser_keeps_empty_lhs(monkeypatch, tmp_path):
    m = _b2(monkeypatch, tmp_path, java=tmp_path / "java")
    out = "\n".join(["[a(<= 0.0)] --> [b(<=1.0)]",
                     "[a(<= 0.0)], [c(<= 1.0)] --> [b(<=1.0)]",          # two-attribute LHS: not unary
                     " --> [state(<=3.0)]"])                             # empty LHS (H05)
    found, empty = m.parse_output(out)
    assert found == {("a", "b")} and empty == {"state"}


def test_embedding_manifest_refuses_other_device(monkeypatch, tmp_path):
    import semfd.proxy as proxy
    monkeypatch.setattr(proxy, "CACHE", tmp_path)
    monkeypatch.setenv("SEMFD_DEVICE", "cpu")
    proxy._check_manifest(proxy.EMB_MODEL)                                # first use records the settings
    man = json.loads((tmp_path / "manifest.json").read_text())[proxy.EMB_MODEL]
    assert man["device"] == "cpu" and man["revision"] != "main"
    monkeypatch.setenv("SEMFD_DEVICE", "cuda")
    with pytest.raises(RuntimeError, match="was built with"):
        proxy._check_manifest(proxy.EMB_MODEL)


def test_g3_rejects_empty_relation():
    from semfd.certify import g3_codes
    with pytest.raises(ValueError):
        g3_codes(np.array([], int), np.array([], int))
    assert g3_codes(np.array([0, 0, 1]), np.array([0, 1, 1])) == pytest.approx(1 / 3)


def test_composite_rejects_separator_in_values():
    from semfd.composite import SEP, CompositeAttr
    from semfd.proxy import Attr
    from semfd.proxy import layer1
    assert SEP not in layer1(f"x{SEP}y")             # Layer-1 treats the separator as whitespace, so Attr values never contain it
    a = Attr("a", pd.Series(["xy", "z"]), exact=True)
    b = Attr("b", pd.Series(["1", "2"]), exact=True)
    a.vals = [f"x{SEP}y", "z"]                        # a hand-built attribute that bypasses Layer-1
    with pytest.raises(ValueError, match="separator"):
        CompositeAttr([a, b])
