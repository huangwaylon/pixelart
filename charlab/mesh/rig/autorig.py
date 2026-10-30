#!/usr/bin/env python3
"""autorig.py: generated character mesh (GLB/OBJ/PLY/FBX/STL, messy, any standing pose) -> clean rigged,
posable Blender character in a natural A-pose, plus walk keys and a pose-test sheet.

  python3 charlab/mesh/rig/autorig.py in.glb [-o OUTDIR] [--height 2.0] [--facing +Y|-Y] [--tris 30000]
          [--weights auto|heat|voxel] [--sym auto|on|off] [--chains auto|none] [--arm-angle 40] [--rigify]

Outputs in OUTDIR (default charlab/mesh/rig/out/<stem>/):
  <stem>.blend   mesh + Rigify-metarig-named armature (deforming), actions "tests" and "walk_keys"
  <stem>.glb     the same, skinned, with the two actions
  sheet.png      pose-test board (rows: front / 3-4 / side clay, cols: poses), flagged faces coloured
  report.json    landmarks, timings, per-pose metrics and flags
  tiles/         individual renders

Runs itself under Blender (/Applications/Blender.app) in background mode; the board is composed with PIL
(pixtools venv). Internal work frame: Z up, faces -Y, character left = +X, feet on Z=0 (Blender/Rigify
convention); --facing +Y (default, project convention) rotates the saved rig 180 deg about Z at the end.
"""
import sys, os, json, math, time, subprocess, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../../.."))
BLENDER = "/Applications/Blender.app/Contents/MacOS/Blender"
VENV_PY = os.path.join(ROOT, ".models/pixtools/venv/bin/python")


def get_args(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("-o", "--out", default=None)
    ap.add_argument("--height", type=float, default=2.0)
    ap.add_argument("--facing", default="+Y", choices=["+Y", "-Y"])
    ap.add_argument("--tris", type=int, default=30000)
    ap.add_argument("--weights", default="auto", choices=["auto", "heat", "voxel"])
    ap.add_argument("--deform", default="auto", choices=["auto", "lbs", "dqs", "lbs+cs", "dqs+cs"])
    ap.add_argument("--sym", default="auto", choices=["auto", "on", "off"])
    ap.add_argument("--chains", default="auto", choices=["auto", "none"])
    ap.add_argument("--arm-angle", type=float, default=40.0, help="A-pose arm abduction from vertical (deg)")
    ap.add_argument("--apose-tol", type=float, default=15.0, help="leave limbs within this many deg of the A-pose target untouched")
    ap.add_argument("--force-apose", action="store_true", help="always pose every limb to the exact A-pose target")
    ap.add_argument("--res", type=int, default=160, help="voxel grid cells over the height")
    ap.add_argument("--in-front", default="auto", choices=["auto", "-Y", "+Y", "+X", "-X"],
                    help="which way the imported mesh faces (after importer axis conversion)")
    ap.add_argument("--rigify", action="store_true", help="also try generating a Rigify control rig")
    ap.add_argument("--no-tests", action="store_true")
    ap.add_argument("--tile", type=int, default=300)
    ap.add_argument("--board-only", action="store_true")
    a = ap.parse_args(argv)
    stem = os.path.splitext(os.path.basename(a.input))[0]
    if a.out is None:
        a.out = os.path.join(HERE, "out", stem)
    a.stem = stem
    return a


# ----------------------------------------------------------------------------------------------------------
# driver (outside Blender)
# ----------------------------------------------------------------------------------------------------------
def driver(argv):
    a = get_args(argv)
    if a.board_only:
        return compose_board(a.out)
    os.makedirs(a.out, exist_ok=True)
    t0 = time.time()
    cmd = [BLENDER, "-b", "--factory-startup", "--python-exit-code", "3", "-P", os.path.abspath(__file__), "--"] + argv
    log = open(os.path.join(a.out, "blender.log"), "w")
    r = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT)
    log.close()
    if r.returncode != 0:
        print(open(os.path.join(a.out, "blender.log")).read()[-4000:])
        sys.exit(f"blender failed ({r.returncode}); log: {a.out}/blender.log")
    try:
        import PIL  # noqa
        compose_board(a.out)
    except ImportError:
        subprocess.run([VENV_PY, os.path.abspath(__file__), a.input, "-o", a.out, "--board-only"], check=True)
    print(f"done in {time.time() - t0:.1f}s -> {a.out}")


def compose_board(out):
    from PIL import Image, ImageDraw, ImageFont
    rep = json.load(open(os.path.join(out, "report.json")))
    tests = rep.get("tests", [])
    if not tests:
        return
    views = rep["views"]
    t = rep["tile"]
    pad, head, foot = 6, 26, 66
    cols = len(tests) + 1
    W = cols * (t + pad) + pad
    Hh = head + len(views) * (t + pad) + foot + pad
    img = Image.new("RGB", (W, Hh), (236, 236, 236))
    dr = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", 12)
        fontb = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", 14)
    except Exception:
        font = fontb = ImageFont.load_default()
    # column 0: colour reference + legend
    x = pad
    dr.text((x, 6), "rest (colour)", fill=(0, 0, 0), font=fontb)
    for vi, v in enumerate(views):
        p = os.path.join(out, "tiles", f"color_{v}.png")
        if os.path.exists(p):
            img.paste(Image.open(p).convert("RGB").resize((t, t)), (x, head + vi * (t + pad)))
    leg = ["red: collapsed tri (area<0.3x)", "orange: stretched tri (>2.5x)", "magenta: self-intersection",
           f"{rep['name']}  tris {rep['mesh']['tris']}", f"weights: {rep['skin']['method']} / {rep['skin'].get('deform', 'lbs')}"]
    for i, s in enumerate(leg):
        dr.text((x, head + len(views) * (t + pad) + 2 + i * 13), s, fill=(60, 60, 60), font=font)
    for ci, te in enumerate(tests):
        x = pad + (ci + 1) * (t + pad)
        bad = te["flags"]
        dr.text((x, 6), te["name"], fill=(170, 0, 0) if bad else (0, 0, 0), font=fontb)
        for vi, v in enumerate(views):
            p = os.path.join(out, "tiles", f"{te['name']}_{v}.png")
            if os.path.exists(p):
                img.paste(Image.open(p).convert("RGB").resize((t, t)), (x, head + vi * (t + pad)))
        m = te["metrics"]
        lines = [f"collapse {m['collapsed']}  str {m['stretched']}", f"isect +{m['isect_new']}  vol {m['vol_ratio']:.3f}"]
        jv = " ".join(f"{k}:{v:.2f}" for k, v in m.get("joint_vol", {}).items())
        while jv:
            lines.append(jv[:44]); jv = jv[44:]
        if bad:
            lines.append("FLAG " + ",".join(bad))
        for i, s in enumerate(lines[:5]):
            dr.text((x, head + len(views) * (t + pad) + 2 + i * 13), s,
                    fill=(170, 0, 0) if s.startswith("FLAG") else (40, 40, 40), font=font)
    img.save(os.path.join(out, "sheet.png"))
    print("board", os.path.join(out, "sheet.png"), img.size)


