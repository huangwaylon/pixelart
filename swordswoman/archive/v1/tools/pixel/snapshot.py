"""Snapshot sprite cells from a model render round into pixel/base/<anim>/ (the hand-cleanup base).

  .venv/bin/python tools/pixel/snapshot.py --round latest --anim idle [--no-hires] [--force]

* --round N|latest: 'latest' = highest renders/model_round_N that has a FULL set of
  anim_<anim>_<DIR>_f<k>_64.png (all 8 dirs, same frame count in every dir).
* copies (byte-identical) renders/model_round_N/anim_<anim>_<DIR>_f<k>_64.png -> pixel/base/<anim>/<DIR>/fKK.png
  and the object-ID pass _masks/anim_<anim>_<DIR>_f<k>_64_id.png -> pixel/base/<anim>/_id/<DIR>/fKK.png
* hi-res source per frame -> pixel/source/<anim>/<DIR>/fKK.png: copied from the round if a 512 px
  frame render exists there (anim_<anim>_<DIR>_f<k>_512.png), otherwise rendered by
  tools/pixel/render_hires.py (Blender, opens model/character.blend read-only).
* writes pixel/base/<anim>/SNAPSHOT.json (round, provenance, per-frame pixel hashes).
Re-snapshotting a different round replaces base + source; overrides are kept and px.py reports
them stale wherever the base frame hash changed.
"""
import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pxlib import DIRS, PIXEL, ROOT, file_hash, load_rgba, pixel_hash, rel  # noqa: E402

BLENDER = "/Applications/Blender.app/Contents/MacOS/Blender"


def round_frames(rdir, anim):
    out = {}
    for d in DIRS:
        ks = []
        for p in glob.glob(os.path.join(rdir, f"anim_{anim}_{d}_f*_64.png")):
            m = re.search(rf"anim_{anim}_{d}_f(\d+)_64\.png$", p)
            if m:
                ks.append(int(m.group(1)))
        out[d] = sorted(ks)
    return out


def is_full(fr, rdir=None, anim=None):
    """all 8 dirs with frames 0..n-1, and (if rdir given) the round finished rendering: checks.json and
    sheet.png (written last by sprite_post / make_sheet) exist and are not older than the cells.
    A round that another workflow is re-rendering right now is therefore skipped."""
    counts = {len(v) for v in fr.values()}
    if not (len(counts) == 1 and counts.pop() > 0 and all(v == list(range(len(v))) for v in fr.values())):
        return False
    if rdir is None:
        return True
    marks = [os.path.join(rdir, m) for m in ("checks.json", "sheet.png")]
    if not all(os.path.exists(m) for m in marks):
        return False
    newest = max(os.path.getmtime(os.path.join(rdir, f"anim_{anim}_{d}_f{k}_64.png")) for d, ks in fr.items() for k in ks)
    return min(os.path.getmtime(m) for m in marks) + 1 >= newest


