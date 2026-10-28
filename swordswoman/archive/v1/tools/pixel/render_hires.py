"""Hi-res (default 512 px) toon source renders that frame-match the 128 px sprite cells.

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/pixel/render_hires.py -- \
      --anim idle [--dirs S,SE,...] [--frames 0,1,..] [--res 512] [--out pixel/source] [--force]

Opens model/character.blend READ-ONLY (never saved).  Camera / pose logic is copied from
model/render_turnaround.py (cam_iso, apply_action, set_sword/set_outline/set_rim) so that a 512 px
render is exactly the 128 px sprite cell scaled x4 (same ortho_scale, same pivot lift):
  sprite f<k> of anim_<anim>_<DIR> == Action anim_<anim>_<DIR> at frame f0 + k.
Differences vs. the sprite cell (on purpose, this is the "what the artist meant" reference): hero
katana instead of the sprite katana, inverted-hull outline and material rim ON, AA on, SPRITE_DROP
parts (chest cord, tassets, chest flower, hair streaks) hidden like on the sprite.
Writes <out>/<anim>/<DIR>/fNN.png  (NN = 2-digit sprite frame index).
"""
import bpy, sys, os, json, math
from mathutils import Vector as V

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(name, default=None):
    return argv[argv.index(name) + 1] if name in argv else default


ANIM = arg("--anim", "idle")
DIRS = ["S", "SE", "E", "NE", "N", "NW", "W", "SW"]
SEL_DIRS = arg("--dirs", ",".join(DIRS)).split(",")
SEL_FRAMES = arg("--frames")
RES = int(arg("--res", "512"))
OUT = os.path.join(ROOT, arg("--out", "pixel/source"))
FORCE = "--force" in argv
BLEND = os.path.join(ROOT, "model", "character.blend")

bpy.ops.wm.open_mainfile(filepath=BLEND, load_ui=False)
sc = bpy.context.scene
cam = bpy.data.objects["cam"]
rig = bpy.data.objects["rig"]
ISO_ORTHO = float(rig.get("iso_ortho", 6.5))
CELL = 128
PIVOT = (64, 104)
SPRITE_DROP = ("chest_cord", "corset_tabs", "chest_flower", "hair_streaks")
RIM_NODES = [(m, n) for m in bpy.data.materials if m.node_tree for n in m.node_tree.nodes if n.name == "rim_thresh"]


def set_rim(on):
    for m, n in RIM_NODES:
        n.inputs[1].default_value = 0.78 if on else 2.0


def set_outline(px_world):
    for ob in bpy.data.objects:
        m = ob.modifiers.get("Outline") if ob.type == "MESH" else None
        if m:
            m.show_render = px_world > 0
            m.thickness = px_world * ob.get("outline_px", 1.5)


def set_sword(sprite):
    bpy.data.objects["katana"].hide_render = sprite
    for n in ("katana_sprite", "katana_sprite_kagi"):
        if n in bpy.data.objects:
            bpy.data.objects[n].hide_render = not sprite


def apply_action(name, frame=1):
    if rig.animation_data is None:
        rig.animation_data_create()
    rig.animation_data.action = bpy.data.actions[name]
    sc.frame_set(frame)
    bpy.context.view_layer.update()


def cam_iso(direction):
    el = math.radians(30)
    cam.rotation_euler = (math.pi / 2 - el, 0, 0)
    cam.data.ortho_scale = ISO_ORTHO
    cam.data.shift_x = cam.data.shift_y = 0
    fwd = V((0, math.cos(el), -math.sin(el)))
    up = V((0, math.sin(el), math.cos(el)))
    px_per_h = CELL / ISO_ORTHO
    lift = (PIVOT[1] - CELL / 2) / px_per_h
    cam.location = up * lift - fwd * 20
    rig.rotation_euler = (0, 0, math.radians(DIRS.index(direction) * 45.0))


def frames_for(an):
    """Same frame enumeration as render_turnaround.py."""
    act = bpy.data.actions[an]
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    base = an.rsplit("_", 1)[0] if an.rsplit("_", 1)[-1] in DIRS else an
    if base in ("anim_idle", "anim_walk"):
        return list(range(f0, f1))
    cyc = json.loads(rig.get("cycles", "{}")).get(base, {})
    return list(range(f0, f1)) if cyc.get("cyclic", False) else list(range(f0, f1 + 1))


r = sc.render
r.resolution_x = r.resolution_y = RES
r.resolution_percentage = 100
r.filter_size = 1.5
sc.eevee.taa_render_samples = 16
r.film_transparent = True
set_sword(False)
set_rim(True)
set_outline(ISO_ORTHO / RES * 1.1)
for n in SPRITE_DROP:
    if n in bpy.data.objects:
        bpy.data.objects[n].hide_render = True

done = 0
for d in SEL_DIRS:
    an = f"anim_{ANIM}_{d}" if f"anim_{ANIM}_{d}" in bpy.data.actions else f"anim_{ANIM}"
    if an not in bpy.data.actions:
        print(f"[render_hires] no Action for anim_{ANIM} ({d}); skipped")
        continue
    frames = frames_for(an)
    sel = range(len(frames)) if not SEL_FRAMES else [int(v) for v in SEL_FRAMES.split(",")]
    od = os.path.join(OUT, ANIM, d)
    os.makedirs(od, exist_ok=True)
    for k in sel:
        if k >= len(frames):
            continue
        path = os.path.join(od, f"f{k:02d}.png")
        if os.path.exists(path) and not FORCE:
            continue
        apply_action(an, frames[k])
        cam_iso(d)
        r.filepath = path
        bpy.ops.render.render(write_still=True)
        done += 1
        print("[render_hires]", path)
print(f"[render_hires] done: {done} renders")
# NOTE: the .blend is never saved.
