#!/bin/zsh
# assemble.sh POLDIR PXDIR R : copy the polished STANDARD TEST SET into R/sprite and R/hires
POL=$1; PX=$2; R=$3
mkdir -p $R/sprite $R/hires
rm -f $R/sprite/*.png $R/hires/*.png
for n in turn_S turn_SE turn_E turn_NE turn_N turn_NW turn_W turn_SW walk_SE_k0 walk_SE_k1 walk_SE_k2 walk_SE_k3 slash_SE_k0 slash_SE_k1 slash_SE_k2 slash_SE_k3 jump_E_crouch jump_E_apex jump_E_land; do
  cp $POL/${n}.png $R/sprite/${n}.png
  cp $PX/${n}_hires.png $R/sprite/${n}_hires.png
  cp $PX/${n}_hires.png $R/hires/${n}.png
done
ls $R/sprite | wc -l
