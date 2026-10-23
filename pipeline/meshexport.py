"""Mesh export of the posed HD SDF model: numpy marching tetrahedra -> binary STL + OBJ/MTL (palette colours).

One closed shell per material (each on its own grid, spacing chosen from that material's thinnest part), so thin
ribbon/bow parts survive while the body stays light. Shells may interpenetrate where materials meet (viewer use).
    export_poses(scene, palette, out_dir)  ->  model_rest.stl/.obj/.mtl, model_apex.stl/.obj/.mtl
"""
import os
import struct

import numpy as np

from .sdf import _Compiled, sdf_units, unit_sdf, scene_sdf

# cube corners and the 6-tetrahedra split along the 0-6 diagonal (consistent across cubes -> watertight)
CORNERS = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0], [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]])
TETS = np.array([[0, 5, 1, 6], [0, 1, 2, 6], [0, 2, 3, 6], [0, 3, 7, 6], [0, 7, 4, 6], [0, 4, 5, 6]])
MAX_TRIS = 95000


def _thickness(p):
    k, P = p["kind"], p["params"]
    if k == "ell":
        return 2 * np.linalg.svd(p["M"][:3, :3], compute_uv=False).min()
    if k == "seg":
        return 2 * max(float(P["ra"][0]), float(P["rb"][0])) * min(float(P["flat"][0]), float(P["flatb"][0]))
    if k == "torus":
        return 2 * float(P["r"][0])
    return 2 * float(P["b"][0].min())


def _march(field, origin, h):
    """field: (nx, ny, nz) SDF samples. Returns (tri vertex positions (T,3,3), edge keys (T,3) for welding)."""
    nx, ny, nz = field.shape
    ix, iy, iz = np.meshgrid(np.arange(nx - 1), np.arange(ny - 1), np.arange(nz - 1), indexing="ij")
    base = np.stack([ix.ravel(), iy.ravel(), iz.ravel()], 1)
    cv = np.stack([field[base[:, 0] + c[0], base[:, 1] + c[1], base[:, 2] + c[2]] for c in CORNERS], 1)
    active = (cv.min(1) < 0) & (cv.max(1) >= 0)
    base, cv = base[active], cv[active]
    tris, keys = [], []
    lin = lambda g: (g[..., 0] * ny + g[..., 1]) * nz + g[..., 2]
    for tet in TETS:
        g = base[:, None, :] + CORNERS[tet][None]          # (n,4,3) grid coords
        v = cv[:, tet]                                      # (n,4)
        inside = v < 0
        cnt = inside.sum(1)
        for want in (1, 2, 3):
            m = cnt == want
            if not m.any():
                continue
            gm, vm, im = g[m], v[m], inside[m]
            order = np.argsort(~im, axis=1, kind="stable")     # inside corners first
            gs = np.take_along_axis(gm, order[..., None], 1)
            vs = np.take_along_axis(vm, order, 1)
            ins = list(range(want))
            outs = list(range(want, 4))

            def edge(a, b):
                va, vb = vs[:, a], vs[:, b]
                t = (va / (va - vb))[:, None]
                p = origin + h * (gs[:, a] + t * (gs[:, b] - gs[:, a]))
                ka, kb = lin(gs[:, a]), lin(gs[:, b])
                return p, np.minimum(ka, kb) * (nx * ny * nz) + np.maximum(ka, kb)
            if want in (1, 3):
                s, o = (ins[0], outs) if want == 1 else (outs[0], ins)
                E = [edge(s, o[0]), edge(s, o[1]), edge(s, o[2])]
                tri = [np.stack([E[0][0], E[1][0], E[2][0]], 1)]
                key = [np.stack([E[0][1], E[1][1], E[2][1]], 1)]
            else:
                a, b = ins
                c, d = outs
                E = [edge(a, c), edge(a, d), edge(b, d), edge(b, c)]
                tri = [np.stack([E[0][0], E[1][0], E[2][0]], 1), np.stack([E[0][0], E[2][0], E[3][0]], 1)]
                key = [np.stack([E[0][1], E[1][1], E[2][1]], 1), np.stack([E[0][1], E[2][1], E[3][1]], 1)]
            # orient outward: normal along (outside centroid - inside centroid)
            cin = (origin + h * gs[:, :want].mean(1))
            cout = (origin + h * gs[:, want:].mean(1))
            out_dir = cout - cin
            for T, K in zip(tri, key):
                nrm = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
                flip = (nrm * out_dir).sum(1) < 0
                T[flip] = T[flip][:, [0, 2, 1]]
                K[flip] = K[flip][:, [0, 2, 1]]
                tris.append(T)
                keys.append(K)
    if not tris:
        return np.zeros((0, 3, 3)), np.zeros((0, 3), np.int64)
    T, K = np.concatenate(tris), np.concatenate(keys)
    area = np.linalg.norm(np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]), axis=1)
    keep = area > 1e-12
    return T[keep], K[keep]


