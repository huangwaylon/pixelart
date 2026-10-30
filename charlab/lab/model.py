"""charlab model builder: designer spec (charlab/designs/<id>.json, VOCAB.md v1) -> one closed, skinned character mesh.

Units are H (head height), floor z = 0, the character faces -Y, +X = her left (VOCAB.md).
Everything is a signed distance field (SDF) built from primitives:
  body    = smooth union of the body-preset capsules/ellipsoids (one per segment, VOCAB 'segments')
  pieces  = VOCAB pieces: cover (offset of body segments, sub-ranges clipped), sphere/ellipsoid/box/cylinder/cone (rigid,
            attached to an anchor), strap (band on the torso), decal (paint, or a small box if it is >= 0.1H thick),
            stripe_pattern (paint)
  hair    = shell + mass + fringe slab (+ tail chain / buns), per VOCAB hair styles
The union is meshed once with marching cubes, so every joint stays connected and nothing interpenetrates.
Per face: material (the outermost layer at the face centre), line group (head/hair/hat/body/armL/armR/legL/legR/pack).
Per vertex: bone weights (top 4), computed automatically from the distance to the body segments (softmin), or rigid /
chain / skirt rules for attached pieces.
CLI:  python model.py SPEC.json TIER BODY OUT.npz        (writes OUT.npz + OUT.json)
"""
import json, math, os, sys
import numpy as np

# ----------------------------------------------------------------------------------------------------------------- presets
# VOCAB body table (H units) + lab choices for radii.  legs = floor -> hip joint, torso = hip joint -> neck base.
PRESETS = {
    'chibi':   dict(heads=2.5, neck=.05, torso=.65, legs=.80, head_w=.95, shoulder_w=.75, hip_k=1.06, waist_k=.80,
                    foot=.34, arm_r=.09, thigh_r=.17, shin_r=.12, ankle_r=.085, hand=.21, hand_r=.085, neck_r=.12,
                    wrist_z=.02, abduct=16),
    'compact': dict(heads=3.5, neck=.10, torso=1.05, legs=1.35, head_w=.85, shoulder_w=.80, hip_k=1.05, waist_k=.78,
                    foot=.30, arm_r=.08, thigh_r=.16, shin_r=.105, ankle_r=.072, hand=.20, hand_r=.075, neck_r=.10,
                    wrist_z=-.14, abduct=14),
    'slim':    dict(heads=5.0, neck=.15, torso=1.55, legs=2.30, head_w=.80, shoulder_w=.85, hip_k=.98, waist_k=.72,
                    foot=.36, arm_r=.07, thigh_r=.145, shin_r=.095, ankle_r=.062, hand=.21, hand_r=.068, neck_r=.085,
                    wrist_z=-.16, abduct=11),
}
BUILD = {'petite': .93, 'average': 1.0, 'athletic': 1.0, 'sturdy': 1.10}
TIER_RES = {'simple': 150, 'medium': 200, 'detailed': 250}      # voxels over the total height
APOSE = math.radians(25)
TOON_SIGMA = 0.07   # H at the compact preset (scaled by total height); 0 = geometric normals
GROUPS = ['bg', 'head', 'hair', 'hat', 'body', 'armL', 'armR', 'legL', 'legR', 'pack']
BONE_GROUP = {'head': 'head', 'neck': 'body', 'chest': 'body', 'spine': 'body', 'hips': 'body', 'root': 'body'}


# ------------------------------------------------------------------------------------------------------------- SDF prims
def _len(v):
    return np.sqrt((v * v).sum(-1))


def sd_ellipsoid(P, c, r):
    q = (P - c) / r
    k0 = _len(q); k1 = _len(q / r)
    return k0 * (k0 - 1.0) / np.maximum(k1, 1e-9)


def sd_roundcone(P, a, b, ra, rb):
    """iq's exact round cone (capsule with two radii)."""
    a = np.asarray(a, float); b = np.asarray(b, float)
    ba = b - a; l2 = ba @ ba; rr = ra - rb; a2 = l2 - rr * rr; il2 = 1.0 / l2
    pa = P - a; y = pa @ ba; z = y - l2
    x2v = pa * l2 - y[:, None] * ba; x2 = (x2v * x2v).sum(-1); y2 = y * y * l2; z2 = z * z * l2
    k = np.sign(rr) * rr * rr * x2
    d = (np.sqrt(x2 * a2 * il2) + y * rr) * il2 - ra
    d = np.where(np.sign(z) * a2 * z2 > k, np.sqrt(x2 + z2) * il2 - rb, d)
    d = np.where(np.sign(y) * a2 * y2 < k, np.sqrt(x2 + y2) * il2 - ra, d)
    return d


def sd_box(P, c, h, r=0.0, R=None):
    q = P - c
    if R is not None: q = q @ R          # R columns = local axes
    q = np.abs(q) - (np.asarray(h) - r)
    return _len(np.maximum(q, 0)) + np.minimum(q.max(-1), 0) - r


def sd_cyl(P, c, rx, ry, hz, axis='z', r=0.0):
    q = P - c
    if axis == 'x': q = q[:, [1, 2, 0]]; rx, ry = ry, rx
    elif axis == 'y': q = q[:, [0, 2, 1]]
    d2 = (np.sqrt((q[:, 0] / rx) ** 2 + (q[:, 1] / ry) ** 2) - 1.0) * min(rx, ry) + r
    dz = np.abs(q[:, 2]) - hz + r
    return np.minimum(np.maximum(d2, dz), 0) + _len(np.stack([np.maximum(d2, 0), np.maximum(dz, 0)], -1)) - r


def sd_econe(P, ztop, zbot, rt, rb, cxy=(0, 0)):
    """elliptic frustum, axis z, top radii rt=(rx,ry) at ztop, bottom rb at zbot (approximate distance)."""
    z = P[:, 2]; t = np.clip((ztop - z) / (ztop - zbot), 0, 1)
    rx = rt[0] + (rb[0] - rt[0]) * t; ry = rt[1] + (rb[1] - rt[1]) * t
    q = np.sqrt(((P[:, 0] - cxy[0]) / rx) ** 2 + ((P[:, 1] - cxy[1]) / ry) ** 2)
    dr = (q - 1.0) * np.minimum(rx, ry) * 0.9
    dz = np.maximum(z - ztop, zbot - z)
    return np.maximum(dr, dz)


def smin(a, b, k):
    if k <= 0: return np.minimum(a, b)
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


def rot_x(deg):
    t = math.radians(deg); c, s = math.cos(t), math.sin(t)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


# ------------------------------------------------------------------------------------------------------------- the body
class Seg:
    """one body segment primitive: SDF + bone + axis (a->b) used for VOCAB sub-ranges (t in 0..1 along the axis)."""
    def __init__(self, name, side, bone, f, a, b, r_hint):
        self.name, self.side, self.bone, self.f, self.a, self.b, self.r = name, side, bone, f, np.asarray(a, float), np.asarray(b, float), r_hint

    def t(self, P):
        ab = self.b - self.a
        return ((P - self.a) @ ab) / (ab @ ab)

    def clip(self, P, d, t0, t1):
        L = np.linalg.norm(self.b - self.a); t = self.t(P)
        return np.maximum(d, np.maximum((t0 - t) * L, (t - t1) * L))


