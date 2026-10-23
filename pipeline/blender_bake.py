"""r19 experiment: bake sprite source passes from the Blender character (model B round 2).

Run inside Blender (headless):
    blender -b /tmp/indep/B/out/model.blend -P pipeline/blender_bake.py -- --out work/r19 --mode true --clip idle

Per (clip frame, direction) it writes <out>/<mode>_<clip>/<dir>_<frame>.npz with, at ss x the 48x64 sprite grid:
    role   (uint8)  colour role id (index into ROLES + 1, 0 = empty)
    part   (uint8)  body-part group id (index into PARTS + 1): dominant deform bone of each face
    depth  (f32)    camera Z depth in metres
    normal (f32x3)  world-space shading normal (Blender axes)
    shade  (f32)    diffuse direct light from the pipeline key-light direction (hard sun, cast shadows on)
    alpha  (f32)
plus meta.json (ppu, camera, light, per-frame eye/mouth/head positions for the face cels).

Camera = pipeline.render.Camera: orthographic, elevation 16 deg, screen-fixed key light
(-0.55 right + 0.68 up + 0.48 to_cam); the character is yawed (DIRECTION_YAW), the camera never moves.
Coordinates: pipeline (x right, y up, z toward the S camera) == Blender (x, -y, z)... i.e. p = (bx, bz, -by).
"""
import json
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

ELEV = 16.0
W, H = 48, 64
PIVOT = (24, 57)
CROWN_PX = 33.5            # S4_hd idle S: hair crown at row 24 -> 57.5 - 24 px above the ground
DIRS = {"S": 0, "SE": 45, "E": 90, "NE": 135, "N": 180, "NW": 225, "W": 270, "SW": 315}

# Blender material -> (pipeline material, forced tone: None | "hi" | "lo")
ROLE_OF = {
    "Skin": ("skin", None), "Hair": ("hair", None), "HairHighlight": ("hair", "hi"),
    "Coat": ("coat", None), "Rust": ("coat_trim", None), "Belt": ("coat_trim", "lo"), "Gold": ("coat_trim", "lo"),
    "Fur": ("boot_cuff", None), "Boots": ("boots", None), "Sole": ("boots", "lo"), "Tights": ("pants", None),
    "TealKnit": ("scarf", None), "TealDark": ("mitten", "lo"), "TealSatin": ("ribbon", None),
}
OBJ_ROLE = {("Mittens", "TealKnit"): ("mitten", None)}
ROLES = sorted({v for v in ROLE_OF.values()} | set(OBJ_ROLE.values()), key=lambda r: (r[0], str(r[1])))
PARTS = ["head", "pony", "hat", "torso", "arm_L", "arm_R", "leg_L", "leg_R", "scarf", "scarf_front"]
HIDE = ["Eyes", "FaceLines", "Brows"]      # modelled face detail: at 48x64 the designed face cels replace it


def bone_part(name):
    for k, v in (("ponytail", "pony"), ("bowtail", "hat"), ("scarf_tail", "scarf_front"), ("sidelock", "head"),
                 ("head", "head"), ("neck", "head")):
        if name.startswith(k):
            return v
    side = "L" if name.endswith(".L") else "R" if name.endswith(".R") else None
    if side and name.split(".")[0] in ("upper_arm", "forearm", "hand"):
        return "arm_" + side
    if side and name.split(".")[0] in ("thigh", "shin", "foot", "toe"):
        return "leg_" + side
    return "torso"


OBJ_PART = {"Bow": "hat", "Hair_Ponytail": "pony", "Scarf": None, "Head": "head", "Hair_Cap": "head",
            "Hair_Bangs": "head", "Hair_SideLocks": "head", "Hair_Back": "head", "Hair_Strands": "head",
            "Hair_Highlight": "head"}


def args():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    o = {"out": "work/r19", "mode": "true", "clip": "idle", "ss": 12, "dirs": ",".join(DIRS),
         "head": "2.8", "thigh": "0.7", "sidelock": "25", "tag": ""}
    for i in range(0, len(a), 2):
        o[a[i].lstrip("-")] = a[i + 1]
    o["ss"] = int(o["ss"])
    return o


