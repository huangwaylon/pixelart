"""mcurve.py (M): key curves. Periodic / one-shot cubic Hermite with Catmull-Rom (or flat) tangents, easing helpers."""
import numpy as np, math


def _herm(p0, p1, m0, m1, u):
    u2 = u * u; u3 = u2 * u
    return (2 * u3 - 3 * u2 + 1) * p0 + (u3 - 2 * u2 + u) * m0 + (-2 * u3 + 3 * u2) * p1 + (u3 - u2) * m1


def pkey(keys, x, tension=0.0):
    """periodic curve on [0,1): keys = [(x, value or array), ...] sorted, x in [0,1). Catmull-Rom (cardinal) tangents.
    A key may be (x, value, 'flat') to force a zero tangent (a hold/extreme)."""
    x = x % 1.0
    xs = [k[0] for k in keys]; n = len(keys)
    vs = [np.asarray(k[1], float) for k in keys]
    flat = [len(k) > 2 and k[2] == "flat" for k in keys]
    i = max(j for j in range(n) if xs[j] <= x) if x >= xs[0] else n - 1
    j = (i + 1) % n
    x0 = xs[i]; x1 = xs[j] + (1.0 if j <= i else 0.0)
    xx = x if x >= x0 else x + 1.0
    def tang(k):
        a = (k - 1) % n; b = (k + 1) % n
        xa = xs[a] - (1.0 if a >= k else 0.0); xb = xs[b] + (1.0 if b <= k else 0.0)
        if flat[k]: return vs[k] * 0
        return (1 - tension) * (vs[b] - vs[a]) / (xb - xa)
    h = x1 - x0; u = (xx - x0) / h
    return _herm(vs[i], vs[j], tang(i) * h, tang(j) * h, u)


def okey(keys, x, tension=0.0):
    """one-shot curve, clamped at both ends; flat tangents at the end keys."""
    xs = [k[0] for k in keys]; vs = [np.asarray(k[1], float) for k in keys]; n = len(keys)
    flat = [len(k) > 2 and k[2] == "flat" for k in keys]
    if x <= xs[0]: return vs[0]
    if x >= xs[-1]: return vs[-1]
    i = max(j for j in range(n - 1) if xs[j] <= x); j = i + 1
    def tang(k):
        if flat[k] or k == 0 or k == n - 1: return vs[k] * 0
        return (1 - tension) * (vs[k + 1] - vs[k - 1]) / (xs[k + 1] - xs[k - 1])
    h = xs[j] - xs[i]; u = (x - xs[i]) / h
    return _herm(vs[i], vs[j], tang(i) * h, tang(j) * h, u)


def smooth(u):
    u = min(1.0, max(0.0, u)); return u * u * (3 - 2 * u)


def c(x): return math.cos(2 * math.pi * x)


def s(x): return math.sin(2 * math.pi * x)
