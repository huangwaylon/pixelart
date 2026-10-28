# fxman.py : add the THROW FX (fx/maps/throw_*.txt + anchors) to v2/fx/manifest.json (group "throw") + fx/atlas_throw_48.png (other effects untouched)
import sys, json, os
FX = "/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/fx/"; sys.path.insert(0, FX + "tools"); import fxlib as F
from PIL import Image
N = ["throw_orb", "throw_trail", "throw_sparkle", "throw_pop"]
M = json.load(open(FX + "manifest.json")); rows = []; y = 0; aw = 0
for n in N:
    F.gif(FX + f"maps/{n}.txt"); fr = F.read(FX + f"maps/{n}.txt"); a = json.load(open(FX + f"maps/{n}.anchors.json"))
    ims = [F.to_img(g) for g, _ in fr]; w, h = ims[0].size
    e = dict(a); e.update(group="throw", map=f"maps/{n}.txt", gif=f"gif/{n}.gif", frames=[f"png/{n}_f{i}.png" for i in range(len(ims))], strip=f"png/{n}_strip.png",
                         ms=[ms for _, ms in fr], size=[w, h], atlas="atlas_throw_48.png", atlas_rects=[[i * (w + 1), y, w, h] for i in range(len(ims))])
    M["effects"][n] = e; rows.append((ims, y)); y += h + 1; aw = max(aw, len(ims) * (w + 1))
At = Image.new("RGBA", (aw, y), (0, 0, 0, 0))
for ims, yy in rows:
    for i, im in enumerate(ims): At.paste(im, (i * (im.width + 1), yy))
At.save(FX + "atlas_throw_48.png")
M["throw"] = {"effects": N, "note": "THROW group (v2/throw): orb held in hand.R until the release key, then spawned at frames.json ball.spawn_px with ball.vel_dir_px (v2/hy3d/frames_mocap/throw_<dir>/s48/frames.json); throw_trail + throw_sparkle on the release key at the hand (E-drawn; flip x for W; other views: rotate/skip per frames.json); orb spins (throw_orb loop) in flight; throw_pop at the landing point (game code).",
              "sequence": [{"key": "release", "fx": ["throw_trail", "throw_sparkle"], "attach": "hand"}, {"key": "release..", "fx": ["throw_orb"], "attach": "ball"}, {"event": "land", "fx": ["throw_pop"], "attach": "ball_land"}],
              "source": "hand-pixelled by Opus (fx/work/throw/), char-maps in maps/"}
json.dump(M, open(FX + "manifest.json", "w"), indent=1); print("manifest throw", N, At.size)
