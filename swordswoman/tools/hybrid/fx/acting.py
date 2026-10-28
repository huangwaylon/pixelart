"""S7 ACTING kit: the head-acting offset table and the ribbon / bow LAG driver.  tools/hybrid/fx/acting.py

HEAD_ACT[action][key] = dict(dx, dy, tilt, sink, expr)  head offsets RELATIVE to the body offset of that key (the
  h3 compositor's `head` = body + this), tilt = the lock stamp tilt (-1 back / 0 / +1 into the move), sink = rows
  the head sinks into the collar (squash keys), expr = lock2 expression stamp name.  From ANIM_DIRECTION 2 / 5:
  the head LEADS on attacks (drives into the cut), LAGS on locomotion (lands a key after the foot), counter-tilts
  on anticipation, and never deforms (rigid; it sinks / rises 1-2 px instead).

lag(driver, lag=1, overshoot=2, ...)  -> per-key offsets of a secondary part (bow, bun, ribbon root / tip, skirt
  tail) relative to its driver: while the driver moves the part trails 1 key behind it (offset = -velocity, capped);
  the key after the driver stops it OVERSHOOTS past rest by `overshoot` px (2 bow, 3 ribbon tips), comes back by
  half on the next key and rests on the one after.  hit-stop keys (`holds`) freeze the offset.  Works per axis on
  scalars or (x, y) tuples.

ribbon(roots, rest_dir, driver, nodes=7, seg=2.0)  -> point chains per key for the h3 @ribbon / ribbonN / ribbonF
  pose fields: root nodes follow lag(lag=1, overshoot=1), the tip follows a lag delayed one more key with
  overshoot 3, blended along the chain, so the overshoot key shows the S-curve (root already reversed, tip still
  trailing).  Segment lengths are re-normalised so the cloth never stretches.

feet_points(g)  -> [(x_outer_left, y, -1), (x_outer_right, y, +1)] at the lowest body row: anchors for kit.dust and
  kit.streaks (dust is ATTACHED to the feet).
"""
import math

import numpy as np

HEAD_ACT = {
    # slash: coil = head counter-tilts back and sinks (eyes stay on the target); smear = head starts forward;
    # impact = head DRIVES into the cut (+3 px, tilt in, kiai); follow-through = head settles forward, tilt held.
    'slash': [dict(dx=-2, dy=1, tilt=-1, sink=1, expr='glare'), dict(dx=1, dy=0, tilt=0, sink=0, expr='wide'),
              dict(dx=3, dy=1, tilt=1, sink=1, expr='kiai'), dict(dx=2, dy=0, tilt=1, sink=0, expr='glare')],
    # overhead f0..f8 (dip, rise, apex coil, smear1, impact, hold, rebound, recover, settle)
    'overhead': [dict(dx=0, dy=1, tilt=0, sink=1, expr='glare'), dict(dx=0, dy=-1, tilt=-1, sink=0, expr='glare'),
                 dict(dx=-1, dy=-1, tilt=-1, sink=0, expr='wide'), dict(dx=1, dy=0, tilt=0, sink=0, expr='kiai'),
                 dict(dx=3, dy=2, tilt=1, sink=2, expr='kiai'), dict(dx=3, dy=2, tilt=1, sink=2, expr='kiai'),
                 dict(dx=2, dy=1, tilt=1, sink=1, expr='glare'), dict(dx=1, dy=0, tilt=0, sink=0, expr='glare'),
                 dict(dx=0, dy=0, tilt=0, sink=0, expr='calm')],
    # jump: crouch sinks 2 into the collar and tilts in; apex rises 1 out of it and looks up; land sinks 2
    'jump': [dict(dx=1, dy=1, tilt=1, sink=2, expr='glare'), dict(dx=0, dy=-1, tilt=-1, sink=0, expr='wide'),
             dict(dx=1, dy=1, tilt=1, sink=2, expr='squeeze')],
    # walk contact / down / passing / up: the head LAGS the cog by one key (use lag() on the cog for dy);
    # here only the small side-to-side and tilt with the stride
    'walk': [dict(dx=0, dy=0, tilt=0, sink=0, expr='calm'), dict(dx=0, dy=0, tilt=0, sink=1, expr='calm'),
             dict(dx=0, dy=0, tilt=0, sink=0, expr='calm'), dict(dx=0, dy=0, tilt=0, sink=0, expr='calm')],
    # run f0..f7 (contact, down, pass, flight, contact, down, pass, flight): leans in, head counters -12 deg
    'run': [dict(dx=2, dy=0, tilt=1, sink=0, expr='glare'), dict(dx=2, dy=1, tilt=1, sink=1, expr='glare'),
            dict(dx=2, dy=0, tilt=1, sink=0, expr='glare'), dict(dx=3, dy=-1, tilt=0, sink=0, expr='glare')] * 2,
    # dash f0..f3: lean back (anticipation), forward travel (x2), brake (head whips forward then the cloth)
    'dash': [dict(dx=-2, dy=1, tilt=-1, sink=1, expr='glare'), dict(dx=3, dy=0, tilt=1, sink=0, expr='glare'),
             dict(dx=3, dy=0, tilt=1, sink=0, expr='glare'), dict(dx=-1, dy=1, tilt=0, sink=1, expr='glare')],
}
JUMP_KEYS = {'crouch': 0, 'apex': 1, 'land': 2}


