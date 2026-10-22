"""Character generator: high-level design spec -> rigged reference model (character dict).

A variant file (data/variants/<name>.json) looks like:
{
  "name": "A_chibi",
  "label": "A · Chibi 2.5 heads",
  "palette": "cw_cranberry",                 # data/palettes/<palette>.json
  "proportions": {...},                      # see DEFAULT_PROPORTIONS (world units ~= screen px)
  "outfit": {"hair": "bob", "hat": "beanie", "coat": "parka", "scarf": "long",
             "legs": "pants", "boots": "snow", "sleeve_cuffs": false, "hem_trim": false},
  "face": {"eyes": "large", "eye_spacing": 0.32, "eye_pitch": -8},
  "render": {"camera_elevation": 16},
  "frame": {"size": [64, 64], "pivot": [32, 56]}  # optional
}

Colour tweaks per variant: "ramp_overrides": {"pom": ["mauve", "oat_1", "oat_2"]}; hair colour: outfit.hair_color.
Materials are semantic (skin, hair, hat, hatcuff, pom, coat, coat_trim, scarf, mitten, pants, skirt, boots,
boot_cuff) so colourways only re-map palette ramps; geometry never changes with colour.
"""
import copy
import math

DEFAULT_PROPORTIONS = {
    "head_r": 10.0,      # head radius (x); head is the main appeal driver
    "neck": 1.5,         # neck bone length
    "torso": 10.0,       # pelvis -> neck
    "leg": 7.0,          # hip -> ankle
    "arm": 9.5,          # shoulder -> hand
    "shoulder_w": 6.0,   # shoulder joint x offset
    "hip_w": 2.8,
    "body_w": 7.6,       # coat half-width
    "body_d": 6.2,       # coat half-depth
    "limb": 1.0,         # limb thickness scale
    "hand_r": 2.0,
    "foot": [2.9, 2.3, 3.8],
    "ankle_h": 2.0,
    "waist": 1.0,        # aline coat: waist width factor (curvy < 1)
    "hip": 1.0,          # aline coat: hip/skirt width factor
    "flare": 1.0,        # aline coat: hem flare factor
    "bust": 1.0,         # aline coat: upper bodice fullness
}
DEFAULT_OUTFIT = {"hair": "bob", "hat": "beanie", "coat": "parka", "scarf": "long", "legs": "pants",
                  "boots": "snow", "sleeve_cuffs": False, "hem_trim": False, "coat_len": 0.55,
                  "pom_size": 1.0, "hair_color": None,
                  "scarf_len": None, "scarf_tails": 2, "hair_volume": 1.0,
                  "fringe": "low", "bangs": "straight", "accessory": None, "ahoge": False}
# hair: bob | bob_long | braids | long | twintails | side_pony | pony | buns
# hat: beanie | beanie_tall | beanie_slouch | beret | earmuffs | cat_beanie | hood | none
# bangs: straight | side | points ; accessory: None | ribbon_side | ribbon_back | clip   # fringe: low | high (skin row above the eyes) | none
# scarf_len: tail segment length (default scales with torso); scarf_tails: 1 = front only;
# hair_volume: scales the bob side flaps / hair mass width   # hair_color picks palette ramp "hair_<name>"
DEFAULT_FACE = {"eyes": "large", "eye_spacing": 0.32, "eye_pitch": -8, "mouth_pitch": -32}


def _p(name, bone, center, radii, material, group, rot=None, clip_all=None, clip_any=None):
    d = {"name": name, "bone": bone, "center": [round(v, 4) for v in center],
         "radii": [round(v, 4) for v in radii], "material": material, "group": group}
    if rot:
        d["rot"] = rot
    if clip_all:
        d["clip_all"] = clip_all
    if clip_any:
        d["clip_any"] = clip_any
    return d