# ----------------------------------------------------------------------------------------------------------
# everything below runs inside Blender
# ----------------------------------------------------------------------------------------------------------
def blender_main(argv):
    import numpy as np
    import bpy, bmesh
    from mathutils import Vector, Matrix, Quaternion
    from mathutils.bvhtree import BVHTree
    from mathutils.interpolate import poly_3d_calc

    A = get_args(argv)
    DEBUG = bool(os.environ.get("AUTORIG_DEBUG"))
    os.makedirs(os.path.join(A.out, "tiles"), exist_ok=True)
    REP = {"name": A.stem, "input": os.path.abspath(A.input), "args": {k: v for k, v in vars(A).items()},
           "timings": {}, "notes": []}
    T0 = [time.time()]

    def tick(name):
        t = time.time(); REP["timings"][name] = round(t - T0[0], 2); T0[0] = t
        print(f"[autorig] {name}: {REP['timings'][name]}s", flush=True)

    def note(s):
        print("[autorig] NOTE", s, flush=True); REP["notes"].append(s)

    # ---------------- mesh helpers ----------------
    def mesh_np(me):
        n = len(me.vertices)
        co = np.empty(n * 3, np.float32); me.vertices.foreach_get("co", co)
        me.calc_loop_triangles()
        nt = len(me.loop_triangles)
        tri = np.empty(nt * 3, np.int32); me.loop_triangles.foreach_get("vertices", tri)
        return co.reshape(-1, 3).astype(np.float64), tri.reshape(-1, 3)

    def set_co(me, co):
        me.vertices.foreach_set("co", co.astype(np.float32).ravel()); me.update()

    def new_obj(name, me):
        ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob); return ob

    def triangulate(me):
        bm = bmesh.new(); bm.from_mesh(me)
        bmesh.ops.triangulate(bm, faces=bm.faces[:])
        bm.to_mesh(me); bm.free(); me.update()

    def eval_mesh(ob):
        dg = bpy.context.evaluated_depsgraph_get()
        return bpy.data.meshes.new_from_object(ob.evaluated_get(dg))

    def apply_mod(ob, mod):
        me = eval_mesh(ob); ob.modifiers.remove(mod); old = ob.data; ob.data = me
        if old.users == 0: bpy.data.meshes.remove(old)

    def components(nv, tri):
        L = np.arange(nv)
        a, b, c = tri[:, 0], tri[:, 1], tri[:, 2]
        while True:
            m = np.minimum(np.minimum(L[a], L[b]), L[c])
            L2 = L.copy()
            np.minimum.at(L2, a, m); np.minimum.at(L2, b, m); np.minimum.at(L2, c, m)
            L2 = L2[L2]; L2 = L2[L2]
            if np.array_equal(L2, L): break
            L = L2
        u, inv = np.unique(L, return_inverse=True)
        return inv, len(u)

    def tri_area(co, tri):
        return 0.5 * np.linalg.norm(np.cross(co[tri[:, 1]] - co[tri[:, 0]], co[tri[:, 2]] - co[tri[:, 0]]), axis=1)

    def signed_volume(co, tri):
        return float(np.einsum("ij,ij->i", co[tri[:, 0]], np.cross(co[tri[:, 1]], co[tri[:, 2]])).sum() / 6.0)

    # ---------------- 1. import ----------------
    bpy.ops.wm.read_factory_settings(use_empty=True)
    ext = os.path.splitext(A.input)[1].lower()
    if ext in (".glb", ".gltf"): bpy.ops.import_scene.gltf(filepath=A.input)
    elif ext == ".obj": bpy.ops.wm.obj_import(filepath=A.input)
    elif ext == ".ply": bpy.ops.wm.ply_import(filepath=A.input)
    elif ext == ".fbx": bpy.ops.import_scene.fbx(filepath=A.input)
    elif ext == ".stl": bpy.ops.wm.stl_import(filepath=A.input)
    else: raise SystemExit("unsupported input " + ext)
    dg = bpy.context.evaluated_depsgraph_get()
    parts = []
    for ob in list(bpy.context.scene.objects):
        if ob.type == "MESH":
            me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))   # applies modifiers / skin pose
            me.transform(ob.matrix_world)
            parts.append(me)
    for ob in list(bpy.data.objects): bpy.data.objects.remove(ob)
    if not parts: raise SystemExit("no meshes in input")

    # colour source: per-triangle-corner colour or texture lookup
    src_co, src_tri, src_col, src_uv, src_img, src_fimg = [], [], [], [], [], []
    images = {}
    voff = 0
    for me in parts:
        co, tri = mesh_np(me)
        nt = len(tri)
        lt = me.loop_triangles
        loops = np.empty(nt * 3, np.int32); lt.foreach_get("loops", loops)
        polys = np.empty(nt, np.int32); lt.foreach_get("polygon_index", polys)
        matidx = np.zeros(len(me.polygons), np.int32)
        if len(me.polygons): me.polygons.foreach_get("material_index", matidx)
        col = np.ones((nt * 3, 4), np.float32) * 0.7
        uvs = np.zeros((nt * 3, 2), np.float32)
        fimg = np.full(nt, -1, np.int32)
        ca = me.color_attributes.active_color if me.color_attributes else None
        if ca is not None:
            n = len(ca.data); arr = np.empty(n * 4, np.float32)
            ca.data.foreach_get("color", arr); arr = arr.reshape(-1, 4)
            if ca.domain == "POINT":
                lv = np.empty(len(me.loops), np.int32); me.loops.foreach_get("vertex_index", lv)
                col = arr[lv[loops]]
            else:
                col = arr[loops]
        else:
            if me.uv_layers.active is not None:
                uv = np.empty(len(me.loops) * 2, np.float32); me.uv_layers.active.data.foreach_get("uv", uv)
                uvs = uv.reshape(-1, 2)[loops]
            for mi, mat in enumerate(me.materials):
                if mat is None: continue
                base = np.array(list(mat.diffuse_color), np.float32)
                img = None
                if mat.use_nodes:
                    for nd in mat.node_tree.nodes:
                        if nd.type == "BSDF_PRINCIPLED":
                            base = np.array(list(nd.inputs["Base Color"].default_value), np.float32)
                        if nd.type == "TEX_IMAGE" and nd.image is not None and img is None:
                            img = nd.image
                sel = np.repeat(matidx[polys] == mi, 3)
                col[sel] = base
                if img is not None and me.uv_layers.active is not None:
                    if img.name not in images:
                        w, h = img.size
                        px = np.empty(w * h * 4, np.float32); img.pixels.foreach_get(px)
                        images[img.name] = (len(images), px.reshape(h, w, 4))
                    fimg[matidx[polys] == mi] = images[img.name][0]
        src_co.append(co); src_tri.append(tri + voff); src_col.append(col); src_uv.append(uvs); src_fimg.append(fimg)
        voff += len(co)
    src_co = np.concatenate(src_co); src_tri = np.concatenate(src_tri)
    src_col = np.concatenate(src_col); src_uv = np.concatenate(src_uv); src_fimg = np.concatenate(src_fimg)
    img_list = [None] * len(images)
    for k, (i, px) in images.items(): img_list[i] = px
    REP["input_stats"] = {"verts": int(len(src_co)), "tris": int(len(src_tri)), "parts": len(parts),
                          "textures": len(img_list), "has_colour": bool(len(img_list) or (src_col.std() > 1e-3))}
    me = bpy.data.meshes.new("body")
    me.from_pydata(src_co.tolist(), [], src_tri.tolist())
    me.validate(); me.update()
    for m in parts: bpy.data.meshes.remove(m)
    body = new_obj("body", me)
    tick("import")

    class Src:   # colour lookup on the original surface (kept in sync with every rigid transform)
        co = src_co; tri = src_tri
    def src_bvh():
        return BVHTree.FromPolygons([tuple(v) for v in Src.co], [tuple(t) for t in Src.tri], all_triangles=True)

    def transform_all(M):
        """apply 4x4 (numpy) to body mesh and colour source"""
        co, _ = mesh_np(body.data)
        R, t = M[:3, :3], M[:3, 3]
        set_co(body.data, co @ R.T + t)
        Src.co = Src.co @ R.T + t

    # ---------------- 2. cleanup ----------------
    def cleanup(ob, H, target_tris, voxel_div=230):
        me = ob.data
        bm = bmesh.new(); bm.from_mesh(me)
        bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=H * 1e-5)
        bm.to_mesh(me); bm.free()
        co, tri = mesh_np(me)
        comp, nc = components(len(co), tri)
        ar = tri_area(co, tri)
        carea = np.bincount(comp[tri[:, 0]], weights=ar, minlength=nc)
        main = int(np.argmax(carea))
        lo_m = co[comp == main].min(0) - 0.03 * H; hi_m = co[comp == main].max(0) + 0.03 * H
        keep = np.zeros(nc, bool)
        for c in range(nc):
            if carea[c] >= 0.01 * carea[main]: keep[c] = True; continue
            pc = co[comp == c]
            inside = np.all((pc.min(0) < hi_m) & (pc.max(0) > lo_m))
            if carea[c] >= 0.0015 * carea[main] and inside: keep[c] = True
        dropped = int((~keep).sum())
        if dropped:
            bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
            kill = [bm.verts[i] for i in np.nonzero(~keep[comp])[0]]
            bmesh.ops.delete(bm, geom=kill, context="VERTS"); bm.to_mesh(me); bm.free(); me.update()
        stats = {"components_in": int(nc), "floaters_removed": dropped,
                 "removed_area_pct": round(100 * float(carea[~keep].sum() / carea.sum()), 3)}
        # voxel remesh (watertight, manifold, consistent normals) then decimate to target
        bm = bmesh.new(); bm.from_mesh(me)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        bm.to_mesh(me); bm.free(); me.update()
        co_b, tri_b = mesh_np(me); area_b = tri_area(co_b, tri_b).sum()
        vs = H / voxel_div
        backup = me.copy()
        mod = ob.modifiers.new("rm", "REMESH"); mod.mode = "VOXEL"; mod.voxel_size = vs; mod.adaptivity = 0.0
        mod.use_smooth_shade = True
        apply_mod(ob, mod)
        co_a, tri_a = mesh_np(ob.data)
        ok = len(tri_a) > 0 and components(len(co_a), tri_a)[1] <= max(3, 3 * int(keep.sum())) and tri_area(co_a, tri_a).sum() > 0.5 * area_b
        if not ok:
            # VDB sign failure (self-intersecting / open input): rebuild from a solidified voxel shell instead
            note("voxel remesh failed sign test -> retry via shell (solidify) + remesh")
            old = ob.data; ob.data = backup.copy(); bpy.data.meshes.remove(old)
            sol = ob.modifiers.new("sol", "SOLIDIFY"); sol.thickness = 2.5 * vs; sol.offset = 0.0
            apply_mod(ob, sol)
            mod = ob.modifiers.new("rm", "REMESH"); mod.mode = "VOXEL"; mod.voxel_size = vs; mod.adaptivity = 0.0
            apply_mod(ob, mod)
            co_a, tri_a = mesh_np(ob.data)
            # keep only the outer surface: largest component by area
            comp2, nc2 = components(len(co_a), tri_a)
            ar2 = np.bincount(comp2[tri_a[:, 0]], weights=tri_area(co_a, tri_a), minlength=nc2)
            if nc2 > 1:
                bm = bmesh.new(); bm.from_mesh(ob.data); bm.verts.ensure_lookup_table()
                bmesh.ops.delete(bm, geom=[bm.verts[i] for i in np.nonzero(comp2 != np.argmax(ar2))[0]], context="VERTS")
                bm.to_mesh(ob.data); bm.free(); ob.data.update()
            stats["remesh_fallback"] = "solidify-shell"
        bpy.data.meshes.remove(backup)
        nq = len(ob.data.polygons)
        if 2 * nq > target_tris:
            mod = ob.modifiers.new("dec", "DECIMATE"); mod.ratio = target_tris / (2.0 * nq)
            mod.use_collapse_triangulate = True
            apply_mod(ob, mod)
        triangulate(ob.data)
        bm = bmesh.new(); bm.from_mesh(ob.data)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        bm.to_mesh(ob.data); bm.free(); ob.data.update()
        co, tri = mesh_np(ob.data)
        comp, nc = components(len(co), tri)
        stats.update({"voxel": round(vs, 5), "tris": int(len(tri)), "verts": int(len(co)), "components_out": int(nc),
                      "watertight": bool(nc >= 1)})
        return stats

    def transfer_colour(ob):
        """per-vertex colour of ob from the (aligned) colour source; also store hit distance"""
        bvh = src_bvh()
        co, tri = mesh_np(ob.data)
        out = np.zeros((len(co), 4), np.float32)
        for i, p in enumerate(co):
            loc, nrm, fi, d = bvh.find_nearest(Vector(p))
            if fi is None: out[i] = (0.7, 0.7, 0.7, 1); continue
            ids = Src.tri[fi]
            w = poly_3d_calc([Vector(Src.co[j]) for j in ids], loc)
            if src_fimg[fi] >= 0:
                uv = sum(w[k] * src_uv[fi * 3 + k] for k in range(3))
                px = img_list[src_fimg[fi]]; h, wd = px.shape[:2]
                out[i] = px[int((uv[1] % 1.0) * (h - 1)), int((uv[0] % 1.0) * (wd - 1))]
            else:
                out[i] = sum(w[k] * src_col[fi * 3 + k] for k in range(3))
        out[:, 3] = 1
        ca = ob.data.color_attributes.get("Col") or ob.data.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
        ca.data.foreach_set("color", out.ravel())
        return out

    co0, _ = mesh_np(body.data)
    H0 = float(np.max(co0.max(0) - co0.min(0)))
    REP["cleanup"] = cleanup(body, H0, A.tris); print("[autorig] cleanup", REP["cleanup"], flush=True)
    tick("cleanup")

    # ---------------- voxel grid ----------------
    class Grid:
        pass

    def voxelize(ob, pitch):
        co, tri = mesh_np(ob.data)
        bvh = BVHTree.FromPolygons([tuple(v) for v in co], [tuple(t) for t in tri], all_triangles=True)
        lo = co.min(0) - 2 * pitch; hi = co.max(0) + 2 * pitch
        n = np.ceil((hi - lo) / pitch).astype(int) + 1
        votes = np.zeros(tuple(n), np.int8)
        for ax in range(3):
            o1, o2 = [a for a in range(3) if a != ax]
            d = Vector([1.0 if k == ax else 0.0 for k in range(3)])
            L = (n[ax] + 2) * pitch
            for i in range(n[o1]):
                for j in range(n[o2]):
                    p = [0.0, 0.0, 0.0]
                    p[ax] = lo[ax] - pitch; p[o1] = lo[o1] + i * pitch; p[o2] = lo[o2] + j * pitch
                    org = Vector(p); hits = []
                    travelled = 0.0
                    eps = 2e-3 * pitch
                    while len(hits) < 400:
                        loc, nrm, fi, dist = bvh.ray_cast(org, d, L - travelled)
                        if loc is None: break
                        hits.append(loc[ax]); travelled += dist + eps
                        org = loc + d * eps
                    if len(hits) < 2: continue
                    for k in range(0, len(hits) - 1, 2):
                        a0 = int(math.ceil((hits[k] - lo[ax]) / pitch)); a1 = int(math.floor((hits[k + 1] - lo[ax]) / pitch))
                        if a1 < a0: continue
                        sl = [i, j]; sl.insert(ax, slice(a0, a1 + 1))
                        idx = [None, None, None]; idx[ax] = slice(a0, a1 + 1); idx[o1] = i; idx[o2] = j
                        votes[tuple(idx)] += 1
        g = Grid(); g.S = votes >= 2; g.lo = lo; g.p = pitch; g.n = n
        g.bvh = bvh
        return g

    def w2v(g, P):
        return np.clip(np.round((np.asarray(P) - g.lo) / g.p).astype(int), 0, g.n - 1)

    def v2w(g, I):
        return g.lo + np.asarray(I) * g.p

    # ---------------- N-D labelling / BFS (numpy only) ----------------
    def shift(a, ax, s, fill):
        out = np.full_like(a, fill)
        src = [slice(None)] * a.ndim; dst = [slice(None)] * a.ndim
        if s > 0: dst[ax] = slice(1, None); src[ax] = slice(None, -1)
        else: dst[ax] = slice(None, -1); src[ax] = slice(1, None)
        out[tuple(dst)] = a[tuple(src)]
        return out

    def label(mask):
        n = mask.size
        idx = np.arange(n, dtype=np.int64).reshape(mask.shape)
        L = np.where(mask, idx, n)
        while True:
            M = L
            for ax in range(mask.ndim):
                M = np.minimum(M, shift(L, ax, 1, n)); M = np.minimum(M, shift(L, ax, -1, n))
            M = np.where(mask, M, n).ravel()
            ext = np.append(M, n)
            for _ in range(4):
                M = ext[M]; ext = np.append(M, n)
            M = M.reshape(mask.shape)
            if np.array_equal(M, L): break
            L = M
        out = np.zeros(mask.shape, np.int32)
        if mask.any():
            u, inv = np.unique(L[mask], return_inverse=True)
            out[mask] = inv + 1
            return out, len(u)
        return out, 0

    def dilate(f, full):
        if full:
            for ax in range(f.ndim):
                f = f | shift(f, ax, 1, False) | shift(f, ax, -1, False)
            return f
        o = f.copy()
        for ax in range(f.ndim):
            o |= shift(f, ax, 1, False); o |= shift(f, ax, -1, False)
        return o

    INF = 1e9

    def bfs(mask, seeds, maxit=100000):
        d = np.full(mask.shape, INF, np.float32)
        front = seeds & mask
        if not front.any(): return d
        d[front] = 0; vis = front.copy(); k = 0
        while front.any() and k < maxit:
            k += 1
            nb = dilate(front, full=(k % 2 == 0)) & mask & ~vis
            d[nb] = k; vis |= nb; front = nb
        return d

    def seed_at(g, mask, P):
        """boolean seed at nearest inside voxel to world point P"""
        I = w2v(g, P)
        s = np.zeros(mask.shape, bool)
        if mask[tuple(I)]: s[tuple(I)] = True; return s
        idx = np.argwhere(mask)
        if len(idx) == 0: return s
        k = np.argmin(((idx - I) ** 2).sum(1)); s[tuple(idx[k])] = True
        return s

    # ---------------- 3. orientation / scale ----------------
    def slice_comps(g, z_frac, mask=None):
        S = g.S if mask is None else mask
        zs = np.nonzero(S.any(axis=(0, 1)))[0]
        z = zs[0] + max(1, int(round(z_frac * (zs[-1] - zs[0]))))
        lab, nl = label(S[:, :, z])
        areas = np.bincount(lab.ravel(), minlength=nl + 1)[1:]
        return lab, areas, z

    def orient():
        co, _ = mesh_np(body.data)
        ext3 = co.max(0) - co.min(0)
        notes = []
        # up axis: trust importer unless another axis is clearly the longest
        up = int(np.argmax(ext3))
        if up != 2 and ext3[up] > 1.25 * ext3[2]:
            M = np.eye(4)
            if up == 1: M[:3, :3] = [[1, 0, 0], [0, 0, -1], [0, 1, 0]]
            else: M[:3, :3] = [[0, 0, 1], [0, 1, 0], [-1, 0, 0]]
            transform_all(M); notes.append(f"up axis was {'XYZ'[up]}")
            co, _ = mesh_np(body.data); ext3 = co.max(0) - co.min(0)
        H = ext3[2]
        g = voxelize(body, H / 64)
        _, ab, _ = slice_comps(g, 0.03); _, at, _ = slice_comps(g, 0.97)
        big_b = int((ab > 0.15 * ab.max()).sum()) if len(ab) else 0
        big_t = int((at > 0.15 * at.max()).sum()) if len(at) else 0
        if big_b == 1 and big_t == 2:
            M = np.eye(4); M[:3, :3] = [[1, 0, 0], [0, -1, 0], [0, 0, -1]]; transform_all(M)
            notes.append("flipped upside-down"); g = voxelize(body, H / 64)
        # yaw: principal horizontal axis of the torso band -> X
        idx = np.argwhere(g.S); P = v2w(g, idx)
        z0, z1 = P[:, 2].min(), P[:, 2].max()
        band = P[(P[:, 2] > z0 + 0.12 * (z1 - z0)) & (P[:, 2] < z0 + 0.6 * (z1 - z0))]
        xy = band[:, :2] - band[:, :2].mean(0)
        ev, evec = np.linalg.eigh(xy.T @ xy)
        if A.in_front == "auto" and ev[1] > 1.3 * ev[0]:
            major = evec[:, 1]; ang = math.atan2(major[1], major[0])
            if abs(math.sin(ang)) > math.sin(math.radians(12)):
                c, s = math.cos(-ang), math.sin(-ang)
                M = np.eye(4); M[:2, :2] = [[c, -s], [s, c]]; transform_all(M)
                notes.append(f"yaw corrected {math.degrees(ang):.1f} deg"); g = voxelize(body, H / 64)
        # front/back: toes stick out forward of the shins
        idx = np.argwhere(g.S); P = v2w(g, idx)
        z0 = P[:, 2].min()
        foot = P[P[:, 2] < z0 + 0.04 * H]; shin = P[(P[:, 2] > z0 + 0.08 * H) & (P[:, 2] < z0 + 0.13 * H)]
        dy = float(foot[:, 1].mean() - shin[:, 1].mean()) if len(foot) and len(shin) else 0.0
        front = A.in_front
        if front == "auto":
            front = "+Y" if dy > 0.008 * H else "-Y"
            if abs(dy) <= 0.008 * H: notes.append(f"toe test inconclusive (dy={dy / H:.4f}H), kept importer front -Y")
        rot = {"-Y": 0, "+Y": 180, "+X": -90, "-X": 90}[front]
        if rot:
            c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
            M = np.eye(4); M[:2, :2] = [[c, -s], [s, c]]; transform_all(M); notes.append(f"rotated {rot} deg to face -Y")
        # feet on z=0, centre, scale to height
        co, _ = mesh_np(body.data)
        lo, hi = co.min(0), co.max(0)
        s = A.height / (hi[2] - lo[2])
        M = np.eye(4) * s; M[3, 3] = 1
        M[:3, 3] = -s * np.array([(lo[0] + hi[0]) / 2, np.median(co[:, 1]), lo[2]])
        transform_all(M)
        return {"toe_dy_over_H": round(dy / H, 4), "notes": notes, "scale": round(s, 5)}

    REP["orient"] = orient(); print("[autorig] orient", REP["orient"], flush=True)
    H = A.height
    transfer_colour(body)
    tick("orient+colour")

    # ---------------- 4. landmarks ----------------
    def axis_profile(g, z_from, z_to, start_xy, mask):
        """per z slice: the component nearest the running axis point -> area, centroid, x half-width"""
        prof = {}
        cxy = np.array(start_xy, float)
        for z in range(z_from, z_to + 1):
            lab, nl = label(mask[:, :, z])
            if nl == 0: continue
            I = w2v(g, [cxy[0], cxy[1], 0])[:2]
            l = lab[I[0], I[1]]
            if l == 0:
                pts = np.argwhere(lab > 0); k = np.argmin(((pts - I) ** 2).sum(1)); l = lab[tuple(pts[k])]
            pts = np.argwhere(lab == l)
            W = v2w(g, np.c_[pts, np.full(len(pts), z)])
            c = W[:, :2].mean(0)
            prof[z] = {"area": len(pts) * g.p ** 2, "c": c, "hw": (W[:, 0].max() - W[:, 0].min()) / 2,
                       "xmin": W[:, 0].min(), "xmax": W[:, 0].max(), "ymin": W[:, 1].min(), "ymax": W[:, 1].max()}
            cxy = 0.7 * cxy + 0.3 * c
        return prof

    def level_curve(g, mask, tip_seed, maxit=100000):
        ge = bfs(mask, tip_seed, maxit)
        fin = ge < INF
        idx = np.argwhere(fin)
        t = ge[fin].astype(int)
        W = v2w(g, idx)
        T = t.max() + 1
        cnt = np.bincount(t, minlength=T).astype(float); cnt[cnt == 0] = 1
        C = np.stack([np.bincount(t, weights=W[:, k], minlength=T) / cnt for k in range(3)], 1)
        sq = np.bincount(t, weights=(W ** 2).sum(1), minlength=T) / cnt
        rms = np.sqrt(np.maximum(sq - (C ** 2).sum(1), 0))
        return {"C": C, "cnt": cnt, "rms": rms, "ge": ge}

    def smooth_curve(C, k=2):
        out = C.copy()
        for i in range(len(C)):
            a, b = max(0, i - k), min(len(C), i + k + 1); out[i] = C[a:b].mean(0)
        return out

    def arclen(C):
        return np.r_[0, np.cumsum(np.linalg.norm(np.diff(C, axis=0), axis=1))]

    def point_at_s(C, s_cum, s):
        i = int(np.clip(np.searchsorted(s_cum, s), 1, len(C) - 1))
        f = (s - s_cum[i - 1]) / max(s_cum[i] - s_cum[i - 1], 1e-9)
        return C[i - 1] + np.clip(f, 0, 1) * (C[i] - C[i - 1])

    def bend_point(C, s_cum, s_lo, s_hi, min_deg=25):
        """max turning angle between incoming/outgoing chords inside [s_lo, s_hi] -> (s, angle)"""
        best = (None, 0)
        L = s_cum[-1]; h = 0.18 * L
        for i in range(len(C)):
            if not (s_lo <= s_cum[i] <= s_hi): continue
            a = point_at_s(C, s_cum, max(0, s_cum[i] - h)); b = point_at_s(C, s_cum, min(L, s_cum[i] + h))
            u, v = C[i] - a, b - C[i]
            nu, nv = np.linalg.norm(u), np.linalg.norm(v)
            if nu < 1e-6 or nv < 1e-6: continue
            ang = math.degrees(math.acos(np.clip(u @ v / nu / nv, -1, 1)))
            if ang > best[1]: best = (s_cum[i], ang)
        return best if best[1] >= min_deg else (None, best[1])

    def landmarks(ob, res):
        g = voxelize(ob, H / res)
        S = g.S
        LM = {"method": {}}
        zs = np.nonzero(S.any(axis=(0, 1)))[0]; z0, z1 = zs[0], zs[-1]; Hv = z1 - z0
        ztop_w = v2w(g, [0, 0, z1])[2]
        # feet seeds
        for zfrac in (0.03, 0.06, 0.10, 0.15):
            lab, areas, zf = slice_comps(g, zfrac)
            order = np.argsort(-areas)
            feet = [l + 1 for l in order[:2] if areas[l] > 0.15 * areas[order[0]]]
            if len(feet) == 2: break
        LM["feet_slice"] = zfrac
        feet_xyz = []
        for l in feet:
            pts = np.argwhere(lab == l); m = pts.mean(0); pk = pts[np.argmin(((pts - m) ** 2).sum(1))]
            feet_xyz.append(v2w(g, np.r_[pk, zf]))
        legs_ok = len(feet) == 2
        if not legs_ok: note("feet not separated at 3% height: legs fused / long skirt -> proportional legs")
        # crotch: lowest z where the two foot columns connect through the solid below z
        crotch_v = None
        if legs_ok:
            sA = np.zeros(S.shape, bool); sB = np.zeros(S.shape, bool)
            sA[tuple(w2v(g, feet_xyz[0]))] = True; sB[tuple(w2v(g, feet_xyz[1]))] = True
            lo_z, hi_z = zf + 1, z0 + int(0.8 * Hv)
            def conn(z):
                lb, _ = label(S[:, :, :z])
                a = lb[sA[:, :, :z]]; b = lb[sB[:, :, :z]]
                return a.size and b.size and a[0] == b[0] and a[0] > 0
            while hi_z - lo_z > 1:
                m = (lo_z + hi_z) // 2
                if conn(m): hi_z = m
                else: lo_z = m
            crotch_v = hi_z - 1
            lb, _ = label(S[:, :, :crotch_v])
            legmask = np.zeros(S.shape, bool)
            leg_parts = []
            for f in feet_xyz:
                I = w2v(g, f); l = lb[I[0], I[1], I[2]]
                m = np.zeros(S.shape, bool); m[:, :, :crotch_v] = lb == l; leg_parts.append(m); legmask |= m
            # left = +X
            if v2w(g, np.argwhere(leg_parts[0]).mean(0))[0] < v2w(g, np.argwhere(leg_parts[1]).mean(0))[0]:
                leg_parts = leg_parts[::-1]
        else:
            crotch_v = z0 + int(0.3 * Hv); legmask = np.zeros(S.shape, bool); leg_parts = [None, None]
        crotch_z = v2w(g, [0, 0, crotch_v])[2]
        # pelvis centre from leg centroids just below the crotch
        if legs_ok:
            cl = [v2w(g, np.argwhere(lp[:, :, max(z0, crotch_v - 3):crotch_v]).mean(0) + [0, 0, max(z0, crotch_v - 3)])
                  for lp in leg_parts]
            pel_xy = (cl[0][:2] + cl[1][:2]) / 2
            leg_area = sum(lp[:, :, crotch_v - 1].sum() for lp in leg_parts) * g.p ** 2
        else:
            idx = np.argwhere(S[:, :, crotch_v]); pel_xy = v2w(g, np.r_[idx.mean(0), crotch_v])[:2]; leg_area = 0
        prof = axis_profile(g, crotch_v, z1, pel_xy, S)
        a_above = np.mean([prof[z]["area"] for z in range(crotch_v + 1, crotch_v + 3) if z in prof])
        hem = bool(legs_ok and a_above > 2.6 * leg_area)
        LM["hem"] = hem
        # neck: min axis-component area in the upper body window
        zA = crotch_v + int(0.35 * (z1 - crotch_v)); zB = z1 - int(0.08 * Hv)
        cand = [(prof[z]["area"], z) for z in range(zA, zB) if z in prof]
        neck_v = min(cand)[1]
        neck_c = prof[neck_v]["c"]; neck_r = math.sqrt(prof[neck_v]["area"] / math.pi)
        neck_z = v2w(g, [0, 0, neck_v])[2]
        # head component (solid above the neck cut containing the top)
        above = S.copy(); above[:, :, :neck_v + 1] = False
        lb, _ = label(above)
        topI = w2v(g, [neck_c[0], neck_c[1], ztop_w])
        tz = np.nonzero(above[:, :, :].any(axis=(0, 1)))[0][-1]
        tpts = np.argwhere(above[:, :, tz]); k = np.argmin(((tpts - topI[:2]) ** 2).sum(1))
        headmask = lb == lb[tpts[k][0], tpts[k][1], tz]
        body_m = S & ~headmask
        # root + geodesic from pelvis on the body without the head
        root_z = crotch_z + 0.03 * H
        rseed = seed_at(g, body_m, [pel_xy[0], pel_xy[1], root_z])
        gd = bfs(body_m, rseed)
        unreach = body_m & (gd >= INF)          # hanging off the head only (ponytail, long hair)
        idx = np.argwhere(headmask | unreach)
        HW = v2w(g, idx)
        head_c = HW.mean(0)
        head_top = np.array([neck_c[0], neck_c[1], ztop_w])
        # torso half-width (median over mid torso band)
        tor = [prof[z]["hw"] for z in range(crotch_v + int(0.25 * (neck_v - crotch_v)), crotch_v + int(0.7 * (neck_v - crotch_v))) if z in prof]
        chest_hw = float(np.median(tor)) if tor else 0.12 * H
        # ---- arms ----
        armpool = body_m & ~legmask & (gd < INF)
        idx = np.argwhere(armpool); W = v2w(g, idx); gv = gd[armpool]
        arms = {}
        # extremity candidates: local maxima of the pelvis geodesic, then pick per side the one with the
        # longest tubular (limb-like) run before its level sets spread out (hands vs hood/hair/skirt corners)
        gp = np.where(armpool, gd, -1.0)
        loc = gp.copy()
        for _ in range(4):
            for ax in range(3): loc = np.maximum(loc, np.maximum(shift(loc, ax, 1, -1), shift(loc, ax, -1, -1)))
        cmask = armpool & (gp >= loc) & (gp > 0.15 * H / g.p)
        cands = []
        if cmask.any():
            lb, nl = label(dilate(dilate(cmask, True), True))
            for l in range(1, nl + 1):
                sel = (lb == l) & cmask; ids = np.argwhere(sel); k = int(np.argmax(gd[sel])); cands.append(ids[k])
        def tubular(tipI, sgn):
            seed = np.zeros(S.shape, bool); seed[tuple(tipI)] = True
            lc = level_curve(g, armpool, seed)
            C = smooth_curve(lc["C"]); rms = lc["rms"]
            tip = v2w(g, tipI)
            sh_guess = np.array([pel_xy[0] + sgn * chest_hw, pel_xy[1], neck_z - 0.25 * (neck_z - crotch_z)])
            tmin = int(0.4 * np.linalg.norm(tip - sh_guess) / g.p)
            r_lim = 0.055 * H / g.p
            J = None
            # limb-like run: level sets stay narrower than a limb radius limit
            Jr = next((t for t in range(3, len(C)) if rms[t] > r_lim and t + 1 < len(C) and rms[t + 1] > r_lim), len(C) - 1)
            for t in range(max(tmin, 3), len(C)):
                base = np.median(rms[max(2, t - 8):t])
                jump = t + 2 < len(rms) and min(rms[t:t + 3]) > 1.8 * base
                hd = abs(C[t, 0] - pel_xy[0])
                if hd < chest_hw or (jump and hd < 1.6 * chest_hw):
                    J = t; break
            tub = Jr * g.p
            return lc, C, rms, J, tub, sh_guess
        arms = {}
        for side, sgn in (("L", 1), ("R", -1)):
            best = None
            for tipI in cands:
                tip = v2w(g, tipI)
                if (tip[0] - pel_xy[0]) * sgn <= 0.5 * neck_r: continue
                res = tubular(tipI, sgn)
                if DEBUG: print(f"[autorig] cand {side} tip={np.round(tip,3)} tub={res[4]:.3f} J={res[3]} n={len(res[1])} rms={np.round(res[2][:40:2]/g.p,1)}", flush=True)
                if best is None or res[4] > best[1][4]: best = (tipI, res)
            if best is None: arms[side] = None; note(f"no arm candidate on side {side}"); continue
            tipI, (lc, C, rms, J, tub, sh_guess) = best
            tip = v2w(g, tipI)
            LM.setdefault("arm_cands", {})[side] = len(cands)
            if J is None:
                J = int(np.argmin(np.linalg.norm(C - sh_guess, axis=1))); LM["method"]["arm_" + side] = "nearest-guess"
            else:
                LM["method"]["arm_" + side] = "levelset"
            Ca = C[:J + 1]; s_cum = arclen(Ca); L = s_cum[-1]
            r_up = float(np.median(rms[int(0.5 * J):J + 1]) * math.sqrt(2)) if J > 4 else 0.03 * H
            k0 = max(0, int(0.75 * J))
            u = Ca[-1] - Ca[k0]; u = u / (np.linalg.norm(u) + 1e-9)
            shoulder = Ca[-1] + u * 0.7 * r_up
            # raise to sit ~1 arm radius under the top of the shoulder (glenohumeral joint, not the armpit)
            I = w2v(g, shoulder); ztop = I[2]
            while ztop + 1 < S.shape[2] and body_m[I[0], I[1], ztop + 1] and v2w(g, [0, 0, ztop + 1])[2] < neck_z: ztop += 1
            zt = v2w(g, [0, 0, ztop])[2]
            if zt - 1.1 * r_up > shoulder[2]:
                shoulder[2] = min(zt - 1.1 * r_up, shoulder[2] + 2.0 * r_up)
            # arm length sanity vs torso length
            torso_len = neck_z - crotch_z
            if np.linalg.norm(shoulder - tip) < 0.55 * torso_len:
                note(f"arm {side} too short ({np.linalg.norm(shoulder - tip):.3f}) -> fused arm, shoulder from torso width")
                shoulder = np.array([pel_xy[0] + sgn * max(chest_hw - r_up, 0.5 * chest_hw), pel_xy[1],
                                     neck_z - 0.15 * torso_len])
                Ca = np.linspace(tip, shoulder, 20); s_cum = arclen(Ca); L = s_cum[-1]
                LM["method"]["arm_" + side] = "fallback-straight"
            # wrist: area minimum near the hand
            cnt = lc["cnt"][:J + 1]
            ilo = np.searchsorted(s_cum, 0.08 * L); ihi = max(ilo + 1, np.searchsorted(s_cum, 0.40 * L))
            iw = ilo + int(np.argmin(cnt[ilo:ihi])) if ihi > ilo else ilo
            if LM["method"]["arm_" + side] != "fallback-straight" and cnt[:iw].size and cnt[:iw].max() > 1.25 * cnt[iw] and 0.12 * L < s_cum[iw] < 0.38 * L:
                s_w = s_cum[iw]; LM["method"]["wrist_" + side] = "area-min"
            else:
                s_w = 0.24 * L; LM["method"]["wrist_" + side] = "proportion"
            wrist = point_at_s(Ca, s_cum, s_w)
            # elbow: bend point or 0.46 of wrist->shoulder
            sb, ang = bend_point(Ca, s_cum, s_w + 0.25 * (L - s_w), s_w + 0.75 * (L - s_w))
            s_e = sb if sb is not None else s_w + 0.46 * (L - s_w)
            elbow = point_at_s(Ca, s_cum, s_e)
            LM["method"]["elbow_" + side] = f"bend {ang:.0f}deg" if sb is not None else f"proportion (max bend {ang:.0f})"
            r_el = float(math.sqrt(lc["cnt"][min(np.searchsorted(s_cum, s_e), J)] / math.pi) * g.p)
            arms[side] = {"tip": tip, "wrist": wrist, "elbow": elbow, "shoulder": shoulder, "r_up": r_up, "r_el": max(r_el, 0.5 * r_up)}
            if LM["method"]["arm_" + side] == "levelset":
                LM.setdefault("armreg", {})[side] = lc["ge"] <= J
        # ---- legs ----
        legs = {}
        for side, li in (("L", 0), ("R", 1)):
            if not legs_ok:
                sgn = 1 if side == "L" else -1
                hx = pel_xy[0] + sgn * 0.45 * chest_hw
                hip = np.array([hx, pel_xy[1], crotch_z]); ank = np.array([hx, pel_xy[1], 0.045 * H])
                legs[side] = {"toe": ank + [0, -0.08 * H, -0.04 * H], "ankle": ank, "heel": ank + [0, 0.03 * H, -0.04 * H],
                              "knee": (hip + ank) / 2 + [0, -0.005 * H, 0], "hip": hip, "r_th": 0.05 * H, "r_kn": 0.04 * H}
                LM["method"]["leg_" + side] = "proportion"; continue
            lp = leg_parts[li]
            if DEBUG: print(f"[autorig] leg {side} vox={lp.sum()} reach={(gd[lp] < INF).sum()} body={body_m.sum()} S={S.sum()} head={headmask.sum()} crotch_v={crotch_v} neck_v={neck_v} feet={np.round(feet_xyz,3).tolist()}", flush=True)
            idx = np.argwhere(lp); W = v2w(g, idx)
            low = W[:, 2] < 0.12 * H
            gl = np.where(low & (gd[lp] < INF), gd[lp], -1)
            if gl.max() < 0: gl = np.where(gd[lp] < INF, gd[lp], -1)
            # toe: farthest from pelvis among foot voxels, preferring the front-most
            # toe: front-most (-Y) foot voxel among the low ones (orientation is known by now)
            lowm = (W[:, 2] < 0.06 * H) & (gd[lp] < INF)
            if lowm.any():
                k = int(np.argmin(np.where(lowm, W[:, 1] - 0.3 * W[:, 2], np.inf)))
            else:
                k = int(np.argmax(gl))
            tipI = idx[k]; toe = v2w(g, tipI)
            seed = np.zeros(S.shape, bool); seed[tuple(tipI)] = True
            lc = level_curve(g, body_m, seed)
            C = smooth_curve(lc["C"])
            J = next((t for t in range(len(C)) if C[t, 2] >= crotch_z), len(C) - 1)
            Cl = C[:J + 1]; s_cum = arclen(Cl); L = s_cum[-1]
            tang = np.gradient(Cl, axis=0); tz = tang[:, 2] / (np.linalg.norm(tang, axis=1) + 1e-9)
            ia = next((i for i in range(2, len(Cl) - 2) if tz[i] > 0.75 and tz[i + 1] > 0.75 and tz[i + 2] > 0.75), None)
            if ia is None:
                ankle = point_at_s(Cl, s_cum, 0.25 * L); LM["method"]["ankle_" + side] = "proportion"
            else:
                ankle = Cl[ia].copy(); LM["method"]["ankle_" + side] = "turn"
            ankle[2] = max(ankle[2], 0.03 * H)
            r_th = float(math.sqrt(lp[:, :, crotch_v - 2].sum() / math.pi) * g.p) if crotch_v >= 2 else 0.05 * H
            hip = Cl[-1].copy()
            if hem:
                hip_hem = ankle[2] + 0.55 * (neck_z - ankle[2])
                hip[2] = max(hip[2] + 0.6 * r_th, hip_hem)
                LM["method"]["hip_" + side] = "hem-proportion"
            else:
                hip[2] = max(hip[2], crotch_z) + 0.6 * r_th; LM["method"]["hip_" + side] = "crotch"
            # knee: bend point or midpoint (on the curve, measured from the ankle)
            sa = s_cum[ia] if ia is not None else 0.25 * L
            L_ah = (L - sa) + max(0, hip[2] - Cl[-1][2])
            sb, ang = bend_point(Cl, s_cum, sa + 0.3 * (L - sa), sa + 0.8 * (L - sa))
            s_k = sb if sb is not None else min(sa + 0.5 * L_ah, L)
            knee = point_at_s(Cl, s_cum, s_k)
            LM["method"]["knee_" + side] = f"bend {ang:.0f}" if sb is not None else f"midpoint (max bend {ang:.0f})"
            r_kn = float(math.sqrt(lc["cnt"][min(np.searchsorted(s_cum, s_k), J)] / math.pi) * g.p)
            footW = W[W[:, 2] < ankle[2]]
            fdir = toe[:2] - ankle[:2]; fdir = fdir / (np.linalg.norm(fdir) + 1e-9)
            proj = (footW[:, :2] - ankle[:2]) @ fdir
            heel = footW[np.argmin(proj)].copy() if len(footW) else ankle + [0, 0.03 * H, -0.03 * H]
            toe_tip = footW[np.argmax(proj)].copy() if len(footW) else toe
            legs[side] = {"toe": toe_tip, "ankle": ankle, "heel": heel, "knee": knee, "hip": hip, "r_th": r_th, "r_kn": max(r_kn, 0.6 * r_th)}
        # ---- spine / neck / head ----
        sh_z = np.mean([arms[s]["shoulder"][2] for s in arms if arms[s] is not None]) if any(arms.values()) else neck_z - 0.1 * H
        hip_z = np.mean([legs[s]["hip"][2] for s in legs])
        neck_base_z = sh_z + 0.5 * max(neck_z - sh_z, 0.02 * H)
        head_start_z = min(neck_z + 0.6 * max(neck_z - neck_base_z, 0.01 * H), head_c[2] - 0.25 * (ztop_w - head_c[2]))
        head_start_z = max(head_start_z, neck_z + 0.005 * H)
        def axis_at(z):
            zi = int(w2v(g, [0, 0, z])[2]); zi = min(max(zi, min(prof)), max(prof))
            while zi not in prof and zi > min(prof): zi -= 1
            p = prof[zi]
            depth = p["ymax"] - p["ymin"]
            return np.array([p["c"][0], p["c"][1] + 0.12 * depth, z])
        spine_z = [hip_z, hip_z + 0.22 * (neck_base_z - hip_z), hip_z + 0.47 * (neck_base_z - hip_z),
                   hip_z + 0.72 * (neck_base_z - hip_z), neck_base_z]
        spine_pts = [axis_at(z) for z in spine_z]
        spine_pts[0][:2] = [pel_xy[0], (spine_pts[0][1] + pel_xy[1]) / 2]
        nm = np.array([neck_c[0], neck_c[1], (neck_base_z + head_start_z) / 2])
        hs = np.array([neck_c[0], neck_c[1], head_start_z])
        top = np.array([hs[0], hs[1], ztop_w])
        LM.update({"grid": g, "S": S, "headmask": headmask, "unreach": unreach, "legmask": legmask, "gd": gd,
                   "crotch_z": crotch_z, "neck_z": neck_z, "neck_r": neck_r, "head_c": head_c, "head_top": top,
                   "pel_xy": pel_xy, "chest_hw": chest_hw, "arms": arms, "legs": legs, "spine": spine_pts,
                   "neck_mid": nm, "head_start": hs, "body_m": body_m, "prof": prof, "crotch_v": crotch_v})
        return LM

    # ---------------- 5. armature ----------------
    import addon_utils
    try:
        addon_utils.enable("rigify", default_set=True)
        RIGIFY = True
    except Exception as e:
        RIGIFY = False; note(f"rigify addon unavailable: {e}")

    def detect_chains(LM):
        """optional hair/ponytail chains (from voxels hanging off the head) and skirt (hem) chains"""
        g = LM["grid"]; chains = []
        if A.chains == "none": return chains
        HH = LM["headmask"] | LM["unreach"]
        hc = LM["head_c"]
        gh = bfs(HH, seed_at(g, HH, hc))
        top_d = gh[tuple(w2v(g, LM["head_top"]))]
        rh = float(top_d if top_d < INF else np.max(gh[gh < INF]) * 0.6)
        fin = (gh < INF) & HH
        mx = np.where(fin, gh, -1)
        loc = mx.copy()
        for _ in range(3):
            for ax in range(3): loc = np.maximum(loc, np.maximum(shift(loc, ax, 1, -1), shift(loc, ax, -1, -1)))
        cand = fin & (mx >= loc) & (mx > 1.6 * rh)
        if cand.any():
            lb, nl = label(dilate(dilate(cand, True), True))
            tips = []
            for l in range(1, nl + 1):
                sel = (lb == l) & cand; ids = np.argwhere(sel); k = np.argmax(gh[sel]); tips.append((gh[sel][k], ids[k]))
            tips.sort(key=lambda t: -t[0])
            for _, tipI in tips[:4]:
                seed = np.zeros(HH.shape, bool); seed[tuple(tipI)] = True
                lc = level_curve(g, HH, seed)
                C = smooth_curve(lc["C"])
                # stop when the curve reaches within ~0.8 head radius (world) of the head centre
                rw = rh * g.p
                stop = next((t for t in range(len(C)) if np.linalg.norm(C[t] - hc) < 0.85 * rw), len(C) - 1)
                Cc = C[:stop + 1][::-1]
                if arclen(Cc)[-1] < 0.25 * rw: continue
                tip = v2w(g, tipI)
                behind = tip[1] > hc[1] + 0.25 * rw and abs(tip[0] - hc[0]) < 0.7 * rw
                chains.append({"kind": "ponytail" if behind else "hair", "curve": Cc, "x": tip[0] - LM["pel_xy"][0]})
        if LM["hem"]:
            chains.append({"kind": "skirt"})
        return chains

    def build_armature(LM, chains):
        arm_d = bpy.data.armatures.new("rig"); rig = new_obj("rig", arm_d)
        arm_d.display_type = "STICK"
        bpy.context.view_layer.objects.active = rig
        bpy.ops.object.mode_set(mode="EDIT")
        eb = arm_d.edit_bones
        def V(p): return Vector([float(x) for x in p])
        def bone(name, h, t, parent=None, connect=False, deform=True, roll_vec=None):
            b = eb.new(name); b.head = V(h); b.tail = V(t)
            if (b.tail - b.head).length < 1e-4: b.tail = b.head + Vector((0, 0, 0.01 * H))
            if parent: b.parent = eb[parent]; b.use_connect = connect
            b.use_deform = deform
            if roll_vec is not None: b.align_roll(V(roll_vec))
            return b
        sp = LM["spine"]
        bone("spine", sp[0], sp[1], roll_vec=(0, -1, 0))
        bone("spine.001", sp[1], sp[2], "spine", True, roll_vec=(0, -1, 0))
        bone("spine.002", sp[2], sp[3], "spine.001", True, roll_vec=(0, -1, 0))
        bone("spine.003", sp[3], sp[4], "spine.002", True, roll_vec=(0, -1, 0))
        bone("spine.004", sp[4], LM["neck_mid"], "spine.003", True, roll_vec=(0, -1, 0))
        bone("spine.005", LM["neck_mid"], LM["head_start"], "spine.004", True, roll_vec=(0, -1, 0))
        bone("spine.006", LM["head_start"], LM["head_top"], "spine.005", True, roll_vec=(0, -1, 0))
        for s, sgn in (("L", 1), ("R", -1)):
            a = LM["arms"][s]
            if a is not None:
                clav_h = np.array([sp[4][0] + sgn * 0.25 * abs(a["shoulder"][0] - sp[4][0]), sp[4][1] - 0.15 * a["r_up"], sp[4][2] - 0.25 * a["r_up"]])
                sh = a["shoulder"].copy(); el = a["elbow"].copy(); el[1] += 0.12 * a["r_el"]   # tiny back-bend for IK
                bone(f"shoulder.{s}", clav_h, sh, "spine.003", roll_vec=(0, 0, 1))
                bone(f"upper_arm.{s}", sh, el, f"shoulder.{s}", False, roll_vec=(0, 1, 0))
                bone(f"forearm.{s}", el, a["wrist"], f"upper_arm.{s}", True, roll_vec=(0, 1, 0))
                bone(f"hand.{s}", a["wrist"], a["tip"], f"forearm.{s}", True, roll_vec=(0, 1, 0))
            l = LM["legs"][s]
            kn = l["knee"].copy(); kn[1] -= 0.15 * l["r_kn"]   # tiny forward knee for IK
            ball = l["ankle"] + 0.68 * (l["toe"] - l["ankle"]); ball[2] = max(0.25 * l["ankle"][2], 0.012 * H)
            toe = l["toe"].copy(); toe[2] = ball[2]
            bone(f"thigh.{s}", l["hip"], kn, "spine", roll_vec=(0, -1, 0))
            bone(f"shin.{s}", kn, l["ankle"], f"thigh.{s}", True, roll_vec=(0, -1, 0))
            bone(f"foot.{s}", l["ankle"], ball, f"shin.{s}", True, roll_vec=(0, 0, 1))
            bone(f"toe.{s}", ball, toe, f"foot.{s}", True, roll_vec=(0, 0, 1))
            hw = 0.5 * l["r_kn"]
            heel = l["heel"].copy(); heel[2] = 0.0
            bone(f"heel.02.{s}", heel + [sgn * hw, 0, 0], heel + [-sgn * hw, 0, 0], f"foot.{s}", deform=False)
        # optional chains
        nh = {"hair": 0, "ponytail": 0}
        for ch in chains:
            if ch["kind"] in ("hair", "ponytail"):
                C = ch["curve"]; s_cum = arclen(C); L = s_cum[-1]
                pts = [point_at_s(C, s_cum, f * L) for f in (0, 1 / 3, 2 / 3, 1)]
                if ch["kind"] == "ponytail":
                    nh["ponytail"] += 1; base = "ponytail" if nh["ponytail"] == 1 else f"ponytail{nh['ponytail']}"
                    names = [f"{base}.{i:02d}" for i in (1, 2, 3)]
                else:
                    nh["hair"] += 1; side = "L" if ch["x"] > 0 else "R"
                    names = [f"hair{nh['hair']}.{i:02d}.{side}" for i in (1, 2, 3)]
                par = "spine.006"
                for i, nm in enumerate(names):
                    bone(nm, pts[i], pts[i + 1], par, i > 0, roll_vec=(0, -1, 0)); par = nm
                ch["bones"] = names
            elif ch["kind"] == "skirt":
                g = LM["grid"]; S = LM["S"]; cv = LM["crotch_v"]
                hip_z = (LM["legs"]["L"]["hip"][2] + LM["legs"]["R"]["hip"][2]) / 2
                top_z = hip_z + 0.35 * (LM["spine"][2][2] - hip_z)
                hem_z = LM["crotch_z"]
                idx = np.argwhere(S[:, :, cv + 1]); W = v2w(g, np.c_[idx, np.full(len(idx), cv + 1)])
                c = np.array([LM["pel_xy"][0], LM["pel_xy"][1]])
                pt = LM["prof"].get(int(w2v(g, [0, 0, top_z])[2]))
                r_top = 0.6 * (pt["hw"] if pt else LM["chest_hw"])
                names = []
                for nm, ang in (("skirt_F", 0), ("skirt_front.L", 45), ("skirt_side.L", 90), ("skirt_back.L", 135),
                                ("skirt_B", 180), ("skirt_back.R", 225), ("skirt_side.R", 270), ("skirt_front.R", 315)):
                    d = np.array([math.sin(math.radians(ang)), -math.cos(math.radians(ang))])
                    proj = (W[:, :2] - c) @ d
                    r_hem = float(np.percentile(proj, 98)) * 0.85
                    p0 = np.r_[c + d * r_top, top_z]; p2 = np.r_[c + d * r_hem, hem_z + 0.01 * H]
                    p1 = 0.5 * (p0 + p2)
                    base, side = (nm.split(".") + [""])[:2]
                    n1 = f"{base}.01" + (f".{side}" if side else ""); n2 = f"{base}.02" + (f".{side}" if side else "")
                    bone(n1, p0, p1, "spine", roll_vec=(0, -1, 0)); bone(n2, p1, p2, n1, True, roll_vec=(0, -1, 0))
                    names += [n1, n2]
                    ch.setdefault("roots", []).append((n1, ang))
                ch["bones"] = names
        bpy.ops.object.mode_set(mode="OBJECT")
        if RIGIFY:
            types = {"spine": "spines.basic_spine", "spine.004": "spines.super_head", "shoulder.L": "basic.super_copy",
                     "shoulder.R": "basic.super_copy", "upper_arm.L": "limbs.arm", "upper_arm.R": "limbs.arm",
                     "thigh.L": "limbs.leg", "thigh.R": "limbs.leg"}
            for ch in chains:
                if ch.get("bones"):
                    heads = [b for b in ch["bones"] if b.endswith(".01") or ".01." in b]
                    for b in heads: types[b] = "basic.copy_chain"
            for k, v in types.items():
                pb = rig.pose.bones.get(k)
                if pb is not None:
                    try: pb.rigify_type = v
                    except Exception: pass
        for pb in rig.pose.bones: pb.rotation_mode = "QUATERNION"
        # skirt follows the thighs (local rotation copy, weighted by angle)
        for ch in chains:
            if ch["kind"] != "skirt": continue
            for n1, ang in ch["roots"]:
                a = math.radians(ang)
                wl = max(0.0, math.sin(a)) * 0.75 + max(0.0, math.cos(a)) * 0.4 * 0.5
                wr = max(0.0, -math.sin(a)) * 0.75 + max(0.0, math.cos(a)) * 0.4 * 0.5
                if abs(math.cos(a)) > 0.9: wl = wr = 0.4 if math.cos(a) > 0 else 0.3
                for tgt, w in (("thigh.L", wl), ("thigh.R", wr)):
                    if w < 0.02: continue
                    c = rig.pose.bones[n1].constraints.new("COPY_ROTATION")
                    c.target = rig; c.subtarget = tgt; c.mix_mode = "ADD"
                    c.owner_space = "LOCAL"; c.target_space = "LOCAL"; c.influence = w
        return rig

    # ---------------- 6. skinning ----------------
    def deform_bones(rig):
        return [b.name for b in rig.data.bones if b.use_deform]

    def adjacency(nv, tri):
        e = np.r_[tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]]
        e = np.r_[e, e[:, ::-1]]
        return e

    def smooth_w(W, edges, it=3, lam=0.5):
        nv = len(W)
        deg = np.bincount(edges[:, 0], minlength=nv).astype(float); deg[deg == 0] = 1
        for _ in range(it):
            acc = np.zeros_like(W); np.add.at(acc, edges[:, 0], W[edges[:, 1]])
            W = (1 - lam) * W + lam * acc / deg[:, None]
        return W

    def limit_norm(W, k=4):
        if W.shape[1] > k:
            thr = -np.sort(-W, axis=1)[:, k - 1:k]
            W = np.where(W >= thr, W, 0)
        W[W < 0.01] = 0
        s = W.sum(1, keepdims=True); bad = s[:, 0] <= 0
        W = W / np.maximum(s, 1e-12)
        return W, bad

    def vert_voxels(g, co, mask):
        """nearest inside voxel index per vertex"""
        nv = len(co); I = w2v(g, co)
        ok = mask[I[:, 0], I[:, 1], I[:, 2]]
        best = I.copy(); bestd = np.where(ok, 0.0, INF)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    J = np.clip(I + [dx, dy, dz], 0, g.n - 1)
                    inside = mask[J[:, 0], J[:, 1], J[:, 2]]
                    d = np.linalg.norm(v2w(g, J) - co, axis=1)
                    upd = inside & (d < bestd) & ~ok
                    best[upd] = J[upd]; bestd[upd] = d[upd]
        miss = bestd >= INF
        if miss.any():
            idx = np.argwhere(mask); P = v2w(g, idx)
            for i in np.nonzero(miss)[0]:
                best[i] = idx[np.argmin(((P - co[i]) ** 2).sum(1))]
        return best

    def voxel_weights(LM, rig, ob, tau=0.022):
        g = LM["grid"]; S = LM["S"]
        co, tri = mesh_np(ob.data)
        names = deform_bones(rig)
        VI = vert_voxels(g, co, S)
        D = np.full((len(co), len(names)), INF, np.float32)
        maxit = int(0.7 * H / g.p)
        for j, nm in enumerate(names):
            b = rig.data.bones[nm]
            h, t = np.array(b.head_local), np.array(b.tail_local)
            seeds = np.zeros(S.shape, bool)
            for f in np.linspace(0, 1, max(3, int(np.linalg.norm(t - h) / g.p) * 2)):
                I = w2v(g, h + f * (t - h))
                if S[tuple(I)]: seeds[tuple(I)] = True
            if not seeds.any(): seeds = seed_at(g, S, (h + t) / 2)
            d = bfs(S, seeds, maxit)
            D[:, j] = d[VI[:, 0], VI[:, 1], VI[:, 2]] * g.p
        dmin = D.min(1, keepdims=True)
        W = np.exp(-(D - dmin) / (tau * H)); W[D >= INF] = 0
        return names, W, VI

    def heat_weights(rig, ob):
        for o in bpy.context.scene.objects: o.select_set(False)
        ob.vertex_groups.clear()
        ob.select_set(True); rig.select_set(True); bpy.context.view_layer.objects.active = rig
        bpy.ops.object.parent_set(type="ARMATURE_AUTO")
        names = deform_bones(rig)
        W = np.zeros((len(ob.data.vertices), len(names)))
        col = {vg.index: names.index(vg.name) for vg in ob.vertex_groups if vg.name in names}
        for v in ob.data.vertices:
            for ge in v.groups:
                if ge.group in col: W[v.index, col[ge.group]] = ge.weight
        return names, W

    def restrict(W, names, LM, VI, co):
        """head/hair vertices -> only head-chain bones; body vertices -> no head/hair bones"""
        headish = (LM["headmask"] | LM["unreach"])[VI[:, 0], VI[:, 1], VI[:, 2]]
        head_set = [i for i, n in enumerate(names) if n in ("spine.006", "spine.005") or n.startswith(("hair", "ponytail"))]
        neck_set = [i for i, n in enumerate(names) if n in ("spine.004", "spine.005", "spine.006")]
        hair_set = [i for i, n in enumerate(names) if n.startswith(("hair", "ponytail"))]
        top_only = np.zeros(len(names), bool); top_only[head_set] = True
        low = co[:, 2] < LM["head_start"][2]
        allowed_head = np.zeros(len(names), bool); allowed_head[head_set] = True; allowed_head[neck_set] = True
        Wn = W.copy()
        # limb/torso segmentation: torso voxels get no forearm/hand/shin/foot weight and only near-joint
        # upper_arm/thigh weight; arm voxels get no spine/leg weight (stops a sleeve touching the coat
        # dragging the torso along, and the torso dragging the arm)
        g = LM["grid"]
        armreg = LM.get("armreg", {})
        in_arm = {sd: m[VI[:, 0], VI[:, 1], VI[:, 2]] for sd, m in armreg.items()}
        in_leg = LM["legmask"][VI[:, 0], VI[:, 1], VI[:, 2]]
        torso = ~headish & ~in_leg
        for sd, m in in_arm.items(): torso &= ~m
        bi = {n: i for i, n in enumerate(names)}
        for sd in ("L", "R"):
            a = LM["arms"].get(sd)
            if a is not None and sd in in_arm:
                for n in (f"forearm.{sd}", f"hand.{sd}"):
                    if n in bi: Wn[torso, bi[n]] = 0
                if f"upper_arm.{sd}" in bi:
                    d = np.linalg.norm(co - a["shoulder"], axis=1)
                    f = np.clip(1 - (d - 1.0 * a["r_up"]) / (1.2 * a["r_up"]), 0, 1)
                    Wn[torso, bi[f"upper_arm.{sd}"]] *= f[torso]
                arm_v = in_arm[sd]
                keep = np.zeros(len(names), bool)
                for n in (f"shoulder.{sd}", f"upper_arm.{sd}", f"forearm.{sd}", f"hand.{sd}", "spine.003"):
                    if n in bi: keep[bi[n]] = True
                Wn[arm_v] *= keep
            l = LM["legs"][sd]
            for n in (f"shin.{sd}", f"foot.{sd}", f"toe.{sd}"):
                if n in bi: Wn[torso, bi[n]] = 0
            d = np.linalg.norm(co - l["hip"], axis=1)
            f = np.clip(1 - (d - 1.5 * l["r_th"]) / (1.5 * l["r_th"]), 0, 1)
            if f"thigh.{sd}" in bi: Wn[torso & (co[:, 2] > l["hip"][2]), bi[f"thigh.{sd}"]] *= f[torso & (co[:, 2] > l["hip"][2])]
        mh = headish & ~low
        Wn[mh] *= top_only
        Wn[headish & low] *= allowed_head
        nb = ~headish
        Wn[np.ix_(nb, hair_set)] = 0
        hi = names.index("spine.006")
        Wn[np.ix_(nb & (co[:, 2] < LM["neck_z"]), [hi])] = 0
        z = Wn.sum(1) <= 1e-9
        Wn[z & headish, hi] = 1.0
        Wn[z & ~headish] = W[z & ~headish]
        return Wn

    def set_deform(ob, mode):
        """mode: lbs | dqs | lbs+cs | dqs+cs  (cs = Corrective Smooth masked to joint-blend regions)"""
        arm = next(m for m in ob.modifiers if m.type == "ARMATURE")
        arm.use_deform_preserve_volume = mode.startswith("dqs")
        cs = next((m for m in ob.modifiers if m.type == "CORRECTIVE_SMOOTH"), None)
        if mode.endswith("+cs"):
            if cs is None:
                cs = ob.modifiers.new("CorrectiveSmooth", "CORRECTIVE_SMOOTH")
            cs.rest_source = "ORCO"; cs.smooth_type = "LENGTH_WEIGHTED"; cs.iterations = 10; cs.factor = 0.5
            cs.scale = 1.0; cs.use_pin_boundary = False; cs.vertex_group = "cs_mask"
        elif cs is not None:
            ob.modifiers.remove(cs)

    def write_cs_mask(ob, W):
        """joint-blend regions: 1 where weight is split between bones, 0 inside rigid regions"""
        srt = -np.sort(-W, axis=1)
        m = np.clip(2.5 * (1.0 - srt[:, 0]), 0, 1)
        vg = ob.vertex_groups.get("cs_mask") or ob.vertex_groups.new(name="cs_mask")
        for i in np.nonzero(m > 0.01)[0]: vg.add([int(i)], float(m[i]), "REPLACE")

    def write_weights(ob, rig, names, W):
        ob.vertex_groups.clear()
        vgs = [ob.vertex_groups.new(name=n) for n in names]
        for j, vg in enumerate(vgs):
            nz = np.nonzero(W[:, j])[0]
            for i in nz: vg.add([int(i)], float(W[i, j]), "REPLACE")
        mod = next((m for m in ob.modifiers if m.type == "ARMATURE"), None) or ob.modifiers.new("Armature", "ARMATURE")
        mod.object = rig; mod.use_deform_preserve_volume = False
        mod.use_vertex_groups = True
        ob.parent = rig; ob.matrix_parent_inverse.identity()
        write_cs_mask(ob, W)

    def skin(LM, rig, ob, method):
        co, tri = mesh_np(ob.data); edges = adjacency(len(co), tri)
        info = {}
        names, Wv, VI = voxel_weights(LM, rig, ob)
        if method in ("heat", "auto"):
            t = time.time()
            hn, Wh = heat_weights(rig, ob)
            assert hn == names
            empty = Wh.sum(1) < 1e-6
            info["heat_empty_pct"] = round(100 * float(empty.mean()), 2)
            info["heat_s"] = round(time.time() - t, 2)
        out = {}
        for m in (["voxel", "heat"] if method == "auto" else [method]):
            if m == "heat":
                W = Wh.copy()
                if empty.any(): W[empty] = Wv[empty] / np.maximum(Wv[empty].sum(1, keepdims=True), 1e-12)
            else:
                W = Wv.copy()
            W = restrict(W, names, LM, VI, co)
            W = smooth_w(W, edges, it=4, lam=0.5)
            W = restrict(W, names, LM, VI, co)
            W, bad = limit_norm(W)
            out[m] = W
        return names, out, info

    # ---------------- 7. posing helpers ----------------
    def reset_pose(rig):
        for pb in rig.pose.bones:
            pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.scale = (1, 1, 1)
        bpy.context.view_layer.update()

    def rot_world(rig, name, axis, deg, pivot="head"):
        pb = rig.pose.bones.get(name)
        if pb is None: return
        bpy.context.view_layer.update()
        piv = pb.head if pivot == "head" else pb.tail
        R = Matrix.Rotation(math.radians(deg), 4, Vector(axis))
        pb.matrix = Matrix.Translation(piv) @ R @ Matrix.Translation(-piv) @ pb.matrix
        bpy.context.view_layer.update()

    def aim(rig, name, direction, keep_roll=True):
        pb = rig.pose.bones.get(name)
        if pb is None: return
        bpy.context.view_layer.update()
        cur = (pb.tail - pb.head).normalized()
        d = Vector(direction).normalized()
        q = cur.rotation_difference(d)
        R = q.to_matrix().to_4x4()
        pb.matrix = Matrix.Translation(pb.head) @ R @ Matrix.Translation(-pb.head) @ pb.matrix
        bpy.context.view_layer.update()

    def bone_dir(rig, name):
        pb = rig.pose.bones[name]; return (pb.tail - pb.head).normalized()

    def rest_dir(rig, name):
        b = rig.data.bones[name]; return (b.tail_local - b.head_local).normalized()

    def ground(rig, ob):
        bpy.context.view_layer.update()
        me = eval_mesh(ob); co, _ = mesh_np(me); bpy.data.meshes.remove(me)
        pb = rig.pose.bones["spine"]
        mz = co[:, 2].min()
        M = pb.matrix.copy(); M.translation.z -= mz; pb.matrix = M
        bpy.context.view_layer.update()

    def rotv(v, axis, deg):
        return Matrix.Rotation(math.radians(deg), 3, Vector(axis)) @ Vector(v)

    def a_pose_targets(rig, arm_deg):
        """target world directions for a natural feminine A-pose (canonical frame: face -Y, left +X)"""
        T = {}
        for s, sgn in (("L", 1), ("R", -1)):
            a = math.radians(arm_deg)
            up = Vector((sgn * math.sin(a), 0, -math.cos(a)))
            up = rotv(up, (sgn * 1, 0, 0), 0)
            up = (up + Vector((0, -0.10, 0))).normalized()           # slightly forward
            fa = (up + Vector((0, -0.20, 0.02))).normalized()        # soft elbow (~12 deg), hands forward
            fa = (fa + Vector((-sgn * 0.07, 0, 0))).normalized()     # hands drift in toward the thighs
            T[f"upper_arm.{s}"] = up; T[f"forearm.{s}"] = fa; T[f"hand.{s}"] = fa
            T[f"thigh.{s}"] = Vector((sgn * math.sin(math.radians(2.5)), 0, -1)).normalized()
            T[f"shin.{s}"] = Vector((sgn * math.sin(math.radians(0.5)), 0.0, -1)).normalized()
        return T

    def pose_to_apose(rig, arm_deg):
        """returns max rotation applied (deg)"""
        T = a_pose_targets(rig, arm_deg)
        maxang = 0.0
        ROT = REP.setdefault("pass1_bone_dev", {})
        # spine upright, neck/head follow if far from vertical
        for nm in ("spine", "spine.001", "spine.002", "spine.003"):
            d = bone_dir(rig, nm); ang = math.degrees(d.angle(Vector((0, 0, 1))))
            if ang > 8:
                tgt = Vector((0, d.y * 0.3, 1)).normalized(); maxang = max(maxang, math.degrees(d.angle(tgt))); aim(rig, nm, tgt)
        for nm in ("spine.004", "spine.005", "spine.006"):
            d = bone_dir(rig, nm); ang = math.degrees(d.angle(Vector((0, 0, 1))))
            if ang > 15:
                tgt = Vector((0, -0.12, 1)).normalized(); maxang = max(maxang, math.degrees(d.angle(tgt))); aim(rig, nm, tgt)
        order = ["thigh.L", "shin.L", "thigh.R", "shin.R", "upper_arm.L", "forearm.L", "hand.L", "upper_arm.R", "forearm.R", "hand.R"]
        for nm in order:
            if nm not in rig.pose.bones: continue
            d = bone_dir(rig, nm); dev = math.degrees(d.angle(T[nm]))
            ROT[nm] = round(dev, 1)
            tol = A.apose_tol * (0.5 if nm.startswith(("thigh", "shin")) else 1.0)
            if dev <= tol and not A.force_apose: continue      # already a usable A-pose: don't touch garments
            maxang = max(maxang, dev); aim(rig, nm, T[nm])
        # feet: flat, pointing forward with ~6 deg toe-out, keep pitch
        for s, sgn in (("L", 1), ("R", -1)):
            if f"foot.{s}" not in rig.pose.bones: continue
            d = bone_dir(rig, f"foot.{s}"); r = rest_dir(rig, f"foot.{s}")
            hz = math.hypot(r.x, r.y)
            yaw = math.radians(6) * sgn
            tgt = Vector((math.sin(yaw) * hz, -math.cos(yaw) * hz, r.z)).normalized()
            ROT[f"foot.{s}"] = round(math.degrees(d.angle(tgt)), 1)
            if ROT[f"foot.{s}"] > A.apose_tol or A.force_apose:
                maxang = max(maxang, math.degrees(d.angle(tgt))); aim(rig, f"foot.{s}", tgt)
            d = bone_dir(rig, f"toe.{s}"); tz = Vector((tgt.x, tgt.y, 0)).normalized(); aim(rig, f"toe.{s}", tz)
        return maxang

    def bake_pose(rig, ob):
        bpy.context.view_layer.update()
        me = eval_mesh(ob); co, _ = mesh_np(me); bpy.data.meshes.remove(me)
        ob.modifiers.clear(); ob.parent = None; ob.vertex_groups.clear()
        set_co(ob.data, co)

    # ---------------- rendering ----------------
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = scene.render.resolution_y = A.tile
    scene.render.film_transparent = False
    sh = scene.display.shading
    sh.light = "STUDIO"; sh.color_type = "SINGLE"; sh.single_color = (0.78, 0.76, 0.72)
    sh.show_cavity = True; sh.cavity_type = "WORLD"; sh.show_object_outline = False
    scene.display.render_aa = "8"
    if scene.world is None: scene.world = bpy.data.worlds.new("w")
    scene.world.color = (0.92, 0.92, 0.92)
    scene.view_settings.view_transform = "Standard"
    cam_d = bpy.data.cameras.new("cam"); cam_d.type = "ORTHO"; cam_d.ortho_scale = 1.42 * H
    cam = new_obj("cam", cam_d); scene.camera = cam
    VIEWS = {"front": -90, "q34": -135, "side": 180}   # azimuth of camera position (deg, from +X)
    REP["views"] = list(VIEWS); REP["tile"] = A.tile

    def render(name, ob, mode="clay"):
        sh.color_type = "VERTEX" if mode != "single" else "SINGLE"
        for v, az in VIEWS.items():
            a = math.radians(az); el = math.radians(8)
            d = Vector((math.cos(a) * math.cos(el), math.sin(a) * math.cos(el), math.sin(el)))
            tgt = Vector((0, 0, 0.52 * H))
            cam.location = tgt + d * 5 * H
            cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
            cam_d.clip_end = 20 * H
            scene.render.filepath = os.path.join(A.out, "tiles", f"{name}_{v}.png")
            bpy.ops.render.render(write_still=True)

    def debug_skeleton(rig, ob, tag):
        """x-ray render of the mesh with the fitted joints/bones as red geometry"""
        bm = bmesh.new()
        for b in rig.data.bones:
            h, t = b.head_local, b.tail_local
            r = 0.006 * H
            m = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=r * 1.8)
            bmesh.ops.translate(bm, verts=m["verts"], vec=h)
            d = t - h
            if d.length > 1e-5:
                c = bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=r, radius2=r * 0.4, depth=d.length)
                q = Vector((0, 0, 1)).rotation_difference(d.normalized())
                bmesh.ops.rotate(bm, verts=c["verts"], cent=Vector((0, 0, 0)), matrix=q.to_matrix())
                bmesh.ops.translate(bm, verts=c["verts"], vec=(h + t) / 2)
        me = bpy.data.meshes.new("dbg"); bm.to_mesh(me); bm.free()
        ca = me.color_attributes.new("Col", "BYTE_COLOR", "POINT")
        ca.data.foreach_set("color", np.tile([0.9, 0.05, 0.05, 1.0], len(me.vertices)).astype(np.float32))
        dbg = new_obj("dbg", me)
        old = (sh.show_xray, sh.xray_alpha, sh.color_type)
        sh.show_xray = True; sh.xray_alpha = 0.35
        render("debug_" + tag, ob)
        sh.show_xray, sh.xray_alpha, sh.color_type = old
        bpy.data.objects.remove(dbg); bpy.data.meshes.remove(me)

    # ---------------- 8. pass 1: fit in the input pose, bring to A-pose ----------------
    if DEBUG:
        sh.show_xray = True; sh.xray_alpha = 0.5; render("debug_clean", body); sh.show_xray = False
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(A.out, "debug_clean.blend"))
    LM = landmarks(body, A.res)
    tick("landmarks-1")
    chains = detect_chains(LM)
    rig = build_armature(LM, chains)
    if DEBUG: debug_skeleton(rig, body, "pass1")
    names, Wd, _ = skin(LM, rig, body, "voxel")
    write_weights(body, rig, names, Wd["voxel"])
    tick("fit+skin-1")
    ang = pose_to_apose(rig, A.arm_angle)
    ground(rig, body)
    print("[autorig] pass1 dev", REP.get("pass1_bone_dev"), flush=True)
    REP["pass1"] = {"max_rotation_deg": round(ang, 1), "landmark_methods": LM["method"], "hem": LM["hem"]}
    bake_pose(rig, body)
    if DEBUG: render("debug_baked", body)
    bpy.data.objects.remove(rig)
    # rebuild colour source in the baked pose: transfer from the deformed mesh itself
    co_b, tri_b = mesh_np(body.data)
    if ang > 20:
        note(f"input pose differed from A-pose by up to {ang:.0f} deg -> re-remesh after bake")
        col = np.empty(len(co_b) * 4, np.float32); body.data.color_attributes["Col"].data.foreach_get("color", col)
        Src.co = co_b; Src.tri = tri_b
        src_col = np.repeat(col.reshape(-1, 4)[tri_b.ravel()].reshape(-1, 4), 1, axis=0)
        src_fimg = np.full(len(tri_b), -1, np.int32)
        src_uv = np.zeros((len(tri_b) * 3, 2), np.float32)
        REP["cleanup2"] = cleanup(body, H, A.tris)
        transfer_colour(body)
    tick("pose-normalise")

    # ---------------- 9. pass 2: symmetry, final fit, skin ----------------
    co, tri = mesh_np(body.data)
    lo, hi = co.min(0), co.max(0)
    s = A.height / (hi[2] - lo[2])
    co = (co - [0, 0, lo[2]]) * s
    set_co(body.data, co)
    LM = landmarks(body, A.res)
    # recentre on the pelvis
    off = np.array([LM["pel_xy"][0], LM["pel_xy"][1], 0])
    co, tri = mesh_np(body.data)
    co = co - off; set_co(body.data, co)
    # symmetry check (mirror X) with plane refinement
    from mathutils.kdtree import KDTree
    kd = KDTree(len(co))
    for i, p in enumerate(co): kd.insert(p, i)
    kd.balance()
    dx = 0.0
    for _ in range(3):
        mir = co.copy(); mir[:, 0] = 2 * dx - mir[:, 0]
        nn = np.array([kd.find(p)[1] for p in mir])
        dx = float(np.median((co[nn, 0] + co[:, 0]) / 2))
    mir = co.copy(); mir[:, 0] = 2 * dx - mir[:, 0]
    dd = np.array([kd.find(p)[2] for p in mir]) / H
    sym = {"plane_x": round(dx, 4), "p50": round(float(np.percentile(dd, 50)), 4), "p90": round(float(np.percentile(dd, 90)), 4),
           "p97": round(float(np.percentile(dd, 97)), 4)}
    do_sym = A.sym == "on" or (A.sym == "auto" and sym["p97"] < 0.012 and sym["p90"] < 0.006)
    sym["applied"] = bool(do_sym)
    if do_sym:
        co[:, 0] -= dx; set_co(body.data, co)
        bm = bmesh.new(); bm.from_mesh(body.data)
        bmesh.ops.symmetrize(bm, input=bm.verts[:] + bm.edges[:] + bm.faces[:], direction="-X", dist=1e-4 * H)
        bmesh.ops.triangulate(bm, faces=bm.faces[:])
        bm.to_mesh(body.data); bm.free(); body.data.update()
    REP["symmetry"] = sym
    LM = landmarks(body, A.res)
    if do_sym:   # symmetric skeleton
        for k in ("arms", "legs"):
            Lb, Rb = LM[k]["L"], LM[k]["R"]
            if Lb is None or Rb is None: continue
            for j in Lb:
                if isinstance(Lb[j], np.ndarray):
                    m = (Lb[j] + Rb[j] * [-1, 1, 1]) / 2; Lb[j] = m; Rb[j] = m * [-1, 1, 1]
                else:
                    Lb[j] = Rb[j] = (Lb[j] + Rb[j]) / 2
        for p in LM["spine"] + [LM["neck_mid"], LM["head_start"], LM["head_top"]]: p[0] = 0.0
    tick("landmarks-2")
    chains = detect_chains(LM)
    rig = build_armature(LM, chains)
    if DEBUG: debug_skeleton(rig, body, "pass2")
    names, Wd, sk_info = skin(LM, rig, body, A.weights)
    tick("fit+skin-2")
    co, tri = mesh_np(body.data)
    REP["mesh"] = {"tris": int(len(tri)), "verts": int(len(co)), "height": A.height,
                   "volume": round(signed_volume(co, tri), 5), "components": int(components(len(co), tri)[1])}
    def r3(p): return [round(float(x), 4) for x in p]
    REP["landmarks"] = {"crotch_z": round(float(LM["crotch_z"]), 4), "neck_z": round(float(LM["neck_z"]), 4),
                        "head_top": r3(LM["head_top"]), "hem": LM["hem"], "chest_halfwidth": round(LM["chest_hw"], 4),
                        "arms": {s: ({k: r3(v) if isinstance(v, np.ndarray) else round(v, 4) for k, v in a.items()} if a else None) for s, a in LM["arms"].items()},
                        "legs": {s: {k: r3(v) if isinstance(v, np.ndarray) else round(v, 4) for k, v in l.items()} for s, l in LM["legs"].items()},
                        "methods": LM["method"], "chains": [c["kind"] + ":" + ",".join(c.get("bones", [])[:1]) for c in chains]}
    REP["bones"] = [b.name for b in rig.data.bones]
    REP["bones_rest"] = {b.name: {"head": r3(b.head_local), "tail": r3(b.tail_local), "parent": b.parent.name if b.parent else None,
                                  "deform": b.use_deform} for b in rig.data.bones}
    REP["frame"] = "internal: Z up, faces -Y, left +X, feet z=0 (saved .blend/.glb rotated to face %s)" % A.facing
    REP["mesh"]["bbox"] = [r3(co.min(0)), r3(co.max(0))]
    REP["head_c"] = r3(LM["head_c"])

    # ---------------- 10. pose tests ----------------
    def P_contact(rig, side="L"):
        o = "R" if side == "L" else "L"; sg = 1 if side == "L" else -1
        rot_world(rig, "spine", (0, 0, 1), -6 * sg)            # front hip forward
        rot_world(rig, "spine", (0, 1, 0), 3 * sg)
        rot_world(rig, "spine.002", (0, 0, 1), 5 * sg); rot_world(rig, "spine.003", (0, 0, 1), 4 * sg)
        rot_world(rig, "spine.004", (0, 0, 1), -3 * sg)
        th = rest_dir(rig, f"thigh.{side}")
        aim(rig, f"thigh.{side}", rotv(Vector((-sg * 0.03, 0, -1)), (1, 0, 0), -26))
        aim(rig, f"shin.{side}", rotv(Vector((0, 0, -1)), (1, 0, 0), -20))
        aim(rig, f"foot.{side}", rotv(Vector((0, -1, 0)), (1, 0, 0), -14))
        aim(rig, f"toe.{side}", rotv(Vector((0, -1, 0)), (1, 0, 0), -14))
        aim(rig, f"thigh.{o}", rotv(Vector((sg * 0.03, 0, -1)), (1, 0, 0), 16))
        aim(rig, f"shin.{o}", rotv(Vector((0, 0, -1)), (1, 0, 0), 34))
        aim(rig, f"foot.{o}", rotv(Vector((0, -1, 0)), (1, 0, 0), 38))
        aim(rig, f"toe.{o}", Vector((0, -1, 0)))
        for s2, sw in ((side, 14), (o, -16)):
            sgn2 = 1 if s2 == "L" else -1
            rot_world(rig, f"upper_arm.{s2}", (1, 0, 0), sw)
            rot_world(rig, f"forearm.{s2}", (1, 0, 0), -14 if sw < 0 else -6)

    def P_passing(rig, side="L"):
        """side = stance leg"""
        o = "R" if side == "L" else "L"; sg = 1 if side == "L" else -1
        rot_world(rig, "spine", (0, 1, 0), -5 * sg)            # swing-side hip drops (feminine sway)
        pb = rig.pose.bones["spine"]; M = pb.matrix.copy(); M.translation.x += sg * 0.012 * H; pb.matrix = M
        rot_world(rig, "spine.002", (0, 1, 0), 3 * sg); rot_world(rig, "spine.003", (0, 1, 0), 2 * sg)
        aim(rig, f"thigh.{side}", Vector((-sg * 0.04, 0.02, -1)))
        aim(rig, f"shin.{side}", Vector((0, 0.03, -1)))
        aim(rig, f"foot.{side}", rotv(Vector((sg * 0.1, -1, 0)), (1, 0, 0), 0)); aim(rig, f"toe.{side}", Vector((sg * 0.1, -1, 0)))
        aim(rig, f"thigh.{o}", rotv(Vector((-sg * 0.02, 0, -1)), (1, 0, 0), -24))
        aim(rig, f"shin.{o}", rotv(Vector((0, 0, -1)), (1, 0, 0), 30))
        aim(rig, f"foot.{o}", rotv(Vector((0, -1, 0)), (1, 0, 0), 22))
        rot_world(rig, f"forearm.L", (1, 0, 0), -8); rot_world(rig, f"forearm.R", (1, 0, 0), -8)

    def P_arms_up(rig):
        for s, sg in (("L", 1), ("R", -1)):
            if f"upper_arm.{s}" not in rig.pose.bones: continue
            rot_world(rig, f"shoulder.{s}", (0, 1, 0), -18 * sg)
            aim(rig, f"upper_arm.{s}", Vector((sg * math.sin(math.radians(120)), -0.05, -math.cos(math.radians(120)))))
            aim(rig, f"forearm.{s}", bone_dir(rig, f"upper_arm.{s}")); aim(rig, f"hand.{s}", bone_dir(rig, f"upper_arm.{s}"))

    def P_squat(rig):
        rot_world(rig, "spine", (1, 0, 0), 18)
        for nm, a in (("spine.001", 8), ("spine.002", 8), ("spine.003", 4)): rot_world(rig, nm, (1, 0, 0), a)
        for nm in ("spine.004", "spine.005"): rot_world(rig, nm, (1, 0, 0), -10)
        aim(rig, "spine.006", Vector((0, -0.1, 1)))
        for s, sg in (("L", 1), ("R", -1)):
            aim(rig, f"thigh.{s}", Vector((sg * 0.30, -1.0, 0.12)))
            aim(rig, f"shin.{s}", Vector((sg * 0.06, 0.45, -1.0)))
            aim(rig, f"foot.{s}", Vector((sg * 0.18, -1, rest_dir(rig, f"foot.{s}").z)))
            aim(rig, f"toe.{s}", Vector((sg * 0.18, -1, 0)))
            if f"upper_arm.{s}" in rig.pose.bones:
                aim(rig, f"upper_arm.{s}", Vector((sg * 0.25, -1, -0.15)))
                aim(rig, f"forearm.{s}", Vector((-sg * 0.15, -0.35, 1.0)))     # elbow ~90 deg
                aim(rig, f"hand.{s}", bone_dir(rig, f"forearm.{s}"))

    def P_twist(rig):
        for nm in ("spine.001", "spine.002", "spine.003"): rot_world(rig, nm, (0, 0, 1), 10)

    def P_head(rig):
        rot_world(rig, "spine.004", (0, 0, 1), 10); rot_world(rig, "spine.005", (0, 0, 1), 10); rot_world(rig, "spine.006", (0, 0, 1), 20)

    def P_forearm_twist(rig):
        for s, sg in (("L", 1), ("R", -1)):
            if f"hand.{s}" not in rig.pose.bones: continue
            rot_world(rig, f"hand.{s}", tuple(bone_dir(rig, f"hand.{s}")), 90 * sg)

    TESTS = [("rest", None, []), ("walk_contact", P_contact, ["knee", "elbow"]), ("walk_passing", P_passing, ["knee"]),
             ("arms_up_120", P_arms_up, ["shoulder", "elbow"]), ("deep_squat", P_squat, ["knee", "elbow", "hip"]),
             ("twist_30", P_twist, ["waist"]), ("head_turn_40", P_head, ["neck"]), ("wrist_twist_90", P_forearm_twist, ["wrist"])]

    def joint_spheres(rig, kinds):
        out = {}
        for k in kinds:
            for s in ("L", "R"):
                if k == "knee": nm, r = f"shin.{s}", LM["legs"][s]["r_kn"]
                elif k == "hip": nm, r = f"thigh.{s}", LM["legs"][s]["r_th"]
                elif k == "elbow":
                    if LM["arms"][s] is None: continue
                    nm, r = f"forearm.{s}", LM["arms"][s]["r_el"]
                elif k == "shoulder":
                    if LM["arms"][s] is None: continue
                    nm, r = f"upper_arm.{s}", LM["arms"][s]["r_up"]
                elif k == "wrist":
                    if LM["arms"][s] is None: continue
                    nm, r = f"hand.{s}", 0.8 * LM["arms"][s]["r_el"]
                elif k == "waist":
                    if s == "R": continue
                    nm, r = "spine.002", LM["chest_hw"]
                elif k == "neck":
                    if s == "R": continue
                    nm, r = "spine.005", LM["neck_r"] * 1.2
                if nm not in rig.pose.bones: continue
                out[f"{k}.{s}" if k not in ("waist", "neck") else k] = (nm, max(r, 0.01 * H) * 1.5)
        return out

    def local_volume(bvh, c, r, n=12):
        g1 = np.linspace(-r, r, 2 * n + 1)
        X, Y, Z = np.meshgrid(g1, g1, g1, indexing="ij")
        P = np.c_[X.ravel(), Y.ravel(), Z.ravel()]
        P = P[(P ** 2).sum(1) <= r * r] + c
        inside = 0
        for p in P:
            loc, nrm, fi, d = bvh.find_nearest(Vector(p))
            if loc is not None and (Vector(p) - loc).dot(nrm) < 0: inside += 1
        return inside

    def isect_faces(co, tri):
        bvh = BVHTree.FromPolygons([tuple(v) for v in co], [tuple(t) for t in tri], all_triangles=True)
        pairs = bvh.overlap(bvh)
        bad = set()
        for a, b in pairs:
            if a == b: continue
            if set(tri[a]) & set(tri[b]): continue
            bad.add(a); bad.add(b)
        return bad

    def set_flag_colours(ob, flags_face):
        """corner colour attribute 'flag' = clay, overwritten for flagged faces"""
        me = ob.data
        nl = len(me.loops)
        ca = me.color_attributes.get("flag") or me.color_attributes.new("flag", "BYTE_COLOR", "CORNER")
        col = np.tile(np.array([0.78, 0.76, 0.72, 1.0], np.float32), (nl, 1))
        lst = np.empty(len(me.polygons), np.int32); me.polygons.foreach_get("loop_start", lst)
        for fi, c in flags_face.items():
            col[lst[fi]:lst[fi] + 3] = c
        ca.data.foreach_set("color", col.ravel())
        me.color_attributes.active_color = ca
        me.color_attributes.render_color_index = me.color_attributes.find("flag")

    def eval_tests(rig, ob, names, W, do_render, label_, mode="lbs"):
        write_weights(ob, rig, names, W)
        set_deform(ob, mode)
        bpy.context.view_layer.update()
        co_r, tri = mesh_np(ob.data)
        area_r = tri_area(co_r, tri); vol_r = signed_volume(co_r, tri)
        comp, nc = components(len(co_r), tri)
        bvh_r = BVHTree.FromPolygons([tuple(v) for v in co_r], [tuple(t) for t in tri], all_triangles=True)
        base_isect = isect_faces(co_r, tri)
        results = []
        rest_vol_cache = {}
        for name, fn, kinds in TESTS:
            reset_pose(rig)
            if fn is not None:
                fn(rig); ground(rig, ob)
            bpy.context.view_layer.update()
            me = eval_mesh(ob); co_p, _ = mesh_np(me); bpy.data.meshes.remove(me)
            area_p = tri_area(co_p, tri)
            ratio = area_p / np.maximum(area_r, 1e-12)
            collapsed = np.nonzero(ratio < 0.3)[0]; stretched = np.nonzero(ratio > 2.5)[0]
            isect = isect_faces(co_p, tri) - base_isect
            vol = signed_volume(co_p, tri) / vol_r
            jv = {}
            if kinds:
                bvh_p = BVHTree.FromPolygons([tuple(v) for v in co_p], [tuple(t) for t in tri], all_triangles=True)
                for jn, (bn, r) in joint_spheres(rig, kinds).items():
                    c_rest = np.array(rig.data.bones[bn].head_local); c_pose = np.array(rig.pose.bones[bn].head)
                    if (jn, r) not in rest_vol_cache: rest_vol_cache[(jn, r)] = local_volume(bvh_r, c_rest, r)
                    v0 = rest_vol_cache[(jn, r)]; v1 = local_volume(bvh_p, c_pose, r)
                    jv[jn] = v1 / max(v0, 1)
            det = 0
            if nc > 1:
                for c in range(nc):
                    m = comp == c
                    if m.sum() < 30: continue
                    d_r = np.linalg.norm(co_r[m].mean(0) - co_r[~m].mean(0)); d_p = np.linalg.norm(co_p[m].mean(0) - co_p[~m].mean(0))
                    if abs(d_p - d_r) > 0.05 * H and fn is not None: det += 1
            flags = []
            if len(collapsed) > 0.002 * len(tri): flags.append("collapse")
            twist_j = [k for k in jv if k.startswith(("waist", "neck", "wrist"))]
            if any(jv[k] < 0.85 for k in twist_j): flags.append("candy-wrapper")
            if any(jv[k] < 0.80 for k in jv if k not in twist_j): flags.append("joint-volume")
            if len(isect) > 0.004 * len(tri): flags.append("intersect")
            if len(stretched) > 0.004 * len(tri): flags.append("stretch")
            if det: flags.append("detached")
            m = {"collapsed": int(len(collapsed)), "stretched": int(len(stretched)), "isect_new": int(len(isect)),
                 "vol_ratio": round(float(vol), 4), "joint_vol": {k: round(float(v), 3) for k, v in jv.items()}}
            results.append({"name": name, "metrics": m, "flags": flags})
            if do_render:
                fc = {}
                for f in stretched: fc[int(f)] = (1.0, 0.55, 0.1, 1)
                for f in collapsed: fc[int(f)] = (0.9, 0.1, 0.1, 1)
                for f in isect: fc[int(f)] = (0.85, 0.1, 0.85, 1)
                set_flag_colours(ob, fc)
                render(name, ob)
        reset_pose(rig)
        return results

    def score(res):
        s = 0.0
        for r in res:
            m = r["metrics"]
            s += m["collapsed"] + 0.5 * m["stretched"] + 0.3 * m["isect_new"]
            s += 4000 * sum(max(0, 0.95 - v) + max(0, v - 1.08) for v in m["joint_vol"].values())
            s += 20000 * max(0, abs(m["vol_ratio"] - 1) - 0.02)
        return s

    sk = {"info": sk_info, "candidates": {}}
    modes = ["lbs", "dqs", "lbs+cs", "dqs+cs"] if A.deform == "auto" else [A.deform]
    combos = [(w, m) for w in Wd for m in modes]
    if len(combos) > 1:
        for w, m in combos:
            res = eval_tests(rig, body, names, Wd[w], False, w, m)
            sk["candidates"][f"{w}/{m}"] = {"score": round(score(res), 1), "flags": sum(len(r["flags"]) for r in res),
                                            "squat_knee": res[4]["metrics"]["joint_vol"].get("knee.L"),
                                            "squat_elbow": res[4]["metrics"]["joint_vol"].get("elbow.L"),
                                            "wrist_twist": res[7]["metrics"]["joint_vol"].get("wrist.L")}
            print("[autorig] cand", w, m, sk["candidates"][f"{w}/{m}"], flush=True)
        best, best_mode = min(combos, key=lambda c: sk["candidates"][f"{c[0]}/{c[1]}"]["score"])
    else:
        best, best_mode = combos[0]
    sk["deform"] = best_mode
    sk["method"] = best
    REP["skin"] = sk
    tick("skin-select")
    write_weights(body, rig, names, Wd[best]); set_deform(body, best_mode)
    if not A.no_tests:
        # colour reference render
        ca = body.data.color_attributes.get("Col")
        if ca is not None:
            body.data.color_attributes.render_color_index = body.data.color_attributes.find("Col")
            body.data.color_attributes.active_color = ca
            render("color", body)
        REP["tests"] = eval_tests(rig, body, names, Wd[best], True, best, best_mode)
        tick("pose-tests")

    # ---------------- 11. actions: tests + walk keys ----------------
    def key_pose(rig, frame):
        for pb in rig.pose.bones:
            pb.keyframe_insert("location", frame=frame); pb.keyframe_insert("rotation_quaternion", frame=frame)

    rig.animation_data_create()
    act = bpy.data.actions.new("tests"); rig.animation_data.action = act
    for i, (name, fn, _) in enumerate(TESTS):
        reset_pose(rig)
        if fn: fn(rig); ground(rig, body)
        key_pose(rig, i + 1)
        mk = scene.timeline_markers.new(name, frame=i + 1)
    act.use_fake_user = True
    walk = bpy.data.actions.new("walk_keys"); rig.animation_data.action = walk
    for f, fn, side in ((1, P_contact, "L"), (5, P_passing, "R"), (9, P_contact, "R"), (13, P_passing, "L"), (17, P_contact, "L")):
        reset_pose(rig); fn(rig, side); ground(rig, body); key_pose(rig, f)
    walk.use_fake_user = True
    reset_pose(rig)
    rig.animation_data.action = None
    scene.frame_start, scene.frame_end = 1, 17
    tick("actions")

    # ---------------- 12. optional Rigify generate ----------------
    if A.rigify and RIGIFY:
        try:
            for o in scene.objects: o.select_set(False)
            rig.select_set(True); bpy.context.view_layer.objects.active = rig
            bpy.ops.pose.rigify_generate()
            REP["rigify"] = "generated: " + ", ".join(o.name for o in scene.objects if o.type == "ARMATURE")
        except Exception as e:
            REP["rigify"] = f"failed: {e}"
            note(f"rigify generate failed: {e}")

    # ---------------- 13. final orientation + save ----------------
    if A.facing == "+Y":
        for o in (rig, body):
            o.matrix_world = Matrix.Rotation(math.pi, 4, "Z") @ o.matrix_world
        for o in scene.objects: o.select_set(False)
        body.parent = None
        bpy.context.view_layer.update()
        rig.select_set(True); body.select_set(True); bpy.context.view_layer.objects.active = rig
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
        body.parent = rig; body.matrix_parent_inverse.identity()
    cam.hide_render = True
    body.data.color_attributes.render_color_index = max(0, body.data.color_attributes.find("Col"))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(A.out, A.stem + ".blend"))
    try:
        bpy.ops.export_scene.gltf(filepath=os.path.join(A.out, A.stem + ".glb"), export_format="GLB",
                                  use_selection=False, export_animations=True, export_animation_mode="ACTIONS")
    except Exception as e:
        note(f"glb export failed: {e}")
    tick("save")
    REP["total_s"] = round(sum(REP["timings"].values()), 1)
    json.dump(REP, open(os.path.join(A.out, "report.json"), "w"), indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))
    print("[autorig] OK", A.out)


if __name__ == "__main__":
    if "--" in sys.argv and "bpy" in sys.modules or any("Blender" in a for a in sys.argv[:1]):
        pass
    try:
        import bpy  # noqa
        IN_BLENDER = True
    except ImportError:
        IN_BLENDER = False
    if IN_BLENDER:
        argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
        blender_main(argv)
    else:
        driver(sys.argv[1:])
