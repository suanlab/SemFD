"""Audit regressions for exact sample caps and zero-observation reporting."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
from semfd.certify import certify
from semfd.proxy import Attr
from semfd.oracle import Canonicalizer

def args():
    a=Attr("x",pd.Series(["a","b"]),exact=True)
    b=Attr("y",pd.Series(["c","d"]),exact=True)
    return (a,b,Canonicalizer(lambda v:v,free=True),Canonicalizer(lambda v:v,free=True),.9,.05,.05,np.random.default_rng(0))

def test_sample_cap_is_not_rounded_up():
    for cap in (1,99,101):
        r=certify(*args(),max_n=cap,batch=100)
        assert r["samples"] <= cap

def test_no_observations_are_not_fabricated():
    for kw in ({"max_n":0},{"max_calls":0}):
        r=certify(*args(),**kw)
        assert r["samples"]==0 and r["mean"] is None and not r["certified"]
