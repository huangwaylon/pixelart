#!/usr/bin/env python3
"""Build SE action JSONs (actions/<act>_SE[_ns].json) from compact keyframe tables, then compose.
F(ms, label, **k): legs, aN, aF, kat=(dir,z) or None, head, bow, skirt, torso (part names),
  root=(dx,dy), tor=(dx,dy) torso offset, hd=(dx,dy) head offset, bw=(dx,dy) bow offset, fx=[(part,dx,dy,z)]
"""
import json, os, sys, subprocess
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
RIG = json.load(open(os.path.join(ROOT, 'actions', 'stand_SE.json')))['rig']

def F(ms, label, **k):
    return dict(ms=ms, label=label, **k)

def frame(f, ns):
    f = dict(f)
    if ns:
        for k in [k for k in f if k.endswith('_ns')]:
            f[k[:-3]] = f.pop(k)
    s = {}
    def put(inst, **v):
        s.setdefault(inst, {}).update(v)
    for inst, key in (('legs', 'legs'), ('head', 'head'), ('bow', 'bow'), ('skirt', 'skirt'), ('torso', 'torso'), ('armN', 'aN'), ('armF', 'aF')):
        if key in f:
            put(inst, part=f[key])
    if 'tor' in f: put('torso', off=list(f['tor']))
    if 'hd' in f: put('head', off=list(f['hd']))
    if 'bw' in f: put('bow', off=list(f['bw']))
    if 'zN' in f: put('armN', z=f['zN'])
    hide = []
    kat = f.get('kat', (13, 5))
    if ns or kat is None:
        hide.append('kat')
    else:
        put('kat', part='kat_%02d' % kat[0], at='armN.hand', z=kat[1])
        if len(kat) > 2: put('kat', off=list(kat[2]))
    fx = []
    for p in f.get('fx', []):
        part, dx, dy, z = p[:4]
        if ns and part.startswith(('smear', 'hit')):
            continue
        at = p[4] if len(p) > 4 else 'ground'
        fx.append({'part': part, 'at': at, 'off': [dx, dy], 'z': z})
    o = {'ms': f['ms'], 'label': f['label'], 'set': s, 'root': list(f.get('root', (0, 0)))}
    if hide: o['hide'] = hide
    if fx: o['fx'] = fx
    if 'shadow' in f: o['shadow'] = f['shadow']
    for k in ('ghosts', 'shake', 'px'):
        if k in f: o[k] = f[k]
    return o

def build(name, frames, ns=False, run=True, cell=(64, 64), ground=(32, 60), d='SE'):
    # d = direction: rig from actions/stand_<d>.json, parts from parts/<d lower>/ (module-level DIR = 'E' etc.)
    rig = json.loads(json.dumps(RIG if d == 'SE' else json.load(open(os.path.join(ROOT, 'actions', 'stand_%s.json' % d)))['rig']))
    rig['kat'] = {'part': 'kat_13', 'at': 'armN.hand', 'z': 5}
    act = {'name': name + ('_ns' if ns else ''), 'partdir': 'parts/' + d.lower(), 'cell': list(cell), 'ground': list(ground),
           'rig': rig, 'frames': [frame(f, ns) for f in frames]}
    p = os.path.join(ROOT, 'actions', act['name'] + '.json')
    json.dump(act, open(p, 'w'), indent=1)
    if run:
        subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'compose.py'), p], check=True)
        subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'qc.py'), act['name']])  # QC: head bbox / palette
    return p

if __name__ == '__main__':
    import importlib.util
    for mod in sys.argv[1:]:   # actions_src/<mod>.py defines ACTIONS = {name: (frames, also_ns)}
        spec = importlib.util.spec_from_file_location(mod, os.path.join(ROOT, 'actions_src', mod + '.py'))
        m = importlib.util.module_from_spec(spec); sys.modules['build'] = sys.modules[__name__]; spec.loader.exec_module(m)
        for name, (frames, ns) in m.ACTIONS.items():
            kw = dict(getattr(m, 'CELLS', {}).get(name, {}), d=getattr(m, 'DIR', 'SE'))
            build(name, frames, **kw)
            if ns: build(name, frames, ns=True, **kw)
