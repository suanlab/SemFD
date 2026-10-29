"""Certificates under updates (paper Sec. IV, "Under change").

If r' arises from r (N tuples) by deleting D and inserting I tuples in total since
certification, and the oracle is unchanged, then an optimal repair of r keeps
(1 - g3)N tuples of which at least (1 - g3)N - D survive in r' with unchanged
canonical values, so

    g3(r') <= 1 - ((1 - g3(r)) N - D) / (N - D + I).

The right-hand side is increasing in g3(r), so the certified bound U + nu_bar may be
substituted for g3(r); the result holds on the event of the original certificate, for
every later version at once, at zero oracle cost.
"""


def propagate(u, n, deleted, inserted):
    """Valid g3 bound after `deleted` deletions and `inserted` insertions (cumulative). If every tuple is deleted
    the relation is empty, which satisfies every FD; 0 is returned by that convention (the paper defines g3 on
    nonempty relations only)."""
    n_new = n - deleted + inserted
    if n_new <= 0:
        return 0.0
    return min(1.0, max(0.0, 1.0 - ((1.0 - u) * n - deleted) / n_new))


def alpha_schedule(alpha, j):
    """Level for the j-th version (j = 0: initial certification): alpha / 2^(j+1), summing to <= alpha."""
    return alpha / 2 ** (j + 1)
