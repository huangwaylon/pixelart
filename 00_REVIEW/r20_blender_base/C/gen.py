"""r20 Track C: Koyuki anime toon base model, built from scratch.

Blender -b --factory-startup -P gen.py -- <outdir> --build base|sprite

Construction: everything is authored in head units (H = 1) with feet at z = 0, then uniformly scaled so the hair
crown sits at z = 1.0. Forms are analytic low-poly cages (superellipse z-slice lofts, frame-transported tubes, offset
sheets over the head) smoothed with Subdivision Surface. Face features are conforming decal geometry ray-projected
onto the subdivided head surface.
"""
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else "/tmp/r20c"
BUILD = argv[argv.index("--build") + 1] if "--build" in argv else "base"
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
SC = bpy.context.scene

# ----------------------------------------------------------------------------------------------------------------
# materials
HEX = dict(skin="FCD6B4", skin_shadow="EBA586", blush="F4A0A0", mouth="8E2C4A", eye_white="FFFFFF", iris="2C9696",
           iris_dark="1C4C54", lash="20223E", brow="6E3C3A", catchlight="FFFFFF", hair="A85A3A",
           hair_shadow="6E3C3A", hair_hi="D08658", teal="2A8C8E", teal_dark="1C4C54", teal_light="6ACBB6",
           coat="F2E6CE", coat_shadow="D2BFA4", rust="A85A3A", belt="6E3C3A", gold="E2A434", tights="45435E",
           boots="6E3C3A", fur="F2E6CE")


def s2l(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


MATS = {}


def M(name):
    if name in MATS:
        return MATS[name]
    h = HEX[name]
    rgb = [s2l(int(h[i:i + 2], 16) / 255.0) for i in (0, 2, 4)]
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*rgb, 1.0)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.8
    MATS[name] = m
    return m


# ----------------------------------------------------------------------------------------------------------------
# math helpers
V = Vector


def spow(v, e):
    return math.copysign(abs(v) ** e, v)


def lerp(a, b, t):
    return a + (b - a) * t


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def catmull(pts, n, closed=False):
    P = [V(p) for p in pts]
    if closed:
        ext = [P[-1]] + P + [P[0], P[1]]
        segs = len(P)
    else:
        ext = [P[0] * 2 - P[1]] + P + [P[-1] * 2 - P[-2]]
        segs = len(P) - 1
    out = []
    for i in range(segs):
        p0, p1, p2, p3 = ext[i], ext[i + 1], ext[i + 2], ext[i + 3]
        for k in range(n):
            t = k / n
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t +
                              (-p0 + 3 * p1 - 3 * p2 + p3) * t * t * t))
    if not closed:
        out.append(P[-1].copy())
    return out


def table_interp(table, x, col):
    """Catmull-Rom interpolation of column `col` of a table sorted by column 0 (ascending or descending)."""
    xs = [r[0] for r in table]
    asc = xs[-1] > xs[0]
    n = len(table)
    for i in range(n - 1):
        a, b = xs[i], xs[i + 1]
        if (asc and a <= x <= b) or ((not asc) and b <= x <= a):
            t = (x - a) / (b - a) if b != a else 0.0
            v0 = table[max(i - 1, 0)][col]
            v1 = table[i][col]
            v2 = table[i + 1][col]
            v3 = table[min(i + 2, n - 1)][col]
            return 0.5 * ((2 * v1) + (-v0 + v2) * t + (2 * v0 - 5 * v1 + 4 * v2 - v3) * t * t +
                          (-v0 + 3 * v1 - 3 * v2 + v3) * t ** 3)
    return table[0][col] if ((asc and x < xs[0]) or ((not asc) and x > xs[0])) else table[-1][col]


def se_pt(phi, w, yf, yb, yc=0.0, nf=2.0, nb=2.0):
    """superellipse cross-section point; phi=0 front (-Y), phi=90deg -> +X."""
    s, c = math.sin(phi), math.cos(phi)
    if c >= 0:
        n = nf
        y = yc - (yc - yf) * (c ** (2.0 / n))
    else:
        n = nb
        y = yc + (yb - yc) * ((-c) ** (2.0 / n))
    x = w * spow(s, 2.0 / n)
    return x, y


# ----------------------------------------------------------------------------------------------------------------
# mesh builders
ALL = []


def new_obj(name, me, mats):
    for m in mats:
        me.materials.append(M(m))
    ob = bpy.data.objects.new(name, me)
    SC.collection.objects.link(ob)
    ALL.append(ob)
    return ob


def add_sub(ob, lv=2):
    md = ob.modifiers.new("subsurf", "SUBSURF")
    md.levels = lv
    md.render_levels = lv
    return md


def add_solid(ob, th, off=-1.0):
    md = ob.modifiers.new("solidify", "SOLIDIFY")
    md.thickness = th
    md.offset = off
    md.use_even_offset = True
    return md


def grid(name, rows, mats=("coat",), closed=True, matfn=None, cap0=False, cap1=False, capmat=0, sub=2,
         solid=0.0, hint=None, smooth_shade=True, pivot=None):
    """rows: list of rings (list of Vector). A row with a single point is a pole. Faces between rows."""
    bm = bmesh.new()
    vrows = [[bm.verts.new(p) for p in r] for r in rows]
    for r in range(len(vrows) - 1):
        A, B = vrows[r], vrows[r + 1]
        if len(A) == 1 or len(B) == 1:
            pole, ring, flip = (A[0], B, False) if len(A) == 1 else (B[0], A, True)
            m = len(ring)
            for j in range(m if closed else m - 1):
                f = bm.faces.new((pole, ring[j], ring[(j + 1) % m]))
                f.material_index = matfn(r, j) if matfn else 0
            continue
        m = len(A)
        for j in range(m if closed else m - 1):
            jj = (j + 1) % m
            f = bm.faces.new((A[j], B[j], B[jj], A[jj]))
            f.material_index = matfn(r, j) if matfn else 0
    for cap, ring in ((cap0, vrows[0]), (cap1, vrows[-1])):
        if cap and len(ring) > 2:
            c = sum((v.co for v in ring), V()) / len(ring)
            cv = bm.verts.new(c)
            m = len(ring)
            for j in range(m):
                f = bm.faces.new((cv, ring[j], ring[(j + 1) % m]))
                f.material_index = capmat
    bm.normal_update()
    if hint is None:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    else:
        orient(bm, hint)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = new_obj(name, me, mats)
    if smooth_shade:
        me.shade_smooth()
    if solid:
        add_solid(ob, solid)
    if sub:
        add_sub(ob, sub)
    if pivot is not None:
        set_pivot(ob, pivot)
    return ob


def orient(bm, hint):
    """flip faces so normals point away from hint (a point) or along hint (a callable returning a direction)."""
    bm.normal_update()
    score = 0.0
    for f in bm.faces:
        c = f.calc_center_median()
        d = hint(c) if callable(hint) else (c - V(hint))
        score += f.normal.dot(d) * f.calc_area()
    if score < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)


def set_pivot(ob, p):
    p = V(p)
    ob.data.transform(Matrix.Translation(-p))
    ob.location = p


def frames(path, up):
    T = []
    n = len(path)
    for i in range(n):
        a = path[max(i - 1, 0)]
        b = path[min(i + 1, n - 1)]
        T.append((b - a).normalized())
    N1 = []
    n1 = (up - up.dot(T[0]) * T[0]).normalized()
    for i in range(n):
        n1 = (n1 - n1.dot(T[i]) * T[i]).normalized()
        N1.append(n1.copy())
    N2 = [T[i].cross(N1[i]) for i in range(n)]
    return T, N1, N2


def arclen(path):
    L = [0.0]
    for i in range(1, len(path)):
        L.append(L[-1] + (path[i] - path[i - 1]).length)
    tot = L[-1] or 1.0
    return [l / tot for l in L]


def tube_rows(path, prof, N=12, up=V((0, 0, 1)), pole0=False, pole1=False, closed_path=False):
    """prof(f, ang, i) -> (a, b) offsets along frame axes (n1, n2)."""
    if closed_path:
        n = len(path)
        T = [(path[(i + 1) % n] - path[i - 1]).normalized() for i in range(n)]
        N1, n1 = [], (up - up.dot(T[0]) * T[0]).normalized()
        for i in range(n):
            n1 = (n1 - n1.dot(T[i]) * T[i]).normalized()
            N1.append(n1.copy())
        N2 = [T[i].cross(N1[i]) for i in range(n)]
        F = [i / n for i in range(n)]
    else:
        T, N1, N2 = frames(path, up)
        F = arclen(path)
    rows = []
    for i, p in enumerate(path):
        if (pole0 and i == 0) or (pole1 and i == len(path) - 1):
            rows.append([p.copy()])
            continue
        ring = []
        for j in range(N):
            ang = 2 * math.pi * j / N
            a, b = prof(F[i], ang, i)
            ring.append(p + N1[i] * a + N2[i] * b)
        rows.append(ring)
    return rows


