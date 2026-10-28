"""Proportion record + silhouette overlays for the guide rig.
  .venv/bin/python tools/hybrid/guide_measure.py
Needs (render_guides / measure_rig outputs):
  hybrid/guide/measure/{guide,r9}_{front,side}/.../f00_mask.png, r9_iso/SE, p3d_iso/<DIR>, p3d_{front,side}
  hybrid/guide/turn/SE/f00_{mask,id}.png, hybrid/guide/measure/{guide_landmarks,r9_landmarks_rest}.json
Writes hybrid/guide/measure/proportions.json and overlay_*.png (red = concept only, blue = guide only)."""
import json
import os
import subprocess

import numpy as np
from PIL import Image, ImageDraw

ROOT = "/Users/waylonhuang/Documents/other/pixelart/swordswoman"
M = os.path.join(ROOT, "hybrid", "guide", "measure")
PY = os.path.join(ROOT, ".venv", "bin", "python")
SIL = os.path.join(ROOT, "tools", "hybrid", "sil_compare.py")

# ---- concept landmarks, hand-measured (original pixel rows / cols)
CONCEPT = {
    "turnaround_v6_front": {"file": "concept/chibi_turnaround_v6.png", "bow_top": 205, "crown": 270, "brow": 423,
                            "eye_c": 447, "chin": 499, "corset_top": 597, "corset_bot": 673, "crotch": 727,
                            "front_hem": 773, "tail_bottom": 847, "sole": 860, "hair_w": 260, "bow_w": 179,
                            "collar_w": 227, "eye_h": 30, "eye_w": 45, "cx": 223},
    "turnaround_v6_side": {"file": "concept/chibi_turnaround_v6.png", "crown": 272, "eye_c": 447, "chin": 493,
                           "sole": 860, "head_depth": 220, "bun_c": 268, "cx": 517},
    "iso_v5_SE": {"file": "concept/chibi_iso_v5.png", "bow_top": 130, "crown": 228, "brow": 440, "eye_c": 468,
                  "chin": 522, "collar_bot": 600, "corset_top": 655, "corset_bot": 745, "front_hem": 835, "sole": 950,
                  "hair_w": 335, "sword_proj": 393, "cx": 497},
}


def concept_ratios(c):
    H = c["chin"] - c["crown"]
    r = {"H_px": H, "crown_sole_H": round((c["sole"] - c["crown"]) / H, 3), "chin_sole_H": round((c["sole"] - c["chin"]) / H, 3),
         "eye_above_chin_H": round((c["chin"] - c["eye_c"]) / H, 3)}
    for k in ("brow",):
        if k in c:
            r["brow_above_chin_H"] = round((c["chin"] - c[k]) / H, 3)
    if "bow_top" in c:
        r["bow_top_above_crown_H"] = round((c["crown"] - c["bow_top"]) / H, 3)
    if "crotch" in c:
        r["legs_crotch_sole_H"] = round((c["sole"] - c["crotch"]) / H, 3)
    if "corset_top" in c:
        r["corset_band_H"] = round((c["corset_bot"] - c["corset_top"]) / H, 3)
    if "tail_bottom" in c:
        r["skirt_tail_above_sole_H"] = round((c["sole"] - c["tail_bottom"]) / H, 3)
        r["front_hem_above_sole_H"] = round((c["sole"] - c["front_hem"]) / H, 3)
    for k in ("hair_w", "bow_w", "collar_w", "eye_h", "eye_w", "head_depth", "sword_proj"):
        if k in c:
            r[k + "_H"] = round(c[k] / H, 3)
    return r


def model_ratios(L, crown, chin, eye_z, hairw, top=None):
    H = crown - chin
    r = {"H_world": round(H, 4), "crown_z": round(crown, 4), "chin_z": round(chin, 4),
         "crown_sole_H": round(crown / H, 3), "chin_sole_H": round(chin / H, 3),
         "eye_above_chin_H": round((eye_z - chin) / H, 3),
         "bow_top_above_crown_H": round((L["bow"]["max"][2] - crown) / H, 3),
         "bow_w_H": round((L["bow"]["max"][0] - L["bow"]["min"][0]) / H, 3),
         "legs_crotch_sole_H": round(L["shorts"]["min"][2] / H, 3),
         "corset_band_H": round((L["corset"]["max"][2] - L["corset"]["min"][2]) / H, 3),
         "collar_w_H": round((L["collar"]["max"][0] - L["collar"]["min"][0]) / H, 3),
         "hair_w_H": round(hairw / H, 3),
         "head_depth_H": round(((L.get("hair_bob") or L["hair"])["max"][1] - (L["head"]["min"][1])) / H, 3),
         "skirt_tail_above_sole_H": round(L["skirt_outer"]["min"][2] / H, 3),
         "eye_h_H": round((L["fd_M_eye_light"]["max"][2] - L["fd_M_eye_light"]["min"][2]) / H, 3),
         "katana_len_H": round(float(np.linalg.norm(np.array(L["katana"]["max"]) - np.array(L["katana"]["min"]))) / H, 3),
         "bun_center_z_above_crown_H": round(((L["bun"]["max"][2] + L["bun"]["min"][2]) / 2 - crown) / H, 3)}
    return r


