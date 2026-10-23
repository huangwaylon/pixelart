"""Head: lofted ring cage (half, mirrored) with face features as localized cage edits,
plus eye-plane / lash / brow / mouth decals projected onto the subdivided surface."""
import bpy, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import lib
from lib import gauss, smoothstep

# row: fy, fz, by, bz, W, sz, sy, taper, n_front
ROWS = [
    (-0.027, 1.250, 0.033, 1.250, 0.030, 1.250, 0.004, 0.0, 2.0),   # 0 neck base
    (-0.028, 1.282, 0.034, 1.285, 0.030, 1.284, 0.004, 0.0, 2.0),   # 1 neck
    (-0.038, 1.298, 0.037, 1.305, 0.034, 1.302, 0.004, 0.2, 2.0),   # 2 throat
    (-0.052, 1.306, 0.042, 1.318, 0.038, 1.314, 0.006, 0.55, 2.0),  # 3 under jaw
    (-0.068, 1.314, 0.048, 1.336, 0.041, 1.330, 0.008, 0.80, 2.0),  # 4 chin bottom
    (-0.081, 1.326, 0.060, 1.360, 0.052, 1.346, 0.010, 0.74, 2.0),  # 5 chin tip
    (-0.082, 1.344, 0.080, 1.386, 0.071, 1.362, 0.012, 0.50, 2.1),  # 6 lower lip
    (-0.085, 1.362, 0.097, 1.408, 0.083, 1.378, 0.014, 0.28, 2.2),  # 7 mouth
    (-0.089, 1.379, 0.106, 1.428, 0.090, 1.394, 0.014, 0.12, 2.3),  # 8 nose base
    (-0.092, 1.396, 0.111, 1.448, 0.093, 1.409, 0.014, 0.03, 2.4),  # 9 cheekbone
    (-0.093, 1.413, 0.113, 1.468, 0.097, 1.428, 0.014, 0.0, 2.4),   # 10 eye low
    (-0.094, 1.431, 0.114, 1.488, 0.099, 1.448, 0.014, 0.0, 2.4),   # 11 eye
    (-0.095, 1.452, 0.113, 1.506, 0.101, 1.468, 0.014, 0.0, 2.3),   # 12 brow
    (-0.094, 1.478, 0.108, 1.526, 0.101, 1.492, 0.014, 0.0, 2.2),   # 13 forehead
    (-0.089, 1.505, 0.098, 1.544, 0.098, 1.515, 0.014, 0.0, 2.1),   # 14
    (-0.077, 1.533, 0.083, 1.559, 0.089, 1.538, 0.014, 0.0, 2.0),   # 15
    (-0.055, 1.557, 0.060, 1.571, 0.070, 1.560, 0.014, 0.0, 2.0),   # 16
    (-0.028, 1.572, 0.031, 1.578, 0.040, 1.573, 0.014, 0.0, 2.0),   # 17
]
TOP = Vector((0, 0.010, 1.578))
SUB = 3          # rings per table interval
NSEG = 13        # half-ring segments (front=0 .. back=NSEG)


def ring_phi(k, n=NSEG):
    q = k / n                     # 0 front .. 1 back
    return math.pi * (0.62 * q + 0.38 * q ** 3)


def row_at(r):
    rows = [(i,) + ROWS[i] for i in range(len(ROWS))]
    return lib.interp_table(rows, r)


def head_point(r, phi):
    fy, fz, by, bz, W, sz, sy, p, nf = row_at(r)
    s, c = math.sin(phi), math.cos(phi)
    if c >= 0:
        se = abs(s) ** (2 / nf); ce = abs(c) ** (2 / nf)
        ex, ey = W * se, (fy - sy) * ce
        u = phi / (math.pi / 2)
        dx, dy = W * math.sin(u * math.pi / 2) ** 0.6 * u ** 0.4, (fy - sy) * (1 - u) ** 1.15
        x = ex + (dx - ex) * p
        y = sy + ey + (dy - ey) * p
        z = sz + (fz - sz) * c * c
    else:
        se = abs(s); ce = abs(c)
        x, y = W * se, sy + (by - sy) * ce
        z = sz + (bz - sz) * c * c
    return Vector((x, y, z))


