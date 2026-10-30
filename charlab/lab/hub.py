"""charlab hub entry: REVIEW/entries/2026-10-30_charlab_<id>.json from out/<id>/summary.json, then the caller runs REVIEW/build.py.
  python hub.py SPEC.json [status] [note]"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '../..'))
REL = '../charlab/lab/out'


def main():
    spec = json.load(open(sys.argv[1])); sid = spec['id']
    status = sys.argv[2] if len(sys.argv) > 2 else 'needs-review'
    note = sys.argv[3] if len(sys.argv) > 3 else ''
    od = os.path.join(HERE, 'out', sid)
    S = json.load(open(os.path.join(od, 'summary.json')))
    rec_body = spec['body'].get('recommended', 'compact')
    rec_sizes = spec['body'].get('test_sprite_heights_px', {}).get(rec_body, [64])
    n = len(S); zig = [v['zig_max'] for v in S.values()]; cols = [v['colours_max'] for v in S.values()]
    gaps = sum(v['gap_max'] for v in S.values()); pal = max(v['palette'] for v in S.values())
    media = [dict(src=f'{REL}/{sid}/grid_SE_4x.gif', caption='walk SE: rows = tier x body preset, cols = 32/48/64/96 px, all shown at the same on-screen height (green corner = designer-recommended size)', wide=False),
             dict(src=f'{REL}/{sid}/boards.png', caption='left: SE contact frame (matched scale); right: S | SE | E contact frames at true relative size (x3)', wide=True)]
    for t in ('simple', 'medium', 'detailed'):
        for s in rec_sizes[-1:]:
            p = f'{sid}/{t}_{rec_body}/{s}/walk_4x.gif'
            if os.path.exists(os.path.join(HERE, 'out', p)):
                media.append(dict(src=f'{REL}/{p}', caption=f'{t} / {rec_body} / {s} px: S | SE | E walk, 4x'))
    e = dict(id=f'2026-10-30_charlab_{sid}', date='2026-10-30', project='charlab', kind='experiment', status=status,
             title=f'charlab: {spec.get("name", sid)} ({sid}), data-driven 3D -> pixel walk, {n} tier/body/size variants',
             question='Can one spec-driven pipeline (designer JSON -> primitive 3D body + parts -> shared walk -> locked pixel chain) give clean walk cycles across 3 complexity tiers x 3 body presets x 4 sprite heights?',
             method='charlab/lab/run.sh (model.py SDF primitives + marching cubes + automatic weights; blender_walk.py armature, shared 8-frame procedural walk, ID + normal/depth passes; pixel.py vector outline, toon-normal 2-tone cel + hair hi, occlusion shadows, interior lines at part/depth edges, eyes+brows stamped at 3D eye points, locked palette; boards.py). Deterministic. No critic calls.',
             result=f'{n} variant-sizes. Colours/frame max {max(cols)} (palette {pal}, 0 off-palette), silhouette gaps {gaps}, lamet zigzag max per frame {min(zig)}-{max(zig)}. Per-cell gates in summary.json. ' + note,
             verdict='Needs owner/reviewer look. ' + spec.get('silhouette_notes', '')[:200],
             scores={'variants': str(n), 'colours max': str(max(cols)), 'palette': str(pal), 'gaps': str(gaps), 'zig max': f'{min(zig)}-{max(zig)}'},
             media=media,
             links=[dict(href='../charlab/lab/NOTES.md', label='lab notes'), dict(href='../charlab/lab/SPEC.md', label='spec format'),
                    dict(href=f'../charlab/designs/{sid}.json', label='design spec'), dict(href=f'{REL}/{sid}/summary.json', label='gates summary')],
             next='Reviewer pass on line/shading at 1x; pick the body preset, tier and size per character.')
    p = os.path.join(ROOT, 'REVIEW/entries', f'2026-10-30_charlab_{sid}.json')
    json.dump(e, open(p, 'w'), indent=1)
    print('wrote', p)


if __name__ == '__main__':
    main()