G = json.load(open(os.path.join(M, "guide_landmarks.json")))
R9 = json.load(open(os.path.join(M, "r9_landmarks_rest.json")))
meta_lm = json.load(open(os.path.join(ROOT, "hybrid", "guide", "rig_reference.json")))["landmarks"]
g_crown = G["hair_bob"]["max"][2]   # the round-9 cap is hidden in the guide
g_chin = meta_lm["chin"][1][2]
g_eye = meta_lm["eye_L"][1][2]
r9_eye = (R9["fd_M_eye_light"]["max"][2] + R9["fd_M_eye_light"]["min"][2]) / 2
out = {"note": "H = head height crown->chin (excl. bun/bow).  Concept values hand-measured on the art; model values from "
               "rest-pose geometry (tools/hybrid/measure_rig.py).  Width/depth are the hair mass.  iso_v5 values are "
               "projected (30 deg elevation), so vertical ratios there are foreshortened vs the orthos.",
       "concept": {k: concept_ratios(v) for k, v in CONCEPT.items()},
       "round9": model_ratios(R9, R9["hair"]["max"][2], 1.80, r9_eye, R9["hair"]["max"][0] - R9["hair"]["min"][0]),
       "guide": model_ratios(G, g_crown, g_chin, g_eye, G["hair_bob"]["max"][0] - G["hair_bob"]["min"][0]),
       "pixal3d_4view": {"note": "from the earlier front ortho (hybrid/guide/measure/tex_p3d_front.png): taller legs, smaller head",
                         "crown_sole_H": 2.91, "eye_above_chin_H": 0.35, "hair_w_H": 1.04}}


def row(z):
    return 512 - (z - 1.62) * 1024 / 3.9


def sil(args, label, outpng):
    cmd = [PY, SIL] + args + ["--out", outpng, "--label", label]
    r = json.loads(subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT).stdout)
    return {"iou": r["iou"], "top_above_crown_ref": r["top_above_crown_ref"], "top_above_crown_guide": r["top_above_crown_guide"],
            "overlay": os.path.relpath(outpng, ROOT)}


T = "concept/chibi_turnaround_v6.png"
ov = {}
for who, crown, base in (("guide", g_crown, "guide"), ("round9", R9["hair"]["max"][2], "r9")):
    ov[f"{who}_front_vs_turnaround_v6"] = sil(["--ref", T, "--ref-box", "0,150,390,900", "--ref-crown", "270", "--ref-sole", "860",
                                              "--ref-cx", "223", "--ref-mirror", "--mask", f"{M}/{base}_front/front/f00_mask.png",
                                              "--crown", str(row(crown)), "--sole", str(row(0)), "--cx", "512"],
                                             f"{who} front", f"{M}/overlay_{who}_front.png")
    ov[f"{who}_side_vs_turnaround_v6"] = sil(["--ref", T, "--ref-box", "390,150,700,900", "--ref-crown", "272", "--ref-sole", "860",
                                             "--ref-cx", "517", "--mask", f"{M}/{base}_side/side/f00_mask.png",
                                             "--crown", str(row(crown)), "--sole", str(row(0)), "--cx", "512"],
                                            f"{who} side", f"{M}/overlay_{who}_side.png")
iso_dirs = {"guide": os.path.join(ROOT, "hybrid/guide/turn/SE"), "round9": f"{M}/r9_iso/SE"}
for who, d in iso_dirs.items():
    ov[f"{who}_isoSE_vs_iso_v5"] = sil(["--ref", "concept/chibi_iso_v5.png", "--ref-crown", "228", "--ref-sole", "950", "--ref-cx", "497",
                                        "--mask", f"{d}/f00_mask.png", "--id", f"{d}/f00_id.png",
                                        "--legend", os.path.join(ROOT, "hybrid/guide/id_legend.json"), "--auto"],
                                       f"{who} iso SE", f"{M}/overlay_{who}_isoSE.png")
# guide vs Pixal3D (same total height), 8 iso directions
p3 = {}
tiles = []
for d in ["S", "SE", "E", "NE", "N", "NW", "W", "SW"]:
    a = np.array(Image.open(os.path.join(ROOT, f"hybrid/guide/turn/{d}/f00_mask.png")))[..., 3] > 127
    b = np.array(Image.open(f"{M}/p3d_iso/{d}/f00_mask.png"))[..., 3] > 127
    p3[d] = round(float((a & b).sum() / (a | b).sum()), 3)
    im = np.full(a.shape + (3,), 255, np.uint8)
    im[b & ~a] = (230, 60, 60)
    im[a & ~b] = (60, 90, 230)
    im[a & b] = (150, 150, 150)
    t = Image.fromarray(im).crop((262, 280, 762, 900))
    ImageDraw.Draw(t).text((5, 5), f"{d} IoU {p3[d]}  red=Pixal3D blue=guide", fill=(0, 0, 0))
    tiles.append(t.resize((250, 310)))
s = Image.new("RGB", (2000, 310), "white")
for i, t in enumerate(tiles):
    s.paste(t, (250 * i, 0))
s.save(f"{M}/overlay_guide_vs_pixal3d_iso8.png")
ov["guide_vs_pixal3d_iso8_iou"] = p3
out["silhouette_overlays"] = ov
# combined sheet of the concept overlays
names = ["overlay_round9_front", "overlay_guide_front", "overlay_round9_side", "overlay_guide_side",
         "overlay_round9_isoSE", "overlay_guide_isoSE"]
ims = [Image.open(f"{M}/{n}.png").convert("RGB").crop((212, 0, 812, 1000)).resize((300, 500)) for n in names]
sheet = Image.new("RGB", (300 * len(ims), 500), "white")
for i, im in enumerate(ims):
    sheet.paste(im, (300 * i, 0))
sheet.save(f"{M}/overlays_concept.png")
json.dump(out, open(f"{M}/proportions.json", "w"), indent=1)
print(json.dumps(out, indent=1))