def ellipse_prof(ra_fn, rb_fn, mod=None):
    def prof(f, ang, i):
        ra, rb = ra_fn(f), rb_fn(f)
        k = mod(f, ang) if mod else 1.0
        return ra * math.cos(ang) * k, rb * math.sin(ang) * k
    return prof


def profile_fn(table):
    """piecewise smooth radius along f in [0,1] from (f, r) table."""
    return lambda f: max(0.0, table_interp(table, f, 1))


def zloft(rings_tab, N=32, cx=0.0, cy=0.0, mod=None):
    """rings_tab: rows (z, w, yf, yb, yc, nf, nb); returns ring rows top->bottom."""
    rows = []
    for (z, w, yf, yb, yc, nf, nb) in rings_tab:
        ring = []
        for j in range(N):
            phi = 2 * math.pi * j / N
            x, y = se_pt(phi, w, yf, yb, yc, nf, nb)
            if mod:
                x, y = mod(z, phi, x, y)
            ring.append(V((cx + x, cy + y, z)))
        rows.append(ring)
    return rows


def resample_table(tab, n_between):
    """densify a z-slice table by Catmull-Rom interpolation of every column."""
    out = []
    for i in range(len(tab) - 1):
        for k in range(n_between):
            t = k / n_between
            z = lerp(tab[i][0], tab[i + 1][0], t)
            out.append(tuple([z] + [table_interp(tab, z, c) for c in range(1, len(tab[0]))]))
    out.append(tab[-1])
    return out


# ----------------------------------------------------------------------------------------------------------------
# build parameters (head units, feet at z=0)
SPRITE = BUILD == "sprite"
CROWN_L, CHIN_L = 0.5, -0.47           # head-local crown / chin
HEAD_H = CROWN_L - CHIN_L
HC = 2.9 if SPRITE else 4.9            # head-local origin height (world, head units)
CHIN = HC + CHIN_L
P = dict(
    base=dict(sh=4.10, belt=3.35, hem=2.12, crotch=2.35, knee=1.22, boot=0.90, shw=0.33, waist=0.36,
              hemw=0.80, hemd=0.50, bust=0.415, arm_len=(0.80, 0.78), mit=0.27, ptail_end=3.38,
              bhair_end=2.70, footlen=0.27, legw=0.145, arm_ang=15, farm_ang=15, shj=0.30, calf=0.118),
    sprite=dict(sh=2.12, belt=1.70, hem=0.80, crotch=0.98, knee=0.52, boot=0.40, shw=0.37, waist=0.425,
                hemw=0.75, hemd=0.44, bust=0.465, arm_len=(0.50, 0.46), mit=0.25, ptail_end=1.76,
                bhair_end=1.70, footlen=0.23, legw=0.15, arm_ang=24, farm_ang=17, shj=0.34, calf=0.12),
)["sprite" if SPRITE else "base"]


def L(x, y, z):
    """head-local -> world (head units)."""
    return V((x, y, z + HC))


# ----------------------------------------------------------------------------------------------------------------
# HEAD (head-local coords: crown z=+0.5, chin z=-0.47, face toward -Y)
#        z      w      yf      yb     yc    nf    nb
HEAD = [(0.500, 0.000, 0.040, 0.040, 0.04, 2.0, 2.0),
        (0.475, 0.190, -0.125, 0.215, 0.04, 2.0, 2.0),
        (0.430, 0.285, -0.225, 0.330, 0.03, 2.0, 2.0),
        (0.350, 0.352, -0.310, 0.410, 0.02, 2.1, 2.0),
        (0.240, 0.380, -0.365, 0.450, 0.01, 2.2, 2.0),
        (0.120, 0.396, -0.400, 0.470, 0.00, 2.3, 2.1),
        (0.000, 0.400, -0.418, 0.465, 0.00, 2.4, 2.1),
        (-0.080, 0.397, -0.424, 0.445, 0.00, 2.45, 2.1),
        (-0.160, 0.388, -0.426, 0.395, 0.00, 2.4, 2.1),
        (-0.220, 0.372, -0.422, 0.335, 0.00, 2.3, 2.05),
        (-0.280, 0.343, -0.408, 0.250, -0.02, 2.15, 2.0),
        (-0.330, 0.302, -0.392, 0.160, -0.05, 2.0, 2.0),
        (-0.375, 0.250, -0.376, 0.070, -0.09, 1.9, 2.0),
        (-0.415, 0.190, -0.362, -0.020, -0.14, 1.85, 2.0),
        (-0.445, 0.128, -0.350, -0.100, -0.19, 1.9, 2.0),
        (-0.462, 0.072, -0.338, -0.165, -0.23, 2.0, 2.0),
        (-0.470, 0.000, -0.315, -0.230, -0.26, 2.0, 2.0)]


def head_params(z):
    return [table_interp(HEAD, z, c) for c in range(1, 7)]


def face_disp(x, y, z):
    """profile sculpt: eye inset, forward cheek bulge, slight mouth dip (added to y; + = back)."""
    k = smooth((-y - 0.20) / 0.15)
    if k <= 0:
        return 0.0
    ax = abs(x)
    d = 0.022 * math.exp(-(((ax - 0.18) / 0.085) ** 2 + ((z + 0.09) / 0.075) ** 2))
    d -= 0.032 * math.exp(-(((ax - 0.16) / 0.12) ** 2 + ((z + 0.235) / 0.075) ** 2))
    d += 0.008 * math.exp(-((x / 0.06) ** 2 + ((z + 0.31) / 0.03) ** 2))
    return d * k


def head_pt(z, phi):
    z = max(min(z, CROWN_L), CHIN_L)
    w, yf, yb, yc, nf, nb = head_params(z)
    x, y = se_pt(phi, max(w, 0.0), yf, yb, yc, nf, nb)
    return V((x, y + face_disp(x, y, z), z))


def head_normal(z, phi):
    e = 0.004
    p = head_pt(z, phi)
    dphi = head_pt(z, phi + e) - head_pt(z, phi - e)
    dz = head_pt(min(z + e, CROWN_L - 1e-4), phi) - head_pt(max(z - e, CHIN_L + 1e-4), phi)
    n = dphi.cross(dz)
    if n.length < 1e-9:
        n = p - V((0, 0.02, 0))
    n.normalize()
    if n.dot(p - V((0, 0.02, -0.05))) < 0:
        n = -n
    return n


def head_off(z, phi, d):
    z = max(min(z, CROWN_L - 5e-4), CHIN_L + 5e-4)
    return head_pt(z, phi) + head_normal(z, phi) * d


def build_head():
    K = 30
    zs = [CROWN_L - HEAD_H * (1 - math.cos(math.pi * k / K)) / 2 for k in range(K + 1)]
    N = 36
    rows = []
    for i, z in enumerate(zs):
        if i == 0:
            rows.append([L(0, 0.04, CROWN_L)])
            continue
        if i == K:
            rows.append([L(0, -0.30, CHIN_L)])
            continue
        rows.append([L(*head_pt(z, 2 * math.pi * j / N)) for j in range(N)])
    head = grid("head", rows, mats=("skin",), sub=2)
    # neck
    nk = [L(0, 0.035, -0.28), L(0, 0.035, -0.55), V((0, 0.02, P["sh"] - 0.05))]
    nk = catmull(nk, 4)
    rows = tube_rows(nk, ellipse_prof(lambda f: 0.10, lambda f: 0.11), N=12, up=V((0, 1, 0)))
    grid("neck", rows, mats=("skin",), cap0=True, cap1=True, sub=2)
    # nose: a soft low bump (~0.02 protrusion), half-buried in the face
    ys = head_pt(-0.205, 0).y
    rows = []
    for k in range(9):
        t = k / 8
        z = lerp(-0.170, -0.232, t)
        env = math.sin(math.pi * t) ** 0.8
        if k in (0, 8):
            rows.append([L(0, ys + 0.012, z)])
            continue
        ring = []
        for j in range(12):
            a = 2 * math.pi * j / 12
            ca = math.cos(a)
            ring.append(L(0.017 * env * math.sin(a), ys + 0.012 - (0.012 + 0.017 * t ** 1.5) * env * max(0.0, ca)
                          + 0.012 * env * max(0.0, -ca), z))
        rows.append(ring)
    grid("nose", rows, mats=("skin",), cap0=False, cap1=False, sub=2)
    return head

