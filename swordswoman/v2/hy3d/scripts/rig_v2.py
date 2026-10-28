# Blender -b --factory-startup -P rig.py -- REST_MAT.glb SKEL.txt KEYS.json OUT_DIR [actions,comma|all] [dirs=SE,E]
# Rig ONE rest mesh (simple humanoid armature, auto weights + overrides: head rigid, skirt on 8 radial bones auto-driven by the knees),
# separate katana parented to hand.R, pose keys from keys.json, render iso 30deg ortho guides: fNN_matid.png (flat IDs) + fNN_shade.png (toon).
# glb frame Y-up faces +Z  ->  Blender Z-up faces -Y, her right = -X. Height normalised to 2, feet at 0.
import bpy, sys, os, json, math, mathutils
import numpy as np
from mathutils import Vector, Matrix, Euler
a = sys.argv[sys.argv.index("--") + 1:]
src, skp, keyp, outd = a[:4]
acts = a[4] if len(a) > 4 else "all"; dirs = (a[5] if len(a) > 5 else "SE,E").split(",")
CELL, SC, PIV = 96, 4, (48, 88)         # 1x cell, upscale, feet pivot (1x px) -> 384 px renders
ABD = 12.0
PPU = 26.0                              # 1x px per unit (char height 2 -> ~48 px at 30deg)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
body = [o for o in bpy.context.scene.objects if o.type == "MESH"][0]
body.data.transform(body.matrix_world); body.parent = None; body.matrix_world = Matrix.Identity(4)
for o in list(bpy.context.scene.objects):
    if o != body: bpy.data.objects.remove(o)
me = body.data
if me.color_attributes: me.color_attributes[0].name = "Color"
V = np.array([v.co[:] for v in me.vertices])
# leg centres measured on the mesh (glb y=-0.7 == blender z=-0.7 before normalisation)
sl = V[np.abs(V[:, 2] + 0.7) < 0.01]
LC = [np.r_[sl[sl[:, 0] * g > 0][:, :2].min(0) + sl[sl[:, 0] * g > 0][:, :2].max(0)] / 2 for g in (-1, 1)]
zlo, H = V[:, 2].min(), V[:, 2].max() - V[:, 2].min(); S = 2.0 / H
cx, cy = (LC[0][0] + LC[1][0]) / 2, (LC[0][1] + LC[1][1]) / 2
T = Matrix.Scale(S, 4) @ Matrix.Translation(Vector((-cx, -cy, -zlo)))
me.transform(T); V = np.array([v.co[:] for v in me.vertices])
def P(p):  # glb skeleton point -> normalised blender
    return T @ Vector((p[0], -p[2], p[1]))
sk = np.loadtxt(skp)
legx = {"R": LC[0][0], "L": LC[1][0]}
def gz(y): return (y - zlo) * S  # glb height -> normalised z
# ---------------- armature
arm = bpy.data.armatures.new("rig"); ao = bpy.data.objects.new("rig", arm); bpy.context.scene.collection.objects.link(ao)
bpy.context.view_layer.objects.active = ao; bpy.ops.object.mode_set(mode="EDIT")
E = arm.edit_bones
def bone(name, h, t, parent=None, deform=True):
    b = E.new(name); b.head = h; b.tail = t; b.use_deform = deform
    if parent: b.parent = E[parent]
    return b
def row(i): return P(sk[i, :3]), P(sk[i, 3:])
bone("root", Vector((0, 0, 0)), Vector((0, 0.3, 0)), deform=False)
pel = P(sk[0, :3]); bone("hips", pel, pel + Vector((0, 0, -0.15)), "root")
bone("spine", *row(0), "hips"); bone("chest", *row(1), "spine"); bone("neck", *row(2), "chest"); bone("head", *row(3), "neck")
for s, (ia, ie, iw) in (("R", (7, 8, 9)), ("L", (26, 27, 28))):
    bone(f"upper_arm.{s}", *row(ia), "chest"); bone(f"forearm.{s}", *row(ie), f"upper_arm.{s}")
    h, t = row(iw); bone(f"hand.{s}", h, h + 2.2 * (t - h), f"forearm.{s}")
for s, (it, ik, ia) in (("R", (45, 46, 47)), ("L", (48, 49, 50))):
    def lx(v): v = v.copy(); v.x = (legx[s] - cx) * S; return v
    h, t = row(it); bone(f"thigh.{s}", lx(h), lx(t), "hips")
    h2, t2 = row(ik); bone(f"shin.{s}", lx(t), lx(t2), f"thigh.{s}")
    h3, t3 = row(ia); bone(f"foot.{s}", lx(t2), lx(t3), f"shin.{s}")