class Body:
    def __init__(self, preset, build=None, tier='medium'):
        p = dict(PRESETS[preset]); b = build or {}
        bk = BUILD.get(b.get('preset', 'average'), 1.0)
        self.preset, self.tier, self.p = preset, tier, p
        L, T, N = p['legs'], p['torso'], p['neck']
        self.z_hip, self.z_neck = L, L + T
        self.z_chin = L + T + N; self.cz = self.z_chin + 0.5; self.top = self.z_chin + 1.0
        self.total = self.top
        sw = p['shoulder_w'] * b.get('shoulder', 1.0) * (0.5 + 0.5 * bk)
        hw = sw * p['hip_k'] * b.get('hip', 1.0) * (0.6 + 0.4 * bk)
        ww = hw * p['waist_k']
        lr = b.get('limb_radius', 1.0) * (0.5 + 0.5 * bk)
        self.sw, self.hw, self.ww, self.lr = sw, hw, ww, lr
        self.head_r = np.array([p['head_w'] / 2, p['head_w'] / 2 * 1.04, 0.5])
        self.head_c = np.array([0, 0.0, self.cz])
        ar, tr, sr, kr = p['arm_r'] * lr, p['thigh_r'] * lr, p['shin_r'] * lr, p['ankle_r'] * lr
        self.ar, self.tr, self.sr, self.kr = ar, tr, sr, kr
        # landmarks
        self.z_pelvis = L + 0.10 * T; self.z_waist = L + 0.40 * T; self.z_chest = L + 0.72 * T
        self.z_sh = self.z_neck - 0.10 * T - 0.02
        self.sh_x = sw / 2 - ar * 0.9
        self.hip_x = max(tr * 1.05, hw / 2 * 0.50)
        self.ankle_z = kr * 1.25
        self.knee_z = self.ankle_z + (L - self.ankle_z) * 0.5
        wrist_z = L + p['wrist_z'] * L
        arm_len = self.z_sh - wrist_z
        self.upper_len = self.fore_len = arm_len * 0.5
        self.foot_len = p['foot']
        self.chest_r = np.array([sw / 2 * 0.86, sw / 2 * 0.62, 0.31 * T])
        self.belly_r = np.array([ww / 2, ww / 2 * 0.78, 0.20 * T])
        self.pelvis_r = np.array([hw / 2, hw / 2 * 0.72, 0.24 * T])
        self.j = {}
        self.j['pelvis'] = np.array([0, 0.02, self.z_pelvis]); self.j['waist'] = np.array([0, 0, self.z_waist])
        self.j['chest'] = np.array([0, 0, self.z_chest]); self.j['neck_base'] = np.array([0, 0.01, self.z_neck])
        self.j['chin'] = np.array([0, 0.0, self.z_chin]); self.j['head'] = self.head_c.copy()
        self.j['top'] = np.array([0, 0, self.top]); self.j['belly'] = np.array([0, 0, self.z_waist])
        self.j['neck'] = np.array([0, 0.01, (self.z_neck + self.z_chin) / 2])
        for s, sx in (('L', 1), ('R', -1)):
            sh = np.array([sx * self.sh_x, 0.0, self.z_sh])
            d = np.array([sx * math.sin(APOSE), 0, -math.cos(APOSE)])
            el = sh + d * self.upper_len; wr = el + d * self.fore_len; ht = wr + d * p['hand']
            self.j['shoulder.' + s] = sh; self.j['elbow.' + s] = el; self.j['wrist.' + s] = wr; self.j['hand_tip.' + s] = ht
            self.j['clav.' + s] = np.array([sx * 0.04, 0.0, self.z_neck - 0.03])
            hp = np.array([sx * self.hip_x, 0.0, L]); kn = np.array([sx * self.hip_x, -0.01, self.knee_z])
            an = np.array([sx * self.hip_x, 0.0, self.ankle_z])
            self.j['hip.' + s] = hp; self.j['knee.' + s] = kn; self.j['ankle.' + s] = an
            self.j['ball.' + s] = np.array([sx * self.hip_x, -0.50 * self.foot_len, kr * 0.6])
            self.j['toe.' + s] = np.array([sx * self.hip_x, -0.72 * self.foot_len, kr * 0.5])
            self.j['heel.' + s] = np.array([sx * self.hip_x, 0.26 * self.foot_len, kr * 0.6])
            self.j['foot.' + s] = np.array([sx * self.hip_x, -0.22 * self.foot_len, kr * 0.6])
        # eye anchors (VOCAB face): eye centre line a little below the head centre
        self.eye_z = self.cz - 0.10
        self.segs = self._segs()

    def _segs(self):
        j, p, S = self.j, self.p, []
        simple = self.tier == 'simple'
        hc, hr = self.head_c, self.head_r
        S.append(Seg('head', None, 'head', lambda P: sd_ellipsoid(P, hc, hr), j['chin'], j['top'], hr[0]))
        if not simple and self.preset != 'chibi':
            jc = hc + np.array([0, -0.05, -0.17]); jr = np.array([hr[0] * 0.80, hr[1] * 0.86, 0.33])
            S.append(Seg('head', None, 'head', lambda P: sd_ellipsoid(P, jc, jr), j['chin'], j['top'], hr[0]))
        nr = p['neck_r']
        S.append(Seg('neck', None, 'neck', lambda P: sd_roundcone(P, j['neck_base'] - [0, 0, .06], j['chin'] + [0, 0.02, .14], nr, nr * .92),
                     j['neck_base'], j['chin'], nr))
        cc, cr = j['chest'], self.chest_r
        zc0, zc1 = self.z_waist, self.z_neck
        S.append(Seg('chest', None, 'chest', lambda P: sd_ellipsoid(P, cc, cr), [0, 0, zc0], [0, 0, zc1], cr[0]))
        a, b = j['shoulder.R'], j['shoulder.L']; ar = self.ar
        S.append(Seg('chest', None, 'chest', lambda P: sd_roundcone(P, a, b, ar * 1.15, ar * 1.15), [0, 0, zc0], [0, 0, zc1], ar))
        if not simple and self.preset != 'chibi':
            for sx in (1, -1):
                bc = np.array([sx * self.sw * 0.16, -cr[1] * 0.55, self.z_chest - 0.04 * p['torso']]); br = self.sw * 0.13
                S.append(Seg('chest', None, 'chest', (lambda bc, br: lambda P: _len(P - bc) - br)(bc, br), [0, 0, zc0], [0, 0, zc1], br))
        bc_, br_ = j['waist'], self.belly_r
        S.append(Seg('belly', None, 'spine', lambda P: sd_ellipsoid(P, bc_, br_), [0, 0, self.z_waist - .2 * p['torso']],
                     [0, 0, self.z_waist + .2 * p['torso']], br_[0]))
        pc, pr = j['pelvis'], self.pelvis_r
        S.append(Seg('pelvis', None, 'hips', lambda P: sd_ellipsoid(P, pc, pr), pc - [0, 0, pr[2]], pc + [0, 0, pr[2]], pr[0]))
        for s in 'LR':
            sh, el, wr, ht = j['shoulder.' + s], j['elbow.' + s], j['wrist.' + s], j['hand_tip.' + s]
            S.append(Seg('upper_arm', s, 'upper_arm.' + s, (lambda a, b: lambda P: sd_roundcone(P, a, b, ar * 1.04, ar * 0.86))(sh, el), sh, el, ar))
            S.append(Seg('forearm', s, 'forearm.' + s, (lambda a, b: lambda P: sd_roundcone(P, a, b, ar * 0.86, ar * 0.70))(el, wr), el, wr, ar * .8))
            hr_ = p['hand_r'] * self.lr; d = (ht - wr) / np.linalg.norm(ht - wr)
            h0, h1 = wr + d * hr_ * 0.6, ht - d * hr_ * 0.8
            S.append(Seg('hand', s, 'hand.' + s, (lambda a, b, r: lambda P: sd_roundcone(P, a, b, r, r * 0.92))(h0, h1, hr_), wr, ht, hr_))
            hp, kn, an = j['hip.' + s], j['knee.' + s], j['ankle.' + s]
            S.append(Seg('thigh', s, 'thigh.' + s, (lambda a, b: lambda P: sd_roundcone(P, a, b, self.tr, self.sr * 1.06))(hp + [0, 0, .04], kn), hp, kn, self.tr))
            S.append(Seg('shin', s, 'shin.' + s, (lambda a, b: lambda P: sd_roundcone(P, a, b, self.sr, self.kr))(kn, an), kn, an, self.sr))
            he, to = j['heel.' + s], j['toe.' + s]; kr = self.kr
            fh = he + [0, 0, 0.0]; ft = to + [0, 0, 0.0]
            S.append(Seg('foot', s, 'foot.' + s, (lambda a, b: lambda P: np.maximum(sd_roundcone(P, a, b, kr * 1.0, kr * 0.85), -P[:, 2]))(fh, ft),
                         he, to, kr))
        return S

    def seg(self, name, side=None):
        return [s for s in self.segs if s.name == name and (side is None or s.side is None or s.side == side)]

    def sdf(self, P):
        torso = None; rest = None
        ktor = 0.16 if self.tier == 'simple' else 0.12
        for s in self.segs:
            d = s.f(P)
            if s.name in ('chest', 'belly', 'pelvis'):
                torso = d if torso is None else smin(torso, d, ktor)
            elif s.name == 'head':
                rest = d if rest is None else smin(rest, d, 0.10)
            else:
                rest = d if rest is None else smin(rest, d, 0.05)
        return smin(torso, rest, 0.06)

    def bones(self):
        j = self.j; B = []
        def add(n, h, t, par): B.append(dict(name=n, head=[float(x) for x in h], tail=[float(x) for x in t], parent=par))
        add('root', [0, 0, 0], [0, -0.4, 0], None)
        add('hips', j['pelvis'], j['waist'], 'root')
        add('spine', j['waist'], j['chest'], 'hips')
        add('chest', j['chest'], j['neck_base'], 'spine')
        add('neck', j['neck_base'], j['chin'], 'chest')
        add('head', j['chin'], j['top'], 'neck')
        for s in 'LR':
            add('shoulder.' + s, j['clav.' + s], j['shoulder.' + s], 'chest')
            add('upper_arm.' + s, j['shoulder.' + s], j['elbow.' + s], 'shoulder.' + s)
            add('forearm.' + s, j['elbow.' + s], j['wrist.' + s], 'upper_arm.' + s)
            add('hand.' + s, j['wrist.' + s], j['hand_tip.' + s], 'forearm.' + s)
            add('thigh.' + s, j['hip.' + s], j['knee.' + s], 'hips')
            add('shin.' + s, j['knee.' + s], j['ankle.' + s], 'thigh.' + s)
            add('foot.' + s, j['ankle.' + s], j['ball.' + s], 'shin.' + s)
            add('toe.' + s, j['ball.' + s], j['toe.' + s], 'foot.' + s)
        return B

    def anchor(self, name):
        """VOCAB attach anchors (centre points)."""
        j = self.j
        if name in j: return j[name].copy()
        side = None
        if name.endswith('.L') or name.endswith('.R'): name, side = name[:-2], name[-1]
        sx = -1 if side == 'R' else 1
        m = {'upper_arm': lambda s: (j['shoulder.' + s] + j['elbow.' + s]) / 2,
             'forearm': lambda s: (j['elbow.' + s] + j['wrist.' + s]) / 2,
             'hand': lambda s: (j['wrist.' + s] + j['hand_tip.' + s]) / 2,
             'thigh': lambda s: (j['hip.' + s] + j['knee.' + s]) / 2,
             'shin': lambda s: (j['knee.' + s] + j['ankle.' + s]) / 2,
             'foot': lambda s: j['foot.' + s],
             'shoulder': lambda s: j['shoulder.' + s] + [0, 0, self.ar]}
        if name in m: return m[name](side or 'L')
        if name == 'back_waist': return np.array([0, self.belly_r[1] + 0.05, self.z_waist])
        raise KeyError(name)


