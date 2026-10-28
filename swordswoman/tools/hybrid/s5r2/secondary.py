"""S5 r2 secondary-motion OVERSHOOT driver.
rope(): a Verlet rope (ribbon / skirt tail) hung from a moving root, simulated through the key sequence with the
real key timing (ms), sampled at each key's display start. The root path is exaggerated by `gain` for the sim
(sprite moves are only a few px, real cloth would barely react) and the rope is re-expressed relative to the real
root, so the result trails AGAINST velocity, lags 1-3 frames root-to-tip and overshoots after every stop (under-
damped), settling over 2-3 frames.
spring(): 1-D/2-D under-damped follower (head, bun, bow loops) -> integer lag offsets with overshoot.
Keys flagged hold=True (hit-stop) freeze the sim (no secondary motion on the held frame) and resume after it."""
import math
import numpy as np

SAMPLE = 0.6
def _timeline(roots, ms, cycles=1, sub=4.0, holds=()):
    """-> list of (t, root(x,y), sample_flag (cycle,key) or None, frozen) at `sub` ms steps.
    The pose of key k is reached at its display start (root = roots[k]) and held while it shows; the root travels
    to the next key during the first `travel` part of the next interval (sprite keys snap, the cloth follows).
    Each key is sampled SAMPLE of the way through its display; hold keys (hit-stop) are sampled at their start and
    freeze the sim while they show."""
    out = []; n = len(roots); t = 0.0
    for c in range(cycles):
        for k in range(n):
            a = np.array(roots[k - 1] if (k > 0 or cycles > 1) else roots[0], float); b = np.array(roots[k], float)
            steps = max(1, int(ms[k] / sub)); travel = max(1, min(steps, int(40 / sub)))
            samp = 0 if k in holds else int(steps * SAMPLE)
            for s in range(steps):
                f = min(1.0, (s + 1) / travel)
                out.append((t, a + (b - a) * f, (c, k) if s == samp else None, k in holds and s > 0))
                t += sub
    return out

def rope(roots, ms, rest_dir=(0.0, 1.0), nodes=6, seg=2.2, gain=3.0, grav=0.06, damp=0.93, stiff=0.04,
         cycles=1, holds=(), wind=(0.0, 0.0), virt=None):
    """roots: per-key root (x,y). rest_dir: the hanging direction at rest (unit-ish, e.g. trailing back + down).
    Returns per key: list of node (x,y) (root first) in sprite coords."""
    rd = np.array(rest_dir, float); rd /= np.linalg.norm(rd)
    # virtual travel: the sim root also moves by `virt` (per-key offsets, sprite px) so a body that only shifts a
    # few px in the cell still drags its cloth like the real move would (a lunge travels, the cell is root-locked)
    sim_roots = [tuple(np.array(r, float) + (np.array(virt[k], float) if virt else 0)) for k, r in enumerate(roots)]
    tl = _timeline(sim_roots, ms, cycles, holds=holds)
    r0 = np.array(sim_roots[0], float)
    P = np.array([[0.0, 0.0] + rd * seg * gain * i for i in range(nodes)])   # sim space, relative to start
    P = np.array([rd * seg * gain * i for i in range(nodes)])
    Pp = P.copy()
    res = {}
    frozen = False
    for t, root, flag, frozen in tl:
        if frozen: continue
        rr = (root - r0) * gain
        V = (P - Pp) * damp
        Pp = P.copy()
        P = P + V + np.array([0, grav]) + np.array(wind)
        # shape memory: pull each node toward its rest pose relative to the previous node
        for i in range(1, nodes):
            want = P[i - 1] + rd * seg * gain
            P[i] += (want - P[i]) * stiff
        P[0] = rr
        for _ in range(6):                                  # length constraints
            for i in range(1, nodes):
                d = P[i] - P[i - 1]; L = np.linalg.norm(d) or 1e-6
                P[i] = P[i - 1] + d / L * seg * gain
        if flag is not None and flag[0] == cycles - 1:
            rel = (P - P[0]) / gain                        # rope relative to the root, back to sprite scale
            res[flag[1]] = [tuple(np.array(roots[flag[1]], float) + q) for q in rel]
    return [res[k] for k in range(len(roots))]

