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
    make_toon("M_skin", R["skin"], (0.16, 0.95))
    # round 2 (AD): very dark brunette. Hair mass = hair[0] base with outline-colour shadow;
    # hair[1] is used only by the angel-ring sheen band (M_hair_sheen), hair[2] as its glint.
    make_toon("M_hair", [OUTLINE_HEX, R["hair"][0]], (0.10,), rim=True)
    make_toon("M_hair_sheen", [R["hair"][1], R["hair"][2]], (0.93,))
    make_toon("M_red", R["red"][1:], (0.26, 0.90))                 # crimson / base / coral
    make_toon("M_red_rim", R["red"][1:], (0.26, 0.90), rim=True)   # bow + sleeves
    make_toon("M_red_under", R["red"][:2], (0.35,))               # violet / crimson (undersides)
    make_toon("M_red_inner", R["red"][1:3], (0.15,))              # collar inner face (lighter)
    make_toon("M_leather", R["leather"], (0.18, 0.86))
    make_toon("M_dark", R["dark"], (0.25,))
    make_toon("M_steel", R["steel"], (0.3, 0.92))
    make_toon("M_pink", PALETTE["roles"]["scarf"], (0.25, 0.965))   # pink[1] base, rare skin[2] lit edge
    make_toon("M_purple", R["purple"], (), flat=True)
    # flat decals (face)
    make_toon("M_eye_dark", [R["eye"][0]], (), flat=True)
    make_toon("M_eye_light", [R["eye"][1]], (), flat=True)
    make_toon("M_ink", [OUTLINE_HEX], (), flat=True)
    make_toon("M_glint", [R["steel"][2]], (), flat=True)
    make_toon("M_blush", [R["pink"][0]], (), flat=True)
    make_toon("M_mouth", [R["skin"][0]], (), flat=True)
    make_toon("M_red_flat", [R["red"][2]], (), flat=True)   # tsuka diamonds
    make_toon("M_steel0_flat", [R["steel"][0]], (), flat=True)   # sprite blade spine half
    make_toon("M_steel1_flat", [R["steel"][1]], (), flat=True)   # sprite guard + kagi
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
        self.w = []     # per-vertex weight dict (bone -> weight) or None
        self.wfn = None  # current weight function p -> dict, applied in add_vert

    def add_vert(self, p, tag=None, w=None):
        self.v.append(V(p))
        self.tags.append(tag)
        if w is None and self.wfn is not None:
            w = self.wfn(V(p))
        self.w.append(w)
        return len(self.v) - 1

    def apply_weights(self, ob):
        """Write analytic per-vertex weights (normalised) into vertex groups."""
        groups = {}
        for i, d in enumerate(self.w):
            if not d:
                continue
            tot = sum(max(0.0, x) for x in d.values())
            if tot <= 0:
                continue
            for b, x in d.items():
                x = max(0.0, x) / tot
                if x < 0.005:
                    continue
                if b not in groups:
                    groups[b] = ob.vertex_groups.new(name=b)
                groups[b].add([i], x, "REPLACE")

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
        if any(self.w):
            self.apply_weights(ob)
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


# idle: blade down, back and out to her left, ~30 deg off the leg line
# rest/idle: blade straight out to her left and 50 deg down (best single direction over the 8 iso
# yaws, see NOTES.md); per-direction idle overrides for E/W live in rig["idle_sword_dir"]
SWORD_DIR = V((math.cos(math.radians(28)), 0.0, -math.sin(math.radians(28))))
GUARD_Y = 0.10          # katana mesh local: guard plane along +Y from its grip origin
KATANA_OFF = 0.15       # round 2: mesh shifted along the blade so the left hand holds the POMMEL end
                        # (the tsuka no longer runs up through the forearm/sleeve)
IDLE_SWORD_DIR = {"E": (90.0, 22.0), "W": (67.5, 28.0)}   # (azimuth from +X toward +Y, down) deg
BLADE_LEN = 1.45
HANDLE_LEN = 0.45
SHEATH_HEAD = V((0.27, -0.30, 1.02))
SHEATH_DIR = V((0.10, 0.94, -0.33)).normalized()


def scarf_points(side):
    """Rest curve of the scarf ribbon (from the back of the collar): splays out to her side,
    S-curve, drifting slightly toward her right (-X) as in refs/1."""
    s = 1 if side == "L" else -1
    drift = -0.07
    return [V((0.10 * s, 0.21, 1.93)),
            V((0.24 * s, 0.34, 1.83)),
            V((0.40 * s + drift * 0.3, 0.46, 1.67)),
            V((0.50 * s + drift * 0.6, 0.56, 1.47)),
            V((0.47 * s + drift, 0.64, 1.27)),
            V((0.55 * s + drift * 1.4, 0.73, 1.10))]


def define_skeleton():
    BONES.clear()
    bone("root", (0, 0, 0), (0, 0.45, 0), None, deform=False)
    bone("cog", (0, 0.0, 0.92), (0, 0.35, 0.92), "root", deform=False)
    bone("hips", (0, 0, 0.92), (0, 0, 1.12), "cog")
    bone("spine", (0, 0, 1.12), (0, 0, 1.38), "hips", connect=True)
    bone("chest", (0, 0, 1.38), (0, 0, 1.72), "spine", connect=True)
    bone("neck", (0, 0, 1.72), (0, 0, 1.88), "chest", connect=True)
    bone("head", (0, 0, 1.88), (0, 0, 2.75), "neck", connect=True)
    bone("bun", (0, 0.16, 2.70), (0, 0.30, 3.05), "head")
    bone("bow", (-0.14, 0.04, 2.90), (-0.14, 0.04, 3.16), "bun")
    for side in ("L", "R"):
        s = 1 if side == "L" else -1
        sh_in, sj, el, wr, ht = arm_points(side)
        bone(f"shoulder.{side}", sh_in, sj, "chest")
        bone(f"upper_arm.{side}", sj, el, f"shoulder.{side}", connect=True)
        bone(f"forearm.{side}", el, wr, f"upper_arm.{side}", connect=True)
        bone(f"hand.{side}", wr, ht, f"forearm.{side}", connect=True)
        # sleeve cuff tip: from wrist to lowest cuff point (hangs down and back)
        bone(f"sleeve.{side}", wr + V((0, 0.02, 0)), wr + V((0.05 * s, 0.10, -0.30)), f"forearm.{side}")
        # arm IK controls (FK by default: prop ik_arm.<side> = 0)
        bone(f"hand_ik.{side}", wr, ht, "cog", deform=False)
        bone(f"elbow_pole.{side}", el + V((0.10 * s, 0.55, 0)), el + V((0.10 * s, 0.70, 0)), "cog",
             deform=False)
        hip, kn, an, toe = leg_points(side)
        ball = V((0.14 * s, -0.11, 0.035))
        tip = V((0.14 * s, -0.215, 0.03))
        heel = V((0.14 * s, 0.075, 0.0))
        bone(f"thigh.{side}", hip, kn, "hips")
        # half-rotation helpers (Copy Rotation 0.5 from the limb): spread the joint bend over
        # two blend zones so raised arms / high knees don't collapse (TA round 1)
        bone(f"thigh_help.{side}", hip, hip.lerp(kn, 0.25), "hips")
        bone(f"upper_arm_help.{side}", sj, sj.lerp(el, 0.28), f"shoulder.{side}")
        bone(f"shin.{side}", kn, an, f"thigh.{side}", connect=True)
        bone(f"foot.{side}", an, ball, f"shin.{side}", connect=True)
        bone(f"toe.{side}", ball, tip, f"foot.{side}", connect=True)
        # leg IK controls (IK by default: prop ik_leg.<side> = 1)
        #   foot_ctrl (heel pivot on the floor) > toe_pivot (ball) > foot_ik (ankle, = foot bone)
        bone(f"foot_ctrl.{side}", heel, heel + V((0, -0.30, 0)), "root", deform=False)
        bone(f"toe_pivot.{side}", V((ball.x, ball.y, 0.0)), V((ball.x, ball.y + 0.12, 0.0)),
             f"foot_ctrl.{side}", deform=False)
        bone(f"foot_ik.{side}", an, ball, f"toe_pivot.{side}", deform=False)
        bone(f"knee_pole.{side}", kn + V((0.02 * s, -0.75, 0)), kn + V((0.02 * s, -0.90, 0)), "root",
             deform=False)
        # scarf chains (5 bones) from the back of the collar
        p = scarf_points(side)
        par = "neck"
        for i in range(len(p) - 1):
            nm = f"scarf.{side}.{i + 1:03d}"
            bone(nm, p[i], p[i + 1], par, connect=(i > 0))
            par = nm
    # skirt: 2-bone chains front and sides, 4-bone chain at the back (skirt.B + tail chain)
    bone("skirt.F", (0, -0.22, 1.04), (0, -0.36, 0.82), "hips")
    bone("skirt.F.001", (0, -0.36, 0.82), (0, -0.47, 0.60), "skirt.F", connect=True)
    for side, s in (("L", 1), ("R", -1)):
        bone(f"skirt.{side}", (0.27 * s, 0, 1.04), (0.42 * s, 0.03, 0.78), "hips")
        bone(f"skirt.{side}.001", (0.42 * s, 0.03, 0.78), (0.55 * s, 0.08, 0.52), f"skirt.{side}", connect=True)
        bone(f"skirt.{side}.002", (0.55 * s, 0.08, 0.52), (0.60 * s, 0.15, 0.28), f"skirt.{side}.001",
             connect=True)
    bone("skirt.B", (0, 0.22, 1.04), (0, 0.38, 0.82), "hips")
    bone("skirt.tail.001", (0, 0.38, 0.82), (0, 0.50, 0.62), "skirt.B", connect=True)
    bone("skirt.tail.002", (0, 0.50, 0.62), (0, 0.60, 0.42), "skirt.tail.001", connect=True)
    bone("skirt.tail.003", (0, 0.60, 0.42), (0, 0.68, 0.24), "skirt.tail.002", connect=True)
    # sword: head at the left-hand grip, Y along the blade, Z = edge direction
    sh_in, sj, el, wr, ht = arm_points("L")
    grip = wr.lerp(ht, 0.5)
    edge = V((0, 0, -1)) - SWORD_DIR * V((0, 0, -1)).dot(SWORD_DIR)
    bone("sword", grip, grip + SWORD_DIR * (KATANA_OFF + GUARD_Y + BLADE_LEN), "hand.L", roll=edge.normalized(),
         deform=True)
    # right-hand grip point on the tsuka (next to the guard; the left hand slides to the pommel)
    # used as the IK target of hand_ik.R when prop two_hand = 1
    sx, sy, sz = sword_axes()
    gR = grip + sy * (KATANA_OFF + GUARD_Y - 0.12) - sz * 0.085
    bone("sword_grip.R", gR, gR + sz * 0.20, "sword", roll=-sx, deform=False)
    # alternative sword parents (Copy Transforms targets, influence 0 by default)
    edge_s = V((0, 0, 1)) - SHEATH_DIR * V((0, 0, 1)).dot(SHEATH_DIR)
    bone("sheath", SHEATH_HEAD, SHEATH_HEAD + SHEATH_DIR * (GUARD_Y + BLADE_LEN), "hips",
         roll=edge_s.normalized(), deform=True)


def sword_axes():
    y = SWORD_DIR.normalized()
    z = V((0, 0, -1)) - y * V((0, 0, -1)).dot(y)
    z.normalize()
    x = y.cross(z).normalized()
    return x, y, z


def _driver_prop(owner, path, rig, prop, expr="var", index=-1):
    fc = owner.driver_add(path, index) if index >= 0 else owner.driver_add(path)
    d = fc.driver
    d.type = "SCRIPTED"
    var = d.variables.new()
    var.name = "var"
    var.type = "SINGLE_PROP"
    var.targets[0].id_type = "OBJECT"
    var.targets[0].id = rig
    var.targets[0].data_path = f'["{prop}"]'
    d.expression = expr
    return fc


