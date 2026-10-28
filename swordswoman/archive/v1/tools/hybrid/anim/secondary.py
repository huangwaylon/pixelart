"""SECONDARY-MOTION DRIVER (shared round-2 foundation).  tools/hybrid/anim/secondary.py

Turns one body DRIVER per key (the direction the cloth must trail, i.e. minus the body/blade velocity, in sprite px)
into per-part offsets with the ANIM_DIRECTION 2.3 lags, travelling waves and automatic overshoot-and-settle:

    lags: head +1, bun +1, bow loops +2, ribbon chain root -> tip 1 -> 3, skirt tail 1, cuffs 1
    amplitude (ribbon tip): walk 3-4 px, attacks 6-10 px  (set with tip_amp)
    overshoot: after a STOP (the drag falls to ~0 after a big value) the part goes 2-4 px PAST rest (against the
    old drag), then half of that, then rest, with the root already reversed while the tip still trails (S-curve).

API
    drags = with_overshoot(drags, os=0.6)                 # list of (dx,dy) per key -> with overshoot frames
    lagged(drags, lag, cyclic, gain)                      # the drag a part sees at each key
    part_offsets(drags, cyclic, gains)                    # {'head','bun','bow','tail','cuff'} -> [(dx,dy) int]
    ribbon(root, rest, drags, i, cyclic, tip_amp, lags=(1,2,3), wave=0) -> node list for kit '@ribbon'
        rest = segment vectors of the ribbon at rest (root first); node k gets drag(i - lag_k) * amp_k
    ribbon_cmd(...) -> '@ribbon x,y ... side=S over=0' string
"""
import math

LAGS = dict(head=1, bun=1, bow=2, tail=1, cuff=1, front=1)


def _get(seq, i, cyclic):
    n = len(seq)
    if cyclic: return seq[i % n]
    if i < 0: return seq[0]
    return seq[min(i, n - 1)]


def with_overshoot(drags, os=0.6, stop_ratio=0.35):
    """insert overshoot after stops (non-cyclic sequences). A stop = |d[i]| < stop_ratio * |d[i-1]|.
    d[i] becomes -os * d[i-1] (past rest), d[i+1] (if also a stop) becomes -os/2 * d[i-1]."""
    out = [tuple(d) for d in drags]
    i = 1
    while i < len(out):
        a = math.hypot(*out[i - 1]); b = math.hypot(*drags[i])
        if a > 1.5 and b < stop_ratio * a:
            ref = out[i - 1]
            out[i] = (drags[i][0] - os * ref[0], drags[i][1] - os * ref[1])
            if i + 1 < len(out) and math.hypot(*drags[i + 1]) < stop_ratio * a:
                out[i + 1] = (drags[i + 1][0] - os / 2 * ref[0], drags[i + 1][1] - os / 2 * ref[1])
                i += 1
        i += 1
    return out


def lagged(drags, lag, cyclic, gain=1.0, i=None):
    if i is not None:
        d = _get(drags, i - lag, cyclic); return (d[0] * gain, d[1] * gain)
    return [(_get(drags, k - lag, cyclic)[0] * gain, _get(drags, k - lag, cyclic)[1] * gain) for k in range(len(drags))]


def part_offsets(drags, cyclic, gains=None):
    gains = gains or dict(head=0.25, bun=0.35, bow=0.6, tail=0.8, cuff=0.6, front=0.5)
    out = {}
    for p, lag in LAGS.items():
        g = gains.get(p, 0.5)
        out[p] = [(int(round(x)), int(round(y))) for x, y in lagged(drags, lag, cyclic, g)]
    return out


def ribbon(root, rest, drags, i, cyclic, tip_amp=4.0, lags=None, wave=0.0, phase=0.0):
    """root (x,y); rest: list of segment vectors; returns node list. Node k (1..n) of n is displaced by the drag
    seen lag_k keys ago times amp_k = tip_amp * (k/n)^1.3 / |drag_max| (normalised so the strongest drag in the
    sequence moves the tip by tip_amp px). wave adds a sideways travelling flutter (px) on the outer nodes."""
    n = len(rest)
    if lags is None: lags = [1 + round(2 * k / max(1, n - 1)) for k in range(n)]
    dmax = max(1e-6, max(math.hypot(*d) for d in drags))
    pts = [root]
    x, y = root
    for k, (vx, vy) in enumerate(rest):
        x += vx; y += vy
        d = _get(drags, i - lags[k], cyclic)
        a = tip_amp * ((k + 1) / n) ** 1.3 / dmax
        ox, oy = d[0] * a, d[1] * a
        if wave:
            L = math.hypot(vx, vy) or 1
            nx, ny = -vy / L, vx / L
            s = wave * ((k + 1) / n) * math.sin(phase + i * math.pi / 2 - k * 0.9)
            ox += nx * s; oy += ny * s
        pts.append((x + ox, y + oy))
    return [(round(px), round(py)) for px, py in pts]


def ribbon_cmd(root, rest, drags, i, cyclic, side=1, tip_amp=4.0, wave=0.0, phase=0.0, over=0, lags=None):
    pts = ribbon(root, rest, drags, i, cyclic, tip_amp, lags, wave, phase)
    return '@ribbon ' + ' '.join(f'{x},{y}' for x, y in pts) + f' side={side} over={over}'
