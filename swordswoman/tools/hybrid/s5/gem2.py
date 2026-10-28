"""Gemini image call with imageConfig (square aspect) - wraps tools/gemini.py call().
gem2.py OUT.png "prompt" ref1 ref2 ... [--model M] [--aspect 1:1]"""
import sys, base64, os
sys.path.insert(0, "/Users/waylonhuang/Documents/other/pixelart/swordswoman/tools")
import gemini as G
a = sys.argv[1:]
model = G.IMAGE_MODEL; aspect = "1:1"
if "--model" in a: i = a.index("--model"); model = a[i+1]; del a[i:i+2]
if "--aspect" in a: i = a.index("--aspect"); aspect = a[i+1]; del a[i:i+2]
out, prompt, refs = a[0], a[1], a[2:]
parts = [G._part(p) for p in refs] + [{"text": prompt}]
cfg = {"responseModalities": ["TEXT", "IMAGE"], "imageConfig": {"aspectRatio": aspect}}
d = G.call(model, parts, cfg)
n = 0
for p in d["candidates"][0]["content"]["parts"]:
    if "inlineData" in p and not p.get("thought"):
        open(out, "wb").write(base64.b64decode(p["inlineData"]["data"]))   # keep the last (final) image
        n += 1
    elif p.get("text") and not p.get("thought"):
        print(p["text"][:400])
print("images", n)
if n == 0: sys.exit("no image")