def _set_prop(rig, name, val, desc, lo=0.0, hi=1.0):
    rig[name] = val
    try:
        ui = rig.id_properties_ui(name)
        ui.update(min=lo, max=hi, soft_min=lo, soft_max=hi, description=desc)
    except Exception:
        pass


def _local_rot_sign(rig, bname, axis, probe_dir):
    """+1 if rotating pose bone `bname` positively about local `axis` moves its tail along
    probe_dir (world), else -1."""
    pb = rig.pose.bones[bname]
    pb.rotation_mode = "XYZ"
    bpy.context.view_layer.update()
    t0 = pb.tail.copy()
    e = [0.0, 0.0, 0.0]
    e["XYZ".index(axis)] = math.radians(20)
    pb.rotation_euler = e
    bpy.context.view_layer.update()
    t1 = pb.tail.copy()
    pb.rotation_euler = (0, 0, 0)
    pb.rotation_mode = "QUATERNION"
    bpy.context.view_layer.update()
    return 1 if (t1 - t0).dot(V(probe_dir)) > 0 else -1


def _follow(rig, owner, target, axis_from, axis_to, rng_from, rng_to, name):
    """Transformation constraint: local rotation of `target` about axis_from in [rng_from]
    maps (clamped) to local rotation of `owner` about axis_to in [rng_to], added on top."""
    c = rig.pose.bones[owner].constraints.new("TRANSFORM")
    c.name = name
    c.target = rig
    c.subtarget = target
    c.target_space = "LOCAL"
    c.owner_space = "LOCAL"
    c.map_from = "ROTATION"
    c.map_to = "ROTATION"
    c.use_motion_extrapolate = False
    a, b = rng_from
    setattr(c, f"from_min_{axis_from.lower()}_rot", math.radians(a))
    setattr(c, f"from_max_{axis_from.lower()}_rot", math.radians(b))
    for ax in "xyz":
        setattr(c, f"map_to_{ax}_from", axis_from.upper())
    a2, b2 = rng_to
    setattr(c, f"to_min_{axis_to.lower()}_rot", math.radians(a2))
    setattr(c, f"to_max_{axis_to.lower()}_rot", math.radians(b2))
    try:
        c.mix_mode_rot = "ADD"
    except Exception:
        pass
    return c


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
    # IK control bones copy the roll of the bones they drive (so rest = identity)
    for side in ("L", "R"):
        eb[f"hand_ik.{side}"].roll = eb[f"hand.{side}"].roll
        eb[f"foot_ik.{side}"].roll = eb[f"foot.{side}"].roll
    bpy.ops.object.mode_set(mode="OBJECT")
    arm.display_type = "STICK"
    for pb in ob.pose.bones:
        pb.rotation_mode = "QUATERNION"

    # ---------------- custom props (keyable, drive constraint influences / shape keys)
    _set_prop(ob, "ik_leg.L", 1.0, "Leg IK (1) / FK (0)")
    _set_prop(ob, "ik_leg.R", 1.0, "Leg IK (1) / FK (0)")
    _set_prop(ob, "ik_arm.L", 0.0, "Arm IK (1) / FK (0)")
    _set_prop(ob, "ik_arm.R", 0.0, "Arm IK (1) / FK (0)")
    _set_prop(ob, "two_hand", 0.0, "Right hand IK target bound to the tsuka (needs ik_arm.R = 1)")
    _set_prop(ob, "skirt_follow", 1.0, "Skirt panels follow thigh flexion (corrective)")

    # ---------------- leg IK
    for side in ("L", "R"):
        pb = ob.pose.bones[f"shin.{side}"]
        c = pb.constraints.new("IK")
        c.name = "IK"
        c.target = ob
        c.subtarget = f"foot_ik.{side}"
        c.pole_target = ob
        c.pole_subtarget = f"knee_pole.{side}"
        c.chain_count = 2
        c.use_stretch = False
        _driver_prop(c, "influence", ob, f"ik_leg.{side}")
        c = ob.pose.bones[f"foot.{side}"].constraints.new("COPY_ROTATION")
        c.name = "IK_rot"
        c.target = ob
        c.subtarget = f"foot_ik.{side}"
        _driver_prop(c, "influence", ob, f"ik_leg.{side}")
        # arm IK
        pb = ob.pose.bones[f"forearm.{side}"]
        c = pb.constraints.new("IK")
        c.name = "IK"
        c.target = ob
        c.subtarget = f"hand_ik.{side}"
        c.pole_target = ob
        c.pole_subtarget = f"elbow_pole.{side}"
        c.chain_count = 2
        c.use_stretch = False
        _driver_prop(c, "influence", ob, f"ik_arm.{side}")
        c = ob.pose.bones[f"hand.{side}"].constraints.new("COPY_ROTATION")
        c.name = "IK_rot"
        c.target = ob
        c.subtarget = f"hand_ik.{side}"
        _driver_prop(c, "influence", ob, f"ik_arm.{side}")
    for side in ("L", "R"):
        for hb, src in ((f"thigh_help.{side}", f"thigh.{side}"), (f"upper_arm_help.{side}", f"upper_arm.{side}")):
            c = ob.pose.bones[hb].constraints.new("COPY_ROTATION")
            c.name = "half_rot"
            c.target = ob
            c.subtarget = src
            c.target_space = "LOCAL"
            c.owner_space = "LOCAL"
            c.influence = 0.5
    # two-handed grip: hand_ik.R snaps to the tsuka grip point
    c = ob.pose.bones["hand_ik.R"].constraints.new("COPY_TRANSFORMS")
    c.name = "to_tsuka"
    c.target = ob
    c.subtarget = "sword_grip.R"
    _driver_prop(c, "influence", ob, "two_hand")

    # sword parent switching
    pb = ob.pose.bones["sword"]
    c = pb.constraints.new("COPY_TRANSFORMS")
    c.name = "to_sheath"
    c.target = ob
    c.subtarget = "sheath"
    c.influence = 0.0
    ob["sword_mode"] = ("hand.L (default, bible: katana in her LEFT hand). Constraint 'to_sheath' influence=1 "
                        "sheathes it. Two-handed: two_hand=1 + ik_arm.R=1 puts the right hand on sword_grip.R "
                        "(child of sword, next to the guard); the left hand always holds the pommel end.")

    # pole angles: numeric search so that IK at rest reproduces the rest pose exactly
    calibrate_poles(ob)

    # ---------------- skirt corrective follow (thigh flexion -> skirt panels)
    # sign probes: which local X direction swings the knee forward (-Y) / the panel forward
    fl = {s: _local_rot_sign(ob, f"thigh.{s}", "X", (0, -1, 0)) for s in ("L", "R")}
    pf = {b: _local_rot_sign(ob, b, "X", (0, -1, 0)) for b in ("skirt.F", "skirt.B", "skirt.L", "skirt.R",
                                                                "skirt.F.001")}
    cons = []

    def fmap(sign_from, amount):
        # map the half-range of thigh rotation that means "forward" (sign_from) to `amount` deg
        return ((0, 100), (0, amount)) if sign_from > 0 else ((-100, 0), (amount, 0))
    for s in ("L", "R"):
        # front panel: forward flex of either thigh pushes it forward (back swing ignored)
        fr, to = fmap(fl[s], 55 * pf["skirt.F"])
        cons.append(_follow(ob, "skirt.F", f"thigh.{s}", "X", "X", fr, to, f"follow_{s}"))
        # back panel: backward swing pushes it back
        fr, to = fmap(-fl[s], -45 * pf["skirt.B"])
        cons.append(_follow(ob, "skirt.B", f"thigh.{s}", "X", "X", fr, to, f"follow_{s}"))
        # side panel follows its own thigh flexion both ways (about half)
        k = 50 * fl[s] * pf[f"skirt.{s}"]
        cons.append(_follow(ob, f"skirt.{s}", f"thigh.{s}", "X", "X", (-100, 100), (-k, k), "follow_flex"))
    for c in cons:
        _driver_prop(c, "influence", ob, "skirt_follow")
    return ob


def calibrate_poles(rig):
    """Find pole_angle for each IK so the chain does not twist at rest (deterministic search)."""
    sc = bpy.context.scene
    for side in ("L", "R"):
        for upper, lower, prop in ((f"thigh.{side}", f"shin.{side}", f"ik_leg.{side}"),
                                   (f"upper_arm.{side}", f"forearm.{side}", f"ik_arm.{side}")):
            c = rig.pose.bones[lower].constraints["IK"]
            old = rig[prop]
            rig[prop] = 1.0
            # drivers are not re-evaluated reliably during the search: drive influence directly
            fc = rig.animation_data.drivers.find(f'pose.bones["{lower}"].constraints["IK"].influence')
            if fc:
                fc.mute = True
            c.influence = 1.0
            ref = (rig.data.bones[upper].matrix_local.copy(), rig.data.bones[lower].matrix_local.copy())

            def err(a):
                c.pole_angle = math.radians(a)
                bpy.context.view_layer.update()
                e = 0.0
                for bn, M in zip((upper, lower), ref):
                    Mp = rig.pose.bones[bn].matrix
                    for i in range(3):
                        e += (V((Mp[0][i], Mp[1][i], Mp[2][i])) - V((M[0][i], M[1][i], M[2][i]))).length
                return e
            best = min(range(-180, 180, 2), key=err)
            lo, hi = best - 2.0, best + 2.0
            for _ in range(30):     # golden-section refine
                m1, m2 = lo + (hi - lo) * 0.382, lo + (hi - lo) * 0.618
                if err(m1) < err(m2):
                    hi = m2
                else:
                    lo = m1
            a = (lo + hi) / 2
            res = err(a)
            c.pole_angle = math.radians(a)
            rig[prop] = old
            if fc:
                fc.mute = False
            c.influence = old
            bpy.context.view_layer.update()
            print(f"[rig] pole {lower}: {a:.2f} deg  residual {res:.5f}")
            c.pole_angle = math.radians(a)



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


def chain_w(p, names, joints, blends):
    """Rigid-segment weights with smooth blends at the joints.
    names: n bones in chain order; joints: n-1 (point, axis) between names[i] and names[i+1];
    blends: n-1 half-widths.  w_i = S_{i-1} - S_i, S_j = smoothstep over the signed distance
    of p past joint j along its axis."""
    S = [1.0]
    for (J, ax), b in zip(joints, blends):
        sd = (V(p) - V(J)).dot(V(ax).normalized())
        S.append(smoothstep(-b, b, sd))
    S.append(0.0)
    # enforce monotone (bent chains)
    for i in range(1, len(S) - 1):
        S[i] = min(S[i], S[i - 1])
    return {n: max(0.0, S[i] - S[i + 1]) for i, n in enumerate(names)}


def arm_chain_w(p, side, blend_sh=0.06, blend_el=0.07, hand=False):
    sh_in, sj, el, wr, ht = arm_points(side)
    a = (el - sj).normalized()
    f = (wr - el).normalized()
    names = [f"shoulder.{side}", f"upper_arm_help.{side}", f"upper_arm.{side}", f"forearm.{side}"]
    joints = [(sj - a * 0.07, a), (sj + a * 0.05, a), (el, (a + f).normalized())]
    bl = [blend_sh * 0.6, blend_sh * 0.6, blend_el]
    if hand:
        names.append(f"hand.{side}")
        joints.append((wr, f))
        bl.append(0.03)
    return chain_w(p, names, joints, bl)


def leg_chain_w(p, side, blend_hip=0.07, blend_knee=0.06):
    hip, kn, an, toe = leg_points(side)
    a = (kn - hip).normalized()
    b = (an - kn).normalized()
    # the hip "joint" plane is tilted: inner thigh joins lower (crotch), outer higher
    s = 1 if side == "L" else -1
    hp = hip + V((0, 0, 0.04))
    nrm = (V((0.35 * s, 0, -1))).normalized()
    return chain_w(p, ["hips", f"thigh_help.{side}", f"thigh.{side}", f"shin.{side}", f"foot.{side}"],
                   [(hp + nrm * 0.06 * -1, nrm), (hp + nrm * 0.08, nrm), (kn, (a + b).normalized()),
                    (an + V((0, 0, -0.02)), V((0, 0, -1)))],
                   [blend_hip * 0.6, blend_hip * 0.6, blend_knee, 0.04])


