# mc.py: BVH loader (numpy FK) + canonical joints + stick-figure contact sheets. Run with .venv python -I.
import numpy as np, re, os, json
def _rot(ax, a):
    c, s = np.cos(a), np.sin(a); o, z = np.ones_like(a), np.zeros_like(a)
    if ax == "X": return np.stack([o, z, z, z, c, -s, z, s, c], -1).reshape(*a.shape, 3, 3)
    if ax == "Y": return np.stack([c, z, s, z, o, z, -s, z, c], -1).reshape(*a.shape, 3, 3)
    return np.stack([c, -s, z, s, c, z, z, z, o], -1).reshape(*a.shape, 3, 3)
def load(path, f0=0, f1=None):
    tx = open(path).read(); hdr, mot = tx.split("MOTION")
    names, parents, offs, chans, stack = [], [], [], [], []; end = False
    toks = re.findall(r"\S+", hdr)
    i = 0
    while i < len(toks):
        t = toks[i]
        if t in ("ROOT", "JOINT"):
            names.append(toks[i + 1]); parents.append(stack[-1] if stack else -1); chans.append([]); offs.append([0, 0, 0]); i += 2; continue
        if t == "End":
            names.append(names[stack[-1]] + "_end"); parents.append(stack[-1]); chans.append([]); offs.append([0, 0, 0]); i += 2; continue
        if t == "{": stack.append(len(names) - 1)
        elif t == "}": stack.pop()
        elif t == "OFFSET": offs[-1] = [float(x) for x in toks[i + 1:i + 4]]; i += 4; continue
        elif t == "CHANNELS":
            n = int(toks[i + 1]); chans[-1] = toks[i + 2:i + 2 + n]; i += 2 + n; continue
        i += 1
    ml = mot.strip().split("\n"); nf = int(ml[0].split()[1]); ft = float(ml[1].split()[2])
    f1 = nf if f1 is None else min(f1, nf)
    D = np.array([[float(x) for x in l.split()] for l in ml[2 + f0:2 + f1]])
    T = len(D); J = len(names); P = np.zeros((T, J, 3)); G = np.zeros((T, J, 3, 3)); c0 = 0
    for j in range(J):
        loc = np.tile(np.array(offs[j], float), (T, 1)); R = np.tile(np.eye(3), (T, 1, 1))
        for c in chans[j]:
            v = D[:, c0]; c0 += 1
            if c.endswith("position"): loc[:, "XYZ".index(c[0])] = v if parents[j] >= 0 or True else v
            else: R = R @ _rot(c[0], np.radians(v))
        p = parents[j]
        if p < 0: P[:, j] = loc; G[:, j] = R
        else: P[:, j] = P[:, p] + np.einsum("tij,tj->ti", G[:, p], loc); G[:, j] = G[:, p] @ R
    P0 = np.zeros((1, J, 3)); G0 = np.tile(np.eye(3), (1, J, 1, 1))  # zero-rotation (bind) pose
    for j in range(J):
        p = parents[j]; loc = np.array(offs[j], float)
        if p < 0: P0[0, j] = 0
        else: P0[0, j] = P0[0, p] + loc
    C = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]], float)  # bvh Y-up -> blender Z-up (x, -z, y)
    P = P @ C.T; G = C @ G @ C.T; P0 = P0 @ C.T; G0 = C @ G0 @ C.T
    return {"names": names, "parents": parents, "fps": round(1 / ft), "P": P, "G": G, "P0": P0, "G0": G0, "path": path}
MAPS = {
 "bandai": {"pelvis": "Hips", "spine": "Spine", "chest": "Chest", "neck": "Neck", "head": "Head", "head_end": "Head_end",
            **{f"{k}.{s}": f"{v}_{s}" for s in "RL" for k, v in (("sh", "UpperArm"), ("el", "LowerArm"), ("wr", "Hand"), ("hip", "UpperLeg"), ("kn", "LowerLeg"), ("an", "Foot"), ("toe", "Toes"))},
            "hd.R": "Hand_R_end", "hd.L": "Hand_L_end"},
 "cmu": {"pelvis": "hip", "spine": "abdomen", "chest": "chest", "neck": "neck", "head": "head", "head_end": "special04",
         **{f"{k}.{s}": f"{s.lower()}{v}" for s in "RL" for k, v in (("sh", "shoulder"), ("el", "elbow"), ("wr", "hand"), ("hip", "hip"), ("kn", "knee"), ("an", "foot"))},
         "toe.R": "toe3-1.r", "toe.L": "toe3-1.l", "hd.R": "finger3-1.r", "hd.L": "finger3-1.l"},
 "lafan": {"pelvis": "Hips", "spine": "Spine", "chest": "Spine2", "neck": "Neck", "head": "Head", "head_end": "Head_end",
           **{f"{k}.{s}": f"{n}{v}" for s, n in (("R", "Right"), ("L", "Left")) for k, v in (("sh", "Arm"), ("el", "ForeArm"), ("wr", "Hand"), ("hip", "UpLeg"), ("kn", "Leg"), ("an", "Foot"), ("toe", "Toe"))},
           "hd.R": "RightHand_end", "hd.L": "LeftHand_end"}}
