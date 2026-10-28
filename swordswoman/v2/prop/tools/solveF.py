# iterate PROPORTIONS_F multipliers so m3.py (design 2D-equivalent front measures) hits the template means
import json, subprocess, copy, sys
R = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/'; PY = '/Users/waylonhuang/Documents/other/pixelart/.models/hunyuan/venv/bin/python'
E = json.load(open(R + 'design/PROPORTIONS_E.json')); T = json.load(open(R + 'prop/template.json'))
tg = dict(heads=T['derived']['heads_tall']['mean'], sh=T['derived']['shoulder_over_headw']['mean'], waist=T['derived']['waist_over_headw']['mean'],
          hem=T['derived']['hip_over_headw']['mean'], legs=round(1 - T['rows']['hem']['mean'], 3), neck=T['derived']['neck_gap_chin_to_shoulder']['mean'])
sp = {k: copy.deepcopy(E[k]) for k in ['head', 'neck', 'torso', 'skirt', 'arms', 'legs', 'hands', 'boots', 'eyes']}
sp['arms']['thickness'] = 0.75   # slimmer sleeves/arms: the hanging sleeves were the main 2D bloat
def meas(s):
    json.dump(s, open(R + 'prop/specF_tmp.json', 'w'))
    subprocess.run([PY, '-I', R + 'hy3d/scripts/reproportion.py', R + 'prop/specF_tmp.json', R + 'hy3d/partsAB4f', R + 'hy3d/best/skel.txt', R + 'prop/rigF_tmp'], capture_output=True, check=True)
    o = subprocess.run([PY, '-I', R + 'design/tools_e/m3.py', R + 'prop/rigF_tmp'], capture_output=True, text=True, check=True).stdout
    return json.loads(o.strip().splitlines()[-1])
for it in range(8):
    m = meas(sp); print(it, {k: m[k] for k in tg}, flush=True)
    if all(abs(m[k] - tg[k]) <= 0.006 for k in tg): break
    sp['head']['scale'] = round(sp['head']['scale'] * (m['heads'] / tg['heads']) ** 0.9, 4)
    sp['arms']['shoulder_x'] = round(sp['arms']['shoulder_x'] * tg['sh'] / m['sh'], 4)
    sp['torso']['waist'] = round(sp['torso']['waist'] * tg['waist'] / m['waist'], 4)
    sp['skirt']['width'] = round(sp['skirt']['width'] * tg['hem'] / m['hem'], 4)
    sp['legs']['length'] = round(sp['legs']['length'] * (tg['legs'] / m['legs']) ** 1.6, 4)
    sp['neck']['extra'] = round(sp['neck']['extra'] + (tg['neck'] - m['neck']) * 2.7, 4)
json.dump({'sp': sp, 'm': m, 'tg': tg}, open(R + 'prop/solveF_last.json', 'w'))