# ----------------------------------------------------------------------------------------------------------------
# FACE DECALS
def bvh_of(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    return BVHTree.FromObject(ev, dg)


def project(bvh, x, z, layer):
    o = L(x, -2.0, z)
    hit = bvh.ray_cast(o, V((0, 1, 0)))
    if hit[0] is None:
        return L(x, -0.3, z)
    p, n = hit[0], hit[1]
    if n.y > 0:
        n = -n
    return p + n * (0.0025 + 0.0018 * layer)


def fill2d(outline, center, rings=3):
    K = len(outline)
    vs = [V(center)]
    for r in range(1, rings + 1):
        f = r / rings
        for p in outline:
            vs.append(V(center) + (V(p) - V(center)) * f)
    faces = []
    for k in range(K):
        faces.append((0, 1 + k, 1 + (k + 1) % K))
    for r in range(1, rings):
        b0, b1 = 1 + (r - 1) * K, 1 + r * K
        for k in range(K):
            kk = (k + 1) % K
            faces.append((b0 + k, b1 + k, b1 + kk, b0 + kk))
    return vs, faces


def strip2d(pts, thick_fn, under=0.006, normal_up=True):
    """band along polyline pts (2D, x,z) growing upward (perpendicular) by thick_fn(t)."""
    n = len(pts)
    vs, faces = [], []
    for i, p in enumerate(pts):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, n - 1)]
        d = (V(b) - V(a)).normalized()
        nrm = V((-d.y, d.x)) if normal_up else V((d.y, -d.x))
        if nrm.y < 0 and normal_up:
            nrm = -nrm
        t = i / (n - 1)
        vs.append(V(p) - nrm * under)
        vs.append(V(p) + nrm * thick_fn(t))
    for i in range(n - 1):
        faces.append((2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1))
    return vs, faces


def decal(name, mat, bvh, vs2, faces, layer, mirror=True):
    """vs2: 2D (x, z) head-local verts of her LEFT feature (+X); mirrored copy for the right."""
    bm = bmesh.new()
    sides = (1, -1) if mirror else (1,)
    for s in sides:
        vv = [bm.verts.new(project(bvh, s * p.x, p.y, layer)) for p in vs2]
        for f in faces:
            try:
                bm.faces.new([vv[i] for i in (f if s == 1 else f[::-1])])
            except ValueError:
                pass
    orient(bm, lambda c: V((0, -1, 0)))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = new_obj(name, me, [mat])
    me.shade_smooth()
    return ob


def pt_in_poly(p, poly):
    x, y = p
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xi = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if xi > x:
                inside = not inside
    return inside


def clip_to(pts, poly, center, shrink=0.004):
    out = []
    c = V(center)
    for p in pts:
        p = V(p)
        if pt_in_poly(p, poly):
            out.append(p)
            continue
        lo, hi = 0.0, 1.0
        for _ in range(24):
            m = (lo + hi) / 2
            if pt_in_poly(c + (p - c) * m, poly):
                lo = m
            else:
                hi = m
        q = c + (p - c) * lo
        out.append(q - (q - c).normalized() * shrink)
    return out


def ellipse2d(cx, cz, rx, rz, n=32, rot=0.0):
    out = []
    for k in range(n):
        a = 2 * math.pi * k / n
        x, z = rx * math.cos(a), rz * math.sin(a)
        out.append(V((cx + x * math.cos(rot) - z * math.sin(rot), cz + x * math.sin(rot) + z * math.cos(rot))))
    return out


def build_face(head):
    bvh = bvh_of(head)
    EX, EZ = 0.0, 0.0
    top = [(0.088, -0.112), (0.100, -0.050), (0.128, -0.008), (0.168, 0.012), (0.214, 0.002), (0.250, -0.036),
           (0.270, -0.086), (0.276, -0.128)]
    bot = [(0.262, -0.163), (0.228, -0.188), (0.186, -0.196), (0.142, -0.186), (0.110, -0.162)]
    top = [V((x + EX, z + EZ)) for x, z in top]
    bot = [V((x + EX, z + EZ)) for x, z in bot]
    outline = catmull(top + bot, 4, closed=True)
    outline = [V((p.x, p.y)) for p in outline]
    ec = V((0.182 + EX, -0.092 + EZ))
    vs, fs = fill2d(outline, ec, 3)
    decal("eye_white", "eye_white", bvh, vs, fs, 0)
    # iris
    ic = V((0.184 + EX, -0.102 + EZ))
    iris = clip_to(ellipse2d(ic.x, ic.y, 0.064, 0.092, 40), outline, ic)
    vs, fs = fill2d(iris, ic, 3)
    decal("iris", "iris", bvh, vs, fs, 1)
    # dark upper iris
    dz = ic.y + 0.012
    dark = [V((p.x, max(p.y, dz + 0.02 * (1 - ((p.x - ic.x) / 0.064) ** 2)))) for p in iris]
    vs, fs = fill2d(dark, V((ic.x, ic.y + 0.05)), 2)
    decal("iris_dark", "iris_dark", bvh, vs, fs, 2)
    # pupil
    vs, fs = fill2d(ellipse2d(ic.x, ic.y + 0.012, 0.026, 0.042, 24), V((ic.x, ic.y + 0.012)), 2)
    decal("pupil", "lash", bvh, vs, fs, 3)
    # catchlights
    vs, fs = fill2d(ellipse2d(ic.x + 0.024, ic.y + 0.040, 0.021, 0.024, 20), V((ic.x + 0.024, ic.y + 0.040)), 2)
    vs2, fs2 = fill2d(ellipse2d(ic.x - 0.026, ic.y - 0.045, 0.010, 0.011, 14), V((ic.x - 0.026, ic.y - 0.045)), 1)
    off = len(vs)
    decal("catchlight", "catchlight", bvh, vs + vs2, fs + [tuple(i + off for i in f) for f in fs2], 4)
    # upper lash line with outer flick
    tl = catmull(top + [V((0.292 + EX, -0.118 + EZ)), V((0.306 + EX, -0.112 + EZ))], 4)
    tl = [V((p.x, p.y)) for p in tl]
    nT = len(tl)

    def lash_th(t):
        if t < 0.78:
            return 0.010 + 0.022 * smooth(t / 0.6)
        return 0.032 * (1 - smooth((t - 0.78) / 0.22)) + 0.002

    vs, fs = strip2d(tl, lash_th, under=0.007)
    decal("lash", "lash", bvh, vs, fs, 4)
    # lower lid line (outer half)
    bl = [V((0.276 + EX, -0.128 + EZ))] + bot[:3]
    bl = [V((p.x, p.y)) for p in catmull(bl, 4)]
    vs, fs = strip2d(bl, lambda t: 0.007 * (1 - t) + 0.002, under=0.0, normal_up=False)
    decal("lid_low", "lash", bvh, vs, fs, 3)
    # brows
    br = [V((0.105, 0.060)), V((0.150, 0.076)), V((0.205, 0.077)), V((0.255, 0.060))]
    br = [V((p.x, p.y)) for p in catmull(br, 4)]
    vs, fs = strip2d(br, lambda t: 0.011 * math.sin(math.pi * (0.15 + 0.85 * t)) + 0.002, under=0.0)
    decal("brow", "brow", bvh, vs, fs, 1)
    # blush
    vs, fs = fill2d(ellipse2d(0.215, -0.222, 0.058, 0.026, 24), V((0.215, -0.222)), 2)
    decal("blush", "blush", bvh, vs, fs, 0.5)
    # mouth: small open smile
    mo = [V((-0.030, -0.302)), V((0.0, -0.307)), V((0.030, -0.302)), V((0.019, -0.319)), V((0.0, -0.326)),
          V((-0.019, -0.319))]
    mo = [V((p.x, p.y)) for p in catmull(mo, 4, closed=True)]
    vs, fs = fill2d(mo, V((0, -0.313)), 2)
    decal("mouth", "mouth", bvh, vs, fs, 1, mirror=False)
    # nose: only a tiny shadow tick under the soft tip
    vs, fs = fill2d(ellipse2d(0.008, -0.236, 0.011, 0.0045, 14, rot=0.25), V((0.008, -0.236)), 1)
    decal("nose_shadow", "skin_shadow", bvh, vs, fs, 1.5, mirror=False)


# ----------------------------------------------------------------------------------------------------------------
# HAIR
HCEN = V((0, 0.02, 0.0))                       # head-local centre for shell rays
WHORL = V((0, 1.0, 0.06)).normalized()          # hair converges toward the ponytail root


def cap_offset(z, phi):
    """hair volume over the skull: dome on top, widest at the temples, curving in toward the ears."""
    s2 = math.sin(phi) ** 2
    c = math.cos(phi)
    d = 0.068
    d += 0.082 * s2 * math.exp(-((z - 0.07) / 0.21) ** 2)            # temple width
    d += 0.035 * max(0.0, -c) * math.exp(-((z - 0.05) / 0.30) ** 2)  # full back of the head
    d -= 0.030 * s2 * smooth(-z / 0.16)                                # curve in below the temples
    return d


