"""Injected probe columns (near-miss `<src>_e<k>`, source conflict `<src>_src<k>`): one definition for all scripts."""
import re

PROBE = re.compile(r"_(e|src)\d+$")


def is_probe_attr(a):
    return bool(PROBE.search(a))


def base_attr(a):
    """Source attribute of a probe column (identity for ordinary attributes)."""
    return PROBE.sub("", a)


def is_probe_fd(fd):
    """'X->Y' string: true if either side is a probe column."""
    return any(is_probe_attr(side) for side in fd.split("->"))