def pipe_cam():
    e = math.radians(ELEV)
    right = Vector((1, 0, 0))
    up = Vector((0, math.cos(e), -math.sin(e)))
    to_cam = Vector((0, math.sin(e), math.cos(e)))
    light = (-0.55 * right + 0.68 * up + 0.48 * to_cam).normalized()
    return right, up, to_cam, light


def p2b(v):
    """pipeline vector -> Blender vector."""
    return Vector((v[0], -v[2], v[1]))


def tag_parts():
    """Face attribute 'part' = body-part group of each polygon's dominant deform bone (inner lines at part breaks)."""
    for ob in bpy.data.objects:
        if ob.type != "MESH" or ob.name not in bpy.context.view_layer.objects:
            continue
        me = ob.data
        fixed = OBJ_PART.get(ob.name)
        names = {vg.index: vg.name for vg in ob.vertex_groups}
        vpart = []
        for v in me.vertices:
            acc = {}
            for g in v.groups:
                if g.group in names:
                    p = bone_part(names[g.group])
                    acc[p] = acc.get(p, 0.0) + g.weight
            vpart.append(acc)
        if "part" in me.attributes:
            me.attributes.remove(me.attributes["part"])
        at = me.attributes.new("part", "FLOAT", "FACE")
        vals = []
        for poly in me.polygons:
            if fixed:
                p = fixed
            else:
                acc = {}
                for vi in poly.vertices:
                    for k, w in vpart[vi].items():
                        acc[k] = acc.get(k, 0.0) + w
                p = max(acc, key=acc.get) if acc else "torso"
                if ob.name == "Scarf" and p == "torso":
                    p = "scarf"
            vals.append(PARTS.index(p) + 1)
        at.data.foreach_set("value", vals)


def node_mat(name, build):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(build(nt), out.inputs["Surface"])
    return m


def id_mat(role_id):
    def build(nt):
        attr = nt.nodes.new("ShaderNodeAttribute")
        attr.attribute_name = "part"
        cam = nt.nodes.new("ShaderNodeCameraData")
        xyz = nt.nodes.new("ShaderNodeCombineXYZ")
        xyz.inputs[0].default_value = float(role_id)
        nt.links.new(attr.outputs["Fac"], xyz.inputs[1])
        nt.links.new(cam.outputs["View Z Depth"], xyz.inputs[2])
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Strength"].default_value = 1.0
        nt.links.new(xyz.outputs[0], em.inputs["Color"])
        return em.outputs[0]
    return node_mat(f"r19_id_{role_id}", build)


def normal_mat():
    def build(nt):
        g = nt.nodes.new("ShaderNodeNewGeometry")
        a = nt.nodes.new("ShaderNodeVectorMath")
        a.operation = "MULTIPLY_ADD"
        a.inputs[1].default_value = (0.5, 0.5, 0.5)
        a.inputs[2].default_value = (0.5, 0.5, 0.5)
        nt.links.new(g.outputs["Normal"], a.inputs[0])
        em = nt.nodes.new("ShaderNodeEmission")
        nt.links.new(a.outputs[0], em.inputs["Color"])
        return em.outputs[0]
    return node_mat("r19_normal", build)


def diffuse_mat():
    def build(nt):
        d = nt.nodes.new("ShaderNodeBsdfDiffuse")
        d.inputs["Color"].default_value = (1, 1, 1, 1)
        return d.outputs[0]
    return node_mat("r19_diffuse", build)