# ----------------------------------------------------------------------------
# modifiers / finishing
# ----------------------------------------------------------------------------
def finish(ob, rig, subsurf=1, thick=0.0, thick_offset=-1.0, shell_mat_offset=0, outline_px=1.5,
           outline=True, dqs=False):
    ob.parent = rig
    m = ob.modifiers.new("Armature", "ARMATURE")
    m.object = rig
    if dqs:
        try:
            m.use_deform_preserve_volume = True
        except Exception:
            pass
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
        fx = 1 - 0.38 * k ** 2.0      # softer anime jaw, keeps chibi cheek fullness (round 2)
        fy = 1 - 0.18 * k ** 2
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

    def torso_w(p):
        d = chain_w(p, ["hips", "spine", "chest", "neck"],
                    [(V((0, 0, 1.12)), V((0, 0, 1))), (V((0, 0, 1.38)), V((0, 0, 1))),
                     (V((0, 0, 1.74)), V((0, 0, 1)))], [0.08, 0.10, 0.05])
        # outer upper chest/shoulder area follows the shoulder bones a little
        for side, s in (("L", 1), ("R", -1)):
            k = smoothstep(0.12, 0.24, p.x * s) * smoothstep(1.50, 1.62, p.z)
            if k > 0:
                d[f"shoulder.{side}"] = k * 0.6
                for b in ("chest", "spine"):
                    d[b] = d.get(b, 0) * (1 - k * 0.6)
        return d
    mb.wfn = torso_w
    rows = [[body_pt(2 * PI * i / nu, z) for i in range(nu)] for z in zs]
    ids = mb.grid(rows, "M_skin", close_u=True)
    mb.cap(ids[0], V((0, 0, 0.82)), "M_skin", flip=True)
    ob = mb.build("body_torso", coll)
    finish(ob, rig, subsurf=2, outline_px=1.2)
    objs.append(ob)

    # neck
    mb = MB()
    mb.wfn = lambda p: chain_w(p, ["chest", "neck", "head"], [(V((0, 0, 1.73)), V((0, 0, 1))),
                                                             (V((0, 0, 1.90)), V((0, 0, 1)))], [0.04, 0.04])
    path = [V((0, 0.01, 1.70)), V((0, 0.0, 1.85)), V((0, -0.01, 2.0))]
    tube(mb, path, lambda t, ph: (0.085, 0.08), "M_skin", nseg=14, cap0=False, cap1=False)
    ob = mb.build("neck", coll)
    finish(ob, rig, subsurf=1, outline=False)

    # head
    mb = MB()
    ellipsoid(mb, HEAD_C, HEAD_R, "M_skin", nu=40, nv=28, deform=head_deform)
    ob = mb.build("head", coll)
    finish(ob, rig, subsurf=2, outline_px=1.5)
    weight_rigid(ob, "head")
    head_ob = ob
    # ears: small, flat against the head, mostly tucked under the side hair (only the lobe shows)
    mb = MB()
    for s in (1, -1):
        ellipsoid(mb, (0.425 * s, 0.05, 2.17), (0.022, 0.05, 0.068), "M_skin", nu=12, nv=8,
                  rot=Euler((0.15, 0.30 * s, 0)).to_matrix())
    ob = mb.build("ears", coll)
    finish(ob, rig, subsurf=1, outline_px=0.8)
    weight_rigid(ob, "head")

    # arms (bare skin; the detached sleeves cover the forearm)
    for side in ("L", "R"):
        sh_in, sj, el, wr, ht = arm_points(side)
        s = 1 if side == "L" else -1
        mb = MB()
        mb.wfn = lambda p, side=side: arm_chain_w(p, side, blend_sh=0.10, blend_el=0.08)
        a_dir = (el - sj).normalized()
        path = catmull([sj - a_dir * 0.07, sj, el, wr], 16)

        def rad(t, ph):
            r = lerp(0.098, 0.056, smoothstep(0.0, 1.0, t))
            r *= 1 + 0.06 * math.sin(PI * t)
            return (r, r * 0.92)
        tube(mb, path, rad, "M_skin", nseg=16)
        # round deltoid cap (sits on the shoulder, slightly above the joint) -> soft round shoulder;
        # weighted (almost) rigidly to the upper arm so it rotates as a unit instead of collapsing
        mb.wfn = lambda p, side=side: {f"upper_arm.{side}": 0.85, f"shoulder.{side}": 0.15}
        ellipsoid(mb, sj + V((0.005 * s, 0.0, 0.015)), (0.10, 0.092, 0.088), "M_skin", nu=18, nv=12)
        ob = mb.build(f"arm.{side}", coll)
        finish(ob, rig, subsurf=2, outline_px=1.2, dqs=True)
        # hand: mitten in fingerless glove, skin fingertips
        mb = MB()
        mb.wfn = lambda p, side=side, wr=wr, ht=ht: chain_w(
            p, [f"forearm.{side}", f"hand.{side}"], [(wr, (ht - wr).normalized())], [0.03])
        hdir = (ht - wr).normalized()
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

    # legs: tapered thigh 0.30 H -> knee 0.18-0.20 H -> soft calf -> ankle 0.12-0.13 H
    for side in ("L", "R"):
        hip, kn, an, toe = leg_points(side)
        s = 1 if side == "L" else -1
        mb = MB()
        mb.wfn = lambda p, side=side: leg_chain_w(p, side, blend_hip=0.11)
        top = hip + V((-0.03 * s, 0, 0.12))
        path = catmull([top, hip, kn + V((-0.008 * s, 0, 0)), an, an + V((0, 0.0, -0.06))], 26)

        def lr(t, ph, s=s):
            z = lerp(1.07, 0.15, t)
            # outer side (cos(ph) * N ~ +X side) slightly fuller on the thigh, inner fuller on the calf
            if z > 0.52:
                u = smoothstep(0.52, 0.98, z)
                r = lerp(0.090, 0.152, u ** 0.8)
            else:
                r = lerp(0.056, 0.090, smoothstep(0.23, 0.52, z))
                r *= 1 + 0.16 * math.exp(-((z - 0.415) / 0.075) ** 2)   # calf
                r *= 1 - 0.05 * math.exp(-((z - 0.51) / 0.03) ** 2)     # soft knee dip
            return (r, r * 0.93)
        tube(mb, path, lr, "M_skin", nseg=18, cap0=False)
        ob = mb.build(f"leg.{side}", coll)
        finish(ob, rig, subsurf=2, outline_px=1.2, dqs=True)
        # foot (skin) inside the sandal
        mb = MB()
        hip_, kn_, an_, toe_ = leg_points(side)
        ballp = V((0.14 * s, -0.11, 0.035))
        mb.wfn = lambda p, side=side, ballp=ballp: chain_w(
            p, [f"shin.{side}", f"foot.{side}", f"toe.{side}"],
            [(V((0, 0, 0.25)), V((0, 0, -1))), (ballp, V((0, -1, 0)))], [0.03, 0.03])
        heel = V((0.14 * s, 0.07, 0.17))
        ball = V((0.14 * s, -0.12, 0.035))
        tip = V((0.14 * s, -0.20, 0.03))
        path = catmull([heel + V((0, 0.02, 0.01)), heel, an.lerp(ball, 0.5), ball, tip], 12)

        def fr(t, ph):
            w = lerp(0.052, 0.058, t) * (1 - 0.6 * smoothstep(0.85, 1.0, t))
            h = lerp(0.05, 0.03, t) * (1 - 0.6 * smoothstep(0.85, 1.0, t))
            return (h, w)
        tube(mb, path, fr, "M_skin", nseg=12, up=V((0, 0, 1)))
        ob = mb.build(f"foot.{side}", coll)
        finish(ob, rig, subsurf=1, outline_px=1.0)
    return head_ob


# ----------------------------------------------------------------------------
# FACE decals (projected onto the evaluated head surface)
# ----------------------------------------------------------------------------
EXPRESSIONS = {
    # lid: upper-lid drop (fraction of eye height) | slant: + = inner corner lower (frown)
    # low: lower-lid raise | mouth: (half width, curve (+ smile), open)
    "calm":  dict(lid=0.20, slant=0.0, low=0.0, mouth=(0.032, 0.004, 0.0)),
    "wide":  dict(lid=0.0, slant=0.0, low=0.0, mouth=(0.030, 0.010, 0.012)),
    "frown": dict(lid=0.30, slant=0.30, low=0.06, mouth=(0.030, -0.006, 0.0)),
    "smile": dict(lid=0.16, slant=-0.10, low=0.22, mouth=(0.040, 0.016, 0.006)),
    "hurt":  dict(lid=0.58, slant=-0.25, low=0.30, mouth=(0.036, -0.010, 0.016)),
}
EYE_Z = 2.165       # round 2: lowered 0.035 H and enlarged so the eyes clear the bangs in iso
EYE_X = 0.212
EYE_RX, EYE_RZ = 0.116, 0.142


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

    def gen(E):
        """Build the decal mesh for expression E.  Topology is identical for every expression
        (only positions change) so the variants become shape keys."""
        mb = MB()
        lid_cache = {}

        def lid_top(s, x):
            # upper lid line (z) for the eye on side s at x
            cx = EYE_X * s
            u = clamp((x - cx) * s / EYE_RX, -1, 1)          # -1 inner .. +1 outer
            top = EYE_Z + EYE_RZ * math.sqrt(max(0.0, 1 - (u * 0.92) ** 2))
            drop = E["lid"] * 2 * EYE_RZ
            drop += E["slant"] * 2 * EYE_RZ * 0.5 * (1 - u) * 0.5
            return top - drop

        def lid_bot(s, x):
            cx = EYE_X * s
            u = clamp((x - cx) * s / EYE_RX, -1, 1)
            bot = EYE_Z - EYE_RZ * math.sqrt(max(0.0, 1 - (u * 0.92) ** 2))
            return bot + E["low"] * 2 * EYE_RZ * (0.6 + 0.4 * u)

        def ellipse(cx, cz, rx, rz, off, mat, n=20, rings=4, side=None):
            def P(x, z):
                if side is not None:
                    z = min(z, lid_top(side, x) - 0.002)
                    z = max(z, min(lid_bot(side, x), lid_top(side, x) - 0.004))
                return proj(x, z, off)
            center = mb.add_vert(P(cx, cz))
            prev = None
            for k in range(1, rings + 1):
                f = k / rings
                ring = []
                for i in range(n):
                    a = 2 * PI * i / n
                    ring.append(mb.add_vert(P(cx + math.cos(a) * rx * f, cz + math.sin(a) * rz * f)))
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

        for s in (1, -1):   # s=+1 her left (screen right in front view)
            cx = EYE_X * s
            ellipse(cx, EYE_Z, EYE_RX, EYE_RZ, 0.004, "M_glint", n=24, side=s)          # sclera
            ellipse(cx + 0.004 * s, EYE_Z - 0.006, 0.092, 0.134, 0.008, "M_eye_dark", n=24, side=s)
            ellipse(cx + 0.004 * s, EYE_Z - 0.050, 0.076, 0.082, 0.011, "M_eye_light", n=20, side=s)
            ellipse(cx + 0.004 * s, EYE_Z + 0.004, 0.036, 0.055, 0.014, "M_ink", n=16, side=s)  # pupil
            ellipse(cx - 0.030 * s, EYE_Z + 0.030, 0.030, 0.034, 0.018, "M_glint", n=12, side=s)
            ellipse(cx + 0.040 * s, EYE_Z - 0.068, 0.013, 0.013, 0.018, "M_glint", n=8, side=s)
            # upper lash: follows the lid line, heavier at the outer corner
            N = 16
            A, B = [], []
            for i in range(N + 1):
                u = i / N            # 0 inner -> 1 outer
                x = cx + s * lerp(-EYE_RX * 1.02, EYE_RX * 1.12, u)
                zt = lid_top(s, x)
                th = lerp(0.024, 0.052, u ** 1.4)
                A.append((x, zt + 0.014 + 0.004 * u))
                B.append((x, zt - th * 0.55))
            band(A, B, 0.022, "M_ink")
            # lash flick at the outer corner
            xo = cx + s * EYE_RX * 1.08
            zo = lid_top(s, xo)
            band([(xo, zo + 0.012), (xo + s * 0.045, zo + 0.040)],
                 [(xo + s * 0.006, zo - 0.032), (xo + s * 0.05, zo + 0.012)], 0.022, "M_ink")
            # blush (pink[0], no ink lines around it)
            ellipse(0.292 * s, 1.995, 0.074, 0.030, 0.006, "M_blush", n=16, rings=2)
        # mouth (small) and tiny nose dot
        hw, cv, op = E["mouth"]
        mz = 1.958
        band([(-hw, mz + cv), (0.0, mz), (hw, mz + cv)],
             [(-hw, mz + cv - 0.012), (0.0, mz - 0.012 - op), (hw, mz + cv - 0.012)], 0.006, "M_mouth")
        ellipse(0.0, 2.035, 0.010, 0.007, 0.005, "M_mouth", n=8, rings=1)
        return mb

    base = gen(EXPRESSIONS["calm"])
    ob = base.build("face_decals", coll)
    ob.shape_key_add(name="Basis", from_mix=False)
    for name, E in EXPRESSIONS.items():
        if name == "calm":
            continue
        mbx = gen(E)
        assert len(mbx.v) == len(base.v)
        sk = ob.shape_key_add(name=name, from_mix=False)
        for i, p in enumerate(mbx.v):
            sk.data[i].co = p
        _set_prop(rig, f"expr_{name}", 0.0, f"Face expression '{name}' (shape key on face_decals)")
        _driver_prop(sk, "value", rig, f"expr_{name}")
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