def whorl_ridge(p_local, amp=0.010, k=15):
    """clump ridges radiating from the crown whorl."""
    q = (p_local - HCEN).normalized()
    e1 = V((1, 0, 0))
    e2 = WHORL.cross(e1).normalized()
    a = math.atan2(q.dot(e2), q.dot(e1))
    dist = math.acos(max(-1.0, min(1.0, q.dot(WHORL))))
    return amp * math.cos(k * a) * smooth(dist / 0.45)


def back_level(z):
    sh, belt, bh_end = P["sh"], P["belt"], P["bhair_end"]
    tab = [(HC + 0.12, 0.45, 0.50, 0.06), (HC - 0.15, 0.49, 0.57, 0.12), (HC - 0.45, 0.50, 0.57, 0.16),
           (sh, 0.56, 0.48, 0.21), (sh - 0.45, 0.56, 0.40, 0.22), (belt, 0.53, 0.35, 0.22),
           (min(belt, bh_end) - 0.6, 0.44, 0.37, 0.24)]
    return [table_interp(tab, z, c) for c in (1, 2, 3)]


def build_hair(head):
    hbvh = bvh_of(head)
    # --- crown cap: offset shell, clump ridges flowing from the whorl; bottom edge rises toward the face
    N, R = 40, 14
    rows = [[L(0, 0.04, 0.5 + cap_offset(0.5, 0))]]
    for i in range(1, R + 1):
        v = i / R
        ring = []
        for j in range(N):
            phi = 2 * math.pi * j / N
            c = math.cos(phi)
            zb = -0.12 + 0.36 * c if c > 0 else -0.12 + 0.20 * c
            z = 0.5 - (0.5 - zb) * (v ** 0.9)
            d = cap_offset(z, phi) - 0.022
            d *= 1 - 0.3 * smooth((0.33 - z) / 0.09) * max(0.0, c)     # tuck the front edge under the bangs
            p = head_off(z, phi, d)
            p += head_normal(z, phi) * whorl_ridge(p, 0.005)
            ring.append(L(*p))
        rows.append(ring)
    grid("hair_cap", rows, mats=("hair_shadow",), solid=0.02, sub=1, hint=L(0, 0.02, 0))

    # --- bangs: ONE continuous shell combed from the ponytail root over a smooth crown dome to a blunt cut.
    #     Panels (centre ~40%) exist only in the bang zone: V notches in the cut + per-panel bulge + notch creases.
    cw = L(*HCEN)
    PROOT = V((0, 1.0, 0.06)).normalized()
    NOTCH = 0.52
    C, R = 88, 20
    p0, p1 = -math.pi, math.pi
    rows = []
    for i in range(R + 1):
        v = 0.06 + 0.94 * i / R
        ring = []
        for j in range(C + 1):
            u = j / C
            phi = lerp(p0, p1, u)
            ap = abs(phi)
            # cut line: blunt, V notches at +-NOTCH, side panels slope lower toward the temples
            dn = abs(ap - NOTCH)
            zcut = 0.085 + 0.052 * max(0.0, 1 - dn / 0.10) ** 1.3
            if ap > NOTCH:
                zcut -= 0.075 * smooth((ap - 0.75) / 0.6)
            # beyond the bangs the sheet ends on the cap's lower edge (above the ears / nape)
            zb_ = -0.12 + 0.36 * math.cos(phi) if math.cos(phi) > 0 else -0.12 + 0.20 * math.cos(phi)
            wside = smooth((ap - 1.30) / 0.25)
            zcut = lerp(zcut, zb_, wside)
            d1 = (L(*head_pt(zcut, phi)) - cw).normalized()
            d = PROOT.slerp(d1, v) if v < 1 else d1
            hit = hbvh.ray_cast(cw, d)
            p, n = hit[0], hit[1]
            if n.dot(d) < 0:
                n = -n
            pl = p - V((0, 0, HC))
            zl = pl.z
            phl = math.atan2(pl.x, -pl.y)
            base = cap_offset(zl, phl) + 0.010
            # bang zone weight: only the lowest ~0.25H above the cut carries panel shaping
            bz = smooth((0.36 - zl) / 0.22) * smooth((v - 0.4) / 0.3)
            if ap < NOTCH:
                pu = ap / NOTCH                                   # centre panel 0..1 from middle
                bulge = 0.016 * math.cos(pu * math.pi / 2)
            else:
                pu = min(1.0, (ap - NOTCH) / (1.36 - NOTCH))
                bulge = 0.013 * math.sin(math.pi * min(1.0, pu * 1.2))
            bulge *= 1 - wside
            crease = -0.016 * max(0.0, 1 - dn / 0.07)
            lift = base - 0.002
            side_w = smooth((abs(phl) - 0.80) / 0.55)
            wcut = smooth((v - 0.10) / 0.90)
            off = lerp(base, lerp(lift, base, side_w), wcut) + (bulge + crease) * bz
            # soft combed ridges converging to the ponytail root (crown only)
            off += 0.004 * math.cos(u * 34) * (1 - bz) * smooth(v * 4)
            nd = (n + d).normalized()
            q = p + nd * off
            if v > 0.86:
                q -= nd * 0.012 * ((v - 0.86) / 0.14) ** 2 * (1 - wside)
            ring.append(q)
        rows.append(ring)
    bob = grid("bangs", rows, mats=("hair",), closed=False, solid=0.025, sub=1, hint=lambda c: c - cw)
    bob.modifiers["solidify"].use_even_offset = False

    # --- side locks: straight blunt panels from the temple, tapered thickness, cupped to the cheek, split at the tip
    def lock_volume(name, mat, rows_c, wd, nrm, hw_fn, th_fn, cup, N=16):
        rows = []
        n = len(rows_c)
        for k, c in enumerate(rows_c):
            t = k / (n - 1)
            hw, th = hw_fn(t), th_fn(t)
            ring = []
            for j in range(N):
                a = 2 * math.pi * j / N
                u = spow(math.cos(a), 0.55)
                w = math.sin(a) * th / 2 * (0.35 + 0.65 * (1 - abs(u) ** 4))
                ring.append(c + wd * (u * hw) + nrm * (w + cup * (1 - u * u)))
            rows.append(ring)
        return grid(name, rows, mats=(mat,), cap0=True, cap1=True, sub=2)

    for s, nm in ((1, "sidelock_L"), (-1, "sidelock_R")):
        cx, cy = 0.448, -0.128
        wd = V((s * 0.70, -0.714, 0)).normalized()
        nrm = V((s * 0.714, 0.70, 0))
        Z0, Z1 = 0.22, -0.86
        parts = []
        cs = []
        for i in range(16):
            t = i / 15
            z = lerp(Z0, Z1, t)
            inward = -0.016 * smooth((t - 0.25) / 0.3) * (1 - smooth((t - 0.72) / 0.2))   # hug the cheek below the cheekbone
            cs.append(L(s * cx, cy, z) + nrm * inward)
        ob_ = lock_volume("sl_main", "hair", cs, wd, nrm, lambda t: 0.09 * (1 - 0.10 * smooth((t - 0.7) / 0.3)),
                          lambda t: lerp(0.062, 0.030, t), 0.012)
        # strand split: a V notch up the middle of the blunt cut
        me_ = ob_.data
        zc_ = HC + Z1
        for vtx in me_.vertices:
            if vtx.co.z < zc_ + 0.12:
                uu = (vtx.co - L(s * cx, cy, vtx.co.z - HC)).dot(wd) / 0.09
                k_ = max(0.0, 1 - abs(uu + 0.1) / 0.28)
                vtx.co.z += 0.075 * k_ * smooth((zc_ + 0.12 - vtx.co.z) / 0.12)
        parts.append(ob_)
        # soft inner layer (hair_shadow) just behind, slightly wider and shorter
        cs = [L(s * cx, cy, lerp(Z0, Z1 + 0.06, i / 15)) - nrm * 0.026 for i in range(16)]
        parts.append(lock_volume("sl_in", "hair_shadow", cs, wd, nrm, lambda t: 0.084, lambda t: lerp(0.03, 0.02, t), 0.012))
        join(parts, nm)

    # --- back hair: hair_shadow under-layer + 4 crisp overlapping locks with defined edges and slight V tips;
    #     the centre stays dark under the ponytail so the ponytail separates
    bh_end = P["bhair_end"]
    parts = []
    C, R = 18, 22
    rows = []
    ztop = HC + 0.12
    for i in range(R + 1):
        v = i / R
        ring = []
        for j in range(C + 1):
            u = lerp(-1.0, 1.0, j / C)
            zend = bh_end + 0.06 + 0.20 * abs(u) ** 1.2
            z = lerp(ztop, zend, v)
            xs, yc, ys = back_level(z)
            ring.append(V((xs * u, ys + (yc - ys) * (1 - u * u) - 0.04, z)))
        rows.append(ring)
    parts.append(grid("hb_under", rows, mats=("hair_shadow",), closed=False, solid=0.022, sub=1,
                      hint=lambda c: V((c.x, 1.0, 0))))
    locks = [  # u centre, u half-width, extra length (+ = shorter), layer lift, material
        (-0.80, 0.27, 0.10, 0.000, "hair"), (0.80, 0.27, 0.10, 0.000, "hair"),
        (-0.40, 0.30, 0.00, 0.016, "hair"), (0.40, 0.30, 0.00, 0.016, "hair"),
    ]
    for li, (uc, uh, sh_, lift, mat) in enumerate(locks):
        Rr, N = 24, 18
        rows = []
        zend = bh_end + 0.20 * abs(uc) ** 1.2 + sh_
        for i in range(Rr + 1):
            v = i / Rr
            z = lerp(ztop, zend, v)
            tip = smooth((v - 0.86) / 0.14)
            uhw = uh * (1 - 0.55 * tip)                   # slight V tip
            th = 0.030 * (1 - 0.5 * tip)
            ring = []
            for j in range(N):
                a = 2 * math.pi * j / N
                cu = spow(math.cos(a), 0.42)
                u = uc + cu * uhw
                xs, yc, ys = back_level(z)
                x = xs * u
                y = ys + (yc - ys) * (1 - u * u) + lift
                w = math.sin(a) * th / 2 * (0.3 + 0.7 * (1 - abs(cu) ** 3))
                y += 0.012 * (1 - cu * cu) * smooth(v * 3)   # each lock slightly rounded
                ring.append(V((x, y + w, z)))
            rows.append(ring)
        parts.append(grid("hb_lock_%d" % li, rows, mats=(mat,), cap0=True, cap1=True, sub=1))
    join(parts, "hair_back")

    # --- half-up ponytail: layered clumps on a true S, proud of the back hair
    root = L(0, 0.50, 0.0)
    drop = root.z - P["ptail_end"]
    S = [(0.0, 0.50), (0.06, 0.70), (0.20, 0.88), (0.38, 0.86), (0.58, 0.70), (0.78, 0.60), (0.92, 0.66), (1.0, 0.76)]
    rad = profile_fn([(0.0, 0.07), (0.06, 0.13), (0.20, 0.245), (0.40, 0.215), (0.62, 0.13), (0.85, 0.05), (1.0, 0.0)])

    def ycl(ff):
        z = root.z - drop * ff
        y = table_interp(S, ff, 1)
        if z < HC - 0.15:
            y = max(y, back_level(z)[1] + 0.08 + rad(ff) * 0.9)
        return y

    clumps = []
    cl = [  # x offset, y offset, radius scale, end fraction, material, x drift at tip
        (0.0, 0.0, 1.0, 1.0, "hair", 0.0),
        (0.10, 0.02, 0.62, 0.88, "hair", 0.07),
        (-0.10, 0.02, 0.62, 0.84, "hair", -0.07),
        (0.0, -0.075, 0.78, 0.93, "hair_shadow", 0.0),
        (0.02, 0.07, 0.55, 0.62, "hair", 0.03),
    ]
    PT = []
    for ci, (xo, yo, rs, ef, mat, drift) in enumerate(cl):
        cps = []
        for k in range(15):
            ff = ef * k / 14
            cps.append(V((xo * math.sin(math.pi * min(1, ff * 1.6)) + drift * ff ** 2, ycl(ff) + yo * (1 - ff * 0.5),
                          root.z - drop * ff)))
        path = catmull(cps, 2)
        if ci == 0:
            PT = [(p.z, p.y, rad(i / (len(path) - 1))) for i, p in enumerate(path)]
        prof = ellipse_prof(lambda f, rs=rs: rad(f) * rs * 1.08 + 0.002, lambda f, rs=rs: rad(f) * rs * 0.92 + 0.002,
                            mod=lambda f, a: 1 + 0.07 * math.cos(3 * a) * smooth(f * 4))
        rows = tube_rows(path, prof, N=16, up=V((1, 0, 0)), pole1=True)
        rows[-1] = [path[-1] + (path[-1] - path[-2]).normalized() * 0.03]
        clumps.append(grid("ponytail_%d" % ci, rows, mats=(mat,), cap0=True, sub=1))
    join(clumps, "ponytail")
    return PT