for b in E: b.use_connect = False
# skirt: 8 radial bones from the obi bottom to the hem
zw, zh = gz(-0.245), gz(-0.505); NSK = 8; SK = []
for i in range(NSK):
    ph = 2 * math.pi * i / NSK; d = np.array([math.sin(ph), -math.cos(ph)])  # i=0 front (-Y)
    def rad(z):
        m = np.abs(V[:, 2] - z) < 0.02; q = V[m][:, :2]; pr = q @ d; perp = np.abs(q @ np.array([-d[1], d[0]]))
        q = pr[(perp < 0.08) & (pr > 0)]; return float(q.max()) if len(q) else 0.3
    rw, rh = rad(zw) * 0.8, rad(zh + 0.03)
    n = f"skirt.{i}"; bone(n, Vector((d[0] * rw, d[1] * rw, zw)), Vector((d[0] * rh, d[1] * rh, zh)), "hips"); SK.append((n, d))
bpy.ops.object.mode_set(mode="OBJECT")
# ---------------- weights
body.select_set(True); ao.select_set(True); bpy.context.view_layer.objects.active = ao
bpy.ops.object.parent_set(type="ARMATURE_AUTO")
VG = {g.name: g for g in body.vertex_groups}
for n, _ in SK:
    if n not in VG: VG[n] = body.vertex_groups.new(name=n)
gi = {g.index: g.name for g in body.vertex_groups}
W = np.zeros((len(V), len(gi)))
for v in me.vertices:
    for g in v.groups: W[v.index, g.group] = g.weight
nm = {n: i for i, n in gi.items()}
nohw = (W.sum(1) == 0).sum(); print("verts without auto weights:", nohw)
zneck = gz(0.115); zc = V[:, 2]
legd = np.minimum.reduce([np.hypot(V[:, 0] - (legx[s] - cx) * S, V[:, 1] - 0) for s in "RL"])
head = zc > zneck
W[head] = 0; W[head, nm["head"]] = 1
def segd(Pt, h, t):
    h = np.array(h[:]); t = np.array(t[:]); d = t - h; u = np.clip((Pt - h) @ d / (d @ d), 0, 1); return np.linalg.norm(Pt - (h + u[:, None] * d), axis=1)
armv = np.zeros(len(V), bool)
for sd in "RL":
    bn = [f"upper_arm.{sd}", f"forearm.{sd}", f"hand.{sd}"]
    D = np.stack([segd(V, arm.bones[b].head_local, arm.bones[b].tail_local) for b in bn], 1)
    m = (D.min(1) < 0.15) & (np.abs(V[:, 0]) > 0.22) & (zc < gz(0.0)) & (np.sign(V[:, 0]) == (-1 if sd == "R" else 1))
    w = 1 / np.maximum(D[m], 0.01) ** 4; w /= w.sum(1, keepdims=True)
    W[m] = 0
    for j, b in enumerate(bn): W[m, nm[b]] = w[:, j]
    armv |= m
print("arm verts", int(armv.sum()))
skirt = (zc < gz(-0.2)) & (zc > zh - 0.03) & ~((legd < 0.085 * S) & (zc < zh + 0.01)) & ~armv
ang = np.arctan2(V[:, 0], -V[:, 1]) % (2 * math.pi); f = ang / (2 * math.pi / NSK); i0 = np.floor(f).astype(int) % NSK; fr = f - np.floor(f)
t = np.clip((gz(-0.2) - zc) / (gz(-0.2) - zh), 0, 1) ** 1.3
W[skirt] = 0
W[skirt, nm["hips"]] = 1 - t[skirt]
for k in range(NSK):
    m0 = skirt & (i0 == k); m1 = skirt & ((i0 + 1) % NSK == k)
    W[m0, nm[f"skirt.{k}"]] += t[m0] * (1 - fr[m0]); W[m1, nm[f"skirt.{k}"]] += t[m1] * fr[m1]
# legs below hem: thighs/shins only (auto weights sometimes leak skirt/hips)
bad = (W.sum(1) == 0); W[bad, nm["hips"]] = 1
W /= W.sum(1, keepdims=True)
for g in body.vertex_groups: g.remove(list(range(len(V))))
for gidx, name in gi.items():
    g = body.vertex_groups[name]; col = W[:, gidx]; nz = np.nonzero(col > 1e-3)[0]
    for vi in nz: g.add([int(vi)], float(col[vi]), "REPLACE")
