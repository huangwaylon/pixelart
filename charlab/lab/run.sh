#!/bin/bash
# charlab one-command runner:  run.sh <spec.json> [tiers] [bodies] [sizes]
#   tiers  default simple,medium,detailed     bodies default chibi,compact,slim     sizes default 32,48,64,96
# e.g.  ./run.sh ../designs/shorthair.json simple compact 48,64
# Builds every tier x body variant in parallel (-j 6; override with CHARLAB_JOBS), then the boards.
# Outputs: out/<id>/<tier>_<body>/<size>/ (walk_4x.gif, walk_strip1x.png, sheet_4x.png, frames, gates.json),
#          out/<id>/grid_SE_4x.gif, out/<id>/boards.png, out/<id>/summary.json.  Intermediates: work/<id>/ (gitignored).
set -euo pipefail
cd "$(dirname "$0")"
[ $# -ge 1 ] || { sed -n 2,8p "$0"; exit 1; }
spec=$(cd "$(dirname "$1")" && pwd)/$(basename "$1")
exec /Users/waylonhuang/Documents/other/pixelart/.models/pixtools/venv/bin/python batch.py "$spec" \
  "${2:-simple,medium,detailed}" "${3:-chibi,compact,slim}" "${4:-32,48,64,96}" -j"${CHARLAB_JOBS:-6}"
