"""Shared helpers: mesh construction, lofts, ribbons, modifiers, toon materials."""
import bpy, bmesh, math
from mathutils import Vector, Matrix

# ---------------------------------------------------------------- colours
def srgb_to_lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def hexc(h, a=1.0):
    h = h.lstrip('#')
    return tuple(srgb_to_lin(int(h[i:i + 2], 16) / 255.0) for i in (0, 2, 4)) + (a,)

# ---------------------------------------------------------------- scene
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def link(ob, coll_name=None):
    sc = bpy.context.scene
    if coll_name:
        coll = bpy.data.collections.get(coll_name)
        if coll is None:
            coll = bpy.data.collections.new(coll_name)
            sc.collection.children.link(coll)
        coll.objects.link(ob)
    else:
        sc.collection.objects.link(ob)
    return ob

def new_obj(name, verts, faces, smooth=True, coll=None, recalc=True, outward_from=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    me.validate(clean_customdata=False)
    me.update()
    ob = bpy.data.objects.new(name, me)
    link(ob, coll)
    if recalc:
        bm = bmesh.new(); bm.from_mesh(me)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        if outward_from is not None:
            # make sure the majority of faces point away from a reference point
            o = Vector(outward_from); s = 0.0
            for f in bm.faces:
                s += f.normal.dot(f.calc_center_median() - o) * f.calc_area()
            if s < 0:
                for f in bm.faces:
                    f.normal_flip()
        bm.to_mesh(me); bm.free()
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    return ob

def flip_normals(ob):
    bm = bmesh.new(); bm.from_mesh(ob.data)
    for f in bm.faces:
        f.normal_flip()
    bm.to_mesh(ob.data); bm.free()

def grid_faces(nr, ns, closed=True, off=0):
    f = []
    for i in range(nr - 1):
        for j in range(ns if closed else ns - 1):
            j2 = (j + 1) % ns
            f.append((off + i * ns + j, off + i * ns + j2, off + (i + 1) * ns + j2, off + (i + 1) * ns + j))
    return f

def loft(rings, closed=True, cap_start=False, cap_end=False):
    """rings: list of lists of Vector (equal length). Returns verts, faces (quads + fan caps)."""
    ns = len(rings[0]); nr = len(rings)
    verts = [v for r in rings for v in r]
    faces = grid_faces(nr, ns, closed)
    if cap_start:
        c = sum(rings[0], Vector()) / ns
        ci = len(verts); verts.append(c)
        for j in range(ns if closed else ns - 1):
            faces.append((ci, (j + 1) % ns, j))
    if cap_end:
        c = sum(rings[-1], Vector()) / ns
        ci = len(verts); verts.append(c)
        b = (nr - 1) * ns
        for j in range(ns if closed else ns - 1):
            faces.append((ci, b + j, b + (j + 1) % ns))
    return verts, faces

# ---------------------------------------------------------------- curves
def catmull(pts, n_per=4, closed=False):
    """Catmull-Rom through points; returns dense list of Vectors."""
    P = [Vector(p) for p in pts]
    out = []
    m = len(P)
    rng = m if closed else m - 1
    for i in range(rng):
        p0 = P[(i - 1) % m] if (closed or i > 0) else P[i] * 2 - P[i + 1]
        p1 = P[i]; p2 = P[(i + 1) % m]
        p3 = P[(i + 2) % m] if (closed or i + 2 < m) else P[(i + 1) % m] * 2 - P[i]
        for k in range(n_per):
            t = k / n_per
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    if not closed:
        out.append(P[-1].copy())
    return out

def resample(pts, n):
    """Resample polyline to n points evenly by arc length."""
    P = [Vector(p) for p in pts]
    L = [0.0]
    for i in range(1, len(P)):
        L.append(L[-1] + (P[i] - P[i - 1]).length)
    tot = L[-1]
    out = []; j = 0
    for k in range(n):
        s = tot * k / (n - 1)
        while j < len(P) - 2 and L[j + 1] < s:
            j += 1
        seg = max(L[j + 1] - L[j], 1e-9)
        t = (s - L[j]) / seg
        out.append(P[j].lerp(P[j + 1], min(max(t, 0), 1)))
    return out

def interp_table(rows, t):
    """rows: list of tuples (t, a, b, c...) sorted by t; smooth (catmull) interpolation of columns."""
    ts = [r[0] for r in rows]
    if t <= ts[0]:
        return list(rows[0][1:])
    if t >= ts[-1]:
        return list(rows[-1][1:])
    i = 0
    while ts[i + 1] < t:
        i += 1
    u = (t - ts[i]) / (ts[i + 1] - ts[i])
    out = []
    for c in range(1, len(rows[0])):
        p1 = rows[i][c]; p2 = rows[i + 1][c]
        p0 = rows[i - 1][c] if i > 0 else 2 * p1 - p2
        p3 = rows[i + 2][c] if i + 2 < len(rows) else 2 * p2 - p1
        u2, u3 = u * u, u * u * u
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u2 + (-p0 + 3 * p1 - 3 * p2 + p3) * u3))
    return out

def frames_along(path, up_hint=Vector((0, 0, 1))):
    """Parallel-transport frames (T, N, B) along a polyline."""
    n = len(path)
    T = []
    for i in range(n):
        a = path[max(i - 1, 0)]; b = path[min(i + 1, n - 1)]
        T.append((b - a).normalized())
    N0 = up_hint - T[0] * up_hint.dot(T[0])
    if N0.length < 1e-6:
        N0 = Vector((1, 0, 0)) - T[0] * T[0].x
    N = [N0.normalized()]
    for i in range(1, n):
        v = N[-1] - T[i] * N[-1].dot(T[i])
        N.append(v.normalized())
    B = [T[i].cross(N[i]).normalized() for i in range(n)]
    return T, N, B

