"""S5 r2: Gemini pixel-native ACTING keys (edit of the S3 cel turn sprite on an explicit grid).
Mirror space (LOCK handedness_trick): the template is the S3 turn cel sprite MIRRORED (so the katana is in her
right hand for Gemini); outputs are flipped back by snap.py.
gen.py TAG [--model M] [--mode 1x|2x] [--refpose] names...  -> hybrid/S5_pixelnative/r2/gem/<name>_<mode>_<TAG>.png"""
import sys, os, subprocess, time
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from PIL import Image
ROOT = "/Users/waylonhuang/Documents/other/pixelart/swordswoman"
OUT = f"{ROOT}/hybrid/S5_pixelnative/r2"
PY = f"{ROOT}/.venv/bin/python"
WIN = (16, 24, 112, 120)          # 96x96 window of the 128 cell
N = 96
BG = (0, 192, 0)
REF1 = os.environ.get("S5_REF1", f"{ROOT}/hybrid/S3_editchain/r1/polished")
def base_dir(name): return "E" if name.startswith("jump_E") else "SE"
def akey(name): return name
def template(name, mode):
    p = f"{OUT}/tpl/{name}_{mode}.png"
    os.makedirs(f"{OUT}/tpl", exist_ok=True)
    s = Image.open(f"{REF1}/turn_{base_dir(name)}.png").convert("RGBA").crop(WIN).transpose(Image.FLIP_LEFT_RIGHT)
    bg = Image.new("RGBA", s.size, BG + (255,)); bg.alpha_composite(s)
    n = N if mode == "1x" else 2 * N
    if mode == "2x": bg = bg.resize((n, n), Image.NEAREST)
    bg.resize((1056 if mode == "1x" else 1152, 1056 if mode == "1x" else 1152), Image.NEAREST).convert("RGB").save(p)
    return p
# mirror space: SE -> she faces DOWN-LEFT (SW); E -> she faces LEFT (W). Sword in her RIGHT hand.
FACE = {"SE": "She faces DOWN-LEFT (3/4 front view toward the lower left of the picture), exactly like image 1.",
        "E": "She faces LEFT (side profile toward the left of the picture), exactly like image 1."}