# ------------------------------------------------------------------------------------------------------------- layers
class Layer:
    """one buildable thing: sdf(P), material(P) -> mat index array, weight mode, line group, order (outer wins ties)."""
    def __init__(self, name, sdf, mat, weight='auto', group='auto', order=0, matf=None, paint=False):
        self.name, self.sdf, self.mat, self.weight, self.group, self.order, self.matf, self.paint = name, sdf, mat, weight, group, order, matf, paint


class Builder:
    def __init__(self, spec, tier, preset):
        self.spec, self.tier, self.preset = spec, tier, preset
        self.body = Body(preset, spec.get('body', {}).get('build'), tier)
        self.pal = dict(spec['palette'])
        self.mats = []          # (base, shade, hi) palette keys
        self.layers = []
        self.extra_bones = []   # (name, head, tail, parent)
        self.secondary = []     # [{bone, type, ...}]
        self.anchors = {}
        self.max_torso_inflate = 0.0
        self.max_limb_inflate = 0.0
        self.warnings = []

    # palette / materials
    def mat(self, base, shade=None, hi=None, auto=False):
        if base not in self.pal: raise KeyError(f'palette key {base!r} missing')
        if shade is not None and shade not in self.pal:
            self.warnings.append(f'shade key {shade!r} not in palette: derived from {base!r} (base x 0.75 value)')
            self.pal[shade] = shade_auto(self.pal[base])
        if hi is not None and hi not in self.pal:
            self.warnings.append(f'hi key {hi!r} not in palette: dropped'); hi = None
        if shade is None and auto:
            shade = base + '_auto'
            if shade not in self.pal: self.pal[shade] = shade_auto(self.pal[base])
        key = (base, shade, hi)
        if key not in self.mats: self.mats.append(key)
        return self.mats.index(key)

    def piece_mat(self, pc):
        return self.mat(pc['colour'], pc.get('shade'), pc.get('hi'), pc.get('shade_auto', False))

    # ------------------------------------------------------------------ build
    def build(self):
        sp, B = self.spec, self.body
        self.skin = self.mat('skin', 'skin_shade')
        names = sp['tiers'][self.tier]
        pieces = [(n, sp['pieces'][n]) for n in names]
        # inflate bookkeeping (straps / wraps sit on the outermost torso garment)
        for n, pc in pieces:
            if pc['geom'] == 'cover':
                segs = pc['segments']
                if any(s.startswith(('chest', 'belly', 'pelvis', 'waist', 'torso')) for s in segs):
                    self.max_torso_inflate = max(self.max_torso_inflate, pc.get('inflate', 0))
        self.layers.append(Layer('body', B.sdf, self.skin, 'auto', 'auto', 0))
        self.build_hair()
        sec = {s['part']: s for s in sp.get('secondary_motion', []) if s.get('type', 'none') != 'none'}
        self.sec_spec = sec
        for i, (n, pc) in enumerate(pieces):
            self.build_piece(n, pc, 10 + i)
        return self

    # covers ----------------------------------------------------------------
    def seg_ranges(self, name, length=None, last=False):
        """VOCAB segment name (incl. sub-ranges) -> list of (Seg, t0, t1, extra) ."""
        B = self.body; out = []
        base, rng = name, (0.0, 1.0); extra = None
        sub = {'_top': (0.0, 0.3), '_low': (0.7, 1.0)}
        for k, r in sub.items():
            if name.endswith(k): base, rng = name[:-len(k)], r
        if name == 'thigh_top_edge':
            base = 'thigh'; c = 0.3 if length is None else length; L = np.linalg.norm(B.j['knee.L'] - B.j['hip.L'])
            rng = (c - 0.02 / L, c + 0.02 / L)
        if name in ('torso_side', 'thigh_side'):
            base = {'torso_side': 'torso', 'thigh_side': 'thigh'}[name]; extra = 'side'
        if name == 'head_band':
            hb = B.eye_z + 0.34
            s = B.seg('head')[0]; t = (hb - B.z_chin)
            return [(s, t - 0.06, t + 0.06, None)]
        if name == 'waist':
            s = B.seg('belly')[0]; L = np.linalg.norm(s.b - s.a)
            return [(s, 0.0, 0.25, None)]
        if base == 'torso': segs = B.seg('chest') + B.seg('belly') + B.seg('pelvis')
        else: segs = B.seg(base)
        if base == 'pelvis' and name == 'pelvis_top': rng = (0.45, 1.0)
        if base == 'forearm' and rng[1] == 1.0: rng = (rng[0], 0.86)
        if length is not None and last and name != 'thigh_top_edge':
            if base in ('thigh', 'upper_arm', 'forearm'): rng = (0.0, length)
            elif base in ('shin',): rng = (1.0 - length, 1.0)
        return [(s, rng[0], rng[1], extra) for s in segs]

    def cover_sdf(self, segs, inflate, side=None, head=False):
        B = self.body
        parts = []
        for name_i, (s, t0, t1, extra) in enumerate(segs):
            if side and s.side and s.side != side: continue
            parts.append((s, t0, t1, extra))

        def f(P):
            dt = None; dl = None
            for s, t0, t1, extra in parts:
                d = s.f(P) - inflate
                if s.name in ('head',):
                    zt0 = B.z_chin + t0; zt1 = B.z_chin + t1
                    d = np.maximum(d, np.maximum(zt0 - P[:, 2], P[:, 2] - zt1))
                elif (t0, t1) != (0.0, 1.0):
                    d = s.clip(P, d, t0, t1)
                if extra == 'side':
                    if s.side:
                        sx = 1 if s.side == 'L' else -1
                        d = np.maximum(d, (s.a[0] * sx + s.r * 0.45) - P[:, 0] * sx)
                    else:
                        d = np.maximum(d, B.ww / 2 * 0.80 - np.abs(P[:, 0]))
                if s.name in ('chest', 'belly', 'pelvis'):
                    dt = d if dt is None else smin(dt, d, 0.10)
                else:
                    dl = d if dl is None else smin(dl, d, 0.04)
            if dt is None: return dl
            if dl is None: return dt
            return smin(dt, dl, 0.05)
        return f

    def build_piece(self, name, pc, order):
        g = pc['geom']; role = pc.get('piece', '')
        B = self.body
        if role == 'visor':
            return  # handled by the helmet (cutter + interior colour)
        if g == 'stripe_pattern':
            self.paint_stripes(name, pc, order); return
        if role == 'decal':
            dims = pc.get('dims', [0, 0, 0])
            if g in ('box', 'sphere', 'ellipsoid') and min(dims) < 0.1:
                self.paint_box(name, pc, order); return
        m = self.piece_mat(pc)
        if g == 'cover':
            segs = []
            names = pc['segments']
            for k, sn in enumerate(names):
                segs += self.seg_ranges(sn, pc.get('length'), last=(k == len(names) - 1) or sn.startswith(('thigh', 'shin')))
            side = pc.get('side')
            f = self.cover_sdf(segs, pc.get('inflate', 0.03), side)
            group = 'auto'
            if role == 'headband' or any(s == 'head_band' for s in names): group = 'hat'
            self.layers.append(Layer(name, f, m, 'auto', group, order))
            if pc.get('knot'):
                kc = B.head_c + np.array([0, B.head_r[1] + pc.get('inflate', .05), 0.05]); r = 0.09
                self.layers.append(Layer(name + '_knot', lambda P, kc=kc: _len(P - kc) - r, m, ('bone', 'head'), 'hat', order))
            return
        if g == 'strap':
            self.build_strap(name, pc, m, order); return
        # rigid primitives --------------------------------------------------------------------------------
        attach = pc.get('attach', 'chest')
        sides = [None]
        if attach in ('foot', 'hand', 'upper_arm', 'forearm', 'thigh', 'shin'):
            sides = [pc['side']] if pc.get('side') else ['L', 'R']
        for side in sides:
            for mir in ([1, -1] if pc.get('mirror') else [1]):
                self.build_rigid(name, pc, m, order, attach, side, mir)

    def attach_bone(self, attach, side):
        mp = {'head': 'head', 'neck': 'neck', 'chest': 'chest', 'belly': 'spine', 'waist': 'spine', 'pelvis': 'hips',
              'foot': 'foot', 'hand': 'hand', 'upper_arm': 'upper_arm', 'forearm': 'forearm', 'thigh': 'thigh', 'shin': 'shin'}
        b = mp.get(attach, 'chest')
        return b + '.' + side if side else b

    def build_rigid(self, name, pc, m, order, attach, side, mir):
        B = self.body; g = pc['geom']; role = pc.get('piece', '')
        anc = B.anchor(attach + ('.' + side if side else ''))
        off = np.array(pc.get('offset', [0, 0, 0]), float)
        sx = -1 if side == 'R' else 1
        off[0] *= sx * mir
        c = anc + off
        dims = np.array(pc.get('dims', [.2, .2, .2]), float); h = dims / 2
        bone = self.attach_bone(attach, side); group = {'head': 'hat', 'neck': 'body'}.get(attach, 'body')
        if role in ('backpack', 'tank', 'bag'): group = 'pack'
        if side: group = 'auto'
        weight = ('bone', bone)
        if side: weight = ('bone', bone)
        # secondary-motion bones for packs/tanks/bags
        if name in self.sec_spec:
            sec = self.sec_spec[name]; sb = name
            par = bone
            if sec['type'] == 'pendulum':
                hb = c + np.array([0, 0, h[2] + 0.25]); self.extra_bones.append((sb, hb, c, par))
            else:
                self.extra_bones.append((sb, c - np.array([0, 0, h[2]]), c + np.array([0, 0, h[2]]), par))
            self.secondary.append(dict(bone=sb, type=sec['type'], parent=par))
            weight = ('bone', sb)
        matf = None
        if role == 'helmet':
            f, matf = self.helmet(c, dims, pc, m)
        elif role == 'cap' and pc.get('brim') and g == 'sphere':
            f = self.cap(c, h, pc)
        elif role == 'cap' and g == 'cylinder':
            f = self.bucket(c, h, pc)
        elif g in ('sphere', 'ellipsoid'):
            f = (lambda c, h: lambda P: sd_ellipsoid(P, c, h))(c, h)
        elif g == 'box' and role in ('collar', 'bib'):
            f = self.wrap_box(c, h, role)
            weight = 'auto'
        elif g == 'box':
            bev = pc.get('bevel', min(h) * 0.35)
            f = (lambda c, h, bev: lambda P: sd_box(P, c, h, min(bev, min(h) * 0.95)))(c, h, bev)
            if role == 'goggles' and pc.get('lens'):
                lm = self.mat(pc['lens'], None)
                matf = (lambda c, h, lm, m: lambda P: np.where((P[:, 1] < c[1] - h[1] * 0.5) & (np.abs(np.abs(P[:, 0] - c[0]) - h[0] * 0.45) < h[0] * 0.38)
                                                              & (np.abs(P[:, 2] - c[2]) < h[2] * 0.62), lm, m))(c, h, lm, m)
        elif g == 'cylinder':
            ax = pc.get('axis', 'z')
            if ax == 'x': rx, ry, hz = h[1], h[2], h[0]
            elif ax == 'y': rx, ry, hz = h[0], h[2], h[1]
            else: rx, ry, hz = h[0], h[1], h[2]
            rr = min(rx, ry) * (0.95 if pc.get('cap') == 'hemisphere' else 0.25)
            f = (lambda c, rx, ry, hz, ax, rr: lambda P: sd_cyl(P, c, rx, ry, hz, ax, rr))(c, rx, ry, hz, ax, rr)
            if pc.get('valve'):
                vc = c + np.array([0, 0, hz + 0.04]); vm = self.mat('outline')
                f0 = f; f = lambda P, f0=f0, vc=vc: np.minimum(f0(P), sd_cyl(P, vc, 0.05, 0.05, 0.06, 'z', 0.01))
                matf = (lambda vc, vm, m: lambda P: np.where(P[:, 2] > vc[2] - 0.05, vm, m))(vc, vm, m)
            if pc.get('tip'):
                tk = pc['tip'].split(); tr = float(tk[1]) / 2 * 1.4; tcol = self.mat(tk[2], None) if tk[2] in self.pal else m
                tc = c + np.array([0, 0, hz + tr * 0.6]); f0 = f
                f = lambda P, f0=f0, tc=tc, tr=tr: np.minimum(f0(P), _len(P - tc) - tr)
                matf = (lambda tc, tr, tcol, m: lambda P: np.where(_len(P - tc) < tr * 1.3, tcol, m))(tc, tr, tcol, m)
        elif g == 'cone':
            f = self.skirt(c, dims, pc)
            weight = 'skirt'; group = 'body'
            if name in self.sec_spec: self.secondary[-1]['type'] = 'rigid_flare'; weight = 'skirt'
        else:
            raise ValueError(f'geom {g}')
        self.layers.append(Layer(name, f, m, weight, group, order, matf))

    # special rigid builders ------------------------------------------------------------------------------
    def helmet(self, c, dims, pc, m):
        r = dims / 2; th = 0.07
        vis = self.spec['pieces'].get('visor') if 'visor' in self.spec['tiers'][self.tier] else None
        if vis:
            vc = self.body.anchor(vis.get('attach', 'head')) + np.array(vis.get('offset', [0, 0, 0]))
            vr = np.array(vis['dims']) / 2
            vm = self.mat(vis['colour'], vis.get('shade'))
            ax_w = min(80.0, np.degrees(np.arcsin(min(0.99, vr[0] / r[0]))) * 1.75)
            el_w = min(50.0, np.degrees(np.arcsin(min(0.99, vr[2] / r[2]))) * 0.95)
        else:
            vc = None; vm = self.mat(pc['colour'], pc.get('shade'))
        def f(P):
            d = sd_ellipsoid(P, c, r)
            sh = np.abs(d + th / 2) - th / 2
            if vc is not None:
                # angular window (from the helmet centre) so the visor wraps round and still reads in 3/4 and profile
                q = P - c
                az = np.degrees(np.arctan2(q[:, 0], -q[:, 1])); el = np.degrees(np.arctan2(q[:, 2] - (vc[2] - c[2]), np.hypot(q[:, 0], q[:, 1])))
                cut = (np.sqrt((az / ax_w) ** 2 + (el / el_w) ** 2) - 1.0) * 0.2
                sh = np.maximum(sh, -cut)
            return sh
        def matf(P):
            d = sd_ellipsoid(P, c, r)
            return np.where(d < -th * 0.5, vm, m)
        # glint anchor (detailed): upper-left inside the visor rim
        if vc is not None:
            self.anchors['glint'] = (vc + np.array([vr[0] * 0.55, -vr[1] * 0.2, vr[2] * 0.55])).tolist()
            self.visor = dict(c=vc.tolist(), r=vr.tolist())
        return f, matf

    def cap(self, c, h, pc):
        B = self.body
        def f(P):
            d = sd_ellipsoid(P, c, h)
            d = np.maximum(d, (c[2] - h[2] * 0.15) - P[:, 2])
            bc = np.array([c[0], c[1] - h[1] - 0.12, c[2] - h[2] * 0.12])
            Rb = rot_x(-10)
            db = sd_box(P, bc, np.array([0.28, 0.20, 0.025]), 0.02, Rb)
            return np.minimum(d, db)
        return f

    def bucket(self, c, h, pc):
        def f(P):
            d = sd_cyl(P, c, h[0], h[1], h[2], 'z', 0.06)
            rr = np.sqrt((P[:, 0] - c[0]) ** 2 + (P[:, 1] - c[1]) ** 2)
            z0 = c[2] - h[2] + 0.02; zb = z0 - np.tan(np.radians(15)) * np.maximum(rr - h[0] * 0.9, 0)
            db = np.maximum(np.abs(P[:, 2] - zb) - 0.025, rr - 0.75 / 1.0 * 0.9)
            return np.minimum(d, db)
        return f

    def wrap_box(self, c, h, role):
        """collar / bib: the box volume intersected with a shell just outside the torso garment."""
        B = self.body
        tors = self.cover_sdf(self.seg_ranges('torso'), self.max_torso_inflate + 0.02)
        hh = h.copy(); hh[1] = max(h[1], 0.6)
        if role == 'bib':
            hh[1] = 0.6; cc = c.copy(); cc[1] = c[1] - 0.6 + h[1]
        else:
            cc = c
        def f(P):
            return np.maximum(tors(P), sd_box(P, cc, hh, 0.02))
        return f

    def skirt(self, c, dims, pc):
        B = self.body
        ztop = B.z_waist - 0.02
        zbot = c[2] - dims[2] / 2
        rt = (B.ww / 2 + self.max_torso_inflate * 0.5 + 0.03, B.belly_r[1] + 0.05)
        rb = (dims[0] / 2, dims[1] / 2)
        self.skirt_info = dict(ztop=ztop, zbot=zbot, rb=rb)
        return lambda P: sd_econe(P, ztop, zbot, rt, rb, (0, 0.02)) - 0.0

    def build_strap(self, name, pc, m, order):
        B = self.body
        sides = [1, -1] if pc.get('mirror') else [1]
        for sx in sides:
            fr, to = pc['from'], pc['to']
            def pt(n, s):
                if n == 'shoulder': return np.array([s * B.sh_x * 0.62, 0, B.z_neck + 0.05])
                if n == 'shoulder.R': return np.array([-B.sh_x * 0.62, 0, B.z_neck + 0.05])
                if n == 'waist': return np.array([s * B.ww * 0.30, 0, B.z_waist - 0.05])
                if n == 'back_waist': return np.array([s * B.ww * 0.30, 0, B.z_waist])
                if n == 'bib_corner': return np.array([s * 0.22, 0, B.z_chest + 0.1])
                if n == 'bag':
                    bp = self.spec['pieces'].get('bag', {})
                    return B.anchor(bp.get('attach', 'pelvis')) + np.array(bp.get('offset', [0, 0, 0])) * [-1 if False else 1, 0, 1]
                return B.anchor(n)
            a, b = pt(fr, sx), pt(to, sx)
            dv = b - a; dv[1] = 0; dv /= np.linalg.norm(dv)
            nrm = np.cross(dv, [0, 1, 0]); nrm /= np.linalg.norm(nrm)
            w = pc.get('width', 0.07) / 2
            zlo, zhi = min(a[2], b[2]) - 0.05, max(a[2], b[2]) + 0.12
            tors = self.cover_sdf(self.seg_ranges('torso') + self.seg_ranges('chest'), self.max_torso_inflate + 0.025)
            f = (lambda a, nrm, w, zlo, zhi, tors: lambda P: np.maximum(np.maximum(tors(P), np.abs((P - a) @ nrm) - w),
                                                                          np.maximum(zlo - P[:, 2], P[:, 2] - zhi)))(a, nrm, w, zlo, zhi, tors)
            self.layers.append(Layer(f'{name}{sx}', f, m, 'auto', 'body', order))

    # paint --------------------------------------------------------------------------------------------------
    def paint_box(self, name, pc, order):
        B = self.body; m = self.mat(pc['colour'], pc.get('shade'))
        attach = pc.get('attach', 'chest')
        sides = [None]
        if attach in ('foot', 'hand', 'upper_arm', 'forearm', 'thigh', 'shin'):
            sides = [pc['side']] if pc.get('side') else ['L', 'R']
        for side in sides:
            for mir in ([1, -1] if pc.get('mirror') else [1]):
                anc = B.anchor(attach + ('.' + side if side else ''))
                off = np.array(pc.get('offset', [0, 0, 0]), float); sx = -1 if side == 'R' else 1
                off[0] *= sx * mir; c = anc + off; h = np.array(pc['dims'], float) / 2
                # project along the thin axis: grow it so the box reaches the surface it sits on
                k = int(np.argmin(h)); hh = h.copy(); hh[k] = max(h[k], 0.18)
                if pc['geom'] in ('sphere', 'ellipsoid'):
                    f = (lambda c, hh: lambda P: sd_ellipsoid(P, c, hh))(c, hh)
                else:
                    f = (lambda c, hh: lambda P: sd_box(P, c, hh))(c, hh)
                self.layers.append(Layer(name, f, m, paint=True, order=order))

    def paint_stripes(self, name, pc, order):
        m = self.mat(pc['colour'], None)
        n = int(pc.get('count', 8)); B = self.body
        def f(P):
            th = np.arctan2(P[:, 0], -P[:, 1] + 0.02)
            fr = (th * n / (2 * np.pi)) % 1.0
            inside = (np.abs(fr - 0.5) < 0.07)
            si = getattr(self, 'skirt_info', None)
            if si is None: return np.full(len(P), 1.0)
            z = P[:, 2]; band = (z < si['ztop'] - (si['ztop'] - si['zbot']) * 0.25) & (z > si['zbot'] - 0.02)
            return np.where(inside & band, -1.0, 1.0)
        self.layers.append(Layer(name, f, m, paint=True, order=order))

    # hair -----------------------------------------------------------------------------------------------------
    def build_hair(self):
        hs = self.spec.get('hair', {}); B = self.body
        style = hs.get('style', 'short_bob')
        covered = style == 'helmet_covered'
        if style in ('helmet_covered', 'cap'): style = hs.get('under', 'short_bob')
        hm = self.mat(hs.get('colour', 'hair'), hs.get('shade'), hs.get('hi'))
        self.hair_mat = hm
        c, r = B.head_c, B.head_r
        vol = hs.get('volume', 1.0)
        th = {'pixie': 0.045, 'short_bob': 0.05, 'ponytail': 0.03, 'buns': 0.028}.get(style, 0.04) + (vol - 1.0) * 0.35
        eye_top = B.eye_z + 0.07
        z_hl = c[2] + 0.30                                       # front hairline
        z_ear = B.eye_z - 0.02
        L = hs.get('length', 0.3)
        z_chin = B.z_chin; z_shoulder = B.z_neck + 0.05
        z_len = z_ear + (z_chin - z_ear) * (L / 0.5) if L <= 0.5 else z_chin + (z_shoulder - z_chin) * ((L - 0.5) / 0.5)
        if style == 'pixie':
            z_side, z_back = B.eye_z + 0.05, z_chin + 0.12
        elif style == 'short_bob':
            z_side, z_back = z_ear + 0.02, z_ear
        else:  # ponytail / buns: pulled back
            z_side, z_back = B.eye_z + 0.10, z_chin + 0.22
        fringe = hs.get('fringe', 'none'); fl = hs.get('fringe_length', 0.4)
        part = 1 if hs.get('part', 'left') == 'left' else -1
        z_fr = z_hl - fl * (z_hl - eye_top) - 0.02

        def cut(P):
            x, y = P[:, 0] - c[0], P[:, 1] - c[1]
            ang = np.arctan2(x, -y); cf = np.cos(ang)
            u = np.clip(cf / 0.55, 0, 1); wf = u * u * (3 - 2 * u)          # face opening spans ~ +-55 deg
            wb = np.maximum(-cf, 0) ** 1.2
            zc = z_side + (z_hl - z_side) * wf + (z_back - z_side) * wb
            if style == 'pixie':  # nape point
                zc = zc - 0.12 * np.maximum(-cf, 0) ** 8
            return (zc - P[:, 2]) * 0.8

        def shell(P):
            return np.maximum(sd_ellipsoid(P, c, r + th), cut(P))

        parts = [shell]
        if fringe != 'none':
            fw = r[0] * 0.95
            def fr_(P):
                x = P[:, 0] - c[0]
                if fringe == 'side_swept':
                    zb = z_fr + 0.06 * (x * part / fw) + 0.04 * np.maximum(x * part / fw, 0)
                else:
                    zb = z_fr + 0.02 * (x / fw) ** 2
                d = sd_ellipsoid(P, c, r + th * 0.75)
                d = np.maximum(d, zb - P[:, 2])
                d = np.maximum(d, (P[:, 1] - (c[1] - r[1] * 0.15)))
                d = np.maximum(d, (np.abs(x) * 0.85 - (c[1] - P[:, 1])) * 0.7)   # front wedge only: profile keeps the cheek
                return d
            parts.append(fr_)
        if style == 'short_bob' and not covered:
            zt, zb = c[2] + r[2] + th, z_len
            bc = np.array([0, 0.03, (zt + zb) / 2]); br = np.array([r[0] + th * 1.15, r[1] + th * 1.1, (zt - zb) / 2])
            fw = r[0] * 0.78
            def bob(P):
                d = sd_ellipsoid(P, bc, br)
                d = np.maximum(d, zb - P[:, 2])
                face = sd_box(P, np.array([0, c[1] - r[1] - 0.2, (z_fr + zb) / 2 - 0.15]), np.array([fw, r[1] * 0.9 + 0.2, (z_fr - zb) / 2 + 0.15]), 0.05)
                return np.maximum(d, -face)
            parts.append(bob)
        if covered:
            parts = [lambda P: np.maximum(shell(P), P[:, 1] - c[1])] + parts[1:]

        def hair(P):
            d = parts[0](P)
            for q in parts[1:]: d = smin(d, q(P), 0.02)
            return d
        self.layers.append(Layer('hair', hair, hm, ('bone', 'head'), 'hair', 5))
        sec = {s['part']: s for s in self.spec.get('secondary_motion', []) if s.get('type', 'none') != 'none'}
        if style == 'ponytail':
            self.build_tail(hs, hm, th, sec)
        if style == 'buns':
            n = hs.get('bun_count', 1); rb = hs.get('bun_radius', 0.2)
            for k in range(n):
                sx = 0 if n == 1 else (1 if k == 0 else -1)
                d = np.array([sx * 0.6, 0.55, 0.65]); d /= np.linalg.norm(d)
                bc = c + d * (r + th) * 0.95 + d * rb * 0.55
                self.layers.append(Layer('bun', (lambda bc: lambda P: _len(P - bc) - rb)(bc), hm, ('bone', 'head'), 'hair', 6))

    def build_tail(self, hs, hm, th, sec):
        B = self.body; c, r = B.head_c, B.head_r
        pos = hs.get('tail_pos', 'high_back')
        base = c + (np.array([0, r[1] * 0.92, 0.22]) if pos == 'high_back' else np.array([0, r[1] * 0.62, 0.40]))
        n = int(hs.get('tail_segments', 3)); taper = hs.get('tail_taper', 0.55)
        total = hs.get('length', 0.9) * 1.25
        pts = [base]; ang0 = math.radians(35 if pos == 'high_back' else 20)
        for k in range(n):
            a = ang0 + (math.radians(80) - ang0) * (k + 1) / n       # angle below horizontal, getting steeper
            seg = total / n
            pts.append(pts[-1] + np.array([0, math.cos(a) * seg, -math.sin(a) * seg]))
        r0 = 0.14 * hs.get('volume', 1.0)
        rads = [r0 * (1 - (1 - taper) * k / n) for k in range(n + 1)]
        names = []
        spring = 'ponytail' in sec
        for k in range(n):
            bn = f'tail.{k + 1}'; names.append(bn)
            self.extra_bones.append((bn, pts[k], pts[k + 1], 'head' if k == 0 else f'tail.{k}'))
        if spring:
            s = sec['ponytail']
            self.secondary.append(dict(bone='tail', type='spring_chain', bones=names, stiffness=s.get('stiffness', 'medium')))
        P0 = np.array(pts)
        def tail(P):
            d = None
            for k in range(n):
                dk = sd_roundcone(P, P0[k], P0[k + 1], rads[k], rads[k + 1])
                d = dk if d is None else smin(d, dk, 0.04)
            # tie at the base
            return smin(d, _len(P - base) - r0 * 1.05, 0.03)
        self.tail_pts = P0
        self.layers.append(Layer('ponytail', tail, hm, 'chain', 'hair', 6))

    # ----------------------------------------------------------------------------------------------- evaluate
    def bbox(self):
        J = np.array(list(self.body.j.values()))
        lo = J.min(0) - 0.85; hi = J.max(0) + 0.85
        lo[2] = -0.02; hi[2] = self.body.top + 0.6
        return lo, hi

    def mesh(self):
        from skimage import measure
        lo, hi = self.bbox()
        vox = self.body.total / TIER_RES[self.tier]
        n = np.ceil((hi - lo) / vox).astype(int) + 1
        xs = [lo[i] + np.arange(n[i]) * vox for i in range(3)]
        geo = [L for L in self.layers if not L.paint]
        vol = np.empty(n, np.float32)
        X, Y = np.meshgrid(xs[0], xs[1], indexing='ij')
        XY = np.stack([X.ravel(), Y.ravel()], 1)
        for k in range(n[2]):    # z slices keep memory low
            P = np.concatenate([XY, np.full((len(XY), 1), xs[2][k])], 1)
            d = np.full(len(P), 1e3)
            for L in geo: d = np.minimum(d, L.sdf(P))
            vol[:, :, k] = d.reshape(n[0], n[1])
        vol[:, :, 0] = np.maximum(vol[:, :, 0], vox * 0.5)  # closed under the floor plane
        V, F, Nn, _ = measure.marching_cubes(vol, 0.0, spacing=(vox, vox, vox))
        # toon normals: gradient of the blurred field (big, clean cel shapes; small bumps don't break the bands)
        from scipy import ndimage as ndi
        sig = TOON_SIGMA * (self.body.total / 3.5) / vox
        bl = ndi.gaussian_filter(vol, sig)
        g = np.gradient(bl)
        idx = (V / vox).T
        Nt = np.stack([ndi.map_coordinates(gi, idx, order=1, mode='nearest') for gi in g], 1)
        Nt /= np.maximum(np.linalg.norm(Nt, axis=1, keepdims=True), 1e-9)
        V = V + lo
        self.toon = Nt.astype(np.float32)
        return V.astype(np.float64), F.astype(np.int32), vox

    def owner(self, P):
        geo = [L for L in self.layers if not L.paint]
        D = np.stack([L.sdf(P) - 1e-4 * L.order for L in geo], 1)
        return geo, D.argmin(1), D

    def run(self):
        V, F, vox = self.mesh()
        geo, ov, Dv = self.owner(V)
        C = V[F].mean(1)
        _, of, _ = self.owner(C)
        # face materials
        fmat = np.zeros(len(F), np.int32)
        for i, L in enumerate(geo):
            sel = of == i
            if not sel.any(): continue
            fmat[sel] = L.matf(C[sel]) if L.matf else L.mat
        for L in self.layers:
            if L.paint:
                sel = L.sdf(C) < 0
                # paint only onto garments/pieces (never onto skin/hair/visor) unless the decal sits on skin on purpose
                sel &= (fmat != self.skin) & (fmat != self.hair_mat)
                fmat[sel] = L.mat
        # weights
        bones = self.body.bones() + [dict(name=n, head=[float(x) for x in h], tail=[float(x) for x in t], parent=p) for n, h, t, p in self.extra_bones]
        bidx = {b['name']: i for i, b in enumerate(bones)}
        W = np.zeros((len(V), len(bones)), np.float32)
        segs = self.body.segs
        Dseg = np.stack([s.f(V) for s in segs], 1)
        tau = 0.045
        dmin = Dseg.min(1, keepdims=True)
        E = np.exp(-(Dseg - dmin) / tau)
        auto = np.zeros_like(W)
        for k, s in enumerate(segs): auto[:, bidx[s.bone]] += E[:, k]
        auto /= auto.sum(1, keepdims=True)
        for i, L in enumerate(geo):
            sel = ov == i
            if not sel.any(): continue
            if L.weight == 'auto':
                W[sel] = auto[sel]
            elif L.weight == 'chain':
                W[sel] = self.chain_weights(V[sel], bidx, len(bones))
            elif L.weight == 'skirt':
                W[sel] = self.skirt_weights(V[sel], bidx, len(bones))
            else:
                W[sel, bidx[L.weight[1]]] = 1.0
        # top-4
        idx = np.argsort(-W, 1)[:, :4]
        wt = np.take_along_axis(W, idx, 1); wt[wt < 0.01] = 0; wt /= wt.sum(1, keepdims=True)
        # face groups
        gi = {g: i for i, g in enumerate(GROUPS)}
        fgrp = np.zeros(len(F), np.int32)
        dom = np.array([bones[i]['name'] for i in idx[:, 0]])
        for i, L in enumerate(geo):
            sel = np.nonzero(of == i)[0]
            if not len(sel): continue
            if L.group != 'auto':
                fgrp[sel] = gi[L.group]; continue
            vb = dom[F[sel, 0]]
            g = np.array([bone_group(b) for b in vb])
            fgrp[sel] = [gi[x] for x in g]
        # anchors: eye surface vertices on head skin
        B = self.body
        anchors = {}
        head_v = np.nonzero((ov == 0) & (V[:, 2] > B.z_chin + 0.15) & (V[:, 1] < 0))[0]
        es = self.spec.get('face', {}).get('eye_spacing', 0.3) / 2
        for s, sx in (('L', 1), ('R', -1)):
            tgt = np.array([sx * es, -B.head_r[1], B.eye_z])
            k = head_v[np.argmin(_len(V[head_v] - tgt * [1, 1, 1]) + 0.0)]
            anchors['eye.' + s] = int(k)
        if 'glint' in self.anchors:
            g = np.array(self.anchors['glint'])
            hv = np.nonzero(np.array([geo[o].name == 'helmet' for o in ov]))[0]
            if len(hv): anchors['glint'] = int(hv[np.argmin(_len(V[hv] - g))])
        return dict(N=self.toon, V=V, F=F, fmat=fmat, fgrp=fgrp, widx=idx.astype(np.int16), wval=wt.astype(np.float32), bones=bones,
                    anchors=anchors, vox=vox)

    def chain_weights(self, P, bidx, nb):
        W = np.zeros((len(P), nb), np.float32); T = self.tail_pts; n = len(T) - 1
        # parameter along the polyline
        best = np.full(len(P), 1e9); par = np.zeros(len(P))
        for k in range(n):
            a, b = T[k], T[k + 1]; ab = b - a; t = np.clip(((P - a) @ ab) / (ab @ ab), 0, 1)
            d = _len(P - (a + t[:, None] * ab)); m = d < best; best[m] = d[m]; par[m] = k + t[m]
        for i in range(len(P)):
            u = par[i] - 0.5
            k0 = int(np.clip(np.floor(u), -1, n - 1)); fr = u - k0
            b0 = 'head' if k0 < 0 else f'tail.{k0 + 1}'; b1 = f'tail.{min(k0 + 2, n)}'
            W[i, bidx[b0]] += 1 - fr; W[i, bidx[b1]] += fr
        return W

    def skirt_weights(self, P, bidx, nb):
        si = self.skirt_info; W = np.zeros((len(P), nb), np.float32)
        fr = np.clip((si['ztop'] - P[:, 2]) / (si['ztop'] - si['zbot']), 0, 1) ** 1.3
        rx = si['rb'][0]
        hipb = 'skirt' if 'skirt' in bidx else 'hips'
        for s, sx in (('L', 1), ('R', -1)):
            u = np.clip((P[:, 0] * sx / rx + 0.15) / 0.75, 0, 1)
            w = 0.42 * fr * u * u * (3 - 2 * u)
            W[:, bidx['thigh.' + s]] = w
        W[:, bidx[hipb]] = 1 - W.sum(1)
        return W


