"""Outfit: Coat (bodice + A-line skirt shell, sleeves, collar, belt, buckle, buttons),
Scarf (cable-knit roll + left tail with fringe), Mittens, Boots (+ fur cuffs)."""
import bpy, math
from mathutils import Vector, Matrix
import lib, body
from lib import gauss, smoothstep

# z, W, F, B, cy, n
COAT = [
    (1.246, 0.040, 0.035, 0.040, 0.006, 2.0),
    (1.234, 0.056, 0.045, 0.047, 0.007, 2.0),
    (1.222, 0.092, 0.056, 0.056, 0.010, 2.3),
    (1.204, 0.128, 0.068, 0.064, 0.012, 2.5),
    (1.176, 0.142, 0.081, 0.069, 0.012, 2.6),
    (1.135, 0.131, 0.097, 0.073, 0.012, 2.5),
    (1.100, 0.117, 0.091, 0.071, 0.012, 2.4),
    (1.065, 0.103, 0.077, 0.067, 0.012, 2.3),
    (1.032, 0.095, 0.069, 0.065, 0.012, 2.2),
    (0.998, 0.110, 0.079, 0.077, 0.014, 2.2),
    (0.950, 0.137, 0.098, 0.094, 0.016, 2.2),
    (0.890, 0.155, 0.114, 0.108, 0.016, 2.2),
    (0.810, 0.180, 0.136, 0.128, 0.016, 2.2),
    (0.730, 0.194, 0.150, 0.141, 0.016, 2.2),
    (0.650, 0.207, 0.162, 0.152, 0.016, 2.2),
    (0.625, 0.210, 0.165, 0.155, 0.016, 2.2),
]
NS = 11
HEM_Z = 0.663


def coat_rings(sub=2):
    sub = 1
    tab = sorted([(-r[0],) + r[1:] for r in COAT])
    zs = [r[0] for r in COAT]
    rings = []
    for i in range(len(COAT) - 1):
        for k in range(sub):
            rings.append(zs[i] + (zs[i + 1] - zs[i]) * k / sub)
    rings.append(zs[-1])
    out = []
    for z in rings:
        W, F, B, cy, ne = lib.interp_table(tab, -z)
        ring = body.half_ring(W, F, B, cy, z, ne, ns=NS)
        fold = 0.22 * smoothstep(1.01, 0.66, z) ** 1.2
        for k, v in enumerate(ring):
            phi = math.pi * k / NS
            if v.y < cy:
                v.y -= 0.016 * gauss(v.x - 0.052, 0.034) * gauss(z - 1.135, 0.040)
            f = 1.0 + fold * (0.5 + 0.5 * math.cos(8 * phi)) ** 2.0 - fold * 0.30
            v.x *= f
            v.y = cy + (v.y - cy) * f
            if z < 0.70:
                v.z -= 0.012 * smoothstep(0.70, 0.625, z) * (0.5 + 0.5 * math.cos(8 * phi)) ** 2
        ring[0].x = 0; ring[-1].x = 0
        out.append(ring)
    return out


def sleeve(mats):
    path, wr, d2 = body.arm_path()
    P = lib.resample(lib.catmull(path, 5), 15)
    rad = lambda s: 0.050 - 0.016 * smoothstep(0.0, 0.55, s) + 0.010 * smoothstep(0.75, 1.0, s)
    v, f = lib.sweep(P[:-1], lambda i, s: lib.ellipse_sec(rad(s), rad(s) * 0.95, 10), up_hint=Vector((0, -1, 0)))
    sl = lib.new_obj('Sleeve', v, f, outward_from=None, recalc=False)
    lib.set_mat(sl, mats['coat'])
    # cuff
    Pc = [wr - d2 * 0.045, wr - d2 * 0.022, wr]
    v, f = lib.sweep(Pc, lambda i, s: lib.ellipse_sec(0.045, 0.043, 10), up_hint=Vector((0, -1, 0)))
    cf = lib.new_obj('Cuff', v, f, recalc=False)
    lib.set_mat(cf, mats['rust'])
    return sl, cf, wr, d2


