"""Publish a set of built clips for the user (viewed on GitHub) into 00_REVIEW/<round>/.

    python -m pipeline.publish --variant S4_halfup_bow --round r11_actions --clips idle walk run ...
Each clip gets <round>/<clip>/ with: <clip>_8dir.gif, <clip>_8dir_slow.gif, <clip>_contact_sheet.png,
<clip>_sheet.png + .json (engine deliverable), qa_report.md; plus <round>/README.md with a summary table.
"""
import argparse
import json
import os
import shutil

from .build import ROOT


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", required=True)
    ap.add_argument("--round", required=True)
    ap.add_argument("--clips", nargs="+", required=True)
    ap.add_argument("--title", default="")
    ap.add_argument("--notes", default="")
    a = ap.parse_args()
    dst_root = os.path.join(ROOT, "00_REVIEW", a.round)
    os.makedirs(dst_root, exist_ok=True)
    rows = []
    for clip in a.clips:
        src = os.path.join(ROOT, "out", "variants", a.variant if clip == "jump" else f"{a.variant}__{clip}")
        if not os.path.isdir(src):
            rows.append(f"| {clip} | not built | | | |")
            continue
        dst = os.path.join(dst_root, clip)
        os.makedirs(dst, exist_ok=True)
        pairs = [(f"preview/{clip}_8dir.gif", f"{clip}_8dir.gif"),
                 (f"preview/slowmo/{clip}_8dir_slow.gif", f"{clip}_8dir_slow.gif"),
                 (f"preview/{clip}_contact_sheet.png", f"{clip}_contact_sheet.png"),
                 (f"{clip}_sheet.png", f"{clip}_sheet.png"), (f"{clip}_sheet.json", f"{clip}_sheet.json"),
                 ("qa_report.md", "qa_report.md")]
        for s, d in pairs:
            if os.path.exists(os.path.join(src, s)):
                shutil.copy2(os.path.join(src, s), os.path.join(dst, d))
        meta = json.load(open(os.path.join(src, f"{clip}_sheet.json")))
        qa = json.load(open(os.path.join(src, "qa_report.json")))
        ev = sorted({e for f in meta["frames"] for e in f.get("events", [])})
        rows.append(f"| [{clip}]({clip}/{clip}_8dir.gif) | {len(meta['frames'])} f / {meta['totalMs']} ms"
                    f"{' loop' if meta.get('loop') else ''} | {len(meta['directions'])} | {', '.join(ev) or '-'} | "
                    f"{'PASS' if qa['pass'] else 'FAIL'} |")
    readme = [f"# {a.title or a.round}", "", a.notes, "",
              "| Clip (click for 8-dir GIF) | Frames / time | Dirs | Events | QA |", "|---|---|---|---|---|"] + rows + [
              "", "Each folder has `<clip>_8dir_slow.gif` (slow motion), `<clip>_contact_sheet.png` (every frame x direction),",
              "and the engine deliverable `<clip>_sheet.png` + `<clip>_sheet.json` (rows = directions, cols = frames)."]
    open(os.path.join(dst_root, "README.md"), "w").write("\n".join(readme) + "\n")
    print("published", dst_root)


if __name__ == "__main__":
    main()
