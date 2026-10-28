# prep.py IN.png OUT.png  -> rembg isnet-anime, crop, pad to square (15%), 768 RGBA
import sys
from PIL import Image
from rembg import remove, new_session
sess = new_session("isnet-anime")
for src, out in zip(sys.argv[1::2], sys.argv[2::2]):
    rgba = remove(Image.open(src).convert("RGB"), session=sess)
    a = rgba.split()[3].point(lambda v: 0 if v < 20 else v); rgba.putalpha(a)
    rgba = rgba.crop(rgba.getbbox()); s = int(max(rgba.size) * 1.15)
    c = Image.new("RGBA", (s, s), (0, 0, 0, 0)); c.paste(rgba, ((s - rgba.width) // 2, (s - rgba.height) // 2), rgba)
    c.resize((768, 768), Image.LANCZOS).save(out); print("prep", out)
