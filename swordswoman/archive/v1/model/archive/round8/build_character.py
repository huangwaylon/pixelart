"""Akane / "Crimson Ronin" chibi character -- procedural build.

Run:
  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P model/build_character.py

Builds every mesh, material, the armature "rig", vertex weights, camera + camera-locked
lights, and saves model/character.blend.  Deterministic (no randomness, no time input).

Units: 1 Blender unit = 1 H (head height, see docs/design_bible.md section 3).
Character faces -Y (front = S iso direction).  +X is HER LEFT, -X is HER RIGHT.
Origin at the feet.
"""
import bpy, bmesh, math, json, os, sys, time
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
            g1.name = "rim_thresh"      # render scripts raise this to 2.0 for sprite cells
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


def make_face_skin(name):
    """Round 3 (AD/TA): the face is ONE flat skin tone (no diffuse terminator wedge).  Only the
    jaw underside (world normal pointing down) takes the skin[0] shadow."""
    m, nt = _new_mat(name)
    idx = len(MAT_ID) + 1
    MAT_ID[name] = idx
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    emis = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(emis.outputs[0], out.inputs["Surface"])
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Normal"], sep.inputs[0])
    lt = nt.nodes.new("ShaderNodeMath")
    lt.operation = "LESS_THAN"
    lt.inputs[1].default_value = -0.88
    nt.links.new(sep.outputs["Z"], lt.inputs[0])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    nt.links.new(lt.outputs[0], mix.inputs["Factor"])
    for s in mix.inputs:
        if s.identifier == "A_Color":
            s.default_value = hexlin(R["skin"][1])
        if s.identifier == "B_Color":
            s.default_value = hexlin(R["skin"][0])
    for s in mix.outputs:
        if s.identifier == "Result_Color":
            nt.links.new(s, emis.inputs["Color"])
    _aov(nt, "matid", ((idx % 8) / 8.0, ((idx // 8) % 8) / 8.0, idx / 64.0, 1.0))
    m["palette_ramp"] = ",".join(R["skin"][:2])
    m["mat_id"] = idx
    MATS[name] = m
    return m


def build_materials():
    make_toon("M_skin", R["skin"], (0.16, 0.95))
    make_face_skin("M_skin_face")
    # round 3 (AD, bible ramp restored): hair[1] #74483a is the lit base, hair[0] #42282a the
    # shadow, outline #1a1220 only in the deepest recesses.  Pink rim (camera-locked).
    # round 4 (GD 'dark brunette'): hair[0] is now the dominant base, hair[1] only on the lit
    # top-left planes (threshold raised 0.30 -> 0.58), so the hair separates from skin + corset
    make_toon("M_hair", [R["hair"][0], R["hair"][1]], (0.92,), rim=True)
    # bangs locks catch more of the key light (hair[1] on their front planes) so the pointed
    # clumps read against the darker hair[0] cap at sprite scale
    make_toon("M_hair_bangs", [R["hair"][0], R["hair"][1]], (0.76,), rim=True)   # r5 (AD darker): 0.70 -> 0.76
    # round 5 (AD/GD bun vs cranium): the bun takes the key light more readily than the skull
    # (hair[1] on its lit half), so it reads as a second, separate circle on the N sprite
    make_toon("M_hair_bun", [R["hair"][0], R["hair"][1]], (0.58,), rim=True)
    make_toon("M_hair0_flat", [R["hair"][0]], (), flat=True)      # bun crease (round 5)
    # angel ring: ONE continuous flat hair[2] band
    make_toon("M_hair_sheen", [R["hair"][2]], (), flat=True)
    # round 3 (GD value separation): the skirt sits one ramp step darker than the sleeves
    make_toon("M_red", R["red"][1:], (0.26, 0.90))                 # crimson / base / coral (collar, bodice)
    make_toon("M_red_skirt", R["red"][1:3], (0.78,))               # skirt: crimson body, red[2] lit only
    # round 4 (AD): bow reads RED -- red[2] base, red[1] shadow, red[3] only on a sliver
    make_toon("M_red_rim", R["red"][1:], (0.30, 0.97), rim=True)   # bow
    # round 4 (AD 'sleeve value'): red[2] base, red[3] only on the top-left lit plane, red[1] on
    # the shadow side (cuff interiors stay red[0]/red[1] via M_red_under)
    make_toon("M_red_sleeve", R["red"][1:], (0.07, 0.93), rim=True)   # r7 (AD): smaller coral cuff specular (0.86 -> 0.93)
    # round 4 (GD 'red mass separation'): the collar is one value step below the bodice/sleeves
    make_toon("M_red_collar", R["red"][1:3], (0.88,))              # collar outer: red[1], lit sliver red[2]
    make_toon("M_red_under", R["red"][:2], (0.35,))               # violet / crimson (undersides)
    # round 5 (AD): sleeve interior -- lighter red[2] inside, red[1] mid, violet only deep inside
    make_toon("M_red_cuff_in", R["red"][:3], (0.45, 0.88))      # r7 (AD red mass): violet/crimson cuff interiors, red[2] only at the lit lip
    make_toon("M_red_inner", R["red"][1:3], (0.80,))              # collar inner face: red[1], lit red[2]
    make_toon("M_leather", R["leather"], (0.18, 0.86))
    make_toon("M_dark", R["dark"], (0.25,))
    make_toon("M_dark1_flat", [R["dark"][1]], (), flat=True)      # sandal uppers / straps
    make_toon("M_steel", R["steel"], (0.3, 0.92))
    # round 3 (GD): scarf darker + more saturated than skin[1]: pink[0] base, pink[1] lit edge,
    # violet (red[0]) underside via the Solidify shell
    make_toon("M_pink", [R["pink"][0], R["pink"][1]], (0.80,))
    make_toon("M_scarf_under", [R["red"][0]], (), flat=True)
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

    def build(self, name, coll=None, outward=None):
        """outward: a point (Vector) or fn(face_centre)->point.  Faces whose normal points
        toward that point are flipped, so open shells (bangs, strands, sheen) face outward."""
        me = bpy.data.meshes.new(name)
        me.from_pydata([tuple(p) for p in self.v], [], self.f)
        me.validate(clean_customdata=False)
        if outward is not None:
            bm = bmesh.new()
            bm.from_mesh(me)
            bm.faces.ensure_lookup_table()
            # round 6 (TA 'scarf.L opposite winding'): decide the flip per connected ISLAND by an
            # area-weighted vote, never per face -- a twisted ribbon has faces whose normal points
            # toward the reference, and flipping only those broke the winding (3 bad edges)
            seen = set()
            for f0 in bm.faces:
                if f0.index in seen:
                    continue
                st, comp = [f0], []
                seen.add(f0.index)
                while st:
                    x = st.pop()
                    comp.append(x)
                    for e in x.edges:
                        for g in e.link_faces:
                            if g.index not in seen:
                                seen.add(g.index)
                                st.append(g)
                vote = 0.0
                for f in comp:
                    c = f.calc_center_median()
                    ref = outward(c) if callable(outward) else V(outward)
                    vote += f.calc_area() * (1 if f.normal.dot(c - ref) >= 0 else -1)
                if vote < 0:
                    for f in comp:
                        f.normal_flip()
            bm.to_mesh(me)
            bm.free()
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


def fix_closed_normals():
    """Round 4 (TA normals): every CLOSED (manifold) island of every mesh gets consistent,
    outward winding (box() / pouch / buckles / tsuka parts were wound inward).  Open shells
    (hair sheets, cloth) keep their explicit outward orientation from MB.build(outward=...)."""
    for ob in bpy.data.objects:
        if ob.type != "MESH" or ob.name in ("face_decals",):
            continue
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        seen = set()
        fixed = 0
        for f in bm.faces:
            if f.index in seen:
                continue
            st, comp = [f], []
            seen.add(f.index)
            while st:
                x = st.pop()
                comp.append(x)
                for e in x.edges:
                    for g in e.link_faces:
                        if g.index not in seen:
                            seen.add(g.index)
                            st.append(g)
            if all(e.is_manifold for x in comp for e in x.edges):
                before = [x.normal.copy() for x in comp]
                bmesh.ops.recalc_face_normals(bm, faces=comp)
                fixed += sum(1 for x, n0 in zip(comp, before) if x.normal.dot(n0) < 0)
        if fixed:
            bm.to_mesh(ob.data)
            ob.data.update()
            print(f"[normals] {ob.name}: {fixed} faces re-wound outward")
        bm.free()


def recalc_normals(ob):
    """Consistent outward winding on every closed island (bmesh.ops.recalc_face_normals works
    per connected region)."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    # closed tube loops repeat their first ring at the end: weld the seam first so every island
    # is a closed manifold, then make the winding consistent + outward per island
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()


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
         smooth=True, mat_fn=None, phase=0.0, closed=False):
    """radius_fn(t, phi) -> (rN, rB) or float.  mat_fn(t) -> material name (optional).
    closed=True (round 4): path is a loop whose last point repeats the first; the last ring is
    welded to the first (ring offset chosen by distance) -> a closed manifold torus."""
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
    for ri, row in enumerate(rows):
        if closed and ri == n - 1:
            ids.append(None)        # round 5 (TA): the duplicate seam ring is never added (was 18 loose verts)
            continue
        ids.append([mb.add_vert(p) for p in row])
    if closed:
        # drop the duplicate last ring; connect ring n-2 to ring 0 with the best index offset
        last = rows[-2]
        off = min(range(nseg), key=lambda o: sum((last[k] - rows[0][(k + o) % nseg]).length for k in range(nseg)))
        ids[-1] = [ids[0][(k + off) % nseg] for k in range(nseg)]
        ids[-1] = ids[-1]
        for i in range(n - 1):
            mname = mat_fn((i + 0.5) / (n - 1)) if mat_fn else mat
            nxt = ids[i + 1] if i + 1 < n - 1 else [ids[0][(k + off) % nseg] for k in range(nseg)]
            for k in range(nseg):
                a, b = ids[i][k], ids[i][(k + 1) % nseg]
                c, d = nxt[(k + 1) % nseg], nxt[k]
                mb.add_face((a, b, c, d), mname, smooth)
        return ids
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
    """Rest curve of the scarf ribbon, round 3 (GD/TA/AD): from the back of the collar the
    ribbons stream BACK and down behind the shoulders (~0.95 H long), spread just enough to keep
    the bare-back strip visible, and stay behind the torso so they never run beside the arms in
    the front-facing views.  Slight drift toward her right (-X) as in refs/1."""
    # round 4 (TA/GD/AD): roots moved down + inward behind the collar's back centre (z 1.86,
    # x +-0.035) so the ribbons clear the bare shoulder tops in N; a gentle S-curve in x
    # (out - in - out) so the back view is not two flat parallel strips
    # round 7 (AD must-fix 'scarf X over the bare back'): the roots sit at the back-SIDE edges of
    # the collar (x +-0.085) and the two ribbons fall straight back + down beside the spine, each
    # staying on its own side (no drift, no crossing), and only splay out below the shoulder
    # line, so the skin strip between the collar and the corset reads from N / NE / NW.  ~15 %
    # longer (1.1 H) with a widened swallowtail tip.
    s = 1 if side == "L" else -1
    return [V((0.100 * s, 0.20, 1.86)),
            V((0.125 * s, 0.36, 1.75)),
            V((0.140 * s, 0.51, 1.59)),
            V((0.170 * s, 0.62, 1.40)),
            V((0.220 * s, 0.70, 1.20)),
            V((0.270 * s, 0.75, 0.99))]


def define_skeleton():
    BONES.clear()
    bone("root", (0, 0, 0), (0, 0.45, 0), None, deform=False)
    bone("cog", (0, 0.0, 0.92), (0, 0.35, 0.92), "root", deform=False)
    bone("hips", (0, 0, 0.92), (0, 0, 1.12), "cog")
    bone("spine", (0, 0, 1.12), (0, 0, 1.38), "hips", connect=True)
    bone("chest", (0, 0, 1.38), (0, 0, 1.72), "spine", connect=True)
    bone("neck", (0, 0, 1.72), (0, 0, 1.88), "chest", connect=True)
    bone("head", (0, 0, 1.88), hs(V((0, 0, 2.75))), "neck", connect=True)
    bone("bun", hs(BUN_C - V((0, 0.08, 0.20))), hs(BUN_C + V((0, 0.05, 0.17))), "head")
    bone("bow", hs(BOW_K), hs(BOW_K + V((0, 0, 0.26))), "bun")
    for side in ("L", "R"):
        s = 1 if side == "L" else -1
        sh_in, sj, el, wr, ht = arm_points(side)
        bone(f"shoulder.{side}", sh_in, sj, "chest")
        # round 5 (TA 'overhead range'): head-clearance layer at the shoulder joint (non-deform).
        # A driver swings it outward about the body's forward axis once the FK arm passes ~95 deg,
        # so a commanded overhead raise passes BESIDE the 1.12x chibi head instead of through it
        bone(f"arm_clear.{side}", sj, sj + (el - sj).normalized() * 0.10, f"shoulder.{side}", deform=False)
        bone(f"upper_arm.{side}", sj, el, f"arm_clear.{side}")
        bone(f"forearm.{side}", el, wr, f"upper_arm.{side}", connect=True)
        bone(f"hand.{side}", wr, ht, f"forearm.{side}", connect=True)
        # round 4 (TA): elbow volume helper (half the forearm rotation), spreads the sleeve /
        # arm fold of bent-elbow poses (idle grip, walk) over two blend zones
        bone(f"elbow_help.{side}", el, el.lerp(wr, 0.22), f"upper_arm.{side}")
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
        bone(f"upper_arm_help.{side}", sj, sj.lerp(el, 0.28), f"arm_clear.{side}")
        bone(f"shin.{side}", kn, an, f"thigh.{side}", connect=True)
        # round 4 (TA 'knee crease collapse'): knee volume helper, child of the thigh at the knee,
        # copies HALF the shin's local rotation; the crease loops are weighted to it so a deep
        # bend is spread over two blend zones (thigh -> knee_help -> shin)
        bone(f"knee_help.{side}", kn, kn.lerp(an, 0.22), f"thigh.{side}")
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
        # round 3: the IK hand takes 65% of the target orientation -- the rest of the wrist twist
        # stays in the forearm, so two-handed grips no longer candy-wrap the wrist / cuff
        _driver_prop(c, "influence", ob, f"ik_arm.{side}", expr="0.65 * var")
    for side in ("L", "R"):
        for hb, src in ((f"thigh_help.{side}", f"thigh.{side}"), (f"upper_arm_help.{side}", f"upper_arm.{side}"),
                        (f"knee_help.{side}", f"shin.{side}"), (f"elbow_help.{side}", f"forearm.{side}")):
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
    # round 3 (TA/GD): cuff pull-back -- with two_hand = 1 the sleeve tip bones shrink toward
    # the wrist so the bell cuffs stop swallowing both hands on the tsuka
    for side in ("L", "R"):
        pb = ob.pose.bones[f"sleeve.{side}"]
        # length-only (bone Y) scale: the hanging furi folds up toward the wrist without the
        # radial collapse a uniform scale causes
        _driver_prop(pb, "scale", ob, "two_hand", expr="1 - 0.35 * var", index=1)

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
    add_shoulder_autoraise(ob)
    add_arm_clear(ob)

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


SHOULDER_RAISE = dict(threshold_deg=85.0, factor=0.30, lift=0.04, lift_threshold_deg=100.0)
# round 5: head-clearance splay (arm_clear.<side>): outward swing = factor x (FK arm angle -
# threshold), about the body's forward axis, so the arm passes beside the head
ARM_CLEAR = dict(threshold_deg=90.0, factor=1.0, max_deg=50.0)


def _fk_angle_vars(d, rig, side):
    for nm, path in (("qw", f'pose.bones["upper_arm.{side}"].rotation_quaternion[0]'),
                     ("ex", f'pose.bones["upper_arm.{side}"].rotation_euler[0]'),
                     ("ey", f'pose.bones["upper_arm.{side}"].rotation_euler[1]'),
                     ("ez", f'pose.bones["upper_arm.{side}"].rotation_euler[2]')):
        v = d.variables.new(); v.name = nm; v.type = "SINGLE_PROP"
        v.targets[0].id_type = "OBJECT"; v.targets[0].id = rig
        v.targets[0].data_path = path


FK_ANG = "max(2.0 * acos(min(1.0, abs(qw))), sqrt(ex * ex + ey * ey + ez * ez))"


def add_arm_clear(rig):
    """Round 5 (TA must-fix 'arms cannot go above 120 deg'): head-clearance layer.
    arm_clear.<side> sits at the shoulder joint between shoulder and upper_arm.  Its quaternion
    is driven from the RAW FK channels of upper_arm (no evaluated data -> no dependency cycle):
        c = min(max_deg, factor * max(0, fk_angle - threshold))
    rotating the arm outward about the body's forward (Y) axis.  A forward overhead raise is
    thereby carried out to the side of the head, a side raise is held at ~125 deg.  It is
    off in IK (IK targets are authored clear of the head).  Plus a clavicle translation: the
    shoulder joint lifts up and back by `lift` H above lift_threshold (shoulder location)."""
    t0 = math.radians(ARM_CLEAR["threshold_deg"])
    k = ARM_CLEAR["factor"]
    cmax = math.radians(ARM_CLEAR["max_deg"])
    for side in ("L", "R"):
        s = 1 if side == "L" else -1
        b = rig.data.bones[f"arm_clear.{side}"]
        R0 = b.matrix_local.to_3x3()
        # world axis whose positive rotation moves an UP-pointing arm outward (+X*s)
        ax_w = V((0, s, 0))            # right-hand rule: +rot about +Y moves +Z toward +X
        ax = (R0.inverted() @ ax_w).normalized()
        ang = f"(1.0 - ik) * min({cmax:.4f}, {k} * max(0.0, {FK_ANG} - {t0:.4f}))"
        pb = rig.pose.bones[f"arm_clear.{side}"]
        pb.rotation_mode = "QUATERNION"
        for idx, expr in ((0, f"cos(0.5 * {ang})"), (1, f"{ax.x:.5f} * sin(0.5 * {ang})"),
                          (2, f"{ax.y:.5f} * sin(0.5 * {ang})"), (3, f"{ax.z:.5f} * sin(0.5 * {ang})")):
            fc = pb.driver_add("rotation_quaternion", idx)
            d = fc.driver
            d.type = "SCRIPTED"
            _fk_angle_vars(d, rig, side)
            v = d.variables.new(); v.name = "ik"; v.type = "SINGLE_PROP"
            v.targets[0].id_type = "OBJECT"; v.targets[0].id = rig
            v.targets[0].data_path = f'["ik_arm.{side}"]'
            d.expression = expr
        # clavicle translation (shoulder bone local space), up + back
        sb = rig.data.bones[f"shoulder.{side}"]
        Rs = sb.matrix_local.to_3x3().inverted()
        lw = Rs @ (V((0, 0.35, 1.0)).normalized() * SHOULDER_RAISE["lift"])
        lt = math.radians(SHOULDER_RAISE["lift_threshold_deg"])
        spb = rig.pose.bones[f"shoulder.{side}"]
        for idx in range(3):
            fc = spb.driver_add("location", idx)
            d = fc.driver
            d.type = "SCRIPTED"
            _fk_angle_vars(d, rig, side)
            v = d.variables.new(); v.name = "ik"; v.type = "SINGLE_PROP"
            v.targets[0].id_type = "OBJECT"; v.targets[0].id = rig
            v.targets[0].data_path = f'["ik_arm.{side}"]'
            d.expression = f"{lw[idx]:.5f} * (1.0 - ik) * min(1.0, max(0.0, ({FK_ANG} - {lt:.4f}) / 0.6))"
    rig["arm_clear"] = json.dumps(ARM_CLEAR)


def add_shoulder_autoraise(rig):
    """Round 4 (TA 'shoulder deformation for raised-arm sword work'): clavicle auto-raise.
    shoulder.<side> rotates up (and so swings the whole arm out, away from the 1.12x head) by
    factor x (arm elevation - threshold).  Arm elevation = the FK upper_arm rotation angle
    (2 acos|w| of its quaternion channel) or, in IK, the elevation of hand_ik above the shoulder
    (90 deg at shoulder height).  The driver reads raw channels / the IK control (a child of cog),
    never the evaluated arm, so there is no dependency cycle.  Quaternion w / axis component are
    driven so the shoulder stays in QUATERNION mode like every other bone."""
    t0 = math.radians(SHOULDER_RAISE["threshold_deg"])
    k = SHOULDER_RAISE["factor"]
    for side in ("L", "R"):
        sgn = _local_rot_sign(rig, f"shoulder.{side}", "Z", (0, 0, 1))      # +Z rot raises the tip?
        sj_z = rig.data.bones[f"upper_arm.{side}"].head_local.z
        # FK angle = quaternion angle, or the Euler magnitude if the channel is in Euler mode
        ang = (f"{k} * max(0.0, max(max(2.0 * acos(min(1.0, abs(qw))), sqrt(ex * ex + ey * ey + ez * ez)), "
               f"ik * (1.5708 + asin(max(-1.0, min(1.0, (hz - {sj_z:.4f}) / 0.95))))) - {t0:.4f})")
        for idx, expr in ((0, f"cos(0.5 * {ang})"), (3, f"{sgn} * sin(0.5 * {ang})")):
            fc = rig.pose.bones[f"shoulder.{side}"].driver_add("rotation_quaternion", idx)
            d = fc.driver
            d.type = "SCRIPTED"
            v = d.variables.new(); v.name = "qw"; v.type = "SINGLE_PROP"
            v.targets[0].id_type = "OBJECT"; v.targets[0].id = rig
            v.targets[0].data_path = f'pose.bones["upper_arm.{side}"].rotation_quaternion[0]'
            for ci, cn in enumerate(("ex", "ey", "ez")):
                v = d.variables.new(); v.name = cn; v.type = "SINGLE_PROP"
                v.targets[0].id_type = "OBJECT"; v.targets[0].id = rig
                v.targets[0].data_path = f'pose.bones["upper_arm.{side}"].rotation_euler[{ci}]'
            v = d.variables.new(); v.name = "ik"; v.type = "SINGLE_PROP"
            v.targets[0].id_type = "OBJECT"; v.targets[0].id = rig
            v.targets[0].data_path = f'["ik_arm.{side}"]'
            v = d.variables.new(); v.name = "hz"; v.type = "TRANSFORMS"
            v.targets[0].id = rig; v.targets[0].bone_target = f"hand_ik.{side}"
            v.targets[0].transform_type = "LOC_Z"; v.targets[0].transform_space = "TRANSFORM_SPACE"
            d.expression = expr
    rig["shoulder_autoraise"] = json.dumps(SHOULDER_RAISE)


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
    names = [f"shoulder.{side}", f"upper_arm_help.{side}", f"upper_arm.{side}", f"elbow_help.{side}",
             f"forearm.{side}"]
    eax = (a + f).normalized()
    joints = [(sj - a * 0.07, a), (sj + a * 0.05, a), (el - eax * 0.05, eax), (el + eax * 0.05, eax)]
    bl = [blend_sh * 0.6, blend_sh * 0.6, blend_el * 0.7, blend_el * 0.7]
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
    kax = (a + b).normalized()
    return chain_w(p, ["hips", f"thigh_help.{side}", f"thigh.{side}", f"knee_help.{side}", f"shin.{side}",
                       f"foot.{side}"],
                   [(hp + nrm * 0.06 * -1, nrm), (hp + nrm * 0.08, nrm), (kn - kax * 0.06, kax),
                    (kn + kax * 0.06, kax), (an + V((0, 0, -0.02)), V((0, 0, -1)))],
                   [blend_hip * 0.6, blend_hip * 0.6, blend_knee, blend_knee, 0.04])


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
# round 3 (GD): the whole head group (head, face, hair, bun, bow) is built at the bible size and
# then scaled up about the chin, so the head reads ~40% of the sprite height.
HEAD_SCALE = 1.12
HEAD_PIVOT = V((0, 0, 1.80))
BUN_RX = 0.25     # round 7 (AD): bun half-width 0.29 -> 0.25 (~0.56 H wide after the head scale), the bow dominates
BUN_C = V((0, 0.21, 2.95))    # round 5 (AD/GD): higher + a touch forward -> breaks the N head contour
BOW_K = V((-0.24, -0.09, 2.78))      # round 8 (AD/Gemini): knot at the front-right BASE of the bun (r7: (-0.21, -0.03, 3.06), on its top shoulder)


def hs(p):
    return HEAD_PIVOT + (V(p) - HEAD_PIVOT) * HEAD_SCALE


HEAD_GROUP = ("head", "ears", "face_decals", "hair_cap", "hair_sheen", "bangs", "hair_strands", "hair_streaks", "bun", "bun_crease",
              "bun_sheen", "bow")


def scale_head_group():
    M = Matrix.Translation(HEAD_PIVOT) @ Matrix.Scale(HEAD_SCALE, 4) @ Matrix.Translation(-HEAD_PIVOT)
    for n in HEAD_GROUP:
        ob = bpy.data.objects.get(n)
        if ob is None:
            continue
        ob.data.transform(M, shape_keys=True)
        ob.data.update()
        for md in ob.modifiers:
            if md.type == "SOLIDIFY" and md.name != "Outline":
                md.thickness *= HEAD_SCALE


def head_deform(p):
    """p local to head centre.  Round 3 (AD 'flat profile'): rounded face volume -- a soft
    forward fullness down the face centre (cheeks / nose / mouth), cheeks widened ~4.5%,
    chibi jaw taper and a soft chin point, so in profile the face is a curve and the eye
    decals sit inside the silhouette."""
    zr = clamp(p.z / HEAD_R.z, -1.0, 1.0)
    q = V(p)
    # flatter face front (round 3): the sides of the face come forward a little, so in 3/4 /
    # iso SE-SW the far eye stays on a visible plane instead of wrapping round the sphere
    fr = clamp(-p.y / HEAD_R.y, 0.0, 1.0)
    band = math.exp(-((zr + 0.25) / 0.55) ** 2)
    q.y *= 1 + 0.30 * (p.x / HEAD_R.x) ** 2 * fr * band
    cheek = math.exp(-((zr + 0.32) / 0.34) ** 2)
    q.x *= 1 + 0.022 * cheek        # round 4 (Gemini): softer, less bulbous lower cheeks
    if p.z < 0:
        k = clamp(-zr, 0, 1)
        fx = 1 - 0.45 * k ** 1.9      # soft anime jaw (round 4: a touch more taper)
        fy = 1 - 0.20 * k ** 2
        q.x *= fx
        q.y *= fy
        front = smoothstep(0.2, 1.0, -p.y / HEAD_R.y)
        q.y -= 0.035 * k ** 3 * front                        # chin slightly forward (soft point)
        q.z -= 0.02 * k ** 4 * front * math.exp(-(p.x / 0.14) ** 2)
    # forward fullness down the face centre: strongest at cheek/mouth height, fades at the eyes'
    # outer corners -> the profile is a curve (forehead -> cheek -> chin), not a plane
    front = smoothstep(0.0, 1.0, -p.y / HEAD_R.y)
    # (centred below the eyes: cheeks / mouth, so the far eye still shows in 3/4 and iso SE/SW)
    mid = math.exp(-(p.x / 0.17) ** 2) * math.exp(-((zr + 0.70) / 0.24) ** 2)
    q.y -= 0.050 * mid * front
    return q


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
    ellipsoid(mb, HEAD_C, HEAD_R, "M_skin_face", nu=40, nv=28, deform=head_deform)
    ob = mb.build("head", coll)
    finish(ob, rig, subsurf=2, outline_px=1.5)
    weight_rigid(ob, "head")
    head_ob = ob
    # ears: small, flat against the head, mostly tucked under the side hair (only the lobe shows)
    mb = MB()
    for s in (1, -1):
        # round 5 (AD 'ear visible'): the hair is pulled up, so the ear stands clear of the skull
        erot = Euler((0.15, 0.30 * s, -0.35 * s)).to_matrix()
        ec = V((0.452 * s, 0.05, 2.165))
        ellipsoid(mb, ec, (0.036, 0.062, 0.082), "M_skin_face", nu=12, nv=8,
                  rot=erot)     # r5: flares out at the back
        # round 6 (AD 'flat disc ear'): inner fold (concha) in flat skin[0], set into the outer
        # face of the ear, so the ear reads as a folded shape and not a disc with one line
        # round 7 (AD/TA 'mauve bruise'): the concha disc is dropped on the model; the sprite
        # ear keeps its 1 px skin[0] inner line (ear_pass)

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
        # round 5 (TA 'peaked deltoid'): the ellipsoid poles point along the arm axis (into the
        # arm / into the torso) instead of straight up, so the shoulder top is one smooth dome
        zax = a_dir
        xax = V((0, 1, 0)).cross(zax).normalized()
        yax = zax.cross(xax).normalized()
        Rd = Matrix((xax, yax, zax)).transposed()
        ellipsoid(mb, sj + V((0.005 * s, 0.0, 0.012)), (0.094, 0.090, 0.104), "M_skin", nu=20, nv=12, rot=Rd)
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
    # round 4 (AD): calm upper lid ~12% lower -> the calm, slightly half-lidded look of refs/1
    "calm":  dict(lid=0.31, slant=0.0, low=0.0, mouth=(0.034, 0.004, 0.0)),
    "wide":  dict(lid=0.0, slant=0.0, low=0.0, mouth=(0.030, 0.010, 0.012)),
    "frown": dict(lid=0.30, slant=0.30, low=0.06, mouth=(0.030, -0.006, 0.0)),
    "smile": dict(lid=0.16, slant=-0.10, low=0.22, mouth=(0.040, 0.016, 0.006)),
    "hurt":  dict(lid=0.58, slant=-0.25, low=0.30, mouth=(0.036, -0.010, 0.016)),
}
BANG_LIFT = 0.045    # round 7 (AD): bang tips + back-layer hem raised
EYE_Z = 2.152       # round 4 (Gemini): 0.013 H lower again (cuter, more forehead under the bangs)
EYE_X = 0.205
EYE_RX, EYE_RZ = 0.105, 0.142


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
            ellipse(cx, EYE_Z, EYE_RX, EYE_RZ, 0.003, "M_glint", n=24, side=s)          # sclera
            ellipse(cx + 0.004 * s, EYE_Z - 0.006, 0.086, 0.134, 0.005, "M_eye_dark", n=24, side=s)
            ellipse(cx + 0.004 * s, EYE_Z - 0.050, 0.071, 0.082, 0.007, "M_eye_light", n=20, side=s)
            ellipse(cx + 0.004 * s, EYE_Z + 0.004, 0.036, 0.055, 0.009, "M_ink", n=16, side=s)  # pupil
            ellipse(cx - 0.030 * s, EYE_Z + 0.030, 0.030, 0.034, 0.011, "M_glint", n=12, side=s)
            ellipse(cx + 0.040 * s, EYE_Z - 0.068, 0.013, 0.013, 0.011, "M_glint", n=8, side=s)
            # upper lash: follows the lid line, heavier at the outer corner
            N = 16
            A, B = [], []
            for i in range(N + 1):
                u = i / N            # 0 inner -> 1 outer
                x = cx + s * lerp(-EYE_RX * 1.06, EYE_RX * 1.20, u)   # round 4: wider lash curve
                zt = lid_top(s, x)
                th = lerp(0.024, 0.052, u ** 1.4)
                A.append((x, zt + 0.014 + 0.004 * u))
                B.append((x, zt - th * 0.55))
            band(A, B, 0.012, "M_ink")
            # lash flick at the outer corner
            xo = cx + s * EYE_RX * 1.08
            zo = lid_top(s, xo)
            # round 5 (AD): short flick (the long one read as a second, winged eyebrow)
            band([(xo, zo + 0.008), (xo + s * 0.022, zo + 0.020)],
                 [(xo + s * 0.004, zo - 0.026), (xo + s * 0.026, zo + 0.002)], 0.012, "M_ink")
            # blush (pink[0], no ink lines around it)
            ellipse(0.290 * s, 2.000, 0.058, 0.024, 0.003, "M_blush", n=16, rings=2)
        # mouth (small) and tiny nose dot
        hw, cv, op = E["mouth"]
        mz = 1.958
        band([(-hw, mz + cv), (0.0, mz), (hw, mz + cv)],
             [(-hw, mz + cv - 0.012), (0.0, mz - 0.012 - op), (hw, mz + cv - 0.012)], 0.004, "M_mouth")
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


def hair_lock(mb, phi0, z0, phi1, z1, width, out0, out1, sweep=0.0, n=12, bulge=0.018, mat="M_hair",
              taper=None):
    """Chunky pointed anime lock lying on the head: root (phi0,z0) -> tip (phi1,z1).
    Cross-section is convex (5 verts across); width tapers to a point."""
    rows = []
    for k in range(n + 1):
        t = k / n
        tt = smoothstep(0, 1, t)
        phi = lerp(phi0, phi1, t) + sweep * math.sin(PI * 0.5 * t)
        z = lerp(z0, z1, t ** 0.9)
        out = lerp(out0, out1, t) + 0.035 * math.sin(PI * min(1.0, t * 1.15)) * (1 - 0.5 * t)
        w = (width * (1 - t ** 1.7) ** 0.8 if taper is None else width * (1 - t) ** taper) + 0.003
        row = []
        for j, a in enumerate((-1.0, -0.5, 0.0, 0.5, 1.0)):
            dphi = a * w / max(0.2, HEAD_R.x * math.cos(math.asin(clamp((z - HEAD_C.z) / HEAD_R.z, -0.95, 0.95))))
            o = out + bulge * (1 - a * a) * (1 - t * 0.6)
            row.append(head_surf(phi + dphi, z, o))
        rows.append(row)
    mb.grid(rows, mat)


def build_hair(rig, coll):
    # skull cap.  Round 5 (AD 'hood/helmet'): the hair is PULLED UP TIGHT -- below the temples
    # the cap hugs the skull (0.016 H of hair), the hairline runs from the temple up over the
    # ear and down behind it to the nape, so the ear shows in side / 3/4 / SE / SW.  The fuller
    # volume is kept only on the crown.  The back-of-skull bulge is smaller (head = one sphere,
    # bun = a separate second circle).
    mb = MB()
    C = HEAD_C + V((0, 0.012, 0.025))
    Rr = V((0.515, 0.488, 0.51))
    nu, nv = 128, 26

    def zmin_of(azd):
        # round 6 (AD 'bald temple'): the hairline comes DOWN over the temple as a short
        # sideburn tuft in front of the ear (az 64-86, to z 2.08), so from the eye back only
        # the cheek and the ear itself show skin; it rises over the ear and drops behind it.
        azd = abs(azd)
        if azd < 42:
            return 2.47
        if azd < 64:
            return lerp(2.47, 2.24, smoothstep(42, 64, azd))       # temple
        if azd < 80:
            return lerp(2.24, 2.08, smoothstep(64, 78, azd))       # sideburn tuft (points down)
        if azd < 99:
            return lerp(2.08, 2.33, smoothstep(80, 90, azd))       # up over the ear (ear visible)
        if azd < 112:
            return lerp(2.33, 2.00, smoothstep(99, 112, azd))      # hairline right behind the ear
        return 2.00                                               # smooth nape (collar covers)

    def cap_pt(ph, th):
        u = V((math.sin(th) * math.sin(ph), -math.sin(th) * math.cos(ph), math.cos(th)))
        az = abs(math.atan2(u.x, -u.y))
        zw = C.z + u.z * Rr.z
        # tight over the temple / ear zone only; the back keeps its volume (covers the cheeks
        # in the N / NE / NW views)
        tight = smoothstep(0.62, 1.20, az) * smoothstep(2.00, 1.72, az) * smoothstep(2.60, 2.36, zw)
        R2 = V([lerp(Rr[k], (HEAD_R[k] + 0.016), tight) for k in range(3)])
        p = V((u.x * R2.x, u.y * R2.y, u.z * R2.z))
        puff = 1 + 0.02 * smoothstep(0.2, 0.45, u.z)
        return C + head_deform(V((p.x * puff, p.y * puff, p.z)))
    # rows follow the hairline exactly (smooth edge, no face-cut stair steps)
    rows = []
    for j in range(1, nv + 1):
        row = []
        for i in range(nu):
            ph = 2 * PI * i / nu
            zm = zmin_of(math.degrees(ph if ph <= PI else ph - 2 * PI))
            thm = math.acos(clamp((zm - C.z) / Rr.z, -0.99, 0.99))
            row.append(cap_pt(ph, thm * (j / nv) ** 0.9))
        rows.append(row)
    ids = mb.grid(rows, "M_hair", close_u=True, flip=True)
    mb.cap(ids[0], C + V((0, 0, Rr.z * 1.02)), "M_hair", flip=False)
    ob = mb.build("hair_cap", coll, outward=C)
    finish(ob, rig, subsurf=2, thick=0.016, thick_offset=-1, outline_px=1.6)
    weight_rigid(ob, "head")

    cap_ob = ob

    # bangs, round 5 (AD/Gemini): heavy fringe whose lock tips TOUCH the upper lash line (no
    # bare-skin band), parted at her left (phi ~ +0.45); the long locks sweep to HER RIGHT
    # (screen-left in the front view) and the tip line is asymmetric: shortest at her left
    # temple, longest just right of centre.  Lock roots are buried under the hair cap (out0 is
    # inside the cap shell), so the side profile has no sliced root strips.
    mb = MB()
    nu, nv = 35, 6
    rows = []
    SPAN = 1.18
    for j in range(nv + 1):
        v = j / nv
        row = []
        for i in range(nu):
            u = i / (nu - 1)
            phi = lerp(-SPAN, SPAN, u)
            side = abs(phi) / SPAN
            # round 6 (AD 'spiky bangs'): the back layer comes down to just above the lash line
            # (gentle scallop), so no skin shows between the lock tips
            # round 7 (AD 'face at sprite scale'): the whole fringe hem rises BANG_LIFT (0.045 H,
            # ~0.05 H after the head scale), so 7-8 px of face show below the bangs at 64 px
            zb = lerp(2.205, 2.34, smoothstep(0.60, 1.0, side)) + 0.008 * math.cos(5.0 * phi) ** 2 + BANG_LIFT
            zt = lerp(2.66, 2.56, smoothstep(0.2, 1.0, side))
            z = lerp(zt, zb, v)
            phs = phi - 0.10 * v * (1 - side * 0.5) * (1 if phi < 0.45 else -0.5)
            out = 0.012 + 0.046 * math.sin(PI * min(1.0, v * 1.05)) ** 0.8
            row.append(head_surf(phs, z, out))
        rows.append(row)
    mb.grid(rows, "M_hair", flip=False)
    # round 6 (AD 'spiky triangles'): FIVE broad, blunt, overlapping locks -- one heavy mass
    # swept to her right, tips at / just above the lash line, no skin gaps between them
    LOCKS = [  # phi_root, z_root, phi_tip, z_tip, half-width, sweep   (part at phi ~ +0.45)
        (-0.78, 2.66, -1.06, 2.25, 0.135, -0.10),   # her right temple
        (-0.36, 2.73, -0.70, 2.19, 0.160, -0.14),   # over her right eye (the heavy side)
        (0.12, 2.76, -0.20, 2.175, 0.160, -0.15),   # the longest lock, between the eyes
        (0.52, 2.75, 0.40, 2.20, 0.140, -0.08),     # her left eye, inner (from the part)
        (0.92, 2.69, 1.02, 2.24, 0.120, 0.04),      # her left eye outer / temple: shortest
    ]
    for (p0, z0, p1, z1, w, sw) in LOCKS:
        z1 += BANG_LIFT
        hair_lock(mb, p0, z0, p1, z1, w * 1.1, 0.030, 0.024, sweep=sw, taper=0.32, n=16, mat="M_hair_bangs")
    ob = mb.build("bangs", coll, outward=HEAD_C)
    finish(ob, rig, subsurf=2, thick=0.022, thick_offset=-1, outline_px=1.4)
    weight_rigid(ob, "head")
    bangs_ob = ob

    # face-framing strands, round 5 (AD): ONE thin tapered lock per side, in front of the ear,
    # reaching the jaw.  It leaves the cheek toward the tip (out 0.03 -> 0.085) so a gap opens
    # between lock and jaw -- no continuous hood outline.
    mb = MB()
    for s in (1, -1):
        # round 6 (AD 'E/W eye hidden'): the lock moves BACK onto the sideburn (az ~76 deg, in
        # front of the ear, behind the eye line), so the profile eye is never covered
        hair_lock(mb, 1.30 * s, 2.40, 1.36 * s, 1.96, 0.058, 0.022, 0.034, sweep=0.03 * s, n=14,
                  bulge=0.016, taper=0.9)
    ob = mb.build("hair_strands", coll, outward=HEAD_C)
    finish(ob, rig, subsurf=1, thick=0.018, thick_offset=0, outline_px=1.0)
    weight_rigid(ob, "head")

    # round 5 (AD 'hood'): pulled-up streaks -- slim raised locks from behind the ear and the
    # nape sweeping UP to the bun base, so the side/back hair reads as gathered into the bun.
    # Model / large renders only (dropped on sprites, see render_turnaround SPRITE_DROP).
    mb = MB()
    for (a0, z0, a1, z1, w) in ((108, 2.12, 150, 2.70, 0.040), (122, 2.06, 160, 2.72, 0.042),
                                (138, 2.02, 168, 2.74, 0.042), (155, 2.00, 176, 2.74, 0.040),
                                (98, 2.44, 140, 2.76, 0.034)):
        for s_ in (1, -1):
            p0, p1 = math.radians(a0) * s_, math.radians(a1) * s_
            rows = []
            n = 14
            for k in range(n + 1):
                t = k / n
                phi = lerp(p0, p1, t)
                z = lerp(z0, z1, t)
                ww = w * math.sin(PI * min(1.0, 0.15 + 0.85 * t)) ** 0.6 * (1 - 0.6 * t) + 0.004
                row = []
                for a_ in (-1.0, 0.0, 1.0):
                    dphi = a_ * ww / 0.45
                    row.append(cap_pt(phi + dphi, math.acos(clamp((z - C.z) / Rr.z, -0.99, 0.99)))
                               + (cap_pt(phi + dphi, math.acos(clamp((z - C.z) / Rr.z, -0.99, 0.99))) - C).normalized()
                               * (0.012 + 0.010 * (1 - a_ * a_)))
                rows.append(row)
            mb.grid(rows, "M_hair_bangs")
    ob = mb.build("hair_streaks", coll, outward=C)
    finish(ob, rig, subsurf=1, thick=0.010, thick_offset=-1, outline_px=0.7)
    weight_rigid(ob, "head")

    # angel ring (round 3, AD): ONE continuous hair[2] band that follows the real hair surface
    # (cap + bangs, found by ray casts toward the skull centre), tilting down toward the back.
    bvh = BVHTree.FromPolygons(
        [v.co.copy() for v in cap_ob.data.vertices] + [v.co.copy() for v in bangs_ob.data.vertices],
        [tuple(p.vertices) for p in cap_ob.data.polygons] +
        [tuple(i + len(cap_ob.data.vertices) for i in p.vertices) for p in bangs_ob.data.polygons])
    # round 4 (Gemini 'tonsure ring'): the ring is now an ARC over the lit front/sides only
    # (azimuth -120..+105 deg, nothing across the back of the crown), with a gentle lock-scallop
    # so it reads as a hair sheen, not a headband
    mb = MB()
    n = 60
    rows = []
    for k in range(n + 1):
        a = math.radians(lerp(-125, 20, k / n))     # lit (key-light) side of the crown only
        back = (1 - math.cos(a)) / 2
        taper = smoothstep(0.0, 0.18, k / n) * smoothstep(1.0, 0.82, k / n)
        scal = 2.2 * math.sin(9 * a)
        row = []
        for de in (-2.4 * taper, 0.0, 2.4 * taper):
            e = math.radians(36 + 8 * back + scal + de * 0.8)
            d = V((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
            hit = bvh.ray_cast(C + d * 2.0, -d)
            p = hit[0] if hit[0] is not None else C + d * 0.55
            row.append(V(p) + d * 0.022)
        rows.append(row)
    mb.grid(rows, "M_hair_sheen")
    ob = mb.build("hair_sheen", coll, outward=C)
    finish(ob, rig, subsurf=0, outline=False)
    weight_rigid(ob, "head")
    ob.visible_shadow = False

    # bun, round 5 (AD/GD 'snowman'): ONE slightly messy loop bun -- a round core wrapped by a
    # single twisted hair loop with a flyaway notch, plus a dark crease ring (M_ink) where the bun
    # sits on the skull, so head and bun read as two distinct circles.  Lighter ramp than the
    # skull (M_hair_bun) so the N sprite is not one flat dark disc.
    mb = MB()
    BC = BUN_C
    Rb = Euler((-0.35, 0, 0)).to_matrix()

    def bun_def(p):
        a = math.atan2(p.y, p.x)
        b = math.atan2(p.z, math.hypot(p.x, p.y))
        bump = 1 + 0.07 * math.sin(3 * a + 1.0) * math.cos(2 * b) + 0.04 * math.sin(5 * b + a)
        return p * bump
    # round 6 (AD 'dark slot' / TA 'inward normals'): the twisted loop is no longer a separate
    # torus tube (its inner faces were 16% of the bun facing the centre, and its pinch read as a
    # dark slot from the back).  The loop is now a soft RIDGE on the core surface: the wrapped
    # strand bulges out over a tilted band whose lower edge is a step, marked by a thin hair[0]
    # crescent wrap line (built with the crease ring).
    LOOP_R = Euler((0.75, 0.42, 0.2)).to_matrix()     # wrap edge crosses the lit upper back (~23 deg up), diagonal
    LOOP_N = LOOP_R @ V((0, 0, 1))                     # loop plane normal (bun-local)

    def bun_def2(p):
        q = bun_def(p)
        n_ = p.normalized()
        h = n_.dot(LOOP_N)                                   # 0 on the loop's lower edge
        a = math.atan2((LOOP_R.transposed() @ n_).y, (LOOP_R.transposed() @ n_).x)
        wrap = 0.5 + 0.5 * math.sin(a + 0.6)                 # the strand thickens round one side
        ridge = 0.075 * smoothstep(-0.06, 0.04, h) * smoothstep(0.55, 0.12, h) * (0.45 + 0.55 * wrap)
        return q * (1 + ridge)
    ellipsoid(mb, BC, (BUN_RX, 0.28, 0.26), "M_hair_bun", nu=40, nv=24, deform=bun_def2, rot=Rb)
    # flyaway (AD/GD/TA 'horn'): a SHORT curl hugging the bun surface (<= 0.04 H proud of the
    # contour), tapering to a point and curling back down toward the bun
    bun_tmp = MB()
    ellipsoid(bun_tmp, BC, (BUN_RX, 0.28, 0.26), "M_hair_bun", nu=40, nv=24, deform=bun_def2, rot=Rb)
    _bvh0 = BVHTree.FromPolygons([V(v) for v in bun_tmp.v], bun_tmp.f)
    fly = []
    for k in range(9):
        t = k / 8
        az_, el_ = math.radians(lerp(60, 95, t)), math.radians(lerp(40, 22, t))
        d = Rb @ V((math.cos(az_) * math.cos(el_), math.sin(az_) * math.cos(el_), math.sin(el_)))
        hit = _bvh0.ray_cast(BC + d * 1.0, -d)
        q = V(hit[0]) if hit[0] is not None else BC + d * 0.28
        fly.append(q + d * (0.012 + 0.022 * math.sin(PI * t) ** 1.5))
    ob = mb.build("bun", coll)      # (the curl tube is built with bun_crease: the bun stays one convex shell)
    recalc_normals(ob)
    finish(ob, rig, subsurf=1, outline_px=1.6)
    weight_rigid(ob, "bun")
    bun_ob = ob
    # crease ring where the bun meets the skull (ray-cast onto the cap: follows the contact line)
    capb = BVHTree.FromPolygons([v.co.copy() for v in cap_ob.data.vertices],
                                [tuple(p.vertices) for p in cap_ob.data.polygons])
    mb = MB()
    ring = []
    base = BC + Rb @ V((0, 0, -0.17))
    for k in range(40):
        a = 2 * PI * k / 40
        d = Rb @ V((math.cos(a), math.sin(a), 0.0))
        q = base + d * (0.215 * BUN_RX / 0.29)
        hit = capb.find_nearest(q)
        q = V(hit[0]) + V(hit[1]).normalized() * 0.012 if hit[0] is not None else q
        ring.append(q)
    ring.append(ring[0])
    tube(mb, ring, lambda t, ph: (0.014, 0.010), "M_hair0_flat", nseg=6, cap0=False, cap1=False, closed=True)
    # round 6: crescent wrap line along the loop ridge's lower edge (~200 deg of arc, tapered)
    bvh_b = BVHTree.FromPolygons([v.co.copy() for v in bun_ob.data.vertices],
                                 [tuple(p.vertices) for p in bun_ob.data.polygons])
    cres = []
    # arc of +-115 deg centred on the part of the loop edge that faces straight back (world +Y)
    a_back = max(range(0, 360, 5), key=lambda ad: (Rb @ (LOOP_R @ V((math.cos(math.radians(ad)),
                                                                       math.sin(math.radians(ad)), 0)))).y)
    for k in range(25):
        a = math.radians(a_back + lerp(-115, 115, k / 24))
        d = Rb @ (LOOP_R @ V((math.cos(a), math.sin(a), -0.03))).normalized()
        hit = bvh_b.ray_cast(BC + d * 1.0, -d)
        q = V(hit[0]) if hit[0] is not None else BC + d * 0.28
        cres.append(q + d * 0.004)
    tube(mb, cres, lambda t, ph: (0.011 * math.sin(PI * t) ** 0.7 + 0.002, 0.007 * math.sin(PI * t) ** 0.7 + 0.002),
         "M_hair0_flat", nseg=6, cap0=True, cap1=True)
    tube(mb, fly, lambda t, ph: (0.020 * (1 - t) + 0.003, 0.014 * (1 - t) + 0.002), "M_hair_bun",
         nseg=6, cap0=True, cap1=True)
    ob = mb.build("bun_crease", coll)
    recalc_normals(ob)
    finish(ob, rig, subsurf=1, outline=False)
    weight_rigid(ob, "bun")
    # one continuous sheen ring on the bun (bible v2: required)
    bvh = BVHTree.FromPolygons([v.co.copy() for v in bun_ob.data.vertices],
                               [tuple(p.vertices) for p in bun_ob.data.polygons])
    mb = MB()
    rows = []
    for k in range(n + 1):
        # round 4 (Gemini 'tonsure'): an arc on the key-lit side of the bun, not a full ring
        # round 5 (AD): ONE short sheen arc high on the bun (upper part only, 70 deg of arc)
        a = math.radians(lerp(-80, -10, k / n))
        tp = smoothstep(0.0, 0.3, k / n) * smoothstep(1.0, 0.7, k / n)
        row = []
        for de in (-3.0 * tp, 0.0, 3.0 * tp):
            e = math.radians(52 + de)
            d = Rb @ V((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
            hit = bvh.ray_cast(BC + d * 1.5, -d)
            p = hit[0] if hit[0] is not None else BC + d * 0.3
            row.append(V(p) + d * 0.02)
        rows.append(row)
    mb.grid(rows, "M_hair_sheen")
    ob = mb.build("bun_sheen", coll, outward=BC)
    finish(ob, rig, subsurf=0, outline=False)
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
BOW_EAR_DEG = 35.0     # round 8: each ear tilts 35 deg off vertical (a 70 deg V of two upright bunny ears)
BOW_EAR_L = 0.52       # ear length knot -> tip (pre head scale)
BOW_EAR_HW = 0.135     # ear half-width at its widest
BOW_LEAN = -8.0        # ears lean FORWARD 8 deg at rest: the idle chin-up (-17 deg) tips them back, so they stand upright in the idle views


def bow_ear(mb, K, d, n0, s, L=BOW_EAR_L, HW=BOW_EAR_HW, nrow=20, nseg=28):
    """Round 8 (AD/GD must-fix 'one lumpy pillow'): one flat, pointed bunny-ear LOOP.  A lens
    cross-section swept from the pinched knot end to a pointed tip; the front face is pushed
    in to a deep recessed 'loop opening' (M_red_under, red[0]/red[1]) inside a red rim, so each
    ear reads as a ribbon loop with its inner face showing, not a solid bean."""
    W = n0.cross(d).normalized()
    out = -W * s                      # away from the V centre
    rows, fr = [], []
    for k in range(nrow):
        t = k / (nrow - 1)
        hw = HW * (math.sin(PI * min(1.0, t ** 0.95 * 0.985 + 0.012))) ** 0.85 + 0.010 * (1 - t)   # r8: pinched base -> deep V to the knot
        hw = max(hw, 0.010)
        th = 0.050 * math.sin(PI * min(1.0, t ** 0.75 * 0.97 + 0.02)) + 0.010
        # the ribbon tip flicks a little outward (pointed, not a round bean); slight forward cup
        ac = 0.045 * t ** 2.2
        c = K + d * (L * t) + out * ac + n0 * (0.020 * math.sin(PI * t))
        row, rf = [], []
        for j in range(nseg):
            ph = 2 * PI * j / nseg
            u = math.cos(ph)
            fz = math.sin(ph)
            off = th * fz
            rec = 0.0
            if fz > 0:
                bump = smoothstep(0.66, 0.40, abs(u)) * smoothstep(0.13, 0.27, t) * smoothstep(0.86, 0.68, t)
                rec = bump
                off = lerp(off, -0.55 * th, bump)
            row.append(c + out * (u * hw) + n0 * off)
            rf.append(rec)
        rows.append(row)
        fr.append(rf)
    ids = [[mb.add_vert(p) for p in row] for row in rows]
    for k in range(nrow - 1):
        for j in range(nseg):
            j2 = (j + 1) % nseg
            r = (fr[k][j] + fr[k][j2] + fr[k + 1][j] + fr[k + 1][j2]) / 4
            mat = "M_red_under" if r > 0.30 else "M_red_rim"
            a, b, cc, dd = ids[k][j], ids[k][j2], ids[k + 1][j2], ids[k + 1][j]
            mb.add_face((a, b, cc, dd), mat)
    mb.cap(ids[0], (rows[0][0] + rows[0][nseg // 2]) * 0.5, "M_red_rim", flip=True)
    mb.cap(ids[-1], (rows[-1][0] + rows[-1][nseg // 2]) * 0.5, "M_red_rim", flip=False)


def build_bow(rig, coll):
    """Big red bow tied at the BASE of the bun on HER RIGHT side (refs/1).  Round 8 (AD/GD/TA/
    Gemini 'one pillow on top of the bun'): the knot moved from the bun's top shoulder down to
    the front-right base of the bun, and the two ears are rebuilt as separate, pointed,
    upright bunny-ear loops (+-33 deg, a clear V gap down to the knot), each with a recessed
    red[0]/red[1] loop opening inside a red rim.  Width ~0.82 H, loop height ~0.4 H after the
    head scale.  The bone 'bow' (camera billboard) presents the pair in every view."""
    mb = MB()
    K = BOW_K
    lean = math.radians(BOW_LEAN)
    n0 = V((0, -math.cos(lean), math.sin(lean)))         # bow front (toward the camera via the billboard)
    for s in (1, -1):
        d = V((math.sin(math.radians(BOW_EAR_DEG)) * s, 0.0, math.cos(math.radians(BOW_EAR_DEG))))
        d = (d - n0 * d.dot(n0)).normalized()
        bow_ear(mb, K + d * 0.035, d, n0, s)
    # tails (short, V-cut), hanging below the knot, splaying a little, laid back over the hair
    for s in (1, -1):
        d = V((0.40 * s, 0.30, -0.87)).normalized()
        base = K + V((0.02 * s, 0.0, -0.035))
        pts = catmull([base, base + d * 0.09 + V((0.02 * s, 0, 0)), base + d * 0.17], 8)
        rows = []
        for k, p in enumerate(pts):
            t = k / (len(pts) - 1)
            w = lerp(0.028, 0.055, t)
            sd = V((1, 0.25 * s, 0)).normalized()
            a, b = p - sd * w, p + sd * w
            if k == len(pts) - 1:
                rows.append([a, p - d * 0.045, b])
            else:
                rows.append([a, p, b])
        mb.grid(rows, "M_red_rim")
    # knot: dark value break at the bottom of the V (red[0] / red[1])
    ellipsoid(mb, K + n0 * 0.012, (0.060, 0.052, 0.066), "M_red_under", nu=12, nv=8)
    ob = mb.build("bow", coll)
    finish(ob, rig, subsurf=1, thick=0.0, outline_px=1.6)
    s = ob.modifiers.new("Thickness", "SOLIDIFY")
    s.thickness = 0.012
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
            ztop = 1.74 + 0.24 * back ** 1.2      # round 3 (GD): front + side wings lower (chin/mouth show)
            # round 4 (AD nice-to-have): side wings ~0.05 H higher toward the ref's jaw-height
            # funnel; the front V (th ~ 0 / 2pi) stays low so the mouth still reads
            ztop += 0.055 * smoothstep(0.35, 0.95, abs(math.sin(th))) * (1 - back) ** 0.5
            z = lerp(1.67, ztop, v)
            fl = v ** 1.7
            rx = lerp(0.215, 0.45, fl)
            ry = lerp(0.175, 0.39, fl)
            yo = lerp(0.0, 0.05, v) * back
            row.append(V((math.sin(th) * rx, -math.cos(th) * ry + yo, z)))
        rows.append(row)
    mb.grid(rows, "M_red_collar", flip=False)
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
        path = catmull([start, el, wr, wr + f_dir * 0.05], 18)   # round 3: glove shows below the cuff
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
                # round 5 (AD 'boxy cuffs'): trumpet bell -- the radius grows fastest near the
                # wrist (convex flare, 0.55 H across the hem) and the lip rolls outward so the
                # lighter interior shows
                r = lerp(r, 0.262, smoothstep(0.30, 1.0, t) ** 1.7)
                r *= 1 + 0.09 * smoothstep(0.90, 1.0, t)
                # soft folds (start mid-forearm), gentler so the bell outline stays a smooth curve
                r *= 1 + 0.05 * smoothstep(0.40, 1.0, t) * math.sin(5 * ph + 0.5)
                # back/outer side of the bell hangs longer (kimono furi)
                hang = 0.5 + 0.5 * radial.dot(V((0.25 * s, 0.85, -0.2)).normalized())
                # curved (U) hem: front + back hang lowest, inner/outer edges rise -> the hem reads
                # as a rounded bell from the front and side, not a planar slanted cut
                fb = abs(radial.y)
                ext = smoothstep(0.6, 1.0, t) * (-0.07 + 0.13 * fb ** 1.3 + 0.07 * max(0.0, radial.x * s)
                                                 + 0.10 * max(0.0, radial.y))
                q = p + radial * r + T[k] * ext + V((0, 0, -1)) * ext * 0.6
                row.append(q)
                # analytic weights by ring parameter (no chest bleed, cuffs on the tip bone)
                wu = 1 - smoothstep(0.20, 0.36, t)
                wsl = smoothstep(0.62, 0.95, t) * (0.35 + 0.65 * hang) * 0.85
                wh = smoothstep(0.20, 0.36, t) * (1 - smoothstep(0.36, 0.56, t))
                wf = max(0.0, 1 - wu - wsl - wh)
                wts.append({f"upper_arm.{side}": wu, f"elbow_help.{side}": wh, f"forearm.{side}": wf,
                            f"sleeve.{side}": wsl})
            rows.append(row)
        mb = MB()
        mb.grid(rows, "M_red_sleeve", close_u=True, flip=False)
        mb.w = wts
        ob = mb.build(f"sleeve.{side}", coll)
        ob.data.materials.append(MATS["M_red_cuff_in"])
        # linear skinning (round 3): DQS + the two_hand cuff-scale driver collapsed the cuff edges
        # round 4 (Gemini 'donut cuffs'): thinner shell -> a crisp cuff edge instead of a rolled tube
        finish(ob, rig, subsurf=1, thick=0.012, thick_offset=-1, shell_mat_offset=1, outline_px=1.2, dqs=False)
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


def build_colliders(rig, coll):
    """Round 3 (TA): sleeve/arm vs head collision.  A hidden ellipsoid that hugs the hair + face
    rides on the head bone; Shrinkwrap (OUTSIDE) after the Armature modifier pushes any raised
    sleeve / arm vertex that would enter it back out (no-op at rest and in normal poses)."""
    mb = MB()
    ellipsoid(mb, hs(HEAD_C + V((0, 0.02, 0.05))), V((0.555, 0.565, 0.50)) * HEAD_SCALE, "M_skin",
              nu=24, nv=14)
    ob = mb.build("head_collider", coll)
    finish(ob, rig, subsurf=0, outline=False)
    weight_rigid(ob, "head")
    ob.hide_render = True
    ob.display_type = "WIRE"
    ob.visible_shadow = False
    ob.visible_camera = False
    for side in ("L", "R"):
        for n in (f"sleeve.{side}", f"arm.{side}", f"sleeve_band.{side}"):
            o = bpy.data.objects[n]
            m = o.modifiers.new("HeadCollide", "SHRINKWRAP")
            m.target = ob
            m.wrap_method = "NEAREST_SURFACEPOINT"
            m.wrap_mode = "OUTSIDE"
            m.offset = 0.015
            o.modifiers.move(len(o.modifiers) - 1, 1)


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
    pip = [body_pt(2 * PI * k / 36, 1.40 + 0.03 * (1 + math.cos(2 * PI * k / 36)) / 2, 0.040)
           for k in range(37)]
    tube(mb, pip, lambda t, ph: 0.011, "M_leather", nseg=6, cap0=False, cap1=False, closed=True)
    # three stacked straps
    for zc in (1.10, 1.20, 1.30):
        # round 5 (TA 'hoop ends'): closed rings hugging the corset.  Round 6 (AD 'barrel hoops'):
        # only the MID strap wraps the back; the upper / lower straps are front arcs whose ends
        # sink into the corset surface at the sides (no ends poking out, no hoops at the back)
        if zc == 1.20:
            ring = [body_pt(2 * PI * k / 36, zc, 0.040) for k in range(37)]
            tube(mb, ring, lambda t, ph: (0.012, 0.024), "M_leather", nseg=8, cap0=False, cap1=False,
                 up=V((0, 0, 1)), closed=True)
        else:
            arc = [body_pt(math.radians(lerp(-105, 105, k / 24)), zc,
                           0.040 - 0.022 * smoothstep(0.75, 1.0, abs(k / 12 - 1))) for k in range(25)]
            tube(mb, arc, lambda t, ph: (0.012, 0.024), "M_leather", nseg=8, cap0=True, cap1=True,
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
    # round 3 (Gemini/AD): plate rivets dropped (they became 1 px noise)
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
    ob = mb.build("belt_pouch", coll)
    finish(ob, rig, subsurf=1, thick=0.0, outline_px=1.2)
    s_ = ob.modifiers.new("Thickness", "SOLIDIFY")
    s_.thickness = 0.02
    ob.modifiers.move(len(ob.modifiers) - 1, 2)
    # two hanging strap tabs (tassets) over the skirt front, on the skirt surface.  Round 3: own
    # object "corset_tabs" so the sprite pass can drop them (they read as brown noise at 64 px)
    mb = MB()
    mb.wfn = tab_w
    for th_t in (-0.28, 0.30):
        pts = []
        for k in range(9):
            t = k / 8
            z = lerp(0.985, 0.76, t)      # round 3: shorter, flatter tabs (no 'sausages')
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
    ob = mb.build("corset_tabs", coll)
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
SKIRT_LOW = 0.20


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
    # round 3 (AD/TA/GD): 6 longer, separated petal tails (3 per side) with tall gaps between
    # round 6 (AD/TA 'back box'): a fifth, slightly shorter tail at the back centre, so the back
    # hem is one continuous petal/tail line (no flat rectangular ledge between 148 and 212)
    TAILS = (110, 146, 180, 214, 250)
    mb = MB()
    mb.wfn = skirt_weights
    nu, nv = 96, 16
    rows = []
    slit = 38.0
    for j in range(nv + 1):
        v = j / nv
        row = []
        gap = lerp(0.0, 72.0, v ** 1.2)       # round 4 (GD): slit opened 56 -> 72 deg at the hem
        for i in range(nu):
            u = i / (nu - 1)
            thd = lerp(slit + gap * 0.5, slit + 360 - gap * 0.5, u)
            th = math.radians(thd)
            back = (1 - math.cos(th)) / 2
            pt = petal(thd, TAILS, 19.0)
            # round 4 (GD 'legs at 64 px'): front panel 0.09 H shorter (hem 0.69 H), so both legs
            # show >= 4-5 px of skin above the sandals in the front-facing cells
            base = lerp(0.69, 0.61, smoothstep(0.05, 0.45, back)) + 0.06 * smoothstep(0.45, 0.9, back)
            # round 5 (AD 'flat apron'): the front panel is a WRAP panel -- its hem dips a little
            # at her right-front and rises diagonally to the overlap edge at the slit on her left
            wrap = smoothstep(330.0, 396.0, thd)
            base += -0.035 * math.exp(-((thd - 340.0) / 22.0) ** 2) + 0.075 * wrap ** 1.5
            low = lerp(0.36, SKIRT_LOW, smoothstep(0.35, 0.9, back))  # back tails longest (0.2 H)
            low += 0.07 * math.exp(-((thd - 180.0) / 12.0) ** 2)     # centre tail a touch shorter
            hem = base - (base - low) * pt ** 0.85
            z = lerp(TOP, hem, v)
            rx, ry, uu = skirt_radius(z)
            # round 6 (AD 'hard terminator at the back'): the folds twist diagonally with depth
            # (phase follows v) and are deeper at the back, so the cel shadow wraps along the
            # tails instead of splitting the back into two flat panels
            fold = 1 + uu * (0.03 * math.sin(8 * th + 0.4) * (1 - back ** 2)
                             + 0.060 * back ** 2 * math.sin(6 * th + 0.9 + 4.5 * v))
            curl = 1 + 0.12 * pt * smoothstep(0.50, 0.22, z)          # tail tips flick outward
            # front hem flares out a little (part of the petal bell, not a flat apron) and the
            # overlap edge stands proud of the layer below it
            frontk = ((1 + math.cos(th)) / 2) ** 2
            curl *= 1 + 0.08 * frontk * smoothstep(0.45, 1.0, v) + 0.035 * smoothstep(0.90, 1.0, u)
            p = V((math.sin(th) * rx * fold * curl, -math.cos(th) * ry * fold * curl, z))
            p.y += 0.10 * back * uu ** 1.5         # tails drift back
            row.append(p)
        rows.append(row)
    mb.grid(rows, "M_red_skirt", flip=True)
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
            # round 5 (TA 'back notch'): the under-layer points sit BEHIND the outer tails
            # (148/212) and its back-centre hem stays just under the outer gap hem, so no
            # rectangular violet box shows through the back-centre gap
            pt = petal(thd, (163, 197), 16)
            hem = 0.60 - 0.04 * back - 0.16 * pt ** 0.85
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
        """Round 3 (TA): waistband ring 100% hips; over the upper 40% of each leg opening a
        hips -> thigh_help -> thigh gradient; centre seam keeps >= 0.5 hips."""
        h = smoothstep(0.80, 0.95, p.z)          # 1 at the waistband
        u = 1 - h
        f = smoothstep(-0.07, 0.07, p.x)         # centre seam blends both legs (no split)
        d = {"hips": h}
        for side, k in (("L", f), ("R", 1 - f)):
            if k > 0:
                d[f"thigh_help.{side}"] = k * u * (1 - 0.45 * u)
                d[f"thigh.{side}"] = k * u * 0.45 * u
        seam = 1 - smoothstep(0.035, 0.095, abs(p.x))
        if seam > 0:
            tot = sum(d.values())
            hw = max(d["hips"] / tot, 0.5 * seam)
            rest_ = tot - d["hips"]
            k = (1 - hw) / rest_ if rest_ > 1e-6 else 0
            d = {b_: (w * k if b_ != "hips" else 0) for b_, w in d.items()}
            d["hips"] = hw
        return d
    def core_w(p):
        # crotch panel: mostly hips (it sits between the thighs under the skirt), so wide stances
        # do not tear it between the legs
        d = shorts_w(p)
        tot = sum(d.values())
        hw = max(d["hips"] / tot, 0.78)
        rest_ = tot - d["hips"]
        k = (1 - hw) / rest_ if rest_ > 1e-6 else 0
        d = {b_: (w * k if b_ != "hips" else 0) for b_, w in d.items()}
        d["hips"] = hw
        return d
    mb.wfn = core_w
    nu = 28
    rows = []
    for j in range(7):
        z = lerp(1.02, 0.86, j / 6)      # round 3 (TA): short crotch panel; the leg cuffs do the rest
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
    mb.wfn = shorts_w
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
    """Black heeled sandals, round 3 (AD/TA/GD): thin dark[0] sole + stiletto point, dark[1]
    toe vamp and criss-cross straps, ONE thin ankle ring with a visible skin gap above the sole,
    no heel counter (the skin heel/ankle reads from the back).  Weights: sole, heel and vamp
    100% foot (toe region -> toe); only the ankle ring and the strap ends above the malleolus
    follow the shin."""
    for side in ("L", "R"):
        s = 1 if side == "L" else -1
        x = 0.14 * s
        mb = MB()
        ballp = V((x, -0.11, 0.035))

        def rigid_w(p, side=side, ballp=ballp):
            k = smoothstep(-0.02, 0.02, ballp.y - p.y)      # in front of the ball -> toe
            return {f"foot.{side}": 1 - k, f"toe.{side}": k}

        def strap_w(p, side=side):
            # straps + ankle ring ride rigidly on the foot (TA: shoe max edge ratio < 1.3)
            return {f"foot.{side}": 1.0}
        mb.wfn = rigid_w
        # sole (follows the foot slope), thin
        sole = catmull([V((x, 0.10, 0.145)), V((x, 0.04, 0.125)), V((x, -0.06, 0.05)), V((x, -0.15, 0.012)),
                        V((x, -0.215, 0.012))], 12)

        def sr(t, ph):
            w = lerp(0.044, 0.058, smoothstep(0.3, 0.8, t)) * (1 - 0.55 * smoothstep(0.9, 1.0, t))
            return (0.015, w)
        tube(mb, sole, sr, "M_dark1_flat", nseg=10)
        # stiletto: thin tapered post to a point
        tube(mb, [V((x, 0.085, 0.14)), V((x, 0.080, 0.07)), V((x, 0.076, 0.0))],
             lambda t, ph: lerp(0.024, 0.009, t), "M_ink", nseg=8)
        # closed toe vamp (dark[1])
        ellipsoid(mb, (x, -0.165, 0.038), (0.064, 0.066, 0.044), "M_dark1_flat", nu=14, nv=8)
        # criss-cross instep straps (vamp sides -> opposite side of the ankle)
        mb.wfn = strap_w
        for k in (1, -1):
            a = V((x + 0.056 * k, -0.105, 0.045))
            m = V((x, -0.06, 0.115))
            b = V((x - 0.066 * k, 0.02, 0.225))
            tube(mb, catmull([a, m + V((0, -0.035, 0)), b], 8), lambda t, ph: (0.013, 0.007), "M_dark1_flat",
                 nseg=6, up=V((0, -1, 0.4)))
        # one thin ankle ring
        ring = [V((x + math.sin(a) * 0.066, 0.035 - math.cos(a) * 0.064, 0.235))
                for a in [2 * PI * k / 22 for k in range(23)]]
        tube(mb, ring, lambda t, ph: (0.011, 0.007), "M_dark1_flat", nseg=6, cap0=False, cap1=False)
        ob = mb.build(f"shoe.{side}", coll)
        finish(ob, rig, subsurf=1, outline_px=1.0)


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
        path = catmull([pts[0] + V((-0.03 * s, -0.05, 0.03))] + pts, 34)
        T, N, B = frames_along(path, V((0, 1, 0)))
        rows = []
        n = len(path)
        for k, p in enumerate(path):
            t = k / (n - 1)
            # round 7 (gate 'scarf_near_arm' in N): the ribbon stays narrow (~1 px) through the
            # shoulder band, where the bare shoulder caps sit 2-3 px away on screen, then widens
            w = lerp(0.022, 0.080, smoothstep(0.32, 0.72, t))   # tied narrow at the collar, ~3 px at the tails
            w += 0.016 * smoothstep(0.78, 1.0, t)               # round 7 (Gemini): flared tips
            # width axis: horizontal-ish (tangential around the body), twisted along the ribbon
            radial = V((p.x, p.y - 0.05, 0)).normalized()
            wd0 = V((0, 0, 1)).cross(radial)
            tw = s * (0.15 + 0.9 * t) + 0.35 * math.sin(2 * PI * t)
            q = Quaternion(T[k], tw)
            wd = q @ wd0
            wd = (wd - T[k] * wd.dot(T[k])).normalized()
            a, b = p - wd * w, p + wd * w
            if k == n - 1:
                # round 5 (Gemini 'jagged tips'): clean swallowtail -- the two points extend past
                # the end, the V centre stays AHEAD of the previous row (no folded faces)
                rows.append([a + T[k] * 0.075, p.lerp(a, 0.5) + T[k] * 0.040, p + T[k] * 0.004,
                             p.lerp(b, 0.5) + T[k] * 0.040, b + T[k] * 0.075])
            else:
                rows.append([a, p.lerp(a, 0.5), p, p.lerp(b, 0.5), b])
        mb.grid(rows, "M_pink")
        ob = mb.build(f"scarf.{side}", coll, outward=lambda c: V((0, 0.05, c.z)))
        ob.data.materials.append(MATS["M_scarf_under"])
        finish(ob, rig, subsurf=1, thick=0.012, thick_offset=-1, shell_mat_offset=1, outline_px=1.0)


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
    # round 4: same crescent orientation as the sprite variant (long horn back toward the blade)
    cc = V((0, g0 + 0.02, end_z + hook_r))
    arc = []
    for k in range(17):
        a = math.radians(lerp(-75, 165, k / 16))
        arc.append(cc + V((0, math.sin(a) * hook_r * (1.25 if a > 0 else 1.0), -math.cos(a) * hook_r)))
    def hr(t, ph):
        a = lerp(-75, 165, t)
        mid = 1 - abs(a - 40) / 130
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


def katana_sprite_mesh(mb, kmb=None):
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
        # round 4 (GD): >= 2 px wide for the first 60% from the guard, then tapering
        rz = 0.078 * (1 - 0.30 * smoothstep(0.55, 1.0, t)) * (1 - 0.85 * tip) + 0.004
        rx = 0.064 * (1 - 0.30 * smoothstep(0.55, 1.0, t)) * (1 - 0.85 * tip) + 0.004
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
    end_z = -bar_len * 0.30 + bar_len / 2
    # round 4: the spine-side arm of the bar is short (it read as a second prong -> 'fork' at
    # 64 px); the edge-side arm carries the crescent
    # round 5 (GD 'symmetric cross-guard at 64 px'): the spine-side stub is cut to ~1 px, so the
    # guard reads as a lopsided hook, not a cross
    box(mb, (0, g0, end_z - 0.045), (0.06, 0.06, 0.09), "M_steel1_flat")
    # round 4 (AD/GD 'kagi not readable'): bigger crescent (0.30 H tip to tip, >= 0.18 H off
    # the bar), thicker, and built as its own object 'katana_sprite_kagi' so the object-ID pass
    # can measure it (checks.json hook_px) and sprite_post can give it a steel[0] outline
    # the crescent sits off the edge-side end of the bar and its long horn curves back toward
    # the BLADE (+Y, bible section 2), away from the hand / tsuka so it never merges with them
    hook_r = 0.135
    cc = V((0, g0 + 0.03, end_z + hook_r * 1.05))
    arc = []
    for k in range(19):
        a = math.radians(lerp(-25, 170, k / 18))
        arc.append(cc + V((0, math.sin(a) * hook_r * (1.25 if a > 0 else 1.0), -math.cos(a) * hook_r)))

    def hr(t, ph):
        a = lerp(-25, 170, t)
        mid = 1 - abs(a - 30) / 140
        return (0.045, 0.016 + 0.042 * max(0.0, mid) ** 0.7)
    tube(kmb if kmb is not None else mb, arc, hr, "M_steel1_flat", nseg=8, up=V((1, 0, 0)))
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
    kmb = MB()
    katana_sprite_mesh(mb, kmb)
    for nm, m_ in (("katana_sprite", mb), ("katana_sprite_kagi", kmb)):
        ob2 = m_.build(nm, coll)
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
# round 4 (AD 'sprite height'): ortho scale 6.5 -> 7.3 H per 128 px cell (17.5 px / H), so the
# bow top lands at ~56-58 px above the sole (bible section 5) instead of 64 px
ISO_ORTHO = 7.3


def add_bow_billboard(rig, cam):
    """Round 4 (AD 'bow reads as a spike in W/SW, pink sliver in N'): a stiff ribbon bow is
    presented to the camera like a 2D sprite.  Locked Track on the 'bow' bone (lock = bone Y =
    up, track = bone Z = bow front) toward the camera, influence driven by rig prop
    'bow_face_camera' (default 0.85).  Both loops + the red[0] opening read in all 8 directions;
    the knot stays on her right at the bun base, so its screen position still tells NE/N/NW."""
    _set_prop(rig, "bow_face_camera", 0.85, "Bow loops turn toward the camera (sprite read)")
    c = rig.pose.bones["bow"].constraints.new("LOCKED_TRACK")
    c.name = "face_camera"
    c.target = cam
    c.track_axis = "TRACK_Z"
    c.lock_axis = "LOCK_Y"
    _driver_prop(c, "influence", rig, "bow_face_camera")


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
    cam_d.ortho_scale = ISO_ORTHO
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


def flat_to_camera_edge(d, yaw, head=None):
    """Round 4 (AD/GD 'kagi never reads'): edge direction for blade direction d such that the
    blade FLAT faces the iso camera of direction `yaw` (the crescent guard lies in the blade
    plane, so it reads in full profile instead of edge-on).  Edge points to the lower side."""
    el = math.radians(ISO_ELEV)
    v = Matrix.Rotation(math.radians(-yaw), 3, "Z") @ V((0, math.cos(el), -math.sin(el)))
    d = V(d).normalized()
    x = v - d * v.dot(d)
    if x.length < 1e-4:
        return V((0, 0, -1))
    x.normalize()
    z = d.cross(x).normalized()
    if head is None:
        return z if z.z <= 0 else -z
    # the hook side (edge, +Z) points away from the body on screen (outward of the grip) and a
    # little downward, so the crescent is never hidden behind the hand / sleeve / body
    hx, _ = iso_screen(yaw, V((head.x, head.y, 0)))
    side = 1 if hx >= 0 else -1

    def score(zz):
        sx, sy = iso_screen(yaw, zz)
        return sx * side - 0.3 * sy
    return z if score(z) >= score(-z) else -z


HOOK_ROLL = {}          # iso yaw (deg) -> extra blade roll (deg), filled by solve_hook_roll()
HOOK_SEARCH_DIRS = ("NE", "E")


def kagi_free_cells(rig, yaw, mask, dv):
    kg = bpy.data.objects["katana_sprite_kagi"]
    dg = bpy.context.evaluated_depsgraph_get()
    ev = kg.evaluated_get(dg)
    me = ev.to_mesh()
    cells = set()
    for v in me.vertices:
        sx, sy = iso_screen(yaw, ev.matrix_world @ v.co)
        cells.add((int(104 - sy * CELL_PPU), int(64 + sx * CELL_PPU)))
    ev.to_mesh_clear()
    head = rig.pose.bones["sword"].matrix.translation.copy()
    bl = set()
    for k in range(40):
        p_ = head + dv * (KATANA_OFF + GUARD_Y + 0.05 + (BLADE_LEN - 0.05) * k / 39)
        sx, sy = iso_screen(yaw, p_)
        y0, x0 = int(104 - sy * CELL_PPU), int(64 + sx * CELL_PPU)
        for dy in (-1, 0, 1, 2):
            for dx in (-1, 0, 1, 2):
                bl.add((y0 + dy, x0 + dx))
    free = {(y, x) for (y, x) in cells if 0 <= y < 128 and 0 <= x < 128 and not mask[y, x] and (y, x) not in bl}
    # round 6 (hook_connected fails): score = LARGEST 8-connected group of free kagi cells, so a
    # crescent split by the hand / blade scores low even when many cells are free
    best, seen = 0, set()
    for c0 in free:
        if c0 in seen:
            continue
        st, n = [c0], 0
        seen.add(c0)
        while st:
            cy, cx = st.pop()
            n += 1
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    q = (cy + dy, cx + dx)
                    if q in free and q not in seen:
                        seen.add(q)
                        st.append(q)
        best = max(best, n)
    return best


def solve_pose_hook_roll(rig, az, de, yaws, label="", max_roll=180):
    """Round 5 (AD 'guard inside the cuff' in pose cells): roll the blade about its axis so the
    kagi is clear of hands / cuffs in ALL listed views (maximise the worst view)."""
    masks = screen_masks(list(yaws))
    a, e = math.radians(az), math.radians(de)
    dv = V((math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), -math.sin(e)))
    best = None
    for r in range(-max_roll, max_roll if max_roll == 180 else max_roll + 1, 15):
        set_sword_dir(rig, az, de, yaw=yaws[0], outward=False, extra_roll=float(r))
        fr = [kagi_free_cells(rig, y, masks[y], dv) for y in yaws]
        sc = min(fr) - 0.02 * abs(r)       # prefer the flat-to-camera roll
        if best is None or sc > best[0]:
            best = (sc, r, fr)
    set_sword_dir(rig, az, de, yaw=yaws[0], outward=False, extra_roll=float(best[1]))
    print(f"[hook roll] {label}: extra roll {best[1]} deg, free kagi cells {best[2]}")
    return best[1]


def solve_hook_roll(rig, dname, az, de):
    """Round 5: for `dname`, try extra rolls of the blade about its own axis and keep the one
    whose projected kagi has the most cells clear of the body silhouette and of the blade line
    (small penalty for leaving the flat-to-camera roll)."""
    import numpy as np
    yaw = ISO_DIRS.index(dname) * 45.0
    key = int(round(yaw)) % 360
    HOOK_ROLL.pop(key, None)
    masks = screen_masks([yaw])
    mask = masks[yaw]
    kg = bpy.data.objects["katana_sprite_kagi"]
    best = None
    a, e = math.radians(az), math.radians(de)
    dv = V((math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), -math.sin(e)))
    for r in range(-90, 91, 10):
        HOOK_ROLL[key] = float(r)
        set_sword_dir(rig, az, de, yaw=yaw)
        dg = bpy.context.evaluated_depsgraph_get()
        ev = kg.evaluated_get(dg)
        me = ev.to_mesh()
        cells = set()
        for v in me.vertices:
            sx, sy = iso_screen(yaw, ev.matrix_world @ v.co)
            cells.add((int(104 - sy * CELL_PPU), int(64 + sx * CELL_PPU)))
        ev.to_mesh_clear()
        head = rig.pose.bones["sword"].matrix.translation.copy()
        bl = set()
        for k in range(40):
            p_ = head + dv * (KATANA_OFF + GUARD_Y + 0.05 + (BLADE_LEN - 0.05) * k / 39)
            sx, sy = iso_screen(yaw, p_)
            y0, x0 = int(104 - sy * CELL_PPU), int(64 + sx * CELL_PPU)
            for dy in (-1, 0, 1, 2):
                for dx in (-1, 0, 1, 2):
                    bl.add((y0 + dy, x0 + dx))
        free = sum(1 for (y, x) in cells if 0 <= y < 128 and 0 <= x < 128 and not mask[y, x] and (y, x) not in bl)
        score = free - 0.04 * abs(r)
        if best is None or score > best[0]:
            best = (score, r, free)
    HOOK_ROLL[key] = float(best[1])
    set_sword_dir(rig, az, de, yaw=yaw)
    print(f"[hook roll] {dname}: extra roll {best[1]} deg, ~{best[2]} free kagi cells")


def set_sword_dir(rig, az, de, yaw=None, outward=True, extra_roll=None):
    """Aim the sword bone (character-local azimuth from +X toward +Y, and down angle, deg).
    With `yaw` (iso direction in deg) the blade is rolled so its flat faces that camera."""
    bpy.context.view_layer.update()
    a, e = math.radians(az), math.radians(de)
    d = V((math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), -math.sin(e)))
    head = rig.pose.bones["sword"].matrix.translation.copy()
    hint = flat_to_camera_edge(d, yaw, head if outward else None) if yaw is not None else V((0, 0, -1))
    if extra_roll is not None:
        hint = Matrix.Rotation(math.radians(extra_roll), 3, d) @ hint
    elif yaw is not None and outward and int(round(yaw)) % 360 in HOOK_ROLL:
        # round 5 (AD/TA 'NE hook split by the hand'): searched extra roll about the blade axis
        hint = Matrix.Rotation(math.radians(HOOK_ROLL[int(round(yaw)) % 360]), 3, d) @ hint
    rig.pose.bones["sword"].matrix = sword_matrix(head, d, hint)
    bpy.context.view_layer.update()


SCARF_ARM_OBJS = ("arm.L", "arm.R", "hand.L", "hand.R")
SCARF_LOG = []


def _proj_cells(obnames, yaw, dg, occ=None):
    """Projected cells of the objects' evaluated vertices; with occ=(bvh, to_cam) only the
    vertices with a clear line of sight to the iso camera (no occluder hit) count."""
    cells = set()
    for n in obnames:
        o = bpy.data.objects.get(n)
        if o is None:
            continue
        e = o.evaluated_get(dg)
        me = e.to_mesh()
        for v in me.vertices:
            w = e.matrix_world @ v.co
            if occ is not None:
                h = occ[0].ray_cast(w + occ[1] * 0.02, occ[1], 30.0)
                if h[0] is not None:
                    continue
            sx, sy = iso_screen(yaw, w)
            cells.add((int(104 - sy * CELL_PPU), int(64 + sx * CELL_PPU)))
        e.to_mesh_clear()
    return cells


OCC_SKIP = ("scarf.L", "scarf.R", "head_collider", "saya", "katana", "hair_sheen", "bun_sheen", "face_decals")


def _occluder(dg, skip=OCC_SKIP):
    verts, polys = [], []
    for o in bpy.data.objects:
        if o.type != "MESH" or o.hide_render or o.name in skip:
            continue
        e = o.evaluated_get(dg)
        me = e.to_mesh()
        off = len(verts)
        verts += [e.matrix_world @ v.co for v in me.vertices]
        polys += [tuple(i + off for i in p.vertices) for p in me.polygons]
        e.to_mesh_clear()
    return BVHTree.FromPolygons(verts, polys)


def _to_cam(yaw):
    el = math.radians(ISO_ELEV)
    return Matrix.Rotation(math.radians(-yaw), 3, "Z") @ V((0, -math.cos(el), math.sin(el)))


def scarf_crossed(rig, margin=0.04):
    """Round 7 (AD 'scarf X over the bare back'): True when either ribbon crosses the spine line,
    i.e. a scarf.L bone tail lies right of (or a scarf.R tail left of) the neck axis by less
    than `margin` in the neck bone's frame (so torso / head turns do not count as crossing)."""
    bpy.context.view_layer.update()
    nk = rig.pose.bones["neck"].matrix
    nk_rest = rig.data.bones["neck"].matrix_local
    for side in ("L", "R"):
        for nm in scarf_names(side)[1:]:
            pr = nk_rest.inverted() @ rig.data.bones[nm].tail_local
            pp = nk.inverted() @ rig.pose.bones[nm].tail
            sg = 1 if pr.x > 0 else -1
            if pp.x * sg < margin:
                return True
    return False


def scarf_clear(rig, yaws, thresh=2, hang=False):
    """Round 6 (GD/TA 'scarf_near_arm'): per-frame ribbon swing so the pink never runs along a
    bare arm on screen.  The ribbon cells (projected scarf vertices) within 2 px of the bare
    arm / hand cells are counted for each camera; if more than `thresh`, a small set of extra
    swings (splay out / swing to one side about Z, lift about X) is searched and the one with
    the fewest near cells (then the smallest swing) is kept.  Occlusion is ignored (pessimistic)."""
    bpy.context.view_layer.update()
    names = scarf_names("L") + scarf_names("R")
    M0 = {n: rig.pose.bones[n].matrix_basis.copy() for n in names}
    dg = bpy.context.evaluated_depsgraph_get()
    # round 6: occlusion-aware (the body / sleeves / hair do not move while the ribbons swing,
    # so one occluder BVH per frame; arm vertices hidden behind the body do not count either)
    bvh = _occluder(dg)
    armd = {}
    for y in yaws:
        a_ = _proj_cells(SCARF_ARM_OBJS, y, dg, occ=(bvh, _to_cam(y)))
        armd[y] = {(cy + dy, cx + dx) for (cy, cx) in a_ for dy in (-2, -1, 0, 1, 2) for dx in (-2, -1, 0, 1, 2)}

    def tilt_pen():
        # round 8 (AD): hanging ribbons stay within ~22 deg of vertical on screen; every degree
        # over costs 1 near-arm cell
        if not hang:
            return 0.0
        bpy.context.view_layer.update()
        pen = 0.0
        for y in yaws:
            for side in ("L", "R"):
                nm = scarf_names(side)
                a = V(iso_screen(y, rig.pose.bones[nm[0]].head))
                b = V(iso_screen(y, rig.pose.bones[nm[-1]].tail))
                v = b - a
                tl = math.degrees(math.atan2(abs(v.x), -v.y))
                pen += max(0.0, tl - 22.0)
        return pen

    def score():
        dg_ = bpy.context.evaluated_depsgraph_get()
        return sum(len(_proj_cells(("scarf.L", "scarf.R"), y, dg_, occ=(bvh, _to_cam(y))) & armd[y])
                   for y in yaws) + tilt_pen()
    base = score()
    crossed0 = scarf_crossed(rig)
    if base <= thresh and not crossed0:
        SCARF_LAST[0] = None
        return 0
    best = (base + (1000 if crossed0 else 0), 0.0, None)
    W = (0.35, 0.7, 1.0, 1.0, 0.8)
    cands = []
    # round 8: hanging (idle / walk) ribbons only get small swings, so the solve can never
    # lift one into a horizontal shoulder-height spike (AD 'second blade / antenna')
    zset = ((25, -25), (-25, 25), (25, 25), (-25, -25), (40, -40), (40, 40), (-40, -40), (60, -60),
            (-12, 12), (0, 0)) if not hang else \
        ((12, -12), (-12, 12), (12, 12), (-12, -12), (22, -22), (-22, 22), (22, 22), (-22, -22), (0, 0))
    for zl, zr in zset:
        for xl in ((0, -20, 20) if not hang else (0, 8, -6)):
            if (zl, zr, xl) != (0, 0, 0):
                cands.append((zl, zr, xl))
    for (zl, zr, xl) in cands:
        for n in names:
            rig.pose.bones[n].matrix_basis = M0[n]
        bpy.context.view_layer.update()
        for side, z_ in (("L", zl), ("R", zr)):
            if xl:
                curve_chain(rig, scarf_names(side), (1, 0, 0), [xl * w for w in W])
            curve_chain(rig, scarf_names(side), (0, 0, 1), [z_ * w for w in W])
        sc_ = score() + 0.02 * (abs(zl) + abs(zr) + abs(xl))
        if scarf_crossed(rig):
            sc_ += 1000          # never trade the bare-back strip for arm clearance
        if sc_ < best[0]:
            best = (sc_, 0, (zl, zr, xl))
    for n in names:
        rig.pose.bones[n].matrix_basis = M0[n]
    bpy.context.view_layer.update()
    if best[2] is not None:
        zl, zr, xl = best[2]
        for side, z_ in (("L", zl), ("R", zr)):
            if xl:
                curve_chain(rig, scarf_names(side), (1, 0, 0), [xl * w for w in W])
            curve_chain(rig, scarf_names(side), (0, 0, 1), [z_ * w for w in W])
    SCARF_LOG.append((tuple(yaws), base, best[2], round(best[0], 2)))
    SCARF_LAST[0] = best[2]
    return base


SCARF_LAST = [None]


def scarf_apply(rig, cand):
    """Round 8: re-apply one scarf_clear swing (zl, zr, xl) -- the idle / walk cycles share the
    frame-0 solve over all frames, so the ribbons sway smoothly instead of popping between
    per-frame swings (round 7: up to 6 px tip jumps)."""
    if cand is None:
        return
    zl, zr, xl = cand
    for side, z_ in (("L", zl), ("R", zr)):
        if xl:
            curve_chain(rig, scarf_names(side), (1, 0, 0), [xl * w for w in SCARF_W])
        curve_chain(rig, scarf_names(side), (0, 0, 1), [z_ * w for w in SCARF_W])


def store_pose(rig, name):
    bpy.context.view_layer.update()
    if name not in ("rest",):
        dn = name[5:] if name.startswith("idle_") else None
        scarf_clear(rig, [ISO_DIRS.index(dn) * 45.0] if dn in ISO_DIRS else [45.0, 225.0],
                    hang=name.startswith(("idle", "walk")))
    POSES[name] = capture_pose(rig)
    # also as a 1-frame Action (pose library entry) with all bones + props keyed
    act = bpy.data.actions.new(f"pose_{name}")
    act.use_fake_user = True
    rig.animation_data.action = act
    for pb in rig.pose.bones:
        pb.keyframe_insert("location", frame=1, group=pb.name)
        pb.keyframe_insert("rotation_quaternion", frame=1, group=pb.name)
        if pb.name in SCALE_KEYED:
            pb.keyframe_insert("scale", frame=1, group=pb.name)
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


ISO_DIRS = ["S", "SE", "E", "NE", "N", "NW", "W", "SW"]
SWORD_TIP = KATANA_OFF + GUARD_Y + BLADE_LEN       # grip -> tip distance
BODY_FOR_SWORD = ("skirt_outer", "skirt_under", "leg.L", "leg.R", "shoe.L", "shoe.R", "body_torso",
                  "belt_pouch", "thigh_strap.L", "shorts", "corset", "sleeve.R", "arm.R", "sleeve.L",
                  "bodice")


def body_bvh(names=BODY_FOR_SWORD):
    dg = bpy.context.evaluated_depsgraph_get()
    verts, polys = [], []
    for n in names:
        o = bpy.data.objects.get(n)
        if o is None:
            continue
        e = o.evaluated_get(dg)
        me = e.to_mesh()
        off = len(verts)
        verts += [e.matrix_world @ v.co for v in me.vertices]
        polys += [tuple(i + off for i in p.vertices) for p in me.polygons]
        e.to_mesh_clear()
    return BVHTree.FromPolygons(verts, polys)


def sword_clear(bvh, head, d, start=0.36, clearance=0.05):
    """True if the blade (from `start` along it to the tip) does not touch the body meshes."""
    a = head + d * start
    L = SWORD_TIP - start
    if bvh.ray_cast(a, d, L)[0] is not None:
        return False
    for k in range(9):
        p = a + d * (L * k / 8)
        hit = bvh.find_nearest(p)
        if hit[0] is not None and hit[3] < clearance:
            return False
    return True


def iso_screen(yaw_deg, v):
    """(screen x, screen y) of armature-space vector v for the iso camera (30 deg elevation) when
    the character is yawed by yaw_deg (the character rotates, the camera stays)."""
    w = Matrix.Rotation(math.radians(yaw_deg), 3, "Z") @ V(v)
    el = math.radians(ISO_ELEV)
    return w.x, w.y * math.sin(el) + w.z * math.cos(el)


CELL_PPU = 128 / ISO_ORTHO     # sprite cell pixels per H
NO_MASK = ("katana", "katana_sprite", "katana_sprite_kagi", "saya", "head_collider")


def screen_masks(yaws):
    """Approximate 128-cell body silhouettes (no sword) for the given yaws: evaluated vertices
    projected with the iso camera, then a 2-px closing.  Used by the sword-aim searches."""
    import numpy as np
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for o in bpy.data.objects:
        if o.type != "MESH" or o.name in NO_MASK or o.hide_render:
            continue
        e = o.evaluated_get(dg)
        me = e.to_mesh()
        pts += [tuple(e.matrix_world @ v.co) for v in me.vertices]
        e.to_mesh_clear()
    P = np.array(pts)
    out = {}
    for yaw in yaws:
        c, s_ = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        wx = P[:, 0] * c - P[:, 1] * s_
        wy = P[:, 0] * s_ + P[:, 1] * c
        sy = wy * 0.5 + P[:, 2] * math.cos(math.radians(ISO_ELEV))
        px = np.clip((64 + wx * CELL_PPU).astype(int), 0, 127)
        py = np.clip((104 - sy * CELL_PPU).astype(int), 0, 127)
        m = np.zeros((128, 128), bool)
        m[py, px] = True
        for _ in range(2):
            g = m.copy()
            g[1:, :] |= m[:-1, :]; g[:-1, :] |= m[1:, :]; g[:, 1:] |= m[:, :-1]; g[:, :-1] |= m[:, 1:]
            m = g
        g = m.copy()
        g[1:, :] &= m[:-1, :]; g[:-1, :] &= m[1:, :]; g[:, 1:] &= m[:, :-1]; g[:, :-1] &= m[:, 1:]
        out[yaw] = g
    return out


def blade_px_outside(mask, yaw, head, d):
    """Pixels of the (2 px wide) sprite blade outside the body silhouette mask."""
    seen = set()
    for k in range(60):
        p = head + d * (KATANA_OFF + GUARD_Y + 0.05 + (BLADE_LEN - 0.05) * k / 59)
        sx, sy = iso_screen(yaw, p)
        x, y = int(64 + sx * CELL_PPU), int(104 - sy * CELL_PPU)
        for dx in (0, 1):
            for dy in (0, 1):
                xx, yy = x + dx, y + dy
                if 0 <= xx < 128 and 0 <= yy < 128 and not mask[yy, xx]:
                    seen.add((xx, yy))
    return len(seen)


def solve_pose_sword(rig, yaws, pref, min_px=40, label=""):
    """Sword aim for a pose: blade clear of the body and >= min_px blade pixels outside the
    silhouette in every listed iso yaw; among those, minimise pref(d) (pose acting)."""
    bpy.context.view_layer.update()
    bvh = body_bvh()
    masks = screen_masks(yaws)
    head = rig.pose.bones["sword"].matrix.translation.copy()
    best = None
    for ia in range(-36, 36):
        for ie in range(-14, 34):
            az, de = ia * 5.0, ie * 2.5
            a, e = math.radians(az), math.radians(de)
            d = V((math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), -math.sin(e)))
            if head.z + d.z * SWORD_TIP < 0.03:
                continue
            sc = pref(d)
            if best is not None and sc >= best[0]:
                continue
            pxs = [blade_px_outside(masks[y], y, head, d) for y in yaws]
            if min(pxs) < min_px or not sword_clear(bvh, head, d):
                continue
            best = (sc, az, de, pxs)
    if best is None:
        print(f"[pose sword] {label}: no aim found")
        return None
    print(f"[pose sword] {label}: az {best[1]} down {best[2]} px_outside {best[3]}")
    # pose cells are shown from SE AND NW (opposite cameras): the flat faces both, and the hook
    # takes the world-down side, which is the screen-down side in both views
    set_sword_dir(rig, best[1], best[2], yaw=yaws[0], outward=False)
    roll = solve_pose_hook_roll(rig, best[1], best[2], yaws, label=label)
    return best + (roll,)


def sword_az_de(rig):
    bpy.context.view_layer.update()
    d = (rig.pose.bones["sword"].matrix.to_3x3() @ V((0, 1, 0))).normalized()
    return math.degrees(math.atan2(d.y, d.x)), math.degrees(math.asin(clamp(-d.z, -1, 1)))


IDLE_VARIANTS = ("hang", "front", "front_out", "side_high")
IDLE_HAND = {   # IK hand_ik.L location (armature space), yaw (deg), elbow pole
    "front": (V((0.24, -0.34, 0.98)), 25, V((0.80, 0.25, 1.25))),
    "front_out": (V((0.36, -0.28, 1.04)), 35, V((0.90, 0.30, 1.30))),
    "side_high": (V((0.43, -0.13, 1.03)), 40, V((0.95, 0.45, 1.30))),
}


# round 5 (GD 'NE idle sword 43 deg'): per-direction nudge of the relaxed left hand (armature
# space, added to the variant's hand_ik.L location): NE only, slightly FORWARD and OUTWARD (not
# back) so the blade can reach the 30 deg screen angle clear of the skirt
IDLE_HAND_DIR_OFF = {"NE": V((0.32, -0.02, 0.10))}


def apply_idle_variant(rig, v, dname=None):
    """'hang': left arm hangs (FK rest).  'front': the relaxed left arm swings slightly forward so
    the hand rests in front of her left hip and the blade can angle down-forward across the
    front (used where the left hand is on the far side of the body: E / NE)."""
    if v in IDLE_HAND:
        loc, yw, pole = IDLE_HAND[v]
        loc = loc + IDLE_HAND_DIR_OFF.get(dname, V())
        set_props(rig, ik_arm__L=1)
        place_ctrl(rig, "hand_ik.L", loc=loc, yaw=yw)
        place_ctrl(rig, "elbow_pole.L", loc=pole)
    bpy.context.view_layer.update()


def solve_idle_sword(rig):
    """Per-direction idle katana aim (round 3, AD/GD):
      * blade hangs down and outward: screen angle from straight down as close to 30 deg as
        the 2.0 H blade allows (tip may stop just above the floor, z >= 0.03)
      * blade clear of the silhouette (>= 40 px outside, approx. mask) and of the body (0.05 H)
      * never a tail: pointing backward in 3D AND against the facing side on screen is
        penalised hard (GD)
      * two arm variants are tried ('hang' and 'front', see apply_idle_variant); 'front' costs
        a small penalty so the natural hang wins whenever it can satisfy the rules
    Returns {dir: (variant, azimuth from +X toward +Y, down angle)} in degrees."""
    base = {pb.name: pb.matrix_basis.copy() for pb in rig.pose.bones}
    props = {k: float(rig[k]) for k in POSE_PROPS}
    zmin = 0.03
    allv = {}
    for var in IDLE_VARIANTS:
        out = {d: None for d in ISO_DIRS}
        allv[var] = out
        for pb in rig.pose.bones:
            pb.matrix_basis = base[pb.name]
        set_props(rig, **{k.replace(".", "__"): v for k, v in props.items()})
        apply_idle_variant(rig, var)
        bvh = body_bvh()
        masks = screen_masks([i * 45.0 for i in range(8)])
        head = rig.pose.bones["sword"].matrix.translation.copy()
        hand = rig.pose.bones["hand.L"].matrix.translation.copy()
        vpen = 0.0
        for i, dname in enumerate(ISO_DIRS):
            yaw = i * 45.0
            hx, _ = iso_screen(yaw, V((hand.x, hand.y, 0)))
            fsx, _ = iso_screen(yaw, V((0, -1, 0)))
            req = math.copysign(1, hx)
            best = out[dname]
            for ia in range(-36, 36):
                az = ia * 5.0
                for ie in range(2, 34):
                    de = ie * 2.5
                    a, e = math.radians(az), math.radians(de)
                    d = V((math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), -math.sin(e)))
                    if head.z + d.z * SWORD_TIP < zmin:
                        continue
                    if var == "hang" and d.x < 0.12:
                        continue
                    sx, sy = iso_screen(yaw, d)
                    if sy > -0.12:
                        continue
                    if abs(fsx) < 0.1 and sx * req < 0.05:      # S / N: on the hand's side
                        continue
                    ang = math.degrees(math.atan2(abs(sx), -sy))
                    slen = math.hypot(sx, sy)
                    trail = max(0.0, d.y - 0.15) * max(0.0, -math.copysign(1, sx) * fsx) / 0.707
                    # round 4 (TA/GD): screen angle dominates (every direction within ~10 deg of
                    # 30), a slight tail is acceptable (TA) -> trail penalty 60 -> 8
                    score = vpen + 2.0 * abs(ang - 30) + 8 * trail + 4 * max(0.0, d.y - 0.25) \
                        + 40 * max(0.0, 0.75 - slen) + 4 * max(0.0, -d.y - 0.6)
                    if best is not None and score >= best[0]:
                        continue
                    if not sword_clear(bvh, head, d):
                        continue
                    px = blade_px_outside(masks[yaw], yaw, head, d)
                    if px < 40:
                        continue
                    best = (score, var, az, de, ang, slen, px)
            out[dname] = best
    for pb in rig.pose.bones:
        pb.matrix_basis = base[pb.name]
    set_props(rig, **{k.replace(".", "__"): v for k, v in props.items()})
    # round 4 (TA 'pick ONE idle arm variant'): the variant that solves all 8 directions with
    # the lowest total score is used everywhere, so the arm never pops between directions
    def total(var):
        o = allv[var]
        return sum(o[d][0] if o[d] else 1e6 for d in ISO_DIRS)
    var_best = min(IDLE_VARIANTS, key=total)
    out = allv[var_best]
    # round 5: directions with a hand nudge are re-solved with the nudged hand
    for dname, off in IDLE_HAND_DIR_OFF.items():
        if var_best not in IDLE_HAND:
            continue
        for pb in rig.pose.bones:
            pb.matrix_basis = base[pb.name]
        set_props(rig, **{k.replace(".", "__"): v for k, v in props.items()})
        apply_idle_variant(rig, var_best, dname)
        bvh = body_bvh()
        yaw = ISO_DIRS.index(dname) * 45.0
        masks = screen_masks([yaw])
        head = rig.pose.bones["sword"].matrix.translation.copy()
        hand = rig.pose.bones["hand.L"].matrix.translation.copy()
        hx, _ = iso_screen(yaw, V((hand.x, hand.y, 0)))
        fsx, _ = iso_screen(yaw, V((0, -1, 0)))
        best = None
        for ia in range(-36, 36):
            az = ia * 5.0
            for ie in range(2, 34):
                de = ie * 2.5
                a, e = math.radians(az), math.radians(de)
                d = V((math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), -math.sin(e)))
                if head.z + d.z * SWORD_TIP < zmin:
                    continue
                sx, sy = iso_screen(yaw, d)
                if sy > -0.12:
                    continue
                ang = math.degrees(math.atan2(abs(sx), -sy))
                slen = math.hypot(sx, sy)
                trail = max(0.0, d.y - 0.15) * max(0.0, -math.copysign(1, sx) * fsx) / 0.707
                score = 2.0 * abs(ang - 30) + 8 * trail + 4 * max(0.0, d.y - 0.25) \
                    + 40 * max(0.0, 0.75 - slen) + 4 * max(0.0, -d.y - 0.6)
                if best is not None and score >= best[0]:
                    continue
                if not sword_clear(bvh, head, d):
                    continue
                px = blade_px_outside(masks[yaw], yaw, head, d)
                if px < 40:
                    continue
                best = (score, var_best, az, de, ang, slen, px)
        if best is not None and (out[dname] is None or best[0] < out[dname][0]):
            out = dict(out)
            out[dname] = best
            print(f"[idle sword] {dname}: hand nudge {tuple(round(c, 3) for c in off)} accepted")
        else:
            IDLE_HAND_DIR_OFF.pop(dname)
    for pb in rig.pose.bones:
        pb.matrix_basis = base[pb.name]
    set_props(rig, **{k.replace(".", "__"): v for k, v in props.items()})
    print(f"[idle sword] variant totals: " + ", ".join(f"{v}={total(v):.1f}" for v in IDLE_VARIANTS)
          + f" -> {var_best}")
    res = {}
    for dname in ISO_DIRS:
        b_ = out[dname] or (0, var_best, 0.0, 28.0, 0, 0, 0)
        res[dname] = (b_[1], b_[2], b_[3])
        print(f"[idle sword] {dname}: {b_[1]} az {b_[2]:.1f} down {b_[3]:.1f} -> screen {b_[4]:.1f} deg "
              f"from vertical, screen len {b_[5]:.2f}, ~{b_[6]} px outside")
    return res


BOW_DZ_DIR = {"E": 0.23, "NE": 0.25, "N": 0.23, "NW": 0.10, "SE": 0.04, "SW": -0.01, "W": 0.08}
# round 8: with the knot at the bun BASE (front-right), the inner ear hides behind the bun in the
# back views; there the bow slides out to her right (-X) and up the bun side so BOTH ears clear it
BOW_DX_DIR = {"N": -0.14, "NE": -0.10, "NW": -0.14}
# round 8: in W / SW (and the ortho side / 3/4 views, which use those poses) the bow is on the far
# side of the bun and its back ear dipped into the bun; the pair is rolled 18 deg about the view
# axis so the back ear rises clear of the bun crown
BOW_ROLL_DIR = {"W": 18.0, "SW": 18.0}
HEAD_PITCH_DIR = {"N": 22.0, "NE": 18.0, "NW": 18.0, "E": 6.0, "W": 6.0,
                  "S": -5.0, "SE": -5.0, "SW": -5.0}   # round 7 (AD face): slight extra chin-up toward the camera


def dir_turn(rig, dname, scarf=True):
    """Per-direction presentation turn (idle poses AND the per-direction cycles).  scarf=False
    (round 7, run): the streaming ribbons keep their own run solve."""
    if dname in ("E", "W"):
        # round 3 (GD): chest + head turn toward the camera so the profile shows the eye and
        # the face edge (not a sliver); feet / facing stay E / W
        k = -1 if dname == "E" else 1
        rotate_world(rig, "chest", (0, 0, 1), math.radians(10 * k))
        rotate_world(rig, "head", (0, 0, 1), math.radians(12 * k))
    if dname in ("SE", "SW"):
        # head turns ~10 deg toward the camera: both eyes read (AD/TA 'one-eyed' SE / SW)
        rotate_world(rig, "head", (0, 0, 1), math.radians(-10 if dname == "SE" else 10))
        # round 4 (GD/TA 'ribbon beside the bare arm'): the ribbons swing to the FAR side, away
        # from the near (camera-side) shoulder, so they never run along the bare arm
        k = 1 if dname == "SE" else -1
        for side in ("L", "R") if scarf else ():
            curve_chain(rig, scarf_names(side), (0, 0, 1), [14 * k, 14 * k, 10 * k, 7 * k, 5 * k])
    if dname in ("NE", "NW"):
        # round 4 (GD 'NE/N/NW identical backs'): torso + head turn toward the camera, so one
        # shoulder blade / sleeve leads and a sliver of cheek + bang edge shows on the facing
        # side; the scarf tails swing to the side opposite the facing.  N stays symmetric.
        k = -1 if dname == "NE" else 1
        rotate_world(rig, "hips", (0, 0, 1), math.radians(8 * k))
        rotate_world(rig, "chest", (0, 0, 1), math.radians(12 * k))
        # round 5: head 16 -> 3 deg -- with the hair pulled up tight (ear visible), the cheek +
        # ear already show from behind; a bigger turn made a 6 px skin patch
        rotate_world(rig, "head", (0, 0, 1), math.radians(3 * k))
        # round 7: only the ribbon on the far side swings (outward), so the two never cross
        for side in (("L",) if dname == "NE" else ("R",)) if scarf else ():
            curve_chain(rig, scarf_names(side), (0, 0, 1), [6 * k, 8 * k, 8 * k, 6 * k, 4 * k])
    if dname in HEAD_PITCH_DIR:
        # round 6 (AD/GD/TA 'N/NE head band 51-52 px'): the idle chin-up (-12 deg, for more face
        # at 30 deg) tips the set-back bun + bow TOWARD the camera in the back views, so they
        # dropped ~3 px on screen.  Facing away, the head pitches forward instead (nobody sees
        # the face), which keeps the bun/bow top at the same screen height in every direction
        rotate_world(rig, "head", (1, 0, 0), math.radians(HEAD_PITCH_DIR[dname]))
    if dname in BOW_DZ_DIR:
        # round 6 (TA 'height spread <= 3 px'): the camera-facing bow sits off-axis (her right,
        # behind), so its loop tips land 5 px higher in W/SW than in E/NE.  A small per-direction
        # slide of the bow along the bun side evens the silhouette top (bow stays on the bun)
        move(rig, "bow", (BOW_DX_DIR.get(dname, 0.0), 0, BOW_DZ_DIR[dname]))
    if dname in BOW_ROLL_DIR:
        cdir = Matrix.Rotation(math.radians(-ISO_DIRS.index(dname) * 45.0), 3, "Z") @ V((0, -1, 0))
        rotate_world(rig, "bow", cdir, math.radians(BOW_ROLL_DIR[dname]))


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
    rotate_world(rig, "head", (1, 0, 0), math.radians(-12))     # chin up: more face for the 30 deg camera
    rotate_world(rig, "head", (0, 1, 0), math.radians(2))
    idle_feet(rig)
    curve_chain(rig, scarf_names("L"), (0, 0, 1), [3, 4, 5, 5, 4])
    curve_chain(rig, scarf_names("R"), (0, 0, 1), [3, 4, 5, 5, 4])
    # round 3 (AD/GD): the idle katana HANGS from the left hand, blade down and outward, tip
    # toward the ground.  One aim per iso direction, found by a geometric search (see
    # solve_idle_sword); pose_idle == pose_idle_S.
    IDLE_SWORD_DIR.clear()
    IDLE_SWORD_DIR.update(solve_idle_sword(rig))
    base = {pb.name: pb.matrix_basis.copy() for pb in rig.pose.bones}
    for dname in ISO_DIRS:
        for pb in rig.pose.bones:
            pb.matrix_basis = base[pb.name]
        bpy.context.view_layer.update()
        var, az, de = IDLE_SWORD_DIR[dname]
        set_props(rig, ik_arm__L=0)
        apply_idle_variant(rig, var, dname)
        dir_turn(rig, dname, scarf=False)
        idle_scarf(rig, 0.0)          # round 8 (AD): hanging ribbons, no streaming rest curve
        set_sword_dir(rig, az, de, yaw=ISO_DIRS.index(dname) * 45.0)
        if dname in HOOK_SEARCH_DIRS:
            solve_hook_roll(rig, dname, az, de)
        store_pose(rig, f"idle_{dname}")
        if dname == "S":
            store_pose(rig, "idle")
    for pb in rig.pose.bones:
        pb.matrix_basis = base[pb.name]
    set_props(rig, ik_arm__L=0)
    bpy.context.view_layer.update()

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
    idle_scarf(rig, 0.0, walk=1.0, sway=0.05)     # round 8: same hanging walk ribbons as anim_walk
    rotate_world(rig, "skirt.B", (1, 0, 0), math.radians(-6))
    # round 6 (TA 'blade_outside walk_contact SE'): the blade is aimed by the pose solver (was the
    # FK rest direction: 28 px outside the SE silhouette, gate 30)
    b_ = solve_pose_sword(rig, (45.0, 225.0), lambda d: -0.8 * d.x - 0.6 * d.y + 2.0 * abs(d.z + 0.6),
                          min_px=42, label="walk_contact")
    if b_ is None:
        az_, de_ = sword_az_de(rig)
        solve_pose_hook_roll(rig, az_, de_, (45.0, 225.0), label="walk_contact")
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
    # run (round 3, AD/GD): blade trails low and back-out, breaking the silhouette in SE + NW
    solve_pose_sword(rig, (45.0, 225.0), lambda d: -1.2 * d.y - 0.8 * d.x + 2.0 * abs(d.z + 0.45),
                     label="run_stride")
    run_scarf(rig, 0.0)        # round 7: streaming ribbons (same solve as anim_run)
    for side in ("L", "R"):
        rotate_world(rig, f"sleeve.{side}", (1, 0, 0), math.radians(-35))
    rotate_world(rig, "skirt.B", (1, 0, 0), math.radians(-18))
    curve_chain(rig, ["skirt.tail.001", "skirt.tail.002", "skirt.tail.003"], (1, 0, 0), [-12, -10, -8])
    store_pose(rig, "run_stride")

    # --- jump apex (refs/3): arched back, chin up, legs together bent back, cloth flares up
    clear_pose(rig)
    move(rig, "cog", (0, 0.0, 0.04))
    # round 8 (AD): arched back + chin up (was a forward tuck: spine +8, chest +6, head +10)
    rotate_world(rig, "spine", (1, 0, 0), math.radians(-10))
    rotate_world(rig, "chest", (1, 0, 0), math.radians(-8))
    rotate_world(rig, "head", (1, 0, 0), math.radians(-12))
    pose_feet(rig, "L", (0.06, 0.44, 0.44), yaw=0)
    pose_feet(rig, "R", (-0.06, 0.40, 0.38), yaw=0)
    for side in ("L", "R"):
        rotate_world(rig, f"foot_ik.{side}", (1, 0, 0), math.radians(-55))
        aim_pole_knee(rig, side, (0, -1, -0.2))
    rotate_world(rig, "upper_arm.L", (0, 1, 0), math.radians(-35))
    rotate_world(rig, "upper_arm.L", (1, 0, 0), math.radians(20))
    rotate_world(rig, "upper_arm.R", (0, 1, 0), math.radians(45))
    rotate_world(rig, "forearm.R", (0, 1, 0), math.radians(25))
    for side, s in (("L", 1), ("R", -1)):
        rotate_world(rig, f"sleeve.{side}", (0, 1, 0), math.radians(-50 * s))     # round 8: cuffs flare up
        rotate_world(rig, f"sleeve.{side}", (1, 0, 0), math.radians(14))
        curve_chain(rig, scarf_names(side), (1, 0, 0), [14, 10, 8, 6, 5])     # round 4: lower than r3 (30 deg), off the arms
        rotate_world(rig, f"skirt.{side}", (0, 1, 0), math.radians(-30 * s))
        rotate_world(rig, f"skirt.{side}.001", (0, 1, 0), math.radians(-24 * s))
        rotate_world(rig, f"skirt.{side}.002", (0, 1, 0), math.radians(-16 * s))
    # round 8 (AD, refs/3): the skirt petals flare up and out (front forward, back tails up behind)
    rotate_world(rig, "skirt.F", (1, 0, 0), math.radians(-12))
    rotate_world(rig, "skirt.B", (1, 0, 0), math.radians(14))
    curve_chain(rig, ["skirt.tail.001", "skirt.tail.002", "skirt.tail.003"], (1, 0, 0), [12, 10, 8])
    # jump (round 3): blade held out to her side, slightly raised diagonal across the silhouette
    solve_pose_sword(rig, (45.0, 225.0), lambda d: -1.5 * d.x + 1.5 * abs(d.z + 0.15) + 0.5 * abs(d.y),
                     label="jump_apex")
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
    # round 3: with the bigger chibi head the hands cannot reach over the crown, so the wind-up
    # is a high hasso-style guard: grip in front of the left shoulder, blade up and back past
    # the left side of the head (no hand / blade inside the head)
    pose_two_hand(rig, (0.34, -0.42, 1.55), (0.55, 0.20, 0.81), edge_hint=V((0, -1, 0)), elbow_out=0.6)
    for side in ("L", "R"):     # round 4: ribbons hang close down the spine, away from the raised arms
        curve_chain(rig, scarf_names(side), (1, 0, 0), [-22, -12, -6, -4, -2])
    # blade raised high and out to her left so it breaks the silhouette in SE and NW
    solve_pose_sword(rig, (45.0, 225.0), lambda d: -2.0 * d.z + 0.6 * abs(d.y - 0.2), min_px=40,
                     label="overhead")
    set_props(rig, expr_frown=1)
    store_pose(rig, "overhead")

    # --- attack slash, mid-swing (GD): horizontal two-handed cut sweeping to her left, torso
    # unwound, wide lunge; the blade is the full-width line across the silhouette
    clear_pose(rig)
    move(rig, "cog", (0.04, -0.06, -0.14))
    rotate_world(rig, "hips", (0, 0, 1), math.radians(14))
    rotate_world(rig, "spine", (1, 0, 0), math.radians(-10))
    rotate_world(rig, "chest", (0, 0, 1), math.radians(22))
    rotate_world(rig, "head", (0, 0, 1), math.radians(-14))
    pose_feet(rig, "L", (0.42, -0.42, 0.0), yaw=-30)
    pose_feet(rig, "R", (-0.36, 0.34, 0.0), yaw=30, heel_lift=18)
    aim_pole_knee(rig, "L", (0.8, -1.0, 0))
    aim_pole_knee(rig, "R", (-0.6, -0.6, 0))
    pose_two_hand(rig, (0.18, -0.62, 1.18), (0.86, -0.50, 0.06), edge_hint=V((0.5, -1, 0)), elbow_out=0.5)
    for side in ("L", "R"):
        rotate_world(rig, f"sleeve.{side}", (0, 0, 1), math.radians(-30))
        curve_chain(rig, scarf_names(side), (0, 0, 1), [-10, -14, -16, -16, -12])
    rotate_world(rig, "skirt.B", (0, 0, 1), math.radians(-12))
    curve_chain(rig, ["skirt.tail.001", "skirt.tail.002", "skirt.tail.003"], (0, 0, 1), [-10, -10, -8])
    set_props(rig, expr_frown=1)
    az_, de_ = sword_az_de(rig)
    solve_pose_hook_roll(rig, az_, de_, (45.0, 225.0), label="attack_slash_mid", max_roll=30)
    store_pose(rig, "attack_slash_mid")

    clear_pose(rig)
    rig["poses"] = json.dumps(POSES)
    rig["idle_sword_dir"] = json.dumps(IDLE_SWORD_DIR)
    rig["pose_names"] = ",".join(POSES.keys())


# ----------------------------------------------------------------------------
# keyframed cycles (round 3, TA: animation proof before the sprite stage)
# ----------------------------------------------------------------------------
SCALE_KEYED = ("scarf.L.001", "scarf.R.001")     # round 7: run ribbons stream longer (root scale)


def key_all(rig, f):
    for pb in rig.pose.bones:
        pb.keyframe_insert("location", frame=f, group=pb.name)
        pb.keyframe_insert("rotation_quaternion", frame=f, group=pb.name)
        if pb.name in SCALE_KEYED:
            pb.keyframe_insert("scale", frame=f, group=pb.name)
    for k in POSE_PROPS:
        rig.keyframe_insert(f'["{k}"]', frame=f, group="props")


def new_cycle(rig, name, nframes):
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    act.use_frame_range = True
    act.frame_start = 1
    act.frame_end = nframes + 1          # frame nframes+1 == frame 1 (loop seam); play 1..nframes
    try:
        act.use_cyclic = True
    except Exception:
        pass
    rig.animation_data.action = act
    return act


def finish_cycle(rig, act, interp="LINEAR"):
    for fc in act_fcurves(act):
        for kp in fc.keyframe_points:
            kp.interpolation = interp
    rig.animation_data.action = None


def idle_feet(rig):
    """Round 4 (Gemini 'fused legs'): relaxed A-stance -- heels 0.045 H further apart each, toes
    turned out 8 deg, so a background gap shows between the legs in S / SE / SW sprite cells."""
    for side, s in (("L", 1), ("R", -1)):
        rest = rig.data.bones[f"foot_ctrl.{side}"].head_local
        pose_feet(rig, side, (rest.x + 0.045 * s, rest.y, 0.0), yaw=8 * s)
        aim_pole_knee(rig, side, (0.12 * s, -1, 0))


def idle_body(rig):
    idle_feet(rig)
    rotate_world(rig, "hips", (0, 1, 0), math.radians(2.5))
    rotate_world(rig, "chest", (0, 1, 0), math.radians(-3))
    rotate_world(rig, "head", (1, 0, 0), math.radians(-12))     # chin up: more face for the 30 deg camera
    rotate_world(rig, "head", (0, 1, 0), math.radians(2))


WALK_STRIDE = 0.64      # heel travel per half cycle (H); round 4 (GD): 0.50 -> 0.64, >= 4 px spread


def walk_foot(p):
    """In-place walk foot path for cycle phase p (0..1): stance 0-0.5 (heel from front to back,
    on the floor, constant speed), swing 0.5-1 (lifted, back to front).  Returns (dy, z, toe_lift,
    heel_lift)."""
    h = WALK_STRIDE / 2
    if p < 0.5:
        u = p / 0.5
        dy = -h + WALK_STRIDE * u                       # -Y is forward
        return dy, 0.0, 14.0 * max(0.0, 1 - u * 4), 30.0 * smoothstep(0.55, 1.0, u)
    u = (p - 0.5) / 0.5
    dy = h - WALK_STRIDE * smoothstep(0.0, 1.0, u)
    return dy, 0.13 * math.sin(PI * u), 0.0, 20.0 * (1 - u)


def make_cycles(rig):
    """Round 4 (GD/TA): every cycle exists per iso direction (anim_idle_<D>, anim_walk_<D>) with
    that direction's idle sword aim, arm variant and presentation turn, so turning between
    directions does not pop the sword / arm.  anim_idle / anim_walk (no suffix) = the S version."""
    cyc = {}
    for dname in [None] + ISO_DIRS:
        dk = dname or "S"
        yaw = ISO_DIRS.index(dk) * 45.0
        var, az, de = IDLE_SWORD_DIR[dk]
        sfx = f"_{dname}" if dname else ""
        clear_pose(rig)
        # ---- idle, 8 frames: 1 px breathing bob, scarf / sleeve / skirt-tail drift (lagging)
        act = new_cycle(rig, f"anim_idle{sfx}", 8)
        for f in range(9):
            ph = 2 * PI * (f % 8) / 8
            clear_pose(rig)
            idle_body(rig)
            apply_idle_variant(rig, var, dk)
            dir_turn(rig, dk, scarf=False)
            move(rig, "cog", (0, 0, -0.022 * (1 - math.cos(ph)) / 2))
            rotate_world(rig, "chest", (1, 0, 0), math.radians(1.5 * math.sin(ph)))
            rotate_world(rig, "head", (1, 0, 0), math.radians(-1.2 * math.sin(ph - 0.6)))
            idle_scarf(rig, ph)       # round 8 (AD): hanging ribbons with a ~1 px lateral sway
            for side in ("L", "R"):
                rotate_world(rig, f"sleeve.{side}", (1, 0, 0), math.radians(3 * math.sin(ph - 1.2)))
            curve_chain(rig, ["skirt.tail.001", "skirt.tail.002", "skirt.tail.003"], (1, 0, 0),
                        [1.5 * math.sin(ph - 1.0 - 0.6 * k) for k in range(3)])
            set_sword_dir(rig, az, de, yaw=yaw)
            if dname is not None:
                _dir_fix_sword(rig, yaw, False, f"cycle {dk} f{f}", hook_need=7)
            if f == 0:
                scarf_clear(rig, [yaw], hang=True)
                scarf_cand = SCARF_LAST[0]
            else:
                scarf_apply(rig, scarf_cand)
            key_all(rig, f + 1)
        finish_cycle(rig, act, "BEZIER")
        cyc[f"anim_idle{sfx}"] = dict(frames=8, loop=True, cyclic=True, play="1-8", direction=dk)

        # ---- walk, 8 frames, in place: contact L f0, passing f2, contact R f4, passing f6.  IK
        # feet: the stance heel/ball is planted and slides back at constant speed (no skate)
        act = new_cycle(rig, f"anim_walk{sfx}", 8)
        for f in range(9):
            ph = (f % 8) / 8
            clear_pose(rig)
            bob = -0.012 - 0.022 * (0.5 + 0.5 * math.cos(4 * PI * ph))     # low at contacts
            move(rig, "cog", (0, 0, bob))
            rotate_world(rig, "hips", (0, 0, 1), math.radians(-8 * math.cos(2 * PI * ph)))
            rotate_world(rig, "hips", (0, 1, 0), math.radians(3 * math.sin(2 * PI * ph)))
            rotate_world(rig, "chest", (0, 0, 1), math.radians(10 * math.cos(2 * PI * ph)))
            rotate_world(rig, "head", (1, 0, 0), math.radians(-6))
            dir_turn(rig, dk, scarf=False)
            for side, off in (("L", 0.0), ("R", 0.5)):
                s_ = 1 if side == "L" else -1
                dy, z, tl, hl = walk_foot((ph + off) % 1.0)
                rest = rig.data.bones[f"foot_ctrl.{side}"].head_local
                pose_feet(rig, side, (rest.x, rest.y + dy, z), heel_lift=hl, toe_lift=tl)
                aim_pole_knee(rig, side, (0.05 * s_, -1, 0))
            # arms: right arm swings opposite the right leg; the sword arm swings less
            sw = math.cos(2 * PI * ph)
            rotate_world(rig, "upper_arm.R", (1, 0, 0), math.radians(22 * sw))
            rotate_world(rig, "forearm.R", (1, 0, 0), math.radians(-10 - 8 * sw))
            if var in IDLE_HAND:
                apply_idle_variant(rig, var, dk)
                move(rig, "hand_ik.L", (0, -0.05 * sw, 0))
            else:
                rotate_world(rig, "upper_arm.L", (1, 0, 0), math.radians(-8 * sw))
            # round 8 (AD): hanging ribbons trailing back against the walk velocity, with flutter
            idle_scarf(rig, 4 * PI * ph, walk=1.0, sway=0.05)
            for side in ("L", "R"):
                rotate_world(rig, f"sleeve.{side}", (1, 0, 0), math.radians(-8 + 5 * math.sin(2 * PI * ph - 1.0)))
            curve_chain(rig, ["skirt.tail.001", "skirt.tail.002", "skirt.tail.003"], (1, 0, 0),
                        [-4 - 3 * math.sin(4 * PI * ph - 1.0 - 0.6 * k) for k in range(3)])
            set_sword_dir(rig, az, de, yaw=yaw)
            if dname is not None:
                _dir_fix_sword(rig, yaw, False, f"cycle {dk} f{f}", hook_need=7)
            if f == 0:
                scarf_clear(rig, [yaw], hang=True)
                scarf_cand = SCARF_LAST[0]
            else:
                scarf_apply(rig, scarf_cand)
            key_all(rig, f + 1)
        finish_cycle(rig, act, "LINEAR")
        cyc[f"anim_walk{sfx}"] = dict(frames=8, loop=True, cyclic=True, play="1-8", contacts=[1, 5],
                                     stride=WALK_STRIDE * 2, speed_per_frame=WALK_STRIDE / 4, direction=dk)
    clear_pose(rig)
    make_timed_actions(rig, cyc)
    for dname in ISO_DIRS:          # round 6 (TA): per-direction variants of every timed Action
        clear_pose(rig)
        make_timed_actions(rig, cyc, dname)
    clear_pose(rig)
    for n in POSES:
        cyc[f"pose_{n}"] = dict(frames=1, loop=False, cyclic=False)
    rig["cycles"] = json.dumps(cyc)


RUN_STRIDE = 1.10       # round 6 (GD/TA): 0.90 -> 1.10, legs separate clearly below the tails


def run_foot(p):
    """In-place run foot path (phase 0..1): short stance (0-0.4) at constant speed, long high
    swing with a flight phase.  Returns (dy, z, toe_lift, heel_lift)."""
    h = RUN_STRIDE / 2
    if p < 0.4:
        u = p / 0.4
        return -h + RUN_STRIDE * u, 0.0, 10.0 * max(0.0, 1 - u * 4), 40.0 * smoothstep(0.5, 1.0, u)
    u = (p - 0.4) / 0.6
    # round 6 (GD 'kick the back heel out'): the swing foot lifts EARLY and high behind the body
    # (peak at u ~0.3, heel up, toes down), then reaches forward low for the next contact
    z = 0.42 * math.sin(PI * u ** 0.62) ** 0.8
    return h - RUN_STRIDE * smoothstep(0.0, 1.0, u), z, 0.0, 70.0 * (1 - u) ** 0.7


def new_timed(rig, name, nframes, cyclic=False):
    act = new_cycle(rig, name, nframes) if cyclic else bpy.data.actions.new(name)
    if not cyclic:
        act.use_fake_user = True
        act.use_frame_range = True
        act.frame_start = 1
        act.frame_end = nframes
        rig.animation_data.action = act
    return act


def two_hand_frame(rig, body, grip, sdir, edge, expr="frown", yaws=(45.0, 225.0)):
    clear_pose(rig)
    body()
    pose_two_hand(rig, grip, V(sdir).normalized(), edge_hint=V(edge), elbow_out=0.6)
    if len(yaws) == 1:
        set_props(rig, **{f"expr_{expr}": 1})
        return              # round 6: direction variants are checked by _dir_fix_sword instead
    az_, de_ = sword_az_de(rig)
    # two-hand grips: the right hand follows the tsuka, so the authored roll is kept unless the
    # kagi is hidden in a view; then only a small roll (wrist twist) is searched
    masks = screen_masks(list(yaws))
    a_, e_ = math.radians(az_), math.radians(de_)
    dv = V((math.cos(a_) * math.cos(e_), math.sin(a_) * math.cos(e_), -math.sin(e_)))
    if min(kagi_free_cells(rig, y, masks[y], dv) for y in yaws) < 4:
        solve_pose_hook_roll(rig, az_, de_, tuple(yaws), label="timed two-hand", max_roll=30)
    set_props(rig, **{f"expr_{expr}": 1})


RUN_SCARF_SCALE = 1.40     # round 7 (AD 'scarf absent in run'): ribbons stream 1.5 H (1.1 H rest x 1.4)


def run_scarf(rig, ph):
    """Round 7 (AD must-fix): run ribbons stream AGAINST the velocity (she runs toward -Y, so
    they trail +Y), nearly level at shoulder height with a travelling flutter, and fan out to
    either side so they show past the silhouette in every direction (S: beside the shoulders;
    E/W/SE/SW: behind; N/NE/NW: over the back).  Each bone is aimed absolutely (the round-6
    cumulative -38 deg chain curled the ribbons under themselves), and the root scale makes the
    stream 1.5 H long."""
    for side in ("L", "R"):
        s_ = 1 if side == "L" else -1
        names = scarf_names(side)
        rig.pose.bones[names[0]].scale = (RUN_SCARF_SCALE,) * 3
        bpy.context.view_layer.update()
        for k, nm in enumerate(names):
            t = (k + 1) / len(names)
            fl = math.sin(4 * PI * ph - 0.9 * k)
            # streams back + slightly DOWN (in S the 30 deg camera lifts anything behind her, so a
            # level stream read as pink horns beside the head; this lands it beside the collar)
            d = V((s_ * (0.22 + 0.50 * t), 1.0, -0.10 - 0.55 * t + 0.14 * fl * t)).normalized()
            head = rig.pose.bones[nm].matrix.translation.copy()
            aim(rig, nm, head + d)


IDLE_SCARF_SCALE = 0.93    # round 8 (AD): idle / walk ribbons 1.0 H (1.08 H rest chain x 0.93)
# per-bone hang directions (lateral out, back, down) for the 5 scarf bones: from the collar the
# ribbon drops back over the shoulder blades, then hangs nearly straight down with a gentle
# S-curve (back - in - back) and drifts a little outward at the tail
IDLE_SCARF_DIRS = ((0.10, 0.62, -1.0), (0.17, 0.36, -1.0), (0.02, 0.14, -1.0), (0.12, 0.10, -1.0),
                   (0.28, 0.26, -1.0))


def idle_scarf(rig, ph=0.0, walk=0.0, sway=0.07):
    """Round 8 (AD must-fix 'horizontal shoulder-height ribbon in idle SE/SW'): in idle and walk
    the ribbons HANG (bible: idle ribbons <= 1 H, hanging down, trailing against velocity).
    Each bone is aimed absolutely (like run_scarf), so the result does not depend on the
    streaming rest curve; the root scale shortens the ribbon to ~1.0 H.  ph drives a small
    lateral sway (travelling down the chain, ~1 px at the tip); walk (0..1) adds a backward
    trail against the velocity with a flutter."""
    for side in ("L", "R"):
        s_ = 1 if side == "L" else -1
        names = scarf_names(side)
        rig.pose.bones[names[0]].scale = (IDLE_SCARF_SCALE,) * 3
        bpy.context.view_layer.update()
        for k, nm in enumerate(names):
            t = (k + 1) / len(names)
            lx, by, dz = IDLE_SCARF_DIRS[k]
            lat = lx + sway * t * math.sin(ph - 0.7 * k + (0.0 if side == "L" else 0.9))
            back = by + walk * (0.05 + 0.05 * t + 0.06 * t * math.sin(2 * ph - 0.9 * k))
            d = V((s_ * lat, back, dz)).normalized()
            head = rig.pose.bones[nm].matrix.translation.copy()
            aim(rig, nm, head + d)


RUN_SWORD_SWING = (12.0, 16.0)     # round 6 (GD/TA): +-12 deg azimuth swing, trailing 16 deg further down


def _sword_eval(rig, yaw):
    bpy.context.view_layer.update()
    m = screen_masks([yaw])[yaw]
    head = rig.pose.bones["sword"].matrix.translation.copy()
    az_, de_ = sword_az_de(rig)
    a_, e_ = math.radians(az_), math.radians(de_)
    dv = V((math.cos(a_) * math.cos(e_), math.sin(a_) * math.cos(e_), -math.sin(e_)))
    return m, dv, blade_px_outside(m, yaw, head, dv), kagi_free_cells(rig, yaw, m, dv)


def _roll_search(rig, yaw, m, dv, two_hand):
    M0 = rig.pose.bones["sword"].matrix.copy()
    best = None
    rng = range(-60, 61, 10) if two_hand else range(-180, 180, 15)
    for r in rng:
        Mr = Matrix.Translation(M0.translation) @ Matrix.Rotation(math.radians(r), 4, dv) @ \
            Matrix.Translation(-M0.translation) @ M0
        rig.pose.bones["sword"].matrix = Mr
        bpy.context.view_layer.update()
        f_ = kagi_free_cells(rig, yaw, m, dv)
        if best is None or f_ - 0.02 * abs(r) > best[0]:
            best = (f_ - 0.02 * abs(r), r, Mr, f_)
    rig.pose.bones["sword"].matrix = best[2]
    bpy.context.view_layer.update()
    return best[1], best[3]


def _dir_fix_sword(rig, yaw, two_hand, label, need=40, redo=None, nk=9, hook_need=5):
    """Round 6 (TA 'direction coverage'): per-direction, per-frame sword check at ONE iso yaw
    (approximate silhouette, vertex projection):
      * blade pixels outside the silhouette >= need (margin over the sprite gate of 30-35)
      * kagi: largest connected group of free cells >= hook_need, else a roll about the blade axis
        is searched (two-handed grips: +-60 deg, the right hand follows the tsuka)
    If either fails and `redo(k)` is given, the frame is re-posed with nudge k = 1..nk-1 (blade
    direction, and for one-handed frames also the sword-arm abduction) and the best is kept."""
    m, dv, px, free = _sword_eval(rig, yaw)
    roll = None
    if free < hook_need:
        roll, free = _roll_search(rig, yaw, m, dv, two_hand)
    if (px >= need and free >= hook_need) or redo is None:
        return dict(px=px, nudge=0, roll=roll, free=free)

    def score(px_, fr_):
        return 10.0 * min(px_, need) / need + min(fr_, hook_need + 3)
    best = (score(px, free), 0, roll)
    for k in range(1, nk):
        redo(k)
        m_k, dv_k, px_k, fr_k = _sword_eval(rig, yaw)
        r_k = None
        if fr_k < hook_need:
            r_k, fr_k = _roll_search(rig, yaw, m_k, dv_k, two_hand)
        sc_ = score(px_k, fr_k) - 0.05 * k
        if sc_ > best[0]:
            best = (sc_, k, r_k)
        if px_k >= need and fr_k >= hook_need:
            break
    redo(best[1])
    m, dv, px, free = _sword_eval(rig, yaw)
    if best[2] is not None:
        _roll_search(rig, yaw, m, dv, two_hand)
        m, dv, px, free = _sword_eval(rig, yaw)
    return dict(px=px, nudge=best[1], roll=best[2], free=free)


def make_timed_actions(rig, cyc, dname=None):
    """Round 5 (TA must-fix + nice-to-have): timed Actions that prove the rig through full arcs,
    not just key poses.  All are 'in place' (root does not travel).
      anim_overhead_slash  8 f  windup ABOVE the head (grip beside the crown) -> strike -> follow
      anim_slash           6 f  horizontal two-handed cut (ready -> windup right -> cut -> follow)
      anim_run             8 f  cyclic, contacts f1 / f5, flight phase, sword trailing back
      anim_jump            8 f  3 phases: anticipation (f1-2), air (f3-6, apex f4-5), landing (f7-8)
    Round 6 (TA 'direction coverage'): called once per iso direction too (dname): the variant
    anim_<x>_<D> adds that direction's presentation turn (dir_turn) and re-checks EVERY frame from
    that camera (_dir_fix_sword: blade-outside nudge + kagi roll).  dname None = the base Action
    (S facing, solved for SE + NW as in round 5)."""
    dk = dname or "S"
    sfx = f"_{dname}" if dname else ""
    yaw_d = ISO_DIRS.index(dk) * 45.0
    yaws = (45.0, 225.0) if dname is None else (yaw_d,)
    fixlog = []

    def present():
        if dname is not None:
            dir_turn(rig, dk)

    def stance():
        pose_feet(rig, "L", (0.34, -0.30, 0.0), yaw=-22)
        pose_feet(rig, "R", (-0.32, 0.26, 0.0), yaw=28, heel_lift=10)
        aim_pole_knee(rig, "L", (0.5, -1, 0))
        aim_pole_knee(rig, "R", (-0.5, -1, 0))

    def body_up(lean, twist, low):
        def f():
            stance()
            move(rig, "cog", (0, 0, -low))
            rotate_world(rig, "spine", (1, 0, 0), math.radians(lean))
            rotate_world(rig, "chest", (0, 0, 1), math.radians(twist))
            for side in ("L", "R"):
                curve_chain(rig, scarf_names(side), (1, 0, 0), [-22, -12, -6, -4, -2])
            present()
        return f

    def two_hand_dir(body, g, d, e, extra=None, label=""):
        """two_hand_frame + (direction variants) the per-frame camera check; nudges rotate the
        blade direction about the vertical / tip it down, keeping the grip."""
        def pose_k(k):
            nud = [(0, 0), (15, 0), (-15, 0), (30, 0), (-30, 0), (0, 12), (45, 0), (-45, 0), (20, 15),
                   (60, 0), (-60, 0), (75, 10), (-75, 10), (90, 0), (-90, 0),
                   (0, 35), (40, 35), (-40, 35), (0, 55), (60, 50), (-60, 50)][k]
            dd = Matrix.Rotation(math.radians(nud[0]), 3, "Z") @ V(d)
            dd = dd.normalized()
            if nud[1]:
                # tip the blade toward the horizontal (up-pointing blades lean out, down-pointing
                # ones level off), about the horizontal axis perpendicular to the blade
                ax = V((0, 0, 1)).cross(dd)
                if ax.length > 1e-4:
                    sg = 1 if dd.z > 0 else -1
                    dd = Matrix.Rotation(math.radians(nud[1]) * sg, 3, ax.normalized()) @ dd
            two_hand_frame(rig, body, g, dd, e, yaws=yaws)
            if extra:
                extra()
        pose_k(0)
        if dname is not None:
            r_ = _dir_fix_sword(rig, yaw_d, True, label, need=38, redo=pose_k, nk=21)
            fixlog.append((label, r_))

    # ---- overhead slash: grip rises past the left side of the head to ABOVE the crown line,
    # blade back over the head, then the strike down the centre line
    OH = [  # (grip, blade dir, edge hint, lean, twist, low)
        ((0.14, -0.62, 0.95), (0.30, -0.82, -0.48), (0, 0, -1), -10, -10, 0.12),   # ready
        ((0.42, -0.56, 1.45), (0.45, 0.15, 0.88), (0, -1, 0), 4, -14, 0.08),       # rising
        ((0.45, -0.60, 1.80), (0.40, 0.40, 0.82), (0, -1, 0), 10, -18, 0.04),      # windup apex: grip at jaw height in front-left, blade up and back OVER the head
        ((0.44, -0.60, 1.84), (0.32, 0.50, 0.80), (0, -1, 0), 12, -18, 0.03),      # hold (anticipation, blade further back)
        ((0.36, -0.64, 1.58), (0.10, -0.85, 0.52), (0, 0, -1), -4, -4, 0.10),      # strike
        ((0.14, -0.70, 1.12), (0.05, -0.80, -0.60), (0, 0, -1), -16, 6, 0.18),     # impact
        ((0.06, -0.60, 0.88), (-0.20, -0.55, -0.81), (0, 0, -1), -20, 10, 0.22),   # follow-through
        ((0.10, -0.60, 0.90), (-0.10, -0.60, -0.79), (0, 0, -1), -18, 8, 0.20),    # settle
    ]
    act = new_timed(rig, f"anim_overhead_slash{sfx}", len(OH))
    for i, (g, d, e, lean, tw, low) in enumerate(OH):
        def sleeves(i=i):
            for side in ("L", "R"):
                rotate_world(rig, f"sleeve.{side}", (1, 0, 0), math.radians(-20 if i < 4 else 15))
        two_hand_dir(body_up(lean, tw, low), g, d, e, extra=sleeves, label=f"overhead{sfx} f{i}")
        if dname is not None:
            scarf_clear(rig, [yaw_d])
        key_all(rig, i + 1)
    finish_cycle(rig, act, "LINEAR")
    cyc[f"anim_overhead_slash{sfx}"] = dict(frames=len(OH), loop=False, cyclic=False, play=f"1-{len(OH)}",
                                            windup=[2, 4], active=[5, 6], recovery=[7, 8], direction=dk)
    # ---- horizontal slash
    SL = [
        ((0.14, -0.62, 0.95), (0.30, -0.82, -0.48), (0, 0, -1), -10, -10, 0.12),
        ((-0.30, -0.40, 1.22), (-0.80, 0.30, 0.15), (0, 0, -1), -6, -30, 0.12),    # windup to her right
        ((-0.10, -0.62, 1.18), (-0.30, -0.95, 0.05), (0.3, 0, -1), -8, -8, 0.14),  # cut start
        ((0.18, -0.62, 1.18), (0.86, -0.50, 0.06), (0.5, -1, 0), -10, 22, 0.14),   # mid (= pose_attack_slash_mid)
        ((0.34, -0.40, 1.12), (0.90, 0.40, -0.10), (0.5, 0, -1), -10, 34, 0.14),   # follow-through
        ((0.22, -0.52, 1.00), (0.60, -0.30, -0.74), (0, 0, -1), -10, 18, 0.13),    # settle
    ]
    act = new_timed(rig, f"anim_slash{sfx}", len(SL))
    for i, (g, d, e, lean, tw, low) in enumerate(SL):
        two_hand_dir(body_up(lean, tw, low), g, d, e, label=f"slash{sfx} f{i}")
        if dname is not None:
            scarf_clear(rig, [yaw_d])
        key_all(rig, i + 1)
    finish_cycle(rig, act, "LINEAR")
    cyc[f"anim_slash{sfx}"] = dict(frames=len(SL), loop=False, cyclic=False, play=f"1-{len(SL)}",
                                   windup=[2], active=[3, 4], recovery=[5, 6], direction=dk)
    # ---- run (cyclic, in place).  Round 6 (GD/TA 'run reads like a walk'): longer stride, high
    # back-heel kick on the passing frames (the foot shows past the skirt tails), 2 px bob (low on
    # the contacts f1/f5, high in flight), more arm pump, and the sword trails 16 deg further
    # down and swings +-12 deg across the cycle
    act = new_timed(rig, f"anim_run{sfx}", 8, cyclic=True)
    run_aim = None
    for f in range(9):
        ph = (f % 8) / 8

        def run_body(ph=ph):
            clear_pose(rig)
            move(rig, "cog", (0, -0.05, -0.05 - 0.065 * math.cos(4 * PI * ph)))
            rotate_world(rig, "spine", (1, 0, 0), math.radians(-18))
            rotate_world(rig, "head", (1, 0, 0), math.radians(10))
            rotate_world(rig, "hips", (0, 0, 1), math.radians(-12 * math.cos(2 * PI * ph)))
            rotate_world(rig, "chest", (0, 0, 1), math.radians(14 * math.cos(2 * PI * ph)))
            for side, off in (("L", 0.0), ("R", 0.5)):
                s_ = 1 if side == "L" else -1
                dy, z, tl, hl = run_foot((ph + off) % 1.0)
                rest = rig.data.bones[f"foot_ctrl.{side}"].head_local
                # feet 0.18 H behind the cog: forward lean, and the reaching front foot stays
                # within the +-3 px pivot band in S / SE / SW
                pose_feet(rig, side, (rest.x, rest.y + dy + 0.18, z), heel_lift=hl, toe_lift=tl)
                aim_pole_knee(rig, side, (0.05 * s_, -1, 0))
            sw = math.cos(2 * PI * ph)
            rotate_world(rig, "upper_arm.R", (1, 0, 0), math.radians(48 * sw))
            rotate_world(rig, "forearm.R", (1, 0, 0), math.radians(-50))
            rotate_world(rig, "upper_arm.L", (1, 0, 0), math.radians(40 - 15 * sw))      # sword arm back
            for side in ("L", "R"):
                rotate_world(rig, f"sleeve.{side}", (1, 0, 0), math.radians(-35 + 6 * math.sin(4 * PI * ph)))
            rotate_world(rig, "skirt.B", (1, 0, 0), math.radians(-20))
            curve_chain(rig, ["skirt.tail.001", "skirt.tail.002", "skirt.tail.003"], (1, 0, 0),
                        [-14 - 5 * math.sin(4 * PI * ph - 1.0 - 0.6 * k) for k in range(3)])
            if dname is not None:
                dir_turn(rig, dk, scarf=False)
            run_scarf(rig, ph)
        run_body()
        # sword trailing back + down (refs/3 diagonal), aimed once (frame 1 body) so it sticks out
        # of the silhouette, then swung across the cycle
        if run_aim is None:
            b_ = solve_pose_sword(rig, yaws, lambda d: -1.2 * d.y - 0.8 * d.x + 2.0 * abs(d.z + 0.45),
                                  min_px=36, label=f"anim_run{sfx}")
            run_aim = (b_[1], b_[2], b_[4]) if b_ else (100.0, 35.0, 0.0)
            run_body()
        swing = math.sin(2 * PI * ph)

        def aim_k(k, swing=swing, ph=ph):
            if k:
                run_body(ph)
                if k >= 5:      # sword arm abducted out from the body (guard clear of the hip)
                    rotate_world(rig, "upper_arm.L", (0, 1, 0), math.radians(-14 * (k - 4)))
            sc_ = [1.0, 0.6, 0.3, 0.0, 1.0, 0.6][k % 6] if k < 6 else 0.0
            dn = RUN_SWORD_SWING[1] * (1.0 if k < 4 else 0.5) * (1 if k < 8 else 0)
            de_ = min(70.0, run_aim[1] + dn + 4 * math.cos(2 * PI * ph) * sc_)
            # keep the tip above the floor
            head = rig.pose.bones["sword"].matrix.translation
            while head.z - math.sin(math.radians(de_)) * SWORD_TIP < 0.04 and de_ > run_aim[1]:
                de_ -= 2.0
            set_sword_dir(rig, run_aim[0] + RUN_SWORD_SWING[0] * swing * sc_, de_,
                          yaw=yaws[0], outward=False, extra_roll=run_aim[2])
        aim_k(0)
        if dname is not None:
            fixlog.append((f"run{sfx} f{f}", _dir_fix_sword(rig, yaw_d, False, "run", need=42, redo=aim_k)))
        if dname is not None:
            scarf_clear(rig, [yaw_d])
        key_all(rig, f + 1)
    finish_cycle(rig, act, "LINEAR")
    cyc[f"anim_run{sfx}"] = dict(frames=8, loop=True, cyclic=True, play="1-8", contacts=[1, 5],
                                 stride=RUN_STRIDE * 2, speed_per_frame=RUN_STRIDE / 3.2, direction=dk,
                                 bob_h=0.13, sword_swing_deg=RUN_SWORD_SWING[0])
    # ---- jump: anticipation / air / landing; cog lift = the jump arc (in place)
    JP = [  # (cog dz, phase)  phase: 0 crouch, 1 air, 2 land
        (-0.16, 0), (-0.20, 0), (0.30, 1), (0.62, 1), (0.66, 1), (0.40, 1), (-0.18, 2), (-0.06, 2)]
    act = new_timed(rig, f"anim_jump{sfx}", len(JP))
    jaim = {}
    for i, (dz, phs) in enumerate(JP):
        def jbody(dz=dz, phs=phs):
            clear_pose(rig)
            if phs == 1:
                k = smoothstep(0.0, 0.62, dz)
                ka = smoothstep(0.45, 0.64, dz)     # round 8 (AD): apex frames (f3-f4) only
                move(rig, "cog", (0, 0.0, dz))
                # round 8 (AD nice-to-have, refs/3): the apex ARCHES (chest out, chin up)
                # instead of the round-7 forward tuck; legs together, bent back behind her
                rotate_world(rig, "spine", (1, 0, 0), math.radians(8 * k - 18 * ka))
                rotate_world(rig, "chest", (1, 0, 0), math.radians(-8 * ka))
                rotate_world(rig, "head", (1, 0, 0), math.radians(10 * k - 22 * ka))
                for side, s_ in (("L", 1), ("R", -1)):
                    pose_feet(rig, side, ((0.10 - 0.04 * ka) * s_, 0.12 + 0.18 * k + 0.14 * ka,
                                          dz + 0.10 + 0.22 * k + 0.10 * ka), yaw=0)
                    rotate_world(rig, f"foot_ik.{side}", (1, 0, 0), math.radians(-35 * k - 20 * ka))
                    aim_pole_knee(rig, side, (0, -1, -0.2))
                    # cuffs and skirt flare UP and out like petals at the apex
                    rotate_world(rig, f"sleeve.{side}", (0, 1, 0), math.radians(-(32 * k + 22 * ka) * s_))
                    rotate_world(rig, f"sleeve.{side}", (1, 0, 0), math.radians(14 * ka))
                    rotate_world(rig, f"skirt.{side}", (0, 1, 0), math.radians(-(20 * k + 12 * ka) * s_))
                    rotate_world(rig, f"skirt.{side}.001", (0, 1, 0), math.radians(-14 * ka * s_))
                    curve_chain(rig, scarf_names(side), (1, 0, 0), [14 * k, 10 * k, 8 * k, 6 * k, 5 * k])
                rotate_world(rig, "skirt.F", (1, 0, 0), math.radians(-12 * ka))
                rotate_world(rig, "skirt.B", (1, 0, 0), math.radians(14 * ka))
                curve_chain(rig, ["skirt.tail.001", "skirt.tail.002", "skirt.tail.003"], (1, 0, 0),
                            [12 * ka, 10 * ka, 8 * ka])
                rotate_world(rig, "upper_arm.L", (0, 1, 0), math.radians(-35 * k))
                rotate_world(rig, "upper_arm.R", (0, 1, 0), math.radians(45 * k))
                set_props(rig, expr_smile=1)
            else:
                idle_feet(rig)
                move(rig, "cog", (0, -0.03, dz))
                rotate_world(rig, "spine", (1, 0, 0), math.radians(-14 if dz < -0.1 else -6))
                rotate_world(rig, "head", (1, 0, 0), math.radians(6))
                for side in ("L", "R"):
                    curve_chain(rig, scarf_names(side), (1, 0, 0),
                                [(-10 if phs == 0 else 18)] * 3 + [-4, -2])
                    rotate_world(rig, f"sleeve.{side}", (1, 0, 0), math.radians(-12 if phs == 0 else 18))
                rotate_world(rig, "upper_arm.L", (1, 0, 0), math.radians(20))
            present()
        jbody()
        key_ = "air" if phs == 1 else "ground"
        if key_ not in jaim:
            if phs == 1:
                b_ = solve_pose_sword(rig, yaws, lambda d: -1.5 * d.x + 1.5 * abs(d.z + 0.15) + 0.5 * abs(d.y),
                                      min_px=36, label=f"anim_jump{sfx} air")
                jaim[key_] = (b_[1], b_[2], b_[4]) if b_ else (-10.0, 8.0, 0.0)
            else:
                b_ = solve_pose_sword(rig, yaws, lambda d: -1.0 * d.x - 0.6 * d.y + 2.0 * abs(d.z + 0.5),
                                      min_px=36, label=f"anim_jump{sfx} ground")
                jaim[key_] = (b_[1], b_[2], b_[4]) if b_ else (100.0, 30.0, 0.0)
            jbody()

        def jaim_k(k, key_=key_, jb=jbody):
            if k:
                jb()
                if k >= 5:      # sword arm abducted out from the body
                    rotate_world(rig, "upper_arm.L", (0, 1, 0), math.radians(-14 * (k - 4)))
            nud = [(0, 0), (15, 0), (-15, 0), (0, 10), (30, 0), (-30, 0), (0, -10), (45, 0), (-45, 0)][k]
            set_sword_dir(rig, jaim[key_][0] + nud[0], jaim[key_][1] + nud[1], yaw=yaws[0], outward=False,
                          extra_roll=jaim[key_][2])
        jaim_k(0)
        if dname is not None:
            fixlog.append((f"jump{sfx} f{i}", _dir_fix_sword(rig, yaw_d, False, "jump", need=42, redo=jaim_k)))
        if dname is not None:
            scarf_clear(rig, [yaw_d])
        key_all(rig, i + 1)
    finish_cycle(rig, act, "LINEAR")
    cyc[f"anim_jump{sfx}"] = dict(frames=len(JP), loop=False, cyclic=False, play=f"1-{len(JP)}",
                                  anticipation=[1, 2], air=[3, 6], apex=[4, 5], landing=[7, 8],
                                  cog_dz=[j[0] for j in JP], direction=dk)
    for lab, r_ in fixlog:
        if r_["nudge"] or r_["roll"] is not None or r_["px"] < 30:
            print(f"[dir fix] {lab}: {r_}")


# ----------------------------------------------------------------------------
# Round 7: render-in-the-loop gate fixes (model/solve_gates.py) replayed by the build
# ----------------------------------------------------------------------------
GATE_FIXES = os.path.join(HERE, "gate_fixes.json")
SCARF_W = (0.35, 0.7, 1.0, 1.0, 0.8)


def sword_delta(rig, yaw=0.0, pitch=0.0, roll=0.0):
    """Rotate the sword bone about its own head: roll about the blade axis, then pitch (tip
    up/down about the horizontal axis across the blade), then yaw about the vertical."""
    pb = rig.pose.bones["sword"]
    bpy.context.view_layer.update()
    M = pb.matrix.copy()
    h = M.translation.copy()
    dv = V((M[0][1], M[1][1], M[2][1])).normalized()
    R = Matrix.Rotation(math.radians(roll), 4, dv)
    ax = V((0, 0, 1)).cross(dv)
    if ax.length > 1e-4 and pitch:
        R = Matrix.Rotation(math.radians(pitch), 4, ax.normalized()) @ R
    R = Matrix.Rotation(math.radians(yaw), 4, "Z") @ R
    pb.matrix = Matrix.Translation(h) @ R @ Matrix.Translation(-h) @ M
    bpy.context.view_layer.update()


def scarf_delta(rig, zl=0.0, zr=0.0, xl=0.0):
    """Same swing family as scarf_clear: lift about X, then swing about Z, per ribbon."""
    for side, z_ in (("L", zl), ("R", zr)):
        if xl:
            curve_chain(rig, scarf_names(side), (1, 0, 0), [xl * w for w in SCARF_W])
        if z_:
            curve_chain(rig, scarf_names(side), (0, 0, 1), [z_ * w for w in SCARF_W])


def arm_delta(rig, arm):
    """Sword-arm correction: [abduction about Y (negative = out from the body, as the build's run
    nudges), flexion about X] in degrees; a bare number = abduction only."""
    ab, fl = (arm, 0.0) if isinstance(arm, (int, float)) else (arm[0], arm[1])
    if ab:
        rotate_world(rig, "upper_arm.L", (0, 1, 0), math.radians(ab))
    if fl:
        rotate_world(rig, "upper_arm.L", (1, 0, 0), math.radians(fl))


def apply_gate_fix(rig, fx):
    """fx = {action, frames: [..], arm: deg | None, sword: [yaw, pitch, roll] | None,
    scarf: [zl, zr, xl] | None}.
    Re-keys only the sword / scarf bones on those frames, keeping each F-curve's interpolation."""
    act = bpy.data.actions.get(fx["action"])
    if act is None:
        return False
    rig.animation_data.action = act
    bones = (["upper_arm.L"] if fx.get("arm") else []) + (["sword"] if fx.get("sword") else []) + \
        (scarf_names("L") + scarf_names("R") if fx.get("scarf") else [])
    interp = {}
    for fc in act_fcurves(act):
        if fc.keyframe_points:
            interp[fc.data_path] = fc.keyframe_points[0].interpolation
    for f in fx["frames"]:
        bpy.context.scene.frame_set(f)
        bpy.context.view_layer.update()
        if fx.get("arm"):
            arm_delta(rig, fx["arm"])
        if fx.get("sword"):
            sword_delta(rig, *fx["sword"])
        if fx.get("scarf"):
            scarf_delta(rig, *fx["scarf"])
        for bn in bones:
            pb = rig.pose.bones[bn]
            pb.keyframe_insert("location", frame=f, group=bn)
            pb.keyframe_insert("rotation_quaternion", frame=f, group=bn)
    for fc in act_fcurves(act):
        ip = interp.get(fc.data_path)
        if ip:
            for kp in fc.keyframe_points:
                kp.interpolation = ip
    rig.animation_data.action = None
    return True


def apply_gate_fixes(rig):
    if not os.path.exists(GATE_FIXES):
        return 0
    fixes = json.load(open(GATE_FIXES)).get("fixes", [])
    n = sum(1 for fx in fixes if apply_gate_fix(rig, fx))
    print(f"[build] gate fixes replayed: {n} / {len(fixes)} ({GATE_FIXES})")
    return n


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
    scale_head_group()
    build_colliders(rig, coll)
    build_corset(rig, coll)
    skirt_ob = build_skirt(rig, coll)
    build_belt_pouch(rig, coll, skirt_ob)
    build_shoes(rig, coll)
    build_scarf(rig, coll)
    build_sword(rig, coll)
    fix_closed_normals()
    cam = setup_scene()
    add_bow_billboard(rig, cam)
    # round 6 (build time): the pose / cycle solvers evaluate the depsgraph thousands of times
    # (sword masks, kagi rolls, scarf swings).  Subdivision is switched off in the viewport
    # (= evaluated) level meanwhile -- the render level is untouched -- and restored afterwards.
    _ss = [(m, m.show_viewport) for o in bpy.data.objects if o.type == "MESH"
           for m in o.modifiers if m.type == "SUBSURF"]
    for m, _ in _ss:
        m.show_viewport = False
    t0 = time.time()
    make_poses(rig)
    make_cycles(rig)
    for m, v in _ss:
        m.show_viewport = v
    print(f"[build] poses + cycles {time.time() - t0:.0f} s, scarf swings searched {len(SCARF_LOG)}")
    if "--no-gate-fixes" not in sys.argv:
        apply_gate_fixes(rig)
    # cel look: only hair/body forms cast shadows; big cloth shapes would blanket the legs/face
    for ob in bpy.data.objects:
        if ob.type == "MESH" and ob.name.split(".")[0] in (
                "skirt_outer", "skirt_under", "sleeve", "scarf", "collar", "katana", "katana_sprite",
                "bow", "belt_pouch", "corset_tabs", "arm_ornament", "chest_flower", "chest_cord", "saya", "sleeve_band",
                "katana_sprite_kagi",
                # round 2 (Gemini): no cast shadows on/onto the face -> no diagonal shadow over the nose
                "bangs", "hair_strands", "hair_streaks", "hair_cap", "bun", "ears", "head", "hair_sheen", "bun_sheen", "bun_crease"):
            ob.visible_shadow = False
    # meta
    rig["H"] = 1.0
    rig["iso_ortho"] = ISO_ORTHO
    rig["front"] = "-Y (S iso direction)"
    rig["handedness"] = "+X = her LEFT (katana hand), -X = her RIGHT (arm ornament)"
    bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND, compress=True)
    nb = len(rig.data.bones)
    print(f"[build] saved {OUT_BLEND}  objects={len(bpy.data.objects)} bones={nb} materials={len(bpy.data.materials)}")


if __name__ == "__main__":
    main()