def sweep(path, section_fn, up_hint=Vector((0, 0, 1)), cap_start=False, cap_end=False, frames=None):
    """section_fn(i, s) -> list of (a, b) in the (N, B) plane; returns verts, faces"""
    T, N, B = frames or frames_along(path, up_hint)
    rings = []
    n = len(path)
    for i in range(n):
        s = i / (n - 1)
        sec = section_fn(i, s)
        rings.append([path[i] + N[i] * a + B[i] * b for (a, b) in sec])
    return loft(rings, True, cap_start, cap_end)

def ellipse_sec(rx, ry, ns=12, phase=0.0, lobes=0, lobe_amp=0.0):
    out = []
    for k in range(ns):
        a = 2 * math.pi * k / ns + phase
        r = 1.0 + lobe_amp * math.cos(lobes * a) if lobes else 1.0
        out.append((rx * r * math.cos(a), ry * r * math.sin(a)))
    return out

# ---------------------------------------------------------------- modifiers
def add_mirror(ob, axis=0, merge=0.0005):
    m = ob.modifiers.new('Mirror', 'MIRROR')
    m.use_axis[0] = axis == 0
    m.use_clip = True
    m.use_mirror_merge = True
    m.merge_threshold = merge
    return m

def add_subsurf(ob, levels=1, render=None):
    m = ob.modifiers.new('Subsurf', 'SUBSURF')
    m.levels = levels
    m.render_levels = levels if render is None else render
    m.quality = 3
    return m

def add_solidify(ob, thickness=0.004, offset=-1.0, even=True, rim=True):
    m = ob.modifiers.new('Solidify', 'SOLIDIFY')
    m.thickness = thickness
    m.offset = offset
    m.use_even_offset = even
    m.use_rim = rim
    m.use_quality_normals = True
    return m

def add_outline(ob, mat_outline, thickness=0.0016):
    """Inverted-hull outline (render only; removed before export)."""
    if mat_outline.name not in [m.name for m in ob.data.materials if m]:
        ob.data.materials.append(mat_outline)
    idx = [m.name for m in ob.data.materials].index(mat_outline.name)
    m = ob.modifiers.new('Outline', 'SOLIDIFY')
    m.thickness = thickness
    m.offset = 1.0
    m.use_flip_normals = True
    m.use_rim = False
    m.material_offset = idx
    m.use_even_offset = False
    m.show_in_editmode = False
    # outline slot is last; out-of-range indices clamp to the last slot
    m.material_offset = 64
    m.material_offset_rim = 64
    return m

def set_mat(ob, mat, faces=None):
    me = ob.data
    if mat.name not in [m.name for m in me.materials if m]:
        me.materials.append(mat)
    idx = [m.name for m in me.materials].index(mat.name)
    if faces is None:
        for p in me.polygons:
            p.material_index = idx
    else:
        for i in faces:
            me.polygons[i].material_index = idx
    return idx

def join(objs, name):
    """Join meshes (keeps materials)."""
    ctx = bpy.context
    for o in ctx.scene.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    ctx.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    ob = ctx.view_layer.objects.active
    ob.name = name; ob.data.name = name
    return ob

def apply_mods(ob, keep=('Outline',)):
    ctx = bpy.context
    ctx.view_layer.objects.active = ob
    for m in list(ob.modifiers):
        if m.name in keep:
            continue
        bpy.ops.object.modifier_apply(modifier=m.name)

def evaluated_copy(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(ev)
    return me

# ---------------------------------------------------------------- materials
MATS = {}

def toon_mat(name, base, shadow, highlight=None, thresh=0.42, hl_thresh=0.93):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    diff = nt.nodes.new('ShaderNodeBsdfDiffuse')
    diff.inputs['Color'].default_value = (1, 1, 1, 1)
    s2r = nt.nodes.new('ShaderNodeShaderToRGB')
    bw = nt.nodes.new('ShaderNodeRGBToBW')
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    cr = ramp.color_ramp
    cr.interpolation = 'CONSTANT'
    cr.elements[0].position = 0.0
    cr.elements[0].color = hexc(shadow)
    cr.elements[1].position = thresh
    cr.elements[1].color = hexc(base)
    if highlight:
        e = cr.elements.new(hl_thresh)
        e.color = hexc(highlight)
    em = nt.nodes.new('ShaderNodeEmission')
    nt.links.new(diff.outputs['BSDF'], s2r.inputs['Shader'])
    nt.links.new(s2r.outputs['Color'], bw.inputs['Color'])
    nt.links.new(bw.outputs['Val'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], em.inputs['Color'])
    nt.links.new(em.outputs['Emission'], out.inputs['Surface'])
    m.diffuse_color = hexc(base)
    MATS[name] = m
    return m

def flat_mat(name, col):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = hexc(col)
    nt.links.new(em.outputs['Emission'], out.inputs['Surface'])
    m.diffuse_color = hexc(col)
    MATS[name] = m
    return m

def outline_mat(col='#3A2630'):
    if 'Outline' in MATS:
        return MATS['Outline']
    m = flat_mat('Outline', col)
    m.use_backface_culling = True
    MATS['Outline'] = m
    return m

def smoothstep(a, b, x):
    t = min(max((x - a) / (b - a), 0.0), 1.0)
    return t * t * (3 - 2 * t)

def gauss(d, s):
    return math.exp(-(d / s) ** 2)
