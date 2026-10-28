"""Consistency summary across poses. Any python with numpy. -> work/summary.json + printed markdown tables"""
import json, os, numpy as np
E = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
GH = json.load(open(E + 'work/proc_gh/scale.json'))
HN = json.load(open(E + 'work/proc_hn/scale.json'))
IDH = {d['name']: d for d in json.load(open(E + 'work/proc_hn/identity.json'))}
CH = {'b': {'walk': 0, 'run': 1, 'jump': 1, 'throw': 1}, 'c': {'walk': 0, 'run': 1, 'jump': 0, 'throw': 1}}
OFF = {'b_walk_1', 'b_jump_0'}  # Gemini returned a 3-figure sheet in a different chibi style (off-model)
out = {}
print('| sample | rig-scale head (hair px, master 35) | head ratio | head-matched h | palL1 | matL1 | colours | orph % |')
print('|---|---|---|---|---|---|---|---|')
for n in sorted(GH):
    kind = n[0]; i = IDH[n + ('_L2' if kind == 'b' else '')]
    r = {'gh_hair': GH[n]['hair_h'], 'ratio': round(GH[n]['hair_h'] / 35, 2), 'hn_h': HN[n]['h'], 'guide_h': GH[n]['guide_h'],
         'palL1': i['palL1'], 'matL1': i['matL1'], 'n_colors': i['n_colors'], 'orph_pct': i['orph_pct'], 'offmodel_sheet': n in OFF}
    out[n] = r
    print(f"| {n}{' (sheet, off-model)' if n in OFF else ''} | {r['gh_hair']} | {r['ratio']} | {r['hn_h']} (guide {r['guide_h']}) | {r['palL1']} | {r['matL1']} | {r['n_colors']} | {r['orph_pct']} |")
print()
agg = {}
for kind in 'bc':
    for sel, names in (('chosen', [f'{kind}_{p}_{k}' for p, k in CH[kind].items()]),
                       ('all_on_model', [n for n in GH if n[0] == kind and n not in OFF])):
        a = {k: [out[n][k] for n in names] for k in ('ratio', 'palL1', 'orph_pct', 'n_colors')}
        agg[f'{kind}_{sel}'] = {k: [round(float(np.mean(v)), 3), round(float(np.std(v)), 3), round(float(min(v)), 2), round(float(max(v)), 2)] for k, v in a.items()}
print('| set | head ratio mean ± sd [min..max] | palL1 mean ± sd | orph % mean |')
print('|---|---|---|---|')
for k, v in agg.items():
    print(f"| {k} | {v['ratio'][0]} ± {v['ratio'][1]} [{v['ratio'][2]}..{v['ratio'][3]}] | {v['palL1'][0]} ± {v['palL1'][1]} | {v['orph_pct'][0]} |")
json.dump({'per': out, 'agg': agg, 'chosen': CH, 'offmodel': sorted(OFF)}, open(E + 'work/summary.json', 'w'), indent=1)
