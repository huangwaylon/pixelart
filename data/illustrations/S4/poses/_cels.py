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
 "bQ_far_wide": (EYE, [".KKKK.", "KwwwwK", "wddwww", "dmmdww", "dmldww", "wddwww", ".wwww.", ".ssss."]),
 "bQ_near_wide": (EYE, [".KKKKKK.", "KwwwwwwK", "wwddwwww", "wdmmdwww", "wdmldwww", "wwddwwww", ".wwwwww.", ".ssssss."]),
 "bQ_far_det": (EYE, ["......", "KK....", "KKKKK.", "KdWWKK", ".dWddw", ".dmmdw", ".dmldw", "..ddd.", ".s...."]),
 "bQ_near_det": (EYE, ["........", "......KK", "...KKKKK", "KKKKKKKK", "wdWWddwK", "wdmmmdw.", "wdmlldw.", ".ddddd..", ".....ss."]),
 "bQ_far_smug": (EYE, ["......", "......", "......", "KKKKKK", ".dWddw", ".dmldw", ".dlld.", "..ddd.", ".s...."]),
 "bQ_near_smug": (EYE, ["........", "........", "........", "KKKKKKKK", "wdWWddwK", "wdmmldw.", "wdmlldw.", ".ddddd..", ".....ss."]),
 "bQ_far_shy": (EYE, ["......", "......", ".KKKK.", "KKKKKK", "dWdwww", "dmdww.", "ldd...", "......", ".s...."]),
 "bQ_near_shy": (EYE, ["........", "........", ".KKKKKK.", "KKKKKKKK", "dWddwwwK", "dmldwww.", "dlldww..", ".dd.....", ".....ss."]),
 "bQ_far_squeeze": (EYE, ["......", "......", "K.....", ".KK...", "...KK.", ".KK...", "K....."]),
 "bQ_near_squeeze": (EYE, ["........", "........", "......KK", "....KK..", "..KK....", "....KK..", "......KK"]),
 # --- mouths (anchor offset so the mouth stays centred on the model-sheet mouth anchor) ---
 "bQ_mouth_smile": (MOUTH, ["s..s", ".ss."], [1, 0]),
 "bQ_mouth_joy": (MOUTH, ["pppp", "pctp", ".pp."], [1, 0]),
 "bQ_mouth_cheer": (MOUTH, ["ppppp", "pcccp", "pcttp", ".ppp."], [1, 0]),
 "bQ_mouth_o": (dict(MOUTH, c="hair_1"), [".p.", "pcp", ".p."], [0, 0]),
 "bQ_mouth_det": (MOUTH, ["sss", "...s"], [1, 0]),
 "bQ_mouth_smirk": (MOUTH, ["...s", "sss."], [1, 0]),
 "bQ_mouth_wobble": (MOUTH, ["s.s.", ".s.s"], [1, 0]),
 "bQ_nose_cold": ({"r": "red_2", "n": "line_skin"}, ["n", "r"]),
 "bQ_blush_far_heavy": ({"r": "red_2"}, [".r.r", "r.r."], [1, 0]),
 "bQ_blush_near_heavy": ({"r": "red_2"}, [".r.r.r", "r.r.r."], [1, 0]),
 # --- fx ---
 "bQ_fx_sweat": (FX, [".b.", "bWb", "bWb", ".b."]),
 "bQ_fx_surprise": (FX, ["...K...", "K..K...", ".K.....", "......K", "....KK."]),
 "bQ_fx_sparkle": (FX, ["..y..", ".yWy.", "..y.."]),
 "bQ_fx_sparkle_s": (FX, [".y.", "yWy", ".y."]),
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
