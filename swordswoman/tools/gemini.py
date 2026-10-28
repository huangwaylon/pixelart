#!/usr/bin/env python3
"""Gemini helper (via Apple Floodgate, mTLS).

Critique / text (vision):
  .venv/bin/python tools/gemini.py ask "prompt" img1.png img2.png ... [--model gemini-3.1-pro-preview] [--json]
Image generation / editing (input images optional, used as references):
  .venv/bin/python tools/gemini.py image "prompt" out.png [ref1.png ...]

Text answer goes to stdout. Exit code != 0 on failure.
"""
import base64, json, mimetypes, os, subprocess, sys, tempfile, time

BASE = "https://floodgate.g.apple.com/api/gemini/v1/publishers/google/models"
CRITIC_MODEL = "gemini-4-argon"  # Gemini 4 Argon (same model Apple Pi CLI uses: apple-gemini/gemini-4-argon)
IMAGE_MODEL = "gemini-3-pro-image"


def _part(path, max_side=1536):
    # Downscale big images to keep requests small (uses sips on macOS).
    mime = mimetypes.guess_type(path)[0] or "image/png"
    src = path
    try:
        from PIL import Image
        im = Image.open(path)
        if max(im.size) > max_side:
            im.thumbnail((max_side, max_side))
            tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name
            im.save(tmp)
            src, mime = tmp, "image/png"
    except Exception:
        pass
    with open(src, "rb") as f:
        return {"inlineData": {"mimeType": mime, "data": base64.b64encode(f.read()).decode()}}


def call(model, parts, gen_config=None, retries=4):
    body = {"contents": [{"role": "user", "parts": parts}]}
    if gen_config:
        body["generationConfig"] = gen_config
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(body, f)
        body_path = f.name
    url = f"{BASE}/{model}:generateContent"
    last = None
    for attempt in range(retries):
        out = subprocess.run(
            ["curl", "-s", "-m", "600",
             "--cert", os.environ["CLAUDE_TLS_CERT_PATH"], "--key", os.environ["CLAUDE_TLS_KEY_PATH"],
             url, "-H", "Authorization: Bearer floodgate", "-H", "Content-Type: application/json",
             "--data-binary", f"@{body_path}"],
            capture_output=True, text=True)
        try:
            d = json.loads(out.stdout)
        except Exception:
            last = out.stdout[:500] + out.stderr[:500]
            time.sleep(5 * (attempt + 1))
            continue
        if "candidates" in d:
            return d
        last = json.dumps(d)[:800]
        time.sleep(5 * (attempt + 1))
    sys.exit(f"gemini call failed: {last}")


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    mode, prompt, rest = sys.argv[1], sys.argv[2], sys.argv[3:]
    model = None
    want_json = False
    if "--model" in rest:
        i = rest.index("--model"); model = rest[i + 1]; del rest[i:i + 2]
    if "--json" in rest:
        rest.remove("--json"); want_json = True

    if mode == "ask":
        parts = [_part(p) for p in rest] + [{"text": prompt}]
        cfg = {"temperature": 0.4}
        if want_json:
            cfg["responseMimeType"] = "application/json"
        d = call(model or CRITIC_MODEL, parts, cfg)
        print("".join(p.get("text", "") for p in d["candidates"][0]["content"]["parts"] if not p.get("thought")))
    elif mode == "image":
        out_path, refs = rest[0], rest[1:]
        parts = [_part(p) for p in refs] + [{"text": prompt}]
        d = call(model or IMAGE_MODEL, parts, {"responseModalities": ["TEXT", "IMAGE"]})
        n = 0
        for p in d["candidates"][0]["content"]["parts"]:
            if "inlineData" in p:
                path = out_path if n == 0 else out_path.replace(".png", f"_{n}.png")
                with open(path, "wb") as f:
                    f.write(base64.b64decode(p["inlineData"]["data"]))
                print("wrote", path)
                n += 1
            elif p.get("text") and not p.get("thought"):
                print(p["text"])
        if n == 0:
            sys.exit("no image returned")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
