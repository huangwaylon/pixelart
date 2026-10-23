"""Modeller B shared helpers: mesh construction, lofts, sweeps, SDF utilities, toon materials."""
import bpy, bmesh, math
import numpy as np

# ---------------------------------------------------------------- colours
def srgb2lin(x):
    return x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4

def hexc(h, a=1.0):
    h = h.lstrip('#')
    return tuple(srgb2lin(int(h[i:i + 2], 16) / 255.0) for i in (0, 2, 4)) + (a,)

# ---------------------------------------------------------------- mesh helpers
def mesh_obj(name, verts, faces, mats=(), mat_idx=None, smooth=True, coll=None, uvs=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(float(c) for c in v) for v in verts], [], [tuple(int(i) for i in f) for f in faces])
    me.validate(clean_customdata=False)
    for m in mats:
        me.materials.append(m)
    if mat_idx is not None and len(mat_idx) == len(me.polygons):
        me.polygons.foreach_set('material_index', [int(i) for i in mat_idx])
    if uvs is not None:
        uvl = me.uv_layers.new(name='UVMap')
        loop_uv = []
        for p in me.polygons:
            for li in p.loop_indices:
                vi = me.loops[li].vertex_index
                loop_uv.extend(uvs[vi])
        uvl.data.foreach_set('uv', loop_uv)
    if smooth:
        me.shade_smooth()
    ob = bpy.data.objects.new(name, me)
    (coll or bpy.context.scene.collection).objects.link(ob)
    return ob

def recalc_normals(ob, inside=False):
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if inside:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.to_mesh(ob.data); bm.free()

def add_mod(ob, kind, **kw):
    names = {'SUBSURF': 'Subdivision', 'SOLIDIFY': 'Solidify', 'MIRROR': 'Mirror',
             'SHRINKWRAP': 'Shrinkwrap', 'LATTICE': 'Lattice', 'SKIN': 'Skin', 'DISPLACE': 'Displace',
             'SMOOTH': 'Smooth', 'WELD': 'Weld'}
    m = ob.modifiers.new(names.get(kind, kind), kind)
    for k, v in kw.items():
        setattr(m, k, v)
    return m

def join_parts(name, parts, mats, coll=None, smooth=True):
    """parts: list of (verts, faces, mat_index). Returns one object."""
    V, F, M = [], [], []
    for verts, faces, mi in parts:
        o = len(V)
        V.extend(list(verts))
        for k, f in enumerate(faces):
            F.append(tuple(i + o for i in f)); M.append(mi[k] if isinstance(mi, (list, tuple, np.ndarray)) else mi)
    return mesh_obj(name, V, F, mats=mats, mat_idx=M, smooth=smooth, coll=coll)

# ---------------------------------------------------------------- lofts
def grid_faces(nr, nc, closed=True, offset=0):
    F = []
    cols = nc if closed else nc - 1
    for i in range(nr - 1):
        for j in range(cols):
            j2 = (j + 1) % nc
            F.append((offset + i * nc + j, offset + i * nc + j2, offset + (i + 1) * nc + j2, offset + (i + 1) * nc + j))
    return F

def loft(rings, closed=True, cap0=False, cap1=False):
    rings = [np.asarray(r, float) for r in rings]
    N, K = len(rings), len(rings[0])
    V = list(np.concatenate(rings))
    F = grid_faces(N, K, closed)
    if cap0:
        ci = len(V); V.append(rings[0].mean(0))
        F += [(ci, (j + 1) % K, j) for j in range(K)]
    if cap1:
        ci = len(V); V.append(rings[-1].mean(0)); o = (N - 1) * K
        F += [(ci, o + j, o + (j + 1) % K) for j in range(K)]
    return V, F

def norm(v):
    v = np.asarray(v, float)
    n = np.linalg.norm(v, axis=-1, keepdims=True)
    return v / np.maximum(n, 1e-12)

def resample(poly, n):
    poly = np.asarray(poly, float)
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(poly, axis=0), axis=1))]
    t = np.linspace(0, d[-1], n)
    return np.stack([np.interp(t, d, poly[:, k]) for k in range(poly.shape[1])], 1)

