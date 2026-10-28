"""Hair: sculpted sheets.
- HairCap: shell grown off the scalp (mirrored), the base mass.
- Bangs: two layers of arched clumps lifting off the forehead, longer at the sides.
- Side locks: two face-framing locks to the collarbone.
- Back hair: broad tapering sheets to mid-back + loose strands.
- Ponytail: one voluminous lofted, lobed mass + layered clumps, tapering to a point.
- Bow: teal ribbon bow (loops, knot, V-cut tails).
All sheets: arched ribbons -> Solidify -> Subsurf."""
import bpy, math, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import lib
from lib import smoothstep, gauss

C = Vector((0, 0.012, 1.445))


class Scalp:
    def __init__(self, head):
        dg = bpy.context.evaluated_depsgraph_get()
        ev = head.evaluated_get(dg)
        me = ev.to_mesh()
        vs = [head.matrix_world @ v.co for v in me.vertices]
        self.bvh = BVHTree.FromPolygons(vs, [tuple(p.vertices) for p in me.polygons])
        ev.to_mesh_clear()

    def dirv(self, th, ph):
        th, ph = math.radians(th), math.radians(ph)
        return Vector((math.sin(th) * math.sin(ph), -math.sin(th) * math.cos(ph), math.cos(th)))

    def hit(self, th, ph):
        d = self.dirv(th, ph)
        o = C + d * 0.4
        loc, n, i, dist = self.bvh.ray_cast(o, -d)
        if loc is None:
            return C + d * 0.1, d
        return loc, n

    def pt(self, th, ph, off):
        p, n = self.hit(th, ph)
        # blend normal with radial direction to keep the shell smooth
        d = self.dirv(th, ph)
        nn = (n * 0.5 + d * 0.5).normalized()
        return p + nn * off, nn


def orient(ob, ref_fn):
    bm = bmesh.new(); bm.from_mesh(ob.data)
    for f in bm.faces:
        c = f.calc_center_median()
        if f.normal.dot(ref_fn(c)) < 0:
            f.normal_flip()
    bm.to_mesh(ob.data); bm.free()


def ribbon(name, path, normals, width_fn, mat, arch=0.35, nw=4, thick=0.005, n=None, tip_lift=0.0,
           solid=True, sub=1, curl_fn=None):
    """Arched ribbon along path. normals = outward directions (away from head)."""
    n = n or len(path)
    P = lib.resample(path, n)
    # resample normals by index ratio
    Nn = [normals[min(int(round(i * (len(normals) - 1) / (n - 1))), len(normals) - 1)] for i in range(n)]
    verts = []
    for i in range(n):
        s = i / (n - 1)
        a = P[max(i - 1, 0)]; b = P[min(i + 1, n - 1)]
        T = (b - a).normalized()
        N = (Nn[i] - T * Nn[i].dot(T)).normalized()
        S = T.cross(N).normalized()
        w = width_fn(s)
        cu = curl_fn(s) if curl_fn else 0.0
        for k in range(nw + 1):
            u = -1 + 2 * k / nw
            verts.append(P[i] + S * (u * w) + N * (arch * w * (1 - u * u) - cu * u * u * w))
    faces = []
    for i in range(n - 1):
        for k in range(nw):
            a = i * (nw + 1) + k
            faces.append((a, a + 1, a + nw + 2, a + nw + 1))
    ob = lib.new_obj(name, verts, faces, recalc=False)
    # orient along the outward normals
    me = ob.data
    bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
    for fi, f in enumerate(bm.faces):
        i = fi // nw
        if f.normal.dot(Nn[i]) < 0:
            f.normal_flip()
    bm.to_mesh(me); bm.free()
    lib.set_mat(ob, mat)
    if solid:
        lib.add_solidify(ob, thick, offset=-1.0)
    if sub:
        lib.add_subsurf(ob, sub)
    return ob


def taper(w0, tip_start=0.6, tip_w=0.08, root=0.0):
    def f(s):
        r = 1.0 - (1 - tip_w) * smoothstep(tip_start, 1.0, s) ** 1.3
        if root:
            r *= 1 - root * (1 - smoothstep(0.0, 0.25, s))
        return w0 * r
    return f


