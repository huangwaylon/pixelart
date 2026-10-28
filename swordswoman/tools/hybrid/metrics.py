"""Consistency / quality / motion metrics for a sprite set (128 cells, palette-locked).

  .venv/bin/python tools/hybrid/metrics.py SPRITES_OR_DIRS... [--guide-dir DIR] [--guide-map map.json]
        [--json OUT.json] [--quiet]

Sprites are named <anim>_<DIR>[_<key>].png (STANDARD TEST SET: turn_<DIR>, walk_SE_k0..3,
slash_SE_k0..3, jump_E_{crouch,apex,land}); aux files (*_4x, *_hires, *_dbg ...) are skipped.
Guides: --guide-map {stem: prefix}, else <guide-dir>/<stem>, else <sprite dir>/guide/<stem>.

Per sprite
  palette     off_palette, semi_alpha, colours, orphans (not whitelisted, sword excluded),
              lint counts (outline_gap, notch, spur, double, jaggy) from tools/pixel/lint.py
  geometry    bbox, height, body_height, baseline (vs pivot 104), feet_cx (vs 64)
  guide       iou (whole), iou_body (sword-free), feature drift vs the guide: eyes / eye_row, bow,
              guard (sword hand), sword_tip; guide features come from the guide's colour sprite
              (P.png / P_body.png) or its joints (bow, face, guard)
  features    normalised positions: eye_row_rel, bow_rel (y from the top / body height)
Set level
  colour      per ramp: share of each tone; drift = L1 distance of each sprite's tone mix from the
              set median (0 = identical shading, 2 = disjoint); worst sprite per ramp; ramp area share
  directions  turn set: height / eye_row_rel / bow_rel spread across the 8 directions
Per sequence (same anim + dir, ordered by key)
  flicker     A->B->A toggles with a static 5x5 neighbourhood (lint R45)
  boil        changed px between consecutive frames inside guide-static regions (when guides exist)
  motion      per-frame height / width relative to rest (turn_<DIR> if present, else frame 0):
              squash = min h ratio, stretch = max h ratio; head / bow displacement vs body
              (overlap = how far the bow moves relative to the body; lag = frames by which the
              bow follows the body, from cyclic cross-correlation); sword-tip path: length,
              smoothness (1 - mean |2nd difference| / mean |1st difference|), circle-fit residual;
              smear px per frame (steel_2 / pink_1 / pink_0 above the rest pose).  Flags:
              'stiff' (idle / walk head moves <= 1 px), 'no_smear' (slash k1 without a smear).
"""
import argparse
import json
import os
import sys
from collections import Counter

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hylib as H  # noqa: E402

sys.path.insert(0, os.path.join(H.ROOT, "tools", "pixel"))
import lint as L  # noqa: E402


def r1(v, n=2):
    if v is None:
        return None
    if isinstance(v, (tuple, list, np.ndarray)):
        return [round(float(x), n) for x in v]
    return round(float(v), n)


def dist(a, b):
    return float(np.hypot(a[0] - b[0], a[1] - b[1]))