def join(objs, name):
    if len(objs) == 1:
        objs[0].name = name
        return objs[0]
    # apply modifiers into mesh, then join (keep one subsurf-free result)
    dg = bpy.context.evaluated_depsgraph_get()
    bm = bmesh.new()
    mats = []
    for ob in objs:
        ev = ob.evaluated_get(dg)
        me = bpy.data.meshes.new_from_object(ev)
        me.transform(ob.matrix_world)
        mi_map = []
        for m in me.materials:
            if m.name not in mats:
                mats.append(m.name)
            mi_map.append(mats.index(m.name))
        for p in me.polygons:
            p.material_index = mi_map[p.material_index] if mi_map else 0
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    for ob in objs:
        ALL.remove(ob)
        bpy.data.objects.remove(ob)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = new_obj(name, me, [m.split(".")[0] for m in mats])
    me.shade_smooth()
    return ob


def build_sheen():
    """hair_hi: broken angel-ring of tapered strokes on the bangs/top, gaps at the panel notches."""
    shells = [o for o in ALL if o.name in ("bangs", "hair_cap")]
    trees = [bvh_of(o) for o in shells]
    c0 = L(*HCEN)
    bm = bmesh.new()
    segs = [(-0.40, -0.13), (0.07, 0.35), (0.64, 0.92), (1.00, 1.26), (-0.92, -0.64), (-1.26, -1.00)]
    for k, (a0, a1) in enumerate(segs):
        zc = 0.255 - 0.02 * (abs(a0 + a1) / 2) ** 2
        n = 12
        ring_o, ring_i = [], []
        for i in range(n + 1):
            t = i / n
            phi = lerp(a0, a1, t)
            hh = 0.0145 * math.sin(math.pi * t) ** 0.8 + 0.0008
            zz = zc
            for dz, lst in ((hh, ring_o), (-hh * 0.7, ring_i)):
                d = (L(*head_off(zz + dz, phi, 0.0)) - c0).normalized()
                o = c0 + d * 2.0
                best = None
                for tr in trees:
                    h = tr.ray_cast(o, -d)
                    if h[0] is not None and (best is None or h[3] < best[3]):
                        best = h
                p = best[0] + d * 0.005 if best else L(*head_off(zz + dz, phi, 0.12))
                lst.append(bm.verts.new(p))
        for i in range(n):
            bm.faces.new((ring_o[i], ring_i[i], ring_i[i + 1], ring_o[i + 1]))
    orient(bm, lambda c: c - c0)
    me = bpy.data.meshes.new("hair_sheen")
    bm.to_mesh(me)
    bm.free()
    ob = new_obj("hair_sheen", me, ["hair_hi"])
    me.shade_smooth()
    return ob