def hair_lock(mb, phi0, z0, phi1, z1, width, out0, out1, sweep=0.0, n=12, bulge=0.018, mat="M_hair"):
    """Chunky pointed anime lock lying on the head: root (phi0,z0) -> tip (phi1,z1).
    Cross-section is convex (5 verts across); width tapers to a point."""
    rows = []
    for k in range(n + 1):
        t = k / n
        tt = smoothstep(0, 1, t)
        phi = lerp(phi0, phi1, t) + sweep * math.sin(PI * 0.5 * t)
        z = lerp(z0, z1, t ** 0.9)
        out = lerp(out0, out1, t) + 0.035 * math.sin(PI * min(1.0, t * 1.15)) * (1 - 0.5 * t)
        w = width * (1 - t ** 1.7) ** 0.8 + 0.003
        row = []
        for j, a in enumerate((-1.0, -0.5, 0.0, 0.5, 1.0)):
            dphi = a * w / max(0.2, HEAD_R.x * math.cos(math.asin(clamp((z - HEAD_C.z) / HEAD_R.z, -0.95, 0.95))))
            o = out + bulge * (1 - a * a) * (1 - t * 0.6)
            row.append(head_surf(phi + dphi, z, o))
        rows.append(row)
    mb.grid(rows, mat)


def build_hair(rig, coll):
    # skull cap (fuller than the head: adds outer hair volume at the sides/back)
    mb = MB()
    C = HEAD_C + V((0, 0.025, 0.025))
    Rr = V((0.515, 0.50, 0.51))
    nu, nv = 48, 30
    rows = []
    for j in range(0, nv + 1):
        th = PI * j / nv
        row = []
        for i in range(nu):
            ph = 2 * PI * i / nu
            p = V((math.sin(th) * math.sin(ph) * Rr.x, -math.sin(th) * math.cos(ph) * Rr.y,
                   math.cos(th) * Rr.z))
            # puff at the temples/back, tighter at the nape (hair pulled up)
            az = abs(math.atan2(p.x, -p.y))
            puff = 1 + 0.035 * math.sin(th) ** 2 * smoothstep(0.6, 1.6, az) * smoothstep(-0.1, 0.25, p.z)
            p = V((p.x * puff, p.y * puff, p.z))
            row.append(C + head_deform(p))
        rows.append(row)

    def keep(p):
        az = abs(math.degrees(math.atan2(p.x, -(p.y - 0.02))))  # 0 front .. 180 back
        if az < 50:
            zmin = 2.47
        elif az < 95:
            zmin = lerp(2.47, 2.26, smoothstep(50, 95, az))
        elif az < 125:
            zmin = lerp(2.26, 1.93, smoothstep(95, 125, az))
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

    # angel-ring sheen band: thin arcs that follow the skull (replaces the round-1 crown disc)
    mb = MB()
    arcs = [(-150, -95), (-80, -30), (-20, 25), (35, 85), (100, 150), (160, 200)]
    for a0, a1 in arcs:
        n = 10
        rows = []
        for k in range(n + 1):
            t = k / n
            a = math.radians(lerp(a0, a1, t))
            back = (1 - math.cos(a)) / 2
            zc = 2.585 - 0.04 * back               # ring tilts down toward the back (skull follows)
            w = 0.022 * math.sin(PI * t) ** 0.6 + 0.002
            sx = 1.0 + 0.03                         # just outside the cap
            row = []
            for dz in (-w, 0.0, w):
                p = cap_point(C, Rr, a, zc + dz, 0.028)
                row.append(p)
            rows.append(row)
        mb.grid(rows, "M_hair_sheen")
    ob = mb.build("hair_sheen", coll)
    finish(ob, rig, subsurf=1, outline=False)
    weight_rigid(ob, "head")
    ob.visible_shadow = False

    # bangs, back layer: short heavy fringe, hem just above the brow, swept to HER RIGHT (-X)
    mb = MB()
    nu, nv = 41, 8
    rows = []
    for j in range(nv + 1):
        v = j / nv
        row = []
        for i in range(nu):
            u = i / (nu - 1)
            phi = lerp(-1.42, 1.42, u)
            nl = 9
            saw = abs(((u * nl + 0.3) % 1.0) - 0.5) * 2   # 1 at lock gaps, 0 at lock tips
            side = abs(phi) / 1.42
            zb = lerp(2.37, 2.30, smoothstep(0.55, 1.0, side)) + 0.085 * saw ** 0.8
            zt = lerp(2.66, 2.52, smoothstep(0.2, 1.0, side))
            z = lerp(zt, zb, v)
            phs = phi - 0.14 * v * (1 - side * 0.6)   # sweep to her right (-X)
            # volume bulges mid-way, tucks back in at the hem so the eyes stay clear in iso
            out = 0.014 + 0.062 * math.sin(PI * min(1.0, v * 1.05)) ** 0.8 + 0.012 * (1 - saw) * v
            row.append(head_surf(phs, z, out))
        rows.append(row)
    mb.grid(rows, "M_hair", flip=False)
    # front layer: chunky pointed locks (2-3 long ones), swept to her right
    LOCKS = [  # phi_root, z_root, phi_tip, z_tip, width, sweep
        (-1.05, 2.62, -1.20, 2.25, 0.085, -0.10),
        (-0.55, 2.68, -0.60, 2.275, 0.10, -0.10),   # long lock over her right eye (outer)
        (-0.15, 2.70, -0.28, 2.33, 0.095, -0.12),
        (0.22, 2.70, 0.07, 2.35, 0.09, -0.12),
        (0.60, 2.68, 0.50, 2.29, 0.10, -0.08),      # long lock over her left eye (outer)
        (1.00, 2.62, 1.02, 2.26, 0.085, -0.04),
    ]
    for (p0, z0, p1, z1, w, sw) in LOCKS:
        hair_lock(mb, p0, z0, p1, z1, w, 0.072, 0.03, sweep=sw)
    ob = mb.build("bangs", coll)
    finish(ob, rig, subsurf=2, thick=0.022, thick_offset=1, outline_px=1.4)
    weight_rigid(ob, "head")

    # face-framing strands: in front of the ears (pulled back so the profile reads in E/W),
    # reaching the jaw, with volume and a pointed tip
    mb = MB()
    for s in (1, -1):
        hair_lock(mb, 1.30 * s, 2.46, 1.20 * s, 1.86, 0.06, 0.05, 0.035, sweep=-0.06 * s, n=14,
                  bulge=0.02)
        # short side lock behind it (adds side volume, hides the top of the ear)
        hair_lock(mb, 1.55 * s, 2.44, 1.60 * s, 2.15, 0.07, 0.05, 0.04, sweep=0.05 * s, n=8, bulge=0.02)
    ob = mb.build("hair_strands", coll)
    finish(ob, rig, subsurf=1, thick=0.02, thick_offset=0, outline_px=1.0)
    weight_rigid(ob, "head")

    # bun: high messy loop bun (crown, set back 0.25 H, ~0.48 H diameter, top at +0.35 H)
    mb = MB()
    BC = V((0, 0.25, 2.88))

    def bun_def(p):
        a = math.atan2(p.y, p.x)
        b = math.atan2(p.z, math.hypot(p.x, p.y))
        bump = 1 + 0.10 * math.sin(3 * a + 1.0) * math.cos(2 * b) + 0.06 * math.sin(5 * b + a)
        return p * bump
    ellipsoid(mb, BC, (0.27, 0.26, 0.24), "M_hair", nu=24, nv=16, deform=bun_def,
              rot=Euler((-0.35, 0, 0)).to_matrix())
    loop = [BC + Euler((-0.35, 0.25, 0)).to_matrix() @ V((math.cos(a) * 0.23, math.sin(a) * 0.22,
                                                          0.03 * math.sin(2 * a)))
            for a in [2 * PI * k / 24 for k in range(25)]]
    tube(mb, loop, lambda t, ph: (0.068, 0.052), "M_hair", nseg=10, cap0=False, cap1=False)
    loop2 = [BC + Euler((0.5, -0.6, 0.4)).to_matrix() @ V((math.cos(a) * 0.205, math.sin(a) * 0.195, 0.0))
             for a in [2 * PI * k / 24 for k in range(25)]]
    tube(mb, loop2, lambda t, ph: (0.05, 0.04), "M_hair", nseg=8, cap0=False, cap1=False)
    for (d, l) in ((V((0.3, 0.2, 1.0)), 0.18), (V((-0.5, 0.5, 0.7)), 0.15), (V((0.6, 0.6, 0.3)), 0.13)):
        d = d.normalized()
        base = BC + d * 0.21
        tip = base + d * l + V((0, 0, 0.04))
        mid = base.lerp(tip, 0.5) + V((0.03, 0, 0.03))
        tube(mb, catmull([base, mid, tip], 6), lambda t, ph: 0.022 * (1 - t) + 0.002, "M_hair", nseg=6)
    ob = mb.build("bun", coll)
    finish(ob, rig, subsurf=1, outline_px=1.6)
    weight_rigid(ob, "bun")
    # sheen arc on the bun (bible v2: required)
    mb = MB()
    Rb = Euler((-0.35, 0, 0)).to_matrix()
    for a0, a1 in ((-60, 40), (70, 150), (175, 250)):
        rows = []
        n = 8
        for k in range(n + 1):
            t = k / n
            a = math.radians(lerp(a0, a1, t))
            w = 0.03 * math.sin(PI * t) ** 0.6 + 0.003
            row = []
            for db in (-w, 0, w):
                el = 0.62 + db / 0.24
                d = V((math.cos(a) * math.cos(el), math.sin(a) * math.cos(el), math.sin(el)))
                q = V((d.x * 0.27, d.y * 0.26, d.z * 0.24))
                row.append(BC + Rb @ (bun_def(q) * 1.10))
            rows.append(row)
        mb.grid(rows, "M_hair_sheen")
    ob = mb.build("bun_sheen", coll)
    finish(ob, rig, subsurf=1, outline=False)
    weight_rigid(ob, "bun")
    ob.visible_shadow = False


def cap_point(C, Rr, az, z, out):
    """Point on the hair-cap ellipsoid at azimuth az (0 = front) and height z."""
    sz = clamp((z - C.z) / Rr.z, -0.999, 0.999)
    ce = math.sqrt(1 - sz * sz)
    p = V((Rr.x * ce * math.sin(az), -Rr.y * ce * math.cos(az), Rr.z * sz))
    p = head_deform(p)
    n = V((p.x / Rr.x ** 2, p.y / Rr.y ** 2, p.z / Rr.z ** 2)).normalized()
    return C + p + n * out


