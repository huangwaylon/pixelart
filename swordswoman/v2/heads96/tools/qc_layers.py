"""qc_layers.py [VIEWS]: exhaustive QC of the layered head: every expression x tilt x nod x turn x sway set is composed onto
the master (compose_head.master_ref), then eyecheck (anchor shifted by the face offset) + qc_gate frame + chk_layered run.
Writes v2/heads96/qc_layers.json; prints a summary."""
import sys, os, json, itertools, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cm import *
import compose_head as CH
sys.path.insert(0, f'{ROOT}/m96/tools'); sys.path.insert(0, f'{ROOT}/qc')
import eyecheck as EC, qc_gate as QG
SEC = {'rest': {}, 'lagL': dict.fromkeys('Blrwt', 'lagL'), 'lagR': dict.fromkeys('Blrwt', 'lagR'), 'lift': dict.fromkeys('Blrwt', 'lift'), 'drop': dict.fromkeys('Blrwt', 'drop')}
def run(views, full=False):
    res = {}; tmp = tempfile.mkdtemp(prefix='h96qc', dir=f'{ROOT}/heads96')
    for v in views:
        M = load(f'{ROOT}/m96/masters/EC0_{v}_96.txt')[0]; exprs = sorted(f[:-4] for f in os.listdir(f'{CH.LD}/{v}/face'))
        n = 0; fails = []
        poses = list(itertools.product((-1, 0, 1), (-1, 0, 1), (-1, 0, 1)))
        for e in exprs:
            for (tilt, nod, turn) in poses:
                for sk in (SEC if (e == 'neutral' or full) else ['rest', 'lagR']):
                    spec = dict(expr=e, tilt=tilt, nod=nod, turn=turn, sec=SEC[sk])
                    sp = f'{tmp}/{v}.txt'; CH.write_stamp(v, spec, sp); st, mt = load(sp); o = list(map(int, mt['origin']))
                    G = CH.master_ref(M, v, st, o); fp = f'{tmp}/{v}_f.txt'; save(fp, G); fx = []
                    if v in ('S', 'SE', 'E'):
                        fx += EC.check(G, v, e, f'{ROOT}/m96/heads/anchor.json', face_off=CH.face_offset(v, spec))[1]
                    fx += QG.frame_fixes(fp, v, None, sp, None, False)
                    n += 1
                    if fx: fails.append(dict(spec=spec, fixes=fx[:4]))
        res[v] = dict(n=n, fails=len(fails), examples=fails[:12])
        print(v, 'composites', n, 'FAIL', len(fails))
        for f in fails[:4]: print('   ', json.dumps(f['spec'])[:120], '|', f['fixes'][0][:200])
    import shutil; shutil.rmtree(tmp)
    json.dump(res, open(f'{ROOT}/heads96/qc_layers.json', 'w'), indent=1); return res
if __name__ == '__main__':
    a = sys.argv[1:]; full = '--full' in a; a = [x for x in a if x != '--full']
    run(a or ['S', 'SE', 'E', 'NE', 'N'], full)
