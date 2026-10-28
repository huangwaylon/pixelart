#!/bin/zsh
# snapall.sh MODE TAG
cd /Users/waylonhuang/Documents/other/pixelart/swordswoman/tools/hybrid/s5
for n in turn_S turn_SE turn_E turn_NE turn_N turn_NW turn_W turn_SW walk_SE_k0 walk_SE_k1 walk_SE_k2 walk_SE_k3 slash_SE_k0 slash_SE_k1 slash_SE_k2 slash_SE_k3 jump_E_crouch jump_E_apex jump_E_land; do
  [ -f ../../../hybrid/S5_pixelnative/r1/gem/${n}_$1_$2.png ] && ../../../.venv/bin/python snap.py $n $1 $2 | python3 -c "import json,sys;d=json.load(sys.stdin);print(d['name'],d['pitch'],round(d['vote_agree'],2),d['reg_shift'],round(d['iou_seed'],2))"
done
