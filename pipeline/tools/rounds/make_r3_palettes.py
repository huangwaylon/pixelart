"""Generate the r3 master palette + six colourway files and a swatch board."""
import json, os, colorsys
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

MASTER = [
    ("outline", "#241628"),   # coloured near-black (plum)
    ("plum_0", "#4A2448"),    # shared deep shadow: cranberry, lavender, espresso hair, boots
    ("hair_1", "#6E3C3A"),    # brown
    ("hair_2", "#A85A3A"),    # copper
    ("skin_0", "#D07C74"),
    ("skin_1", "#EBA586"),
    ("skin_2", "#FCD6B4"),
    ("ink", "#20223E"),       # shared cool dark: navy, charcoal, blue-black hair
    ("navy_1", "#2F3A6C"),
    ("navy_2", "#4E609C"),
    ("char_1", "#45435E"),
    ("mauve", "#9C8EB2"),     # shared lilac shadow for creams / lavender light
    ("oat_1", "#D2BFA4"),
    ("oat_2", "#F2E6CE"),
    ("crn_1", "#8E2C4A"),
    ("crn_2", "#BA4A58"),
    ("red_1", "#DC3A40"),     # ACCENT
    ("red_2", "#F06A58"),     # r5 AD: was #F7845E (salmon merged with skin_1 / copper hair)
    ("gold_0", "#9C5C2E"),
    ("gold_1", "#E2A434"),    # ACCENT
    ("gold_2", "#FAD872"),
    ("orange", "#EC7032"),    # ACCENT
    ("teal_0", "#1C4C54"),
    ("teal_1", "#2A8C8E"),    # ACCENT
    ("teal_2", "#6ACBB6"),
    ("fg_1", "#3C6248"),
    ("fg_2", "#6E8C5A"),
    ("lav_1", "#6E5A92"),
    ("snow_0", "#6A7AA8"),
    ("snow_1", "#A8C0E0"),
    ("snow_2", "#DFEAF6"),
    ("snow_3", "#FFFFFF"),
]

R = dict(
    oat_knit=["mauve", "oat_1", "oat_2"], oat_cuff=["mauve", "oat_2"], oat_cuff_mid=["mauve", "oat_1"],
    red=["crn_1", "red_1", "red_2"], red2=["crn_1", "red_1"],
    gold=["gold_0", "gold_1", "gold_2"], gold2=["gold_0", "gold_1"],
    orange=["gold_0", "orange", "gold_2"], orange2=["gold_0", "orange"],
    teal=["teal_0", "teal_1", "teal_2"], teal2=["teal_0", "teal_1"],
    cranberry=["plum_0", "crn_1", "crn_2"], navy=["ink", "navy_1", "navy_2"], navy2=["ink", "navy_1"],
    charcoal=["ink", "char_1", "lav_1"], charcoal2=["ink", "char_1"],
    oatmeal=["mauve", "oat_1"], forest=["teal_0", "fg_1", "fg_2"], lavender=["plum_0", "lav_1", "mauve"],
    boots=["plum_0", "hair_1"], camel=["hair_1", "hair_2"],
    skin=["skin_0", "skin_1", "skin_2"], snow=["snow_0", "snow_1", "snow_2", "snow_3"],
)
HAIR = {
    "espresso": ["plum_0", "hair_1", "hair_2"],
    "auburn": ["hair_1", "hair_2", "red_2"],
    "blueblack": ["ink", "char_1", "navy_2"],
}

def cw(name, hair, coat, trim, hat, cuff, pom, scarf, mitten, pants, accents, notes):
    return dict(name=name, hair=hair, ramps={
        "skin": R["skin"], "hair": HAIR[hair], "hat": hat, "hatcuff": cuff, "pom": pom,
        "coat": coat, "coat_trim": trim, "scarf": scarf, "mitten": mitten,
        "pants": pants, "boots": R["boots"], "boot_cuff": R["oat_cuff"], "snow": R["snow"],
        "hair_espresso": HAIR["espresso"], "hair_auburn": HAIR["auburn"], "hair_blueblack": HAIR["blueblack"],
    }, accents=accents, notes=notes)