# ----------------------------------------------------------------------------
# BOW
# ----------------------------------------------------------------------------
def build_bow(rig, coll):
    """Big red bow at the base of the bun, on HER RIGHT side.  Two stiff bunny-ear loops tilted
    back ~25 deg (faces toward camera-up) and splayed so both loops read as two ears from every
    iso direction; dark (violet/crimson) knot and loop openings as value breaks.  Width <= 0.85 H."""
    mb = MB()
    K = V((-0.14, 0.04, 2.90))      # front-right base of the (round-2 larger) bun
    lean = math.radians(25)
    for s in (1, -1):
        d = V((0.76 * s, 0.12, 0.64)).normalized()
        # loop face normal: toward the front and up (lean), splayed outward per side
        n0 = V((0, -math.cos(lean), math.sin(lean)))
        n0 = Matrix.Rotation(math.radians(-22 * s), 3, "Z") @ n0
        n0 = (n0 - d * n0.dot(d)).normalized()
        W = n0.cross(d).normalized()
        L = 0.42
        n = 14
        path = [K + d * (L * k / (n - 1)) + n0 * 0.025 * math.sin(PI * k / (n - 1)) for k in range(n)]

        def rr(t, ph):
            w = 0.16 * (math.sin(PI * clamp(t, 0, 1) ** 0.62)) ** 0.75 + 0.012
            th = 0.05 * math.sin(PI * clamp(t, 0, 1) ** 0.7) + 0.012
            return (w, th)
        tube(mb, path, rr, "M_red_rim", nseg=16, up=W, phase=0.0)
        # loop opening: darker inner fold on the front face, near the knot side
        c = K + d * (L * 0.42) + n0 * 0.052
        R3 = Matrix((W, d, n0)).transposed()
        ellipsoid(mb, c, (0.068, 0.11, 0.012), "M_red_under", nu=14, nv=6, rot=R3)
        # back face too (seen from N / NW / NE)
        c2 = K + d * (L * 0.42) - n0 * 0.052
        ellipsoid(mb, c2, (0.06, 0.10, 0.012), "M_red_under", nu=14, nv=6, rot=R3)
    # tails (short, V-cut)
    for s in (1, -1):
        d = V((0.40 * s, 0.25, -0.88)).normalized()
        base = K + V((0.02 * s, -0.01, -0.03))
        pts = catmull([base, base + d * 0.13 + V((0.03 * s, 0, 0)), base + d * 0.26], 8)
        rows = []
        for k, p in enumerate(pts):
            t = k / (len(pts) - 1)
            w = lerp(0.03, 0.065, t)
            sd = V((1, 0.25 * s, 0)).normalized()
            a = p - sd * w
            b = p + sd * w
            if k == len(pts) - 1:
                rows.append([a, p - d * 0.05, b])
            else:
                rows.append([a, p, b])
        mb.grid(rows, "M_red_rim")
    # knot: dark value break between the loops
    ellipsoid(mb, K + V((0, -0.01, 0)), (0.07, 0.065, 0.075), "M_red_under", nu=12, nv=8)
    ob = mb.build("bow", coll)
    finish(ob, rig, subsurf=1, thick=0.0, outline_px=1.6)
    s = ob.modifiers.new("Thickness", "SOLIDIFY")
    s.thickness = 0.02
    s.offset = 0
    ob.modifiers.move(len(ob.modifiers) - 1, 2)
    weight_rigid(ob, "bow")


# ----------------------------------------------------------------------------
# COLLAR, choker, bodice, chest flower, cord
# ----------------------------------------------------------------------------
def build_upper_costume(rig, coll):
    # stiff flared funnel collar, open in a wide V at the front.  Round 2 (AD): capped at
    # 0.3 H above the base; the front edges stop at jaw level so chin + mouth stay visible,
    # and the flare goes outward (~0.9 H wide at the top) instead of up.
    mb = MB()
    nv, nu = 10, 40
    rows = []
    for j in range(nv + 1):
        v = j / nv
        row = []
        gap = math.radians(lerp(16, 76, v ** 1.0))
        for i in range(nu):
            u = i / (nu - 1)
            th = lerp(gap, 2 * PI - gap, u)
            back = (1 - math.cos(th)) / 2
            ztop = 1.77 + 0.21 * back ** 0.75
            z = lerp(1.67, ztop, v)
            fl = v ** 1.7
            rx = lerp(0.215, 0.45, fl)
            ry = lerp(0.175, 0.39, fl)
            yo = lerp(0.0, 0.05, v) * back
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
        wts = []
        for k, p in enumerate(path):
            t = k / (len(path) - 1)
            row = []
            for i in range(nseg):
                ph = 2 * PI * i / nseg
                radial = N[k] * math.cos(ph) + B[k] * math.sin(ph)
                # round 2: slight taper under the top band, bell flare starts sooner
                r = lerp(0.112, 0.100, smoothstep(0.0, 0.14, t))
                r = lerp(r, 0.29, smoothstep(0.26, 1.0, t) ** 1.2)
                # soft folds (start mid-forearm)
                r *= 1 + 0.075 * smoothstep(0.35, 1.0, t) * math.sin(5 * ph + 0.5)
                # back/outer side of the bell hangs longer (kimono furi)
                hang = 0.5 + 0.5 * radial.dot(V((0.25 * s, 0.85, -0.2)).normalized())
                ext = smoothstep(0.6, 1.0, t) * (-0.10 + 0.34 * hang ** 1.4)
                q = p + radial * r + T[k] * ext + V((0, 0, -1)) * ext * 0.6
                row.append(q)
                # analytic weights by ring parameter (no chest bleed, cuffs on the tip bone)
                wu = 1 - smoothstep(0.24, 0.42, t)
                wsl = smoothstep(0.62, 0.95, t) * (0.35 + 0.65 * hang) * 0.85
                wf = max(0.0, 1 - wu - wsl)
                wts.append({f"upper_arm.{side}": wu, f"forearm.{side}": wf, f"sleeve.{side}": wsl})
            rows.append(row)
        mb = MB()
        mb.grid(rows, "M_red_rim", close_u=True, flip=False)
        mb.w = wts
        ob = mb.build(f"sleeve.{side}", coll)
        ob.data.materials.append(MATS["M_red_under"])
        finish(ob, rig, subsurf=1, thick=0.022, thick_offset=-1, shell_mat_offset=1, outline_px=1.4, dqs=True)
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
                off = rot @ V((math.cos(a) * 0.078, 0, math.sin(a) * 0.078))
                ellipsoid(mb, fc + off, (0.075, 0.024, 0.044), "M_red", nu=8, nv=6,
                          rot=rot @ Euler((0, -a, 0)).to_matrix())
            ellipsoid(mb, fc + outer * 0.02, (0.034, 0.028, 0.034), "M_purple", nu=8, nv=6)
            # lacing zig-zag down the sleeve front-outer face
            pts = []
            for k in range(7):
                t = 0.12 + k * 0.05
                pp = sj + a_dir * (0.14 + k * 0.035)
                ang = 0.35 if k % 2 == 0 else -0.35
                rd = (Matrix.Rotation(ang, 3, a_dir) @ outer).normalized()
                pts.append(pp + rd * 0.128)
            tube(mb, pts, lambda t, ph: 0.016, "M_purple", nseg=5)
            # dangling ribbon
            rb = catmull([fc + V((0, -0.01, -0.03)), fc + V((-0.05, -0.04, -0.22)),
                          fc + V((-0.03, -0.03, -0.42))], 12)
            rows = [[p - V((0.03, 0.0, 0)), p + V((0.03, 0, 0))] for p in rb]
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



def skirt_surface_fn(skirt_ob):
    """Returns f(theta, z) -> (point, outward normal) on the rest skirt_outer surface."""
    me = skirt_ob.data
    bvh = BVHTree.FromPolygons([v.co.copy() for v in me.vertices], [tuple(p.vertices) for p in me.polygons])

    def f(th, z):
        d = V((math.sin(th), -math.cos(th), 0))
        hit = bvh.ray_cast(V((0, 0, z)) + d * 2.0, -d)
        if hit[0] is None:
            return body_pt(th, z, 0.2), d
        n = V(hit[1])
        if n.dot(d) < 0:
            n = -n
        return V(hit[0]), n.normalized()
    return f


def build_belt_pouch(rig, coll, skirt_ob):
    """Low hip belt, a real-volume pouch hanging from the belt at the front of her RIGHT hip
    (sits on the skirt surface, tucked under the corset edge) and two hanging strap tabs."""
    surf = skirt_surface_fn(skirt_ob)
    mb = MB()
    mb.wfn = lambda p: {"hips": 1.0, "skirt.F": 1.6 * smoothstep(0.97, 0.80, p.z) if p.y < -0.15 else 0.0,
                        "skirt.R": 1.2 * smoothstep(0.97, 0.80, p.z) if p.x < -0.2 else 0.0}
    belt = [body_pt(2 * PI * k / 40, 0.985 - 0.03 * math.sin(2 * PI * k / 40), 0.06) for k in range(41)]
    tube(mb, belt, lambda t, ph: (0.013, 0.032), "M_leather", nseg=8, cap0=False, cap1=False)
    tab_w = mb.wfn
    mb.wfn = lambda p: {"hips": 0.6, "skirt.R": 0.2, "skirt.F": 0.2}     # pouch moves as one piece
    # pouch: rounded box on the skirt surface, flap + steel stud, strap loop up to the belt
    th = -0.62
    sp, sn = surf(th, 0.90)
    side = V((0, 0, 1)).cross(sn).normalized()
    up = sn.cross(side).normalized()
    R3 = Matrix((side, sn, up)).transposed()     # local X = side, Y = out, Z = up
    pc = sp + sn * 0.055

    def rbox(p):     # superellipse-ish rounding of an ellipsoid -> soft box
        x, y, z = p
        k = 0.55
        return V((math.copysign(abs(x) ** k, x) * 0.085 ** (1 - k),
                  math.copysign(abs(y) ** k, y) * 0.05 ** (1 - k),
                  math.copysign(abs(z) ** k, z) * 0.075 ** (1 - k)))
    ellipsoid(mb, pc, (0.085, 0.05, 0.075), "M_leather", nu=16, nv=10, rot=R3, deform=rbox)
    # flap (lighter edge comes from the leather[2] highlight band)
    ellipsoid(mb, pc + R3 @ V((0, 0.035, 0.035)), (0.088, 0.03, 0.05), "M_leather", nu=12, nv=8, rot=R3)
    box(mb, pc + R3 @ V((0, 0.065, 0.02)), (0.026, 0.014, 0.03), "M_steel", rot=R3)
    # strap loop from the belt to the pouch top
    bt = body_pt(th, 0.975, 0.07)
    tube(mb, catmull([bt, bt.lerp(pc + up * 0.075, 0.5) + sn * 0.02, pc + up * 0.07], 6),
         lambda t, ph: (0.012, 0.028), "M_leather", nseg=6, up=sn)
    # two hanging strap tabs (tassets) over the skirt front, on the skirt surface
    mb.wfn = tab_w
    for th_t in (-0.28, 0.30):
        pts = []
        for k in range(9):
            t = k / 8
            z = lerp(0.985, 0.70, t)
            p_, n_ = surf(th_t + 0.04 * t * (1 if th_t > 0 else -1), z)
            pts.append(p_ + n_ * 0.022)
        rows = []
        for k, p_ in enumerate(pts):
            t = k / (len(pts) - 1)
            w = 0.052 * (1 - 0.45 * smoothstep(0.7, 1, t))
            sd = V((math.cos(th_t), math.sin(th_t), 0))
            rows.append([p_ - sd * w, p_, p_ + sd * w])
            if k == len(pts) - 1:
                rows[-1][1] = p_ + V((0, 0, -0.04))     # pointed tab end
        mb.grid(rows, "M_leather")
        p_, n_ = surf(th_t, 0.90)
        box(mb, p_ + n_ * 0.04, (0.06, 0.016, 0.026), "M_steel",
            rot=look_rot(n_, V((0, 0, 1))))
    ob = mb.build("belt_pouch", coll)
    finish(ob, rig, subsurf=1, thick=0.0, outline_px=1.2)
    s = ob.modifiers.new("Thickness", "SOLIDIFY")
    s.thickness = 0.02
    ob.modifiers.move(len(ob.modifiers) - 1, 2)