def face_disp(v):
    """Localized sculpt on the cage (front half only)."""
    x, y, z = v
    if y > 0:
        return v
    ax = abs(x)
    dy = 0.0
    # nose: tiny tip + soft bridge
    dy -= 0.0075 * gauss(ax, 0.0065) * gauss(z - 1.384, 0.008)
    dy -= 0.0028 * gauss(ax, 0.009) * smoothstep(1.43, 1.39, z) * smoothstep(1.37, 1.385, z)
    # lips
    dy -= 0.0010 * gauss(ax, 0.013) * gauss(z - 1.3625, 0.004)
    dy -= 0.0012 * gauss(ax, 0.011) * gauss(z - 1.3495, 0.0045)
    dy += 0.0010 * gauss(ax, 0.012) * gauss(z - 1.356, 0.002)
    # under-lip dent / chin ball
    dy += 0.0012 * gauss(ax, 0.012) * gauss(z - 1.339, 0.004)
    # eye sockets (slight hollow so eye planes sit in)
    dy += 0.0035 * gauss(ax - 0.041, 0.017) * gauss(z - 1.424, 0.014)
    # chin point
    dy -= 0.0025 * gauss(ax, 0.010) * gauss(z - 1.327, 0.006)
    # cheeks: soft fullness below the eyes
    dy -= 0.0025 * gauss(ax - 0.052, 0.020) * gauss(z - 1.384, 0.016)
    return Vector((x, y + dy, z))


def build_cage():
    nrows = (len(ROWS) - 1) * SUB + 1
    rings = []
    for i in range(nrows):
        r = i / SUB
        ring = []
        for k in range(NSEG + 1):
            v = head_point(r, ring_phi(k))
            ring.append(face_disp(v))
        ring[0].x = 0.0; ring[-1].x = 0.0
        rings.append(ring)
    ns = NSEG + 1
    verts = [v for rg in rings for v in rg]
    faces = lib.grid_faces(nrows, ns, closed=False)
    ti = len(verts); verts.append(TOP)
    b = (nrows - 1) * ns
    for k in range(NSEG):
        faces.append((ti, b + k + 1, b + k))
    return verts, faces


def build(mats):
    verts, faces = build_cage()
    ob = lib.new_obj('Head', verts, faces, outward_from=(0, 0.01, 1.43))
    lib.set_mat(ob, mats['skin'])
    # anime neck shadow: everything below the jaw line
    ns = NSEG + 1
    nf = [p.index for p in ob.data.polygons if max(v // ns for v in p.vertices) <= 3 * SUB]
    lib.set_mat(ob, mats['neck_sh'], nf)
    lib.add_mirror(ob)
    lib.add_subsurf(ob, 1)
    add_face_normals(ob)
    return ob


def add_face_normals(ob):
    """Anime-style clean face shading: transfer normals from a smooth ellipsoid proxy
    onto the face (weighted by a vertex group), as is common for toon game heads."""
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=32, radius=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * 0.098, v.co.y * 0.115 + 0.012, v.co.z * 0.150 + 1.432))
    me = bpy.data.meshes.new('HeadNormalProxy'); bm.to_mesh(me); bm.free()
    px = bpy.data.objects.new('HeadNormalProxy', me)
    bpy.context.scene.collection.objects.link(px)
    for p in me.polygons:
        p.use_smooth = True
    px.hide_render = True; px.hide_viewport = True
    vg = ob.vertex_groups.new(name='face_normals')
    for v in ob.data.vertices:
        w = smoothstep(1.290, 1.320, v.co.z) * smoothstep(0.03, -0.04, v.co.y)
        if w > 0:
            vg.add([v.index], w, 'REPLACE')
    m = ob.modifiers.new('FaceNormals', 'DATA_TRANSFER')
    m.object = px
    m.use_loop_data = True
    m.data_types_loops = {'CUSTOM_NORMAL'}
    m.loop_mapping = 'POLYINTERP_NEAREST'
    m.vertex_group = 'face_normals'
    m.mix_factor = 1.0


