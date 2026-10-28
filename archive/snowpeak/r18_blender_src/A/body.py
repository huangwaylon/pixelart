"""Body (neck/torso/arms under clothing) and Tights (legs)."""
import math
from mathutils import Vector
import lib
from lib import gauss, smoothstep

NS = 12   # half-ring segments

def half_ring(W, F, B, cy, z, n=2.3, ns=NS, bust=0.0, bust_z=None):
    pts = []
    for k in range(ns + 1):
        phi = math.pi * k / ns
        s, c = math.sin(phi), math.cos(phi)
        e = 2.0 / n
        x = W * abs(s) ** e
        d = F if c >= 0 else B
        y = cy - d * math.copysign(abs(c) ** e, c)
        pts.append(Vector((x, y, z)))
    pts[0].x = 0; pts[-1].x = 0
    return pts

# z, W, F, B, cy, n
TORSO = [
    (1.250, 0.031, 0.028, 0.033, 0.004, 2.0),
    (1.236, 0.046, 0.037, 0.040, 0.006, 2.0),
    (1.222, 0.105, 0.050, 0.050, 0.010, 2.4),
    (1.200, 0.140, 0.062, 0.056, 0.012, 2.6),
    (1.170, 0.140, 0.074, 0.060, 0.012, 2.6),
    (1.135, 0.122, 0.088, 0.064, 0.012, 2.5),
    (1.100, 0.108, 0.082, 0.062, 0.012, 2.4),
    (1.065, 0.094, 0.068, 0.058, 0.012, 2.3),
    (1.030, 0.086, 0.060, 0.056, 0.012, 2.2),
    (0.990, 0.098, 0.062, 0.062, 0.014, 2.2),
    (0.940, 0.122, 0.066, 0.074, 0.016, 2.3),
    (0.890, 0.134, 0.068, 0.078, 0.016, 2.4),
    (0.850, 0.132, 0.066, 0.074, 0.014, 2.4),
]

def torso_rings(offset=0.0, rows=TORSO, sub=2, bust=True):
    tab = [(r[0],) + r[1:] for r in rows]
    tab = [(-r[0],) + r[1:] for r in tab]  # interp needs ascending key
    tab.sort()
    out = []
    zs = [r[0] for r in rows]
    n = (len(rows) - 1) * sub + 1
    for i in range(n):
        z = zs[0] + (zs[-1] - zs[0]) * i / (n - 1)
        W, F, B, cy, ne = lib.interp_table(tab, -z)
        ring = half_ring(W + offset, F + offset, B + offset, cy, z, ne)
        if bust:
            for v in ring:
                if v.y < cy:
                    v.y -= 0.016 * gauss(v.x - 0.052, 0.034) * gauss(z - 1.132, 0.040)
        out.append(ring)
    return out

SHOULDER = Vector((0.118, 0.008, 1.188))
ARM_DIR = Vector((math.sin(math.radians(40)), 0.0, -math.cos(math.radians(40))))

def arm_path():
    S = SHOULDER
    E = S + ARM_DIR * 0.25
    d2 = Vector((0.60, -0.10, -0.79)).normalized()
    Wr = E + d2 * 0.215
    return [S - ARM_DIR * 0.03, S, S.lerp(E, 0.5), E, E.lerp(Wr, 0.5), Wr], Wr, d2

HIP = Vector((0.072, 0.010, 0.86))

def leg_path():
    return [HIP + Vector((0, 0, 0.06)), HIP, Vector((0.078, 0.004, 0.62)), Vector((0.083, 0.000, 0.45)),
            Vector((0.086, 0.010, 0.30)), Vector((0.088, 0.016, 0.12)), Vector((0.088, 0.018, 0.06))]

def leg_radius(z):
    # (z, r_side, r_front, r_back)
    tab = [(0.06, 0.026, 0.026, 0.028), (0.12, 0.028, 0.027, 0.030), (0.22, 0.034, 0.032, 0.040),
           (0.32, 0.042, 0.037, 0.050), (0.40, 0.040, 0.037, 0.040), (0.46, 0.037, 0.037, 0.036),
           (0.54, 0.043, 0.043, 0.041), (0.64, 0.052, 0.050, 0.049), (0.76, 0.062, 0.058, 0.058),
           (0.86, 0.070, 0.062, 0.068), (0.92, 0.072, 0.064, 0.072)]
    return lib.interp_table(tab, z)

def build_legs(name, mat, extra=0.0, z_top=0.92, z_bot=0.055, nr=18, ns=12):
    pts = lib.catmull(leg_path(), 6)
    rings = []
    for i in range(nr):
        z = z_top + (z_bot - z_top) * i / (nr - 1)
        # find path point at z
        best = min(pts, key=lambda p: abs(p.z - z))
        cx, cy = best.x, best.y
        rs, rf, rb = leg_radius(z)
        ring = []
        for k in range(ns):
            a = 2 * math.pi * k / ns
            ca, sa = math.cos(a), math.sin(a)   # a=0 -> +x (outer side)
            ry = (rf if sa < 0 else rb) + extra
            ring.append(Vector((cx + (rs + extra) * ca, cy + ry * sa, z)))
        rings.append(ring)
    v, f = lib.loft(rings, True, cap_start=False, cap_end=True)
    ob = lib.new_obj(name, v, f, outward_from=(0.08, 0.01, 0.5))
    lib.set_mat(ob, mat)
    m = ob.modifiers.new('Mirror', 'MIRROR'); m.use_axis[0] = True; m.use_mirror_merge = False
    lib.add_subsurf(ob, 1)
    return ob

def build(mats):
    rings = torso_rings(-0.008)
    ns = NS + 1
    verts = [v for r in rings for v in r]
    faces = lib.grid_faces(len(rings), ns, closed=False)
    body = lib.new_obj('Body', verts, faces, outward_from=(0, 0.01, 1.05))
    lib.set_mat(body, mats['skin'])
    lib.add_mirror(body)
    tights = build_legs('Tights', mats['tights'])
    # pelvis/briefs part of tights so there is no gap under the skirt
    pr = torso_rings(0.004, TORSO[-4:], 2, bust=False)
    v2 = [v for r in pr for v in r]
    f2 = lib.grid_faces(len(pr), ns, closed=False)
    pel = lib.new_obj('Tights_Pelvis', v2, f2, outward_from=(0, 0.01, 0.9))
    lib.set_mat(pel, mats['tights']); lib.add_mirror(pel)
    return {'Body': body, 'Tights': tights, 'TightsPelvis': pel}