# ----------------------------------------------------------------------------
# SKIRT (asymmetric layered petal skirt) + shorts + thigh strap
# ----------------------------------------------------------------------------
def petal(theta_deg, centers, width):
    """0..1 pointed (linear-to-the-tip) petal profile around the given centres."""
    v = 0.0
    for c in centers:
        d = abs(((theta_deg - c + 180) % 360) - 180)
        v = max(v, max(0.0, 1 - d / width))
    return v


def skirt_weights(p, top=1.04):
    th = math.atan2(p.x, -p.y)  # 0 front, +pi/2 her left (+X)
    depth = clamp((top - p.z) / 0.8, 0, 1)
    c, s_ = math.cos(th), math.sin(th)
    wF = max(0.0, c) ** 2
    wB = max(0.0, -c) ** 2
    wL = max(0.0, s_) ** 2
    wR = max(0.0, -s_) ** 2
    k = smoothstep(0.0, 0.35, depth)
    d = {"hips": (1 - k) * 1.5 + 0.01}
    zj = lambda z: (V((0, 0, z)), V((0, 0, -1)))
    F = chain_w(p, ["skirt.F", "skirt.F.001"], [zj(0.82)], [0.07])
    Ls = chain_w(p, ["skirt.L", "skirt.L.001", "skirt.L.002"], [zj(0.78), zj(0.52)], [0.07, 0.07])
    Rs = chain_w(p, ["skirt.R", "skirt.R.001", "skirt.R.002"], [zj(0.78), zj(0.52)], [0.07, 0.07])
    Bs = chain_w(p, ["skirt.B", "skirt.tail.001", "skirt.tail.002", "skirt.tail.003"],
                 [zj(0.82), zj(0.62), zj(0.42)], [0.07, 0.07, 0.07])
    Ls = {b.replace("skirt.L", "skirt.L"): w for b, w in Ls.items()}
    for grp, wa in ((F, wF), (Ls, wL), (Rs, wR), (Bs, wB)):
        for b, w in grp.items():
            d[b] = d.get(b, 0) + w * wa * k
    # thigh follow on the front/side panels (legs don't poke through in strides)
    d["thigh.L"] = 0.35 * k * max(0.0, s_ + 0.3) * max(0.0, c + 0.35)
    d["thigh.R"] = 0.35 * k * max(0.0, -s_ + 0.3) * max(0.0, c + 0.35)
    return d


SKIRT_TOP = 1.05
SKIRT_LOW = 0.22


def skirt_radius(z, scale=1.0):
    """Bell down to ~0.5 H, then the long tails hang nearly straight (petal tails, not a dome)."""
    rx0, ry0, yo0 = torso_profile(SKIRT_TOP)
    zb = 0.50
    u = clamp((SKIRT_TOP - z) / (SKIRT_TOP - zb), 0, 1.0) ** 0.75
    rx = lerp(rx0 + 0.045, 0.53, u)
    ry = lerp(ry0 + 0.05, 0.47, u)
    if z < zb:
        k = (zb - z) / (zb - SKIRT_LOW)
        rx += 0.035 * k
        ry += 0.05 * k
    return rx * scale, ry * scale, u


def build_skirt(rig, coll):
    TOP = SKIRT_TOP
    # outer layer: knee-length front panel with a wide slit on HER LEFT, 4 long pointed petal
    # tails at the sides/back separated by clear gaps (violet underside shows in the gaps)
    TAILS = (116, 152, 208, 244)
    mb = MB()
    mb.wfn = skirt_weights
    nu, nv = 96, 16
    rows = []
    slit = 38.0
    for j in range(nv + 1):
        v = j / nv
        row = []
        gap = lerp(0.0, 56.0, v ** 1.2)
        for i in range(nu):
            u = i / (nu - 1)
            thd = lerp(slit + gap * 0.5, slit + 360 - gap * 0.5, u)
            th = math.radians(thd)
            back = (1 - math.cos(th)) / 2
            pt = petal(thd, TAILS, 15)
            base = 0.60 + 0.03 * smoothstep(0.25, 0.9, back)        # gaps stay high -> legs show
            hem = base - (base - SKIRT_LOW) * pt ** 0.85              # pointed tails to 0.22 H
            z = lerp(TOP, hem, v)
            rx, ry, uu = skirt_radius(z)
            fold = 1 + 0.045 * uu * math.sin(8 * th + 0.4)
            curl = 1 + 0.12 * pt * smoothstep(0.50, 0.22, z)          # tail tips flick outward
            p = V((math.sin(th) * rx * fold * curl, -math.cos(th) * ry * fold * curl, z))
            p.y += 0.10 * back * uu ** 1.5         # tails drift back
            row.append(p)
        rows.append(row)
    mb.grid(rows, "M_red", flip=True)
    ob = mb.build("skirt_outer", coll)
    ob.data.materials.append(MATS["M_red_under"])
    finish(ob, rig, subsurf=1, thick=0.022, thick_offset=-1, shell_mat_offset=1, outline_px=1.6)
    skirt_ob = ob

    # under layer: violet/crimson, back half only, shorter (hem ~0.46 H, small points to 0.38 H)
    # so the shins + heels stay visible below it in N / NE / NW
    mb = MB()
    mb.wfn = skirt_weights
    nu, nv = 56, 14
    rows = []
    for j in range(nv + 1):
        v = j / nv
        row = []
        for i in range(nu):
            u = i / (nu - 1)
            thd = lerp(80, 280, u)
            th = math.radians(thd)
            back = (1 - math.cos(th)) / 2
            pt = petal(thd, (130, 180, 230), 18)
            hem = 0.50 - 0.05 * back - 0.08 * pt ** 0.85
            z = lerp(TOP - 0.02, hem, v)
            rx, ry, uu = skirt_radius(z, 0.93)
            fold = 1 + 0.04 * uu * math.sin(7 * th + 1.3)
            p = V((math.sin(th) * rx * fold, -math.cos(th) * ry * fold, z))
            p.y += 0.08 * back * uu ** 1.5
            row.append(p)
        rows.append(row)
    mb.grid(rows, "M_red_under", flip=True)
    ob = mb.build("skirt_under", coll)
    ob.data.materials.append(MATS["M_red_under"])
    finish(ob, rig, subsurf=1, thick=0.018, thick_offset=-1, shell_mat_offset=0, outline_px=1.4)

    # black shorts
    mb = MB()
    def shorts_w(p):
        dL = leg_chain_w(p, "L", blend_hip=0.11)
        dR = leg_chain_w(p, "R", blend_hip=0.11)
        f = smoothstep(-0.07, 0.07, p.x)       # centre seam blends both sides (no tearing)
        return {"hips": f * dL["hips"] + (1 - f) * dR["hips"] + 1e-4,
                "thigh_help.L": f * dL["thigh_help.L"], "thigh_help.R": (1 - f) * dR["thigh_help.R"],
                "thigh.L": f * dL["thigh.L"], "thigh.R": (1 - f) * dR["thigh.R"]}
    mb.wfn = shorts_w
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
    finish(ob, rig, subsurf=1, outline_px=1.2, dqs=True)

    # thigh strap + small pouch (HER LEFT thigh)
    mb = MB()
    hip, kn, an, toe = leg_points("L")
    ax = (kn - hip).normalized()
    c = hip.lerp(kn, 0.66)
    rn = 0.118
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
    return skirt_ob


# ----------------------------------------------------------------------------
# SANDALS (chibi heeled, criss-cross ankle straps)
# ----------------------------------------------------------------------------
def build_shoes(rig, coll):
    """Black heeled sandals: dark sole + heel post, closed toe vamp, criss-cross instep straps,
    two ankle rings with an X between them (front), skin ankle visible above."""
    for side in ("L", "R"):
        s = 1 if side == "L" else -1
        x = 0.14 * s
        mb = MB()
        ballp = V((x, -0.11, 0.035))
        mb.wfn = lambda p, side=side, ballp=ballp: chain_w(
            p, [f"shin.{side}", f"foot.{side}", f"toe.{side}"],
            [(V((0, 0, 0.19)), V((0, 0, -1))), (ballp, V((0, -1, 0)))], [0.03, 0.025])
        # sole (follows the foot slope)
        sole = catmull([V((x, 0.10, 0.145)), V((x, 0.04, 0.125)), V((x, -0.06, 0.05)), V((x, -0.15, 0.012)),
                        V((x, -0.215, 0.012))], 12)

        def sr(t, ph):
            w = 0.064 * (1 - 0.55 * smoothstep(0.9, 1.0, t)) * (1 - 0.3 * smoothstep(0.1, 0.0, t))
            return (0.02, w)
        tube(mb, sole, sr, "M_dark", nseg=10)
        # heel post (tapered stiletto, shortened for chibi stability)
        tube(mb, [V((x, 0.08, 0.14)), V((x, 0.074, 0.07)), V((x, 0.068, 0.0))],
             lambda t, ph: lerp(0.036, 0.02, t), "M_dark", nseg=10)
        # closed toe vamp
        ellipsoid(mb, (x, -0.165, 0.038), (0.066, 0.068, 0.046), "M_dark", nu=14, nv=8)
        # criss-cross instep straps (vamp sides -> opposite side of the ankle)
        for k in (1, -1):
            a = V((x + 0.058 * k, -0.105, 0.045))
            m = V((x, -0.06, 0.115))
            b = V((x - 0.066 * k, 0.0, 0.205))
            tube(mb, catmull([a, m + V((0, -0.035, 0)), b], 8), lambda t, ph: (0.016, 0.009), "M_dark",
                 nseg=6, up=V((0, -1, 0.4)))
        # ankle rings + X between them on the front
        for zc in (0.205, 0.275):
            ring = [V((x + math.sin(a) * 0.072, 0.035 - math.cos(a) * 0.07, zc))
                    for a in [2 * PI * k / 22 for k in range(23)]]
            tube(mb, ring, lambda t, ph: (0.014, 0.008), "M_dark", nseg=6, cap0=False, cap1=False)
        for k in (1, -1):
            a = V((x + 0.05 * k, 0.035 - 0.055, 0.205))
            b = V((x - 0.05 * k, 0.035 - 0.055, 0.275))
            tube(mb, [a, a.lerp(b, 0.5) + V((0, -0.018, 0)), b], lambda t, ph: (0.012, 0.007), "M_dark",
                 nseg=6, up=V((0, -1, 0)))
        # heel counter strap (back)
        tube(mb, catmull([V((x, 0.10, 0.15)), V((x, 0.105, 0.18)), V((x, 0.10, 0.205))], 5),
             lambda t, ph: (0.008, 0.014), "M_dark", nseg=6, up=V((0, 1, 0)))
        ob = mb.build(f"shoe.{side}", coll)
        finish(ob, rig, subsurf=1, outline_px=1.2)