CWS = [
    cw("cw_cranberry", "espresso", R["cranberry"], R["oat_cuff"], R["cranberry"], R["oat_cuff_mid"], R["gold"],
       R["gold"], R["gold2"], R["navy2"], ["gold_1", "gold_2"],
       "Muted cranberry coat + matching beanie (plum shadow), cream cuffs, mustard scarf + pom accent. Warm-on-cool classic."),
    cw("cw_navy", "auburn", R["navy"], R["oat_cuff"], R["navy"], R["oat_cuff_mid"], R["red"],
       R["red"], R["red2"], R["charcoal2"], ["red_1", "red_2"],
       "Denim-navy coat + beanie, cream cuffs, red scarf + pom + mittens. Auburn hair warms the cool base."),
    cw("cw_oatmeal", "espresso", R["oatmeal"], R["camel"], R["teal"], R["teal2"], R["oat_knit"],
       R["teal"], R["teal2"], R["charcoal2"], ["teal_1", "teal_2"],
       "Oatmeal coat (2 tones, no near-white so it never merges with snow) with camel piping (keeps it off the snow), teal beanie/scarf/mittens, cream pom. "
       "Darkest hair + charcoal pants anchor the value read; lightest-coat option, weakest on snow."),
    cw("cw_forest", "auburn", R["forest"], R["oat_cuff"], R["orange"], R["oat_cuff_mid"], R["oat_knit"],
       R["orange"], R["orange2"], R["navy2"], ["orange", "gold_2"],
       "Forest-green coat (teal-black shadow), orange beanie + scarf + mittens, cream pom and cuffs. Outdoorsy."),
    cw("cw_lavender", "auburn", R["lavender"], R["oat_cuff"], R["gold"], R["oat_cuff_mid"], R["oat_knit"],
       R["gold"], R["gold2"], R["charcoal2"], ["gold_1", "gold_2"],
       "Plum/lavender coat, warm-yellow beanie + scarf (complementary to violet), cream pom."),
    cw("cw_charcoal", "espresso", R["charcoal"], R["oat_cuff"], R["red"], R["oat_cuff_mid"], R["oat_knit"],
       R["red"], R["red2"], R["navy2"], ["red_1", "red_2"],
       "HERO. Cool charcoal coat, saturated red beanie + scarf + mittens, cream pom + cuffs (pom contrasts the dome). Max value contrast "
       "on snow; red is the only saturated hue so the eye goes straight to head and scarf tails."),
]

SPECIAL = {"outline": "outline", "eye": "outline", "catchlight": "snow_3", "mouth": "crn_1",
           "blush": "red_2", "ground_shadow": "snow_1"}
BANDS = {"2": [-0.10], "3": [-0.45, 0.85], "4": [-0.3, 0.4, 0.85]}
MATERIAL_BANDS = {"hair": [-0.35, 0.55], "hat": [-0.45, 0.94], "hatcuff": [-0.5]}  # r5 AD: smaller hair shine / hat highlight, fewer cuff shadow specks

def hex2rgb(h): return tuple(int(h[i:i+2], 16) for i in (1, 3, 5))
def luma(rgb): return int(0.299*rgb[0] + 0.587*rgb[1] + 0.114*rgb[2])

def main():
    colors = [{"name": n, "hex": h} for n, h in MASTER]
    assert len(colors) <= 32 and len({n for n, _ in MASTER}) == len(MASTER)
    os.makedirs(os.path.join(ROOT, "data/palettes"), exist_ok=True)
    for c in CWS:
        out = {"name": "frost_r3_" + c["name"][3:], "colors": colors, "ramps": c["ramps"], "bands": BANDS,
               "special": SPECIAL, "material_bands": MATERIAL_BANDS, "accents": c["accents"], "notes": c["notes"] + f" Default hair: {c['hair']}; "
               "alternates in hair_espresso / hair_auburn / hair_blueblack."}
        with open(os.path.join(ROOT, "data/palettes", c["name"] + ".json"), "w") as f:
            json.dump(out, f, indent=2)
    board()

def board():
    pal = dict(MASTER)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", 12)
        big = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", 16)
    except Exception:
        font = big = ImageFont.load_default()
    S = 40
    mats = ["hair", "hat", "hatcuff", "pom", "scarf", "coat", "coat_trim", "mitten", "pants", "boots", "boot_cuff", "skin"]
    W = 1500
    H = 70 + 2*(S+30) + 40 + len(CWS)*(S+50) + 20
    img = Image.new("RGB", (W, H*2 - 0), (40, 36, 48))
    d = ImageDraw.Draw(img)
    def panel(y0, grey):
        def col(h):
            rgb = hex2rgb(h)
            if grey: v = luma(rgb); return (v, v, v)
            return rgb
        d.text((10, y0+8), "r3 master palette (32)" + (" -- GREYSCALE" if grey else ""), fill=(240, 240, 240), font=big)
        y = y0 + 36
        for i, (n, h) in enumerate(MASTER):
            x = 10 + (i % 16) * (S + 52); yy = y + (i // 16) * (S + 30)
            d.rectangle([x, yy, x+S+40, yy+S], fill=col(h), outline=(20, 20, 20))
            d.text((x, yy+S+2), n, fill=(220, 220, 220), font=font)
        y += 2*(S+30) + 10
        for c in CWS:
            d.text((10, y), c["name"] + "  accents: " + ",".join(c["accents"]), fill=(240, 240, 240), font=font)
            # snow strip behind
            d.rectangle([10, y+16, W-10, y+16+S], fill=col("#DFEAF6"))
            x = 16
            for m in mats:
                r = c["ramps"][m]
                w = 3*20
                for j, cn in enumerate(r):
                    d.rectangle([x + j*20, y+20, x + j*20 + 19, y+12+S], fill=col(pal[cn]))
                d.rectangle([x-1, y+19, x + len(r)*20, y+13+S], outline=col("#241628"))
                d.text((x, y+18+S), m, fill=(200, 200, 200), font=font)
                x += w + 50
            y += S + 50
        return y
    y = panel(0, False)
    y2 = panel(y + 10, True)
    img = img.crop((0, 0, W, y2 + 10))
    os.makedirs(os.path.join(ROOT, "docs/review"), exist_ok=True)
    img.save(os.path.join(ROOT, "docs/review/r3_palette_board.png"))

if __name__ == "__main__":
    main()