def catmull(pts, n=64):
    """Centripetal-ish uniform Catmull-Rom through pts, returns dense polyline resampled to n."""
    P = np.asarray(pts, float)
    P = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]])
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for t in np.linspace(0, 1, 16, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(P[-2])
    return resample(np.array(out), n)

def frames(path, up_hint):
    """Tangent + parallel transported normal (biased to up_hint at start)."""
    path = np.asarray(path, float)
    T = np.gradient(path, axis=0); T = norm(T)
    up = np.asarray(up_hint, float)
    N0 = norm(up - T[0] * np.dot(up, T[0]))
    Ns = [N0]
    for i in range(1, len(path)):
        n = Ns[-1] - T[i] * np.dot(Ns[-1], T[i])
        Ns.append(norm(n))
    Ns = np.array(Ns)
    B = norm(np.cross(T, Ns))
    return T, Ns, B

def sweep(path, N, widths, thick, K=12, cup=None, closed_tip=True, twist=None):
    """Sweep a lens/ribbon custom profile along path.
    N: per-point 'out' vector (sheet normal hint); width axis = T x N.
    widths/thick: per-point full width / thickness. cup: edge curl toward -N (m)."""
    path = np.asarray(path, float)
    n = len(path)
    T = norm(np.gradient(path, axis=0))
    N = np.asarray(N, float)
    if N.ndim == 1:
        N = np.tile(N, (n, 1))
    N = norm(N - T * np.sum(N * T, 1, keepdims=True))
    B = norm(np.cross(T, N))
    if twist is not None:
        c, s = np.cos(twist)[:, None], np.sin(twist)[:, None]
        B, N = c * B + s * N, -s * B + c * N
    a = np.linspace(0, 2 * np.pi, K, endpoint=False)
    ca, sa = np.cos(a), np.sin(a)
    cup = np.zeros(n) if cup is None else np.asarray(cup, float)
    rings = []
    for i in range(n):
        w, th = widths[i] / 2, thick[i] / 2
        lat = w * ca
        out = th * sa - cup[i] * (ca ** 2)
        rings.append(path[i] + np.outer(lat, B[i]) + np.outer(out, N[i]))
    V, F = loft(rings, closed=True, cap0=True, cap1=closed_tip)
    return V, F

def ring(c, u, v, ru, rv, K, mod=None, phase=0.0, p=2.0):
    a = np.linspace(0, 2 * np.pi, K, endpoint=False) + phase
    ca, sa = np.cos(a), np.sin(a)
    if p != 2.0:
        ca = np.sign(ca) * np.abs(ca) ** (2.0 / p); sa = np.sign(sa) * np.abs(sa) ** (2.0 / p)
    r = 1.0 + (mod(a) if mod is not None else 0.0)
    return np.asarray(c, float) + np.outer(ru * ca * r, u) + np.outer(rv * sa * r, v)

def tube_along(path, radii_u, radii_v, K, up_hint=(0, 0, 1), mod=None, cap0=True, cap1=True, p=2.0):
    path = np.asarray(path, float)
    T, Nn, B = frames(path, up_hint)
    rings = []
    for i in range(len(path)):
        m = (lambda a, i=i: mod(i, a)) if mod else None
        rings.append(ring(path[i], B[i], Nn[i], radii_u[i], radii_v[i], K, mod=m, p=p))
    return loft(rings, True, cap0, cap1)

# ---------------------------------------------------------------- SDF (sign is what matters)
def sd_ellipsoid(p, c, r):
    q = (p - np.asarray(c)) / np.asarray(r)
    k0 = np.linalg.norm(q, axis=-1)
    k1 = np.linalg.norm(q / np.asarray(r), axis=-1)
    return k0 * (k0 - 1.0) / np.maximum(k1, 1e-9)

def sd_capsule(p, a, b, r):
    a, b = np.asarray(a, float), np.asarray(b, float)
    pa, ba = p - a, b - a
    h = np.clip(np.sum(pa * ba, -1) / np.dot(ba, ba), 0, 1)
    return np.linalg.norm(pa - h[..., None] * ba, axis=-1) - r

def sd_roundcone(p, a, b, r1, r2):
    a, b = np.asarray(a, float), np.asarray(b, float)
    ba = b - a; l2 = np.dot(ba, ba); rr = r1 - r2; a2 = l2 - rr * rr; il2 = 1.0 / l2
    pa = p - a
    y = np.sum(pa * ba, -1); z = y - l2
    q = pa * l2 - y[..., None] * ba
    x2 = np.sum(q * q, -1); y2 = y * y * l2; z2 = z * z * l2
    k = np.sign(rr) * rr * rr * x2
    d3 = (np.sqrt(np.maximum(x2 * a2 * il2, 0)) + y * rr) * il2 - r1
    d1 = np.sqrt(x2 + z2) * il2 - r2
    d2 = np.sqrt(x2 + y2) * il2 - r1
    return np.where(np.sign(z) * a2 * z2 > k, d1, np.where(np.sign(y) * a2 * y2 < k, d2, d3))

def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)

def smax(a, b, k):
    return -smin(-a, -b, k)

