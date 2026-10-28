"""qa_final.py DIR_PV DIR_FULL STEM STRESS_JSON OUT [cols] : stress QA sheet = smooth preview (top) + pixel 4x + pixel 1x strip (bottom), labelled"""
import sys, json
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_hires3d/scripts'); import hx
from PIL import Image, ImageDraw
dpv, dfu, stem, sj, out = sys.argv[1:6]; cols = int(sys.argv[6]) if len(sys.argv) > 6 else 6
M = json.load(open(sj)); n = len(M['frames']); keys = [f.get('key', str(i)) for i, f in enumerate(M['frames'])]
def lab(ims, title):
    w, h = ims[0].size; rows = (len(ims) + cols - 1) // cols; S = Image.new('RGB', (w * cols, (h + 16) * rows + 18), (40, 40, 44)); d = ImageDraw.Draw(S)
    d.text((4, 3), title, fill=(255, 255, 255))
    for i, im in enumerate(ims):
        x, y = (i % cols) * w, 18 + (i // cols) * (h + 16); S.paste(im.convert('RGB'), (x, y + 16)); d.text((x + 4, y + 2), keys[i], fill=(240, 230, 120))
    return S
pv = []
for i in range(n):
    a = Image.open(f'{dpv}/{stem}_f{i:02d}_pv.png').convert('RGBA'); k = a.size[0] // 192; a = a.crop((50 * k, 40 * k, 145 * k, 160 * k)).resize((380, 480), Image.LANCZOS)
    bg = Image.new('RGBA', a.size, (110, 110, 110, 255)); bg.alpha_composite(a); pv.append(bg)
p4 = [hx.render(hx.read_grid(f'{dfu}/{stem}_rq/f{i:02d}.txt'), 4).crop((88, 32, 468, 512)) for i in range(n)]
p1 = Image.new('RGB', (100 * n, 110), (110, 110, 110))
for i in range(n): p1.paste(hx.render(hx.read_grid(f'{dfu}/{stem}_rq/f{i:02d}.txt'), 1).crop((14, 12, 114, 122)), (i * 100, 0))
A = lab(pv, 'smooth preview (6x, head shows the projected master texture)'); Bm = lab(p4, 'pixel chain (R QA chain: round-1 chain + projected master head), 4x')
C = Image.new('RGB', (max(A.width, p1.width * 2), A.height + Bm.height + 2 * p1.height + 20), (40, 40, 44))
C.paste(A, (0, 0)); C.paste(Bm, (0, A.height)); ImageDraw.Draw(C).text((4, A.height + Bm.height + 3), 'pixel 1x (shown 2x, nearest)', fill=(255, 255, 255))
C.paste(p1.resize((p1.width * 2, p1.height * 2), Image.NEAREST), (0, A.height + Bm.height + 18)); C.save(out); print(out, C.size)
