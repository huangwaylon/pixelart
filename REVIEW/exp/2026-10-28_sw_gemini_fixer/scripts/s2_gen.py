"""Step 2: new Gemini generations (gemini-3-pro-image via swordswoman/tools/gemini.py). Any python3.
  python3 s2_gen.py [a|b|c ...]   -> work/gen/<job>.png (+ _1.png when Gemini returns 2 images), work/gen/prompts.json
Jobs: a1/a2 (SE illustration -> pixel sprite), b_<pose>_<k> (illus + master + guide -> pixel pose), c_<pose>_<k> (illus + guide -> HD illustration pose)."""
import os, sys, json, subprocess
from concurrent.futures import ThreadPoolExecutor

E = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
SW = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/'
R = E + 'work/refs/'; O = E + 'work/gen/'; os.makedirs(O, exist_ok=True)
POSES = {'walk': 'walking, contact step (front leg forward, heel down, back leg behind)',
         'run': 'running, airborne stride (both feet off the ground, arms swinging)',
         'jump': 'jumping, apex of the jump (knees tucked up, arms up and out)',
         'throw': 'throwing, release (body twisted, throwing arm extended forward)'}
DESIGN = ("chibi swordswoman girl: big red ribbon bow at the back-top of the head with a small hair bun under it, "
          "dark brown bob haircut with bangs and side locks, big brown anime eyes, red short kimono dress with wide "
          "hanging sleeves and V collar, grey-lavender obi sash, black thigh-high socks, brown boots")
PIX = ("TRUE PIXEL ART game sprite: the whole figure about 96 art pixels tall from the top of the bow to the soles, "
       "every art pixel drawn as one uniform square block of 8x8 image pixels on one perfect grid, hard pixel edges, "
       "no anti-aliasing, no blur, no gradients, no dithering noise, limited palette of about 16 colours, a 1-pixel "
       "dark outline around the figure, flat cel shading with the light from the top-left")
A1 = (f"Image 1 is the design illustration of our character ({DESIGN}). Convert it into a {PIX}. Keep the design, "
      "proportions, face and colours of image 1 exactly; same 3/4 view facing front-right (SE camera, 30 degrees from above), "
      "same relaxed standing pose. Plain flat mid-grey (#808080) background, nothing else, no text.")
A2 = (f"Image 1 is the design illustration of our character ({DESIGN}). Image 2 is our approved pixel-art master of her "
      "at the target pixel scale (each art pixel = one 8x8 block, figure ~96 art pixels tall). Redraw image 1 as a "
      f"{PIX}, matching image 2's pixel scale, palette, outline and head-to-body proportions, but with the face and design "
      "of image 1. Same 3/4 front-right view and standing pose. Plain flat mid-grey (#808080) background, nothing else, no text.")
B = (f"Image 1 is the design illustration of our character ({DESIGN}); it is the authority for her identity: face, eyes, "
     "hair, bow, bun, kimono, obi, socks, boots and colours. Image 2 is our approved pixel-art master sprite of her at the "
     "target pixel scale (each art pixel = one 8x8 block, figure ~96 art pixels tall). Image 3 is a rough 3D POSE GUIDE: use "
     "it ONLY for the body pose (limb positions, lean, head tilt, feet), ignore its colours, face, hair shape and proportions. "
     "Draw the character of images 1 and 2 {pose}, in exactly the pose of image 3, as a " + PIX + ". Same pixel scale, "
     "palette, outline, head size and proportions as image 2; same 3/4 front-right camera. Plain flat mid-grey (#808080) "
     "background, nothing else, no text.")
C = (f"Image 1 is the design illustration of our character ({DESIGN}). Image 2 is a rough 3D POSE GUIDE: use it ONLY for "
     "the body pose (limb positions, lean, head tilt, feet), ignore its colours, face, hair shape and proportions. "
     "Redraw the character of image 1 {pose}, in exactly the pose of image 2, as a clean high-resolution anime character "
     "illustration in exactly the same art style as image 1: same line weight, same cel shading, same colours, same face "
     "and eyes, same head-to-body proportions, same 3/4 front-right camera (30 degrees from above). Full body, the whole "
     "figure visible, plain pure white background, no pixel art, no text, no shadow on the ground.")

JOBS = {'a1': (A1, [R + 'illus_SE.png']), 'a1b': (A1, [R + 'illus_SE.png']),
        'a2': (A2, [R + 'illus_SE.png', R + 'master_SE_8x.png']), 'a2b': (A2, [R + 'illus_SE.png', R + 'master_SE_8x.png'])}
for p, d in POSES.items():
    for k in (0, 1):
        JOBS[f'b_{p}_{k}'] = (B.format(pose=d), [R + 'illus_SE.png', R + 'master_SE_8x.png', R + f'guide_{p}.png'])
        JOBS[f'c_{p}_{k}'] = (C.format(pose=d), [R + 'illus_SE.png', R + f'guide_{p}.png'])


def go(name):
    prompt, refs = JOBS[name]
    out = O + name + '.png'
    if os.path.exists(out): return name, 'exists'
    r = subprocess.run([SW + '.venv/bin/python', SW + 'tools/gemini.py', 'image', prompt, out] + refs, cwd=SW,
                       capture_output=True, text=True)
    open(O + name + '.log', 'w').write(r.stdout[-2000:] + '\n---\n' + r.stderr[-2000:])
    return name, 'ok' if os.path.exists(out) else 'FAIL ' + (r.stdout + r.stderr)[-300:]


if __name__ == '__main__':
    sel = [j for j in JOBS if not sys.argv[1:] or any(j.startswith(s) for s in sys.argv[1:])]
    json.dump({j: {'prompt': JOBS[j][0], 'refs': JOBS[j][1]} for j in JOBS}, open(O + 'prompts.json', 'w'), indent=1)
    with ThreadPoolExecutor(6) as ex:
        for n, s in ex.map(go, sel):
            print(n, s, flush=True)
