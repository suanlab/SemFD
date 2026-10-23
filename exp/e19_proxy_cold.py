"""E19 companion: proxy-index build time for NDC with an EMPTY embedding cache (cold), against the cached build
the E19 certify arm measured. Same loader and proxy as the certify arm; the on-disk embedding cache is redirected to
a fresh temporary directory, so every embedding is computed. Run after E19 (not concurrently) to keep the load alike.
Output: results/icde27/e19_proxy_cold.json
"""

import json
import os
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import semfd.proxy as proxy  # noqa: E402
from semfd.data import ndc  # noqa: E402


def main(reps=3):
    ds = ndc(seed=0, near_miss=())
    cold, warm = [], []
    for _ in range(reps):
        with tempfile.TemporaryDirectory() as d:
            proxy.CACHE = Path(d)
            t = time.perf_counter()
            ds.attrs()
            cold.append(time.perf_counter() - t)
            t = time.perf_counter()
            ds.attrs()
            warm.append(time.perf_counter() - t)
    res = {"cold_sec": cold, "cached_sec": warm, "threads": os.environ.get("OMP_NUM_THREADS"),
           "loadavg": os.getloadavg()}
    (ROOT / "results/icde27/e19_proxy_cold.json").write_text(json.dumps(res, indent=1))
    print(res)


if __name__ == "__main__":
    main()
