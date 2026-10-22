"""Local editor server (stdlib only).

    python -m pipeline.server            # http://127.0.0.1:8777/editor/

Static files are served from the project root. API:
    GET  /api/state?anim=jump                     sheet metadata, palette, qa, all overrides, feedback
    PUT  /api/override?anim=&dir=&frame=          body {"px": [[x,y,idx],...], "note": ""}  (empty px deletes)
    POST /api/build?anim=jump                     runs the pipeline, returns log + exit code
    POST /api/feedback                            body {"anim","dir","frame","author","note"}
"""
import json
import os
import subprocess
import sys
import time
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIRS = {"S", "SE", "E", "NE", "N", "NW", "W", "SW"}


def _read_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path) as f:
        return json.load(f)


def _palette_for(out_dir):
    """Palette snapshot used by that build (variants use data/palettes/<colourway>.json)."""
    pdir = os.path.join(out_dir, "inputs", "data", "palettes")
    if os.path.isdir(pdir):
        files = [f for f in os.listdir(pdir) if f.endswith(".json")]
        if files:
            return _read_json(os.path.join(pdir, files[0]))
    return _read_json(os.path.join(ROOT, "data", "palette.json"))


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def _json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        n = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(n) or b"{}")

    def _variant(self, q):
        v = q.get("variant", [""])[0]
        if v and not v.replace("_", "").isalnum():
            raise ValueError("bad variant name")
        return v or None

    def _out(self, anim, variant):
        return os.path.join(ROOT, "out", anim) if not variant else os.path.join(ROOT, "out", "variants", variant)

    def _ovdir(self, anim, variant):
        return os.path.join(ROOT, "overrides", anim) if not variant else os.path.join(ROOT, "overrides", "variants", variant, anim)

    def _anim(self, q):
        anim = q.get("anim", ["jump"])[0]
        if not anim.replace("_", "").isalnum():
            raise ValueError("bad anim name")
        return anim

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/":
            self.send_response(302)
            self.send_header("Location", "/editor/")
            self.end_headers()
            return
        if u.path == "/api/state":
            q = parse_qs(u.query)
            anim, variant = self._anim(q), self._variant(q)
            out = self._out(anim, variant)
            rel = os.path.relpath(out, ROOT)
            overrides = {}
            od = self._ovdir(anim, variant)
            if os.path.isdir(od):
                for d in sorted(os.listdir(od)):
                    for fn in sorted(os.listdir(os.path.join(od, d))):
                        if fn.endswith(".json"):
                            overrides[f"{d}/{int(fn[:-5])}"] = _read_json(os.path.join(od, d, fn))
            fb_path = os.path.join(ROOT, "feedback", f"{variant + '_' if variant else ''}{anim}.jsonl")
            feedback = []
            if os.path.exists(fb_path):
                with open(fb_path) as f:
                    feedback = [json.loads(line) for line in f if line.strip()]
            return self._json({
                "sheet": _read_json(os.path.join(out, f"{anim}_sheet.json")),
                "manifest": _read_json(os.path.join(out, "manifest.json")),
                "qa": _read_json(os.path.join(out, "qa_report.json")),
                "palette": _palette_for(out),
                "overrides": overrides, "feedback": feedback,
                "baseSheet": f"/{rel}/editor/{anim}_sheet_base.png",
                "shadowStrip": f"/{rel}/{anim}_shadow.png",
                "variants": sorted(f[:-5] for f in os.listdir(os.path.join(ROOT, "data", "variants")) if f.endswith(".json")),
            })
        return super().do_GET()

    def do_PUT(self):
        u = urlparse(self.path)
        if u.path != "/api/override":
            return self._json({"error": "not found"}, 404)
        q = parse_qs(u.query)
        anim, variant, d, frame = self._anim(q), self._variant(q), q["dir"][0], int(q["frame"][0])
        if d not in DIRS:
            return self._json({"error": "bad dir"}, 400)
        body = self._body()
        path = os.path.join(self._ovdir(anim, variant), d, f"{frame:02d}.json")
        px = sorted({(int(x), int(y)): int(v) for x, y, v in body.get("px", [])}.items())
        if not px:
            if os.path.exists(path):
                os.remove(path)
            return self._json({"ok": True, "deleted": True})
        manifest = _read_json(os.path.join(self._out(anim, variant), "manifest.json"), {})
        old = _read_json(path, {})
        base_hash = manifest.get("frameHashes", {}).get(d, [None] * (frame + 1))[frame]
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump({"base_hash": base_hash, "note": body.get("note", old.get("note", "")),
                       "reasons": old.get("reasons", []),          # per-pixel rationale from reviews is preserved
                       "px": [[x, y, v] for (x, y), v in px]}, f, indent=1)
        return self._json({"ok": True, "pixels": len(px), "base_hash": base_hash})

    def do_POST(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        if u.path == "/api/build":
            anim, variant = self._anim(q), self._variant(q)
            t = time.time()
            cmd = [sys.executable, "-m", "pipeline.build", "--anim", anim] + (["--variant", variant] if variant else [])
            r = subprocess.run(cmd, cwd=ROOT,
                               capture_output=True, text=True)
            return self._json({"code": r.returncode, "log": r.stdout + r.stderr, "seconds": round(time.time() - t, 1)})
        if u.path == "/api/feedback":
            b = self._body()
            anim = b.get("anim", "jump")
            variant = b.get("variant") or ""
            entry = {"time": time.strftime("%Y-%m-%d %H:%M"), "anim": anim, "dir": b.get("dir"),
                     "frame": b.get("frame"), "author": b.get("author", "reviewer"), "note": b.get("note", ""),
                     "status": "open"}
            os.makedirs(os.path.join(ROOT, "feedback"), exist_ok=True)
            with open(os.path.join(ROOT, "feedback", f"{variant + '_' if variant else ''}{anim}.jsonl"), "a") as f:
                f.write(json.dumps(entry) + "\n")
            return self._json({"ok": True})
        return self._json({"error": "not found"}, 404)

    def log_message(self, fmt, *args):
        if "/api/" in (args[0] if args else ""):
            sys.stderr.write("%s\n" % (fmt % args))


def main():
    port = int(os.environ.get("PORT", 8777))
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"editor: http://127.0.0.1:{port}/editor/")
    srv.serve_forever()


if __name__ == "__main__":
    main()
