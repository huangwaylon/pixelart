# motion_sheet.py FRAMES_ROOT OUT_DIR [size=s32] : motion_<dir>.png (one strip per action + onion) + <act>_<dir>.gif copies for critics
import sys, os, shutil
from PIL import Image, ImageDraw
root, out = sys.argv[1:3]; sz = sys.argv[3] if len(sys.argv) > 3 else "s32"; os.makedirs(out, exist_ok=True)
acts = ["idle", "walk", "run", "jump", "dash", "slash"]
for dn in ("SE", "E"):
    rows, ons = [], []
    for a in acts:
        d = os.path.join(root, f"{a}_{dn}", sz)
        if not os.path.exists(d): continue
        sh = Image.open(os.path.join(d, "sheet.png")); rows.append((a, sh.crop((0, 0, sh.width, 18 + 192))))
        ons.append(Image.open(os.path.join(d, "onion.png")).resize((192, 192), Image.NEAREST))
        shutil.copy(os.path.join(d, "preview.gif"), os.path.join(out, f"{a}_{dn}.gif"))
    W = max(r.width for _, r in rows) + 200; H = sum(r.height for _, r in rows)
    s = Image.new("RGB", (W, H), (40, 40, 40)); dr = ImageDraw.Draw(s); y = 0
    for (a, r), o in zip(rows, ons): s.paste(r, (0, y)); s.paste(o, (W - 196, y + 10)); dr.text((4, y + 4), a, fill="yellow"); y += r.height
    s.save(os.path.join(out, f"motion_{dn}.png")); print(out, dn, s.size)
