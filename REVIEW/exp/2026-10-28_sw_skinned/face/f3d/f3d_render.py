# f3d_render.py (F, round 5) -- render R's rig with F's face TEXTURES on the 3D head (no projection, no decals), in memory only.
#   <blender> -b rig/rig.blend -P face/f3d/f3d_render.py -- motion/<act>.json|rest <view> <outdir> [--preview] [--frames=a:b] [--expr=<key>]
# 1. UV `face_uv` (planar, head-bone rest frame, f3d_lib box) on the head's front-facing skin polygons; everything else (-1,-1) (CLIP).
# 2. Full mode: R's render_motion.py renders lum + dep (KINDS=lum,dep, no tex); then per frame F renders the `guide` (matid) pass with
#    EEVEE emission = mix(vertex matid colour, face_<key>_mid texture, texture alpha), 1 sample (exact colours, same as R's Workbench guide).
#    Preview mode: R's pv pass with the face_<key>_pv texture mixed into the base colour (smooth shaded like the body).
# 3. Expression switching per frame: key = f3d_lib.face_key(frame.face, frame.blink, frame.mouth) (M's keys), or --expr=<key> for all frames.
import bpy, sys, os, json, math
from mathutils import Vector
argv = sys.argv[sys.argv.index("--") + 1:]
HERE = os.path.dirname(os.path.abspath(__file__)); FACE = os.path.dirname(HERE); EXP = os.path.dirname(FACE)
pos = [x for x in argv if not x.startswith("--")]; flags = [x for x in argv if x.startswith("--")]
MOT, VIEW, OUT = pos[:3]; PREVIEW = "--preview" in flags
EXPR = next((f.split("=", 1)[1] for f in flags if f.startswith("--expr=")), None)
TD = os.environ.get("F3D_TEXDIR", os.path.join(HERE, "tex"))
FT = json.load(open(os.path.join(TD, "face_tex.json"))); X0, X1, Y0, Y1 = FT["box"]
os.makedirs(OUT, exist_ok=True)
ao = bpy.data.objects["rig"]; body = bpy.data.objects["body"]; me = body.data


def face_key(expr, blink=None, mouth=None):   # = f3d_lib.face_key (Blender python has no access to the pixtools libs)
    al = {'joy': 'joyful', 'cheerful': 'smile_open', 'blink_closed': 'blink', 'blink_half': 'half_blink', 'half-blink': 'half_blink',
          'land': 'squint', 'pain': 'hurt', 'dash': 'focused', 'tear': 'hurt_tear', 'tears': 'hurt_tear'}
    k = al.get(expr, expr) if expr else 'neutral'
    if isinstance(blink, (int, float)) and not isinstance(blink, bool): blink = 'closed' if blink >= 0.75 else ('half' if blink >= 0.25 else None)
    return k + (f'+b{blink}' if blink in ('half', 'closed') else '') + (f'+m{mouth}' if mouth in ('open', 'closed') else '')


# ---- 1. face UV (in memory)
B = ao.data.bones["head"].matrix_local; Bi = B.inverted(); B3i = Bi.to_3x3()
gi = body.vertex_groups["head"].index if "head" in body.vertex_groups else None
hw = [0.0] * len(me.vertices)
for v in me.vertices:
    for g in v.groups:
        if g.group == gi: hw[v.index] = g.weight
col = me.color_attributes["Color"]
lin = lambda u: u / 12.92 if u <= 0.04045 else ((u + 0.055) / 1.055) ** 2.4
SKIN = [lin(c / 255) for c in (248, 218, 194)]
if not me.uv_layers.get("face_uv"):   # round 5: no master projection -> drop R's pj_<V> layers in memory (Blender allows 8 UV maps)
    for l in [l for l in me.uv_layers if l.name.startswith("pj_")]: me.uv_layers.remove(l)
uvl = me.uv_layers.get("face_uv") or me.uv_layers.new(name="face_uv")
# F3D_STANDIN=1 (testing only, until R's round-5 head lands): clean the hull's noisy matid labels on the face in memory: the front of the
# head below the agreed fringe line (head-local y < FRINGE_Y) inside the face oval -> skin; above it, in front -> hair (a full fringe to the brows)
STANDIN = os.environ.get("F3D_STANDIN", "0") == "1"; FRINGE_Y = float(os.environ.get("F3D_FRINGE", "0.205"))
if STANDIN:
    HAIR = [lin(c / 255) for c in (61, 50, 53)]
    for p in me.polygons:
        if min(hw[v] for v in p.vertices) <= 0.5: continue
        q = Bi @ p.center; nz = (B3i @ p.normal).z
        if nz < 0.1 or q.z < 0.05: continue
        inside = (q.x / 0.125) ** 2 + ((q.y - 0.085) / 0.125) ** 2 < 1.0
        if not inside: continue
        c = SKIN if q.y < FRINGE_Y - 0.012 * math.cos(q.x * 40) else HAIR   # scalloped fringe edge (clumps)
        for li in p.loop_indices: col.data[li].color = (*c, 1.0)
    print("F3D_STANDIN face cleaned", flush=True)
n_on = 0
for p in me.polygons:
    nz = (B3i @ p.normal).z
    c = col.data[p.loop_indices[0]].color if col.domain == "CORNER" else col.data[p.vertices[0]].color
    skin = all(abs(c[k] - SKIN[k]) < 0.02 for k in range(3))
    on = skin and nz > 0.15 and min(hw[v] for v in p.vertices) > 0.5
    for li in p.loop_indices:
        if on:
            q = Bi @ me.vertices[me.loops[li].vertex_index].co
            uvl.data[li].uv = ((q.x - X0) / (X1 - X0), (q.y - Y0) / (Y1 - Y0))
        else:
            uvl.data[li].uv = (-1.0, -1.0)
    n_on += on
