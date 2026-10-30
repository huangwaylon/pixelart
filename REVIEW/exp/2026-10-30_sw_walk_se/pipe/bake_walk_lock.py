"""bake_walk_lock.py OUT.json  -- step 1b: re-bake the walk with the DESIGN_LOCK spring set (~10 spring bones).

Reuses M's bake unchanged (motion/scripts/mbuild.py: body gait, head lag, timing, expression keys) and only swaps the
secondary-chain list that msim.ChainSim simulates. Lock section 5:
  bun 1, bow 2, back hair 2, side locks 2 (1 each), skirt front/back 2, sleeve tips 1 (shared)  = 10 simulated bones.
Everything else is DRIVEN (a fixed fraction of a simulated bone, so it follows through without its own state) or STATIC:
  bow.X.2 = 0.6 x bow.X.1 | hair_side.X.2/.3 = 0.5 / 0.3 x hair_side.X.1 | skirt.FL/FR = 0.5 x F, BL/BR = 0.5 x B,
  skirt.L/R static | skirt.*.2 = 0.4 x own .1 | hair_front.* static (bangs are painted on the head) | hair_back.1 static.
'Shared' sleeve tip: sleeve.L.2 is simulated; sleeve.R.2 = the X-mirror of sleeve.L.2 half a cycle later (the walk is
left/right symmetric: frame k+4 is the mirrored frame k), so one spring state drives both cuffs.
Deterministic: same input skeleton/code -> byte-identical output.  Posture gate: motion/scripts/mgate.py on the result."""
import sys, os, json
import numpy as np
SK = '/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_skinned'
sys.path.insert(0, SK + '/motion/scripts')
import mbuild, msim  # noqa: E402
from scipy.spatial.transform import Rotation as Rot  # noqa: E402

SIM = [("bun", ["bun"], "head"),
       ("bow", ["bow.L.1"], "bow_knot"), ("bow", ["bow.R.1"], "bow_knot"),
       ("hair_back", ["hair_back.2", "hair_back.3"], "hair_back.1"),
       ("hair_side", ["hair_side.L.1"], "head"), ("hair_side", ["hair_side.R.1"], "head"),
       ("skirt", ["skirt.F.1"], "pelvis"), ("skirt", ["skirt.B.1"], "pelvis"),
       ("sleeve", ["sleeve.L.2"], "sleeve.L.1")]
DRIVEN = {"bow.L.2": ("bow.L.1", .6), "bow.R.2": ("bow.R.1", .6),
          "hair_side.L.2": ("hair_side.L.1", .5), "hair_side.L.3": ("hair_side.L.1", .3),
          "hair_side.R.2": ("hair_side.R.1", .5), "hair_side.R.3": ("hair_side.R.1", .3),
          "skirt.FL.1": ("skirt.F.1", .5), "skirt.FR.1": ("skirt.F.1", .5), "skirt.BL.1": ("skirt.B.1", .5), "skirt.BR.1": ("skirt.B.1", .5),
          "skirt.F.2": ("skirt.F.1", .4), "skirt.B.2": ("skirt.B.1", .4), "skirt.FL.2": ("skirt.FL.1", .4), "skirt.FR.2": ("skirt.FR.1", .4),
          "skirt.BL.2": ("skirt.BL.1", .4), "skirt.BR.2": ("skirt.BR.1", .4)}
N_SIM = sum(len(c) for _, c, _ in SIM)


class LockSim(msim.ChainSim):
    def __init__(self, sk, chains=None):
        super().__init__(sk, chains=[(g, list(c), a) for g, c, a in SIM])
        self.ring = []  # no panel ring: only F and B are simulated


def slerp_id(q, k):
    """fraction k of rotation q (w,x,y,z) from identity"""
    r = Rot.from_quat([q[1], q[2], q[3], q[0]]); v = r.as_rotvec() * k; x, y, z, w = Rot.from_rotvec(v).as_quat()
    return [round(float(w), 6), round(float(x), 6), round(float(y), 6), round(float(z), 6)]


def mirror_x(q):
    """X-mirror of a local rotation between mirror-image bones (.L <-> .R): (w, x, -y, -z)"""
    return [q[0], q[1], -q[2], -q[3]]


def bake(out):
    msim.ChainSim = LockSim
    tmpd = os.path.dirname(os.path.abspath(out)); mbuild.MOT = tmpd
    p = mbuild.build('walk')  # writes <tmpd>/walk.json
    m = json.load(open(p)); os.remove(p)
    n = len(m['frames']); half = n // 2
    for k, fr in enumerate(m['frames']):
        b = fr['bones']
        for d, (src, f) in DRIVEN.items(): b[d] = {'rot': slerp_id(b[src]['rot'], f)}
        b['sleeve.R.2'] = {'rot': mirror_x(m['frames'][(k + half) % n]['bones']['sleeve.L.2']['rot'])}
    # driven bones computed from simulated ones in frame order above (FL.2 uses the just-driven FL.1)
    m['notes'] += f" | LOCK re-bake (pipe/bake_walk_lock.py): {N_SIM} simulated spring bones {[c for _, ch, _ in SIM for c in ch]}; driven {sorted(DRIVEN)} + sleeve.R.2 (shared, mirrored half-cycle); others static."
    m['lock_springs'] = {'simulated': [c for _, ch, _ in SIM for c in ch], 'driven': sorted(DRIVEN) + ['sleeve.R.2'], 'n_sim': N_SIM}
    json.dump(m, open(out, 'w'), indent=0)
    return m


if __name__ == '__main__':
    m = bake(sys.argv[1]); print('BAKED', sys.argv[1], 'frames', len(m['frames']), 'sim bones', N_SIM)
