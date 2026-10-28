"""Sparse, reasoned per-frame pixel overrides on top of the snapshotted base frames.

  px.py set    --anim idle --dir S --frame 3 30,41,outline 31,41,red_2 --reason "close the cuff outline"
  px.py erase  --anim idle --dir S --frame 3 44,60 45,60 --reason "remove 1px spur on the skirt hem"
  px.py line   --anim idle --dir S --frame 3 40,50,44,54,outline --reason "straighten the sleeve edge"
  px.py revert --anim idle --dir S --frame 3 30,41 [--all] --reason "..."   (drop override px -> base)
  px.py show   --anim idle [--dir S] [--frame 3]      list edits (+ stale / conflict status)
  px.py stale  --anim idle                            report overrides whose base frame changed
  px.py approve --anim idle --dir S --frame 3 --reason "checked on round 7 base"  re-bind to current base
  px.py apply  --anim idle [--dir S] [--frame 3]      write pixel/clean/<anim>/<DIR>/fNN.png = base + overrides
  px.py copy   --anim idle --dir S --frame 3 --to 4,5 --reason "same fix, held pose"   copy edits to frames

Frames are 0-based (fNN.png).  Colours: palette names from docs/palette.json (outline, skin_0..2,
hair_0..2, red_0..3, leather_1..2, dark_1, steel_0..2, eye_0..1, pink_0..1, purple_0; aliases
leather_0/dark_0 = outline; '#hex' accepted only if in the palette) or 'clear'.
Override file pixel/overrides/<anim>/<DIR>/fNN.json is a JSON list, one entry per pixel:
  {"x", "y", "color", "reason", "author", "time", "base_hash", "base_color"}
base_hash = pixel hash of the base frame the edit was made on; base_color = the base pixel it
replaced.  Stale = base_hash differs from the current base (re-snapshot).  Conflict = the base pixel
under the edit changed too (the fix may be obsolete or wrong now).  Every change also appends to
pixel/overrides/<anim>/HISTORY.jsonl.
"""
import argparse
import json
import os
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pxlib import (CELL, PIXEL, Palette, base_hash, compose, dirs_of, frame_path, frames_of,  # noqa: E402
                   load_overrides, load_rgba, rel, save_overrides, save_rgba)


def bresenham(x0, y0, x1, y1):
    pts = []
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        pts.append((x0, y0))
        if x0 == x1 and y0 == y1:
            return pts
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def xy(s):
    x, y = (int(v) for v in s.split(",")[:2])
    if not (0 <= x < CELL and 0 <= y < CELL):
        raise SystemExit(f"({x},{y}) outside the {CELL}x{CELL} cell")
    return x, y


def log(anim, entry):
    p = os.path.join(PIXEL, "overrides", anim, "HISTORY.jsonl")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "a") as f:
        f.write(json.dumps(entry) + "\n")


def status_of(anim, d, k, edits, pal):
    """-> (stale bool, list of conflicting edits)"""
    cur = base_hash(anim, d, k)
    bp = frame_path("base", anim, d, k)
    base = load_rgba(bp) if os.path.exists(bp) else None
    stale = any(e.get("base_hash") != cur for e in edits)
    conflicts = []
    if base is not None:
        for e in edits:
            if e.get("base_hash") != cur and pal.name_of(base[e["y"], e["x"]]) != e.get("base_color"):
                conflicts.append(e)
    return stale, conflicts


def edit_frame(a, pal, d, k, ops):
    """ops: list of (x, y, colour-name or None for revert)."""
    if not a.reason:
        raise SystemExit("--reason is required: every pixel must have a purpose")
    bp = frame_path("base", a.anim, d, k)
    if not os.path.exists(bp):
        raise SystemExit(f"no base frame {rel(bp)} (run snapshot.py first)")
    base = load_rgba(bp)
    h = base_hash(a.anim, d, k)
    edits = {(e["x"], e["y"]): e for e in load_overrides(a.anim, d, k)}
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    changed = []
    for x, y, col in ops:
        if col is None:
            if edits.pop((x, y), None) is not None:
                changed.append([x, y, "REVERT"])
            continue
        bcol = pal.name_of(base[y, x]) or "OFF_PALETTE"
        if col == bcol:            # identical to base: no override needed (drop an existing one)
            if edits.pop((x, y), None) is not None:
                changed.append([x, y, "REVERT(=base)"])
            continue
        edits[(x, y)] = {"x": x, "y": y, "color": col, "reason": a.reason, "author": a.author, "time": now,
                         "base_hash": h, "base_color": bcol}
        changed.append([x, y, col])
    p = save_overrides(a.anim, d, k, list(edits.values()))
    log(a.anim, {"time": now, "cmd": a.cmd, "dir": d, "frame": k, "author": a.author, "reason": a.reason, "pixels": changed})
    print(f"{d} f{k:02d}: {len(changed)} px changed, {len(edits)} override px total -> {rel(p)}")
    return changed


def targets(a, need_frame=False):
    dirs = [a.dir] if a.dir else dirs_of(a.anim)
    out = []
    for d in dirs:
        ks = [a.frame] if a.frame is not None else frames_of(a.anim, d)
        out += [(d, k) for k in ks]
    if need_frame and (a.dir is None or a.frame is None):
        raise SystemExit("--dir and --frame are required")
    return out