def fix_out(ob, axis_pts):
    """Orient tube normals away from its axis."""
    import bmesh
    bm = bmesh.new(); bm.from_mesh(ob.data)
    for fc in bm.faces:
        c = fc.calc_center_median()
        p = min(axis_pts, key=lambda q: (q - c).length)
        if fc.normal.dot(c - p) < 0:
            fc.normal_flip()
    bm.to_mesh(ob.data); bm.free()


def build_coat(mats):
    rings = coat_rings()
    ns = NS + 1
    verts = [v for r in rings for v in r]
    faces = lib.grid_faces(len(rings), ns, closed=False)
    coat = lib.new_obj('Coat', verts, faces, outward_from=(0, 0.01, 0.95))
    lib.set_mat(coat, mats['coat'])
    hem = [p.index for p in coat.data.polygons if p.center.z < HEM_Z]
    lib.set_mat(coat, mats['rust'], hem)
    # sleeves + cuffs (built at +X, mirrored by modifier)
    sl, cf, wr, d2 = sleeve(mats)
    path, _, _ = body.arm_path()
    ax = lib.resample(lib.catmull(path, 5), 40)
    fix_out(sl, ax); fix_out(cf, ax)
    # collar: round flaps lying on the shoulders
    cr = []
    for (z, W, F, B, cy, sc) in [(1.240, 0.050, 0.043, 0.046, 0.007, 1.0), (1.226, 0.085, 0.060, 0.056, 0.008, 1.0),
                                 (1.212, 0.118, 0.080, 0.066, 0.010, 1.0)]:
        ring = body.half_ring(W, F, B, cy, z, 2.3, ns=NS)
        cr.append(ring)
    # round the front of the flaps: pull outer front verts up toward the neck
    for k in range(4):
        t = 1 - k / 4
        cr[2][k] = cr[2][k].lerp(cr[1][k], 0.55 * t)
        cr[1][k] = cr[1][k].lerp(cr[0][k], 0.25 * t)
    for r in cr:
        for v in r:
            v.y -= 0.004 if v.y < 0 else -0.002
            v.z += 0.004
    cv = [v for r in cr for v in r]
    cfc = lib.grid_faces(3, ns, closed=False)
    cfc = [f for f in cfc if not (f[0] % ns == 0)]   # open slit at the front centre
    col = lib.new_obj('Collar', cv, cfc, outward_from=(0, 0.01, 1.0))
    lib.set_mat(col, mats['coat'])
    coat = lib.join([coat, sl, cf, col], 'Coat')
    lib.add_mirror(coat)
    lib.add_solidify(coat, 0.005, offset=-1.0)
    lib.add_subsurf(coat, 1)
    # belt
    tab = sorted([(-r[0],) + r[1:] for r in COAT])
    br = []
    for z in (1.044, 1.032, 1.020):
        W, F, B, cy, ne = lib.interp_table(tab, -z)
        br.append(body.half_ring(W + 0.0075, F + 0.0075, B + 0.0075, cy, z, ne, ns=NS))
    bv = [v for r in br for v in r]
    belt = lib.new_obj('Belt', bv, lib.grid_faces(3, ns, False), outward_from=(0, 0.01, 1.03))
    lib.set_mat(belt, mats['belt'])
    lib.add_mirror(belt); lib.add_solidify(belt, 0.003, offset=1.0)
    return coat, belt


