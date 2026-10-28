"""Local pixel-override editor server (stdlib only), port of pixelart/pipeline/server.py.

  .venv/bin/python tools/pixel/server.py [--port 8778]      ->  http://127.0.0.1:8778/

Static: /           -> tools/pixel/editor/index.html  (editor UI)
        /editor/*   -> tools/pixel/editor/
        /pixel/*    -> pixel/  (base / source / clean frames; read-only over HTTP)
API:
  GET  /api/state?anim=idle                 dirs, frames, palette (locked), overrides (+ _stale), lint, ms, snapshot
  PUT  /api/override?anim=&dir=&frame=      body {"px": [[x, y, "palette_name"|"clear"], ...], "reason", "author"}
                                            full override set for the frame; unchanged px keep their old
                                            reason/author, new/changed px get this reason (required)
  POST /api/apply?anim=idle                 px.py apply + lint.py (src clean); returns log
  POST /api/feedback                        body {"anim","dir","frame","author","note"} -> pixel/feedback/<anim>.jsonl
Writes only under pixel/overrides, pixel/clean, pixel/lint, pixel/feedback.
"""
import argparse
import json
import os
import subprocess
import sys
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pxlib import (CELL, DIRS, PIVOT, PIXEL, ROOT, Palette, anim_ms, base_hash, dirs_of, frame_path,  # noqa: E402
                   frames_of, load_overrides, load_rgba, save_overrides, snapshot_info)
from px import log  # noqa: E402

EDITOR = os.path.join(HERE, "editor")
PAL = Palette()