def scalp_path(sc, ph, th0, th1, n, off0, off1, lift_pow=2.0):
    pts, nrs = [], []
    for i in range(n):
        s = i / (n - 1)
        th = th0 + (th1 - th0) * s
        off = off0 + (off1 - off0) * s ** lift_pow
        p, nn = sc.pt(th, ph, off)
        pts.append(p); nrs.append(nn)
    return pts, nrs


def build_cap(sc, mat):
    """Hair shell over the cranium (half, mirrored)."""
    NPH, NTH = 10, 10
    rows = []
    for j in range(NTH + 1):
        ring = []
        for i in range(NPH + 1):
            ph = 180.0 * i / NPH
            thmax = 74 + 52 * smoothstep(10, 110, ph) + 8 * smoothstep(110, 180, ph)
            th = 3 + (thmax - 3) * j / NTH
            off = 0.009 + 0.004 * (1 - smoothstep(40, 110, th))
            p, nn = sc.pt(th, ph, off)
            if i == 0 or i == NPH:
                p.x = 0
            ring.append(p)
        rows.append(ring)
    ns = NPH + 1
    verts = [v for r in rows for v in r]
    faces = lib.grid_faces(len(rows), ns, closed=False)
    ob = lib.new_obj('Hair_Cap', verts, faces, recalc=False)
    orient(ob, lambda c: c - C)
    lib.set_mat(ob, mat)
    lib.add_mirror(ob, merge=0.001)
    lib.add_solidify(ob, 0.006, offset=-1.0)
    lib.add_subsurf(ob, 1)
    return ob


def build_bangs(sc, mat):
    obs = []
    # back layer: broad clumps, tips just above the brows
    back = [(-56, 91, 0.032), (-37, 82, 0.034), (-18, 76.5, 0.034), (0, 76, 0.034),
            (18, 76.5, 0.034), (37, 82, 0.034), (56, 91, 0.032)]
    for k, (ph, thend, w) in enumerate(back):
        pts, nrs = scalp_path(sc, ph, 18, thend, 10, 0.010, 0.016)
        obs.append(ribbon(f'Bang_B{k}', pts, nrs, taper(w, 0.80, 0.50), mat, arch=0.30, thick=0.004, n=10, nw=2))
    # front layer: offset clumps, varied length -> notches
    front = [(-44, 90, 0.044, 0.022), (-17, 81, 0.042, 0.027), (8, 79.5, 0.040, 0.028),
             (35, 86.5, 0.044, 0.024)]
    for k, (ph, thend, w, lift) in enumerate(front):
        pts, nrs = scalp_path(sc, ph, 22, thend, 12, 0.014, 0.016 + lift * 0.55, lift_pow=1.6)
        # tips curl slightly inward toward the face
        obs.append(ribbon(f'Bang_F{k}', pts, nrs, taper(w, 0.80, 0.22), mat, arch=0.40, thick=0.004, n=11, nw=2))
    # side bangs sloping into the side locks (no bare temples)
    for sgn in (-1, 1):
        for k, (ph, thend, w) in enumerate([(66, 108, 0.022), (76, 116, 0.020)]):
            pts, nrs = scalp_path(sc, sgn * ph, 30, thend, 12, 0.014, 0.022)
            obs.append(ribbon(f'Bang_S{k}{sgn}', pts, nrs, taper(w, 0.5, 0.08), mat, arch=0.35, thick=0.004, n=10, nw=2))
    return obs