def build(spec):
    P = dict(DEFAULT_PROPORTIONS, **spec.get("proportions", {}))
    O = dict(DEFAULT_OUTFIT, **spec.get("outfit", {}))
    F = dict(DEFAULT_FACE, **spec.get("face", {}))
    hr, T, L, A = P["head_r"], P["torso"], P["leg"], P["arm"]
    bw, bd, ls = P["body_w"], P["body_d"], P["limb"]
    pelvis_y = P["ankle_h"] + L + 1.0
    hc = hr * 0.85                       # head centre above head bone

    bones = [
        {"name": "root", "parent": None, "offset": [0, 0, 0]},
        {"name": "pelvis", "parent": "root", "offset": [0, pelvis_y, 0]},
        {"name": "spine", "parent": "pelvis", "offset": [0, 0.3 * T, 0]},
        {"name": "chest", "parent": "spine", "offset": [0, 0.4 * T, 0]},
        {"name": "neck", "parent": "chest", "offset": [0, 0.3 * T, 0]},
        {"name": "head", "parent": "neck", "offset": [0, P["neck"], 0]},
    ]
    for s, sg in (("L", 1), ("R", -1)):
        bones += [
            {"name": f"shoulder_{s}", "parent": "chest", "offset": [sg * P["shoulder_w"], 0.2 * T, 0]},
            {"name": f"elbow_{s}", "parent": f"shoulder_{s}", "offset": [0, -A * 0.53, 0]},
            {"name": f"hand_{s}", "parent": f"elbow_{s}", "offset": [0, -A * 0.47, 0]},
            {"name": f"hip_{s}", "parent": "pelvis", "offset": [sg * P["hip_w"], -1.0, 0]},
            {"name": f"knee_{s}", "parent": f"hip_{s}", "offset": [0, -L / 2, 0]},
            {"name": f"ankle_{s}", "parent": f"knee_{s}", "offset": [0, -L / 2, 0]},
        ]

    prims, chains = [], []
    # ---------------------------------------------------------------- legs
    leg_mat = "pants"
    thin = 0.85 if O["legs"] == "skirt_tights" else 1.0
    fs = P["foot"]
    for s in "LR":
        prims.append(_p(f"thigh_{s}", f"hip_{s}", [0, -L / 4, 0], [2.4 * ls * thin, L / 4 + 0.9, 2.4 * ls * thin],
                        leg_mat, f"leg_{s}"))
        shin_mat = "boots" if O["boots"] == "tall" else leg_mat
        sr = 2.15 if O["boots"] == "tall" else 1.9 * thin
        prims.append(_p(f"shin_{s}", f"knee_{s}", [0, -L / 4, 0], [sr * ls, L / 4 + 0.6, sr * ls], shin_mat, f"leg_{s}"))
        cy = P["ankle_h"] - 0.2
        k = cy / fs[1]
        prims.append(_p(f"boot_{s}", f"ankle_{s}", [0, -0.2, 0.25 * fs[2]], fs, "boots", f"leg_{s}",
                        clip_all=[[0, 1, 0, -round(k, 4)]]))
        if O["boots"] == "snow":
            prims.append(_p(f"bootcuff_{s}", f"ankle_{s}", [0, 1.5, 0.2], [fs[0] * 1.17, 1.4, fs[0] * 1.17],
                            "boot_cuff", f"leg_{s}"))
        elif O["boots"] == "tall":
            prims.append(_p(f"bootcuff_{s}", f"knee_{s}", [0, -0.6, 0.1], [2.85 * ls, 1.3, 2.85 * ls], "boot_cuff", f"leg_{s}"))
    prims.append(_p("hips", "pelvis", [0, 0, 0], [bw * 0.66, 2.6, bd * 0.65], leg_mat, "torso"))
    if O["legs"] == "skirt_tights":
        prims.append(_p("skirt", "pelvis", [0, -1.4, 0.1], [bw * 1.02, 2.0, bd * 1.02], "skirt", "torso"))

    # ---------------------------------------------------------------- coat
    coat = O["coat"]
    if coat in ("parka", "duffle"):
        prims.append(_p("coat_up", "chest", [0, -0.04 * T, 0], [bw * 0.87, 0.46 * T, bd * 0.87], "coat", "torso"))
        if coat == "parka":
            prims.append(_p("coat_low", "spine", [0, -0.04 * T, 0.2], [bw, 0.48 * T, bd], "coat", "torso"))
            prims.append(_p("hem", "pelvis", [0, 0.02 * T, 0.2], [bw * 1.05, 0.22 * T, bd * 1.06],
                            "coat_trim" if O["hem_trim"] else "coat", "torso"))
        else:
            top = 0.45 * T
            bottom = -O["coat_len"] * L
            prims.append(_p("coat_low", "pelvis", [0, (top + bottom) / 2, 0.2], [bw * 1.06, (top - bottom) / 2, bd * 1.04],
                            "coat", "torso"))
            for k, y in enumerate((0.3 * T, -0.02 * T)):
                prims.append(_p(f"toggle_{k}", "spine", [0, y, bd * 1.0], [1.9, 0.85, 0.9], "coat_trim", "toggles"))
            if O["hem_trim"]:
                prims.append(_p("hem", "pelvis", [0, bottom + 0.5, 0.2], [bw * 1.1, 0.9, bd * 1.08], "coat_trim", "torso"))
        prims.append(_p("hood", "chest", [0, 0.24 * T, -bd * 0.84], [bw * 0.8, 0.34 * T, bd * 0.52], "coat", "torso"))
    elif coat == "aline":
        # fitted bodice -> cinched waist (belt) -> flared skirt coat: the feminine hourglass silhouette
        wa, hp, fl, bu = P["waist"], P["hip"], P["flare"], P["bust"]
        prims.append(_p("bodice", "chest", [0, -0.02 * T, 0.05], [bw * 0.8 * bu, 0.36 * T, bd * 0.8 * bu], "coat", "torso"))
        prims.append(_p("waist", "spine", [0, 0.05 * T, 0.1], [bw * 0.7 * wa, 0.26 * T, bd * 0.68 * wa], "coat", "torso"))
        prims.append(_p("belt", "spine", [0, -0.08 * T, 0.1], [bw * 0.74 * wa, 0.06 * T + 0.5, bd * 0.72 * wa],
                        "coat_trim", "belt"))
        top = -0.12 * T
        bottom = -O["coat_len"] * L
        prims.append(_p("skirt_coat", "pelvis", [0, (top + bottom) / 2 + 0.4 * T * 0.3, 0.15],
                        [bw * 0.95 * hp * fl, (top - bottom) / 2 + 0.6, bd * 0.95 * hp * fl], "coat", "torso",
                        clip_all=[[0, -1, 0, -0.85]]))
        prims.append(_p("hips_coat", "pelvis", [0, 0.1 * T, 0.12], [bw * 0.82 * hp, 0.22 * T, bd * 0.8 * hp], "coat", "torso"))
        if O["hem_trim"]:
            prims.append(_p("hem", "pelvis", [0, bottom + 0.6, 0.15], [bw * 1.0 * hp * fl, 0.8, bd * 1.0 * hp * fl],
                            "coat_trim", "torso"))
        prims.append(_p("collar", "neck", [0, -0.6, 0.0], [bw * 0.55, 0.12 * T, bd * 0.55], "coat_trim", "torso"))
    elif coat == "puffer":
        prims.append(_p("core", "spine", [0, 0.1 * T, 0.1], [bw * 0.9, 0.55 * T, bd * 0.88], "coat", "torso"))
        for k, (bone, y, sx) in enumerate((("pelvis", 0.06 * T, 1.04), ("spine", 0.14 * T, 1.0), ("chest", 0.04 * T, 0.92))):
            prims.append(_p(f"puff_{k}", bone, [0, y, 0.2], [bw * sx, 0.2 * T, bd * sx], "coat", "torso"))
        prims.append(_p("collar", "neck", [0, -0.3, 0], [bw * 0.6, 0.22 * T, bd * 0.6], "coat", "torso"))

    # ---------------------------------------------------------------- arms
    for s in "LR":
        sg = 1 if s == "L" else -1
        prims.append(_p(f"uparm_{s}", f"shoulder_{s}", [0, -A * 0.26, 0], [2.5 * ls, A * 0.53 / 2 + 0.6, 2.5 * ls],
                        "coat", f"arm_{s}"))
        prims.append(_p(f"forearm_{s}", f"elbow_{s}", [0, -A * 0.235, 0], [2.2 * ls, A * 0.47 / 2 + 0.45, 2.2 * ls],
                        "coat", f"arm_{s}"))
        if O["sleeve_cuffs"]:
            prims.append(_p(f"cuff_{s}", f"elbow_{s}", [0, -A * 0.47 + 0.5, 0], [2.45 * ls, 0.75, 2.45 * ls],
                            "coat_trim", f"arm_{s}"))
        h = P["hand_r"]
        prims.append(_p(f"mitten_{s}", f"hand_{s}", [0, -h * 0.75, 0.2], [h, h * 1.05, h], "mitten", f"arm_{s}"))
        prims.append(_p(f"thumb_{s}", f"hand_{s}", [-sg * 0.4 * h, -0.45 * h, 0.8 * h], [0.45 * h] * 3, "mitten", f"arm_{s}"))

    # ---------------------------------------------------------------- neck + scarf
    prims.append(_p("neck", "neck", [0, 0.6, 0], [2.4, 2.2, 2.4], "skin", "torso"))
    sc = O["scarf"]
    if sc in ("long", "chunky"):
        big = 1.12 if sc == "chunky" else 1.0
        prims.append(_p("scarf_wrap1", "neck", [0, 0.5, 0.3], [bw * 0.79 * big, 2.0 * big, bd * 0.89 * big], "scarf", "scarf"))
        prims.append(_p("scarf_wrap2", "neck", [0.3, -0.9, 0.6], [bw * 0.87 * big, 1.7 * big, bd * 0.95 * big], "scarf",
                        "scarf", rot=[0, 0, 6]))
        tails = [("scarf_front", [bw * 0.55, -0.6, bd * 0.74], [0.18, -1, 0.28] if O.get("scarf_v2") else [0.2, -1, 0.6])]
        seg_len = O["scarf_len"] or round(3.2 * T / 10.0, 3)
        if sc == "long" and O["scarf_tails"] >= 2:
            tails.append(("scarf_back", [-bw * 0.58, -0.2, -bd * 0.74], [-0.4, -1, -0.45]))
        for name, anchor, rd in tails:
            nseg = 4 if sc == "long" else 3
            w = 3.0 if sc == "long" else 3.6
            chains.append({"name": name, "anchor_bone": "neck", "anchor": anchor, "rest_dir": rd,
                           "segments": nseg, "seg_len": seg_len, "widths": [w - 0.2 * i for i in range(nseg)],
                           "thickness": 1.3, "material": "scarf",
                           **({"stiffness": 140, "damping": 0.08, "gravity": 1200, "max_swing": 40} if O.get("scarf_v2")
                              else {"stiffness": 40, "damping": 0.10, "gravity": 650})})
            if O.get("scarf_v2") and name == "scarf_front":
                # visible knot where the tail leaves the wrap: the tie side reads the same in every view
                prims.append(_p("scarf_knot", "neck", [anchor[0], anchor[1] + 0.2, anchor[2]], [1.6 * big, 1.3 * big, 1.2 * big],
                                "scarf", "scarf"))

    # ---------------------------------------------------------------- head, hair, hat
    # under a hat the skull top is never visible; clip it so it can't poke through a low dome
    prims.append(_p("head", "head", [0, hc, 0.5], [hr, hr * 0.95, hr * 0.95], "skin", "head",
                    clip_all=[[0, -1, 0, -0.6]] if O["hat"] in ("beanie", "beanie_tall", "beanie_slouch", "cat_beanie") else None))
    hair = O["hair"]
    hair_mat = f"hair_{O['hair_color']}" if O["hair_color"] else "hair"
    if hair in ("bob", "bob_long"):
        cut = -0.62 if hair == "bob" else -0.86
        prims.append(_p("hair_cap", "head", [0, hc + 0.04 * hr, 0.1], [hr * 1.07, hr * 1.02, hr * 1.03], hair_mat, "head",
                        # top clip keeps hair under the hat cuff so the beanie dome reads as its own shape
                        clip_all=[[0, 1, 0, cut]] + ([[0, -1, 0, -0.40]] if O["hat"] in ("beanie", "beanie_tall", "beanie_slouch", "cat_beanie", "hood")
                                                     else [[0, -1, 0, -0.62]] if O["hat"] == "beret" else []),
                        clip_any=[[0, 0, -1, -0.22], [0, 1, 0, 0.30]]))
        for s, sg in (("L", 1), ("R", -1)):
            hv = O["hair_volume"]
            prims.append(_p(f"bob_side_{s}", "head", [sg * hr * (0.74 + 0.08 * (hv - 1)), hc - 0.28 * hr, -0.08 * hr],
                            [hr * 0.38 * hv, hr * 0.5, hr * 0.62 * hv], hair_mat, "head", clip_all=[[0, 1, 0, -0.6]]))
            chains.append({"name": f"bob_{s}", "anchor_bone": "head", "anchor": [sg * hr * 0.8, hc - 0.3 * hr, -0.1 * hr],
                           "rest_dir": [sg * 0.15, -1, 0.05], "segments": 1, "seg_len": hr * (0.32 if hair == "bob" else 0.5),
                           "widths": [hr * 0.3], "thickness": hr * 0.42, "material": hair_mat,
                           "stiffness": 220, "damping": 0.10, "gravity": 500})
        # straight-cut fringe hanging just below the hat cuff (never pokes through it)
        if O["fringe"] != "none":
            fy = 0.12 if O["fringe"] == "low" else 0.2
            if O["bangs"] == "side":
                prims.append(_p("fringe", "head", [0.16 * hr, hc + fy * hr, 0.84 * hr], [hr * 0.8, hr * 0.16, hr * 0.18],
                                hair_mat, "head", rot=[0, 0, -12]))
            elif O["bangs"] == "points":
                for k, x in enumerate((-0.48, -0.16, 0.16, 0.48)):
                    prims.append(_p(f"bang_{k}", "head", [x * hr, hc + fy * hr, 0.86 * hr],
                                    [hr * 0.2, hr * 0.22, hr * 0.16], hair_mat, "head"))
            else:
                prims.append(_p("fringe", "head", [0, hc + fy * hr, 0.84 * hr], [hr * 0.74, hr * 0.15, hr * 0.18], hair_mat, "head"))
    elif hair == "braids":
        prims.append(_p("hair_cap", "head", [0, hc + 0.04 * hr, 0.1], [hr * 1.06, hr * 1.01, hr * 1.01], hair_mat, "head",
                        clip_all=[[0, 1, 0, -0.55]] + ([[0, -1, 0, -0.40]] if O["hat"] != "none" else []),
                        clip_any=[[0, 0, -1, -0.3], [0, 1, 0, 0.32]]))
        for s, sg in (("L", 1), ("R", -1)):
            chains.append({"name": f"braid_{s}", "anchor_bone": "head", "anchor": [sg * hr * 0.92, hc - 0.3 * hr, -0.32 * hr],
                           "rest_dir": [sg * 0.85, -1.3, -0.25], "segments": 2, "seg_len": hr * 0.36,
                           "widths": [hr * 0.24, hr * 0.22], "thickness": hr * 0.2, "material": hair_mat,
                           "tip": {"radius": hr * 0.125, "material": "pom"},
                           "stiffness": 180, "damping": 0.10, "gravity": 500})


    elif hair in ("long", "twintails", "side_pony", "pony", "buns"):
        # crown + sides; the back of the head is covered down to the nape for every long style
        top_clip = [[0, -1, 0, -0.40]] if O["hat"] not in ("none", "beret", "earmuffs") else []
        if O["hat"] == "beret":
            top_clip = [[0, -1, 0, -0.62]]
        prims.append(_p("hair_cap", "head", [0, hc + 0.04 * hr, 0.0], [hr * 1.07, hr * 1.03, hr * 1.04], hair_mat, "head",
                        clip_all=[[0, 1, 0, -0.72]] + top_clip, clip_any=[[0, 0, -1, -0.22], [0, 1, 0, 0.32]]))
        # cheek-length side locks frame the face (hime-style)
        for s_, sg in (("L", 1), ("R", -1)):
            prims.append(_p(f"sidelock_{s_}", "head", [sg * hr * 0.86, hc - 0.32 * hr, 0.22 * hr],
                            [hr * 0.24, hr * 0.5, hr * 0.32], hair_mat, "head", rot=[0, 0, sg * 6]))
        def lock(name, anchor, rd, n, seg, w0, w1, thick, tie=None, stiff=160):
            chains.append({"name": name, "anchor_bone": "head", "anchor": anchor, "rest_dir": rd, "segments": n,
                           "seg_len": seg, "widths": [w0 + (w1 - w0) * k / max(n - 1, 1) for k in range(n)],
                           "thickness": thick, "material": hair_mat, "group": "head", "stiffness": stiff, "damping": 0.12,
                           "gravity": 520, **({"tie": tie} if tie else {})})
        hl = O.get("hair_len", 1.0)          # long styles: 1.0 = shoulder blades, 2.0 = waist
        nseg = max(2, int(round(3 * hl)))
        if hair == "long":
            prims.append(_p("hair_back", "head", [0, hc - 0.5 * hr, -0.55 * hr], [hr * 0.98, hr * 0.85, hr * 0.5],
                            hair_mat, "head"))
            for k, x in enumerate((-0.55, 0.0, 0.55)):
                lock(f"lock_{k}", [x * hr, hc - 1.0 * hr, -0.62 * hr], [x * 0.25, -1, -0.25], nseg, 0.34 * hr,
                     0.38 * hr, 0.18 * hr, 0.26 * hr)
        elif hair == "twintails":
            for s_, sg in (("L", 1), ("R", -1)):
                a = [sg * hr * 0.98, hc + 0.42 * hr, -0.38 * hr]
                tl = O.get("tail_len", 1.0)
                lock(f"tail_{s_}", [a[0] + sg * 0.12 * hr, a[1], a[2]], [sg * 0.9, -1, -0.15], max(4, nseg), 0.3 * hr * tl,
                     0.3 * hr, 0.16 * hr, 0.26 * hr)
                prims.append(_p(f"tie_{s_}", "head", [a[0] + sg * 0.1 * hr, a[1], a[2]], [hr * 0.2] * 3, "ribbon", "hat"))
        elif hair == "side_pony":
            a = [hr * 0.88, hc + 0.22 * hr, -0.42 * hr]
            lock("pony", a, [0.5, -1, -0.25], max(4, nseg), 0.34 * hr, 0.4 * hr, 0.2 * hr, 0.32 * hr)
            prims.append(_p("tie", "head", [a[0] + 0.1 * hr, a[1], a[2]], [hr * 0.2] * 3, "ribbon", "hat"))
        elif hair == "pony":
            a = [0, hc + 0.42 * hr, -0.96 * hr]
            lock("pony", a, [0, -1, -0.55], max(4, nseg), 0.34 * hr, 0.4 * hr, 0.2 * hr, 0.32 * hr)
            prims.append(_p("tie", "head", [a[0], a[1], a[2] - 0.1 * hr], [hr * 0.2] * 3, "ribbon", "hat"))
        elif hair == "buns":
            for s_, sg in (("L", 1), ("R", -1)):
                prims.append(_p(f"bun_{s_}", "head", [sg * hr * 0.62, hc + 0.78 * hr, -0.3 * hr], [hr * 0.34] * 3,
                                hair_mat, "head"))
                prims.append(_p(f"bun_tie_{s_}", "head", [sg * hr * 0.5, hc + 0.55 * hr, 0.05 * hr],
                                [hr * 0.17] * 3, "ribbon", "hat"))
        # bangs
        if O["bangs"] == "side":
            prims.append(_p("fringe", "head", [0.18 * hr, hc + 0.28 * hr, 0.84 * hr], [hr * 0.8, hr * 0.17, hr * 0.2],
                            hair_mat, "head", rot=[0, 0, -12]))
        elif O["bangs"] == "points":
            for k, x in enumerate((-0.48, -0.16, 0.16, 0.48)):
                prims.append(_p(f"bang_{k}", "head", [x * hr, hc + 0.24 * hr, 0.86 * hr], [hr * 0.2, hr * 0.24, hr * 0.16],
                                hair_mat, "head"))
        else:
            prims.append(_p("fringe", "head", [0, hc + 0.26 * hr, 0.84 * hr], [hr * 0.78, hr * 0.17, hr * 0.2],
                            hair_mat, "head"))

    if O["ahoge"] and O["hat"] in ("none", "earmuffs"):
        chains.append({"name": "ahoge", "anchor_bone": "head", "anchor": [0.1 * hr, hc + 1.0 * hr, 0.1 * hr],
                       "rest_dir": [0.4, 1, 0.3], "segments": 2, "seg_len": 0.22 * hr, "widths": [0.12 * hr, 0.08 * hr],
                       "thickness": 0.1 * hr, "material": hair_mat, "stiffness": 300, "damping": 0.12, "gravity": 200})

    if O["hat"] in ("beanie", "beanie_tall", "beanie_slouch", "cat_beanie"):
        dome_h = {"beanie": 0.8, "beanie_tall": 0.95, "beanie_slouch": 0.85, "cat_beanie": 0.78}[O["hat"]]
        rot = [-12, 0, 0] if O["hat"] == "beanie_slouch" else None
        dz = -0.05 * hr if O["hat"] == "beanie_slouch" else 0
        slouch = O["hat"] == "beanie_slouch"
        prims.append(_p("beanie", "head", [0, hc + (0.12 if slouch else 0.19) * hr, dz], [hr * 1.04, hr * dome_h, hr * 1.02],
                        "hat", "hat", rot=rot, clip_all=[[0, 1, 0, 0.12 if slouch else 0.2]]))
        # knit cuff: a fat band that protrudes past the dome so it reads as a separate stripe from above
        prims.append(_p("beanie_cuff", "head", [0, hc + 0.36 * hr, 0.02 * hr], [hr * 1.13, hr * 0.2, hr * 1.11],
                        "hatcuff", "hat"))
        top = hc + 0.19 * hr + hr * dome_h * 0.95
        if O["hat"] == "cat_beanie":
            O["pom_size"] = 0          # cat beanie: ears replace the pom
        pom_r = hr * 0.24 * O["pom_size"]
        if pom_r > 0:
            chains.append({"name": "pom", "anchor_bone": "head", "anchor": [0, top - 0.6, dz * 1.6 - 0.1 * hr],
                         "rest_dir": [0, 1, -0.2 if O["hat"] != "beanie_slouch" else -0.8], "segments": 1,
                         "seg_len": pom_r * 1.2, "widths": [1.0], "thickness": 1.0, "material": "pom",
                         "draw_segments": False, "tip": {"radius": pom_r, "material": "pom"},
                         "stiffness": 200, "damping": 0.10, "gravity": 260})


    if O["hat"] == "cat_beanie":
        for s_, sg in (("L", 1), ("R", -1)):
            prims.append(_p(f"cat_ear_{s_}", "head", [sg * hr * 0.55, hc + 1.02 * hr, 0.0], [hr * 0.26, hr * 0.34, hr * 0.16],
                            "hat", "hat", rot=[0, 0, -sg * 22]))
    elif O["hat"] == "beret":
        prims.append(_p("beret", "head", [0.12 * hr, hc + 0.78 * hr, -0.05 * hr], [hr * 1.12, hr * 0.3, hr * 1.06],
                        "hat", "hat", rot=[-6, 0, -12]))
        prims.append(_p("beret_nub", "head", [0.2 * hr, hc + 1.06 * hr, -0.05 * hr], [hr * 0.12] * 3, "hat", "hat"))
    elif O["hat"] == "earmuffs":
        prims.append(_p("muff_band", "head", [0, hc + 0.05 * hr, -0.05 * hr], [hr * 1.12, hr * 1.12, hr * 0.14],
                        "hat", "hat", clip_all=[[0, 1, 0, 0.35]]))   # only the arc over the crown
        for s_, sg in (("L", 1), ("R", -1)):
            prims.append(_p(f"muff_{s_}", "head", [sg * hr * 1.02, hc - 0.02 * hr, -0.18 * hr], [hr * 0.2, hr * 0.27, hr * 0.27],
                            "pom", "hat"))
    elif O["hat"] == "hood":
        prims.append(_p("hood_up", "head", [0, hc + 0.06 * hr, -0.12 * hr], [hr * 1.2, hr * 1.16, hr * 1.18], "coat", "hat",
                        clip_any=[[0, 0, -1, -0.42], [0, 1, 0, 0.58], [0, -1, 0, 0.8]]))
        import math as _m
        for k in range(12):          # fur trim: closed ring around the face opening
            ang = _m.radians(k * 30)
            prims.append(_p(f"hood_fur_{k}", "head",
                            [hr * 0.95 * _m.sin(ang), hc + 0.05 * hr + hr * 0.82 * _m.cos(ang), 0.62 * hr],
                            [hr * 0.24] * 3, "coat_trim", "hat"))
    acc = O["accessory"]
    if acc in ("ribbon_side", "ribbon_back"):
        base = [hr * 0.78, hc + 0.62 * hr, -0.2 * hr] if acc == "ribbon_side" else [0, hc + 0.5 * hr, -0.98 * hr]
        sg = 1
        for k, dx in enumerate((-0.22, 0.22)):
            c_ = [base[0] + dx * hr * (1 if acc == "ribbon_back" else 0.4), base[1], base[2] + (dx * hr * 0.9 if acc == "ribbon_side" else 0)]
            prims.append(_p(f"ribbon_loop_{k}", "head", c_, [hr * 0.2, hr * 0.15, hr * 0.12], "ribbon", "hat",
                            rot=[0, 0, 25 if k else -25]))
        prims.append(_p("ribbon_knot", "head", base, [hr * 0.09] * 3, "ribbon", "hat"))
    elif acc == "clip":
        prims.append(_p("hairclip", "head", [hr * 0.62, hc + 0.5 * hr, 0.72 * hr], [hr * 0.16, hr * 0.07, hr * 0.06],
                        "ribbon", "hat", rot=[0, 0, -30]))

    colliders = [{"bone": "spine", "center": [0, -0.04 * T, 0.2], "radius": min(bw, bd) * 1.03},
                 {"bone": "chest", "center": [0, -0.04 * T, 0], "radius": min(bw, bd) * 0.9},
                 {"bone": "head", "center": [0, hc, 0.5], "radius": hr * 0.98}]
    # designer geometry overrides (no code edits needed):
    #   "prim_overrides": {"<prim name>": {"center": [...], "radii": [...], "rot": [...], "material": "..."}},
    #   "chain_overrides": {"<chain name>": {...}}, "remove": ["<name>", ...], "add_prims": [{...}, ...]
    po, co = spec.get("prim_overrides", {}), spec.get("chain_overrides", {})
    rm = set(spec.get("remove", []))
    prims = [dict(p_, **po.get(p_["name"], {})) for p_ in prims if p_["name"] not in rm]
    chains = [dict(c_, **co.get(c_["name"], {})) for c_ in chains if c_["name"] not in rm]
    prims += [dict({"group": "hat", "material": "hat"}, **ap) for ap in spec.get("add_prims", [])]
    # designers may add whole chains (extra hair locks, ribbon tails, tassels): same schema as generated chains
    chains += [dict({"segments": 2, "seg_len": 2.0, "widths": [1.5], "thickness": 1.0, "stiffness": 160,
                     "damping": 0.1, "gravity": 520, "rest_dir": [0, -1, 0]}, **ac) for ac in spec.get("add_chains", [])]
    yaw = math.degrees(math.asin(min(F["eye_spacing"] / math.cos(math.radians(F["eye_pitch"])), 0.9)))
    hd = {}
    if spec.get("model") == "hd":
        # HD reference model: SDF parts next to the legacy primitives (which stay the sim/QA collision proxies)
        chains += [dict({"segments": 2, "seg_len": 2.0, "widths": [1.5], "thickness": 1.0, "stiffness": 160,
                         "damping": 0.1, "gravity": 520, "rest_dir": [0, -1, 0]}, **ac) for ac in spec.get("hd_chains", [])]
        hd = {"model": "hd", "parts": hd_parts(prims, spec)}
    return {
        "name": spec.get("name", "variant"),
        "label": spec.get("label", spec.get("name", "")),
        "version": 2,
        "generated_from": copy.deepcopy(spec),
        "head_bones": ["head"],
        "render": dict({"camera_elevation": 16}, **spec.get("render", {})),
        "shadow": spec.get("shadow"),
        "sim": spec.get("sim", {}),
        "bones": bones, "primitives": prims, "chains": chains, "colliders": colliders,
        "face": {"bone": "head", "center": [0, hc, 0.5], "radii": [hr, hr * 0.95, hr * 0.95],
                 "eye_yaw": round(yaw, 3), "eye_pitch": F["eye_pitch"], "mouth_pitch": F["mouth_pitch"],
                 "eyes": F["eyes"], "visibility_min": 0.18},
        **hd,
    }


def hd_parts(prims, spec):
    """Legacy ellipsoids converted 1:1 to parts, then the variant's HD parts.
    Variant keys: "parts" / "add_parts" (part specs, see pipeline/sdf.py), "remove_parts" (names, parts only:
    the legacy primitives stay as collision proxies), "part_overrides": {"<name>": {...}}."""
    rm = set(spec.get("remove_parts", []))
    po = spec.get("part_overrides", {})
    parts = []
    for p_ in prims:
        if p_["name"] in rm:
            continue
        d = {"name": p_["name"], "bone": p_["bone"], "shape": "ellipsoid", "center": p_["center"],
             "radii": p_["radii"], "rot": p_.get("rot", [0, 0, 0]), "material": p_["material"],
             "group": p_.get("group", p_["bone"]), "legacy": True}
        for k in ("clip_all", "clip_any"):
            if p_.get(k):
                d[k] = p_[k]
        parts.append(dict(d, **po.get(p_["name"], {})))
    for ap in spec.get("parts", []) + spec.get("add_parts", []):
        if ap["name"] not in rm:
            parts.append(dict({"group": "head", "op": "union", "lod": "all"}, **ap, **po.get(ap["name"], {})))
    return parts