def anims():
    p = os.path.join(PIXEL, "base")
    return sorted(a for a in os.listdir(p) if os.path.isdir(os.path.join(p, a))) if os.path.isdir(p) else []


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def translate_path(self, path):
        p = unquote(urlparse(path).path)
        if p in ("/", "/index.html"):
            return os.path.join(EDITOR, "index.html")
        for prefix, base in (("/editor/", EDITOR), ("/pixel/", PIXEL)):
            if p.startswith(prefix):
                full = os.path.realpath(os.path.join(base, p[len(prefix):]))
                if full.startswith(os.path.realpath(base) + os.sep):
                    return full
        return os.path.join(EDITOR, "__404__")

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

    def _anim(self, q):
        a = q.get("anim", ["idle"])[0]
        if not a.replace("_", "").isalnum():
            raise ValueError("bad anim name")
        return a

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/api/state":
            try:
                anim = self._anim(parse_qs(u.query))
            except ValueError as e:
                return self._json({"error": str(e)}, 400)
            dirs = dirs_of(anim)
            frames = {d: frames_of(anim, d) for d in dirs}
            ov = {}
            for d in dirs:
                for k in frames[d]:
                    e = load_overrides(anim, d, k)
                    if e:
                        h = base_hash(anim, d, k)
                        for x in e:
                            x["_stale"] = x.get("base_hash") != h
                        ov[f"{d}/{k}"] = e
            lp = os.path.join(PIXEL, "lint", f"{anim}_clean.json")
            if not os.path.exists(lp):
                lp = os.path.join(PIXEL, "lint", f"{anim}_base.json")
            fbp = os.path.join(PIXEL, "feedback", f"{anim}.jsonl")
            fb = [json.loads(l) for l in open(fbp) if l.strip()] if os.path.exists(fbp) else []
            n = len(frames[dirs[0]]) if dirs else 0
            return self._json({"anims": anims() or [anim], "anim": anim, "dirs": dirs, "frames": frames, "W": CELL, "H": CELL,
                               "pivot": list(PIVOT), "palette": PAL.json(), "overrides": ov,
                               "lint": json.load(open(lp)) if os.path.exists(lp) else None,
                               "ms": anim_ms(anim, n)[0] if n else [], "snapshot": {k: v for k, v in snapshot_info(anim).items() if k != "frames"},
                               "feedback": fb})
        if u.path.startswith("/api/"):
            return self._json({"error": "not found"}, 404)
        return super().do_GET()

    def do_PUT(self):
        u = urlparse(self.path)
        if u.path != "/api/override":
            return self._json({"error": "not found"}, 404)
        q = parse_qs(u.query)
        try:
            anim, d, k = self._anim(q), q["dir"][0], int(q["frame"][0])
        except (KeyError, ValueError) as e:
            return self._json({"error": f"bad query: {e}"}, 400)
        if d not in DIRS or k not in frames_of(anim, d):
            return self._json({"error": "bad dir/frame"}, 400)
        body = self._body()
        reason, author = (body.get("reason") or "").strip(), body.get("author") or "artist"
        base = load_rgba(frame_path("base", anim, d, k))
        h = base_hash(anim, d, k)
        old = {(e["x"], e["y"]): e for e in load_overrides(anim, d, k)}
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        new, changed = {}, []
        try:
            for x, y, col in body.get("px", []):
                x, y = int(x), int(y)
                if not (0 <= x < CELL and 0 <= y < CELL):
                    raise ValueError(f"({x},{y}) outside the cell")
                col = PAL.resolve(str(col))
                bcol = PAL.name_of(base[y, x]) or "OFF_PALETTE"
                if col == bcol:
                    continue
                o = old.get((x, y))
                if o and o["color"] == col:
                    new[(x, y)] = o
                    continue
                new[(x, y)] = {"x": x, "y": y, "color": col, "reason": reason, "author": author, "time": now,
                               "base_hash": h, "base_color": bcol}
                changed.append([x, y, col])
        except ValueError as e:
            return self._json({"error": str(e)}, 400)
        removed = [[x, y, "REVERT"] for (x, y) in old if (x, y) not in new]
        if changed and not reason:
            return self._json({"error": "reason is required: every pixel must have a purpose"}, 400)
        save_overrides(anim, d, k, list(new.values()))
        if changed or removed:
            log(anim, {"time": now, "cmd": "editor", "dir": d, "frame": k, "author": author, "reason": reason,
                       "pixels": changed + removed})
        edits = load_overrides(anim, d, k)
        for e in edits:
            e["_stale"] = e.get("base_hash") != h
        return self._json({"ok": True, "pixels": len(new), "changed": len(changed), "removed": len(removed), "edits": edits})

    def do_POST(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        if u.path == "/api/apply":
            anim = self._anim(q)
            t = time.time()
            py = sys.executable
            log_ = ""
            code = 0
            for cmd in ([py, os.path.join(HERE, "px.py"), "apply", "--anim", anim],
                        [py, os.path.join(HERE, "lint.py"), "--anim", anim, "--src", "clean"]):
                r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
                log_ += r.stdout + r.stderr
                code = code or r.returncode
            return self._json({"code": code, "log": log_, "seconds": round(time.time() - t, 1)})
        if u.path == "/api/feedback":
            b = self._body()
            anim = b.get("anim", "idle")
            if not str(anim).replace("_", "").isalnum():
                return self._json({"error": "bad anim"}, 400)
            entry = {"time": time.strftime("%Y-%m-%d %H:%M"), "anim": anim, "dir": b.get("dir"), "frame": b.get("frame"),
                     "author": b.get("author", "reviewer"), "note": b.get("note", ""), "status": "open"}
            os.makedirs(os.path.join(PIXEL, "feedback"), exist_ok=True)
            with open(os.path.join(PIXEL, "feedback", f"{anim}.jsonl"), "a") as f:
                f.write(json.dumps(entry) + "\n")
            return self._json({"ok": True})
        return self._json({"error": "not found"}, 404)

    def log_message(self, fmt, *args):
        if "/api/" in str(args[0] if args else ""):
            sys.stderr.write("%s\n" % (fmt % args))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8778)))
    a = ap.parse_args()
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    print(f"pixel editor: http://127.0.0.1:{a.port}/", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
