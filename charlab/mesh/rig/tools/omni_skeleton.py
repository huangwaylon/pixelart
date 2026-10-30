"""Write an Omni pose-control skeleton (51 rows, demo bone layout) from an autorig report.

usage: python omni_skeleton.py <autorig out dir> <id> [skeletons dir]
  -> skeletons/<id>_pose.txt   Omni 51x6 (head xyz, tail xyz), same frame + normalisation as R3's
                               omni/scripts/lab_export.py: glb frame (Y up, faces +Z, her left +X),
                               mesh bbox centre at 0, longest extent -> 2*0.98
  -> skeletons/<id>.json       Rigify-named joints (same frame/normalisation) + provenance
The skeleton is the autorig A-pose rest (arms ~40 deg, soft elbows), so a mesh generated with it matches the rig rest.
Finger joints are the Omni demo hand, rotated onto our forearm direction and scaled to our hand length (as lab_export).
"""
import sys, os, json
import numpy as np

DEMO = "/Users/waylonhuang/Documents/other/pixelart/.models/hy_omni/src_omni_mlx/demos/pose"
out_dir, cid = sys.argv[1], sys.argv[2]
sk_dir = sys.argv[3] if len(sys.argv) > 3 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "skeletons")
os.makedirs(sk_dir, exist_ok=True)
R = json.load(open(os.path.join(out_dir, "report.json")))
to_glb = lambda p: np.stack([p[..., 0], p[..., 2], -p[..., 1]], -1)       # internal (Z up, faces -Y) -> glb
B = {n: (to_glb(np.array(b["head"])), to_glb(np.array(b["tail"]))) for n, b in R["bones_rest"].items()}
lo, hi = [to_glb(np.array(x)) for x in R["mesh"]["bbox"]]
lo, hi = np.minimum(lo, hi), np.maximum(lo, hi)
c = (lo + hi) / 2; s = 2 * 0.98 / (hi - lo).max()
N = lambda p: (p - c) * s

demo = json.load(open(f"{DEMO}/a_pose_bone.json")); names = list(demo)
dj = {n: np.array(v[0]) for n, v in demo.items()}
dtxt = np.loadtxt(f"{DEMO}/a_pose_bone.txt")
hc = to_glb(np.array(R["head_c"]))
head_len = np.linalg.norm(B["spine.006"][1] - B["spine.006"][0])
eye_y = B["spine.006"][0][1] + 0.38 * head_len
newj = {"Upper Body": B["spine"][0], "Lower Body": B["spine"][0] - [0, 0.02, 0], "Upper Body 2": B["spine.003"][0],
        "Neck": B["spine.004"][0], "Head": B["spine.006"][0],
        "Eye.R": np.array([hc[0] - 0.16 * head_len, eye_y, hc[2] + 0.42 * head_len]),
        "Eye.L": np.array([hc[0] + 0.16 * head_len, eye_y, hc[2] + 0.42 * head_len])}
FTs = {}
for side in ("R", "L"):
    newj[f"Shoulder.{side}"] = B[f"shoulder.{side}"][0]; newj[f"Arm.{side}"] = B[f"upper_arm.{side}"][0]
    newj[f"Elbow.{side}"] = B[f"forearm.{side}"][0]; newj[f"Wrist.{side}"] = B[f"hand.{side}"][0]
    newj[f"Foot.{side}"] = B[f"thigh.{side}"][0]; newj[f"Knee.{side}"] = B[f"shin.{side}"][0]; newj[f"Ankle.{side}"] = B[f"foot.{side}"][0]
    dw, de = dj[f"Wrist.{side}"], dj[f"Elbow.{side}"]; ow, oe = newj[f"Wrist.{side}"], newj[f"Elbow.{side}"]
    hand_len = np.linalg.norm(B[f"hand.{side}"][1] - B[f"hand.{side}"][0])
    a, b = (dw - de) / np.linalg.norm(dw - de), (ow - oe) / np.linalg.norm(ow - oe)
    v = np.cross(a, b); cth = a @ b; K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    Rm = np.eye(3) + K + K @ K / (1 + cth)
    fscale = hand_len / np.linalg.norm(dj[f"Middle3.{side}"] - dw)
    FTs[side] = (lambda dw, ow, Rm, fscale: (lambda p: ow + Rm @ (p - dw) * fscale))(dw, ow, Rm, fscale)
    for n in names:
        if n.endswith("." + side) and n.startswith(("Thumb", "Index", "Middle", "Ring", "Pinky")):
            newj[n] = FTs[side](dj[n])
assert set(newj) == set(names), set(names) - set(newj)
Q = np.zeros_like(dtxt)
for i, row in enumerate(dtxt):
    n0 = names[i]
    Q[i, :3] = N(newj[n0])
    p = row[3:]; n1 = min(names, key=lambda m: np.linalg.norm(dj[m] - p))
    if np.linalg.norm(dj[n1] - p) < 5e-3:
        Q[i, 3:] = N(newj[n1])
    elif n0 == "Head":
        Q[i, 3:] = N(B["spine.006"][1])
    elif n0.startswith("Ankle"):
        Q[i, 3:] = N(B["toe." + n0[-1]][1])
    elif n0[-2:] in (".R", ".L") and n0.startswith(("Wrist", "Thumb", "Index", "Middle", "Ring", "Pinky")):
        Q[i, 3:] = N(FTs[n0[-1]](p))
    else:
        Q[i, 3:] = Q[i, :3] + (p - dj[n0])
np.savetxt(os.path.join(sk_dir, f"{cid}_pose.txt"), Q)
json.dump({"id": cid, "source": R["input"], "frame": "glb: Y up, faces +Z, her left +X; mesh bbox centre 0, longest extent 1.96",
           "arm_angle_deg": R["args"]["arm_angle"], "omni_rows": names,
           "bones": {n: {"head": np.round(N(h), 5).tolist(), "tail": np.round(N(t), 5).tolist(), "parent": R["bones_rest"][n]["parent"]}
                     for n, (h, t) in B.items()}},
          open(os.path.join(sk_dir, f"{cid}.json"), "w"), indent=1)
print("wrote", os.path.join(sk_dir, f"{cid}_pose.txt"), Q.shape)
