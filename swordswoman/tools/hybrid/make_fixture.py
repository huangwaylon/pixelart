"""Build a STANDARD-TEST-SET fixture from the round-9 render cells + their mask guides, so the tools
can be tested end-to-end before real hybrid sprites exist.  (Round-9 art is rejected as visible
art; this is test data only.)

  .venv/bin/python tools/hybrid/make_fixture.py [--out hybrid/_pipeline_test/fixture]
Writes <out>/<std name>.png and <out>/guide/<std name>_{body,id,sword}.png (+ <name>.png colour).
"""
import argparse
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hylib as H  # noqa: E402

R9 = os.path.join(H.ROOT, "renders", "model_round_9")
MAP = {**{f"turn_{d}": ("idle", d, 0) for d in H.DIRS},
       **{f"walk_SE_k{i}": ("walk", "SE", f) for i, f in enumerate((0, 1, 2, 3))},
       **{f"slash_SE_k{i}": ("slash", "SE", f) for i, f in enumerate((1, 2, 3, 5))},
       "jump_E_crouch": ("jump", "E", 0), "jump_E_apex": ("jump", "E", 3), "jump_E_land": ("jump", "E", 6)}


def guide_prefix(anim, d, f):
    return os.path.join(R9, "_masks", f"anim_{anim}_{d}_f{f}_64")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(H.ROOT, "hybrid", "_pipeline_test", "fixture"))
    a = ap.parse_args()
    os.makedirs(os.path.join(a.out, "guide"), exist_ok=True)
    for name, (anim, d, f) in MAP.items():
        src = os.path.join(R9, f"anim_{anim}_{d}_f{f}_64.png")
        shutil.copy(src, os.path.join(a.out, name + ".png"))
        gp = guide_prefix(anim, d, f)
        for s in ("_body", "_id", "_sword"):
            if os.path.exists(gp + s + ".png"):
                shutil.copy(gp + s + ".png", os.path.join(a.out, "guide", name + s + ".png"))
        shutil.copy(src, os.path.join(a.out, "guide", name + ".png"))
    print(f"fixture: {len(MAP)} sprites -> {os.path.relpath(a.out, H.ROOT)}")


if __name__ == "__main__":
    main()
