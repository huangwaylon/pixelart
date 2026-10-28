#!/bin/bash
# gen.sh out.png "prompt" ref1 ref2 ...  (run from project root)
out=$1; p=$2; shift 2
cd /Users/waylonhuang/Documents/other/pixelart/swordswoman
.venv/bin/python tools/gemini.py image "$p" "$out" "$@" > "${out%.png}.log" 2>&1; tail -1 "${out%.png}.log"
