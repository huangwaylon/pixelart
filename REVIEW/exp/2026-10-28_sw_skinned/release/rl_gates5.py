"""rl_gates5.py (I, round 5 gates): posture (M's measured torso/head pitch, head-forward over the neck) and bangs coverage.
Imported by rl.py gates.  Posture = release/rl_pose.py in Blender on each action's E-view motion file + R's per-frame E-view pts
(head centre vs neck base, 1x px).  Bangs = per 1x cell majority of R's matid (guide) pass x P's part pass (head group):
skin cells above the eye/brow line that have hair above them in the same column (= scalp/forehead showing between fringe clumps)."""
import os, json, subprocess
import numpy as np
EXP = '/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_skinned'
BL = '/Applications/Blender.app/Contents/MacOS/Blender'
POSE_GATED = ('idle', 'walk')       # torso pitch >= 0 and head level gates apply to these (standing / walking) actions
HEAD_PITCH = (-3.0, 8.0)            # deg, + = chin down: level (+-3) to slightly down
COS30 = 0.8660254


def pose(motions, out):
    """motions: {act: motion path}; -> {act: [per-frame rows]} (cached in out)"""
    if not os.path.exists(out):
        r = subprocess.run([BL, '-b', f'{EXP}/rig/rig.blend', '-P', f'{EXP}/release/rl_pose.py', '--', out, *motions.values()],
                           capture_output=True, text=True)
        if not os.path.exists(out): return {'_error': r.stdout[-500:] + r.stderr[-500:]}
    d = json.load(open(out)); return {a: d.get(m, []) for a, m in motions.items()}


def head_forward_px(info):
    """E profile: her front = screen +x.  head centre (mid of the head bone) x - neck base x, 1x px, per frame"""
    return [round(f['pts']['head'][0] - f['pts']['neck'][0], 2) for f in info['frames']]


def torso_px_pitch(info):
    """cross-check from the E-view projection: pelvis -> neck base angle from vertical (vertical foreshortened by cos 30)"""
    out = []
    for f in info['frames']:
        (px_, py_), (nx, ny) = f['pts']['pelvis'], f['pts']['neck']
        out.append(round(float(np.degrees(np.arctan2(nx - px_, (py_ - ny) / COS30))), 2))
    return out


def bangs(W, stem, info):
    import pixel_chain as PC
    dx, dy = info.get('out_dxdy', [0, 0]); MN = list(PC.MN); hair, skin = MN.index('hair'), MN.index('skin')
    base = {MN.index(m) for m in ('hair', 'skin', 'bow', 'dress', 'sleeve', 'obi', 'socks', 'boots') if m in MN}
    HEAD = PC.PI['head']; res = []
    for f in info['frames']:
        i = f['i']; F = PC.load(f'{W}/{stem}', i, dx, dy, f'{W}/parts')
        mid, part = F['mid'], F['part']; N = mid.shape[0] // 8
        c = lambda a: a.reshape(N, 8, N, 8).transpose(0, 2, 1, 3).reshape(N, N, 64)
        m8, p8 = c(mid), c(part)
        hm = (p8 == HEAD).sum(-1) >= 32
        def maj(k): return (m8 == k).sum(-1)
        cnt = np.stack([maj(k) for k in range(len(MN))], -1); cm = cnt.argmax(-1); cm[cnt.max(-1) < 32] = -1
        H = hm & (cm == hair); S = hm & (cm == skin); feat = hm & (cm >= 0) & ~np.isin(cm, list(base))
        ys = np.nonzero(feat.any(1))[0]; src = 'matid'
        if len(ys): ftop = int(ys.min())
        else:
            fa = f.get('face') or {}; ey = [v['px'][1] for k, v in fa.items() if k.startswith(('eye', 'brow')) and 'px' in v]
            if not ey: res.append({'i': i, 'skin_px': None}); continue
            ftop = int(np.floor(min(ey))) - 1; src = 'anchor'
        above = np.cumsum(H, 0) > 0  # some hair above (or at) this row in the column
        bad = S & above & (np.arange(N)[:, None] < ftop - 1)
        res.append({'i': i, 'skin_px': int(bad.sum()), 'eye_line': ftop, 'src': src, 'xy': [list(map(int, p)) for p in np.argwhere(bad)[:12]]})
    return res