# ---------------- katana (separate object, parented to hand.R)
def box(name, size, loc, rgb):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    ca = o.data.color_attributes.new("Color", "BYTE_COLOR", "POINT")
    lin = [((c / 255) / 12.92 if c / 255 <= 0.04045 else (((c / 255) + 0.055) / 1.055) ** 2.4) for c in rgb]
    for d in ca.data: d.color_srgb = (rgb[0] / 255, rgb[1] / 255, rgb[2] / 255, 1)
    return o
pb_hand = arm.bones["hand.R"]; fist = (pb_hand.head_local + pb_hand.tail_local) / 2
hilt = box("hilt", (0.05, 0.24, 0.05), fist + Vector((0, 0.02, 0)), (0x24, 0x1c, 0x28))
blade = box("blade", (0.022, 0.80, 0.045), fist + Vector((0, -0.10 - 0.40, 0)), (0xc8, 0xd0, 0xdc))
kat = [hilt, blade]
for o in kat:
    o.parent = ao; o.parent_type = "BONE"; o.parent_bone = "hand.R"
    o.matrix_parent_inverse = (ao.matrix_world @ Matrix.Translation(pb_hand.tail_local) @ pb_hand.matrix_local.to_3x3().to_4x4()).inverted()
bpy.context.view_layer.update()
# ---------------- materials (toon pass)
def toon_mat(name, outline=False):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; L = nt.links
    for n in list(N): N.remove(n)
    o = N.new("ShaderNodeOutputMaterial")
    if outline:
        e = N.new("ShaderNodeEmission"); e.inputs[0].default_value = (0.012, 0.008, 0.01, 1); L.new(e.outputs[0], o.inputs[0])
        m.use_backface_culling = True; return m
    at = N.new("ShaderNodeAttribute"); at.attribute_name = "Color"
    df = N.new("ShaderNodeBsdfDiffuse"); df.inputs[0].default_value = (1, 1, 1, 1)
    s2r = N.new("ShaderNodeShaderToRGB"); L.new(df.outputs[0], s2r.inputs[0])
    bw = N.new("ShaderNodeRGBToBW"); L.new(s2r.outputs[0], bw.inputs[0])
    cr = N.new("ShaderNodeValToRGB"); cr.color_ramp.interpolation = "CONSTANT"
    el = cr.color_ramp.elements; el[0].position = 0.0; el[0].color = (0.42, 0.42, 0.46, 1); el[1].position = 0.18; el[1].color = (0.72, 0.72, 0.74, 1)
    e3 = el.new(0.55); e3.color = (1, 1, 1, 1)
    L.new(bw.outputs[0], cr.inputs[0])
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs[0].default_value = 1
    ci = [i for i in mx.inputs if i.type == 'RGBA']; co = [o for o in mx.outputs if o.type == 'RGBA'][0]
    L.new(at.outputs[0], ci[0]); L.new(cr.outputs[0], ci[1])
    em = N.new("ShaderNodeEmission"); L.new(co, em.inputs[0]); L.new(em.outputs[0], o.inputs[0]); return m
TM, OM = toon_mat("toon"), toon_mat("outline", True)
for o in [body] + kat:
    o.data.materials.clear(); o.data.materials.append(TM); o.data.materials.append(OM)
    so = o.modifiers.new("outline", "SOLIDIFY"); so.thickness = 0.014 if o == body else 0.008; so.offset = 1; so.use_flip_normals = True
    so.material_offset = 1; so.show_render = False
# ---------------- scene / camera
sc = bpy.context.scene
sc.render.resolution_x = sc.render.resolution_y = CELL * SC; sc.render.film_transparent = True
sc.view_settings.view_transform = "Standard"
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = "ORTHO"; cam.data.ortho_scale = CELL / PPU
cam.data.shift_x = 0.5 - PIV[0] / CELL; cam.data.shift_y = (PIV[1] / CELL) - 0.5
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun); sun.data.energy = 3.0
world = bpy.data.worlds.new("w"); sc.world = world; world.color = (0, 0, 0)
AZ = {"SE": (-1, -1), "E": (-1, 0), "S": (0, -1), "SW": (1, -1)}
def set_view(dn):
    c = Vector((*AZ[dn], 0)).normalized(); el = math.radians(30)
    loc = Vector((c.x * math.cos(el), c.y * math.cos(el), math.sin(el))) * 10
    cam.location = loc; cam.rotation_euler = (-loc).to_track_quat("-Z", "Y").to_euler()
    right = (-loc).normalized().cross(Vector((0, 0, 1))).normalized()
    ld = (-right * 0.7 + Vector((0, 0, 1)) * 0.9 + c * 0.6).normalized()  # light from screen upper-left, toward camera
    sun.rotation_euler = (-ld).to_track_quat("-Z", "Y").to_euler()
