"""S5 r3 (acting refs only, never shipped pixels): Gemini pixel-native ACTING keys (edit of the S3 cel turn sprite on an explicit grid).
Mirror space (LOCK handedness_trick): the template is the S3 turn cel sprite MIRRORED (so the katana is in her
right hand for Gemini); outputs are flipped back by snap.py.
gen.py TAG [--model M] [--mode 1x|2x] [--refpose] names...  -> hybrid/S5_pixelnative/r2/gem/<name>_<mode>_<TAG>.png"""
import sys, os, subprocess, time
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from PIL import Image
ROOT = "/Users/waylonhuang/Documents/other/pixelart/swordswoman"
OUT = f"{ROOT}/hybrid/S5_pixelnative/r3"
PY = f"{ROOT}/.venv/bin/python"
WIN = (16, 24, 112, 120)          # 96x96 window of the 128 cell
N = 96
BG = (0, 192, 0)
REF1 = os.environ.get("S5_REF1", f"{ROOT}/hybrid/S3_editchain/r2/polished")
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
 "slash_SE_k0": "SLASH ANTICIPATION, DEEPLY COILED like a spring: knees bent, hips dropped LOW, weight sunk on the BACK leg (right of the picture). Upper body TWISTED away from the target so we see more of her back shoulder, torso leaning back and away from the swing, the near shoulder dropped. BOTH hands grip the katana up beside her BACK shoulder (right side of the picture), elbows high, the blade pointing back and up behind her head. Her other sleeve is pulled across her chest. Head tilted back a little, fierce glare toward the target. Ribbons and sleeves trail toward the left.",
 "slash_SE_k1": "SLASH MID-SWING at full speed: hips and shoulders whipping round, she steps into a lunge toward the lower left, BOTH FISTS on the handle sweeping the katana across her front at waist height, the blade pointing down-left toward the viewer, head leaning into the swing. Her two fists and the black-red handle are clearly visible. Ribbons and skirt tails whip behind (to the right). Draw NO smear, NO effect: only the character and her one sword.",
 "slash_SE_k2": "SLASH IMPACT (hit-stop): a very WIDE, DEEP forward lunge toward the lower left: front knee strongly bent over the front foot, back leg stretched long behind with the back HEEL LIFTED off the ground, torso pitched forward, head pushed forward and down, gritted teeth. Both arms fully extended forward from the shoulders, both fists on the handle, the katana straight out level to the left at the end of the cut. Ribbons and skirt tails flung forward by the sudden stop. No effects.",
 "slash_SE_k3": "SLASH FOLLOW-THROUGH, LOW recovery: the blade has passed the target and is now held LOW and across her body, pointing down to the left about 30 degrees below horizontal, arms relaxed and extended low in front. Body settled forward and down over the bent front knee, back leg long. Pink ribbons trail BEHIND her arm in an S-curve (to the right), skirt tails still swinging. Calm focused face. No effects.",
 "jump_E_apex": "JUMP APEX in strict SIDE PROFILE toward the left (only one eye visible): high in the air, body STRETCHED tall, knees TUCKED up under the skirt, toes pointed down, both arms flung up and back, the katana raised high in her right hand, skirt hem and pink ribbons trailing downward a little, open happy mouth. Sleeves attached to the shoulders.",
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
"Make the pose very EXPRESSIVE, EXAGGERATED and dynamic like images 3 and 4 (strong line of action, clear readable silhouette). Image 2 is the locked character design sheet (costume, katana, head, bow). "
"Costume: tall flared red collar, bare shoulders, red dress with detached flared bell sleeves, dark-brown buckled corset band, thin pink scarf ribbons, black shorts, pale legs, small strappy dark heels; katana with black/red wrapped handle, small crescent hook guard, straight silver blade 2 blocks wide. "
"OUTPUT ONLY the edited image 1 (one sprite on green, same framing as image 1); never copy or reproduce the reference sheets. Clean 1-block dark outline (#1a1220), 2-3 flat tones per material, light from the upper left. Flat solid green (#00c000) background everywhere else, no ground, no shadow, no text, no grid lines.")
def refs(name, refpose):
    r = [os.environ.get("S5_REF2", f"{ROOT}/hybrid/lock/lock_overview.png"), f"{ROOT}/refs/2.png", f"{ROOT}/refs/3.png"]
    if refpose:
        rp = f"{OUT}/tpl/r2pose_{name}.png"
        if not os.path.exists(rp):
            s = Image.open(f"{ROOT}/hybrid/S5_pixelnative/r2/polished/{name}.png").convert("RGBA").crop(WIN).transpose(Image.FLIP_LEFT_RIGHT)
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
