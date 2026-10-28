# finalize.py METHOD PARTS_DIR OUT_ROOT [katana_raw.glb]
# Writes OUT_ROOT/METHOD/<part>.glb (Y-up, faces +Z, feet y=-1 frame of the 2mv mesh), a combined scene METHOD_assembled.glb with
# one named node per part, and pivots.json (bone pivot per part = joint it binds to 1:1; derived from part bboxes).
import sys, os, glob, json, numpy as np, trimesh
meth, pd, root = sys.argv[1:4]; kat = sys.argv[4] if len(sys.argv) > 4 else None
od = f'{root}/{meth}'; os.makedirs(od, exist_ok=True)
P = {os.path.basename(f)[:-4]: trimesh.load(f, force='mesh') for f in sorted(glob.glob(f'{pd}/*.glb'))}
def piv(n, m):
    lo, hi = m.bounds; c = (lo + hi) / 2
    if n in ('head', 'bow', 'bun'): b = P['head'].bounds; return [0, b[0][1] + 0.02, (b[0][2] + b[1][2]) / 2], 'head', 'neck'
    if n == 'torso': return [0, lo[1], c[2]], 'chest', 'spine'
    if n == 'skirt': return [0, hi[1], c[2]], 'skirt', 'hips'
    if n.startswith('arm_'):
        s = np.sign(c[0]); tv = m.vertices[m.vertices[:, 1] > hi[1] - 0.06]
        if os.environ.get('ARMPIV') == 'top':  # shoulder = centre of the sleeve top, nudged outward -> sleeve does not sweep into the chest
            return [tv[:, 0].mean() + s * 0.015, hi[1] - 0.02, tv[:, 2].mean()], 'upper_arm.' + n[-1], 'chest'
        return [lo[0] if s > 0 else hi[0], hi[1] - 0.03, c[2]], 'upper_arm.' + n[-1], 'chest'
    if n.startswith('leg_'): return [c[0], hi[1] - 0.04, c[2]], 'thigh.' + n[-1], 'hips'
    if n.startswith('boot_'): return [c[0], hi[1], c[2]], 'foot.' + n[-1], 'thigh.' + n[-1]
    return c.tolist(), n, 'root'
if kat:  # katana prop from 2mini: colour by height bands (hilt / guard / blade), length 0.95, held in the right hand angled out 22 deg
    k = trimesh.load(kat, force='mesh'); y = k.vertices[:, 1]; t = (y.max() - y) / (y.max() - y.min())
    lin = lambda c: (np.where(np.array(c) / 255 <= 0.04045, np.array(c) / 255 / 12.92, ((np.array(c) / 255 + 0.055) / 1.055) ** 2.4) * 255).round()
    col = np.where((t < 0.24)[:, None], lin([0x2c, 0x20, 0x2c]), np.where((t < 0.31)[:, None], lin([0x8a, 0x5a, 0x3a]), lin([0xa8, 0xb0, 0xc0])))
    k.visual = trimesh.visual.ColorVisuals(k, vertex_colors=np.c_[col, np.full(len(col), 255)].astype(np.uint8))
    s = 0.95 / (y.max() - y.min()); grip = np.array([0, y.max() - 0.12 * (y.max() - y.min()), 0])
    a = P['arm_R']; hand = np.array([a.bounds[0][0] + 0.03, a.bounds[0][1] + 0.03, (a.bounds[0][2] + a.bounds[1][2]) / 2 + 0.03])
    R = trimesh.transformations.rotation_matrix(np.radians(-22), [0, 0, 1])
    k.apply_translation(-grip); k.apply_scale(s); k.apply_transform(R); k.apply_translation(hand)
    k.export(f'{od}/katana.glb')
lin = lambda c: (np.where(np.array(c) / 255 <= 0.04045, np.array(c) / 255 / 12.92, ((np.array(c) / 255 + 0.055) / 1.055) ** 2.4) * 255).round().astype(np.uint8)
RED, OBI = np.r_[lin([0xc0, 0x3a, 0x3c]), 255], np.r_[lin([0x44, 0x37, 0x4a]), 255]
PIV = {n: piv(n, m) for n, m in P.items()}  # pivots from the raw part bboxes
if 'torso' in P and os.environ.get('OBI', '1') == '1':  # clean straight obi band (nearest-vertex colours were ragged after decimation)
    t = P['torso']; y = t.vertices[:, 1]; vc = t.visual.vertex_colors.copy()
    ob = (y > -0.25) & (y < -0.105); vc[ob] = OBI; vc[(~ob) & (np.abs(vc[:, :3].astype(int) - OBI[:3]).sum(1) < 12)] = RED
    t.visual = trimesh.visual.ColorVisuals(t, vertex_colors=vc)
for n in [k for k in P if k.startswith('arm_')]:  # shoulder ball: stays at the pivot when the arm rotates -> no gap at the socket
    m = P[n]; p = np.array(PIV[n][0]); v = m.vertices
    top = v[v[:, 1] > m.bounds[1][1] - 0.06]; r = 0.5 * max(np.ptp(top[:, 0]), np.ptp(top[:, 2]), 0.08)
    if os.environ.get('ARMPIV') == 'top': r *= 0.75   # smaller ball tucked inside the sleeve cap
    b = trimesh.creation.icosphere(3, radius=r); b.apply_translation(p - [np.sign(p[0]) * r * 0.3, r * (0.6 if os.environ.get('ARMPIV') == 'top' else 0.35), 0])
    b.visual = trimesh.visual.ColorVisuals(b, vertex_colors=np.tile(RED, (len(b.vertices), 1)))
    P[n] = trimesh.util.concatenate([m, b])
sc = trimesh.Scene(); info = {}
for n, m in P.items():
    m.export(f'{od}/{n}.glb'); p, bone, parent = PIV[n] if n in PIV else piv(n, m)
    info[n] = dict(bone=bone, parent=parent, pivot=np.round(p, 4).tolist(), faces=len(m.faces), watertight=bool(m.is_watertight))
    sc.add_geometry(m, node_name=n, geom_name=n)
sc.export(f'{root}/{meth}_assembled.glb')
json.dump(info, open(f'{od}/pivots.json', 'w'), indent=1); print(meth, len(P), 'parts ->', od)
