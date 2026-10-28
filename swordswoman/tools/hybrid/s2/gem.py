#!/usr/bin/env python3
"""Gemini image call with imageConfig (aspect ratio + size), reusing tools/gemini.py call().
  gem.py "prompt" out.png ref1 ref2 ... [--model M] [--aspect 4:3] [--size 2K] [--maxside 2048]
"""
import base64, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import gemini  # tools/gemini.py

args = sys.argv[1:]
def opt(name, default):
    if name in args:
        i = args.index(name); v = args[i + 1]; del args[i:i + 2]; return v
    return default
model = opt("--model", gemini.IMAGE_MODEL)
aspect = opt("--aspect", None)
size = opt("--size", "2K")
maxside = int(opt("--maxside", "2048"))
prompt, out, refs = args[0], args[1], args[2:]
parts = [gemini._part(p, max_side=maxside) for p in refs] + [{"text": prompt}]
cfg = {"responseModalities": ["TEXT", "IMAGE"]}
ic = {}
if aspect: ic["aspectRatio"] = aspect
if size and "flash" not in model: ic["imageSize"] = size
if ic: cfg["imageConfig"] = ic
d = gemini.call(model, parts, cfg)
n = 0
for p in d["candidates"][0]["content"]["parts"]:
    if "inlineData" in p and not p.get("thought"):
        path = out if n == 0 else out.replace(".png", f"_{n}.png")
        open(path, "wb").write(base64.b64decode(p["inlineData"]["data"]))
        print("wrote", path); n += 1
    elif p.get("text") and not p.get("thought"):
        print(p["text"][:300])
if n == 0:
    sys.exit("no image returned")