# ----------------------------------------------------------------------------
# SCARF ribbons
# ----------------------------------------------------------------------------
def build_scarf(rig, coll):
    """Two pink ribbons from the back of the collar: splay out to either side of the spine
    (the bare-back strip stays visible), gentle S-curve + twist, taper, swallowtail notch.
    Weighted along the 5-bone scarf chains."""
    for side in ("L", "R"):
        s = 1 if side == "L" else -1
        pts = scarf_points(side)
        names = [f"scarf.{side}.{i + 1:03d}" for i in range(len(pts) - 1)]
        joints = [(pts[i + 1], (pts[i + 2] - pts[i]).normalized()) for i in range(len(pts) - 2)]
        mb = MB()
        root_j = (pts[0] + (pts[1] - pts[0]) * 0.15, (pts[1] - pts[0]).normalized())
        mb.wfn = lambda p, names=names, joints=joints, root_j=root_j: chain_w(
            p, ["neck"] + names, [root_j] + joints, [0.03] + [0.06] * len(joints))
        path = catmull([pts[0] + V((-0.05 * s, -0.05, 0.03))] + pts, 34)
        T, N, B = frames_along(path, V((0, 1, 0)))
        rows = []
        n = len(path)
        for k, p in enumerate(path):
            t = k / (n - 1)
            w = 0.062 * (1 + 0.12 * math.sin(PI * t)) * (1 - 0.25 * smoothstep(0.6, 1.0, t))
            # width axis: horizontal-ish (tangential around the body), twisted along the ribbon
            radial = V((p.x, p.y - 0.05, 0)).normalized()
            wd0 = V((0, 0, 1)).cross(radial)
            tw = s * (0.15 + 0.9 * t) + 0.35 * math.sin(2 * PI * t)
            q = Quaternion(T[k], tw)
            wd = q @ wd0
            wd = (wd - T[k] * wd.dot(T[k])).normalized()
            a, b = p - wd * w, p + wd * w
            if k == n - 1:     # swallowtail notch
                rows.append([a + T[k] * 0.03, p.lerp(a, 0.5), p - T[k] * 0.07, p.lerp(b, 0.5), b + T[k] * 0.03])
            else:
                rows.append([a, p.lerp(a, 0.5), p, p.lerp(b, 0.5), b])
        mb.grid(rows, "M_pink")
        ob = mb.build(f"scarf.{side}", coll)
        finish(ob, rig, subsurf=1, thick=0.012, thick_offset=0, outline_px=1.0)


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


def katana_sprite_mesh(mb):
    """Sprite-render katana (bible section 3): blade >= 2 px from every view, flat 2-tone
    (steel[0] spine half / steel[2] edge half, no per-facet shading -> no dashed look),
    chunky red/black banded tsuka (>= 2x4 px), big crescent kagi (>= 3 px)."""
    g0 = GUARD_Y
    L = BLADE_LEN
    n = 16
    nseg = 8
    rings = []
    for k in range(n + 1):
        t = k / n
        y = g0 + 0.03 + t * (L - 0.03)
        sori = -0.07 * t * t
        tip = smoothstep(0.86, 1.0, t)
        rz = 0.066 * (1 - 0.15 * t) * (1 - 0.85 * tip) + 0.004
        rx = 0.056 * (1 - 0.15 * t) * (1 - 0.85 * tip) + 0.004
        rings.append([(V((math.cos(2 * PI * i / nseg) * rx, y, sori + math.sin(2 * PI * i / nseg) * rz)),
                       math.sin(2 * PI * i / nseg)) for i in range(nseg)])
    ids = [[mb.add_vert(p) for p, _ in r] for r in rings]
    for k in range(n):
        for i in range(nseg):
            a, b = ids[k][i], ids[k][(i + 1) % nseg]
            c, d = ids[k + 1][(i + 1) % nseg], ids[k + 1][i]
            zs = rings[k][i][1] + rings[k][(i + 1) % nseg][1]
            # one flat shade (GD round 1): no internal tone boundary -> no dashed blade at 1x.
            # The pipeline outline adds the steel[0] lit-side edge, giving the 2-tone read.
            mb.add_face((a, b, c, d), "M_glint", smooth=False)
    mb.cap(ids[0], V((0, g0 + 0.03, 0)), "M_glint", flip=True, smooth=False)
    mb.cap(ids[-1], rings[-1][0][0] * 0 + V((0, g0 + L, -0.07)), "M_glint", flip=False, smooth=False)
    # guard bar + kagi (flat steel[1]); bar 0.25 H, hook ~0.24 H across
    bar_len = 0.25
    box(mb, (0, g0, -bar_len * 0.30), (0.06, 0.06, bar_len), "M_steel1_flat")
    end_z = -bar_len * 0.30 + bar_len / 2
    hook_r = 0.115
    cc = V((0, g0, end_z + hook_r))
    arc = []
    for k in range(17):
        a = math.radians(lerp(-140, 105, k / 16))
        arc.append(cc + V((0, math.sin(a) * hook_r * (1.15 if a < 0 else 1.0), -math.cos(a) * hook_r)))

    def hr(t, ph):
        a = lerp(-140, 105, t)
        mid = 1 - abs(a + 10) / 130
        return (0.035, 0.012 + 0.03 * max(0.0, mid) ** 0.7)
    tube(mb, arc, hr, "M_steel1_flat", nseg=8, up=V((1, 0, 0)))
    # tsuka: chunky, red/black bands
    hy0, hy1 = g0 - 0.03, g0 - HANDLE_LEN
    nb = 7
    for k in range(nb):
        y0 = lerp(hy0, hy1, k / nb)
        y1 = lerp(hy0, hy1, (k + 1) / nb)
        tube(mb, [V((0, y0, 0)), V((0, y1, 0))], lambda t, ph: (0.056, 0.06),
             "M_red_flat" if k % 2 == 1 else "M_ink", nseg=10, up=V((0, 0, 1)), cap0=(k == 0), cap1=False,
             smooth=False)
    tube(mb, [V((0, hy1, 0)), V((0, hy1 - 0.045, 0))], lambda t, ph: (0.058, 0.062), "M_steel1_flat",
         nseg=10, up=V((0, 0, 1)), smooth=False)


def place_on_bone(ob, rig, bname, yoff=0.0):
    bmat = rig.data.bones[bname].matrix_local @ Matrix.Translation(V((0, yoff, 0)))
    ob.data.transform(bmat)
    ob.data.update()


def build_sword(rig, coll):
    mb = MB()
    katana_mesh(mb)
    ob = mb.build("katana", coll)
    place_on_bone(ob, rig, "sword", KATANA_OFF)
    finish(ob, rig, subsurf=0, outline_px=1.0)
    weight_rigid(ob, "sword")
    # sprite-render variant: blade 0.12 H wide (2 px), hook 0.18 H (3 px), bar 0.25 H
    mb = MB()
    katana_sprite_mesh(mb)
    ob2 = mb.build("katana_sprite", coll)
    place_on_bone(ob2, rig, "sword", KATANA_OFF)
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


POSE_PROPS = ["ik_leg.L", "ik_leg.R", "ik_arm.L", "ik_arm.R", "two_hand", "skirt_follow"] + \
    [f"expr_{n}" for n in EXPRESSIONS if n != "calm"]
PROP_DEFAULTS = {"ik_leg.L": 1.0, "ik_leg.R": 1.0, "ik_arm.L": 0.0, "ik_arm.R": 0.0, "two_hand": 0.0,
                 "skirt_follow": 1.0}


def capture_pose(rig):
    out = {}
    for pb in rig.pose.bones:
        q = pb.rotation_quaternion
        l = pb.location
        if abs(q.w - 1) > 1e-6 or l.length > 1e-6 or abs(q.x) + abs(q.y) + abs(q.z) > 1e-6:
            out[pb.name] = [round(q.w, 6), round(q.x, 6), round(q.y, 6), round(q.z, 6),
                            round(l.x, 6), round(l.y, 6), round(l.z, 6)]
    out["_props"] = {k: float(rig[k]) for k in POSE_PROPS}
    return out


def clear_pose(rig):
    for pb in rig.pose.bones:
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.location = (0, 0, 0)
        pb.scale = (1, 1, 1)
    for k in POSE_PROPS:
        rig[k] = PROP_DEFAULTS.get(k, 0.0)
    rig.update_tag()
    bpy.context.view_layer.update()


def set_props(rig, **kw):
    for k, v in kw.items():
        rig[k.replace("__", ".")] = float(v)
    rig.update_tag()
    bpy.context.view_layer.update()


def place_ctrl(rig, name, loc=None, yaw=0.0, pitch=0.0, roll=0.0, offset=None):
    """Put a control bone at armature-space `loc` (or rest + offset), rotated (deg) about the
    world Z (yaw), then its own X (pitch)."""
    bpy.context.view_layer.update()
    rest = rig.data.bones[name].matrix_local.copy()
    R3 = (Matrix.Rotation(math.radians(yaw), 3, "Z") @ Matrix.Rotation(math.radians(pitch), 3, "X")
          @ Matrix.Rotation(math.radians(roll), 3, "Y") @ rest.to_3x3())
    M = R3.to_4x4()
    t = V(loc) if loc is not None else rest.translation + V(offset or (0, 0, 0))
    M.translation = t
    rig.pose.bones[name].matrix = M
    bpy.context.view_layer.update()


def curve_chain(rig, names, axis, angles):
    """Successive world-axis rotations along a chain -> smooth curvature (no straight segments)."""
    for nm, a in zip(names, angles):
        rotate_world(rig, nm, axis, math.radians(a))


def scarf_names(side):
    return [f"scarf.{side}.{i:03d}" for i in range(1, 6)]


def sword_world_to_hand(rig, sword_M, slide=0.0):
    """hand.L armature-space matrix that puts the sword bone at sword_M when the sword bone is
    slid `slide` along its own Y relative to the hand (left hand toward the pommel)."""
    R_sh = rig.data.bones["hand.L"].matrix_local.inverted() @ rig.data.bones["sword"].matrix_local
    basis = Matrix.Translation(V((0, slide, 0)))
    return sword_M @ basis.inverted() @ R_sh.inverted()


def sword_matrix(head, ydir, edge_hint=V((0, 0, -1))):
    y = V(ydir).normalized()
    z = V(edge_hint) - y * V(edge_hint).dot(y)
    z.normalize()
    x = y.cross(z).normalized()
    M = Matrix((x, y, z)).transposed().to_4x4()
    M.translation = V(head)
    return M


def pose_two_hand(rig, handle_center, sdir, edge_hint=V((0, 0, -1)), elbow_out=0.45):
    """Both hands on the tsuka: left hand at the pommel end, right hand at the guard."""
    slide = 0.0
    # handle centre sits at sword-local y = KATANA_OFF + GUARD_Y - 0.22
    Msw = sword_matrix(V(handle_center) - V(sdir).normalized() * (KATANA_OFF + GUARD_Y - 0.22), sdir, edge_hint)
    Mh = sword_world_to_hand(rig, Msw, slide)
    set_props(rig, ik_arm__L=1, ik_arm__R=1, two_hand=1)
    pb = rig.pose.bones["hand_ik.L"]
    pb.matrix = Mh
    bpy.context.view_layer.update()
    for side, s in (("L", 1), ("R", -1)):
        el = rig.pose.bones[f"upper_arm.{side}"].tail
        place_ctrl(rig, f"elbow_pole.{side}", loc=V(el) + V((elbow_out * s, 0.5, -0.1)))
    bpy.context.view_layer.update()


def pose_feet(rig, side, loc, yaw=0.0, heel_lift=0.0, toe_lift=0.0):
    place_ctrl(rig, f"foot_ctrl.{side}", loc=loc, yaw=yaw)
    if heel_lift:
        # rotate around the ball (toe_pivot) -> heel comes up
        pb = rig.pose.bones[f"toe_pivot.{side}"]
        rotate_world(rig, f"toe_pivot.{side}", rig.pose.bones[f"foot_ctrl.{side}"].x_axis, math.radians(-heel_lift))
    if toe_lift:
        rotate_world(rig, f"foot_ctrl.{side}", rig.pose.bones[f"foot_ctrl.{side}"].x_axis, math.radians(toe_lift))


def aim_pole_knee(rig, side, fwd):
    kn = rig.pose.bones[f"thigh.{side}"].tail
    place_ctrl(rig, f"knee_pole.{side}", loc=V(kn) + V(fwd).normalized() * 0.8)


POSES = {}


def set_sword_dir(rig, az, de):
    """Aim the sword bone (character-local azimuth from +X toward +Y, and down angle, deg)."""
    bpy.context.view_layer.update()
    a, e = math.radians(az), math.radians(de)
    d = V((math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), -math.sin(e)))
    head = rig.pose.bones["sword"].matrix.translation.copy()
    rig.pose.bones["sword"].matrix = sword_matrix(head, d)
    bpy.context.view_layer.update()