# ----------------------------------------------------------------------------------------------------------------
# BOW
def build_bow(PT):
    K = L(0, 0.61, 0.06)
    parts = []
    for s in (1, -1):
        up, back = math.radians(5), math.radians(25)
        ea = V((s * math.cos(up) * math.cos(back), math.sin(back), math.sin(up))).normalized()
        n0 = V((0, 1, 0))
        eb = n0.cross(ea).normalized()
        if eb.z < 0:
            eb = -eb
        nn = ea.cross(eb).normalized()
        if nn.y < 0:
            nn = -nn
        Lw = 0.84
        # puffy teardrop: narrow pinch at the knot, round bulb at the tip
        OL = [(0.0, 0.0), (0.18, 0.026), (0.36, 0.052), (0.52, 0.078), (0.64, 0.090), (0.725, 0.084), (0.765, 0.052),
              (0.775, 0.0), (0.762, -0.048), (0.715, -0.078), (0.62, -0.086), (0.48, -0.072), (0.32, -0.046),
              (0.16, -0.022)]
        pts2 = catmull([V((x * Lw / 0.775, y * 0.88, 0)) for x, y in OL], 4, closed=True)
        M_ = len(pts2)
        pts = [K + ea * q.x + eb * q.y for q in pts2]
        cen = sum(pts, V()) / len(pts)
        rows = []
        for k, p in enumerate(pts):
            q = pts2[k]
            g = min(1.0, max(0.0, q.x / Lw))
            nxt, prv = pts[(k + 1) % M_], pts[k - 1]
            tg = (nxt - prv).normalized()
            m = nn.cross(tg).normalized()
            if m.dot(p - cen) < 0:
                m = -m
            ell = 0.6 + 0.4 * math.sqrt(max(0.0, 1 - (q.y / 0.095) ** 2))
            hw = (0.045 + 0.13 * math.sin(math.pi * min(1.0, 0.15 + 0.85 * g)) ** 0.5) * ell        # ribbon half depth: teardrop when seen edge-on
            th = 0.022 + 0.52 * abs(q.y)                  # fat satin pillow: rim fills in, leaving a slot
            fk = k / M_
            crease = 1 - 0.18 * math.exp(-((fk - 0.27) / 0.05) ** 2)
            ring = []
            for j in range(12):
                a = 2 * math.pi * j / 12
                ring.append(p + nn * (hw * crease * math.cos(a)) + m * (th * math.sin(a) + 0.012 * abs(math.cos(a))))
            rows.append(ring)
        ob = grid_closed_rows("bow_loop_%d" % (s > 0), rows, "teal")
        parts.append(ob)
        inner = [cen + V(((p - cen).x * 0.95, (p - cen).y * 0.95, (p - cen).z * 0.62)) for p in pts]
        parts.append(grid("bow_in_%d" % (s > 0), [[cen + nn * 0.012]] + [inner], mats=("teal_dark",), sub=1,
                          hint=lambda c: V((0, 1, 0))))
    # knot
    rows = []
    for i in range(9):
        v = i / 8
        z = lerp(0.075, -0.075, v)
        r = math.sin(math.pi * (0.02 + 0.96 * v)) ** 0.55
        r *= 1 - 0.10 * math.exp(-((v - 0.5) / 0.12) ** 2)      # pinched wrap band
        ring = []
        for j in range(12):
            a = 2 * math.pi * j / 12
            ring.append(K + V((0.068 * r * math.sin(a), 0.064 * r * -math.cos(a) * (1 if math.cos(a) < 0 else 0.8), z)))
        rows.append(ring)
    parts.append(grid("bow_knot", rows, mats=("teal_dark",), cap0=True, cap1=True, sub=2))
    # tails: flat swallowtail ribbons lying on the ponytail surface, ending at the shoulder blades
    zend = HC - 1.0
    # walk along the ponytail centreline (handles the backward-running root), tails lie on its upper/back surface
    cpts = [V((0, y, z)) for (z, y, r) in PT]
    crad = [r for (z, y, r) in PT]
    iend = max(i for i, p in enumerate(cpts) if p.z >= zend)
    X = V((1, 0, 0))
    for s in (1, -1):
        rows = []
        R = 22
        for i in range(R + 1):
            v = i / R
            fi = v * iend
            i0 = min(int(fi), len(cpts) - 2)
            t = fi - i0
            C = cpts[i0].lerp(cpts[i0 + 1], t)
            T = (cpts[i0 + 1] - cpts[i0]).normalized()
            Nb = X.cross(T).normalized()
            pr = lerp(crad[i0], crad[i0 + 1], t)
            R_ = pr * 1.02 + 0.02 + 0.05 * (1 - smooth(v / 0.25))   # ride over the side clumps near the root
            th_ = s * lerp(0.15, 1.0, smooth(v * 1.3))
            P_ = C + (X * math.sin(th_) + Nb * math.cos(th_)) * R_
            if v < 0.08:   # grow out of the knot
                P_ = P_.lerp(K + V((s * 0.03, 0.04, -0.02)), smooth(1 - v / 0.08))
            tg = X * math.cos(th_) - Nb * math.sin(th_)
            hw = lerp(0.036, 0.046, v)
            ring = []
            for j in range(5):
                u = j / 4 * 2 - 1
                q = P_ + tg * (u * hw)
                if i == R:
                    q -= T * (0.06 * (1 - abs(u)))   # swallowtail V notch
                ring.append(q)
            rows.append(ring)
        parts.append(grid("bow_tail_%d" % (s > 0), rows, mats=("teal",), closed=False, solid=0.012, sub=2,
                          hint=lambda c: V((0, 1, 0.3))))
    join(parts, "bow")

# ----------------------------------------------------------------------------------------------------------------
# BODY / OUTFIT
def coat_table():
    sh, belt, hem = P["sh"], P["belt"], P["hem"]
    w, ww, hmw, hd, bu = P["shw"], P["waist"], P["hemw"], P["hemd"], P["bust"]
    top = CHIN - 0.10
    chest = lerp(sh, belt, 0.34)
    sk = lambda t, a, b: lerp(a, b, t)
    t = [
        (top, 0.12, -0.12, 0.13, 0.0, 2.0, 2.0),
        (sh + 0.08, 0.20, -0.14, 0.15, 0.0, 2.1, 2.1),           # neck base: shoulders slope from here
        (sh + 0.02, 0.27, -0.16, 0.165, 0.0, 2.2, 2.2),
        (sh - 0.05, w, -0.195, 0.18, 0.0, 2.3, 2.3),             # shoulder joint line
        (sh - 0.17, w + 0.03, -0.235, 0.185, 0.0, 2.3, 2.3),      # under-arm
        (chest, bu, -0.275, 0.18, 0.0, 2.2, 2.3),                 # bust
        (lerp(chest, belt, 0.6), (bu + ww) / 2 - 0.012, -0.215, 0.165, 0.0, 2.1, 2.2),
        (belt, ww, -0.185, 0.152, 0.0, 2.0, 2.1),                 # pinched waist
        (belt - 0.07, ww + 0.035, -0.205, 0.175, 0.0, 2.0, 2.05),  # flare starts at the belt
        (sk(0.35, belt, hem), sk(0.42, ww, hmw), sk(0.42, -0.205, -hd), sk(0.42, 0.175, hd + 0.07), 0.0, 2.0, 2.0),
        (sk(0.70, belt, hem), sk(0.76, ww, hmw), sk(0.76, -0.205, -hd), sk(0.76, 0.175, hd + 0.07), 0.0, 2.0, 2.0),
        (hem + 0.10, hmw - 0.02, -(hd - 0.02), hd + 0.06, 0.0, 2.0, 2.0),
        (hem, hmw, -hd, hd + 0.08, 0.0, 2.0, 2.0),
    ]
    return t


def coat_ring(z):
    t = coat_table()
    return [table_interp(t, z, c) for c in range(1, 7)]


def coat_front_y(x, z):
    w, yf, yb, yc, nf, nb = coat_ring(z)
    s = min(abs(x) / w, 0.999) ** (nf / 2)
    c = math.sqrt(max(0.0, 1 - s * s))
    return yc - (yc - yf) * c ** (2 / nf)


def build_coat():
    tab = resample_table(coat_table(), 4)
    hem, belt = P["hem"], P["belt"]
    N = 64

    def mod(z, phi, x, y):
        # soft vertical folds on the skirt
        k = smooth((belt - 0.1 - z) / (belt - hem))
        a = 1 + 0.032 * k * math.cos(phi * 10 + 0.3)
        # slightly curved hem: sides dip a touch
        return x * a, y * a

    rows = zloft(tab, N=N, mod=mod)
    # curved hem: lower the hem ring's sides slightly, front/back up
    for ring in rows[-1:]:
        for j, p in enumerate(ring):
            phi = 2 * math.pi * j / N
            p.z += 0.025 * math.cos(phi) ** 2 - 0.01 + 0.014 * math.cos(phi * 10 + 0.3)
    # inner hem lip (coat_shadow underside)
    last = rows[-1]
    lip = [V((p.x * 0.93, p.y * 0.93, p.z + 0.03)) for p in last]
    rows.append(lip)
    nrows = len(rows)
    trim_z = hem + 0.085

    def matfn(r, j):
        if r >= nrows - 2:
            return 2
        z = (rows[r][j].z + rows[r + 1][j].z) / 2
        return 1 if z < trim_z else 0

    coat = grid("coat", rows, mats=("coat", "rust", "coat_shadow"), matfn=matfn, cap0=True, cap1=True, capmat=2,
                sub=1)
    # belt
    rows = []
    for dz in (0.03, 0.03, -0.03, -0.03):
        pass
    for k, (dz, dr) in enumerate(((0.032, 0.0), (0.034, 0.018), (-0.034, 0.018), (-0.032, 0.0))):
        z = belt + dz
        w, yf, yb, yc, nf, nb = coat_ring(z)
        ring = []
        for j in range(48):
            phi = 2 * math.pi * j / 48
            x, y = se_pt(phi, w + dr, yf - dr, yb + dr, yc, nf, nb)
            ring.append(V((x, y, z)))
        rows.append(ring)
    grid("belt", rows, mats=("belt",), sub=1)
    # buckle
    yb_ = coat_front_y(0, belt) - 0.025
    rows = []
    for k, (dy, sc) in enumerate(((0.012, 0.85), (0.0, 1.0), (-0.012, 1.0), (-0.02, 0.8))):
        ring = []
        for j in range(16):
            a = 2 * math.pi * j / 16
            ring.append(V((0.045 * sc * spow(math.cos(a), 0.5), yb_ + dy, belt + 0.038 * sc * spow(math.sin(a), 0.5))))
        rows.append(ring)
    grid("buckle", rows, mats=("gold",), cap0=True, cap1=True, sub=1)
    # buttons
    sh = P["sh"]
    above = [lerp(belt, CHIN - 0.28, f) for f in (0.2, 0.47, 0.74)]
    below = [lerp(belt, hem, f) for f in (0.2, 0.43, 0.66)]
    bts = []
    for z in above + below:
        y = coat_front_y(0, z)
        rows = []
        for k, (dy, sc) in enumerate(((0.01, 0.8), (-0.004, 1.0), (-0.016, 0.55))):
            ring = [V((0.026 * sc * math.cos(2 * math.pi * j / 12), y + dy, z + 0.026 * sc * math.sin(2 * math.pi * j / 12)))
                    for j in range(12)]
            rows.append(ring)
        bts.append(grid("btn", rows, mats=("gold",), cap0=True, cap1=True, sub=1))
    join(bts, "buttons")
    # back skirt seam (coat_shadow stripe)
    rows = []
    for i in range(10):
        z = lerp(belt - 0.05, hem + 0.09, i / 9)
        w, yf, yb, yc, nf, nb = coat_ring(z)
        y = yb * (1 + 0.032 * smooth((belt - 0.1 - z) / (belt - hem)) * math.cos(math.pi * 10 + 0.3)) + 0.004
        rows.append([V((-0.008, y, z)), V((0.008, y, z))])
    grid("coat_seam", rows, mats=("coat_shadow",), closed=False, sub=0, hint=lambda c: V((0, 1, 0)))
    return coat


