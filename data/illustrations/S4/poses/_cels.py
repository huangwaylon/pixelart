"""Pose face cels (full-body 3/4 scale: far eye 6x9, near eye 8x9, anchor top-left like the model sheet).
    python data/illustrations/S4/poses/_cels.py   -> writes poses/face/*.json"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
EYE = {"K": "ink", "d": "iris_0", "m": "iris_1", "l": "iris_2", "W": "snow_3", "w": "snow_3", "s": "line_skin"}
MOUTH = {"s": "line_skin", "p": "plum_0", "c": "crn_1", "t": "crn_2", "r": "red_2"}
FX = {"o": "snow_0", "b": "snow_1", "W": "snow_3", "y": "gold_2", "g": "gold_1", "K": "outline", "t": "teal_2",
      "r": "red_2"}
C = {
 # --- eyes ---
 "bQ_far_happy": (EYE, ["......", "......", "......", "..KK..", ".K..K.", "K....K"]),
 "bQ_near_happy": (EYE, ["........", "........", "........", "..KKKK..", ".KK..KK.", "K......K"]),
 "bQ_far_wide": (EYE, [".KKKK.", "KwwwwK", "wddwww", "dmmdww", "dlldww", "wddwww", ".wwww.", ".ssss."]),
 "bQ_near_wide": (EYE, [".KKKKKK.", "KwwwwwwK", "wwddwwww", "wdmmdwww", "wdlldwww", "wwddwwww", ".wwwwww.", ".ssssss."]),
 "bQ_far_det": (EYE, ["......", "KK....", "KKKKK.", "KdWWKK", ".dWddw", ".dmmdw", ".dmldw", "..ddd.", ".s...."]),
 "bQ_near_det": (EYE, ["........", "......KK", "...KKKKK", "KKKKKKKK", "wdWWddwK", "wdmmmdw.", "wdmlldw.", ".ddddd..", ".....ss."]),
 "bQ_far_smug": (EYE, ["......", "......", "......", "KKKKKK", ".dWWdw", ".dmldw", ".dlld.", "..ddd.", ".s...."]),
 "bQ_near_smug": (EYE, ["........", "........", "........", "KKKKKKKK", "wdWWddwK", "wdmmldw.", "wdmlldw.", ".ddddd..", ".....ss."]),
 "bQ_far_shy": (EYE, ["......", "......", ".KKKK.", "KKKKKK", "WWdwww", "mmdww.", "lld...", "dd....", ".s...."]),
 "bQ_near_shy": (EYE, ["........", "........", ".KKKKKK.", "KKKKKKKK", "WWddwwwK", "mmldwww.", "llldww..", "ddd.....", ".....ss."]),
 # determined (B's bust determined eye, lid lowered, lashes slanted 1 px down toward the nose), pose scale
 "bQ_far_det2": (EYE, ["......", ".KKK..", "KKKKKK", "KdWWKK", ".dmmdw", ".dmldw", ".dlld.", "..ddd.", ".ss..."]),
 "bQ_near_det2": (EYE, ["........", "...KKKK.", "KKKKKKKK", "KKWWddwK", "wdWdddw.", "wdmmldw.", "wdmlldw.", ".ddddd..", ".....ss."]),
 "bQ_far_squeeze": (EYE, ["......", "......", "K.....", ".KK...", "...KK.", ".KK...", "K....."]),
 "bQ_near_squeeze": (EYE, ["........", "........", "......KK", "....KK..", "..KK....", "....KK..", "......KK"]),
 # --- brows (model-sheet browQ_* geometry: far 4x2, near 7x2; inner ends = far right / near left) ---
 "bQ_brow_far_up": (EYE, [".KKK", "K..."], [0, 1]),
 "bQ_brow_near_up": (EYE, [".KKKKK.", "K.....K"], [0, 1]),
 "bQ_brow_far_det": (EYE, ["KK..", "..KK"]),
 "bQ_brow_near_det": (EYE, ["....KKK", "KKKK..."]),
 "bQ_brow_far_flat": (EYE, ["....", "KKKK"]),
 "bQ_brow_near_flat": (EYE, [".......", ".KKKKKK"]),
 "bQ_brow_far_worry": (EYE, ["..KK", "KK.."]),
 "bQ_brow_near_worry": (EYE, ["KKK....", "...KKKK"]),
 # --- mouths (anchor offset so the mouth stays centred on the model-sheet mouth anchor) ---
 "bQ_mouth_smile": (MOUTH, ["s..s", ".ss."], [1, 0]),
 "bQ_mouth_joy": (MOUTH, ["pppp", "pctp", ".pp."], [1, 0]),
 "bQ_mouth_cheer": (MOUTH, ["ppppp", "pcccp", "pcttp", ".ppp."], [1, 0]),
 "bQ_mouth_o": (dict(MOUTH, c="hair_1"), [".p.", "pcp", ".p."], [0, 0]),
 "bQ_mouth_det": (MOUTH, ["sss", "...s"], [1, 0]),
 "bQ_mouth_smirk": (MOUTH, ["...s", "sss."], [1, 0]),
 "bQ_mouth_wobble": (MOUTH, ["s.s.", ".s.s"], [1, 0]),
 "bQ_nose_cold": ({"r": "red_2"}, ["rr"], [1, 0]),
 "bQ_blush_far_heavy": ({"r": "red_2"}, [".r.r", "r.r."], [1, 0]),
 "bQ_blush_near_heavy": ({"r": "red_2"}, [".r.r.r", "r.r.r."], [1, 0]),
 # --- wave knee (r2 fix 7): leg split extension + back-leg bend highlight ---
 "bQ_knee_split": ({"k": "ink"}, ["k"] * 6),
 "bQ_knee_hi": ({"m": "mauve"}, ["mm"]),
 # --- fx ---
 "bQ_fx_sweat": (FX, [".b.", "bWb", "bWb", ".b."]),
 "bQ_fx_surprise": (FX, ["...K...", "K..K...", ".K.....", "......K", "....KK."]),
 "bQ_fx_sparkle": (FX, ["..y..", ".yyy.", "yyWyy", ".yyy.", "..y.."]),
 "bQ_fx_sparkle_s": (FX, [".y.", "yyy", ".y."]),
 "bQ_fx_shiver": (FX, ["o.", "o.", ".o", ".o", "o.", "o."]),
 "bQ_fx_wave": (FX, ["o..", ".o.", ".o.", "o.."]),
 "bQ_fx_shy": (FX, ["r.r.r"]),
}
if __name__ == "__main__":
    os.makedirs(os.path.join(HERE, "face"), exist_ok=True)
    for n, v in C.items():
        leg, grid = v[0], v[1]
        anc = v[2] if len(v) > 2 else [0, 0]
        used = set("".join(grid)) - {"."}
        json.dump({"note": "S4 pose cel", "anchor": anc, "legend": {k: leg[k] for k in sorted(used)}, "grid": grid},
                  open(os.path.join(HERE, "face", n + ".json"), "w"), indent=1)
    print(len(C), "cels")