def pick_round(arg, anim):
    rounds = sorted(int(m.group(1)) for p in glob.glob(os.path.join(ROOT, "renders", "model_round_*"))
                    if (m := re.search(r"model_round_(\d+)$", p)))
    if arg != "latest":
        n = int(arg)
        rd = os.path.join(ROOT, "renders", f"model_round_{n}")
        if not is_full(round_frames(rd, anim), rd, anim):
            raise SystemExit(f"model_round_{n} has no complete anim_{anim} set (8 dirs x same frames, finished render)")
        return n
    for n in reversed(rounds):
        rd = os.path.join(ROOT, "renders", f"model_round_{n}")
        if is_full(round_frames(rd, anim), rd, anim):
            return n
        print(f"skip model_round_{n}: no complete anim_{anim} set (missing frames or render in progress)")
    raise SystemExit(f"no renders/model_round_* with a full anim_{anim} set")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", default="latest")
    ap.add_argument("--anim", default="idle")
    ap.add_argument("--no-hires", action="store_true", help="skip the 512 px source renders")
    ap.add_argument("--force", action="store_true", help="re-copy even if the same round is already snapshotted")
    a = ap.parse_args()
    n = pick_round(a.round, a.anim)
    rdir = os.path.join(ROOT, "renders", f"model_round_{n}")
    fr = round_frames(rdir, a.anim)
    nfr = len(fr["S"])
    bdir = os.path.join(PIXEL, "base", a.anim)
    sdir = os.path.join(PIXEL, "source", a.anim)
    snap_p = os.path.join(bdir, "SNAPSHOT.json")
    old = json.load(open(snap_p)) if os.path.exists(snap_p) else {}
    if old.get("round") != n or a.force:
        # different round: replace base, id passes and source renders (they belong to that round)
        for p in (bdir, sdir):
            if os.path.isdir(p):
                shutil.rmtree(p)
    frames, copied = {}, 0
    for d in DIRS:
        frames[d] = {}
        os.makedirs(os.path.join(bdir, d), exist_ok=True)
        for k in fr[d]:
            src = os.path.join(rdir, f"anim_{a.anim}_{d}_f{k}_64.png")
            dst = os.path.join(bdir, d, f"f{k:02d}.png")
            if not os.path.exists(dst) or file_hash(dst) != file_hash(src):
                shutil.copyfile(src, dst)
                copied += 1
            frames[d][f"f{k:02d}"] = pixel_hash(load_rgba(dst))
            idp = os.path.join(rdir, "_masks", f"anim_{a.anim}_{d}_f{k}_64_id.png")
            if os.path.exists(idp):
                os.makedirs(os.path.join(bdir, "_id", d), exist_ok=True)
                shutil.copyfile(idp, os.path.join(bdir, "_id", d, f"f{k:02d}.png"))
            hi = os.path.join(rdir, f"anim_{a.anim}_{d}_f{k}_512.png")
            if os.path.exists(hi):
                os.makedirs(os.path.join(sdir, d), exist_ok=True)
                shutil.copyfile(hi, os.path.join(sdir, d, f"f{k:02d}.png"))
    idg = os.path.join(rdir, "_masks", "id_groups.json")
    if os.path.exists(idg):
        shutil.copyfile(idg, os.path.join(bdir, "_id", "id_groups.json"))
    blend = os.path.join(ROOT, "model", "character.blend")
    blend_mtime = os.path.getmtime(blend)
    render_mtime = max(os.path.getmtime(os.path.join(rdir, f"anim_{a.anim}_{d}_f{k}_64.png")) for d in DIRS for k in fr[d])
    hires = "skipped"
    if not a.no_hires:
        missing = [(d, k) for d in DIRS for k in fr[d] if not os.path.exists(os.path.join(sdir, d, f"f{k:02d}.png"))]
        if missing:
            if blend_mtime > render_mtime + 1:
                print(f"WARNING: model/character.blend is newer than model_round_{n}; the 512 px source renders "
                      f"show the CURRENT model, not exactly round {n}")
            t = time.time()
            r = subprocess.run([BLENDER, "-b", "--factory-startup", "-P", os.path.join(ROOT, "tools", "pixel", "render_hires.py"),
                                "--", "--anim", a.anim, "--out", rel(os.path.join(PIXEL, "source"))],
                               capture_output=True, text=True)
            ok = r.returncode == 0
            print(f"render_hires: {'ok' if ok else 'FAILED'} ({time.time() - t:.0f} s)")
            if not ok:
                print(r.stdout[-3000:], r.stderr[-3000:])
        hires = "rendered by tools/pixel/render_hires.py (model/character.blend, read-only)"
    info = {
        "anim": a.anim, "round": n, "render_dir": rel(rdir), "snapshot_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "frames_per_dir": nfr, "dirs": DIRS, "cell": [128, 128], "pivot": [64, 104],
        "source_hires": hires,
        "blend": {"path": "model/character.blend", "sha256_16": file_hash(blend),
                  "mtime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(blend_mtime)),
                  "newer_than_renders": blend_mtime > render_mtime + 1},
        "renders_mtime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(render_mtime)),
        "hash": "sha256(decoded RGBA bytes)[:16] per base frame; overrides store the hash they were made on",
        "frames": frames,
    }
    json.dump(info, open(snap_p, "w"), indent=1)
    print(f"snapshot: anim={a.anim} round={n} ({rel(rdir)}) {nfr} frames x {len(DIRS)} dirs, "
          f"{copied} files copied -> {rel(bdir)}")


if __name__ == "__main__":
    main()