ACT = {
 "slash_SE_k0": "SLASH ANTICIPATION, fully COILED: she winds up for a big horizontal cut. Weight sunk on the BACK leg (the leg on the right of the picture), knees bent, hips pushed back, front foot light on its toe. Torso twisted away from the target, back shoulder pulled back. BOTH hands grip the katana handle up beside her back shoulder (right side of the picture), the blade pointing back and up behind her, clear of the head. Sleeves and pink ribbons pulled toward the target side. Determined glare.",
 "slash_SE_k1": "SLASH MID-SWING at full speed, a fraction of a second after the coil: hips and shoulders unwinding, she steps into a lunge toward the lower left, both arms sweeping the katana horizontally across her front at chest height, the blade pointing toward the viewer, arms and sleeves stretched along the swing. Ribbons and skirt tails whip behind (to the right). Eyes wide. Draw NO smear, NO effect: only the character and her one sword.",
 "slash_SE_k2": "SLASH IMPACT (hit-stop): a DEEP forward lunge toward the lower left, front knee bent over the toe, back leg extended with the heel up, body low and wide. Both arms fully extended, the katana level and straight out to the left at the end of the cut. Ribbons and skirt tails flung forward by the sudden stop. Fierce shouting face. No effects.",
 "slash_SE_k3": "SLASH FOLLOW-THROUGH: the blade has carried PAST the target and swings up and back over her left shoulder (left side of the picture), arms crossed over her front, chest still leaning past the hips, front foot planted, hips low. Sleeves, ribbons, bow and skirt tails OVERSHOOT forward and curl. No effects.",
 "jump_E_crouch_g": "JUMP CROUCH, STANDING ON THE GROUND: BOTH FEET FLAT ON THE GROUND at the bottom of the frame, about to spring up. Knees bent DEEP and pushed forward (left), hips dropped low behind them, torso leaning forward over the knees, both arms swung straight BACK behind her hips (to the right), the katana held low behind her pointing back, head tucked down. Short, compact, wide squashed silhouette. Strict side profile toward the left: we see only one eye.",
 "jump_E_apex_p": "JUMP APEX in strict SIDE PROFILE toward the left (we see only one eye and the side of the body): high in the air, body stretched tall and arched back slightly, legs tucked with toes pointed down, both arms flung up and back, the katana raised high above her head in her right hand, skirt and pink ribbons floating upward, open happy mouth.",
 "jump_E_crouch": "JUMP CROUCH (anticipation squash): deep knee bend with the knees pushed FORWARD (left), torso pitched forward, both arms swung BACK behind her (to the right), the katana held low behind her in her right hand pointing back, head sunk into the collar, body short and wide, skirt flared. Side profile toward the left.",
 "jump_E_apex": "JUMP APEX: high in the air at the top of the jump, body STRETCHED tall, legs tucked up under the skirt with toes pointed, BOTH arms flung up and out, the katana raised UP high in her right hand, skirt and pink ribbons floating upward, open happy face. Side profile toward the left.",
 "jump_E_land": "JUMP LANDING squash: she has just touched down, knees deeply bent, feet wide apart, body squashed short, the skirt flared out WIDE like a bell to both sides almost to the ground, arms out to the sides for balance, the katana held low out to the side, ribbons and bow still dropping. Side profile toward the left.",
 "walk_SE_k2": "WALK PASSING key: mid-stride, one foot planted under her, the other foot lifted with the knee bent and passing beside it, body upright and tall, free arm swinging, the katana held low in her right hand swinging back, ribbons and skirt tails lagging behind.",
}
def prompt(name, mode):
    n = N if mode == "1x" else 2 * N
    return (
f"EDIT image 1. Image 1 is a {n}x{n}-pixel game sprite of a chibi anime swordswoman, shown enlarged so each sprite pixel is one flat square block. "
"RE-POSE HER INTO THE ACTION BELOW as FINISHED hand-made PIXEL ART on EXACTLY THE SAME GRID: the same block size, every block one single flat colour, hard edges, no anti-aliasing, no gradients, no blur, no half blocks. "
"Keep the SAME character at the SAME scale: the head, hair dome, bun and red bow keep the same size in blocks as in image 1 (the head is about 26 blocks wide), the same costume and the same colours; only the body pose changes. "
"Exactly ONE character, ONE katana. Her feet stay near the bottom of the frame where they are in image 1. "
+ FACE[base_dir(name)] + " The katana is in her RIGHT hand (two-handed grip allowed). "
f"ACTION: {ACT[name]} "
"Make the pose very EXPRESSIVE and dynamic like images 3 and 4 (strong line of action, clear readable silhouette). Image 2 is the locked character design sheet (costume, katana, head, bow). "
"Costume: tall flared red collar, bare shoulders, red dress with detached flared bell sleeves, dark-brown buckled corset band, thin pink scarf ribbons, black shorts, pale legs, small strappy dark heels; katana with black/red wrapped handle, small crescent hook guard, straight silver blade 2 blocks wide. "
"OUTPUT ONLY the edited image 1 (one sprite on green, same framing as image 1); never copy or reproduce the reference sheets. Clean 1-block dark outline (#1a1220), 2-3 flat tones per material, light from the upper left. Flat solid green (#00c000) background everywhere else, no ground, no shadow, no text, no grid lines.")
def refs(name, refpose):
    r = [os.environ.get("S5_REF2", f"{ROOT}/hybrid/lock/lock_overview.png"), f"{ROOT}/refs/2.png", f"{ROOT}/refs/3.png"]
    if refpose:
        rp = f"{OUT}/tpl/r1pose_{name}.png"
        if not os.path.exists(rp):
            s = Image.open(f"{ROOT}/hybrid/S5_pixelnative/r1/polished/{name}.png").convert("RGBA").crop(WIN).transpose(Image.FLIP_LEFT_RIGHT)
            bg = Image.new("RGBA", s.size, BG + (255,)); bg.alpha_composite(s)
            bg.resize((768, 768), Image.NEAREST).convert("RGB").save(rp)
        r.append(rp)
    return r
def run(a):
    name, mode, tag, model, refpose = a
    os.makedirs(f"{OUT}/gem", exist_ok=True)
    out = f"{OUT}/gem/{name}_{mode}_{tag}.png"
    if os.path.exists(out): return name, "cached"
    p = prompt(name, mode)
    if refpose: p += " Image 5 is a rough earlier pixel version of this exact pose: use its pose and energy, but redraw it cleanly at the scale and in the costume of image 1."
    cmd = [PY, f"{ROOT}/tools/hybrid/s5/gem2.py", out, p, template(name, mode)] + refs(name, refpose)
    if model: cmd += ["--model", model]
    open(out[:-4] + ".prompt.txt", "w").write(p + "\nREFS: " + " ".join(cmd[4:]))
    for k in range(3):
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
        open(out[:-4] + ".log", "a").write(f"--- try {k} model={model}\n{r.stdout}\n{r.stderr[-2000:]}\n")
        if os.path.exists(out): return name, "ok"
        time.sleep(5)
    return name, "FAIL"
if __name__ == "__main__":
    a = sys.argv[1:]; tag = a.pop(0); model = None; mode = "1x"; refpose = False
    if "--model" in a: i = a.index("--model"); model = a[i + 1]; del a[i:i + 2]
    if "--mode" in a: i = a.index("--mode"); mode = a[i + 1]; del a[i:i + 2]
    if "--refpose" in a: a.remove("--refpose"); refpose = True
    names = a or list(ACT)
    with ThreadPoolExecutor(4) as ex:
        for r in ex.map(run, [(n, mode, tag, model, refpose) for n in names]): print(*r, flush=True)