def cmd_apply(a, pal):
    n_copy = n_edit = 0
    for d, k in targets(a):
        bp = frame_path("base", a.anim, d, k)
        cp = frame_path("clean", a.anim, d, k)
        edits = load_overrides(a.anim, d, k)
        os.makedirs(os.path.dirname(cp), exist_ok=True)
        if not edits:
            shutil.copyfile(bp, cp)          # zero overrides -> byte-identical to base
            n_copy += 1
        else:
            stale, conf = status_of(a.anim, d, k, edits, pal)
            save_rgba(compose(load_rgba(bp), edits, pal), cp)
            n_edit += 1
            if stale:
                print(f"WARNING {d} f{k:02d}: overrides are STALE (base changed){f', {len(conf)} conflicting px' if conf else ''}")
    # remove clean frames that no longer have a base (e.g. after a re-snapshot with fewer frames)
    if a.frame is None:
        for d in ([a.dir] if a.dir else dirs_of(a.anim, "clean")):
            for k in set(frames_of(a.anim, d, "clean")) - set(frames_of(a.anim, d)):
                os.remove(frame_path("clean", a.anim, d, k))
    print(f"apply {a.anim}: {n_edit} frames with overrides, {n_copy} copied unchanged -> {rel(os.path.join(PIXEL, 'clean', a.anim))}")


def cmd_show(a, pal):
    tot = 0
    for d, k in targets(a):
        edits = load_overrides(a.anim, d, k)
        if not edits:
            continue
        stale, conf = status_of(a.anim, d, k, edits, pal)
        tot += len(edits)
        cset = {(e["x"], e["y"]) for e in conf}
        print(f"== {d} f{k:02d}: {len(edits)} px{'  [STALE]' if stale else ''}{f'  [{len(conf)} CONFLICT]' if conf else ''}")
        for e in edits:
            flag = " !conflict" if (e["x"], e["y"]) in cset else ""
            print(f"  ({e['x']:3d},{e['y']:3d}) {e.get('base_color', '?'):>10} -> {e['color']:<10} {e['author']}: {e['reason']}{flag}")
    print(f"total override px: {tot}")


def cmd_stale(a, pal):
    n = 0
    for d, k in targets(a):
        edits = load_overrides(a.anim, d, k)
        if not edits:
            continue
        stale, conf = status_of(a.anim, d, k, edits, pal)
        if stale:
            n += 1
            print(f"STALE {d} f{k:02d}: {len(edits)} px, {len(conf)} conflicting (base pixel under the edit changed)")
    print(f"{n} stale override files" if n else "no stale overrides")
    return 1 if n else 0


def cmd_approve(a, pal):
    if not a.reason:
        raise SystemExit("--reason is required")
    for d, k in targets(a, need_frame=False):
        edits = load_overrides(a.anim, d, k)
        if not edits:
            continue
        base = load_rgba(frame_path("base", a.anim, d, k))
        h = base_hash(a.anim, d, k)
        keep = []
        for e in edits:
            e["base_hash"] = h
            e["base_color"] = pal.name_of(base[e["y"], e["x"]]) or "OFF_PALETTE"
            if e["base_color"] != e["color"]:
                keep.append(e)          # base now produces this pixel itself -> drop
        save_overrides(a.anim, d, k, keep)
        log(a.anim, {"time": time.strftime("%Y-%m-%d %H:%M:%S"), "cmd": "approve", "dir": d, "frame": k,
                     "author": a.author, "reason": a.reason, "kept": len(keep), "dropped": len(edits) - len(keep)})
        print(f"approved {d} f{k:02d}: {len(keep)} px kept, {len(edits) - len(keep)} now equal to base (dropped)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["set", "erase", "line", "revert", "show", "stale", "approve", "apply", "copy"])
    ap.add_argument("specs", nargs="*", help="set: x,y,colour  erase/revert: x,y  line: x0,y0,x1,y1,colour")
    ap.add_argument("--anim", default="idle")
    ap.add_argument("--dir")
    ap.add_argument("--frame", type=int, help="0-based (fNN)")
    ap.add_argument("--to", help="copy: comma list of target frames")
    ap.add_argument("--all", action="store_true", help="revert: every override px of the frame")
    ap.add_argument("--reason", default="")
    ap.add_argument("--author", default=os.environ.get("PX_AUTHOR", "artist"))
    a = ap.parse_args()
    pal = Palette()
    if a.cmd == "apply":
        return cmd_apply(a, pal)
    if a.cmd == "show":
        return cmd_show(a, pal)
    if a.cmd == "stale":
        return cmd_stale(a, pal)
    if a.cmd == "approve":
        return cmd_approve(a, pal)
    if a.dir is None or a.frame is None:
        raise SystemExit("--dir and --frame are required")
    ops = []
    try:
        if a.cmd == "set":
            for s in a.specs:
                x, y = xy(s)
                ops.append((x, y, pal.resolve(s.split(",", 2)[2])))
        elif a.cmd == "erase":
            ops = [(*xy(s), "clear") for s in a.specs]
        elif a.cmd == "line":
            for s in a.specs:
                p = s.split(",")
                x0, y0 = xy(",".join(p[0:2]))
                x1, y1 = xy(",".join(p[2:4]))
                col = pal.resolve(p[4])
                ops += [(x, y, col) for x, y in bresenham(x0, y0, x1, y1)]
        elif a.cmd == "revert":
            if a.all:
                ops = [(e["x"], e["y"], None) for e in load_overrides(a.anim, a.dir, a.frame)]
            else:
                ops = [(*xy(s), None) for s in a.specs]
        elif a.cmd == "copy":
            src = load_overrides(a.anim, a.dir, a.frame)
            if not a.to:
                raise SystemExit("--to is required")
            if not a.reason:
                raise SystemExit("--reason is required")
            for k in (int(v) for v in a.to.split(",")):
                ops = [(e["x"], e["y"], e["color"]) for e in src]
                edit_frame(a, pal, a.dir, k, ops)
            return
    except ValueError as e:
        raise SystemExit(str(e))
    if not ops:
        raise SystemExit("nothing to do")
    edit_frame(a, pal, a.dir, a.frame, ops)


if __name__ == "__main__":
    sys.exit(main())
