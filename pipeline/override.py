"""Pixel override CLI for reviewers (every pixel change carries a reason).

    python -m pipeline.override --variant H1_B_final --dir S --frame 6 \
        --set 23,14,outline --set 24,14,red_1 --reason "close the gap in the beanie outline"
    python -m pipeline.override --variant H1_B_final --dir S --frame 6 --erase 30,8 --reason "..."
    python -m pipeline.override --variant H1_B_final --dir S --frame 6 --show
Frames are 1-based (as in contact sheets / pixel review sheets). Colours are palette names.
Overrides land in overrides/variants/<variant>/jump/<DIR>/<NN>.json (NN = frame-1) and are re-applied on
every rebuild; if the generated base changes underneath, QA flags them "stale".
"""
import argparse
import json
import os
import time

from .palette import Palette

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", required=True)
    ap.add_argument("--anim", default="jump")
    ap.add_argument("--dir")
    ap.add_argument("--frame", type=int, help="1-based")
    ap.add_argument("--set", action="append", default=[], help="x,y,colour_name")
    ap.add_argument("--erase", action="append", default=[], help="x,y -> transparent")
    ap.add_argument("--revert", action="append", default=[], help="x,y -> back to generated pixel")
    ap.add_argument("--approve", action="store_true", help="re-approve this frame's overrides on the current base")
    ap.add_argument("--reason", default="")
    ap.add_argument("--author", default="reviewer")
    ap.add_argument("--show", action="store_true")
    ap.add_argument("--prune", action="store_true",
                    help="after a generator change: drop override px the base now produces itself (all dirs/frames)")
    ap.add_argument("--preview", action="store_true",
                    help="render base+overrides zoom sheet to out/variants/<v>/pixelreview/fixed/ (no rebuild)")
    a = ap.parse_args()
    out = os.path.join(ROOT, "out", "variants", a.variant)
    pdir = os.path.join(out, "inputs", "data", "palettes")
    pal = Palette(os.path.join(pdir, [f for f in os.listdir(pdir) if f.endswith(".json")][0]))
    manifest = json.load(open(os.path.join(out, "manifest.json")))
    if a.prune:
        return prune(a, out, pal, manifest)
    i = a.frame - 1
    path = os.path.join(ROOT, "overrides", "variants", a.variant, a.anim, a.dir, f"{i:02d}.json")
    ov = json.load(open(path)) if os.path.exists(path) else {"px": [], "reasons": [], "note": ""}
    px = {(x, y): v for x, y, v in ov["px"]}
    if a.preview:
        import numpy as np
        from PIL import Image
        from .pixelreview import sheet_for
        meta = json.load(open(os.path.join(out, f"{a.anim}_sheet.json")))
        W, H = meta["frameSize"]
        r = meta["directions"].index(a.dir)
        base = pal.from_rgba(np.array(Image.open(os.path.join(out, "editor", f"{a.anim}_sheet_base.png")).convert("RGBA")))

        def cell(k):
            f = base[r * H:(r + 1) * H, k * W:(k + 1) * W].copy()
            p2 = os.path.join(ROOT, "overrides", "variants", a.variant, a.anim, a.dir, f"{k:02d}.json")
            if os.path.exists(p2):
                for x, y, v in json.load(open(p2))["px"]:
                    f[y, x] = v
            return f
        f = cell(i)
        prev = cell(i - 1) if i > 0 else None
        dst = os.path.join(out, "pixelreview", "fixed", f"{a.dir}_{a.frame:02d}.png")
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        sheet_for(f, pal, f"{a.dir} f{a.frame} WITH OVERRIDES ({len(px)} px)", 14, prev).save(dst)
        print("preview:", os.path.relpath(dst, ROOT))
        return
    if a.show:
        for (x, y), v in sorted(px.items()):
            print(x, y, "ERASE" if v < 0 else pal.names[v])
        for r in ov.get("reasons", []):
            print("-", r)
        return
    changed = []
    for spec in a.set:
        x, y, name = spec.split(",")
        if name not in pal.index:
            raise SystemExit(f"unknown colour {name}; valid: {', '.join(pal.names)}")
        px[(int(x), int(y))] = pal.index[name]
        changed.append([int(x), int(y), name])
    for spec in a.erase:
        x, y = (int(v) for v in spec.split(","))
        px[(x, y)] = -1
        changed.append([x, y, "ERASE"])
    for spec in a.revert:
        x, y = (int(v) for v in spec.split(","))
        px.pop((x, y), None)
        changed.append([x, y, "REVERT"])
    if not changed and a.approve:
        changed.append(["approved"])
    if not changed:
        raise SystemExit("nothing to do")
    if not a.reason:
        raise SystemExit("--reason is required: every pixel must have a purpose")
    ov["px"] = [[x, y, v] for (x, y), v in sorted(px.items())]
    ov["base_hash"] = manifest["frameHashes"][a.dir][i]
    ov.pop("needs_review", None)
    ov.setdefault("reasons", []).append({"time": time.strftime("%Y-%m-%d %H:%M"), "author": a.author,
                                         "pixels": changed, "why": a.reason})
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if ov["px"]:
        json.dump(ov, open(path, "w"), indent=1)
    elif os.path.exists(path):
        os.remove(path)
    print(f"{a.dir} f{a.frame}: {len(changed)} px recorded -> {os.path.relpath(path, ROOT)}")


def prune(a, out, pal, manifest):
    import numpy as np
    from PIL import Image
    meta = json.load(open(os.path.join(out, f"{a.anim}_sheet.json")))
    W, H = meta["frameSize"]
    base = pal.from_rgba(np.array(Image.open(os.path.join(out, "editor", f"{a.anim}_sheet_base.png")).convert("RGBA")))
    root = os.path.join(ROOT, "overrides", "variants", a.variant, a.anim)
    kept = dropped = files_removed = 0
    for r, d in enumerate(meta["directions"]):
        dd = os.path.join(root, d)
        if not os.path.isdir(dd):
            continue
        for fn in sorted(os.listdir(dd)):
            i = int(fn[:-5])
            path = os.path.join(dd, fn)
            ov = json.load(open(path))
            f = base[r * H:(r + 1) * H, i * W:(i + 1) * W]
            keep = [[x, y, v] for x, y, v in ov["px"] if f[y, x] != v]
            n_drop = len(ov["px"]) - len(keep)
            dropped += n_drop
            kept += len(keep)
            if not keep:
                os.remove(path)
                files_removed += 1
                continue
            if n_drop or ov.get("base_hash") != manifest["frameHashes"][d][i]:
                ov["reasons"].append({"time": time.strftime("%Y-%m-%d %H:%M"), "author": "prune",
                                      "pixels": [], "why": f"rebased onto new generator output; {n_drop} px now "
                                                         f"produced procedurally and removed; {len(keep)} px still differ"})
            ov["px"] = keep
            if n_drop == 0 and ov.get("base_hash") == manifest["frameHashes"][d][i]:
                pass
            else:
                ov["needs_review"] = True        # leftover px must be re-approved by a reviewer (stays stale)
            json.dump(ov, open(path, "w"), indent=1)
    print("remaining overrides are flagged needs_review / stale until a reviewer re-approves them")
    print(f"prune: {dropped} px now generated procedurally (removed), {kept} px still hand-placed, "
          f"{files_removed} override files emptied")


if __name__ == "__main__":
    main()