def mesh_parts(parts, scale_h=1.0, open_clips=False):
    """Posed part list -> {material: (triangles, edge keys)}.
    open_clips: renderer clip semantics (sdf.raycast) - surface whose nearest part fails that part's clip planes is
    dropped (open shell, e.g. the hair cap's face opening) instead of meshing the unclipped set (default, legacy)."""
    mats = sorted({p["material"] for p in parts if p.get("op", "union") == "union"})
    out = {}
    for m in mats:
        ids = [i for i, p in enumerate(parts) if p["material"] == m]
        sub = [parts[i] for i in ids]
        # a set may mix materials: keep subtract/intersect partners of this material's sets
        sets = {p.get("set") for p in sub if p.get("set")}
        sub += [p for p in parts if p.get("set") in sets and p["material"] != m]
        uni = [k for k, p in enumerate(sub) if p.get("op", "union") == "union"]
        Cs = _Compiled(sub)
        lo = np.min([Cs.center[k] - Cs.radius[k] for k in uni], 0) - 0.5
        hi = np.max([Cs.center[k] + Cs.radius[k] for k in uni], 0) + 0.5
        h = float(np.clip(0.4 * np.percentile([_thickness(sub[k]) for k in uni], 20), 0.12, 0.4)) * scale_h
        n = np.ceil((hi - lo) / h).astype(int) + 1
        while np.prod(n) > 6e6:
            h *= 1.15
            n = np.ceil((hi - lo) / h).astype(int) + 1
        d = np.full(tuple(n), 1e3)
        for unit, c, r in sdf_units(Cs):
            i0 = np.maximum(np.floor((c - r - 2 * h - lo) / h).astype(int), 0)
            i1 = np.minimum(np.ceil((c + r + 2 * h - lo) / h).astype(int) + 1, n)
            if (i1 <= i0).any():
                continue
            g = [lo[a] + h * np.arange(i0[a], i1[a]) for a in range(3)]
            X, Y, Z = np.meshgrid(*g, indexing="ij")
            dd = unit_sdf(Cs, unit, np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1))[0].reshape(X.shape)
            sl = tuple(slice(i0[a], i1[a]) for a in range(3))
            d[sl] = np.minimum(d[sl], dd)
        T, K = _march(d, lo, h)
        if open_clips and len(T) and any(p.get("clip_all") or p.get("clip_any") for p in sub):
            cen = T.mean(1)
            _, arg = scene_sdf(sub, cen, Cs)
            ok = np.ones(len(T), bool)
            for k in np.unique(arg):
                if k >= 0 and (sub[k].get("clip_all") or sub[k].get("clip_any")):
                    mk = arg == k
                    ok[mk] = Cs.clip_ok_world(k, cen[mk])
            T, K = T[ok], K[ok]
        out[m] = (T, K)
    return out


def write_stl(path, meshes):
    T = np.concatenate([t for t, _ in meshes.values()]).astype(np.float32)
    nrm = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-12)
    rec = np.zeros(len(T), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    rec["n"], rec["v"] = nrm, T
    with open(path, "wb") as f:
        f.write(b"snowpeak HD SDF model".ljust(80, b" "))
        f.write(struct.pack("<I", len(T)))
        f.write(rec.tobytes())
    return len(T)


def write_obj(path, meshes, palette):
    base = os.path.splitext(os.path.basename(path))[0]
    lines = [f"mtllib {base}.mtl"]
    mtl = []
    off = 1
    for m, (T, K) in meshes.items():
        keys, inv = np.unique(K.ravel(), return_inverse=True)
        verts = np.zeros((len(keys), 3))
        verts[inv] = T.reshape(-1, 3)
        lines += [f"v {x:.3f} {y:.3f} {z:.3f}" for x, y, z in verts]
        lines += [f"g {m}", f"usemtl {m}"]
        f = inv.reshape(-1, 3) + off
        lines += [f"f {a} {b} {c}" for a, b, c in f]
        off += len(keys)
        ramp = palette.ramps.get(m)
        rgb = palette.rgb[palette.index[ramp[len(ramp) // 2]]] if ramp else (200, 200, 200)
        mtl += [f"newmtl {m}", "Kd {:.4f} {:.4f} {:.4f}".format(*[c / 255 for c in rgb]), "Ka 0 0 0", "Ks 0 0 0", ""]
    with open(path, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    with open(os.path.join(os.path.dirname(path), f"{base}.mtl"), "w") as fh:
        fh.write("\n".join(mtl))


def export_poses(scene, palette, out_dir, poses=None):
    """STL + OBJ at the rest pose and the jump apex (highest z), facing S, in place, LOD ref."""
    os.makedirs(out_dir, exist_ok=True)
    n = len(scene.anim.keys)
    zs = [p["z_px"] for p in scene.anim.poses]
    poses = dict(poses or {"rest": n - 1, "apex": int(np.argmax(zs))})
    stats = {}
    for name, i in poses.items():
        parts, _ = scene.primitives(i, "S", lod="ref")
        s = 1.8                      # first guess for ~100k triangles at S4 scale
        for _ in range(4):           # triangle count ~ 1/h^2: rescale the grid to the budget in 1-2 passes
            meshes = mesh_parts(parts, s)
            tri = sum(len(t) for t, _ in meshes.values())
            if tri <= MAX_TRIS:
                break
            s *= max(1.05, (tri / (0.97 * MAX_TRIS)) ** 0.5)
        ntri = write_stl(os.path.join(out_dir, f"model_{name}.stl"), meshes)
        write_obj(os.path.join(out_dir, f"model_{name}.obj"), meshes, palette)
        stats[name] = {"frame": i + 1, "triangles": ntri,
                       "stl_bytes": os.path.getsize(os.path.join(out_dir, f"model_{name}.stl"))}
    return stats
