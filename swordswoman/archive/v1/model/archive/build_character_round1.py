"""Akane / "Crimson Ronin" chibi character -- procedural build.

Run:
  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P model/build_character.py

Builds every mesh, material, the armature "rig", vertex weights, camera + camera-locked
lights, and saves model/character.blend.  Deterministic (no randomness, no time input).

Units: 1 Blender unit = 1 H (head height, see docs/design_bible.md section 3).
Character faces -Y (front = S iso direction).  +X is HER LEFT, -X is HER RIGHT.
Origin at the feet.
"""
import bpy, bmesh, math, json, os, sys
from mathutils import Vector, Matrix, Quaternion, Euler
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT_BLEND = os.path.join(HERE, "character.blend")
PALETTE = json.load(open(os.path.join(ROOT, "docs", "palette.json")))

V = Vector
PI = math.pi


def lerp(a, b, t):
    return a + (b - a) * t


def smoothstep(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def clamp(x, a, b):
    return max(a, min(b, x))


# ----------------------------------------------------------------------------
# scene reset
# ----------------------------------------------------------------------------
def reset_scene():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.armatures, bpy.data.cameras,
                 bpy.data.lights, bpy.data.images, bpy.data.actions):
        for d in list(coll):
            coll.remove(d)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)


# ----------------------------------------------------------------------------
# colour / materials
# ----------------------------------------------------------------------------
def srgb_to_lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hexlin(h):
    h = h.lstrip("#")
    return tuple(srgb_to_lin(int(h[i:i + 2], 16) / 255.0) for i in (0, 2, 4)) + (1.0,)


R = PALETTE["ramps"]
OUTLINE_HEX = PALETTE["outline"]
RIM_HEX = PALETTE["roles"]["rim_light"]

MATS = {}
MAT_ID = {}


def _new_mat(name):
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    return m, nt


def _aov(nt, name, value_rgb):
    a = nt.nodes.new("ShaderNodeOutputAOV")
    a.aov_name = "matid"
    a.inputs["Color"].default_value = value_rgb
    return a