def build_scarf():
    parts = []
    for k, (zc, rx, ry, th, hh, tilt, ribs) in enumerate((
            (CHIN - 0.17, 0.285, 0.235, 0.095, 0.105, 0.02, 34),
            (CHIN - 0.06, 0.232, 0.195, 0.085, 0.088, 0.065, 30))):
        Np, Nr = ribs * 3, 10
        rows = []
        for i in range(Np):
            th_ = 2 * math.pi * i / Np
            c = 0.5 + 0.5 * math.cos(th_ * ribs)
            rib = 1 - 0.065 * c ** 2
            cx, cy = rx * math.sin(th_) + 0.022 * k, -ry * math.cos(th_) + 0.02
            z0 = zc - tilt * math.cos(th_)
            out = V((math.sin(th_), -math.cos(th_) * rx / ry, 0)).normalized()
            ring = []
            for j in range(Nr):
                a = 2 * math.pi * j / Nr
                r_ = th * rib * (1 + 0.1 * max(0, math.cos(a)))
                ring.append(V((cx, cy, z0)) + out * (r_ * math.cos(a)) + V((0, 0, hh * math.sin(a) * (0.9 + 0.1 * rib))))
            rows.append(ring)
        # tube around a closed path: rows are rings around the path; wrap rows
        parts.append(grid_closed_rows("scarf_wrap_%d" % k, rows, "teal"))
    # tail on HER LEFT (+X), down the front to the belt
    belt = P["belt"]
    ztop, zbot = CHIN - 0.20, belt - 0.02
    rows = []
    R, C = 18, 13
    for i in range(R + 1):
        v = i / R
        z = lerp(ztop, zbot, v)
        xc = lerp(0.13, 0.17, v)
        hw = lerp(0.095, 0.105, v)
        ring = []
        # rectangle-ish profile with vertical rib grooves on the front face
        prof = []
        for j in range(C):
            u = j / (C - 1) * 2 - 1
            groove = 0.006 * math.cos(u * math.pi * 3.5) ** 2
            prof.append((u, -0.032 - groove))
        for j in range(C - 1, -1, -1):
            u = j / (C - 1) * 2 - 1
            prof.append((u, 0.022))
        for u, d in prof:
            x = xc + u * hw
            yf = coat_front_y(x, z) - 0.028
            if v < 0.12:
                yf -= 0.012 * (1 - v / 0.12)
            ring.append(V((x, yf + d, z)))
        rows.append(ring)
    parts.append(grid("scarf_tail", rows, mats=("teal",), cap0=True, cap1=True, sub=1))
    # fringe tassels
    tas = []
    for k in range(7):
        x = lerp(0.17 - 0.09, 0.17 + 0.09, k / 6)
        y = coat_front_y(x, zbot) - 0.04
        path = [V((x, y, zbot + 0.01)), V((x, y - 0.004, zbot - 0.04)), V((x + 0.004, y - 0.008, zbot - 0.085))]
        rows = tube_rows(path, ellipse_prof(lambda f: 0.012 * (1 - 0.6 * f), lambda f: 0.010 * (1 - 0.6 * f)), N=6,
                         up=V((0, -1, 0)), pole1=True)
        tas.append(grid("tassel", rows, mats=("teal_light",), cap0=True, sub=1))
    join(tas, "scarf_fringe")
    join(parts, "scarf")


