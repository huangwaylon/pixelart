"""Burn correction notes onto the canonical concept sheets so modelers can't copy mirrored details."""
from PIL import Image, ImageDraw, ImageFont
F = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
C = (0, 190, 255); OK = (40, 200, 90)
def annotate(src, dst, title, marks, footer):
    im = Image.open(src).convert("RGB"); w, h = im.size
    band_top, band_bot = 60, 26 + 22*len(footer)
    out = Image.new("RGB", (w, h + band_top + band_bot), "white"); out.paste(im, (0, band_top))
    d = ImageDraw.Draw(out); f = ImageFont.truetype(F, 17); fb = ImageFont.truetype(F, 22)
    d.rectangle([0, 0, w, band_top-4], fill=(20, 20, 30))
    d.text((10, 8), title, fill=(255, 230, 0), font=fb)
    d.text((10, 34), "Cyan = WRONG, do not copy.  Green = correct target.  Text spec: docs/design_bible.md section 0", fill="white", font=f)
    for n, (box, label, color, cross, lpos) in enumerate(marks, 1):
        x0, y0, x1, y1 = box; y0 += band_top; y1 += band_top
        d.rectangle([x0, y0, x1, y1], outline=color, width=4)
        if cross:
            d.line([x0, y0, x1, y1], fill=color, width=4); d.line([x0, y1, x1, y0], fill=color, width=4)
        lx, ly = lpos[0], lpos[1] + band_top
        tw = d.textlength(f"{n}. {label}", font=f)
        d.rectangle([lx-3, ly-2, lx+tw+3, ly+20], fill=color)
        d.text((lx, ly), f"{n}. {label}", fill="black", font=f)
    y = h + band_top + 6
    for line in footer:
        d.text((10, y), line, fill="black", font=f); y += 22
    out.save(dst); print(dst, out.size)

annotate("concept/chibi_turnaround_v6.png", "concept/chibi_turnaround_v6_annotated.png",
 "TURNAROUND v6 - USE FOR PROPORTIONS ONLY (handedness MIRRORED)",
 [((0, 680, 125, 840), "katana in her RIGHT hand", C, True, (4, 850)),
  ((330, 640, 420, 760), "katana goes HERE (her LEFT)", OK, False, (290, 900)),
  ((295, 555, 345, 640), "ornament on her LEFT arm", C, True, (225, 520)),
  ((125, 600, 175, 650), "ornament goes HERE (her RIGHT)", OK, False, (10, 575)),
  ((80, 690, 120, 730), "plain guard: needs kagi hook", C, False, (4, 875)),
  ((390, 640, 700, 770), "SHEATHED sword - no sheath exists", C, True, (400, 780)),
  ((515, 550, 575, 640), "her LEFT arm: no ornament", C, False, (440, 490)),
  ((728, 550, 768, 610), "ornament on her LEFT arm", C, True, (700, 520)),
  ((905, 690, 1024, 840), "katana in her RIGHT hand", C, True, (770, 900))],
 ["Correct: katana in LEFT hand (front: viewer-right; back: viewer-left), drawn, blade down/back, angled OUT from silhouette.",
  "Correct: flower + purple lacing + ribbon on her RIGHT upper arm. Guard = straight bar + crescent kagi hook (refs/1.png).",
  "Already correct here: right-hip pouch, LEFT thigh strap, LEFT front slit, open funnel collar. Bow must stay <= 0.85 H wide."])

annotate("concept/chibi_iso_v5.png", "concept/chibi_iso_v5_annotated.png",
 "ISO v5 (SE) - USE FOR CAMERA/MASSING ONLY",
 [((65, 765, 385, 1045), "katana in her RIGHT hand", C, True, (60, 1050)),
  ((330, 770, 380, 815), "plain guard: needs kagi", C, False, (60, 735)),
  ((600, 700, 700, 800), "katana goes HERE (her LEFT)", OK, False, (600, 810)),
  ((345, 535, 575, 625), "SCARF collar: must be stiff open funnel", C, False, (500, 455)),
  ((580, 555, 625, 650), "ornament on her LEFT arm", C, True, (630, 600)),
  ((390, 560, 450, 640), "ornament -> her RIGHT arm", OK, False, (230, 640)),
  ((430, 820, 570, 940), "legs too cylindrical: taper", C, False, (580, 880)),
  ((440, 650, 600, 750), "corset: needs 3 straps+plate+tabs", C, False, (620, 680))],
 ["Correct: katana LEFT hand + kagi hook; RIGHT-arm ornament; stiff flared collar open in a V framing the jaw;",
  "3-strap harness + central plate + 2 hanging tabs + round right-hip pouch; face strands reach the jaw; tapered legs.",
  "Ground shadow here is fine as a concept, but in-game it is an engine layer on 2:1 math (see bible section 5)."])