def sprite_metrics(path, guide):
    a = H.load_rgba(path)
    pal = H.palette()
    idx = H.index_of(a)
    flags, info, _ = L.lint_frame(a, pal, guide.ids if guide is not None and guide.ids is not None else None,
                                  guide.gnames if guide is not None else None)
    cnt = Counter(f["type"] for f in flags if f["sev"] != "info")
    # FX mask (S5 r3): <stem>_fxmask.png (alpha > 0 = FX pixel: smears, sparks, dust, streaks, afterimages) is
    # removed before the geometric features, so body height / squash-stretch and the sword-tip track measure the
    # character, not the effects. Lint / palette / smear_px still see the full frame.
    fxp = path[:-4] + "_fxmask.png"
    af = a
    if os.path.exists(fxp):
        fm = H.load_rgba(fxp)[..., 3] > 0
        af = a.copy(); af[fm] = 0
    F = H.features(af, guide)
    steel = H.base_mask(idx, "steel")
    sword = H.disk_op(steel, 1)
    orph = [f for f in flags if f["type"] == "orphan" and f.get("detail") not in H.ORPHAN_OK and not sword[f["y"], f["x"]]]
    m = dict(name=os.path.basename(path), path=os.path.relpath(path, H.ROOT),
             off_palette=int((idx == -2).sum()), semi_alpha=int(((a[..., 3] > 0) & (a[..., 3] < 255)).sum()),
             colours=info["n_colours"], opaque=int((idx != -1).sum()), orphans=len(orph),
             lint={k: cnt.get(k, 0) for k in ("outline_gap", "notch", "spur", "double", "jaggy", "banding")})
    for k in ("bbox", "height", "width", "body_height", "baseline", "feet_cx", "eye_row", "sword_px"):
        if k in F:
            m[k] = r1(F[k]) if k != "bbox" else F[k]
    if "baseline" in F:
        m["baseline_off"] = int(F["baseline"] - H.PIVOT[1])
    if F.get("feet_cx") is not None:
        m["feet_cx_off"] = r1(F["feet_cx"] - H.PIVOT[0])
    bh = F.get("body_height") or 1
    if "eye_row" in F:
        m["eye_row_rel"] = r1((F["eye_row"] - F["body_top"]) / bh, 3)
    if "bow" in F:
        m["bow_rel"] = r1((F["bow"][1] - F["body_top"]) / bh, 3)
    m["feat"] = {k: r1(F[k]) for k in ("eyes", "bow", "head", "body", "guard", "sword_tip") if k in F}
    # tone mix per ramp
    mix = {}
    for b in H.BASE:
        tones = [n for n in H.base_tones(b, False)]
        ids = [pal.index[n] for n in tones]
        c = np.array([(idx == i).sum() for i in ids], float)
        if c.sum() >= 4:
            mix[b] = dict(zip(tones, (c / c.sum()).round(3).tolist()))
            mix[b]["_px"] = int(c.sum())
    m["tone_mix"] = mix
    if guide is not None:
        op = idx != -1
        m["guide"] = guide.prefix if not os.path.isabs(guide.prefix) else os.path.relpath(guide.prefix, H.ROOT)
        m["iou"] = r1(iou(op, guide.mask), 4)
        m["iou_body"] = r1(iou(op & ~H.disk_op(guide.sword, 1), guide.body), 4)
        GF = H.features(guide.color, guide) if guide.color is not None else {}
        gj = dict(guide.joints)
        ref = {"eyes": GF.get("eyes") or gj.get("eyes") or gj.get("face"), "bow": GF.get("bow") or gj.get("bow"),
               "guard": GF.get("guard") or gj.get("guard"), "sword_tip": GF.get("sword_tip"),
               "head": GF.get("head") or gj.get("hair")}
        drift = {}
        for k, gv in ref.items():
            if gv is not None and k in F:
                drift[k] = dict(dx=r1(F[k][0] - gv[0], 1), dy=r1(F[k][1] - gv[1], 1), d=r1(dist(F[k], gv), 1))
        if "eye_row" in F and GF.get("eye_row") is not None:
            drift["eye_row"] = r1(F["eye_row"] - GF["eye_row"], 1)
        m["drift"] = drift
    return m, idx, F


def iou(a, b):
    u = (a | b).sum()
    return float((a & b).sum() / u) if u else 0.0


def colour_drift(ms):
    out = {}
    for b in H.BASE:
        rows = [(m["name"], m["tone_mix"][b]) for m in ms if b in m["tone_mix"]]
        if len(rows) < 2:
            continue
        tones = [t for t in rows[0][1] if t != "_px"]
        V = np.array([[r[t] for t in tones] for _, r in rows])
        med = np.median(V, 0)
        d = np.abs(V - med).sum(1)
        k = int(d.argmax())
        out[b] = dict(median=dict(zip(tones, med.round(3).tolist())), max_drift=r1(d[k], 3), worst=rows[k][0],
                      mean_drift=r1(d.mean(), 3))
    tot = {m["name"]: max(m["opaque"], 1) for m in ms}
    area = {}
    for b in H.BASE:
        v = [m["tone_mix"].get(b, {}).get("_px", 0) / tot[m["name"]] for m in ms]
        if max(v) > 0.01:
            area[b] = dict(mean=r1(np.mean(v), 3), min=r1(min(v), 3), max=r1(max(v), 3))
    return out, area


def circle_fit(P):
    P = np.asarray(P, float)
    if len(P) < 3:
        return None
    A = np.c_[2 * P, np.ones(len(P))]
    b = (P ** 2).sum(1)
    try:
        sol, *_ = np.linalg.lstsq(A, b, rcond=None)
    except np.linalg.LinAlgError:
        return None
    c = sol[:2]
    r = np.sqrt(max(sol[2] + (c ** 2).sum(), 0))
    res = np.abs(np.linalg.norm(P - c, axis=1) - r)
    return dict(cx=r1(c[0], 1), cy=r1(c[1], 1), r=r1(r, 1), rms=r1(np.sqrt((res ** 2).mean()), 2))


