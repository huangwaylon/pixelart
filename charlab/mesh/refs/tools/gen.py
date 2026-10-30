#!/usr/bin/env python3
"""Gemini image gen with aspect ratio + size control (wraps swordswoman/tools/gemini.py call()).
usage: gen.py "prompt" out.png [--ar 16:9] [--size 2K|4K] [ref.png ...]
Logs every call to refs/raw/calls.jsonl."""
import sys, os, json, base64, time
sys.path.insert(0, "/Users/waylonhuang/Documents/other/pixelart/swordswoman/tools")
import gemini
args = sys.argv[1:]
ar, size = "1:1", "2K"
if "--ar" in args: i = args.index("--ar"); ar = args[i+1]; del args[i:i+2]
if "--size" in args: i = args.index("--size"); size = args[i+1]; del args[i:i+2]
prompt, out, refs = args[0], args[1], args[2:]
parts = [gemini._part(p, 2048) for p in refs] + [{"text": prompt}]
t = time.time()
d = gemini.call(gemini.IMAGE_MODEL, parts, {"responseModalities": ["TEXT", "IMAGE"], "imageConfig": {"aspectRatio": ar, "imageSize": size}})
n = 0
for p in d["candidates"][0]["content"]["parts"]:
    if "inlineData" in p and not p.get("thought"):
        path = out if n == 0 else out.replace(".png", f"_{n}.png")
        open(path, "wb").write(base64.b64decode(p["inlineData"]["data"])); print("wrote", path); n += 1
    elif p.get("text") and not p.get("thought"):
        print(p["text"])
log = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "raw", "calls.jsonl")
open(log, "a").write(json.dumps({"t": time.strftime("%H:%M:%S"), "out": out, "refs": refs, "ar": ar, "size": size, "prompt": prompt, "n": n, "sec": round(time.time()-t)}) + "\n")
if n == 0: sys.exit("no image returned")