# ---------------------------------------------------------------- decals
class Projector:
    def __init__(self, ob):
        dg = bpy.context.evaluated_depsgraph_get()
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        vs = [ob.matrix_world @ v.co for v in me.vertices]
        ps = [tuple(p.vertices) for p in me.polygons]
        self.bvh = BVHTree.FromPolygons(vs, ps)
        ev.to_mesh_clear()

    def project(self, x, z, off, ydir=1.0):
        o = Vector((x, -0.5, z)); d = Vector((0, 1, 0))
        hit, n, i, dist = self.bvh.ray_cast(o, d)
        if hit is None:
            return Vector((x, -0.08, z))
        if n.y > 0:
            n = -n
        return hit + n * off


def region(x0, x1, zlo, zhi, nx=10, nz=5):
    """Grid filling area between zlo(x) and zhi(x); returns list of (x,z) rows and faces."""
    pts = []; faces = []
    cols = []
    for i in range(nx + 1):
        x = x0 + (x1 - x0) * i / nx
        a, b = zlo(x), zhi(x)
        if b < a:
            m = 0.5 * (a + b); a = b = m
        cols.append([(x, a + (b - a) * j / nz) for j in range(nz + 1)])
    for c in cols:
        pts.extend(c)
    for i in range(nx):
        for j in range(nz):
            a = i * (nz + 1) + j
            faces.append((a, a + nz + 1, a + nz + 2, a + 1))
    return pts, faces


def ribbon2d(curve, width_fn, side=1.0, n=24):
    """2D ribbon along curve [(x,z)], width_fn(s); grows to `side` normal."""
    C = lib.resample([Vector((p[0], p[1], 0)) for p in curve], n)
    pts = []; faces = []
    for i, p in enumerate(C):
        a = C[max(i - 1, 0)]; b = C[min(i + 1, n - 1)]
        t = (b - a).normalized()
        nrm = Vector((-t.y, t.x, 0)) * side
        w = width_fn(i / (n - 1))
        pts.append((p.x, p.y))
        pts.append((p.x + nrm.x * w, p.y + nrm.y * w))
    for i in range(n - 1):
        a = 2 * i
        faces.append((a, a + 2, a + 3, a + 1))
    return pts, faces