def make_toon(name, colors, stops, rim=False, flat=False):
    """Cel material. colors: list of hex (dark->light). stops: thresholds (len = len(colors)-1)
    on N.L light value.  Emission output => exact palette colour on screen (Standard view)."""
    m, nt = _new_mat(name)
    idx = len(MAT_ID) + 1
    MAT_ID[name] = idx
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    emis = nt.nodes.new("ShaderNodeEmission")
    emis.inputs["Strength"].default_value = 1.0
    nt.links.new(emis.outputs[0], out.inputs["Surface"])
    if flat:
        emis.inputs["Color"].default_value = hexlin(colors[0])
        col_socket = None
    else:
        dif = nt.nodes.new("ShaderNodeBsdfDiffuse")
        dif.inputs["Color"].default_value = (1, 1, 1, 1)
        s2r = nt.nodes.new("ShaderNodeShaderToRGB")
        nt.links.new(dif.outputs[0], s2r.inputs[0])
        bw = nt.nodes.new("ShaderNodeRGBToBW")
        nt.links.new(s2r.outputs["Color"], bw.inputs[0])
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.interpolation = "CONSTANT"
        els = ramp.color_ramp.elements
        els[0].position = 0.0
        els[0].color = hexlin(colors[0])
        els[1].position = stops[0]
        els[1].color = hexlin(colors[1])
        for i in range(2, len(colors)):
            e = els.new(stops[i - 1])
            e.color = hexlin(colors[i])
        nt.links.new(bw.outputs[0], ramp.inputs["Fac"])
        col_socket = ramp.outputs["Color"]
        if rim:
            # camera-locked rim: grazing normal AND normal pointing screen-right (away from key)
            geo = nt.nodes.new("ShaderNodeNewGeometry")
            vt = nt.nodes.new("ShaderNodeVectorTransform")
            vt.vector_type = "NORMAL"
            vt.convert_from = "WORLD"
            vt.convert_to = "CAMERA"
            nt.links.new(geo.outputs["Normal"], vt.inputs[0])
            sep = nt.nodes.new("ShaderNodeSeparateXYZ")
            nt.links.new(vt.outputs[0], sep.inputs[0])
            lw = nt.nodes.new("ShaderNodeLayerWeight")
            lw.inputs["Blend"].default_value = 0.5
            g1 = nt.nodes.new("ShaderNodeMath"); g1.operation = "GREATER_THAN"
            g1.inputs[1].default_value = 0.78
            nt.links.new(lw.outputs["Facing"], g1.inputs[0])
            g2 = nt.nodes.new("ShaderNodeMath"); g2.operation = "GREATER_THAN"
            g2.inputs[1].default_value = 0.45
            nt.links.new(sep.outputs["X"], g2.inputs[0])
            mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
            nt.links.new(g1.outputs[0], mul.inputs[0])
            nt.links.new(g2.outputs[0], mul.inputs[1])
            mix = nt.nodes.new("ShaderNodeMix")
            mix.data_type = "RGBA"
            nt.links.new(mul.outputs[0], mix.inputs["Factor"])
            # inputs by identifier are safer for the Mix node
            for s in mix.inputs:
                if s.identifier == "A_Color":
                    nt.links.new(col_socket, s)
                if s.identifier == "B_Color":
                    s.default_value = hexlin(RIM_HEX)
            for s in mix.outputs:
                if s.identifier == "Result_Color":
                    col_socket = s
        nt.links.new(col_socket, emis.inputs["Color"])
    # material-id AOV (for per-material quantisation in the sprite pipeline)
    _aov(nt, "matid", ((idx % 8) / 8.0, ((idx // 8) % 8) / 8.0, idx / 64.0, 1.0))
    m["palette_ramp"] = ",".join(colors)
    m["mat_id"] = idx
    MATS[name] = m
    return m


def make_outline_mat():
    m, nt = _new_mat("M_outline")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    emis = nt.nodes.new("ShaderNodeEmission")
    emis.inputs["Color"].default_value = hexlin(OUTLINE_HEX)
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    lp = nt.nodes.new("ShaderNodeLightPath")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lp.outputs["Is Shadow Ray"], mix.inputs[0])
    nt.links.new(emis.outputs[0], mix.inputs[1])
    nt.links.new(tr.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    m.use_backface_culling = True
    for attr in ("use_backface_culling_shadow",):
        if hasattr(m, attr):
            setattr(m, attr, True)
    if hasattr(m, "use_transparent_shadow"):
        m.use_transparent_shadow = True
    MAT_ID["M_outline"] = 0
    _aov(nt, "matid", (0, 0, 0, 1))
    m["palette_ramp"] = OUTLINE_HEX
    MATS["M_outline"] = m
    return m


def build_materials():
    make_toon("M_skin", R["skin"], (0.16, 0.90))
    make_toon("M_hair", R["hair"], (0.32, 0.965), rim=True)
    make_toon("M_red", R["red"][1:], (0.26, 0.90))                 # crimson / base / coral
    make_toon("M_red_rim", R["red"][1:], (0.26, 0.90), rim=True)   # bow + sleeves
    make_toon("M_red_under", R["red"][:2], (0.35,))               # violet / crimson (undersides)
    make_toon("M_red_inner", R["red"][1:3], (0.15,))              # collar inner face (lighter)
    make_toon("M_leather", R["leather"], (0.18, 0.86))
    make_toon("M_dark", R["dark"], (0.25,))
    make_toon("M_steel", R["steel"], (0.3, 0.92))
    make_toon("M_pink", R["roles"] if False else PALETTE["roles"]["scarf"], (0.2, 0.85))
    make_toon("M_purple", R["purple"], (), flat=True)
    # flat decals (face)
    make_toon("M_eye_dark", [R["eye"][0]], (), flat=True)
    make_toon("M_eye_light", [R["eye"][1]], (), flat=True)
    make_toon("M_ink", [OUTLINE_HEX], (), flat=True)
    make_toon("M_glint", [R["steel"][2]], (), flat=True)
    make_toon("M_blush", [R["pink"][0]], (), flat=True)
    make_toon("M_mouth", [R["skin"][0]], (), flat=True)
    make_toon("M_red_flat", [R["red"][2]], (), flat=True)   # tsuka diamonds
    make_outline_mat()


# ----------------------------------------------------------------------------
# mesh building helpers
# ----------------------------------------------------------------------------
class MB:
    """Mesh builder: accumulate verts / faces / material names."""

    def __init__(self):
        self.v = []
        self.f = []
        self.m = []
        self.smooth = []
        self.tags = []  # per-vertex user tag (for weighting)

    def add_vert(self, p, tag=None):
        self.v.append(V(p))
        self.tags.append(tag)
        return len(self.v) - 1

    def add_face(self, idx, mat, smooth=True):
        self.f.append(tuple(idx))
        self.m.append(mat)
        self.smooth.append(smooth)

    def grid(self, rows, mat, close_u=False, smooth=True, tags=None, flip=False):
        """rows: list (v) of lists (u) of points. Returns index grid."""
        ids = []
        for j, row in enumerate(rows):
            r = []
            for i, p in enumerate(row):
                r.append(self.add_vert(p, tags[j][i] if tags else (j, i)))
            ids.append(r)
        nu = len(rows[0])
        for j in range(len(rows) - 1):
            for i in range(nu if close_u else nu - 1):
                a = ids[j][i]
                b = ids[j][(i + 1) % nu]
                c = ids[j + 1][(i + 1) % nu]
                d = ids[j + 1][i]
                q = (a, b, c, d) if not flip else (a, d, c, b)
                self.add_face(q, mat, smooth)
        return ids

    def cap(self, ring_ids, center, mat, flip=False, smooth=True):
        c = self.add_vert(center)
        n = len(ring_ids)
        for i in range(n):
            a, b = ring_ids[i], ring_ids[(i + 1) % n]
            self.add_face((a, b, c) if not flip else (b, a, c), mat, smooth)
        return c

    def build(self, name, coll=None):
        me = bpy.data.meshes.new(name)
        me.from_pydata([tuple(p) for p in self.v], [], self.f)
        me.validate(clean_customdata=False)
        mats = []
        for mn in self.m:
            if mn not in mats:
                mats.append(mn)
        for mn in mats:
            me.materials.append(MATS[mn])
        me.polygons.foreach_set("material_index", [mats.index(mn) for mn in self.m])
        me.polygons.foreach_set("use_smooth", self.smooth)
        me.update()
        ob = bpy.data.objects.new(name, me)
        (coll or bpy.context.scene.collection).objects.link(ob)
        ob["tags"] = 0
        ob["_mb_tags"] = json.dumps(self.tags) if False else ""
        return ob


def catmull(points, samples):
    """Catmull-Rom through points, returns `samples` points (inclusive ends)."""
    P = [V(p) for p in points]
    if len(P) == 2:
        return [P[0].lerp(P[1], i / (samples - 1)) for i in range(samples)]
    ext = [P[0] * 2 - P[1]] + P + [P[-1] * 2 - P[-2]]
    segs = len(P) - 1
    out = []
    for k in range(samples):
        t = k / (samples - 1) * segs
        i = min(int(t), segs - 1)
        u = t - i
        p0, p1, p2, p3 = ext[i], ext[i + 1], ext[i + 2], ext[i + 3]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u
                          + (-p0 + 3 * p1 - 3 * p2 + p3) * u * u * u))
    return out


def frames_along(path, up=V((0, 0, 1))):
    """Parallel-transport frames (T, N, B) along a polyline."""
    T = []
    n = len(path)
    for i in range(n):
        a = path[max(0, i - 1)]
        b = path[min(n - 1, i + 1)]
        T.append((b - a).normalized())
    N0 = up - T[0] * up.dot(T[0])
    if N0.length < 1e-4:
        N0 = V((1, 0, 0)) - T[0] * T[0].x
    N0.normalize()
    Ns = [N0]
    for i in range(1, n):
        q = T[i - 1].rotation_difference(T[i])
        Nn = q @ Ns[-1]
        Nn = (Nn - T[i] * Nn.dot(T[i])).normalized()
        Ns.append(Nn)
    Bs = [T[i].cross(Ns[i]).normalized() for i in range(n)]
    return T, Ns, Bs


def tube(mb, path, radius_fn, mat, nseg=16, cap0=True, cap1=True, up=V((0, 0, 1)),
         smooth=True, mat_fn=None, phase=0.0):
    """radius_fn(t, phi) -> (rN, rB) or float.  mat_fn(t) -> material name (optional)."""
    T, N, B = frames_along(path, up)
    n = len(path)
    rows = []
    for i in range(n):
        t = i / (n - 1)
        row = []
        for k in range(nseg):
            phi = 2 * PI * k / nseg + phase
            r = radius_fn(t, phi)
            if not isinstance(r, tuple):
                r = (r, r)
            row.append(path[i] + N[i] * (math.cos(phi) * r[0]) + B[i] * (math.sin(phi) * r[1]))
        rows.append(row)
    ids = []
    for row in rows:
        ids.append([mb.add_vert(p) for p in row])
    for i in range(n - 1):
        mname = mat_fn((i + 0.5) / (n - 1)) if mat_fn else mat
        for k in range(nseg):
            a, b = ids[i][k], ids[i][(k + 1) % nseg]
            c, d = ids[i + 1][(k + 1) % nseg], ids[i + 1][k]
            mb.add_face((a, b, c, d), mname, smooth)
    if cap0:
        mb.cap(ids[0], path[0], mat_fn(0) if mat_fn else mat, flip=True, smooth=smooth)
    if cap1:
        mb.cap(ids[-1], path[-1], mat_fn(1) if mat_fn else mat, flip=False, smooth=smooth)
    return ids


def ellipsoid(mb, center, radii, mat, nu=24, nv=14, rot=None, deform=None, smooth=True):
    """UV ellipsoid. rot: Matrix(3x3). deform(p_local)->p_local optional."""
    c = V(center)
    rot = rot or Matrix.Identity(3)
    rows = []
    for j in range(1, nv):
        th = PI * j / nv  # 0 top .. pi bottom
        row = []
        for i in range(nu):
            ph = 2 * PI * i / nu
            p = V((math.sin(th) * math.sin(ph) * radii[0],
                   -math.sin(th) * math.cos(ph) * radii[1],
                   math.cos(th) * radii[2]))
            if deform:
                p = deform(p)
            row.append(c + rot @ p)
        rows.append(row)
    ids = mb.grid(rows, mat, close_u=True, smooth=smooth, flip=True)
    top = V((0, 0, radii[2]))
    bot = V((0, 0, -radii[2]))
    if deform:
        top, bot = deform(top), deform(bot)
    mb.cap(ids[0], c + rot @ top, mat, flip=False, smooth=smooth)
    mb.cap(ids[-1], c + rot @ bot, mat, flip=True, smooth=smooth)
    return ids


def box(mb, center, size, mat, rot=None, smooth=False):
    c = V(center)
    rot = rot or Matrix.Identity(3)
    sx, sy, sz = [s / 2 for s in size]
    pts = [V((x, y, z)) for z in (-sz, sz) for y in (-sy, sy) for x in (-sx, sx)]
    ids = [mb.add_vert(c + rot @ p) for p in pts]
    F = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    for f in F:
        mb.add_face([ids[i] for i in f], mat, smooth)


def look_rot(fwd, up=V((0, 0, 1))):
    """3x3 with local Y = fwd, local Z ~ up."""
    y = V(fwd).normalized()
    x = y.cross(up)
    if x.length < 1e-5:
        x = V((1, 0, 0))
    x.normalize()
    z = x.cross(y).normalized()
    return Matrix((x, y, z)).transposed()


# ----------------------------------------------------------------------------
# skeleton definition (rest = relaxed A-pose)
# ----------------------------------------------------------------------------
def arm_points(side):
    s = 1 if side == "L" else -1
    sh_in = V((0.06 * s, 0.0, 1.66))
    sj = V((0.25 * s, 0.0, 1.62))
    u = V((0.42 * s, -0.05, -0.905)).normalized()
    el = sj + u * 0.36
    u2 = V((0.38 * s, -0.15, -0.91)).normalized()
    wr = el + u2 * 0.36
    u3 = V((0.30 * s, -0.15, -0.94)).normalized()
    ht = wr + u3 * 0.20
    return sh_in, sj, el, wr, ht


def leg_points(side):
    s = 1 if side == "L" else -1
    hip = V((0.13 * s, 0.0, 0.95))
    kn = V((0.14 * s, -0.025, 0.52))
    an = V((0.14 * s, 0.035, 0.21))
    toe = V((0.14 * s, -0.16, 0.035))
    return hip, kn, an, toe


BONES = {}   # name -> dict(head, tail, parent, roll_vec, deform)


def bone(name, head, tail, parent=None, roll=None, deform=True, connect=False):
    BONES[name] = dict(head=V(head), tail=V(tail), parent=parent, roll=roll, deform=deform,
                       connect=connect)


SWORD_DIR = V((0.80, 0.25, -0.55)).normalized()   # idle: blade down, back, out (her left)
GUARD_Y = 0.10          # sword local: guard plane along +Y from grip
BLADE_LEN = 1.45
HANDLE_LEN = 0.45
SHEATH_HEAD = V((0.27, -0.30, 1.02))
SHEATH_DIR = V((0.10, 0.94, -0.33)).normalized()


def define_skeleton():
    BONES.clear()
    bone("root", (0, 0, 0), (0, 0.45, 0), None, deform=False)
    bone("hips", (0, 0, 0.92), (0, 0, 1.12), "root")
    bone("spine", (0, 0, 1.12), (0, 0, 1.38), "hips", connect=True)
    bone("chest", (0, 0, 1.38), (0, 0, 1.72), "spine", connect=True)
    bone("neck", (0, 0, 1.72), (0, 0, 1.88), "chest", connect=True)
    bone("head", (0, 0, 1.88), (0, 0, 2.75), "neck", connect=True)
    bone("bun", (0, 0.16, 2.70), (0, 0.30, 3.05), "head")
    bone("bow", (-0.05, 0.10, 2.90), (-0.05, 0.10, 3.15), "bun")
    for side in ("L", "R"):
        s = 1 if side == "L" else -1
        sh_in, sj, el, wr, ht = arm_points(side)
        bone(f"shoulder.{side}", sh_in, sj, "chest")
        bone(f"upper_arm.{side}", sj, el, f"shoulder.{side}", connect=True)
        bone(f"forearm.{side}", el, wr, f"upper_arm.{side}", connect=True)
        bone(f"hand.{side}", wr, ht, f"forearm.{side}", connect=True)
        # sleeve cuff tip: from wrist to lowest cuff point (hangs down and back)
        bone(f"sleeve.{side}", wr + V((0, 0.02, 0)), wr + V((0.05 * s, 0.10, -0.30)), f"forearm.{side}")
        hip, kn, an, toe = leg_points(side)
        bone(f"thigh.{side}", hip, kn, "hips")
        bone(f"shin.{side}", kn, an, f"thigh.{side}", connect=True)
        bone(f"foot.{side}", an, toe, f"shin.{side}", connect=True)
        # scarf chains from the back of the collar
        p = [V((0.09 * s, 0.22, 1.93)), V((0.15 * s, 0.36, 1.66)), V((0.19 * s, 0.44, 1.38)),
             V((0.21 * s, 0.50, 1.08))]
        par = "neck"
        for i in range(3):
            nm = f"scarf.{side}.{i + 1:03d}"
            bone(nm, p[i], p[i + 1], par, connect=(i > 0))
            par = nm
    # skirt
    bone("skirt.F", (0, -0.20, 1.04), (0, -0.40, 0.62), "hips")
    bone("skirt.B", (0, 0.20, 1.04), (0, 0.42, 0.68), "hips")
    bone("skirt.L", (0.27, 0, 1.04), (0.55, 0.03, 0.48), "hips")
    bone("skirt.R", (-0.27, 0, 1.04), (-0.55, 0.03, 0.48), "hips")
    bone("skirt.tail.001", (0, 0.42, 0.68), (0, 0.55, 0.48), "skirt.B", connect=True)
    bone("skirt.tail.002", (0, 0.55, 0.48), (0, 0.64, 0.32), "skirt.tail.001", connect=True)
    bone("skirt.tail.003", (0, 0.64, 0.32), (0, 0.70, 0.18), "skirt.tail.002", connect=True)
    # sword: head at the left-hand grip, Y along the blade, Z = edge direction
    sh_in, sj, el, wr, ht = arm_points("L")
    grip = wr.lerp(ht, 0.5)
    edge = V((0, 0, -1)) - SWORD_DIR * V((0, 0, -1)).dot(SWORD_DIR)
    bone("sword", grip, grip + SWORD_DIR * (GUARD_Y + BLADE_LEN), "hand.L", roll=edge.normalized(),
         deform=True)
    # alternative sword parents (Copy Transforms targets, influence 0 by default)
    edge_s = V((0, 0, 1)) - SHEATH_DIR * V((0, 0, 1)).dot(SHEATH_DIR)
    bone("sheath", SHEATH_HEAD, SHEATH_HEAD + SHEATH_DIR * (GUARD_Y + BLADE_LEN), "hips",
         roll=edge_s.normalized(), deform=True)
    sh_in, sj, el, wr, ht = arm_points("R")
    g_r = wr.lerp(ht, 0.5)
    sdr = V((-0.36, 0.78, -0.52)).normalized()
    bone("sword_grip.R", g_r, g_r + sdr * 0.5, "hand.R", roll=V((0, 0, -1)), deform=False)


def build_rig():
    arm = bpy.data.armatures.new("rig")
    ob = bpy.data.objects.new("rig", arm)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm.edit_bones
    for name, d in BONES.items():
        b = eb.new(name)
        b.head = d["head"]
        b.tail = d["tail"]
        if d["roll"] is not None:
            b.align_roll(d["roll"])
        else:
            # deterministic default roll: Z axis toward -Y (front) or +Z for horizontal bones
            ax = (d["tail"] - d["head"]).normalized()
            ref = V((0, -1, 0)) if abs(ax.y) < 0.9 else V((0, 0, 1))
            b.align_roll(ref)
        b.use_deform = d["deform"]
    for name, d in BONES.items():
        if d["parent"]:
            eb[name].parent = eb[d["parent"]]
            eb[name].use_connect = d["connect"]
    bpy.ops.object.mode_set(mode="OBJECT")
    arm.display_type = "STICK"
    # sword parent switching
    pb = ob.pose.bones["sword"]
    c = pb.constraints.new("COPY_TRANSFORMS")
    c.name = "to_sheath"
    c.target = ob
    c.subtarget = "sheath"
    c.influence = 0.0
    c = pb.constraints.new("COPY_TRANSFORMS")
    c.name = "to_hand.R"
    c.target = ob
    c.subtarget = "sword_grip.R"
    c.influence = 0.0
    ob["sword_mode"] = "hand.L (default). Set constraint 'to_sheath' or 'to_hand.R' influence=1 to switch."
    return ob


# ----------------------------------------------------------------------------
# weighting
# ----------------------------------------------------------------------------
def seg_dist(p, a, b):
    ab = b - a
    t = clamp((p - a).dot(ab) / max(ab.length_squared, 1e-9), 0, 1)
    return (p - (a + ab * t)).length, t


def weight_rigid(ob, bname):
    vg = ob.vertex_groups.new(name=bname)
    vg.add(list(range(len(ob.data.vertices))), 1.0, "REPLACE")


def weight_distance(ob, bones, power=6.0, keep=3, bias=None):
    vgs = {b: ob.vertex_groups.new(name=b) for b in bones}
    for v in ob.data.vertices:
        p = v.co
        ws = []
        for b in bones:
            d, _ = seg_dist(p, BONES[b]["head"], BONES[b]["tail"])
            w = 1.0 / (d + 0.03) ** power
            if bias and b in bias:
                w *= bias[b]
            ws.append((w, b))
        ws.sort(reverse=True)
        ws = ws[:keep]
        tot = sum(w for w, _ in ws)
        for w, b in ws:
            if w / tot > 0.01:
                vgs[b].add([v.index], w / tot, "REPLACE")


def weight_custom(ob, fn):
    """fn(co) -> dict bone->weight"""
    groups = {}
    for v in ob.data.vertices:
        d = fn(V(v.co))
        tot = sum(d.values())
        if tot <= 0:
            continue
        for b, w in d.items():
            if w / tot < 0.01:
                continue
            if b not in groups:
                groups[b] = ob.vertex_groups.new(name=b)
            groups[b].add([v.index], w / tot, "REPLACE")


# ----------------------------------------------------------------------------
# modifiers / finishing
# ----------------------------------------------------------------------------
def finish(ob, rig, subsurf=1, thick=0.0, thick_offset=-1.0, shell_mat_offset=0, outline_px=1.5,
           outline=True):
    ob.parent = rig
    m = ob.modifiers.new("Armature", "ARMATURE")
    m.object = rig
    if subsurf:
        s = ob.modifiers.new("Subsurf", "SUBSURF")
        s.levels = subsurf
        s.render_levels = subsurf
    if thick:
        s = ob.modifiers.new("Thickness", "SOLIDIFY")
        s.thickness = thick
        s.offset = thick_offset
        s.use_even_offset = False
        s.use_quality_normals = True
        s.material_offset = shell_mat_offset
    if outline:
        ob.data.materials.append(MATS["M_outline"])
        s = ob.modifiers.new("Outline", "SOLIDIFY")
        s.thickness = 0.012
        s.offset = 1.0
        s.use_flip_normals = True
        s.use_rim = False
        s.use_even_offset = False
        s.use_quality_normals = True
        s.material_offset = 999
        ob["outline_px"] = outline_px
    return ob


# ----------------------------------------------------------------------------
# BODY
# ----------------------------------------------------------------------------
HEAD_C = V((0, 0, 2.27))
HEAD_R = V((0.47, 0.44, 0.48))


def head_deform(p):
    # p local to head centre. chibi chin taper + soft cheeks
    if p.z < 0:
        k = clamp(-p.z / HEAD_R.z, 0, 1)
        fx = 1 - 0.34 * k ** 2.2
        fy = 1 - 0.16 * k ** 2
        q = V((p.x * fx, p.y * fy, p.z))
        q.y -= 0.03 * k ** 3  # chin slightly forward
        return q
    return V(p)


def torso_profile(z):
    """returns (rx, ry, yoff) of the body cross-section at height z."""
    keys = [  # z, rx, ry, yoff
        (0.84, 0.05, 0.05, 0.0),
        (0.90, 0.22, 0.16, 0.0),
        (1.00, 0.265, 0.185, 0.0),
        (1.14, 0.245, 0.170, -0.005),
        (1.28, 0.205, 0.150, -0.01),
        (1.42, 0.220, 0.165, -0.02),
        (1.54, 0.245, 0.165, -0.015),
        (1.60, 0.235, 0.145, 0.0),
        (1.66, 0.185, 0.125, 0.0),
        (1.71, 0.13, 0.105, 0.0),
        (1.76, 0.10, 0.095, 0.0),
    ]
    if z <= keys[0][0]:
        return keys[0][1:]
    for i in range(len(keys) - 1):
        a, b = keys[i], keys[i + 1]
        if a[0] <= z <= b[0]:
            t = (z - a[0]) / (b[0] - a[0])
            t = t * t * (3 - 2 * t)
            return tuple(lerp(a[j], b[j], t) for j in (1, 2, 3))
    return keys[-1][1:]


def body_pt(theta, z, off=0.0):
    rx, ry, yo = torso_profile(z)
    return V((math.sin(theta) * (rx + off), -math.cos(theta) * (ry + off) + yo, z))


def build_body(rig, coll):
    objs = []
    # torso
    mb = MB()
    nu = 28
    zs = [0.84 + (1.80 - 0.84) * j / 22 for j in range(23)]
    rows = [[body_pt(2 * PI * i / nu, z) for i in range(nu)] for z in zs]
    ids = mb.grid(rows, "M_skin", close_u=True)
    mb.cap(ids[0], V((0, 0, 0.82)), "M_skin", flip=True)
    # neck tube continues
    ob = mb.build("body_torso", coll)
    finish(ob, rig, subsurf=2, outline_px=1.2)
    weight_distance(ob, ["hips", "spine", "chest", "neck", "shoulder.L", "shoulder.R"], power=4)
    objs.append(ob)

    # neck
    mb = MB()
    path = [V((0, 0.01, 1.70)), V((0, 0.0, 1.85)), V((0, -0.01, 2.0))]
    tube(mb, path, lambda t, ph: (0.085, 0.08), "M_skin", nseg=14, cap0=False, cap1=False)
    ob = mb.build("neck", coll)
    finish(ob, rig, subsurf=1, outline=False)
    weight_distance(ob, ["chest", "neck", "head"], power=4)

    # head
    mb = MB()
    ellipsoid(mb, HEAD_C, HEAD_R, "M_skin", nu=40, nv=28, deform=head_deform)
    ob = mb.build("head", coll)
    finish(ob, rig, subsurf=2, outline_px=1.5)
    weight_rigid(ob, "head")
    head_ob = ob
    # ears
    mb = MB()
    for s in (1, -1):
        ellipsoid(mb, (0.445 * s, 0.03, 2.13), (0.035, 0.07, 0.09), "M_skin", nu=12, nv=8,
                  rot=Euler((0, 0.25 * s, 0)).to_matrix())
    ob = mb.build("ears", coll)
    finish(ob, rig, subsurf=1, outline_px=1.0)
    weight_rigid(ob, "head")

    # arms (bare skin; the detached sleeves cover the forearm)
    for side in ("L", "R"):
        sh_in, sj, el, wr, ht = arm_points(side)
        mb = MB()
        path = catmull([sj + (sj - el).normalized() * 0.06, sj, el, wr], 14)
        rad = lambda t, ph: lerp(0.105, 0.058, smoothstep(0.0, 1.0, t)) * (1 + 0.08 * math.sin(PI * t))
        tube(mb, path, rad, "M_skin", nseg=14)
        # rounded deltoid cap so the bare shoulder reads soft, not boxy
        ellipsoid(mb, sj + V((-0.015 * (1 if side == "L" else -1), 0, 0.0)), (0.105, 0.095, 0.095), "M_skin",
                  nu=16, nv=10)
        ob = mb.build(f"arm.{side}", coll)
        finish(ob, rig, subsurf=2, outline_px=1.2)
        weight_distance(ob, [f"shoulder.{side}", f"upper_arm.{side}", f"forearm.{side}", "chest"],
                        power=5, bias={"chest": 0.3})
        # hand: mitten in fingerless glove, skin fingertips
        mb = MB()
        hdir = (ht - wr).normalized()
        s = 1 if side == "L" else -1
        path = catmull([wr - hdir * 0.02, wr + hdir * 0.08, wr + hdir * 0.17, wr + hdir * 0.22], 10)
        def hr(t, ph):
            w = 0.05 + 0.012 * math.sin(PI * min(1, t * 1.2))
            if t > 0.85:
                w *= math.sqrt(max(0.0, 1 - ((t - 0.85) / 0.15) ** 2)) * 0.9 + 0.1
            return (w * 1.05, w * 0.62)
        tube(mb, path, hr, "M_dark", nseg=12, up=V((0, -1, 0)),
             mat_fn=lambda t: "M_skin" if t > 0.66 else "M_dark")
        # thumb
        tpos = wr + hdir * 0.08 + V((0, -0.045, 0))
        ellipsoid(mb, tpos, (0.022, 0.022, 0.05), "M_skin", nu=8, nv=6,
                  rot=look_rot(V((0.2 * s, -0.6, -0.8)), V((0, 0, 1))) @ Euler((PI / 2, 0, 0)).to_matrix())
        ob = mb.build(f"hand.{side}", coll)
        finish(ob, rig, subsurf=1, outline_px=1.0)
        weight_distance(ob, [f"hand.{side}", f"forearm.{side}"], power=6, bias={f"forearm.{side}": 0.2})

    # legs
    for side in ("L", "R"):
        hip, kn, an, toe = leg_points(side)
        s = 1 if side == "L" else -1
        mb = MB()
        top = hip + V((-0.03 * s, 0, 0.12))
        path = catmull([top, hip, kn, an, an + V((0, 0.0, -0.06))], 22)
        def lr(t, ph, s=s):
            # thigh 0.30 -> knee 0.20 -> ankle 0.13 widths (radius = half)
            z = lerp(1.07, 0.15, t)
            if z > 0.52:
                r = lerp(0.10, 0.155, smoothstep(0.52, 0.95, z))
                # calf / thigh soft bulge on the outside
            else:
                r = lerp(0.065, 0.10, smoothstep(0.24, 0.52, z))
                r *= 1 + 0.10 * math.exp(-((z - 0.40) / 0.07) ** 2)  # calf
            return (r, r * 0.95)
        tube(mb, path, lr, "M_skin", nseg=16, cap0=False)
        ob = mb.build(f"leg.{side}", coll)
        finish(ob, rig, subsurf=2, outline_px=1.2)
        weight_distance(ob, ["hips", f"thigh.{side}", f"shin.{side}", f"foot.{side}"], power=5,
                        bias={"hips": 0.6})
        # foot (skin) inside the sandal
        mb = MB()
        heel = V((0.14 * s, 0.07, 0.17))
        ball = V((0.14 * s, -0.12, 0.035))
        tip = V((0.14 * s, -0.20, 0.03))
        path = catmull([heel + V((0, 0.02, 0.01)), heel, an.lerp(ball, 0.5) + V((0, 0, 0.0)), ball, tip], 12)
        def fr(t, ph):
            w = lerp(0.055, 0.06, t) * (1 - 0.6 * smoothstep(0.85, 1.0, t))
            h = lerp(0.05, 0.03, t) * (1 - 0.6 * smoothstep(0.85, 1.0, t))
            return (h, w)
        tube(mb, path, fr, "M_skin", nseg=12, up=V((0, 0, 1)))
        ob = mb.build(f"foot.{side}", coll)
        finish(ob, rig, subsurf=1, outline_px=1.0)
        weight_distance(ob, [f"foot.{side}", f"shin.{side}"], power=6, bias={f"shin.{side}": 0.3})
    return head_ob


# ----------------------------------------------------------------------------
# FACE decals (projected onto the evaluated head surface)
# ----------------------------------------------------------------------------
def build_face(rig, coll, head_ob):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = head_ob.evaluated_get(dg)
    me = ev.to_mesh()
    bvh = BVHTree.FromPolygons([ev.matrix_world @ v.co for v in me.vertices],
                               [tuple(p.vertices) for p in me.polygons])
    ev.to_mesh_clear()

    def proj(x, z, off):
        hit = bvh.ray_cast(V((x, -2.0, z)), V((0, 1, 0)))
        if hit[0] is None:
            return V((x, -0.3, z))
        p, n = hit[0], hit[1].normalized()
        if n.y > 0:
            n = -n
        return p + n * off

    mb = MB()

    def ellipse(cx, cz, rx, rz, off, mat, rot=0.0, n=20, rings=4, clip=None):
        # polar grid; clip(x,z)->bool keeps only some (approx via squash)
        cr, sr = math.cos(rot), math.sin(rot)
        center = mb.add_vert(proj(cx, cz, off))
        prev = None
        for k in range(1, rings + 1):
            f = k / rings
            ring = []
            for i in range(n):
                a = 2 * PI * i / n
                lx, lz = math.cos(a) * rx * f, math.sin(a) * rz * f
                x = cx + lx * cr - lz * sr
                z = cz + lx * sr + lz * cr
                ring.append(mb.add_vert(proj(x, z, off)))
            if prev is None:
                for i in range(n):
                    mb.add_face((center, ring[i], ring[(i + 1) % n]), mat)
            else:
                for i in range(n):
                    mb.add_face((prev[i], ring[i], ring[(i + 1) % n], prev[(i + 1) % n]), mat)
            prev = ring

    def band(pts_a, pts_b, off, mat):
        A = [mb.add_vert(proj(x, z, off)) for x, z in pts_a]
        B = [mb.add_vert(proj(x, z, off)) for x, z in pts_b]
        for i in range(len(A) - 1):
            mb.add_face((A[i], A[i + 1], B[i + 1], B[i]), mat)

    EYE_Z = 2.20
    for s in (1, -1):   # s=+1 her left (screen right in front view)
        cx = 0.205 * s
        # sclera (light), iris dark, iris light lower, pupil, glints
        ellipse(cx, EYE_Z - 0.005, 0.105, 0.125, 0.004, "M_glint", n=24)
        ellipse(cx + 0.005 * s, EYE_Z - 0.01, 0.082, 0.118, 0.008, "M_eye_dark", n=24)
        ellipse(cx + 0.005 * s, EYE_Z - 0.045, 0.066, 0.075, 0.011, "M_eye_light", n=20)
        ellipse(cx + 0.005 * s, EYE_Z + 0.005, 0.034, 0.05, 0.014, "M_ink", n=16)
        ellipse(cx - 0.025 * s, EYE_Z + 0.045, 0.022, 0.026, 0.018, "M_glint", n=12)
        ellipse(cx + 0.035 * s, EYE_Z - 0.06, 0.011, 0.011, 0.018, "M_glint", n=8)
        # upper lash: thick arc, heavier at the outer corner, half-lidded (covers top of eye)
        N = 14
        A, B = [], []
        for i in range(N + 1):
            u = i / N            # 0 inner -> 1 outer
            x = cx + s * lerp(-0.11, 0.125, u)
            ztop = EYE_Z + 0.085 + 0.05 * math.sin(PI * lerp(0.1, 0.95, u)) - 0.03 * u
            th = lerp(0.022, 0.05, u ** 1.5)
            A.append((x, ztop + 0.012))
            B.append((x, ztop - th - 0.03 * math.sin(PI * u) * 0.5))
        band(A, B, 0.022, "M_ink")
        # lash flick at the outer corner
        band([(cx + s * 0.11, EYE_Z + 0.06), (cx + s * 0.15, EYE_Z + 0.085)],
             [(cx + s * 0.115, EYE_Z + 0.02), (cx + s * 0.155, EYE_Z + 0.07)], 0.022, "M_ink")
        # small lower lash mark (outer)
        band([(cx + s * 0.04, EYE_Z - 0.128), (cx + s * 0.095, EYE_Z - 0.105)],
             [(cx + s * 0.04, EYE_Z - 0.14), (cx + s * 0.1, EYE_Z - 0.115)], 0.012, "M_ink")
        # blush
        ellipse(0.30 * s, 2.04, 0.075, 0.032, 0.006, "M_blush", n=16, rings=2)
    # mouth (small) and tiny nose
    band([(-0.03, 1.965), (0.0, 1.958), (0.03, 1.965)], [(-0.03, 1.952), (0.0, 1.945), (0.03, 1.952)],
         0.006, "M_mouth")
    ellipse(0.0, 2.06, 0.01, 0.007, 0.005, "M_mouth", n=8, rings=1)
    ob = mb.build("face_decals", coll)
    finish(ob, rig, subsurf=0, outline=False)
    weight_rigid(ob, "head")
    ob.visible_shadow = False
    return ob


# ----------------------------------------------------------------------------
# HAIR
# ----------------------------------------------------------------------------
def head_surf(phi, z, out=0.0, Rs=None, C=None):
    """Point on the head-ish ellipsoid at azimuth phi (0=front,-Y; +pi/2 = +X) & height z,
    pushed outwards by `out`."""
    C = C or HEAD_C
    Rr = Rs or HEAD_R
    sz = clamp((z - C.z) / Rr.z, -0.999, 0.999)
    ce = math.sqrt(1 - sz * sz)
    p = V((Rr.x * ce * math.sin(phi), -Rr.y * ce * math.cos(phi), Rr.z * sz))
    p = head_deform(p)
    h = V((p.x, p.y, 0))
    n = V((p.x / Rr.x ** 2, p.y / Rr.y ** 2, p.z / Rr.z ** 2)).normalized()
    return C + p + n * out


def build_hair(rig, coll):
    # skull cap
    mb = MB()
    C = HEAD_C + V((0, 0.025, 0.02))
    Rr = V((0.505, 0.485, 0.505))
    nu, nv = 48, 30
    verts = {}
    rows = []
    for j in range(0, nv + 1):
        th = PI * j / nv
        row = []
        for i in range(nu):
            ph = 2 * PI * i / nu
            p = V((math.sin(th) * math.sin(ph) * Rr.x, -math.sin(th) * math.cos(ph) * Rr.y,
                   math.cos(th) * Rr.z))
            row.append(C + head_deform(p))
        rows.append(row)

    def keep(p):
        az = abs(math.degrees(math.atan2(p.x, -(p.y - 0.02))))  # 0 front .. 180 back
        if az < 48:
            zmin = 2.47
        elif az < 92:
            zmin = lerp(2.47, 2.30, smoothstep(48, 92, az))
        elif az < 125:
            zmin = lerp(2.30, 1.93, smoothstep(92, 125, az))
        else:
            zmin = 1.93
        return p.z >= zmin

    ids = [[None] * nu for _ in range(nv + 1)]
    for j in range(nv):
        for i in range(nu):
            q = [rows[j][i], rows[j][(i + 1) % nu], rows[j + 1][(i + 1) % nu], rows[j + 1][i]]
            cen = sum(q, V()) / 4
            if not keep(cen):
                continue
            for (jj, ii) in ((j, i), (j, (i + 1) % nu), (j + 1, (i + 1) % nu), (j + 1, i)):
                if ids[jj][ii] is None:
                    ids[jj][ii] = mb.add_vert(rows[jj][ii])
            mb.add_face((ids[j][i], ids[j + 1][i], ids[j + 1][(i + 1) % nu], ids[j][(i + 1) % nu]),
                        "M_hair")
    ob = mb.build("hair_cap", coll)
    finish(ob, rig, subsurf=2, thick=0.03, thick_offset=-1, outline_px=1.6)
    weight_rigid(ob, "head")

    # bangs: heavy straight fringe swept to HER RIGHT (-X), with pointed locks
    mb = MB()
    nu, nv = 49, 9
    rows = []
    for j in range(nv + 1):
        v = j / nv
        row = []
        for i in range(nu):
            u = i / (nu - 1)
            phi = lerp(-1.62, 1.62, u)
            # lock pattern on the bottom edge
            nl = 11
            saw = abs(((u * nl) % 1.0) - 0.5) * 2   # 1 at lock gaps, 0 at lock tips
            side = abs(phi) / 1.62
            zb = lerp(2.355, 2.13, smoothstep(0.45, 1.0, side)) + 0.055 * saw ** 1.3
            zb -= 0.02 * math.exp(-((phi + 0.35) / 0.25) ** 2)   # longest lock over her right eye
            zt = lerp(2.64, 2.50, smoothstep(0.2, 1.0, side))
            z = lerp(zt, zb, v)
            phs = phi - 0.16 * v * (1 - side * 0.6)   # sweep to her right (-X)
            out = 0.012 + 0.07 * math.sin(PI * 0.5 * min(1.0, v * 1.6)) * (1 - 0.35 * v) + 0.01 * (1 - saw) * v
            row.append(head_surf(phs, z, out))
        rows.append(row)
    mb.grid(rows, "M_hair", flip=False)
    ob = mb.build("bangs", coll)
    finish(ob, rig, subsurf=2, thick=0.025, thick_offset=1, outline_px=1.4)
    weight_rigid(ob, "head")

    # jaw-length face-framing strands + side locks
    mb = MB()
    for s in (1, -1):
        pts = [head_surf(1.28 * s, 2.42, 0.06), head_surf(1.22 * s, 2.22, 0.06),
               head_surf(1.12 * s, 2.02, 0.05), head_surf(1.0 * s, 1.84, 0.06) + V((0, -0.02, -0.02))]
        path = catmull(pts, 12)
        T, N, B = frames_along(path)
        rows = []
        for k, p in enumerate(path):
            t = k / (len(path) - 1)
            w = 0.05 * (1 - t ** 1.6) + 0.004
            # ribbon width roughly tangential to the face
            side = V((0, 0, 1)).cross(T[k]).normalized() if abs(T[k].z) < 0.99 else V((1, 0, 0))
            side = (p - HEAD_C)
            side.z = 0
            side = side.normalized().cross(T[k]).normalized()
            rows.append([p - side * w, p + side * w])
        rows_t = [list(r) for r in zip(*rows)]
        mb.grid([list(x) for x in zip(*rows_t)], "M_hair")
    ob = mb.build("hair_strands", coll)
    finish(ob, rig, subsurf=1, thick=0.022, thick_offset=0, outline_px=1.0)
    weight_rigid(ob, "head")

    # bun: high messy loop bun (crown, set back 0.25 H, 0.45 H diameter, top at +0.35 H)
    mb = MB()
    BC = V((0, 0.25, 2.87))
    def bun_def(p):
        a = math.atan2(p.y, p.x)
        b = math.atan2(p.z, math.hypot(p.x, p.y))
        bump = 1 + 0.10 * math.sin(3 * a + 1.0) * math.cos(2 * b) + 0.06 * math.sin(5 * b + a)
        return p * bump
    ellipsoid(mb, BC, (0.225, 0.215, 0.205), "M_hair", nu=24, nv=16, deform=bun_def,
              rot=Euler((-0.35, 0, 0)).to_matrix())
    # wrapped loop around the bun
    loop = [BC + Euler((-0.35, 0.25, 0)).to_matrix() @ V((math.cos(a) * 0.19, math.sin(a) * 0.18,
                                                          0.03 * math.sin(2 * a)))
            for a in [2 * PI * k / 24 for k in range(25)]]
    tube(mb, loop, lambda t, ph: (0.065, 0.05), "M_hair", nseg=10, cap0=False, cap1=False)
    loop2 = [BC + Euler((0.5, -0.6, 0.4)).to_matrix() @ V((math.cos(a) * 0.17, math.sin(a) * 0.16, 0.0))
             for a in [2 * PI * k / 24 for k in range(25)]]
    tube(mb, loop2, lambda t, ph: (0.05, 0.04), "M_hair", nseg=8, cap0=False, cap1=False)
    # flyaway strands
    for (d, l) in ((V((0.3, 0.2, 1.0)), 0.18), (V((-0.5, 0.5, 0.7)), 0.15), (V((0.6, 0.6, 0.3)), 0.13)):
        d = d.normalized()
        base = BC + d * 0.17
        tip = base + d * l + V((0, 0, 0.04))
        mid = base.lerp(tip, 0.5) + V((0.03, 0, 0.03))
        tube(mb, catmull([base, mid, tip], 6), lambda t, ph: 0.022 * (1 - t) + 0.002, "M_hair", nseg=6)
    ob = mb.build("bun", coll)
    finish(ob, rig, subsurf=1, outline_px=1.6)
    weight_rigid(ob, "bun")


# ----------------------------------------------------------------------------
# BOW
# ----------------------------------------------------------------------------
def build_bow(rig, coll):
    mb = MB()
    K = V((-0.05, 0.11, 2.93))
    for s in (1, -1):
        d = V((0.78 * s, 0.22, 0.62)).normalized()
        L = 0.43
        n = 14
        path = [K + d * (L * k / (n - 1)) + V((0, 0.03, 0)) * math.sin(PI * k / (n - 1)) for k in range(n)]
        def rr(t, ph):
            w = 0.16 * (math.sin(PI * clamp(t, 0, 1) ** 0.62)) ** 0.75 + 0.012
            th = 0.055 * math.sin(PI * clamp(t, 0, 1) ** 0.7) + 0.012
            return (w, th)
        # frame: N = in-front-plane perpendicular (wide), B = depth (thin)
        tube(mb, path, rr, "M_red_rim", nseg=16, up=V((0, -1, 0)).cross(d), phase=0.0)
    # tails
    for s in (1, -1):
        d = V((0.35 * s, 0.45, -0.82)).normalized()
        base = K + V((0.02 * s, 0.02, -0.02))
        pts = catmull([base, base + d * 0.14 + V((0.02 * s, 0, 0)), base + d * 0.27], 8)
        T, N, B = frames_along(pts, V((0, -1, 0)))
        rows = []
        for k, p in enumerate(pts):
            t = k / (len(pts) - 1)
            w = lerp(0.03, 0.07, t)
            sd = V((1, 0, 0))
            a = p - sd * w
            b = p + sd * w
            if k == len(pts) - 1:  # V-cut
                a = a + d * 0.0
                b = b + d * 0.0
                c = p - d * 0.05
                rows.append([a, c, b])
            else:
                rows.append([a, p, b])
        mb.grid(rows, "M_red_rim")
    # knot
    ellipsoid(mb, K, (0.075, 0.06, 0.07), "M_red_rim", nu=12, nv=8)
    ob = mb.build("bow", coll)
    finish(ob, rig, subsurf=1, thick=0.0, outline_px=1.6)
    # tails are open sheets: give them some thickness through a small solidify
    s = ob.modifiers.new("Thickness", "SOLIDIFY")
    s.thickness = 0.02
    s.offset = 0
    ob.modifiers.move(len(ob.modifiers) - 1, 2)
    weight_rigid(ob, "bow")


# ----------------------------------------------------------------------------
# COLLAR, choker, bodice, chest flower, cord
# ----------------------------------------------------------------------------
def build_upper_costume(rig, coll):
    # stiff tall flared funnel collar, open in a V at the front
    mb = MB()
    nv, nu = 10, 40
    rows = []
    for j in range(nv + 1):
        v = j / nv
        row = []
        gap = math.radians(lerp(9, 52, v ** 1.1))
        for i in range(nu):
            u = i / (nu - 1)
            th = lerp(gap, 2 * PI - gap, u)
            back = (1 - math.cos(th)) / 2
            z = lerp(1.67, 2.00 + 0.07 * back, v)
            rx = lerp(0.215, 0.45, v ** 1.35)
            ry = lerp(0.175, 0.40, v ** 1.35)
            yo = lerp(0.0, 0.05, v)
            row.append(V((math.sin(th) * rx, -math.cos(th) * ry + yo, z)))
        rows.append(row)
    mb.grid(rows, "M_red", flip=False)
    ob = mb.build("collar", coll)
    ob.data.materials.append(MATS["M_red_inner"])
    finish(ob, rig, subsurf=1, thick=0.03, thick_offset=-1, shell_mat_offset=1, outline_px=1.6)
    weight_custom(ob, lambda p: {"chest": max(0.0, 1 - (p.z - 1.66) / 0.2),
                                 "neck": clamp((p.z - 1.66) / 0.2, 0, 1)})

    # choker inside the collar
    mb = MB()
    ring = [V((math.sin(a) * 0.092, -math.cos(a) * 0.088, 1.86)) for a in [2 * PI * k / 20 for k in range(21)]]
    tube(mb, ring, lambda t, ph: (0.012, 0.025), "M_dark", nseg=6, cap0=False, cap1=False,
         up=V((0, 0, 1)))
    ob = mb.build("choker", coll)
    finish(ob, rig, subsurf=0, outline=False)
    weight_rigid(ob, "neck")

    # bodice: fitted red top, front + sides, off-shoulder, bare back
    mb = MB()
    nu, nv = 30, 12
    rows = []
    for j in range(nv + 1):
        v = j / nv
        row = []
        for i in range(nu):
            u = i / (nu - 1)
            th = lerp(-2.25, 2.25, u)
            side = abs(th) / 2.25
            ztop = lerp(1.74, 1.52, smoothstep(0.25, 0.75, side)) + 0.02 * smoothstep(0.85, 1, side)
            z = lerp(1.26, ztop, v)
            row.append(body_pt(th, z, 0.016 + 0.006 * math.sin(PI * v)))
        rows.append(row)
    mb.grid(rows, "M_red")
    ob = mb.build("bodice", coll)
    finish(ob, rig, subsurf=2, thick=0.012, thick_offset=1, outline_px=1.2)
    weight_distance(ob, ["spine", "chest", "shoulder.L", "shoulder.R"], power=4,
                    bias={"shoulder.L": 0.4, "shoulder.R": 0.4})

    # chest flower (her RIGHT chest/shoulder) + braided cord + gem
    mb = MB()
    fc = body_pt(-0.55, 1.57, 0.05)
    nrm = (fc - V((0, 0, 1.57))).normalized()
    rot = look_rot(nrm, V((0, 0, 1)))
    for k in range(5):
        a = 2 * PI * k / 5 + 0.3
        off = rot @ V((math.cos(a) * 0.055, 0, math.sin(a) * 0.055))
        ellipsoid(mb, fc + off, (0.05, 0.016, 0.03), "M_red", nu=10, nv=6,
                  rot=rot @ Euler((0, -a, 0)).to_matrix())
    ellipsoid(mb, fc + nrm * 0.012, (0.022, 0.02, 0.022), "M_red_inner", nu=8, nv=6)
    ob = mb.build("chest_flower", coll)
    finish(ob, rig, subsurf=1, outline_px=1.0)
    weight_rigid(ob, "chest")

    mb = MB()
    cord = catmull([body_pt(-0.25, 1.70, 0.04), body_pt(-0.38, 1.62, 0.035), body_pt(-0.5, 1.55, 0.04)], 14)
    tube(mb, cord, lambda t, ph: 0.013 * (1 + 0.35 * math.sin(t * 40 + ph)), "M_dark", nseg=6)
    ellipsoid(mb, body_pt(0.0, 1.69, 0.03), (0.022, 0.014, 0.03), "M_purple", nu=8, nv=6)
    ob = mb.build("chest_cord", coll)
    finish(ob, rig, subsurf=0, outline_px=0.8)
    weight_rigid(ob, "chest")


# ----------------------------------------------------------------------------
# SLEEVES (detached, flared bell) + band + right-arm ornament
# ----------------------------------------------------------------------------
def build_sleeves(rig, coll):
    for side in ("L", "R"):
        s = 1 if side == "L" else -1
        sh_in, sj, el, wr, ht = arm_points(side)
        a_dir = (el - sj).normalized()
        f_dir = (wr - el).normalized()
        start = sj + a_dir * 0.10
        path = catmull([start, el, wr, wr + f_dir * 0.12], 18)
        T, N, B = frames_along(path, V((0, 1, 0)))
        nseg = 24
        rows = []
        for k, p in enumerate(path):
            t = k / (len(path) - 1)
            row = []
            for i in range(nseg):
                ph = 2 * PI * i / nseg
                radial = N[k] * math.cos(ph) + B[k] * math.sin(ph)
                r = lerp(0.098, 0.12, smoothstep(0.0, 0.35, t))
                r = lerp(r, 0.285, smoothstep(0.42, 1.0, t) ** 1.25)
                # soft folds near the cuff
                r *= 1 + 0.07 * smoothstep(0.6, 1.0, t) * math.sin(6 * ph + 0.5)
                # back/outer side of the bell hangs longer (kimono furi)
                hang = 0.5 + 0.5 * radial.dot(V((0.25 * s, 0.85, -0.2)).normalized())
                ext = smoothstep(0.6, 1.0, t) * (-0.10 + 0.34 * hang ** 1.4)
                q = p + radial * r + T[k] * ext + V((0, 0, -1)) * ext * 0.6
                row.append(q)
            rows.append(row)
        mb = MB()
        mb.grid(rows, "M_red_rim", close_u=True, flip=False)
        ob = mb.build(f"sleeve.{side}", coll)
        ob.data.materials.append(MATS["M_red_under"])
        finish(ob, rig, subsurf=1, thick=0.022, thick_offset=-1, shell_mat_offset=1, outline_px=1.4)
        def sw(p, side=side):
            d_u, _ = seg_dist(p, BONES[f"upper_arm.{side}"]["head"], BONES[f"upper_arm.{side}"]["tail"])
            d_f, tf = seg_dist(p, BONES[f"forearm.{side}"]["head"], BONES[f"forearm.{side}"]["tail"])
            d_s, ts = seg_dist(p, BONES[f"sleeve.{side}"]["head"], BONES[f"sleeve.{side}"]["tail"])
            wu = 1 / (d_u + 0.03) ** 4
            wf = 1 / (d_f + 0.03) ** 4
            # cuff: past the wrist -> sleeve tip bone
            along = (p - BONES[f"forearm.{side}"]["tail"]).dot(f_dir)
            wsl = smoothstep(-0.12, 0.08, along) * 3.0 * (wu + wf)
            return {f"upper_arm.{side}": wu, f"forearm.{side}": wf, f"sleeve.{side}": wsl}
        weight_custom(ob, sw)
        # dark band at the top edge of the sleeve
        mb = MB()
        ring = [start + (N[0] * math.cos(a) + B[0] * math.sin(a)) * 0.112 for a in
                [2 * PI * k / 20 for k in range(21)]]
        tube(mb, ring, lambda t, ph: (0.018, 0.009), "M_dark", nseg=6, cap0=False, cap1=False)
        ob = mb.build(f"sleeve_band.{side}", coll)
        finish(ob, rig, subsurf=0, outline_px=0.8)
        weight_rigid(ob, f"upper_arm.{side}")

        if side == "R":
            # red flower cluster + purple criss-cross lacing + dangling purple ribbon (her RIGHT arm)
            mb = MB()
            outer = V((-1, -0.35, 0.15)).normalized()
            fc = start + a_dir * 0.03 + outer * 0.13
            rot = look_rot(outer, V((0, 0, 1)))
            for k in range(5):
                a = 2 * PI * k / 5
                off = rot @ V((math.cos(a) * 0.06, 0, math.sin(a) * 0.06))
                ellipsoid(mb, fc + off, (0.058, 0.02, 0.034), "M_red", nu=8, nv=6,
                          rot=rot @ Euler((0, -a, 0)).to_matrix())
            ellipsoid(mb, fc + outer * 0.015, (0.026, 0.022, 0.026), "M_purple", nu=8, nv=6)
            # lacing zig-zag down the sleeve front-outer face
            pts = []
            for k in range(7):
                t = 0.12 + k * 0.05
                pp = sj + a_dir * (0.14 + k * 0.035)
                ang = 0.35 if k % 2 == 0 else -0.35
                rd = (Matrix.Rotation(ang, 3, a_dir) @ outer).normalized()
                pts.append(pp + rd * 0.128)
            tube(mb, pts, lambda t, ph: 0.011, "M_purple", nseg=5)
            # dangling ribbon
            rb = catmull([fc + V((0, -0.01, -0.03)), fc + V((-0.05, -0.04, -0.22)),
                          fc + V((-0.03, -0.03, -0.42))], 12)
            rows = [[p - V((0.02, 0.0, 0)), p + V((0.02, 0, 0))] for p in rb]
            mb.grid(rows, "M_purple")
            ob = mb.build("arm_ornament.R", coll)
            finish(ob, rig, subsurf=0, outline_px=0.8)
            weight_rigid(ob, "upper_arm.R")


# ----------------------------------------------------------------------------
# CORSET / harness, belt, pouch, tabs
# ----------------------------------------------------------------------------
def build_corset(rig, coll):
    mb = MB()
    nu, nv = 36, 10
    rows = []
    for j in range(nv + 1):
        v = j / nv
        row = []
        for i in range(nu):
            th = 2 * PI * i / nu
            front = (1 + math.cos(th)) / 2
            ztop = 1.40 + 0.03 * front    # slight sweetheart rise at the front
            z = lerp(1.0, ztop, v)
            row.append(body_pt(th, z, 0.03 + 0.004 * math.sin(PI * v)))
        rows.append(row)
    mb.grid(rows, "M_leather", close_u=True, flip=False)
    # top-edge highlight rim (leather[2] via the highlight band is lighting dependent; add a piping)
    pip = [body_pt(2 * PI * k / 36, 1.40 + 0.03 * (1 + math.cos(2 * PI * k / 36)) / 2, 0.042)
           for k in range(37)]
    tube(mb, pip, lambda t, ph: 0.011, "M_leather", nseg=6, cap0=False, cap1=False)
    # three stacked straps
    for zc in (1.10, 1.20, 1.30):
        ring = [body_pt(2 * PI * k / 36, zc, 0.05) for k in range(37)]
        tube(mb, ring, lambda t, ph: (0.015, 0.027), "M_leather", nseg=8, cap0=False, cap1=False,
             up=V((0, 0, 1)))
    # central vertical plate
    for k in range(10):
        pass
    plate = [body_pt(0.0, z, 0.06) for z in (1.03, 1.12, 1.22, 1.32, 1.40)]
    tube(mb, plate, lambda t, ph: (0.016, 0.042), "M_leather", nseg=8, up=V((0, -1, 0)))
    ob = mb.build("corset", coll)
    finish(ob, rig, subsurf=1, outline_px=1.4)
    weight_distance(ob, ["hips", "spine", "chest"], power=4)

    # buckles (steel) on her right-front of each strap + rivets on the plate
    mb = MB()
    for zc in (1.10, 1.20, 1.30):
        th = -0.45
        p = body_pt(th, zc, 0.07)
        n = (p - V((0, 0, zc)))
        n.z = 0
        rot = look_rot(n.normalized(), V((0, 0, 1)))
        for (dx, dz, sx, sz) in ((-0.022, 0, 0.009, 0.042), (0.022, 0, 0.009, 0.042), (0, 0.018, 0.052, 0.009),
                                 (0, -0.018, 0.052, 0.009), (0, 0, 0.04, 0.006)):
            box(mb, p + rot @ V((dx, 0, dz)), (sx, 0.016, sz), "M_steel", rot=rot)
    for z in (1.08, 1.17, 1.26, 1.35):
        ellipsoid(mb, body_pt(0.0, z, 0.083), (0.011, 0.008, 0.011), "M_steel", nu=8, nv=5)
    ob = mb.build("corset_buckles", coll)
    finish(ob, rig, subsurf=0, outline_px=0.8)
    weight_distance(ob, ["hips", "spine"], power=4)

    # low hip belt + round pouch (front of her RIGHT hip) + two hanging tabs
    mb = MB()
    belt = [body_pt(2 * PI * k / 40, 0.985 - 0.03 * math.sin(2 * PI * k / 40), 0.06) for k in range(41)]
    tube(mb, belt, lambda t, ph: (0.012, 0.03), "M_leather", nseg=8, cap0=False, cap1=False)
    pc = body_pt(-0.55, 0.93, 0.13)
    prot = look_rot(V((-0.45, -1, 0)).normalized(), V((0, 0, 1)))
    ellipsoid(mb, pc, (0.085, 0.06, 0.08), "M_leather", nu=16, nv=10, rot=prot)
    ellipsoid(mb, pc + prot @ V((0, -0.035, 0.035)), (0.08, 0.035, 0.05), "M_leather", nu=12, nv=8, rot=prot)
    box(mb, pc + prot @ V((0, -0.07, 0.02)), (0.022, 0.012, 0.03), "M_steel", rot=prot)
    for s in (1, -1):
        top = body_pt(0.33 * s, 1.0, 0.07)
        pts = catmull([top, top + V((0.01 * s, -0.04, -0.12)), top + V((0.015 * s, -0.08, -0.24))], 8)
        rows = []
        for k, p in enumerate(pts):
            t = k / (len(pts) - 1)
            w = 0.04 * (1 - 0.5 * smoothstep(0.75, 1, t))
            rows.append([p + V((-w, 0, 0)), p + V((w, 0, 0))])
        mb.grid(rows, "M_leather")
        box(mb, top + V((0, -0.015, -0.05)), (0.05, 0.014, 0.022), "M_steel")
    ob = mb.build("belt_pouch", coll)
    finish(ob, rig, subsurf=1, thick=0.0, outline_px=1.2)
    s = ob.modifiers.new("Thickness", "SOLIDIFY")
    s.thickness = 0.02
    ob.modifiers.move(len(ob.modifiers) - 1, 2)
    weight_custom(ob, lambda p: {"hips": 1.0, "skirt.F": 1.8 * smoothstep(0.95, 0.78, p.z) if p.y < -0.2 else 0.0})


# ----------------------------------------------------------------------------
# SKIRT (asymmetric layered petal skirt) + shorts + thigh strap
# ----------------------------------------------------------------------------
def petal(theta_deg, centers, width):
    v = 0.0
    for c in centers:
        d = abs(((theta_deg - c + 180) % 360) - 180)
        v = max(v, max(0.0, 1 - d / width) ** 1.6)
    return v


def skirt_weights(p, top=1.04):
    th = math.atan2(p.x, -p.y)  # 0 front, +pi/2 her left (+X)
    depth = clamp((top - p.z) / 0.8, 0, 1)
    wF = max(0.0, math.cos(th)) ** 2
    wB = max(0.0, -math.cos(th)) ** 2
    wL = max(0.0, math.sin(th)) ** 2
    wR = max(0.0, -math.sin(th)) ** 2
    d = {"hips": (1 - depth) ** 2 * 2.0 + 0.02}
    k = depth ** 0.8
    d["skirt.F"] = wF * k
    d["skirt.L"] = wL * k
    d["skirt.R"] = wR * k
    # back: skirt.B then tail chain by height
    if wB > 0:
        if p.z > 0.66:
            d["skirt.B"] = wB * k
        else:
            zz = p.z
            a = smoothstep(0.66, 0.50, zz)
            b = smoothstep(0.48, 0.32, zz)
            d["skirt.B"] = wB * k * (1 - a)
            d["skirt.tail.001"] = wB * k * a * (1 - b)
            d["skirt.tail.002"] = wB * k * b * (1 - smoothstep(0.30, 0.2, zz))
            d["skirt.tail.003"] = wB * k * smoothstep(0.30, 0.2, zz)
    # a little thigh follow for the front/sides so legs don't poke through
    d["thigh.L"] = 0.25 * k * max(0.0, math.sin(th)) * max(0.0, math.cos(th) + 0.4)
    d["thigh.R"] = 0.25 * k * max(0.0, -math.sin(th)) * max(0.0, math.cos(th) + 0.4)
    return d


def build_skirt(rig, coll):
    TOP = 1.05
    # outer layer: knee-length front panel (slit on HER LEFT), long layered tails at sides/back
    mb = MB()
    nu, nv = 72, 14
    rows = []
    for j in range(nv + 1):
        v = j / nv
        row = []
        gap = lerp(0.0, 38.0, v ** 1.1)
        slit = 32.0   # degrees, her left-front
        for i in range(nu):
            u = i / (nu - 1)
            thd = lerp(slit + gap * 0.5, slit + 360 - gap * 0.5, u)
            th = math.radians(thd)
            back = (1 - math.cos(th)) / 2
            hem = 0.62 - 0.30 * back ** 1.1
            hem -= 0.13 * petal(thd, (112, 156, 204, 248), 20)   # 4 petal points
            hem += 0.07 * (1 - petal(thd, (112, 156, 204, 248), 20)) * smoothstep(0.25, 0.6, back)
            z = lerp(TOP, hem, v)
            rx0, ry0, yo0 = torso_profile(TOP)
            rx0 += 0.045
            ry0 += 0.05
            flare = v ** 0.85
            rx = lerp(rx0, 0.64, flare)
            ry = lerp(ry0, 0.56 + 0.08 * back, flare)
            fold = 1 + 0.06 * flare * math.sin(9 * th + 0.4)
            p = V((math.sin(th) * rx * fold, -math.cos(th) * ry * fold, z))
            p.y += 0.10 * back * v ** 1.5         # tails drift back
            row.append(p)
        rows.append(row)
    mb.grid(rows, "M_red", flip=True)
    ob = mb.build("skirt_outer", coll)
    ob.data.materials.append(MATS["M_red_under"])
    finish(ob, rig, subsurf=1, thick=0.022, thick_offset=-1, shell_mat_offset=1, outline_px=1.6)
    weight_custom(ob, skirt_weights)

    # under layer: darker crimson tails at the back reaching 0.2 H above the sole
    mb = MB()
    nu, nv = 48, 14
    rows = []
    for j in range(nv + 1):
        v = j / nv
        row = []
        for i in range(nu):
            u = i / (nu - 1)
            thd = lerp(78, 282, u)
            th = math.radians(thd)
            back = (1 - math.cos(th)) / 2
            hem = 0.42 - 0.20 * back
            hem -= 0.10 * petal(thd, (134, 180, 226), 18)
            hem += 0.06 * (1 - petal(thd, (134, 180, 226), 18))
            z = lerp(TOP - 0.02, hem, v)
            rx0, ry0, yo0 = torso_profile(TOP - 0.02)
            flare = v ** 0.85
            rx = lerp(rx0 + 0.035, 0.60, flare)
            ry = lerp(ry0 + 0.04, 0.56 + 0.06 * back, flare)
            fold = 1 + 0.05 * flare * math.sin(7 * th + 1.3)
            p = V((math.sin(th) * rx * fold, -math.cos(th) * ry * fold, z))
            p.y += 0.12 * back * v ** 1.5
            row.append(p)
        rows.append(row)
    mb.grid(rows, "M_red_under", flip=True)
    ob = mb.build("skirt_under", coll)
    ob.data.materials.append(MATS["M_red_under"])
    finish(ob, rig, subsurf=1, thick=0.018, thick_offset=-1, shell_mat_offset=0, outline_px=1.4)
    weight_custom(ob, skirt_weights)

    # black shorts
    mb = MB()
    nu = 28
    rows = []
    for j in range(7):
        z = lerp(1.02, 0.80, j / 6)
        row = []
        for i in range(nu):
            th = 2 * PI * i / nu
            if z > 0.9:
                row.append(body_pt(th, z, 0.012))
            else:
                # split into two leg openings
                p = body_pt(th, 0.9, 0.012)
                row.append(V((p.x, p.y, z)))
        rows.append(row)
    mb.grid(rows, "M_dark", close_u=True, flip=True)
    ob = mb.build("shorts_core", coll)
    finish(ob, rig, subsurf=0, outline=False)
    # actual shorts legs (cuffs around the thighs)
    for side in ("L", "R"):
        hip, kn, an, toe = leg_points(side)
        s = 1 if side == "L" else -1
        path = [hip + V((-0.02 * s, 0, 0.1)), hip + V((0, 0, -0.03)), hip.lerp(kn, 0.33)]
        tube(mb, path, lambda t, ph: lerp(0.17, 0.162, t), "M_dark", nseg=16, cap0=False, cap1=False)
    bpy.data.objects.remove(ob, do_unlink=True)
    ob = mb.build("shorts", coll)
    finish(ob, rig, subsurf=1, outline_px=1.2)
    weight_distance(ob, ["hips", "thigh.L", "thigh.R"], power=5, bias={"hips": 1.5})

    # thigh strap + small pouch (HER LEFT thigh)
    mb = MB()
    hip, kn, an, toe = leg_points("L")
    ax = (kn - hip).normalized()
    c = hip.lerp(kn, 0.66)
    rn = 0.125
    T, N, B = frames_along([hip, kn], V((0, -1, 0)))
    ring = [c + (N[0] * math.cos(a) + B[0] * math.sin(a)) * rn for a in [2 * PI * k / 24 for k in range(25)]]
    tube(mb, ring, lambda t, ph: (0.016, 0.04), "M_leather", nseg=6, cap0=False, cap1=False)
    outer = V((1, -0.45, 0)).normalized()
    pc = c + outer * (rn + 0.035) + V((0, 0, -0.02))
    box(mb, pc, (0.05, 0.07, 0.09), "M_leather", rot=look_rot(V((0.25, 1, 0)).normalized()), smooth=True)
    box(mb, pc + V((0.012, -0.003, 0.03)), (0.04, 0.074, 0.035), "M_leather",
        rot=look_rot(V((0.25, 1, 0)).normalized()))
    box(mb, pc + V((0.03, -0.01, 0.015)), (0.008, 0.02, 0.02), "M_steel")
    ob = mb.build("thigh_strap.L", coll)
    finish(ob, rig, subsurf=1, outline_px=1.0)
    weight_rigid(ob, "thigh.L")


# ----------------------------------------------------------------------------
# SANDALS (chibi heeled, criss-cross ankle straps)
# ----------------------------------------------------------------------------
def build_shoes(rig, coll):
    for side in ("L", "R"):
        s = 1 if side == "L" else -1
        hip, kn, an, toe = leg_points(side)
        x = 0.14 * s
        mb = MB()
        # sole (follows the foot slope)
        sole = catmull([V((x, 0.10, 0.145)), V((x, 0.04, 0.125)), V((x, -0.06, 0.05)), V((x, -0.15, 0.012)),
                        V((x, -0.215, 0.012))], 12)
        def sr(t, ph):
            w = 0.062 * (1 - 0.55 * smoothstep(0.9, 1.0, t)) * (1 - 0.3 * smoothstep(0.1, 0.0, t))
            return (0.018, w)
        tube(mb, sole, sr, "M_dark", nseg=10)
        # heel post
        tube(mb, [V((x, 0.075, 0.14)), V((x, 0.07, 0.07)), V((x, 0.065, 0.0))],
             lambda t, ph: lerp(0.034, 0.018, t), "M_dark", nseg=10)
        # toe vamp (closed toe band)
        vamp = catmull([V((x - 0.06 * s, -0.12, 0.02)), V((x, -0.13, 0.075)), V((x + 0.06 * s, -0.12, 0.02))], 8)
        tube(mb, vamp, lambda t, ph: (0.035, 0.012), "M_dark", nseg=8, up=V((0, -1, 0)))
        # ankle straps: two rings + criss-cross
        for zc, tilt in ((0.24, 0.25), (0.31, -0.25)):
            ring = [V((x + math.sin(a) * 0.075, 0.03 - math.cos(a) * 0.072, zc + tilt * 0.06 * math.cos(a)))
                    for a in [2 * PI * k / 20 for k in range(21)]]
            tube(mb, ring, lambda t, ph: (0.012, 0.006), "M_dark", nseg=6, cap0=False, cap1=False)
        ob = mb.build(f"shoe.{side}", coll)
        finish(ob, rig, subsurf=1, outline_px=1.2)
        weight_custom(ob, lambda p, side=side: {f"foot.{side}": 1.0,
                                                  f"shin.{side}": 3.0 * smoothstep(0.2, 0.3, p.z)})


# ----------------------------------------------------------------------------
# SCARF ribbons
# ----------------------------------------------------------------------------
def build_scarf(rig, coll):
    for side in ("L", "R"):
        s = 1 if side == "L" else -1
        chain = [BONES[f"scarf.{side}.001"]["head"]] + [BONES[f"scarf.{side}.{i:03d}"]["tail"] for i in (1, 2, 3)]
        path = catmull([chain[0] + V((-0.04 * s, -0.04, 0.03))] + chain, 22)
        T, N, B = frames_along(path, V((0, 1, 0)))
        rows = []
        for k, p in enumerate(path):
            t = k / (len(path) - 1)
            w = 0.06 * (1 + 0.15 * math.sin(PI * t))
            tw = 0.5 * s * t + 0.25 * math.sin(3 * t)     # gentle twist
            wd = (V((1, 0, 0)) * math.cos(tw) + V((0, 1, 0)) * math.sin(tw) * 0.5)
            wd = (wd - T[k] * wd.dot(T[k])).normalized()
            a, b = p - wd * w, p + wd * w
            if k == len(path) - 1:     # angled cut end
                b = b + T[k] * 0.06
            rows.append([a, p, b])
        mb = MB()
        mb.grid(rows, "M_pink")
        ob = mb.build(f"scarf.{side}", coll)
        finish(ob, rig, subsurf=1, thick=0.012, thick_offset=0, outline_px=1.0)
        names = [f"scarf.{side}.{i:03d}" for i in (1, 2, 3)]
        weight_distance(ob, ["neck"] + names, power=5, bias={"neck": 0.5})


# ----------------------------------------------------------------------------
# KATANA (+ sprite variant) and optional saya
# ----------------------------------------------------------------------------
def katana_mesh(mb, blade_w=0.06, blade_t=0.018, hook_r=0.085, bar_len=0.22, sprite=False):
    """Sword in local space: grip at origin, +Y along the blade, +Z = edge, X = flat normal."""
    g0 = GUARD_Y
    L = BLADE_LEN
    n = 24
    rings = []
    for k in range(n + 1):
        t = k / n
        y = g0 + 0.035 + t * (L - 0.035)
        sori = -0.07 * t * t           # tip curves toward the spine (-Z)
        w = blade_w * (1 - 0.18 * t)
        tip = smoothstep(0.90, 1.0, t)
        we = w * (1 - tip)             # edge recedes toward the spine at the kissaki
        th = blade_t * (1 - 0.6 * t) * (1 - 0.9 * tip) + 0.001
        zs = -w / 2 + sori                 # spine
        ze = zs + w * (1 - tip) + 0.0005   # edge
        zm = zs + (ze - zs) * 0.32
        rings.append([V((0, y, ze)), V((th / 2, y, zm)), V((0, y, zs)), V((-th / 2, y, zm))])
    ids = []
    for r in rings:
        ids.append([mb.add_vert(p) for p in r])
    for k in range(n):
        for i in range(4):
            a, b = ids[k][i], ids[k][(i + 1) % 4]
            c, d = ids[k + 1][(i + 1) % 4], ids[k + 1][i]
            mb.add_face((a, b, c, d), "M_steel", smooth=False)
    mb.cap(ids[0], V((0, g0 + 0.035, sum(p.z for p in rings[0]) / 4)), "M_steel", flip=True, smooth=False)
    # habaki
    box(mb, (0, g0 + 0.03, 0), (blade_t * 2.2 + 0.01, 0.05, blade_w * 1.15), "M_steel")
    # guard bar: straight cross-bar perpendicular to the blade (long arm toward the spine side)
    bar_t = 0.035 if not sprite else 0.05
    box(mb, (0, g0, -bar_len * 0.30), (bar_t, bar_t, bar_len), "M_steel")
    # kagi: crescent hook at the edge-side end of the bar, horns: long toward the handle,
    # short toward the blade -- reads as a crescent moon (refs/1.png)
    end_z = -bar_len * 0.30 + bar_len / 2
    cc = V((0, g0, end_z + hook_r))
    arc = []
    for k in range(17):
        a = math.radians(lerp(-140, 105, k / 16))
        arc.append(cc + V((0, math.sin(a) * hook_r * (1.15 if a < 0 else 1.0), -math.cos(a) * hook_r)))
    def hr(t, ph):
        a = lerp(-140, 105, t)
        mid = 1 - abs(a + 10) / 130
        r = (0.004 + 0.016 * max(0.0, mid) ** 0.8) * (1.6 if sprite else 1.0)
        return (bar_t * 0.45, r)
    tube(mb, arc, hr, "M_steel", nseg=8, up=V((1, 0, 0)))
    # fuchi collar
    tube(mb, [V((0, g0 - 0.005, 0)), V((0, g0 - 0.035, 0))], lambda t, ph: (0.03, 0.036), "M_steel", nseg=10,
         up=V((0, 0, 1)))
    # tsuka: black wrap with red diamond windows
    hy0, hy1 = g0 - 0.035, g0 - HANDLE_LEN
    tube(mb, [V((0, hy0, 0)), V((0, (hy0 + hy1) / 2, 0)), V((0, hy1, 0))],
         lambda t, ph: (0.026 * (1 - 0.06 * math.sin(PI * t)), 0.032 * (1 - 0.06 * math.sin(PI * t))),
         "M_dark", nseg=12, up=V((0, 0, 1)), cap0=False, cap1=False)
    # diamonds on both flats (+X / -X)
    nd = 5
    for sx in (1, -1):
        for k in range(nd):
            y = lerp(hy0 - 0.04, hy1 + 0.04, k / (nd - 1))
            dw, dh = 0.03, 0.028 if not sprite else 0.034
            x = sx * (0.0275 if not sprite else 0.03)
            q = [V((x, y + dw, 0)), V((x, y, dh)), V((x, y - dw, 0)), V((x, y, -dh))]
            idx = [mb.add_vert(p) for p in q]
            mb.add_face(idx if sx > 0 else list(reversed(idx)), "M_red_flat", smooth=False)
    # kashira cap
    tube(mb, [V((0, hy1 + 0.01, 0)), V((0, hy1 - 0.035, 0))], lambda t, ph: (0.03, 0.036) if t < 0.7 else (0.024, 0.03),
         "M_steel", nseg=10, up=V((0, 0, 1)), cap0=False)


def place_on_bone(ob, rig, bname):
    bmat = rig.data.bones[bname].matrix_local
    ob.data.transform(bmat)
    ob.data.update()


def build_sword(rig, coll):
    mb = MB()
    katana_mesh(mb)
    ob = mb.build("katana", coll)
    place_on_bone(ob, rig, "sword")
    finish(ob, rig, subsurf=0, outline_px=1.0)
    weight_rigid(ob, "sword")
    # sprite-render variant: blade 0.12 H wide (2 px), hook 0.18 H (3 px), bar 0.25 H
    mb = MB()
    katana_mesh(mb, blade_w=0.12, blade_t=0.03, hook_r=0.09, bar_len=0.25, sprite=True)
    ob2 = mb.build("katana_sprite", coll)
    place_on_bone(ob2, rig, "sword")
    finish(ob2, rig, subsurf=0, outline_px=1.0)
    weight_rigid(ob2, "sword")
    ob2.hide_render = True
    ob2.hide_set(True)
    ob2["variant"] = "sprite"
    ob["variant"] = "hero"
    # optional saya (bible: no sheath shown; kept hidden, for sheathed locomotion if direction changes)
    mb = MB()
    path = [V((0, GUARD_Y - 0.0 + 0.005, 0)), V((0, GUARD_Y + BLADE_LEN * 0.5, -0.03)),
            V((0, GUARD_Y + BLADE_LEN + 0.04, -0.09))]
    tube(mb, path, lambda t, ph: (0.026, 0.05 * (1 - 0.3 * t)), "M_dark", nseg=10, up=V((0, 0, 1)),
         mat_fn=lambda t: "M_red" if t < 0.06 else "M_dark")
    ob3 = mb.build("saya", coll)
    place_on_bone(ob3, rig, "sheath")
    finish(ob3, rig, subsurf=1, outline_px=1.0)
    weight_rigid(ob3, "sheath")
    ob3.hide_render = True
    ob3.hide_set(True)


# ----------------------------------------------------------------------------
# camera, lights, render settings
# ----------------------------------------------------------------------------
ISO_ELEV = 30.0


def setup_scene():
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.film_transparent = True
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    sc.view_settings.exposure = 0
    sc.view_settings.gamma = 1
    sc.render.dither_intensity = 0.0
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.render.image_settings.color_depth = "8"
    try:
        sc.eevee.taa_render_samples = 16
    except Exception:
        pass
    # world black => only the sun drives the cel ramp
    w = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    sc.world = w
    try:
        w.use_nodes = True
    except Exception:
        pass
    bg = w.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0, 0, 0, 1)
        bg.inputs[1].default_value = 0.0
    # AOV for material ids
    vl = sc.view_layers[0]
    if "matid" not in [a.name for a in vl.aovs]:
        a = vl.aovs.add()
        a.name = "matid"
        a.type = "COLOR"

    cam_d = bpy.data.cameras.new("cam")
    cam_d.type = "ORTHO"
    cam_d.ortho_scale = 6.5
    cam_d.clip_start = 0.1
    cam_d.clip_end = 100
    cam = bpy.data.objects.new("cam", cam_d)
    sc.collection.objects.link(cam)
    sc.camera = cam
    el = math.radians(ISO_ELEV)
    cam.rotation_euler = (PI / 2 - el, 0, 0)
    fwd = V((0, math.cos(el), -math.sin(el)))
    cam.location = V((0, 0, 1.4)) - fwd * 20
    # key light: camera-locked, from screen top-left and slightly toward the viewer
    ld = bpy.data.lights.new("key", "SUN")
    ld.energy = PI
    ld.angle = math.radians(1.0)
    try:
        ld.use_shadow = True
    except Exception:
        pass
    key = bpy.data.objects.new("key", ld)
    sc.collection.objects.link(key)
    key.parent = cam
    d_cam = V((0.45, -0.50, -0.74)).normalized()     # travel direction in camera space
    key.rotation_euler = d_cam.to_track_quat("-Z", "Y").to_euler()
    key.location = (0, 0, 0)
    return cam


# ----------------------------------------------------------------------------
# poses (stored as JSON on the rig, applied by render / sprite scripts)
# ----------------------------------------------------------------------------
def pose_space(rig, name):
    return rig.pose.bones[name].matrix.copy()


def aim(rig, name, target, roll_ref=None):
    """Rotate pose bone `name` so its Y axis points at armature-space `target`."""
    pb = rig.pose.bones[name]
    bpy.context.view_layer.update()
    M = pb.matrix.copy()
    head = M.translation.copy()
    y0 = V((M[0][1], M[1][1], M[2][1])).normalized()
    d = (V(target) - head).normalized()
    q = y0.rotation_difference(d)
    R3 = q.to_matrix() @ M.to_3x3()
    if roll_ref is not None:
        # twist around the new Y so that Z points toward roll_ref
        y = d
        z = V(roll_ref) - y * V(roll_ref).dot(y)
        if z.length > 1e-5:
            z.normalize()
            x = y.cross(z).normalized()
            R3 = Matrix((x, y, z)).transposed()
    NM = R3.to_4x4()
    NM.translation = head
    pb.matrix = NM
    bpy.context.view_layer.update()


def move(rig, name, offset):
    pb = rig.pose.bones[name]
    bpy.context.view_layer.update()
    M = pb.matrix.copy()
    M.translation = M.translation + V(offset)
    pb.matrix = M
    bpy.context.view_layer.update()


def rotate_world(rig, name, axis, angle):
    pb = rig.pose.bones[name]
    bpy.context.view_layer.update()
    M = pb.matrix.copy()
    t = M.translation.copy()
    R3 = Matrix.Rotation(angle, 3, V(axis)) @ M.to_3x3()
    NM = R3.to_4x4()
    NM.translation = t
    pb.matrix = NM
    bpy.context.view_layer.update()


def two_bone(rig, upper, lower, target, pole):
    bpy.context.view_layer.update()
    S = rig.pose.bones[upper].matrix.translation.copy()
    l1 = rig.data.bones[upper].length
    l2 = rig.data.bones[lower].length
    T = V(target)
    d = min((T - S).length, (l1 + l2) * 0.995)
    di = (T - S).normalized()
    a = (l1 * l1 - l2 * l2 + d * d) / (2 * d)
    h = math.sqrt(max(0.0, l1 * l1 - a * a))
    pp = V(pole) - S
    pp = (pp - di * pp.dot(di)).normalized()
    E = S + di * a + pp * h
    aim(rig, upper, E)
    aim(rig, lower, S + di * d)


def capture_pose(rig):
    out = {}
    for pb in rig.pose.bones:
        q = pb.rotation_quaternion
        l = pb.location
        if abs(q.w - 1) > 1e-6 or l.length > 1e-6 or abs(q.x) + abs(q.y) + abs(q.z) > 1e-6:
            out[pb.name] = [round(q.w, 6), round(q.x, 6), round(q.y, 6), round(q.z, 6),
                            round(l.x, 6), round(l.y, 6), round(l.z, 6)]
    return out


def clear_pose(rig):
    for pb in rig.pose.bones:
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.location = (0, 0, 0)
        pb.scale = (1, 1, 1)
    bpy.context.view_layer.update()


def make_poses(rig):
    poses = {"rest": {}}
    # --- sword_ready (refs/2.png): low wide two-handed stance, blade low on her left-front
    clear_pose(rig)
    move(rig, "hips", (0.0, 0.03, -0.16))
    rotate_world(rig, "hips", (0, 0, 1), math.radians(-12))
    rotate_world(rig, "spine", (1, 0, 0), math.radians(-10))
    rotate_world(rig, "chest", (1, 0, 0), math.radians(-8))
    rotate_world(rig, "chest", (0, 0, 1), math.radians(18))
    rotate_world(rig, "head", (0, 0, 1), math.radians(-14))
    rotate_world(rig, "head", (1, 0, 0), math.radians(8))
    # legs: left leg forward-out, right leg back-out, knees bent
    two_bone(rig, "thigh.L", "shin.L", V((0.52, -0.36, 0.21)), V((0.9, -1.0, 0.6)))
    two_bone(rig, "thigh.R", "shin.R", V((-0.46, 0.36, 0.21)), V((-0.9, -0.6, 0.6)))
    for side, fw in (("L", V((0.25, -1, -0.95))), ("R", V((-0.3, -1, -0.95)))):
        bpy.context.view_layer.update()
        h = rig.pose.bones[f"foot.{side}"].matrix.translation
        aim(rig, f"foot.{side}", h + fw.normalized() * 0.2)
    # grip: hands together low at her left front, blade forward-down-left toward the ground
    grip = V((0.30, -0.50, 0.92))
    sdir = V((0.42, -0.62, -0.66)).normalized()
    two_bone(rig, "upper_arm.L", "forearm.L", grip - V((0.05, -0.02, -0.06)), V((0.8, 0.5, 0.6)))
    aim(rig, "hand.L", grip + sdir * 0.15)
    gripR = grip - sdir * 0.17
    two_bone(rig, "upper_arm.R", "forearm.R", gripR - V((0.06, -0.03, -0.05)), V((-0.6, -0.2, 0.3)))
    aim(rig, "hand.R", gripR + sdir * 0.15)
    # sword bone: head at the left-hand grip point, Y along blade, edge (Z) down
    bpy.context.view_layer.update()
    hm = rig.pose.bones["hand.L"].matrix
    gp = hm.translation + V((hm[0][1], hm[1][1], hm[2][1])) * 0.1
    pb = rig.pose.bones["sword"]
    y = sdir
    z = V((0, 0, -1)) - y * V((0, 0, -1)).dot(y)
    z.normalize()
    x = y.cross(z).normalized()
    M = Matrix((x, y, z)).transposed().to_4x4()
    M.translation = gp
    pb.matrix = M
    bpy.context.view_layer.update()
    # secondary: scarf streams back/up, skirt flares, sleeves trail
    for side, s in (("L", 1), ("R", -1)):
        for i, (dx, dy, dz) in enumerate(((0.10, 0.9, -0.35), (0.25, 1.0, 0.05), (0.35, 0.8, 0.40))):
            nm = f"scarf.{side}.{i + 1:03d}"
            bpy.context.view_layer.update()
            h = rig.pose.bones[nm].matrix.translation
            aim(rig, nm, h + V((dx * s - 0.35, dy, dz + (0.1 if s > 0 else -0.05))).normalized())
        bpy.context.view_layer.update()
        h = rig.pose.bones[f"sleeve.{side}"].matrix.translation
        aim(rig, f"sleeve.{side}", h + V((0.0, 0.8, -0.6)).normalized())
    rotate_world(rig, "skirt.B", (1, 0, 0), math.radians(-25))
    rotate_world(rig, "skirt.L", (0, 1, 0), math.radians(-14))
    rotate_world(rig, "skirt.R", (0, 1, 0), math.radians(14))
    rotate_world(rig, "skirt.F", (1, 0, 0), math.radians(12))
    rotate_world(rig, "skirt.tail.001", (1, 0, 0), math.radians(-15))
    poses["sword_ready"] = capture_pose(rig)
    clear_pose(rig)
    rig["poses"] = json.dumps(poses)


# ----------------------------------------------------------------------------
def main():
    reset_scene()
    build_materials()
    define_skeleton()
    coll = bpy.data.collections.new("character")
    bpy.context.scene.collection.children.link(coll)
    rig = build_rig()
    head = build_body(rig, coll)
    bpy.context.view_layer.update()
    build_face(rig, coll, head)
    build_hair(rig, coll)
    build_bow(rig, coll)
    build_upper_costume(rig, coll)
    build_sleeves(rig, coll)
    build_corset(rig, coll)
    build_skirt(rig, coll)
    build_shoes(rig, coll)
    build_scarf(rig, coll)
    build_sword(rig, coll)
    setup_scene()
    make_poses(rig)
    # cel look: only hair/body forms cast shadows; big cloth shapes would blanket the legs/face
    for ob in bpy.data.objects:
        if ob.type == "MESH" and ob.name.split(".")[0] in (
                "skirt_outer", "skirt_under", "sleeve", "scarf", "collar", "katana", "katana_sprite",
                "bow", "belt_pouch", "arm_ornament", "chest_flower", "chest_cord", "saya", "sleeve_band"):
            ob.visible_shadow = False
    # meta
    rig["H"] = 1.0
    rig["front"] = "-Y (S iso direction)"
    rig["handedness"] = "+X = her LEFT (katana hand), -X = her RIGHT (arm ornament)"
    for ob in bpy.data.objects:
        if ob.type == "MESH":
            for p in ob.data.polygons:
                pass
    bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND, compress=True)
    nb = len(rig.data.bones)
    print(f"[build] saved {OUT_BLEND}  objects={len(bpy.data.objects)} bones={nb} materials={len(bpy.data.materials)}")


if __name__ == "__main__":
    main()
