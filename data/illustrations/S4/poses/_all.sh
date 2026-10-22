#!/bin/sh
# rebuild every pose: cels -> pose json -> render -> lineup + sprite sheet
cd "$(dirname "$0")/../../../.." || exit 1
.venv/bin/python data/illustrations/S4/poses/_cels.py
.venv/bin/python data/illustrations/S4/poses/_build.py
for p in idle wave point hands_on_hips recoil shy shiver cheer; do
  .venv/bin/python -m pipeline.illustrate data/illustrations/S4/poses/$p.json --out 00_REVIEW/r12_illustration/poses | head -1
done
.venv/bin/python data/illustrations/S4/poses/_compose.py "$@"
