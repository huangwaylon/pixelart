#!/bin/bash
R=/Users/waylonhuang/Documents/other/pixelart/swordswoman; H=$R/.scratch/hy_omni
while pgrep -f batch2b.sh >/dev/null; do sleep 20; done
cd $H; PT_ROT180=1 /usr/bin/time -l venv/bin/python -I $R/v2/hy3d/scripts/run_omni.py $H/src_omni_mlx $H/weights/Hunyuan3D-Omni $R/v2/hy3d/inputs/front.png $R/v2/hy3d/out/omni2 --tag _rot points:$R/v2/hy3d/out/mv4_s5.glb points:$R/v2/hy3d/out/mini_s5.glb
echo BATCHDONE