def head_for(action, key, body=(0, 0)):
    """-> dict(head=(x, y), tilt, sink, expr) for the h3 frame dict (head = body offset + acting offset)"""
    k = JUMP_KEYS.get(key, key) if isinstance(key, str) else key
    a = HEAD_ACT[action][k]
    return dict(head=(body[0] + a['dx'], body[1] + a['dy']), tilt=a['tilt'], sink=a['sink'], expr=a['expr'])


def _lag1(d, lag=1, overshoot=2, cap=4, holds=(), loop=False, settle=(0.5, 0.0), thr=0.5):
    n = len(d)
    v = [0.0] * n
    for i in range(n):
        if i == 0 and not loop: v[i] = 0.0
        else: v[i] = d[i] - d[i - 1]
    off = [0.0] * n
    pend = []                                        # overshoot queue
    lastv = 0.0
    for i in range(n):
        if i in holds and i > 0:
            off[i] = off[i - 1]; continue
        if abs(v[i]) > thr:
            # trail: where the driver was `lag` keys ago, relative to now (capped)
            back = d[i - lag] - d[i] if (i - lag >= 0 or loop) else 0.0
            off[i] = max(-cap, min(cap, back))
            lastv = v[i]; pend = []
        else:
            if lastv:
                sg = 1 if lastv > 0 else -1
                pend = [sg * overshoot] + [sg * overshoot * f for f in settle]
                lastv = 0.0
            off[i] = pend.pop(0) if pend else 0.0
    return off


def lag(driver, lag=1, overshoot=2, cap=4, holds=(), loop=False, tip=False, settle=(0.5, 0.0)):
    """secondary offsets (relative to the driver) per key; driver = list of scalars or (x, y).  tip=True: the
    chain tip, delayed one more key and overshooting more (use overshoot=3)."""
    if tip: lag = lag + 1
    if driver and isinstance(driver[0], (tuple, list)):
        xs = _lag1([p[0] for p in driver], lag, overshoot, cap, holds, loop, settle)
        ys = _lag1([p[1] for p in driver], lag, overshoot, cap, holds, loop, settle)
        return [(int(round(a)), int(round(b))) for a, b in zip(xs, ys)]
    return [int(round(a)) for a in _lag1(list(driver), lag, overshoot, cap, holds, loop, settle)]


def ribbon(roots, rest_dir, driver, nodes=7, seg=2.0, overshoot=3, cap=5, holds=(), loop=False, sag=0.0, rest_shape=None, max_bend=40):
    """-> [ [ (x, y) * nodes ] per key ].  roots: the ribbon root per key (moves with the collar); rest_dir: the
    hanging direction at rest; driver: the travel (x, y) per key that the cloth reacts to (body / virtual travel).
    rest_shape: the cel's own rest chain [(x, y) ...] (root first) - used instead of a straight rest_dir line so the
    lagged ribbon keeps the drawn curve of the lock cel; nodes = len(rest_shape)."""
    A = lag(driver, 1, 1, cap, holds, loop)
    B = lag(driver, 1, overshoot, cap + 2, holds, loop, tip=True)
    L = math.hypot(*rest_dir) or 1.0
    rd = (rest_dir[0] / L, rest_dir[1] / L)
    if rest_shape:
        nodes = len(rest_shape)
    out = []
    for k, r in enumerate(roots):
        pts = []
        for j in range(nodes):
            w = j / max(1, nodes - 1)
            wb = w ** 1.3
            ox = (1 - wb) * A[k][0] * w + wb * B[k][0]
            oy = (1 - wb) * A[k][1] * w + wb * B[k][1]
            if rest_shape:
                bx = r[0] + rest_shape[j][0] - rest_shape[0][0]; by = r[1] + rest_shape[j][1] - rest_shape[0][1]
            else:
                bx = r[0] + rd[0] * seg * j; by = r[1] + rd[1] * seg * j + sag * j * j
            pts.append((bx + ox, by + oy))
        # re-normalise segment lengths (cloth does not stretch)
        segs = ([math.hypot(rest_shape[j][0] - rest_shape[j - 1][0], rest_shape[j][1] - rest_shape[j - 1][1])
                 for j in range(1, nodes)] if rest_shape else [seg] * (nodes - 1))
        fixed = [pts[0]]
        prev = None
        for j in range(1, nodes):
            px, py = fixed[-1]; qx, qy = pts[j]
            a = math.atan2(qy - py, qx - px)
            if prev is not None:                      # cloth bends, it never kinks: max turn per node
                d_a = (a - prev + math.pi) % (2 * math.pi) - math.pi
                lim = math.radians(max_bend)
                a = prev + max(-lim, min(lim, d_a))
            prev = a
            fixed.append((px + math.cos(a) * segs[j - 1], py + math.sin(a) * segs[j - 1]))
        out.append([(int(round(x)), int(round(y))) for x, y in fixed])
    return out


def feet_points(g, ground='auto', exclude='tTw'):
    """dust / streak anchors at the lowest body row: [(left_x, y, -1), (right_x, y, +1)].  ground='auto' = the
    lowest body row; ground=None = the same (airborne figure: anchors under the soles)."""
    body = (g != '.') & ~np.isin(g, list(exclude))
    ys, xs = np.nonzero(body)
    y = ys.max() if ground in ('auto', None) else ground
    row = xs[ys == ys.max()]
    # foot columns: the lowest 2 rows
    low = xs[ys >= ys.max() - 1]
    return [(int(low.min()) - 1, int(y), -1), (int(low.max()) + 1, int(y), 1)]