def kind(path):
    return "bandai" if "bandai" in path else "cmu" if "/cmu/" in path else "lafan"
def canon(clip, zero=False):
    if zero: clip = dict(clip, P=clip["P0"], G=clip["G0"])
    M = MAPS[kind(clip["path"])]; ix = {n: i for i, n in enumerate(clip["names"])}
    out = {}
    for k, v in M.items():
        if v in ix: out[k] = clip["P"][:, ix[v]]
    out["G_head"] = clip["G"][:, ix[M["head"]]]; out["G_pelvis"] = clip["G"][:, ix[M["pelvis"]]]; out["G_wr.R"] = clip["G"][:, ix[M["wr.R"]]]; out["G_wr.L"] = clip["G"][:, ix[M["wr.L"]]]
    if "head_end" not in out: out["head_end"] = out["head"] + (out["head"] - out["neck"])
    return out
def leglen(c):
    return float(np.median(np.linalg.norm(c["hip.R"] - c["kn.R"], axis=-1) + np.linalg.norm(c["kn.R"] - c["an.R"], axis=-1)))
BONES = [("pelvis", "spine"), ("spine", "chest"), ("chest", "neck"), ("neck", "head"), ("head", "head_end"), ("chest", "sh.R"), ("sh.R", "el.R"), ("el.R", "wr.R"), ("chest", "sh.L"), ("sh.L", "el.L"), ("el.L", "wr.L"),
         ("pelvis", "hip.R"), ("hip.R", "kn.R"), ("kn.R", "an.R"), ("an.R", "toe.R"), ("pelvis", "hip.L"), ("hip.L", "kn.L"), ("kn.L", "an.L"), ("an.L", "toe.L")]
def sheet(c, frames, path, views=("side", "front"), cell=90, extra=None, labels=None):
    from PIL import Image, ImageDraw
    L = leglen(c); s = cell * 0.42 / L; n = len(frames)
    im = Image.new("RGB", (cell * n, cell * len(views)), (110, 110, 110)); d = ImageDraw.Draw(im)
    for vi, v in enumerate(views):
        for k, t in enumerate(frames):
            pel = c["pelvis"][t]; ox, oy = k * cell + cell / 2, vi * cell + cell * 0.88
            def pr(p):
                q = p - np.array([pel[0], pel[1], 0])
                x = -q[1] if v == "side" else q[0]
                return ox + x * s, oy - q[2] * s
            for a, b in BONES:
                if a in c and b in c:
                    col = (230, 80, 80) if b.endswith(".R") or a.endswith(".R") and b != "sh.R" else (80, 140, 255) if b.endswith(".L") else (20, 20, 20)
                    d.line([pr(c[a][t]), pr(c[b][t])], fill=col, width=2)
            if extra is not None and "blade" in extra:
                p0 = c["wr.R"][t]; d.line([pr(p0), pr(p0 + extra["blade"][t] * L * 0.9)], fill=(250, 250, 250), width=1)
            d.line([(k * cell, oy), (k * cell + cell, oy)], fill=(80, 80, 80))
            d.text((k * cell + 2, vi * cell + 2), str(labels[k] if labels else t), fill=(255, 255, 0))
    im.save(path); return im.size
def info(c, fps):
    L = leglen(c); out = {}
    for s in "RL":
        lo = np.minimum(c["an." + s][:, 2], c.get("toe." + s, c["an." + s])[:, 2])
        out["foot_h." + s] = lo
        v = np.linalg.norm(np.gradient(c["an." + s], axis=0), axis=-1) * fps / L
        out["foot_v." + s] = v
    out["pel_h"] = c["pelvis"][:, 2] / L; out["L"] = L
    return out