def grid_closed_rows(name, rows, mat):
    """rows form a closed loop along the path (torus)."""
    bm = bmesh.new()
    vr = [[bm.verts.new(p) for p in r] for r in rows]
    n, m = len(vr), len(vr[0])
    for i in range(n):
        A, B = vr[i], vr[(i + 1) % n]
        for j in range(m):
            jj = (j + 1) % m
            bm.faces.new((A[j], B[j], B[jj], A[jj]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = new_obj(name, me, [mat])
    me.shade_smooth()
    add_sub(ob, 1)
    return ob


def build_arms():
    sh = P["sh"]
    ua, fa = P["arm_len"]
    for s, side in ((1, "L"), (-1, "R")):
        ang = math.radians(P["arm_ang"])
        fang = math.radians(P["farm_ang"])
        sp = V((s * P["shj"], 0.0, sh - 0.06))
        d1 = V((s * math.sin(ang), 0.02, -math.cos(ang))).normalized()
        el = sp + d1 * ua
        bend = math.radians(8)
        d2 = V((s * math.sin(fang), -math.sin(bend), -math.cos(fang))).normalized()
        wr = el + d2 * fa
        path = catmull([sp - d1 * 0.06, sp + d1 * 0.12, el, el + d2 * fa * 0.5, wr], 4)
        rad = profile_fn([(0.0, 0.11), (0.09, 0.155), (0.22, 0.128), (0.45, 0.102), (0.55, 0.100), (0.78, 0.112),
                          (0.9, 0.106), (0.92, 0.12), (1.0, 0.12)])
        F = arclen(path)
        nrows = len(path)

        def matfn(r, j, F=F):
            return 1 if F[r] >= 0.905 else 0

        rows = tube_rows(path, ellipse_prof(rad, lambda f: rad(f) * 0.95), N=20, up=V((0, -1, 0)))
        grid("sleeve_" + side, rows, mats=("coat", "rust"), matfn=matfn, cap0=True, cap1=True, capmat=1, sub=1,
             pivot=sp)
        # mitten
        dm = (d2 + V((0, 0, -0.15))).normalized()
        m0 = wr - dm * 0.03
        mlen = P["mit"]
        mp = [m0 + dm * (mlen * k / 8) for k in range(9)]
        mr = profile_fn([(0.0, 0.07), (0.25, 0.088), (0.6, 0.095), (0.85, 0.08), (1.0, 0.0)])
        palm = V((s, 0, 0))
        rows = tube_rows(mp, ellipse_prof(lambda f: mr(f) * 0.82, lambda f: mr(f) * 1.05), N=14, up=palm, pole1=True)
        rows[-1] = [mp[-1] + dm * 0.012]
        parts = [grid("mit", rows, mats=("teal",), cap0=True, sub=2)]
        # thumb: forward-inward
        tb = m0 + dm * (mlen * 0.30) + V((-s * 0.02, -0.045, 0))
        tdir = (dm * 0.85 + V((-s * 0.15, -0.30, 0))).normalized()
        tp = [tb, tb + tdir * 0.05, tb + tdir * 0.10]
        rows = tube_rows(tp, ellipse_prof(lambda f: 0.036 * (1 - 0.3 * f), lambda f: 0.034 * (1 - 0.3 * f)), N=10,
                         up=V((0, 0, 1)), pole1=True)
        rows[-1] = [tp[-1] + tdir * 0.025]
        parts.append(grid("thumb", rows, mats=("teal",), cap0=True, sub=2))
        ob = join(parts, "mitten_" + side)
        set_pivot(ob, wr)


def build_legs():
    knee, boot, crotch = P["knee"], P["boot"], P["crotch"]
    lw = P["legw"]
    for s, side in ((1, "L"), (-1, "R")):
        cx_top, cx_bot = s * 0.15, s * 0.14
        tab = [
            (crotch + 0.55, lw + 0.02, -0.16, 0.16, 0.0, 2.0, 2.0),
            (crotch, lw + 0.005, -0.155, 0.155, 0.0, 2.0, 2.0),
            (lerp(crotch, knee, 0.4), lw - 0.012, -0.135, 0.14, 0.0, 2.0, 2.0),
            (lerp(crotch, knee, 0.75), lw - 0.035, -0.11, 0.115, 0.0, 2.0, 2.0),
            (knee, 0.083, -0.09, 0.09, 0.0, 2.0, 2.0),
            (lerp(knee, boot, 0.5), P["calf"], -0.095, 0.15, 0.0, 2.0, 2.0),
            (boot, 0.104, -0.085, 0.12, 0.0, 2.0, 2.0),
            (boot - 0.25, 0.075, -0.07, 0.08, 0.0, 2.0, 2.0),
        ]
        tab = resample_table(tab, 3)
        rows = []
        top = tab[0][0]
        for (z, w, yf, yb, yc, nf, nb) in tab:
            t = (top - z) / (top - tab[-1][0])
            cx = lerp(cx_top, cx_bot, t)
            ring = []
            for j in range(24):
                x, y = se_pt(2 * math.pi * j / 24, w, yf, yb, yc, nf, nb)
                ring.append(V((cx + x, y, z)))
            rows.append(ring)
        grid("leg_" + side, rows, mats=("tights",), cap0=True, cap1=True, sub=1, pivot=V((s * 0.17, 0, crotch + 0.1)))
        # boot
        fl = P["footlen"]
        bt = [
            (boot, 0.124, -0.112, 0.14, 0.01, 2.0, 2.0),
            (lerp(boot, 0.25, 0.35), 0.112, -0.104, 0.128, 0.0, 2.0, 2.0),
            (lerp(boot, 0.25, 0.75), 0.092, -0.096, 0.100, 0.0, 2.0, 2.0),
            (0.26, 0.092, -0.110, 0.100, 0.0, 2.0, 2.0),
            (0.17, 0.104, -fl * 0.75, 0.108, 0.0, 2.3, 2.0),
            (0.09, 0.106, -fl, 0.108, 0.0, 2.4, 2.0),
            (0.04, 0.104, -fl, 0.118, 0.0, 2.4, 2.4),
            (0.015, 0.102, -fl + 0.005, 0.118, 0.0, 2.4, 2.6),
            (0.0, 0.096, -fl + 0.012, 0.112, 0.0, 2.4, 2.6),
        ]
        bt = resample_table(bt, 2)
        rows = []
        for (z, w, yf, yb, yc, nf, nb) in bt:
            ring = []
            for j in range(28):
                x, y = se_pt(2 * math.pi * j / 28, w, yf, yb, yc, nf, nb)
                ring.append(V((cx_bot + x, y, z)))
            rows.append(ring)
        grid("boot_" + side, rows, mats=("boots",), cap0=True, cap1=True, capmat=0, sub=1,
             pivot=V((cx_bot, 0, 0.1)))
        # fur cuff (knit bumps)
        rows = []
        Np = 40
        for i in range(Np):
            a = 2 * math.pi * i / Np
            rib = 1 + 0.12 * math.cos(a * 10) ** 2
            c = V((cx_bot + 0.126 * math.sin(a), 0.01 - 0.13 * math.cos(a), boot))
            out = V((math.sin(a), -math.cos(a), 0))
            ring = []
            for j in range(10):
                b = 2 * math.pi * j / 10
                ring.append(c + out * (0.042 * rib * math.cos(b)) + V((0, 0, 0.055 * math.sin(b))))
            rows.append(ring)
        grid_closed_rows("boot_cuff_" + side, rows, "fur")


# ----------------------------------------------------------------------------------------------------------------
# OPTIONAL EEVEE TOON SETUP (does not touch diffuse_color; outline modifiers are disabled by default so the
# Workbench harness is unaffected. Enable with: for o: o.modifiers["toon_outline"].show_render = True)
SHADOW_OF = dict(skin="skin_shadow", hair="hair_shadow", hair_hi="hair", teal="teal_dark", teal_light="teal",
                 coat="coat_shadow", fur="coat_shadow", hair_shadow=None, coat_shadow=None, teal_dark=None)
FLAT = {"eye_white", "iris", "iris_dark", "lash", "brow", "catchlight", "mouth", "blush", "skin_shadow"}


def lin_of(name):
    h = HEX[name]
    return [s2l(int(h[i:i + 2], 16) / 255.0) for i in (0, 2, 4)]


def build_toon():
    for name, m in list(MATS.items()):
        base = lin_of(name)
        if name in FLAT:
            sh = base
        elif SHADOW_OF.get(name):
            sh = lin_of(SHADOW_OF[name])
        else:
            sh = [c * 0.55 for c in base]
        nt = m.node_tree
        nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        dif = nt.nodes.new("ShaderNodeBsdfDiffuse")
        dif.inputs["Color"].default_value = (1, 1, 1, 1)
        s2r = nt.nodes.new("ShaderNodeShaderToRGB")
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.interpolation = "CONSTANT"
        ramp.color_ramp.elements[0].position = 0.0
        ramp.color_ramp.elements[0].color = (*sh, 1)
        ramp.color_ramp.elements[1].position = 0.14 if name in ("skin",) else 0.32
        ramp.color_ramp.elements[1].color = (*base, 1)
        emi = nt.nodes.new("ShaderNodeEmission")
        nt.links.new(dif.outputs[0], s2r.inputs[0])
        nt.links.new(s2r.outputs["Color"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], emi.inputs["Color"])
        nt.links.new(emi.outputs[0], out.inputs["Surface"])
    # outline material (inverted hull)
    om = bpy.data.materials.new("outline")
    om.diffuse_color = (*[s2l(int("20223E"[i:i + 2], 16) / 255.0) for i in (0, 2, 4)], 1.0)
    om.use_nodes = True
    om.use_backface_culling = True
    nt = om.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    emi = nt.nodes.new("ShaderNodeEmission")
    emi.inputs["Color"].default_value = (*om.diffuse_color[:3], 1)
    nt.links.new(emi.outputs[0], out.inputs["Surface"])
    skip = ("eye_white", "iris", "iris_dark", "pupil", "catchlight", "lash", "lid_low", "brow", "blush", "mouth",
            "nose_shadow", "hair_sheen", "coat_seam", "hair_cap")
    for ob in ALL:
        if ob.name in skip:
            continue
        k = len(ob.data.materials)
        ob.data.materials.append(om)
        md = ob.modifiers.new("toon_outline", "SOLIDIFY")
        md.thickness = 0.0028
        md.offset = 1.0
        md.use_flip_normals = True
        md.use_rim = False
        md.material_offset = k
        md.show_render = False
        md.show_viewport = False


# ----------------------------------------------------------------------------------------------------------------
def main():
    head = build_head()
    build_face(head)
    PT = build_hair(head)
    build_bow(PT)
    build_sheen()
    build_coat()
    build_scarf()
    build_arms()
    build_legs()
    # normalise: hair crown -> z = 1.0
    dg = bpy.context.evaluated_depsgraph_get()
    top = 0.0
    for ob in ALL:
        if ob.name.startswith(("hair_cap", "bangs")):
            ev = ob.evaluated_get(dg)
            for c in ev.bound_box:
                top = max(top, (ev.matrix_world @ V(c)).z)
    s = 1.0 / top
    S = Matrix.Scale(s, 4)
    for ob in ALL:
        ob.data.transform(S)
        ob.location = ob.location * s
        for md in ob.modifiers:
            if md.type == "SOLIDIFY":
                md.thickness *= s
    build_toon()
    hc = bpy.data.objects.new("head_center", None)
    SC.collection.objects.link(hc)
    hc.location = (0, 0, (HC + (CROWN_L + CHIN_L) / 2) * s)
    hc["head_h"] = HEAD_H * s
    hc.empty_display_size = 0.05
    dg = bpy.context.evaluated_depsgraph_get()
    tris = 0
    for ob in ALL:
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        me.calc_loop_triangles()
        tris += len(me.loop_triangles)
        ev.to_mesh_clear()
    print("R20C build=%s H=%.4f tris=%d objects=%d" % (BUILD, s, tris, len(ALL)))
    with open(os.path.join(OUT, "stats.txt"), "w") as f:
        f.write("build=%s head_h=%.5f tris=%d objects=%d\n" % (BUILD, s, tris, len(ALL)))
        for ob in sorted(ALL, key=lambda o: o.name):
            f.write(ob.name + "\n")
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "model.blend"))


main()