# ---------------- posing
keys = json.load(open(keyp)); pbs = ao.pose.bones
for p in pbs: p.rotation_mode = "QUATERNION"
rest_knee = {s: arm.bones[f"shin.{s}"].head_local.copy() for s in "RL"}
def pose(kd):
    ao.location = (0, 0, 0)
    for p in pbs: p.rotation_quaternion = (1, 0, 0, 0); p.location = (0, 0, 0)
    kd = dict(kd)
    for s_ in ("upper_arm.R", "upper_arm.L"): kd.setdefault(s_, [0, 0, 0])
    q = kd.get("sq", 0.0); ao.scale = (1 + q / 2, 1 + q / 2, 1 - q)
    for bn, e in kd.items():
        if bn in ("lift", "fwd", "katana", "sq"): continue
        if bn.startswith("upper_arm"): e = [e[0], e[1] + (ABD if bn.endswith(".R") else -ABD), e[2]]
        R = arm.bones[bn].matrix_local.to_3x3(); Q = Euler([math.radians(x) for x in e], "XYZ").to_matrix()
        pbs[bn].rotation_quaternion = (R.inverted() @ Q @ R).to_quaternion()
    bpy.context.view_layer.update()
    # skirt follows the knees (in hips space) + a little flare in the air
    Mh = pbs["hips"].matrix; Rh = arm.bones["hips"].matrix_local
    flare = 0.10 if kd.get("lift", 0) > 0.05 else 0.0
    for n, d in SK:
        push = 0.0
        for s in "RL":
            kp = Mh.inverted() @ pbs[f"shin.{s}"].head; kr = Rh.inverted() @ rest_knee[s]
            dl = Rh.to_3x3() @ (kp - kr); push += max(0.0, dl.x * d[0] + dl.y * d[1])
        b = arm.bones[n]; L = (b.tail_local - b.head_local).length
        th = min(math.radians(75), math.atan2(push * 1.15, L) + flare)
        k = Vector((d[1], -d[0], 0)); R = b.matrix_local.to_3x3(); Q = Matrix.Rotation(th, 3, k)
        pbs[n].rotation_quaternion = (R.inverted() @ Q @ R).to_quaternion()
    for o in kat: o.hide_render = not kd.get("katana", 0)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(dg)
    zmin = min((ev.matrix_world @ v.co).z for v in ev.data.vertices)
    pbs["root"].location = (0, 0, 0)
    ao.location = (0, -kd.get("fwd", 0.0), -zmin + kd.get("lift", 0.0))
    bpy.context.view_layer.update()
def render(path, mode):
    if mode == "matid":
        sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "FLAT"; sh.color_type = "VERTEX"
        sh.show_object_outline = False; sh.show_cavity = False; sc.display.render_aa = "OFF"
        for o in [body] + kat: o.modifiers["outline"].show_render = False
    else:
        sc.render.engine = "BLENDER_EEVEE"; sc.eevee.taa_render_samples = 8
        for o in [body] + kat: o.modifiers["outline"].show_render = True
    sc.render.filepath = path; bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(outd, "..", "rig", "rig.blend"))
order = list(keys) if acts == "all" else acts.split(",")
for act in order:
    if act.startswith("_"): continue
    for dn in dirs:
        od = os.path.join(outd, f"{act}_{dn}"); os.makedirs(od, exist_ok=True); set_view(dn); names = []
        for fi, (kn, kd) in enumerate(keys[act].items()):
            pose(kd); names.append(kn)
            for mode in ("matid", "shade"): render(os.path.join(od, f"f{fi:02d}_{mode}.png"), mode)
        json.dump({"action": act, "dir": dn, "keys": names, "cell_1x": CELL, "scale": SC, "pivot_1x": PIV, "px_per_unit_1x": PPU,
                   "elev_deg": 30, "ids": ["skin", "hair", "dress", "obi", "boots", "eyes", "bow", "blade", "hilt"]},
                  open(os.path.join(od, "keys.json"), "w"), indent=1)
        print("DONE", act, dn, names, flush=True)