def ray_exit(f, O, D, tmax=0.4, steps=200, iters=30):
    """First exit distance along rays O + t D from inside (f<0) to outside."""
    O = np.asarray(O, float); D = np.asarray(D, float)
    ts = np.linspace(0, tmax, steps)
    P = O[None, None, :] + D[:, None, :] * ts[None, :, None]
    vals = f(P.reshape(-1, 3)).reshape(len(D), steps)
    outside = vals > 0
    first = np.argmax(outside, axis=1)
    first = np.where(outside.any(1), first, steps - 1)
    lo = ts[np.maximum(first - 1, 0)]; hi = ts[first]
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        v = f(O[None, :] + D * mid[:, None])
        lo = np.where(v < 0, mid, lo); hi = np.where(v < 0, hi, mid)
    return 0.5 * (lo + hi)

def ray_enter(f, O, D, tmax=0.4, steps=300, iters=30):
    """First entry distance along rays from outside."""
    O = np.asarray(O, float); D = np.asarray(D, float)
    if O.ndim == 1:
        O = np.tile(O, (len(D), 1))
    ts = np.linspace(0, tmax, steps)
    P = O[:, None, :] + D[:, None, :] * ts[None, :, None]
    vals = f(P.reshape(-1, 3)).reshape(len(D), steps)
    inside = vals < 0
    first = np.argmax(inside, axis=1)
    lo = ts[np.maximum(first - 1, 0)]; hi = ts[first]
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        v = f(O + D * mid[:, None])
        hi = np.where(v < 0, mid, hi); lo = np.where(v < 0, lo, mid)
    return 0.5 * (lo + hi)

def grad(f, P, e=1e-4):
    P = np.asarray(P, float)
    g = np.zeros_like(P)
    for k in range(3):
        d = np.zeros(3); d[k] = e
        g[:, k] = f(P + d) - f(P - d)
    return norm(g)

# ---------------------------------------------------------------- materials
def toon_mat(name, base, shadow, hi=None, t_shadow=0.32, t_hi=0.93, outline=False, emit_only=False,
             image=None, alpha=None):
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); out.location = (600, 0)
    m.diffuse_color = hexc(base)
    m['base_hex'] = base
    if outline or emit_only or image is not None:
        em = nt.nodes.new('ShaderNodeEmission'); em.location = (300, 0)
        if image is not None:
            tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = image; tex.location = (0, 0)
            tex.interpolation = 'Linear'
            nt.links.new(tex.outputs['Color'], em.inputs['Color'])
            if alpha:
                pass
        else:
            em.inputs['Color'].default_value = hexc(base)
        sh = em
        if outline:
            m.use_backface_culling = True
            m.use_backface_culling_shadow = True
    else:
        dif = nt.nodes.new('ShaderNodeBsdfDiffuse'); dif.location = (-400, 0)
        dif.inputs['Color'].default_value = (1, 1, 1, 1)
        s2r = nt.nodes.new('ShaderNodeShaderToRGB'); s2r.location = (-200, 0)
        ramp = nt.nodes.new('ShaderNodeValToRGB'); ramp.location = (0, 0)
        cr = ramp.color_ramp; cr.interpolation = 'CONSTANT'
        cr.elements[0].position = 0.0; cr.elements[0].color = hexc(shadow)
        cr.elements[1].position = t_shadow; cr.elements[1].color = hexc(base)
        if hi:
            e = cr.elements.new(t_hi); e.color = hexc(hi)
        em = nt.nodes.new('ShaderNodeEmission'); em.location = (300, 0)
        nt.links.new(dif.outputs[0], s2r.inputs[0])
        nt.links.new(s2r.outputs['Color'], ramp.inputs['Fac'])
        nt.links.new(ramp.outputs['Color'], em.inputs['Color'])
        sh = em
    if alpha is not None:
        tr = nt.nodes.new('ShaderNodeBsdfTransparent'); tr.location = (300, -200)
        mix = nt.nodes.new('ShaderNodeMixShader'); mix.location = (450, 0)
        mix.inputs[0].default_value = alpha
        nt.links.new(tr.outputs[0], mix.inputs[1]); nt.links.new(sh.outputs[0], mix.inputs[2])
        nt.links.new(mix.outputs[0], out.inputs['Surface'])
        m.surface_render_method = 'BLENDED'
    else:
        nt.links.new(sh.outputs[0], out.inputs['Surface'])
    return m

def torus_faces(nu, nv):
    return [(i * nv + j, i * nv + (j + 1) % nv, ((i + 1) % nu) * nv + (j + 1) % nv, ((i + 1) % nu) * nv + j)
            for i in range(nu) for j in range(nv)]

def loft_cyclic(rings):
    """Closed band (rings loop back to the first) -> watertight torus-like strip with a profile."""
    rings = [np.asarray(r, float) for r in rings]
    N, K = len(rings), len(rings[0])
    V = list(np.concatenate(rings))
    F = []
    for i in range(N):
        i2 = (i + 1) % N
        for j in range(K):
            j2 = (j + 1) % K
            F.append((i * K + j, i * K + j2, i2 * K + j2, i2 * K + j))
    return V, F