def setup_scene(ss):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    cy = sc.cycles
    cy.device = "CPU"
    cy.samples = 1
    cy.use_adaptive_sampling = False
    cy.use_denoising = False
    cy.max_bounces = 0
    for k in ("diffuse_bounces", "glossy_bounces", "transmission_bounces", "volume_bounces", "transparent_max_bounces"):
        setattr(cy, k, 0)
    cy.filter_width = 0.01
    cy.seed = 0
    sc.render.film_transparent = True
    sc.render.use_persistent_data = False     # persistent data dropped re-posed meshes in some views
    sc.render.resolution_x, sc.render.resolution_y = W * ss, H * ss
    sc.render.resolution_percentage = 100
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    sc.view_settings.exposure = 0.0
    sc.view_settings.gamma = 1.0
    im = sc.render.image_settings
    im.file_format = "OPEN_EXR"
    im.color_mode = "RGBA"
    im.color_depth = "32"
    im.exr_codec = "ZIP"
    if sc.world is None:
        sc.world = bpy.data.worlds.new("r19")
    sc.world.use_nodes = True
    bg = sc.world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Strength"].default_value = 0.0
    for ob in bpy.data.objects:
        if ob.type == "LIGHT":
            ob.hide_render = True
        if ob.name in HIDE:
            ob.hide_render = True
        for md in getattr(ob, "modifiers", []):
            if md.type == "SOLIDIFY" and md.name == "Outline":
                md.show_render = False        # inverted-hull outlines: the pixel pass draws its own line
    return sc


def setup_camera(sc, ppu):
    right, up, to_cam, light = pipe_cam()
    cd = bpy.data.cameras.new("r19_cam")
    cd.type = "ORTHO"
    cd.sensor_fit = "VERTICAL"
    cd.ortho_scale = H / ppu
    cd.clip_start, cd.clip_end = 0.1, 40.0
    cam = bpy.data.objects.new("r19_cam", cd)
    sc.collection.objects.link(cam)
    fwd_b, up_b = p2b(-to_cam), p2b(up)
    # frame centre (24, 32) vs pivot (24, 57.5): the world origin sits 25.5 px below the centre
    cam.location = up_b * ((PIVOT[1] + 0.5 - H / 2) / ppu) - fwd_b * 10.0
    rot = Matrix((p2b(right), up_b, -fwd_b)).transposed()       # columns: cam X, cam Y, cam Z (= -view)
    cam.rotation_euler = rot.to_euler()
    sc.camera = cam
    ld = bpy.data.lights.new("r19_key", "SUN")
    ld.energy = 1.0
    ld.angle = 0.0
    sun = bpy.data.objects.new("r19_key", ld)
    sc.collection.objects.link(sun)
    sun.rotation_euler = p2b(light).to_track_quat("Z", "Y").to_euler()   # sun shines along its -Z
    sun.hide_render = True
    return cam, sun, light


def rot_bone(pb, axis_world, deg):
    """Rotate a pose bone about a WORLD-space axis (given in rest orientation, relative to its parent's pose)."""
    ax = pb.bone.matrix_local.to_3x3().inverted() @ Vector(axis_world)
    pb.rotation_mode = "QUATERNION"
    pb.rotation_quaternion = Quaternion(ax.normalized(), math.radians(deg)) @ pb.rotation_quaternion


def reset_pose(rig):
    for pb in rig.pose.bones:
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = Quaternion()
        pb.location = (0, 0, 0)
        pb.scale = (1, 1, 1)


CHIBI = {"head": 2.8, "thigh": 0.7, "sidelock": 25.0}


def head_weights(zmin=1.30):
    """chibi only: above the chin line the face blends head/neck weights, so a scaled head bone would grow the hair
    but not the face. Move neck weight to head there (face and hair scale together)."""
    for ob in bpy.data.objects:
        if ob.type != "MESH" or not (ob.name == "Head" or ob.name.startswith("Hair")):
            continue
        vh, vn = ob.vertex_groups.get("head"), ob.vertex_groups.get("neck")
        if vh is None or vn is None:
            continue
        for v in ob.data.vertices:
            if v.co.z < zmin:
                continue
            w = {g.group: g.weight for g in v.groups}
            if vn.index in w and w[vn.index] > 0:
                vh.add([v.index], w.get(vh.index, 0.0) + w[vn.index], "REPLACE")
                vn.remove([v.index])


