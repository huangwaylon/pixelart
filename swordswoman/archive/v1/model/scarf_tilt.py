"""Round 8 (AD 'idle / walk ribbons hang'): screen-space check of the two scarf ribbons in the
idle / walk Actions (and pose_idle_<D>) from the iso camera.  Per ribbon: on-screen length
(H), tilt of the root->tip vector off vertical (deg), tip height vs the sleeve-cuff line.
Run: Blender -b --factory-startup -P model/scarf_tilt.py [-- --dirs SE,SW]"""
import bpy, sys, os, math, json
from mathutils import Vector as V, Matrix
HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
DIRS = ["S", "SE", "E", "NE", "N", "NW", "W", "SW"]
want = argv[argv.index("--dirs") + 1].split(",") if "--dirs" in argv else DIRS
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, "character.blend"))
rig = bpy.data.objects["rig"]
sc = bpy.context.scene
el = math.radians(30)


def scr(yaw, p):
    w = Matrix.Rotation(math.radians(yaw), 3, "Z") @ p
    return V((w.x, w.y * math.sin(el) + w.z * math.cos(el)))


out = {}
worst = 0.0
for d in want:
    yaw = DIRS.index(d) * 45.0
    for base in ("pose_idle", "anim_idle", "anim_walk"):
        an = f"{base}_{d}"
        if an not in bpy.data.actions:
            continue
        act = bpy.data.actions[an]
        rig.animation_data.action = act
        f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
        frames = [1] if base == "pose_idle" else list(range(f0, f1))
        rows = []
        for f in frames:
            sc.frame_set(f)
            bpy.context.view_layer.update()
            cuff = min(rig.pose.bones[f"sleeve.{s}"].tail.z for s in ("L", "R"))
            r = {}
            for side in ("L", "R"):
                root = rig.pose.bones[f"scarf.{side}.001"].head
                tip = rig.pose.bones[f"scarf.{side}.005"].tail
                a, b = scr(yaw, root), scr(yaw, tip)
                v = b - a
                tilt = math.degrees(math.atan2(abs(v.x), -v.y)) if v.length > 1e-6 else 0
                L = sum((rig.pose.bones[f"scarf.{side}.{i:03d}"].tail - rig.pose.bones[f"scarf.{side}.{i:03d}"].head).length
                        for i in range(1, 6))
                r[side] = dict(tilt=round(tilt, 1), len3d=round(L, 2), tip_x=round(b.x, 3), tip_below_cuff=bool(tip.z < cuff + 0.05))
                worst = max(worst, tilt)
            rows.append(r)
        out[an] = rows
        tl = [x[s]["tilt"] for x in rows for s in "LR"]
        sway = max(x["L"]["tip_x"] for x in rows) - min(x["L"]["tip_x"] for x in rows)
        print(f"[scarf] {an}: tilt {min(tl):.0f}-{max(tl):.0f} deg, len {rows[0]['L']['len3d']} H, "
              f"L tip sway {sway * 128 / 7.3:.1f} px, below cuff {[x[s]['tip_below_cuff'] for x in rows[:1] for s in 'LR']}")
print(f"[scarf] worst tilt {worst:.1f} deg")
if "--detail" in argv:
    for an, rows in out.items():
        print(an, [(r["L"]["tilt"], r["R"]["tilt"]) for r in rows])