def build_side_locks(mat):
    obs = []
    for sgn in (-1, 1):
        pts = [Vector((0.090, -0.030, 1.470)), Vector((0.100, -0.036, 1.420)), Vector((0.101, -0.042, 1.360)),
               Vector((0.098, -0.052, 1.300)), Vector((0.104, -0.074, 1.245)), Vector((0.112, -0.082, 1.195)),
               Vector((0.116, -0.080, 1.160))]
        for p in pts:
            p.x *= sgn
        P = lib.catmull(pts, 3)
        nrs = [Vector((sgn * 0.8, -0.6, 0)).normalized() for _ in P]
        w = lambda s: 0.027 * (1 - 0.9 * smoothstep(0.55, 1.0, s)) * (0.8 + 0.2 * smoothstep(0, 0.2, s))
        obs.append(ribbon(f'Hair_SideLock{sgn}', P, nrs, w, mat, arch=0.45, nw=3, thick=0.006, n=16,
                          curl_fn=lambda s: 0.25 * smoothstep(0.3, 1.0, s)))
        # thin secondary strand
        pts2 = [p + Vector((sgn * 0.008, 0.012, 0.0)) for p in pts[:-1]]
        pts2[-1] = pts2[-1] + Vector((sgn * 0.010, 0.010, 0.02))
        P2 = lib.catmull(pts2, 3)
        nrs2 = [Vector((sgn * 0.8, -0.6, 0)).normalized() for _ in P2]
        obs.append(ribbon(f'Hair_SideStrand{sgn}', P2, nrs2, taper(0.010, 0.5, 0.1), mat, arch=0.4, nw=2, thick=0.004, n=14))
    return obs