def gold_details(mats, coat):
    bpy.context.view_layer.update()
    import head
    proj = head.Projector(coat)
    import bmesh
    objs = []
    # buckle: rounded rectangular frame
    bc = proj.project(0.0, 1.032, 0.0095)
    bm = bmesh.new()
    w, h, t, d = 0.016, 0.013, 0.0035, 0.004
    for (x0, x1, z0, z1) in [(-w, w, h - t, h), (-w, w, -h, -h + t), (-w, -w + t, -h, h), (w - t, w, -h, h)]:
        res = bmesh.ops.create_cube(bm, size=1.0)
        for v in res['verts']:
            v.co = Vector(((x0 + x1) / 2 + v.co.x * (x1 - x0), v.co.y * d, (z0 + z1) / 2 + v.co.z * (z1 - z0)))
    for v in bm.verts:
        v.co += bc
    me = bpy.data.meshes.new('Buckle'); bm.to_mesh(me); bm.free()
    bk = bpy.data.objects.new('Buckle', me); bpy.context.scene.collection.objects.link(bk)
    lib.set_mat(bk, mats['gold'])
    bv = bk.modifiers.new('Bevel', 'BEVEL'); bv.width = 0.0012; bv.segments = 2
    objs.append(bk)
    # 6 buttons, double-breasted
    for z in (1.168, 1.116, 1.068):
        for x in (-0.024, 0.024):
            p = proj.project(x, z, 0.002)
            bm = bmesh.new()
            bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=4, radius=0.0075)
            for v in bm.verts:
                v.co = Vector((v.co.x, v.co.y * 0.45, v.co.z)) + p
            me = bpy.data.meshes.new('Button'); bm.to_mesh(me); bm.free()
            o = bpy.data.objects.new('Button', me); bpy.context.scene.collection.objects.link(o)
            for pl in me.polygons:
                pl.use_smooth = True
            lib.set_mat(o, mats['gold'])
            objs.append(o)
    g = lib.join(objs, 'CoatGold')
    return g


def closed_tube(rings):
    nr, ns = len(rings), len(rings[0])
    verts = [v for r in rings for v in r]
    faces = []
    for i in range(nr):
        for j in range(ns):
            i2, j2 = (i + 1) % nr, (j + 1) % ns
            faces.append((i * ns + j, i * ns + j2, i2 * ns + j2, i2 * ns + j))
    return verts, faces


def build_scarf(mats):
    C = Vector((0, 0.006, 1.262))
    NP, NSc = 36, 12
    rings = []
    for i in range(NP):
        a = 2 * math.pi * i / NP
        # a=0 front (-Y)
        dirv = Vector((math.sin(a), -math.cos(a), 0))
        R = 0.072 + 0.006 * math.cos(a)
        P = C + dirv * R + Vector((0, 0, -0.012 * max(0.0, math.cos(a)) + 0.004 * max(0, -math.cos(a))))
        T = Vector((math.cos(a), math.sin(a), 0))
        N = dirv; Bv = T.cross(N)
        ring = []
        for k in range(NSc):
            b = 2 * math.pi * k / NSc
            ph = b + a * 7
            r = 0.036 * (1 + 0.09 * math.cos(4 * ph))
            ring.append(P + N * (r * 1.05 * math.cos(b)) + Bv * (r * 0.92 * math.sin(b)))
        rings.append(ring)
    v, f = closed_tube(rings)
    roll = lib.new_obj('ScarfRoll', v, f, outward_from=None, recalc=False)
    lib.set_mat(roll, mats['teal'])
    # orient outward from the tube axis
    axis = [C + Vector((math.sin(2 * math.pi * i / 64), -math.cos(2 * math.pi * i / 64), 0)) * 0.072 for i in range(64)]
    fix_out(roll, axis)
    # tail on HER LEFT (+X), hanging down the front
    path = lib.resample(lib.catmull([Vector((0.050, -0.078, 1.250)), Vector((0.068, -0.115, 1.200)),
                                     Vector((0.076, -0.130, 1.140)), Vector((0.078, -0.124, 1.07)),
                                     Vector((0.080, -0.116, 1.00)), Vector((0.082, -0.116, 0.935))], 6), 18)
    T, N, B = lib.frames_along(path, Vector((0, -1, 0)))
    HW, HT = 0.036, 0.0125
    nsx = 7
    rings = []
    for i, p in enumerate(path):
        s = i / (len(path) - 1)
        ring = []
        hw = HW * (0.85 + 0.15 * smoothstep(0, 0.25, s))
        for k in range(nsx):     # front edge, left to right
            u = -1 + 2 * k / (nsx - 1)
            th = HT * (1 + 0.28 * math.cos(3 * math.pi * u + s * 0.0))
            ring.append(p + B[i] * (u * hw) + N[i] * th)
        for k in range(nsx):     # back edge, right to left
            u = 1 - 2 * k / (nsx - 1)
            ring.append(p + B[i] * (u * hw) - N[i] * HT * 0.8)
        rings.append(ring)
    v, f = lib.loft(rings, True, cap_start=True, cap_end=True)
    tail = lib.new_obj('ScarfTail', v, f, outward_from=None)
    fix_out(tail, path)
    lib.set_mat(tail, mats['teal'])
    # fringe
    end = path[-1]; Tn = T[-1]
    tass = []
    for k in range(5):
        u = -0.80 + 1.6 * k / 4
        base = end + B[-1] * (u * HW) - Tn * 0.004
        tp = [base + Tn * (0.016 * j) + B[-1] * (0.002 * math.sin(j + k)) for j in range(4)]
        vv, ff = lib.sweep(tp, lambda i, s: lib.ellipse_sec(0.0055 * (1 - 0.65 * s), 0.0045 * (1 - 0.65 * s), 8),
                           up_hint=Vector((0, -1, 0)), cap_end=True)
        o = lib.new_obj('Fringe', vv, ff, recalc=False)
        fix_out(o, tp)
        lib.set_mat(o, mats['teal'])
        tass.append(o)
    sc = lib.join([roll, tail] + tass, 'Scarf')
    lib.add_subsurf(sc, 1)
    return sc


