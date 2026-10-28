# p_parts.py (P, round 2) -- extra "part ID" pass for the pixel chain, without touching R's renderer.
#   <blender> -b rig/rig.blend -P render/p_parts.py -- motion/<act>.json <view> <outdir> [--yaw=..] [--frames=a:b]
# Builds a per-vertex colour attribute PART = the dominant deform bone (inside the dominant part group leg.L/R, arm.L/R, sleeve.L/R,
# torso, head, skirt), makes it the active/render colour, then runs R's render/render_motion.py with KINDS=guide
# --no-post, so the "guide" pass (Workbench flat vertex colour, AA off, same camera/pose/yaw) becomes the part pass.
# Files are renamed <act>_<view>_fNN_part.png.  When R ships native leg_near/leg_far or L/R IDs this pass can be retired.
import bpy, sys, os, glob, re
argv = sys.argv[sys.argv.index("--") + 1:]
HERE = os.path.dirname(os.path.abspath(__file__))
# encoding: dominant deform bone index i (vertex-group order, written to <outdir>/bones.json) -> colour (4i+2, 253-4i, 37i mod 256)


def part_of(g):
    for s in "LR":
        if g in (f"thigh.{s}", f"shin.{s}", f"foot.{s}", f"toe.{s}"): return "leg." + s
        if g in (f"shoulder.{s}", f"upper_arm.{s}", f"forearm.{s}", f"hand.{s}"): return "arm." + s
        if g.startswith(f"sleeve.{s}"): return "sleeve." + s
    if g.startswith("skirt"): return "skirt"
    if g in ("root", "pelvis", "spine", "chest"): return "torso"
    return "head"  # neck, head, hair*, bun, bow*


body = bpy.data.objects["body"]; me = body.data
import json
names = [g.name for g in body.vertex_groups]
os.makedirs(argv[2], exist_ok=True)
json.dump({"bones": names, "parts": {n: part_of(n) for n in names}}, open(os.path.join(argv[2], "bones.json"), "w"), indent=0)
if me.color_attributes.get("PART"): me.color_attributes.remove(me.color_attributes["PART"])
ca = me.color_attributes.new("PART", "BYTE_COLOR", "CORNER")  # per-face constant (no interpolation between bone codes)
vb = [0] * len(me.vertices)
for v in me.vertices:
    acc = {}
    for e in v.groups:  # dominant bone, but chosen inside the dominant part group (so part = group of the bone)
        acc.setdefault(part_of(names[e.group]), {})[e.group] = e.weight
    if acc:
        pg = max(acc, key=lambda k: sum(acc[k].values())); i = max(acc[pg], key=acc[pg].get)
    else:
        i = names.index("pelvis")
    vb[v.index] = i
for poly in me.polygons:
    vs = [vb[me.loops[l].vertex_index] for l in poly.loop_indices]; i = max(set(vs), key=vs.count)
    c = (4 * i + 2, 253 - 4 * i, (37 * i) % 256)
    for l in poly.loop_indices: ca.data[l].color = (c[0] / 255, c[1] / 255, c[2] / 255, 1)
# second attribute RPOS: rest-pose position (bbox-normalised, 8 bit per axis) -> exact surface correspondence between frames
ra = me.color_attributes.get("RPOS") or me.color_attributes.new("RPOS", "BYTE_COLOR", "POINT")
xs = [v.co for v in me.vertices]; lo = [min(c[k] for c in xs) for k in range(3)]; hi = [max(c[k] for c in xs) for k in range(3)]
lin = lambda u: u / 12.92 if u <= 0.04045 else ((u + 0.055) / 1.055) ** 2.4  # attribute is linear, the 8-bit output is sRGB-encoded
for v in me.vertices:
    ra.data[v.index].color = tuple(lin((v.co[k] - lo[k]) / (hi[k] - lo[k])) for k in range(3)) + (1,)
json.dump({"lo": lo, "hi": hi}, open(os.path.join(argv[2], "rpos.json"), "w"))
os.environ["KINDS"] = "guide"
out = argv[2]
sys.argv = [sys.argv[0], "--"] + argv[:3] + [a for a in argv[3:] if a.startswith("--")] + ["--no-post"]
src = open(os.path.join(HERE, "render_motion.py")).read()
orig = me.color_attributes["Color"]; orig.name = "_P_matid"   # R's guide pass reads the attribute named "Color": swap names in memory
os.environ["KINDS"] = "guide"
for attr, suf in ((ca, "part"), (ra, "rpos")):
    nm = attr.name; attr.name = "Color"; me.color_attributes.active_color = attr
    exec(compile(src, os.path.join(HERE, "render_motion.py"), "exec"), {"__name__": "__main__", "__file__": os.path.join(HERE, "render_motion.py")})
    attr.name = nm
    for f in glob.glob(os.path.join(out, "*_guide.png")):
        os.replace(f, re.sub(r"_guide\.png$", f"_{suf}.png", f))
orig.name = "Color"
print("PARTS_DONE", out, flush=True)
