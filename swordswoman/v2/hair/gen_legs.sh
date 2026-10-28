#!/bin/bash
# gen_legs.sh variant view : legs/<variant>_<view>.png edited from turnE_final/<view>.png
cd /Users/waylonhuang/Documents/other/pixelart/swordswoman; L=$1; v=$2; o=v2/hair/legs/${L}_$v.png; [ -f $o ] && exit 0
case $L in
a) C="add BLACK THIGH-HIGH SOCKS: opaque black socks from the boots up to the MIDDLE OF THE THIGHS (well above the knees), ending in a neat band with a thin red trim, so a CLEARLY VISIBLE band of bare thigh skin (about a hand-width tall, the classic zettai ryouiki) shows between the sock tops and the skirt hem; the knees are covered; keep the dark short boots";;
b) C="add DARK OPAQUE TIGHTS: both legs fully covered in opaque very dark charcoal/black tights from the skirt hem down into the boots, with a subtle soft sheen on the knees and shins; keep the dark short boots";;
c) C="add black CALF SOCKS (knee socks): the black socks cover ONLY the calves, from the boot tops up to a top band with a thin red stripe that sits clearly BELOW the knee; the round kneecaps are BARE and visible, and the whole thighs are bare skin; the black covers less than half the leg length above the boots; keep the dark short boots";;
d) C="make the red kimono skirt LONGER, reaching just above the knees, in soft pleats, AND add opaque black thigh-high socks under it so only the knees area shows a tiny gap or no skin; keep the dark short boots";;
esac
P="Edit this image: keep EVERYTHING the same (same view and direction, pose, face, hair, bow, red kimono top, obi, sleeves, colours, slim proportions, flat cel style). Only change the legs: $C. The legs stay slim and graceful. Cute, feminine Japanese-anime look. NO sword. Plain white background, no text."
for k in 1 2 3; do .venv/bin/python tools/gemini.py image "$P" $o v2/hair/turnE_final/$v.png > /dev/null 2>&1; [ -f $o ] && { rm -f ${o%.png}_1.png; exit 0; }; sleep 30; done; echo FAIL $L $v