print("FACE_UV polys", n_on, flush=True)
IM = {}


def img(key, kind):
    nm = f"face_{key}_{kind}"
    if nm not in IM:
        p = os.path.join(TD, nm + ".png")
        if not os.path.exists(p): p = os.path.join(TD, f"face_{key.split('+')[0]}_{kind}.png")
        IM[nm] = bpy.data.images.load(p, check_existing=True); IM[nm].colorspace_settings.name = "sRGB"
    return IM[nm]


def mat_guide():
    m = bpy.data.materials.new("f3d_guide"); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    for n in list(N): N.remove(n)
    out = N.new("ShaderNodeOutputMaterial"); em = N.new("ShaderNodeEmission"); at = N.new("ShaderNodeAttribute"); at.attribute_name = "Color"
    uv = N.new("ShaderNodeUVMap"); uv.uv_map = "face_uv"; im = N.new("ShaderNodeTexImage"); im.name = "FACE"; im.interpolation = "Closest"; im.extension = "CLIP"
    mx = N.new("ShaderNodeMixRGB"); L.new(uv.outputs[0], im.inputs[0]); L.new(im.outputs["Alpha"], mx.inputs[0])
    L.new(at.outputs["Color"], mx.inputs[1]); L.new(im.outputs["Color"], mx.inputs[2]); L.new(mx.outputs[0], em.inputs[0]); L.new(em.outputs[0], out.inputs[0])
    return m


def mat_pv():
    m = bpy.data.materials.new("f3d_pv"); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    for n in list(N): N.remove(n)
    out = N.new("ShaderNodeOutputMaterial"); df = N.new("ShaderNodeBsdfPrincipled"); df.inputs["Roughness"].default_value = 0.8
    at = N.new("ShaderNodeAttribute"); at.attribute_name = "PV" if "PV" in me.color_attributes else "Color"
    uv = N.new("ShaderNodeUVMap"); uv.uv_map = "face_uv"; im = N.new("ShaderNodeTexImage"); im.name = "FACE"; im.interpolation = "Linear"; im.extension = "CLIP"
    mx = N.new("ShaderNodeMixRGB"); L.new(uv.outputs[0], im.inputs[0]); L.new(im.outputs["Alpha"], mx.inputs[0])
    L.new(at.outputs["Color"], mx.inputs[1]); L.new(im.outputs["Color"], mx.inputs[2]); L.new(mx.outputs[0], df.inputs["Base Color"]); L.new(df.outputs[0], out.inputs[0])
    return m


MG, MP = mat_guide(), mat_pv()
# ---- 2. R's renderer: lum/dep (full) or nothing (preview, we render pv ourselves), with all its camera / pose / info code
src = open(os.path.join(EXP, "render", "render_motion.py")).read()
os.environ["KINDS"] = "lum,dep" if not PREVIEW else "none"
rargs = [MOT, VIEW, OUT] + (["--preview"] if PREVIEW else []) + [f for f in flags if f.startswith("--frames=")] + ["--no-post"]
G = {"__name__": "__main__", "__file__": os.path.join(EXP, "render", "render_motion.py")}
sys.argv = [sys.argv[0], "--"] + rargs
if PREVIEW:   # R's loop would render the pv pass with its own material: neutralise rpass during the exec, render ourselves after
    src = src.replace('kinds = ["pv"] if PREVIEW else', 'kinds = [] if PREVIEW else')
exec(compile(src, G["__file__"], "exec"), G)
sc, apply, frames, act = G["sc"], G["apply"], G["frames"], G["act"]
stem = os.path.join(OUT, f"{act}_{VIEW}")
idxs = list(range(len(frames)))
fr_flag = next((f.split("=")[1] for f in flags if f.startswith("--frames=")), None)
if fr_flag: a_, b_ = fr_flag.split(":"); idxs = idxs[int(a_ or 0):int(b_) if b_ else None]
keys = {}
body.data.materials.clear(); body.data.materials.append(MP if PREVIEW else MG)
nd = (MP if PREVIEW else MG).node_tree.nodes["FACE"]
for i in idxs:
    fr = frames[i]; apply(fr)
    key = EXPR or face_key(fr.get("face"), fr.get("blink"), fr.get("mouth")); keys[i] = key
    nd.image = img(key, "pv" if PREVIEW else "mid")
    if PREVIEW:
        G["set_mat"] = lambda kind: None   # keep MP on the body
        G["rpass"](f"{stem}_f{i:02d}_pv.png", "pv")
    else:
        sc.render.engine = "BLENDER_EEVEE"; sc.eevee.taa_render_samples = 1; sc.world.color = (0, 0, 0)
        sc.view_settings.view_transform = "Standard"; sc.view_settings.look = "None"; sc.view_settings.exposure = 0; sc.view_settings.gamma = 1
        sc.render.image_settings.color_depth = "8"; sc.render.image_settings.color_mode = "RGBA"; sc.render.film_transparent = True
        sc.render.filter_size = 0.0
        sc.render.filepath = f"{stem}_f{i:02d}_guide.png"; bpy.ops.render.render(write_still=True)
info = json.load(open(stem + ".json")); info["face_keys"] = keys; info["face_tex"] = TD
json.dump(info, open(stem + ".json", "w"), indent=0)
print("F3D_DONE", OUT, len(idxs), flush=True)