def bone_group(b):
    if b in BONE_GROUP: return BONE_GROUP[b]
    s = b[-1]
    if b.startswith(('shoulder', 'upper_arm', 'forearm', 'hand')): return 'arm' + s
    if b.startswith(('thigh', 'shin', 'foot', 'toe')): return 'leg' + s
    if b.startswith('tail'): return 'hair'
    return 'body'


# ------------------------------------------------------------------------------------------------------------- colour
def hex2rgb(h):
    h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb2hex(c):
    return '#%02x%02x%02x' % tuple(int(round(max(0, min(255, v)))) for v in c)


def shade_auto(hx):
    """VOCAB: base x 0.75 value, nudged slightly toward blue-violet so the shade is not muddy."""
    import colorsys
    r, g, b = [v / 255 for v in hex2rgb(hx)]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    v *= 0.75; s = min(1, s * 1.08 + 0.04)
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return rgb2hex((r * 255, g * 255, b * 255))


def build(spec_path, tier, preset, out):
    spec = json.load(open(spec_path))
    b = Builder(spec, tier, preset).build()
    R = b.run()
    B = b.body
    secondary = list(b.secondary)
    # hair rigid lag (VOCAB rigid_lag on the hair) and helmet lag are motion-only (no extra geometry)
    for s in spec.get('secondary_motion', []):
        if s.get('type') == 'rigid_lag' and s['part'].startswith('hair'):
            secondary.append(dict(bone='head', type='rigid_lag_head', note='hair follows head; lag applied to head bob only'))
    meta = dict(id=spec['id'], name=spec.get('name', spec['id']), tier=tier, preset=preset, H=1.0, total=B.total,
                bones=R['bones'], mats=b.mats, palette=b.pal, groups=GROUPS, anchors=R['anchors'],
                secondary=secondary, face=spec.get('face', {}), vox=R['vox'],
                walk=dict(hip_x=B.hip_x, ankle_z=B.ankle_z, foot_len=B.foot_len, legs=B.p['legs'], thigh=float(np.linalg.norm(B.j['knee.L'] - B.j['hip.L'])),
                          shin=float(np.linalg.norm(B.j['ankle.L'] - B.j['knee.L'])), hip_half=B.hw / 2, sh_x=B.sh_x,
                          arm=B.upper_len + B.fore_len, abduct=B.p['abduct'], hand_r=B.p['hand_r'] * B.lr,
                          torso=B.p['torso'], cloth=float(b.max_torso_inflate)),
                skin_mat=b.skin, hair_mat=b.hair_mat, eye_z=B.eye_z, head_c=B.head_c.tolist(), head_r=B.head_r.tolist(),
                tris=int(len(R['F'])), verts=int(len(R['V'])), warnings=b.warnings)
    np.savez_compressed(out, N=R['N'], V=R['V'].astype(np.float32), F=R['F'], fmat=R['fmat'].astype(np.uint8), fgrp=R['fgrp'].astype(np.uint8),
                        widx=R['widx'], wval=R['wval'])
    json.dump(meta, open(os.path.splitext(out)[0] + '.json', 'w'), indent=1)
    return meta


if __name__ == '__main__':
    import time
    t = time.time()
    m = build(*sys.argv[1:5])
    print(f"MODEL {m['id']} {m['tier']} {m['preset']}: {m['verts']} verts {m['tris']} tris, {len(m['mats'])} mats, "
          f"{len(m['bones'])} bones, {time.time() - t:.1f}s", flush=True)