def seq_metrics(anim, d, names, recs, rest, guides):
    pal = H.palette()
    idxs = [recs[n][1] for n in names]
    F = [recs[n][2] for n in names]
    loop = anim in ("idle", "walk", "run", "turn", "combat")
    out = dict(anim=anim, dir=d, frames=names, loop=loop)
    fl = L.flicker(idxs, loop)
    out["flicker"] = sum(len(v) for v in fl.values())
    # boil inside guide-static regions
    gs = [guides.get(n) for n in names]
    if all(g is not None and g.ids is not None for g in gs) and len(gs) > 1:
        boil = []
        for k in range(len(names) - (0 if loop else 1)):
            k2 = (k + 1) % len(names)
            if k2 == k:
                continue
            stat = (gs[k].ids == gs[k2].ids) & gs[k].mask & gs[k2].mask
            stat = ~H.disk_op(~stat, 1)
            boil.append(int(((idxs[k] != idxs[k2]) & stat).sum()))
        out["boil_px"] = boil
    # motion
    R = rest if rest is not None else F[0]
    # body (sword-free) extents: squash & stretch is about the body, not the blade
    hr, wr = R.get("body_height") or 1, R.get("body_width") or 1
    hs = [f.get("body_height", 0) / hr for f in F]
    ws = [f.get("body_width", 0) / wr for f in F]
    out["h"] = [f.get("body_height") for f in F]
    out["w"] = [f.get("body_width") for f in F]
    out["h_ratio"] = [r1(v, 3) for v in hs]
    out["w_ratio"] = [r1(v, 3) for v in ws]
    out["squash"] = r1(min(hs), 3)
    out["stretch"] = r1(max(hs), 3)

    def series(key):
        if all(key in f for f in F):
            return np.array([f[key] for f in F], float)
        return None
    body, head, bow = series("body"), series("head"), series("bow")
    if body is not None:
        out["body_path"] = [r1(p, 1) for p in body]
    for nm, s in (("head", head), ("bow", bow)):
        if s is None or body is None:
            continue
        rel = s - body
        out[f"{nm}_disp_max"] = r1(np.abs(s - s[0]).max(), 1)
        out[f"{nm}_overlap"] = r1(np.linalg.norm(rel - rel.mean(0), axis=1).max(), 2)
        if len(s) >= 3:
            vb = np.diff(np.r_[body, body[:1]] if loop else body, axis=0)[:, 1]
            vs = np.diff(np.r_[s, s[:1]] if loop else s, axis=0)[:, 1]
            if vb.std() > 1e-6 and vs.std() > 1e-6:
                cors = [float(np.corrcoef(vb, np.roll(vs, -k))[0, 1]) for k in range(len(vb) if loop else 1)]
                out[f"{nm}_lag"] = int(np.argmax(cors))
                out[f"{nm}_lag_corr"] = r1(max(cors), 2)
    tip = series("sword_tip")
    if tip is not None and len(tip) >= 2:
        d1 = np.linalg.norm(np.diff(tip, axis=0), axis=1)
        out["tip_path"] = [r1(p, 1) for p in tip]
        out["tip_len"] = r1(d1.sum(), 1)
        if len(tip) >= 3 and d1.mean() > 0:
            d2 = np.linalg.norm(np.diff(tip, 2, axis=0), axis=1)
            out["tip_smooth"] = r1(1 - d2.mean() / (2 * d1.mean()), 3)
            out["tip_arc"] = circle_fit(tip)
    sm_ids = H.names_to_idx(H.SMEAR_TONES)
    if all(g is not None for g in gs):
        # smear = smear-tone px outside the (1 px dilated) guide silhouette
        out["smear_px"] = [int((np.isin(i, sm_ids) & ~H.disk_op(g.mask, 1)).sum()) for i, g in zip(idxs, gs)]
        out["smear_src"] = "outside guide"
    else:
        base_sm = int(np.isin(recs[names[0]][1] if rest is None else rest["_idx"], sm_ids).sum())
        out["smear_px"] = [int(np.isin(i, sm_ids).sum()) - base_sm for i in idxs]
        out["smear_src"] = "delta vs rest"
    fl_ = []
    if anim in ("idle", "walk", "run") and out.get("head_disp_max") is not None and out["head_disp_max"] <= 1.0:
        fl_.append("stiff: head moves <= 1 px")
    if anim in ("slash", "attack") and len(names) >= 2:
        k1 = [i for i, n in enumerate(names) if n.endswith("_k1.png")]
        if k1 and out["smear_px"][k1[0]] < 15:
            fl_.append("no_smear: k1 has < 15 smear px")
    if anim == "jump" and out["stretch"] - out["squash"] < 0.08:
        fl_.append("weak squash/stretch (< 8 % height range)")
    out["flags"] = fl_
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("--guide-dir")
    ap.add_argument("--guide-map")
    ap.add_argument("--json")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    paths = H.collect(a.inputs)
    if not paths:
        sys.exit("no sprites found")
    gmap = json.load(open(a.guide_map)) if a.guide_map else None
    recs, guides, ms = {}, {}, []
    for p in paths:
        gp = H.find_guide(p, a.guide_dir, gmap)
        g = H.load_guide(gp) if gp else None
        m, idx, F = sprite_metrics(p, g)
        F["_idx"] = idx
        recs[os.path.basename(p)] = (m, idx, F)
        guides[os.path.basename(p)] = g
        ms.append(m)
    cd, area = colour_drift(ms)
    seqs = H.group_sequences(paths)
    S = []
    for (anim, d), lst in sorted(seqs.items()):
        names = [os.path.basename(p) for p in lst]
        if len(names) < 2 and anim != "turn":
            continue
        rest = recs.get(f"turn_{d}.png", (None, None, None))[2] if anim != "turn" else None
        if anim == "turn":
            continue
        S.append(seq_metrics(anim, d, names, recs, rest, guides))
    turn = [m for m in ms if m["name"].startswith("turn_")]
    dirs = {}
    if len(turn) >= 2:
        for k in ("height", "body_height", "eye_row_rel", "bow_rel", "baseline", "feet_cx"):
            v = [m[k] for m in turn if m.get(k) is not None]
            if v:
                dirs[k] = dict(min=min(v), max=max(v), spread=r1(max(v) - min(v), 3))
    rep = dict(sprites=ms, colour_drift=cd, ramp_area=area, directions=dirs, sequences=S)
    for v in recs.values():
        v[2].pop("_idx", None)
    if a.json:
        os.makedirs(os.path.dirname(os.path.abspath(a.json)), exist_ok=True)
        json.dump(rep, open(a.json, "w"), indent=1)
    # ---- print
    print(f"{'sprite':<22}{'h':>4}{'bodyH':>6}{'base':>5}{'fx':>6}{'cols':>5}{'offp':>5}{'orph':>5}{'gap':>4}"
          f"{'ntch':>5}{'spur':>5}{'dbl':>4}{'IoU':>7}{'IoUb':>7}{'eyeΔ':>6}{'bowΔ':>6}{'grdΔ':>6}")
    for m in ms:
        dr = m.get("drift", {})
        g = lambda k: f"{dr[k]['d']:>6}" if k in dr else f"{'-':>6}"
        print(f"{m['name'][:21]:<22}{m.get('height', '-'):>4}{m.get('body_height', '-'):>6}{m.get('baseline_off', '-'):>5}"
              f"{m.get('feet_cx_off', '-'):>6}{m['colours']:>5}{m['off_palette']:>5}{m['orphans']:>5}"
              f"{m['lint']['outline_gap']:>4}{m['lint']['notch']:>5}{m['lint']['spur']:>5}{m['lint']['double']:>4}"
              f"{m.get('iou', '-'):>7}{m.get('iou_body', '-'):>7}{g('eyes')}{g('bow')}{g('guard')}")
    if cd:
        print("colour drift (L1 of tone mix vs set median; worst sprite):")
        print("  " + "  ".join(f"{b} {v['max_drift']} ({v['worst'][:-4]})" for b, v in cd.items()))
    if dirs:
        print("directions (turn set) spread: " + ", ".join(f"{k} {v['spread']}" for k, v in dirs.items()))
    for s in S:
        print(f"seq {s['anim']}_{s['dir']} ({len(s['frames'])} fr): h_ratio {s['h_ratio']} w_ratio {s['w_ratio']} "
              f"squash {s['squash']} stretch {s['stretch']} flicker {s['flicker']}"
              + (f" boil {s['boil_px']}" if 'boil_px' in s else ""))
        print(f"    head disp {s.get('head_disp_max', '-')} overlap {s.get('head_overlap', '-')} lag {s.get('head_lag', '-')} | "
              f"bow disp {s.get('bow_disp_max', '-')} overlap {s.get('bow_overlap', '-')} lag {s.get('bow_lag', '-')} | "
              f"tip len {s.get('tip_len', '-')} smooth {s.get('tip_smooth', '-')} arc {s.get('tip_arc')} | smear {s['smear_px']}"
              + (f"  FLAGS {s['flags']}" if s['flags'] else ""))
    if a.json:
        print("report:", os.path.relpath(a.json, H.ROOT))


if __name__ == "__main__":
    main()