def spring(targets, ms, k=0.012, c=0.10, cycles=1, holds=(), sub=4.0):
    """under-damped follower of a per-key target (x,y) -> per-key position (float). Lag + overshoot."""
    tl = _timeline(targets, ms, cycles, sub, holds=holds)
    x = np.array(targets[0], float); v = np.zeros(2); res = {}
    for t, tg, flag, frozen in tl:
        if not frozen:
            a = k * (tg - x) - c * v
            v = v + a * sub; x = x + v * sub
        if flag is not None and flag[0] == cycles - 1: res[flag[1]] = tuple(x)
    return [res[i] for i in range(len(targets))]

def ints(pts): return [(int(round(x)), int(round(y))) for x, y in pts]
def fmt(pts): return ' '.join(f'{int(round(x))},{int(round(y))}' for x, y in pts)

if __name__ == '__main__':
    # demo: slash timing, root swinging left->right then stopping
    roots = [(54, 78), (60, 80), (70, 81), (72, 80)]
    ms = [220, 50, 160, 240]
    for k, r in enumerate(rope(roots, ms, rest_dir=(-0.6, 1.0), holds=(2,))):
        print(k, fmt(r))
    print(spring([(0, 0), (0, 3), (0, 4), (0, 2)], ms, holds=(2,)))

# ------------------------------------------------------------------ kinematic follow-through chain (designable)
KERNEL = (1.0, 0.55, -0.45, -0.25, 0.1)     # response to a velocity impulse, per frame after the lag: trail,
                                            # ease, OVERSHOOT past rest, half back, settle (S-curve settle)
def chain(roots, virt, rest_dir, nodes=6, seg=2.2, amp=0.45, lags=(1.0, 3.0), kernel=KERNEL, holds=(), loop=False,
          bend=0.0, maxdev=None, sag=0.0):
    """Deterministic follow-through: every node's direction = rest_dir trailing AGAINST the (virtual) velocity of
    the body, delayed root-to-tip by lags[0]..lags[1] frames, filtered by `kernel` (trail -> overshoot -> settle).
    roots: per-key root (x, y); virt: per-key virtual body position (sprite px; the travel the move implies).
    holds: hit-stop keys copy the previous key's cloth (no secondary motion on the held frame).
    bend: extra curl per node (radians, + = clockwise on screen) for S-curves. Returns per key node lists."""
    n = len(roots); V = []
    for k in range(n):
        p = np.array(virt[k], float); q = np.array(virt[k - 1] if (k > 0 or loop) else virt[0], float)
        V.append(p - q)
    V = np.array(V)
    def vel(t):                                  # fractional frame index into V (0 before the start unless loop)
        if loop: t = t % n
        if t < 0: return np.zeros(2)
        i0 = int(math.floor(t)); f = t - i0
        a = V[i0 % n] if (loop or i0 < n) else np.zeros(2); b = V[(i0 + 1) % n] if (loop or i0 + 1 < n) else np.zeros(2)
        return a * (1 - f) + b * f
    rd = np.array(rest_dir, float); rd /= np.linalg.norm(rd)
    out = []
    for k in range(n):
        kk = k
        while kk in holds and kk > 0: kk -= 1   # held frame: show the previous key's cloth response
        pts = [np.array(roots[k], float)]
        for i in range(1, nodes):
            L = lags[0] + (lags[1] - lags[0]) * (i - 1) / max(1, nodes - 2)
            R = sum(w * vel(kk - L + 1 - m) for m, w in enumerate(kernel))
            d = rd - amp * R
            if maxdev is not None:                       # clamp the swing (cloth never planks out horizontal)
                a_r = math.atan2(rd[1], rd[0]); a_d = math.atan2(d[1], d[0])
                dev = (a_d - a_r + math.pi) % (2 * math.pi) - math.pi
                dev = max(-maxdev, min(maxdev, dev)); d = np.array([math.cos(a_r + dev), math.sin(a_r + dev)])
            if bend:
                c, s = math.cos(bend * i), math.sin(bend * i); d = np.array([c * d[0] - s * d[1], s * d[0] + c * d[1]])
            d /= (np.linalg.norm(d) or 1)
            if sag: d = d + np.array([0.0, sag * i]); d /= np.linalg.norm(d)   # tips droop under gravity
            pts.append(pts[-1] + d * seg)
        out.append([tuple(p) for p in pts])
    return out