def pose(rig, mode, clip, i, n):
    """Relaxed idle (S4_hd idle f0: arms down, slight elbow bend) or an 8-frame walk keyed on the rig."""
    reset_pose(rig)
    P = rig.pose.bones
    if mode == "chibi":
        # sprite proportion retarget: bigger head (hair/bow chains inherit), shorter thighs (shins keep size)
        hs = CHIBI["head"]
        P["head"].scale = (hs, hs, hs)
        for s, sg in (("L", 1), ("R", -1)):
            P[f"thigh.{s}"].scale = (1, CHIBI["thigh"], 1)
            rig.data.bones[f"shin.{s}"].inherit_scale = "NONE"
            if CHIBI["sidelock"]:
                # swing the side locks back/out off the cheeks so the (small) face reads in 3/4 and profile
                rot_bone(P[f"sidelock.{s}.01"], (1, 0, 0), CHIBI["sidelock"])
                rot_bone(P[f"sidelock.{s}.01"], (0, 1, 0), -0.4 * CHIBI["sidelock"] * sg)
    for s, sg in (("L", 1), ("R", -1)):
        rot_bone(P[f"upper_arm.{s}"], (0, 1, 0), 16 * sg)      # A-pose 24 deg -> ~8 deg off the body
        rot_bone(P[f"forearm.{s}"], (1, 0, 0), -12)            # slight bend, hands forward
    if clip == "walk":
        ph = 2 * math.pi * i / n
        for s, off in (("L", 0.0), ("R", math.pi)):
            a = ph + off
            rot_bone(P[f"thigh.{s}"], (1, 0, 0), -24 * math.sin(a))
            rot_bone(P[f"shin.{s}"], (1, 0, 0), 6 + 32 * max(0.0, math.cos(a)))
            rot_bone(P[f"foot.{s}"], (1, 0, 0), -10 * max(0.0, math.cos(a)))
            rot_bone(P[f"upper_arm.{s}"], (1, 0, 0), 16 * math.sin(a))   # opposite to the same-side leg
            rot_bone(P[f"forearm.{s}"], (1, 0, 0), -8 * max(0.0, math.sin(a)))
        rot_bone(P["hips"], (0, 0, 1), 5 * math.sin(ph))
        rot_bone(P["chest"], (0, 0, 1), -7 * math.sin(ph))
        rot_bone(P["ponytail.01"], (1, 0, 0), 6 * math.cos(2 * ph))
    bpy.context.view_layer.update()