def build_mittens(mats, wr, d2):
    P0 = wr - d2 * 0.035
    path = [P0 + d2 * (0.150 * i / 10) for i in range(11)]
    def sec(i, s):
        # width (along N ~ Y) and thickness (B)
        w = 0.030 + 0.006 * smoothstep(0.0, 0.45, s)
        t = 0.019 + 0.003 * smoothstep(0.1, 0.5, s)
        if s > 0.72:
            k = (s - 0.72) / 0.28
            f = math.sqrt(max(0.0, 1 - k ** 2.2))
            w *= max(f, 0.06); t *= max(f, 0.06)
        return lib.ellipse_sec(w, t, 14)
    v, f = lib.sweep(path, sec, up_hint=Vector((0, 1, 0)), cap_start=True, cap_end=True)
    mit = lib.new_obj('MittenHand', v, f, recalc=False)
    fix_out(mit, path)
    lib.set_mat(mit, mats['teal'])
    T, N, B = lib.frames_along(path, Vector((0, 1, 0)))
    # thumb on the front (-Y) side, angled forward
    i0 = 4
    root = path[i0] - N[i0] * 0.022 - B[i0] * 0.004
    tdir = (d2 * 0.75 - N[i0] * 0.55 - B[i0] * 0.25).normalized()
    tp = [root + tdir * (0.050 * j / 8) for j in range(9)]
    def tsec(i, s):
        r = 0.0125 * (1 - 0.15 * s)
        if s > 0.7:
            r *= max(math.sqrt(max(0, 1 - ((s - 0.7) / 0.3) ** 2)), 0.08)
        return lib.ellipse_sec(r, r * 0.9, 10)
    v, f = lib.sweep(tp, tsec, up_hint=Vector((0, 0, 1)), cap_end=True)
    th = lib.new_obj('Thumb', v, f, recalc=False)
    fix_out(th, tp)
    lib.set_mat(th, mats['teal'])
    # knit cuff band
    cp = [wr - d2 * 0.038, wr - d2 * 0.010]
    v, f = lib.sweep(cp, lambda i, s: lib.ellipse_sec(0.034, 0.026, 14, lobes=0), up_hint=Vector((0, 1, 0)))
    cu = lib.new_obj('MittenCuff', v, f, recalc=False)
    fix_out(cu, cp)
    lib.set_mat(cu, mats['teal'])
    m = lib.join([mit, th, cu], 'Mittens')
    mm = m.modifiers.new('Mirror', 'MIRROR'); mm.use_axis[0] = True; mm.use_mirror_merge = False
    lib.add_subsurf(m, 1)
    return m