def store_pose(rig, name):
    bpy.context.view_layer.update()
    POSES[name] = capture_pose(rig)
    # also as a 1-frame Action (pose library entry) with all bones + props keyed
    act = bpy.data.actions.new(f"pose_{name}")
    act.use_fake_user = True
    rig.animation_data.action = act
    for pb in rig.pose.bones:
        pb.keyframe_insert("location", frame=1, group=pb.name)
        pb.keyframe_insert("rotation_quaternion", frame=1, group=pb.name)
    for k in POSE_PROPS:
        rig.keyframe_insert(f'["{k}"]', frame=1, group="props")
    for fc in act_fcurves(act):
        for kp in fc.keyframe_points:
            kp.interpolation = "CONSTANT"
    rig.animation_data.action = None


def act_fcurves(act):
    try:
        return list(act.fcurves)
    except Exception:
        out = []
        for layer in act.layers:
            for strip in layer.strips:
                for cb in strip.channelbags:
                    out.extend(cb.fcurves)
        return out


def make_poses(rig):
    if rig.animation_data is None:
        rig.animation_data_create()
    # --- rest
    clear_pose(rig)
    store_pose(rig, "rest")

    # --- idle: relaxed, slight forward head tilt (more face pixels at 30 deg), weight on one hip
    clear_pose(rig)
    rotate_world(rig, "hips", (0, 1, 0), math.radians(2.5))
    rotate_world(rig, "chest", (0, 1, 0), math.radians(-3))
    rotate_world(rig, "head", (1, 0, 0), math.radians(-8))
    rotate_world(rig, "head", (0, 1, 0), math.radians(2))
    curve_chain(rig, scarf_names("L"), (0, 0, 1), [3, 4, 5, 5, 4])
    curve_chain(rig, scarf_names("R"), (0, 0, 1), [3, 4, 5, 5, 4])
    store_pose(rig, "idle")
    # per-direction idle variants (sword re-aimed so it projects out past the silhouette)
    for dname, (az, de) in IDLE_SWORD_DIR.items():
        bpy.context.view_layer.update()
        set_sword_dir(rig, az, de)
        store_pose(rig, f"idle_{dname}")
        rig.pose.bones["sword"].matrix_basis = Matrix.Identity(4)

    # --- sword_ready (refs/2): low, wide two-handed stance; blade forward and down
    clear_pose(rig)
    move(rig, "cog", (0.0, 0.04, -0.20))
    rotate_world(rig, "hips", (0, 0, 1), math.radians(18))
    rotate_world(rig, "spine", (1, 0, 0), math.radians(-14))
    rotate_world(rig, "chest", (1, 0, 0), math.radians(-8))
    rotate_world(rig, "chest", (0, 0, 1), math.radians(-14))
    rotate_world(rig, "head", (1, 0, 0), math.radians(12))
    rotate_world(rig, "head", (0, 0, 1), math.radians(-6))
    pose_feet(rig, "L", (0.58, -0.44, 0.0), yaw=-35)
    pose_feet(rig, "R", (-0.56, 0.38, 0.0), yaw=45, heel_lift=12)
    aim_pole_knee(rig, "L", (1.0, -0.8, 0))      # knees bend outward
    aim_pole_knee(rig, "R", (-1.0, -0.3, 0))
    pose_two_hand(rig, (0.14, -0.64, 0.92), (0.30, -0.82, -0.48), elbow_out=0.7)
    curve_chain(rig, scarf_names("L"), (0, 0, 1), [-12, -16, -18, -18, -14])
    curve_chain(rig, scarf_names("L"), (1, 0, 0), [-20, -12, -10, -8, -6])
    curve_chain(rig, scarf_names("R"), (0, 0, 1), [-10, -14, -18, -20, -16])
    curve_chain(rig, scarf_names("R"), (1, 0, 0), [-24, -14, -10, -8, -6])
    for side in ("L", "R"):
        rotate_world(rig, f"sleeve.{side}", (1, 0, 0), math.radians(-25))
    rotate_world(rig, "skirt.B", (1, 0, 0), math.radians(-14))
    curve_chain(rig, ["skirt.tail.001", "skirt.tail.002", "skirt.tail.003"], (1, 0, 0), [-10, -8, -6])
    set_props(rig, expr_frown=1)
    store_pose(rig, "sword_ready")

    # --- walk contact (left heel strike, right toe-off)
    clear_pose(rig)
    move(rig, "cog", (0, 0, -0.03))
    rotate_world(rig, "hips", (0, 0, 1), math.radians(-8))
    rotate_world(rig, "chest", (0, 0, 1), math.radians(12))
    pose_feet(rig, "L", (0.15, -0.33, 0.0), toe_lift=14)
    pose_feet(rig, "R", (-0.13, 0.30, 0.0), heel_lift=28)
    aim_pole_knee(rig, "L", (0, -1, 0))
    aim_pole_knee(rig, "R", (0, -1, 0))
    rotate_world(rig, "upper_arm.L", (1, 0, 0), math.radians(18))      # left arm (sword) back
    rotate_world(rig, "upper_arm.R", (1, 0, 0), math.radians(-22))     # right arm forward
    rotate_world(rig, "forearm.R", (1, 0, 0), math.radians(-15))
    curve_chain(rig, scarf_names("L"), (1, 0, 0), [-8, -8, -8, -6, -5])
    curve_chain(rig, scarf_names("R"), (1, 0, 0), [-8, -8, -8, -6, -5])
    rotate_world(rig, "skirt.B", (1, 0, 0), math.radians(-6))
    store_pose(rig, "walk_contact")

    # --- run stride (lean forward, sword trailing back)
    clear_pose(rig)
    move(rig, "cog", (0, -0.05, -0.05))
    rotate_world(rig, "spine", (1, 0, 0), math.radians(-16))
    rotate_world(rig, "head", (1, 0, 0), math.radians(10))
    pose_feet(rig, "L", (0.14, -0.52, 0.10), toe_lift=20)
    pose_feet(rig, "R", (-0.12, 0.45, 0.20), heel_lift=55)
    aim_pole_knee(rig, "L", (0, -1, 0.2))
    aim_pole_knee(rig, "R", (0, -1, -0.3))
    rotate_world(rig, "upper_arm.L", (1, 0, 0), math.radians(45))
    rotate_world(rig, "upper_arm.R", (1, 0, 0), math.radians(-40))
    rotate_world(rig, "forearm.R", (1, 0, 0), math.radians(-40))
    set_sword_dir(rig, 75, 25)          # run: sword held back and trailing
    curve_chain(rig, scarf_names("L"), (1, 0, 0), [-35, -15, -10, -8, -6])
    curve_chain(rig, scarf_names("R"), (1, 0, 0), [-38, -15, -10, -8, -6])
    for side in ("L", "R"):
        rotate_world(rig, f"sleeve.{side}", (1, 0, 0), math.radians(-35))
    rotate_world(rig, "skirt.B", (1, 0, 0), math.radians(-18))
    curve_chain(rig, ["skirt.tail.001", "skirt.tail.002", "skirt.tail.003"], (1, 0, 0), [-12, -10, -8])
    store_pose(rig, "run_stride")

    # --- jump apex (refs/3): arched back, chin up, legs together bent back, cloth flares up
    clear_pose(rig)
    move(rig, "cog", (0, 0.0, 0.04))
    rotate_world(rig, "spine", (1, 0, 0), math.radians(8))
    rotate_world(rig, "chest", (1, 0, 0), math.radians(6))
    rotate_world(rig, "head", (1, 0, 0), math.radians(10))
    pose_feet(rig, "L", (0.10, 0.30, 0.34), yaw=0)
    pose_feet(rig, "R", (-0.10, 0.26, 0.28), yaw=0)
    for side in ("L", "R"):
        rotate_world(rig, f"foot_ik.{side}", (1, 0, 0), math.radians(-35))
        aim_pole_knee(rig, side, (0, -1, -0.2))
    rotate_world(rig, "upper_arm.L", (0, 1, 0), math.radians(-35))
    rotate_world(rig, "upper_arm.L", (1, 0, 0), math.radians(20))
    rotate_world(rig, "upper_arm.R", (0, 1, 0), math.radians(45))
    rotate_world(rig, "forearm.R", (0, 1, 0), math.radians(25))
    for side, s in (("L", 1), ("R", -1)):
        rotate_world(rig, f"sleeve.{side}", (0, 1, 0), math.radians(-60 * s))
        curve_chain(rig, scarf_names(side), (1, 0, 0), [30, 18, 12, 10, 8])
        rotate_world(rig, f"skirt.{side}", (0, 1, 0), math.radians(-20 * s))
        rotate_world(rig, f"skirt.{side}.001", (0, 1, 0), math.radians(-18 * s))
        rotate_world(rig, f"skirt.{side}.002", (0, 1, 0), math.radians(-14 * s))
    rotate_world(rig, "skirt.F", (1, 0, 0), math.radians(10))
    rotate_world(rig, "skirt.B", (1, 0, 0), math.radians(-16))
    curve_chain(rig, ["skirt.tail.001", "skirt.tail.002", "skirt.tail.003"], (1, 0, 0), [-10, -10, -10])
    set_sword_dir(rig, 55, 30)          # sword trails back and down (refs/3 diagonal)
    set_props(rig, expr_smile=1)
    store_pose(rig, "jump_apex")

    # --- overhead (attack wind-up; stress test for shoulders)
    clear_pose(rig)
    pose_feet(rig, "L", (0.30, -0.25, 0.0), yaw=-20)
    pose_feet(rig, "R", (-0.28, 0.22, 0.0), yaw=25)
    aim_pole_knee(rig, "L", (0.3, -1, 0))
    aim_pole_knee(rig, "R", (-0.3, -1, 0))
    move(rig, "cog", (0, 0, -0.10))
    rotate_world(rig, "spine", (1, 0, 0), math.radians(10))      # arched back, wind-up
    rotate_world(rig, "chest", (1, 0, 0), math.radians(8))
    rotate_world(rig, "chest", (0, 0, 1), math.radians(-15))
    rotate_world(rig, "head", (1, 0, 0), math.radians(-12))
    pose_two_hand(rig, (0.0, -0.05, 2.30), (0.0, 0.55, 0.83), edge_hint=V((0, -1, 0)), elbow_out=0.6)
    set_props(rig, expr_frown=1)
    store_pose(rig, "overhead")

    clear_pose(rig)
    rig["poses"] = json.dumps(POSES)
    rig["idle_sword_dir"] = json.dumps(IDLE_SWORD_DIR)
    rig["pose_names"] = ",".join(POSES.keys())


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
    skirt_ob = build_skirt(rig, coll)
    build_belt_pouch(rig, coll, skirt_ob)
    build_shoes(rig, coll)
    build_scarf(rig, coll)
    build_sword(rig, coll)
    setup_scene()
    make_poses(rig)
    # cel look: only hair/body forms cast shadows; big cloth shapes would blanket the legs/face
    for ob in bpy.data.objects:
        if ob.type == "MESH" and ob.name.split(".")[0] in (
                "skirt_outer", "skirt_under", "sleeve", "scarf", "collar", "katana", "katana_sprite",
                "bow", "belt_pouch", "arm_ornament", "chest_flower", "chest_cord", "saya", "sleeve_band",
                # round 2 (Gemini): no cast shadows on/onto the face -> no diagonal shadow over the nose
                "bangs", "hair_strands", "hair_cap", "bun", "ears", "head", "hair_sheen", "bun_sheen"):
            ob.visible_shadow = False
    # meta
    rig["H"] = 1.0
    rig["front"] = "-Y (S iso direction)"
    rig["handedness"] = "+X = her LEFT (katana hand), -X = her RIGHT (arm ornament)"
    bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND, compress=True)
    nb = len(rig.data.bones)
    print(f"[build] saved {OUT_BLEND}  objects={len(bpy.data.objects)} bones={nb} materials={len(bpy.data.materials)}")


if __name__ == "__main__":
    main()
