# pv.py CLIP F0 F1 STEP TAG [VIEW] [blade=carry|grip|two] [ref=0|zero] : quick rig preview strip of a clip segment (evenly sampled, no locks)
import sys, os, json, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import actions as AC, retarget as RT
clip, f0, f1, st, tag = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
view = sys.argv[6] if len(sys.argv) > 6 else "SE"; bm = sys.argv[7] if len(sys.argv) > 7 else "carry"; ref = sys.argv[8] if len(sys.argv) > 8 else "0"
ref = "zero" if ref == "zero" else int(ref)
c = AC.P(clip, ref=ref, yaw_frames=range(f0, f1))
opt = {"blade": bm}
if bm == "grip":
    g, sp = RT.grip_axis(c, range(0, c["_T"])); print("grip axis", g, "consistency", round(sp, 3)); opt["grip"] = g
keys = [dict(name=str(t), t=t, ms=100) for t in range(f0, f1, st)][:16]
fr = []
for k in keys: fr.append({"name": k["name"], "ms": 100})
ps, _ = RT.build(c, keys, view, dict(AC.CAM, **opt))
for f, p in zip(fr, ps): f[view] = p
W = {"pv": {"loop": False, "frames": fr}}
jp = os.path.join(AC.ROOT, "tmp", "pv_act.json"); json.dump(W, open(jp, "w"))
env = dict(os.environ, ACT_JSON=jp)
subprocess.run([os.path.join(os.path.dirname(os.path.dirname(AC.ROOT)), ".venv/bin/python"), "-I", os.path.join(HERE, "pt.py"), "render", "pv", view, "tmp/pv_" + tag], env=env, cwd=AC.ROOT, capture_output=True)
from PIL import Image
im = Image.open(os.path.join(AC.ROOT, "tmp", "pv_" + tag, "pv_" + view, "ones4.png")); h = im.height // 2; im = im.crop((0, h, im.width, im.height))
n = len(keys); per = im.width // n; rows = [im.crop((i * per, 0, min(im.width, (i + 8) * per), h)) for i in range(0, n, 8)]
C = Image.new("RGB", (8 * per, h * len(rows)), (110, 110, 110))
for i, r in enumerate(rows): C.paste(r, (0, i * h))
C.thumbnail((800, 800)); C.save(os.path.join(AC.ROOT, "tmp", "pv_" + tag + ".png")); print("saved", C.size, [k["t"] for k in keys])