def eval_verts(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    M = np.array(ev.matrix_world)
    co = co @ M[:3, :3].T + M[:3, 3]
    return ev, me, co


def mat_centroid(obname, matname):
    ob = bpy.data.objects[obname]
    ev, me, co = eval_verts(ob)
    slots = [s.material.name if s.material else None for s in ob.material_slots]
    vs = set()
    for p in me.polygons:
        if slots[p.material_index] == matname:
            vs.update(p.vertices)
    c = co[sorted(vs)].mean(axis=0) if vs else None
    ev.to_mesh_clear()
    return None if c is None else [float(v) for v in c]


def ground(rig):
    """Keep the lowest sole on Z=0 (planted foot) after the pose changes leg lengths."""
    rig.location.z = 0.0
    bpy.context.view_layer.update()
    ev, me, co = eval_verts(bpy.data.objects["Boots"])
    ev.to_mesh_clear()
    rig.location.z = -float(co[:, 2].min())
    bpy.context.view_layer.update()


def face_info(rig):
    hb = rig.matrix_world @ rig.pose.bones["head"].matrix
    return {"eye_L": mat_centroid("Eyes", "Eye_L"), "eye_R": mat_centroid("Eyes", "Eye_R"),
            "mouth": mat_centroid("FaceLines", "Mouth"),
            "head_head": list(hb.translation), "head_y": list(hb.to_3x3().col[1].normalized())}


def read_exr(path):
    img = bpy.data.images.load(path, check_existing=False)
    img.colorspace_settings.name = "Non-Color"
    w, h = img.size
    buf = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(buf)
    bpy.data.images.remove(img)
    return buf.reshape(h, w, 4)[::-1]          # top row first


def render_pass(sc, path):
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return read_exr(path)


ORIG = {}      # (object, slot) -> original material name


def assign(objs, fn):
    """Swap every material slot (object-level link) via fn(ob, original material name)."""
    for ob in objs:
        for k, s in enumerate(ob.material_slots):
            s.link = "OBJECT"
            s.material = fn(ob, ORIG[(ob.name, k)])


def main():
    o = args()
    ss = o["ss"]
    for k in CHIBI:
        CHIBI[k] = float(o[k])
    out = os.path.join(o["out"], f"{o['mode']}{o['tag']}_{o['clip']}")
    os.makedirs(out, exist_ok=True)
    sc = setup_scene(ss)
    rig = bpy.data.objects["Rig"]
    meshes = [ob for ob in bpy.data.objects if ob.type == "MESH" and not ob.hide_render]
    for ob in meshes:
        for k, s in enumerate(ob.material_slots):
            ORIG[(ob.name, k)] = s.material.name if s.material else ""
    tag_parts()
    if o["mode"] == "chibi":
        head_weights()
    role_mats = {r: id_mat(k + 1) for k, r in enumerate(ROLES)}
    nmat, dmat = normal_mat(), diffuse_mat()

    def role_of(ob, name):
        return OBJ_ROLE.get((ob.name, name)) or ROLE_OF.get(name, ("coat", None))

    n = 8 if o["clip"] == "walk" else 1
    # scale: hair crown of the idle S pose at CROWN_PX above the ground (S4_hd idle f0)
    pose(rig, o["mode"], "idle", 0, 1)
    ground(rig)
    ev, me, co = eval_verts(bpy.data.objects["Hair_Cap"])
    ev.to_mesh_clear()
    crown = float(co[:, 2].max())
    ppu = CROWN_PX / crown
    cam, sun, light = setup_camera(sc, ppu)
    meta = {"mode": o["mode"], "chibi": dict(CHIBI) if o["mode"] == "chibi" else None, "clip": o["clip"], "ss": ss, "ppu_m": ppu, "crown_m": crown, "elevation": ELEV,
            "pivot": PIVOT, "size": [W, H], "roles": ROLES, "parts": PARTS, "cam_dist": 10.0,
            "light_pipeline": list(light), "frames": {}}
    dirs = o["dirs"].split(",")
    tmp = os.path.join(out, "_exr")
    os.makedirs(tmp, exist_ok=True)
    for i in range(n):
        pose(rig, o["mode"], o["clip"], i, n)
        for d in dirs:
            rig.rotation_euler = (0, 0, math.radians(DIRS[d]))
            ground(rig)
            meta["frames"][f"{d}_{i}"] = face_info(rig)
            assign(meshes, lambda ob, nm: role_mats[role_of(ob, nm)])
            a = render_pass(sc, os.path.join(tmp, "id.exr"))
            assign(meshes, lambda ob, nm: nmat)
            b = render_pass(sc, os.path.join(tmp, "nrm.exr"))
            assign(meshes, lambda ob, nm: dmat)
            sun.hide_render = False
            c = render_pass(sc, os.path.join(tmp, "shade.exr"))
            sun.hide_render = True
            np.savez_compressed(os.path.join(out, f"{d}_{i}.npz"),
                                role=np.rint(a[..., 0]).astype(np.uint8), part=np.rint(a[..., 1]).astype(np.uint8),
                                depth=a[..., 2].astype(np.float32), alpha=a[..., 3].astype(np.float32),
                                normal=(b[..., :3] * 2 - 1).astype(np.float32), shade=c[..., 0].astype(np.float32))
            print(f"r19 bake {o['mode']} {o['clip']} {d} f{i}", flush=True)
    rig.rotation_euler = (0, 0, 0)
    with open(os.path.join(out, "meta.json"), "w") as f:
        json.dump(meta, f, indent=1)
    if o.get("save_blend"):
        bpy.ops.wm.save_as_mainfile(filepath=o["save_blend"], copy=True)


main()