def build_back(sc, mat):
    obs = []
    # broad sheets: start on the scalp below the ponytail, drop to mid-back
    specs = [(102, 0.048, 1.07, 0.106), (124, 0.056, 1.00, 0.100), (148, 0.060, 0.975, 0.096),
             (171, 0.058, 0.965, 0.094)]
    for sgn in (-1, 1):
        for k, (ph, w, zend, yback) in enumerate(specs):
            phs = sgn * ph
            pts = []; nrs = []
            for th in (45, 65, 85, 100, 112):
                p, nn = sc.pt(th, phs, {45: 0.0, 65: 0.007, 85: 0.013, 100: 0.015, 112: 0.016}[th])
                pts.append(p); nrs.append(nn)
            d = sc.dirv(112, phs)
            last = pts[-1]
            r = Vector((d.x, d.y, 0)).normalized()
            # fall over the back/shoulders
            for z in (1.30, 1.22, 1.14, 1.06, zend):
                spread = 1.0 + 0.5 * smoothstep(1.32, 1.05, z)
                x = last.x * spread + r.x * 0.03 * smoothstep(1.32, 1.18, z)
                y = max(last.y, yback) + 0.012 * smoothstep(1.3, 1.0, z) + (0.0 if abs(ph) > 120 else 0.0)
                if abs(ph) < 112:
                    y = last.y * 0.6 + yback * 0.4
                pts.append(Vector((x, y, z))); nrs.append(Vector((r.x * 0.6, 1.0, 0)).normalized())
            P = lib.catmull(pts, 2)
            Nr = []
            for i in range(len(P)):
                j = min(int(i / 2), len(nrs) - 1)
                Nr.append(nrs[j])
            obs.append(ribbon(f'Hair_Back{k}{sgn}', P, Nr, taper(w, 0.62, 0.10), mat, arch=0.28, nw=3,
                              thick=0.006, n=12))
    # loose thin strands
    for sgn, ph, zend in [(1, 128, 1.04), (-1, 146, 1.02)]:
        pts = []; nrs = []
        for th in (95, 110):
            p, nn = sc.pt(th, sgn * ph, 0.018); pts.append(p); nrs.append(nn)
        l = pts[-1]
        for z in (1.28, 1.18, 1.10, zend):
            pts.append(Vector((l.x * 1.25 + sgn * 0.01 * math.sin(z * 30), 0.118, z))); nrs.append(Vector((0, 1, 0)))
        P = lib.catmull(pts, 2)
        obs.append(ribbon(f'Hair_Strand{sgn}', P, [nrs[min(i // 2, len(nrs) - 1)] for i in range(len(P))],
                          taper(0.008, 0.4, 0.1), mat, arch=0.4, nw=2, thick=0.004, n=14))
    return obs


PT_BASE = Vector((0.0, 0.118, 1.505))


def pony_path():
    pts = [PT_BASE + Vector((0, -0.022, 0.006)), PT_BASE, Vector((0, 0.150, 1.507)), Vector((0, 0.192, 1.480)),
           Vector((0, 0.216, 1.420)), Vector((0, 0.222, 1.350)), Vector((0, 0.212, 1.275)), Vector((0, 0.196, 1.205)),
           Vector((0, 0.180, 1.150))]
    return lib.resample(lib.catmull(pts, 4), 18)


def build_ponytail(mat):
    P = pony_path()
    def rad(s):
        r = 0.024 - 0.004 * smoothstep(0.0, 0.08, s) + 0.044 * smoothstep(0.08, 0.30, s) - 0.004 * smoothstep(0.35, 0.55, s)
        r *= 1 - 0.93 * smoothstep(0.45, 1.0, s) ** 1.2
        return max(r, 0.0015)
    def sec(i, s):
        r = rad(s)
        out = []
        for k in range(15):
            a = 2 * math.pi * k / 15 + s * 1.2
            lob = 1 + 0.16 * math.cos(5 * a) * smoothstep(0.1, 0.3, s)
            out.append((r * lob * math.cos(a), r * 0.92 * lob * math.sin(a)))
        return out
    v, f = lib.sweep(P, sec, up_hint=Vector((0, 1, 0)), cap_start=True, cap_end=True)
    ob = lib.new_obj('Hair_Ponytail', v, f, recalc=False)
    orient(ob, lambda c: c - min(P, key=lambda q: (q - c).length))
    lib.set_mat(ob, mat)
    lib.add_subsurf(ob, 1)
    obs = [ob]
    # layered clumps around the mass (fan out, flick at the ends)
    T, N, B = lib.frames_along(P, Vector((0, 1, 0)))
    for k, (ang, ln, w, flick) in enumerate([(0, 0.95, 0.024, 0.03), (65, 0.80, 0.022, 0.04), (-65, 0.82, 0.022, 0.04),
                                             (150, 0.70, 0.024, 0.02), (-150, 0.72, 0.024, 0.02)]):
        a = math.radians(ang)
        pts = []; nrs = []
        m = int(len(P) * ln)
        for i in range(1, m):
            s = i / (len(P) - 1)
            r = rad(s) * 0.95 + 0.004
            d = (N[i] * math.cos(a) + B[i] * math.sin(a))
            fl = flick * smoothstep(0.5 * ln, ln, s)
            pts.append(P[i] + d * (r + fl)); nrs.append(d)
        obs.append(ribbon(f'Hair_PonyClump{k}', pts, nrs, taper(w, 0.45, 0.05), mat, arch=0.45, nw=3,
                          thick=0.005, n=11))
    return obs


def build_bow(mat):
    K = PT_BASE + Vector((0, 0.036, 0.010))     # knot centre
    obs = []
    for sgn in (-1, 1):
        # closed loop path in the XY-ish plane: out along +x and back
        L = 0.160
        path = []
        NP = 16
        for i in range(NP):
            t = 2 * math.pi * i / NP
            x = L * 0.5 * (1 - math.cos(t))           # 0 at knot .. L at tip
            puff = 0.018 * math.sin(t) * (0.5 + 0.5 * math.sin(math.pi * x / L) ** 0.6)
            y = puff * (1.0 if math.sin(t) >= 0 else 0.8)
            z = 0.22 * x + 0.006 * math.sin(math.pi * x / L)
            path.append(K + Vector((sgn * (x + 0.012), y, z)))
        rings = []
        for i, p in enumerate(path):
            t = 2 * math.pi * i / NP
            x = abs(p.x - K.x) - 0.012
            xl = min(max(x / L, 0.0), 1.0)
            h = 0.011 + 0.040 * xl ** 1.1 + 0.006 * math.sin(math.pi * min(xl, 1.0)) ** 2
            if xl > 0.90:
                h *= max(math.sqrt(max(0.0, 1 - ((xl - 0.90) / 0.13) ** 2)), 0.80)
            ring = []
            for k in range(6):
                u = -1 + 2 * k / 5
                bulge = 0.010 * (1 - u * u) * (0.3 + x / L)
                # cup outward from the loop centre (y)
                yc = K.y
                outward = 1.0 if p.y >= yc else -1.0
                ring.append(p + Vector((-sgn * 0.012 * u * u * xl ** 4, outward * bulge, u * h)))
            rings.append(ring)
        verts = [v for r in rings for v in r]
        faces = []
        for i in range(NP):
            for k in range(5):
                i2 = (i + 1) % NP
                faces.append((i * 6 + k, i * 6 + k + 1, i2 * 6 + k + 1, i2 * 6 + k))
        lp = lib.new_obj(f'BowLoop{sgn}', verts, faces, recalc=False)
        cen = K + Vector((sgn * (L * 0.5 + 0.012), 0, 0))
        orient(lp, lambda c, cc=cen: Vector((0, c.y - cc.y, 0)) + (c - cc) * 0.2)
        lib.set_mat(lp, mat)
        obs.append(lp)
        # tails with V-cut ends
        tp = [K + Vector((sgn * 0.008, 0.006, -0.012)), K + Vector((sgn * 0.040, 0.016, -0.055)),
              K + Vector((sgn * 0.066, 0.026, -0.105)), K + Vector((sgn * 0.080, 0.030, -0.150))]
        P = lib.resample(lib.catmull(tp, 4), 12)
        verts = []
        for i, p in enumerate(P):
            s = i / (len(P) - 1)
            w = 0.017 + 0.008 * s
            a = P[max(i - 1, 0)]; b = P[min(i + 1, len(P) - 1)]
            T = (b - a).normalized()
            S = Vector((1, 0, 0)) - T * T.x
            S.normalize()
            for k in range(5):
                u = -1 + 2 * k / 4
                vcut = 0.0
                if i == len(P) - 1:
                    vcut = 0.020 * (1 - abs(u))     # notch: centre pulled up
                verts.append(p + S * (u * w) + Vector((0, 0.004 * (1 - u * u), 0)) - T * vcut)
        faces = []
        for i in range(len(P) - 1):
            for k in range(4):
                a = i * 5 + k
                faces.append((a, a + 1, a + 6, a + 5))
        tl = lib.new_obj(f'BowTail{sgn}', verts, faces, recalc=False)
        orient(tl, lambda c: Vector((0, 1, 0)))
        lib.set_mat(tl, mat)
        obs.append(tl)
    # knot
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=1.0)
    for v in bm.verts:
        v.co = K + Vector((v.co.x * 0.022, v.co.y * 0.024 + 0.002, v.co.z * 0.030))
    me = bpy.data.meshes.new('BowKnot'); bm.to_mesh(me); bm.free()
    kn = bpy.data.objects.new('BowKnot', me); bpy.context.scene.collection.objects.link(kn)
    for p in me.polygons:
        p.use_smooth = True
    lib.set_mat(kn, mat)
    obs.append(kn)
    bow = lib.join(obs, 'Bow')
    lib.add_solidify(bow, 0.004, offset=-1.0)
    lib.add_subsurf(bow, 1)
    return bow


def build(mats, head):
    sc = Scalp(head)
    mat = mats['hair']
    out = {}
    out['Hair_Cap'] = build_cap(sc, mat)
    bangs = build_bangs(sc, mat)
    sides = build_side_locks(mat)
    back = build_back(sc, mat)
    pony = build_ponytail(mat)
    # bake each sheet's modifiers then join by group, re-adding nothing (already subdivided)
    def bake_join(objs, name):
        for o in objs:
            lib.apply_mods(o)
        return lib.join(objs, name)
    out['Hair_Bangs'] = bake_join(bangs, 'Hair_Bangs')
    out['Hair_SideLocks'] = bake_join(sides, 'Hair_SideLocks')
    out['Hair_Back'] = bake_join(back, 'Hair_Back')
    out['Hair_Ponytail'] = bake_join(pony, 'Hair_Ponytail')
    out['Bow'] = build_bow(mats['teal'])
    return out