def build_boots(mats):
    shaft = body.build_legs('BootShaft', mats['boots'], extra=0.009, z_top=0.300, z_bot=0.050, nr=9, ns=12)
    for m in list(shaft.modifiers):
        shaft.modifiers.remove(m)
    # foot: rings along Y from heel to toe
    cx = 0.090
    rings = []
    ys = [0.052 - 0.190 * i / 12 for i in range(13)]
    for y in ys:
        u = (0.052 - y) / 0.190     # 0 heel .. 1 toe
        hw = 0.036 + 0.004 * smoothstep(0.5, 0.85, u)
        top = 0.105 - 0.060 * smoothstep(0.25, 0.75, u)
        endf = 1.0
        if u < 0.12:
            endf = math.sqrt(max(0.0, 1 - ((0.12 - u) / 0.12) ** 2))
        if u > 0.80:
            endf = math.sqrt(max(0.0, 1 - ((u - 0.80) / 0.20) ** 2))
        endf = max(endf, 0.05)
        zc = top / 2
        hz = top / 2 * (0.4 + 0.6 * endf)
        ring = []
        for k in range(12):
            a = 2 * math.pi * k / 12
            ca, sa = math.cos(a), math.sin(a)
            x = cx + hw * endf * math.copysign(abs(ca) ** 0.7, ca)
            z = zc + hz * math.copysign(abs(sa) ** 0.7, sa)
            z = max(z, 0.0)
            ring.append(Vector((x, y, z)))
        rings.append(ring)
    v, f = lib.loft(rings, True, cap_start=True, cap_end=True)
    foot = lib.new_obj('BootFoot', v, f, outward_from=(cx, -0.04, 0.04))
    lib.set_mat(foot, mats['boots'])
    # fur cuff: lumpy torus at the boot top
    pts = lib.catmull(body.leg_path(), 6)
    best = min(pts, key=lambda p: abs(p.z - 0.30))
    C = Vector((best.x, best.y, 0.300))
    rs, rf, rb = body.leg_radius(0.30)
    rings = []
    for i in range(24):
        a = 2 * math.pi * i / 24
        dirv = Vector((math.cos(a), math.sin(a), 0))
        R = (rs + 0.014)
        Pc = C + Vector((math.cos(a) * R, math.sin(a) * ((rf if math.sin(a) < 0 else rb) + 0.014), 0))
        ring = []
        for k in range(8):
            b = 2 * math.pi * k / 8
            r = 0.021 * (1 + 0.12 * math.cos(9 * a) * math.cos(2 * b) + 0.06 * math.cos(5 * a + 3 * b))
            ring.append(Pc + dirv * (r * math.cos(b)) + Vector((0, 0, r * 1.15 * math.sin(b))))
        rings.append(ring)
    v, f = closed_tube(rings)
    fur = lib.new_obj('BootFur', v, f, recalc=False)
    fix_out(fur, [C + Vector((math.cos(2 * math.pi * i / 64) * (rs + 0.014), math.sin(2 * math.pi * i / 64) * (rf + 0.014), 0)) for i in range(64)])
    lib.set_mat(fur, mats['fur'])
    b = lib.join([shaft, foot, fur], 'Boots')
    mm = b.modifiers.new('Mirror', 'MIRROR'); mm.use_axis[0] = True; mm.use_mirror_merge = False
    lib.add_subsurf(b, 1)
    return b


def build(mats):
    coat, belt = build_coat(mats)
    gold = gold_details(mats, coat)
    scarf = build_scarf(mats)
    _, wr, d2 = body.arm_path()
    mit = build_mittens(mats, wr, d2)
    boots = build_boots(mats)
    return {'Coat': coat, 'Belt': belt, 'CoatGold': gold, 'Scarf': scarf, 'Mittens': mit, 'Boots': boots}