def bez(pts, n=24):
    out = lib.catmull([Vector((p[0], p[1], 0)) for p in pts], n_per=max(2, n // (len(pts) - 1)))
    return [(v.x, v.y) for v in out]


def lerp_curve(curve, x):
    """z of polyline curve (sorted by x) at x."""
    if x <= curve[0][0]:
        return curve[0][1]
    for i in range(len(curve) - 1):
        (xa, za), (xb, zb) = curve[i], curve[i + 1]
        if xa <= x <= xb:
            t = (x - xa) / max(xb - xa, 1e-9)
            return za + (zb - za) * t
    return curve[-1][1]


def make_decal(name, proj, pts2d, faces, off, mat, mirror=True, solid=0.0):
    verts = [proj.project(x, z, off) for (x, z) in pts2d]
    if mirror:
        n = len(verts)
        verts2 = [proj.project(-x, z, off) for (x, z) in pts2d]
        verts = verts + verts2
        faces = list(faces) + [tuple(i + n for i in reversed(f)) for f in faces]
    ob = lib.new_obj(name, verts, faces, recalc=False)
    # orient towards -Y (camera side)
    me = ob.data
    flip = [p.normal.y > 0 for p in me.polygons]
    if any(flip):
        import bmesh
        bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
        for f, fl in zip(bm.faces, flip):
            if fl:
                f.normal_flip()
        bm.to_mesh(me); bm.free()
    lib.set_mat(ob, mat)
    if solid:
        lib.add_solidify(ob, solid, offset=1.0)
    return ob


EYE = dict(cx=0.0420, cz=1.4190)


def eye_curves():
    cx, cz = EYE['cx'], EYE['cz']
    inner = (cx - 0.0205, cz - 0.0030)
    outer = (cx + 0.0225, cz + 0.0045)
    upper = bez([inner, (cx - 0.013, cz + 0.0125), (cx - 0.001, cz + 0.0185),
                 (cx + 0.012, cz + 0.0172), (cx + 0.0195, cz + 0.0110), outer], 30)
    lower = bez([inner, (cx - 0.011, cz - 0.0150), (cx + 0.003, cz - 0.0200),
                 (cx + 0.015, cz - 0.0140), outer], 30)
    return inner, outer, upper, lower


def build_face_decals(head, mats):
    proj = Projector(head)
    cx, cz = EYE['cx'], EYE['cz']
    inner, outer, upper, lower = eye_curves()
    up = lambda x: lerp_curve(upper, x)
    lo = lambda x: lerp_curve(lower, x)
    objs = []
    # sclera (eye plane)
    p, f = region(inner[0], outer[0], lo, up, 16, 6)
    objs.append(make_decal('Eye_White', proj, p, f, 0.0006, mats['sclera']))
    # iris
    icx, icz, irx, irz = cx + 0.0008, cz - 0.0010, 0.0148, 0.0200
    def ell_lo(x, rx, rz, ccx, ccz):
        u = (x - ccx) / rx
        return ccz - rz * math.sqrt(max(0.0, 1 - u * u))
    def ell_hi(x, rx, rz, ccx, ccz):
        u = (x - ccx) / rx
        return ccz + rz * math.sqrt(max(0.0, 1 - u * u))
    p, f = region(icx - irx, icx + irx, lambda x: max(lo(x), ell_lo(x, irx, irz, icx, icz)),
                  lambda x: min(up(x), ell_hi(x, irx, irz, icx, icz)), 16, 8)
    objs.append(make_decal('Eye_Iris', proj, p, f, 0.0011, mats['iris']))
    # iris light lower crescent
    p, f = region(icx - irx * 0.8, icx + irx * 0.8,
                  lambda x: max(lo(x), ell_lo(x, irx * 0.82, irz * 0.82, icx, icz)),
                  lambda x: min(up(x), ell_lo(x, irx * 0.82, irz * 0.82, icx, icz) + 0.0055 * math.sqrt(max(0, 1 - ((x - icx) / (irx * 0.8)) ** 2))), 12, 3)
    objs.append(make_decal('Eye_IrisLight', proj, p, f, 0.0014, mats['iris_light']))
    # iris dark upper band (lash shadow)
    p, f = region(icx - irx, icx + irx, lambda x: max(lo(x), up(x) - 0.0075),
                  lambda x: min(up(x), ell_hi(x, irx, irz, icx, icz)), 16, 3)
    objs.append(make_decal('Eye_IrisDark', proj, p, f, 0.0016, mats['iris_dark']))
    # pupil
    prx, prz = 0.0058, 0.0092
    p, f = region(icx - prx, icx + prx, lambda x: max(lo(x), ell_lo(x, prx, prz, icx, icz + 0.0005)),
                  lambda x: min(up(x), ell_hi(x, prx, prz, icx, icz + 0.0005)), 8, 4)
    objs.append(make_decal('Eye_Pupil', proj, p, f, 0.0018, mats['pupil']))
    # sclera shadow under the upper lid
    p, f = region(inner[0] + 0.001, outer[0] - 0.001, lambda x: max(lo(x), up(x) - 0.0032), up, 16, 2)
    objs.append(make_decal('Eye_WhiteShadow', proj, p, f, 0.0009, mats['sclera_sh']))
    # highlights
    for (hx, hz, hrx, hrz, nm) in [(icx - 0.0048, icz + 0.0055, 0.0034, 0.0042, 'Eye_HL1'),
                                   (icx + 0.0050, icz - 0.0070, 0.0016, 0.0016, 'Eye_HL2')]:
        p, f = region(hx - hrx, hx + hrx, lambda x, a=hx, b=hz, c=hrx, d=hrz: ell_lo(x, c, d, a, b),
                      lambda x, a=hx, b=hz, c=hrx, d=hrz: ell_hi(x, c, d, a, b), 6, 3)
        objs.append(make_decal(nm, proj, p, f, 0.0022, mats['white']))
    # upper lash: thick, thin at inner corner, wing at outer
    wing = upper + [(outer[0] + 0.0045, outer[1] + 0.0042), (outer[0] + 0.0085, outer[1] + 0.0080)]
    def lw(s):
        return 0.0007 + 0.0036 * smoothstep(0.0, 0.35, s) * (1 - smoothstep(0.80, 1.0, s)) + 0.0010 * gauss(s - 0.72, 0.1)
    p, f = ribbon2d(wing, lw, side=1.0, n=40)
    objs.append(make_decal('Lash_Upper', proj, [(x, z - 0.0004) for x, z in p], f, 0.0024, mats['lash']))
    # lower lash: thin, outer half
    lw2 = lambda s: 0.0011 * math.sin(math.pi * min(s * 1.1, 1.0)) + 0.0002
    lseg = [q for q in lower if q[0] > cx - 0.004]
    p, f = ribbon2d(lseg, lw2, side=-1.0, n=16)
    objs.append(make_decal('Lash_Lower', proj, p, f, 0.0020, mats['lash']))
    # lid crease
    crease = [(x, z + 0.0045) for (x, z) in upper if x > cx - 0.011]
    p, f = ribbon2d(crease, lambda s: 0.0007 * math.sin(math.pi * s) + 0.0001, side=1.0, n=16)
    objs.append(make_decal('Lid_Crease', proj, p, f, 0.0010, mats['crease']))
    # brows: thin shaped arc
    brow = bez([(cx - 0.021, cz + 0.0300), (cx - 0.006, cz + 0.0362), (cx + 0.010, cz + 0.0368), (cx + 0.025, cz + 0.0300)], 20)
    p, f = ribbon2d(brow, lambda s: 0.0026 * (1 - 0.75 * s) + 0.0003, side=1.0, n=20)
    objs.append(make_decal('Brows', proj, p, f, 0.0010, mats['brow']))
    # mouth: small soft smile line
    mouth = bez([(0.0, 1.3555), (0.0055, 1.3560), (0.0095, 1.3578)], 10)
    p, f = ribbon2d(mouth, lambda s: 0.0011 * (1 - 0.6 * s), side=-1.0, n=10)
    objs.append(make_decal('Mouth', proj, [(x, z + 0.0005) for x, z in p], f, 0.0008, mats['mouth']))
    # lower lip tint
    p, f = region(-0.0001, 0.0085, lambda x: 1.3555 - 0.0060 * math.sqrt(max(0, 1 - (x / 0.0086) ** 2)),
                  lambda x: 1.3548, 8, 2)
    objs.append(make_decal('Lips', proj, p, f, 0.0006, mats['lip']))
    # nose shadow tick
    nose = bez([(0.0006, 1.3770), (0.0030, 1.3775), (0.0046, 1.3790)], 8)
    p, f = ribbon2d(nose, lambda s: 0.0009 * math.sin(math.pi * s) + 0.0001, side=-1.0, n=8)
    objs.append(make_decal('Nose', proj, p, f, 0.0008, mats['skin_sh']))
    # blush
    bx, bz, brx, brz = 0.054, 1.390, 0.012, 0.0055
    p, f = region(bx - brx, bx + brx, lambda x: ell_lo(x, brx, brz, bx, bz), lambda x: ell_hi(x, brx, brz, bx, bz), 8, 4)
    objs.append(make_decal('Blush', proj, p, f, 0.0005, mats['blush']))
    for o in objs:
        o.parent = None
    face = lib.join(objs, 'Eyes')
    return face
