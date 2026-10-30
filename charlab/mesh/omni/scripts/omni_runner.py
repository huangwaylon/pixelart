"""Persistent Hunyuan3D-Omni runner (MLX fork, wraps .models/hy_omni/src_omni_mlx without modifying it).

Usage: venv/bin/python -I omni_runner.py JOBS.jsonl OUT_DIR [--variant ema]
JOBS.jsonl: one JSON object per line:
  {"name": "astronaut_base", "image": "...png", "control": "bbox:0.54,1,0.45" | "pose:FILE.txt" | "points:FILE.(glb|ply|npy)"
   | "voxel:FILE.(glb|npy)", "steps": 50, "guidance": 4.5, "octree": 384, "seed": 1234, "dino": 518}
Re-reads the job file after every job (so jobs can be appended while it runs); skips names whose .glb exists.
Stops when no pending job is left (or a file OUT_DIR/STOP exists). Writes OUT_DIR/<name>.glb (raw MC mesh, no cleanup)
and appends a row to OUT_DIR/runs.jsonl.
Point/voxel inputs are given in the glb frame (Y up, faces +Z) = Omni's control frame (same as pose); they are
normalised to [-0.98, 0.98] like the upstream demo. "rot": true rotates 180 deg about Y (the swordswoman 2mv glb
needed it; the charlab lab meshes do not: rot=true gave a back-to-front astronaut, run astronaut_point_rot180).
"""
import argparse, os, sys, time, json, resource

HY = '/Users/waylonhuang/Documents/other/pixelart/.models/hy_omni'
ap = argparse.ArgumentParser()
ap.add_argument('jobs'); ap.add_argument('out')
ap.add_argument('--variant', default='ema')
ap.add_argument('--device', default='mlx')
a = ap.parse_args()

os.environ.setdefault('PYTORCH_ENABLE_MPS_FALLBACK', '1')
os.environ.setdefault('HF_HUB_OFFLINE', '1')
sys.path.insert(0, f'{HY}/src_omni_mlx')
import numpy as np, torch, trimesh
from hy3dshape.pipelines import Hunyuan3DOmniSiTFlowMatchingPipeline
from hy3dshape.runtime import make_generator, resolve_device, resolve_dtype
import mlx.core as mx

os.makedirs(a.out, exist_ok=True)
t0 = time.time()
dev = 'mlx' if a.device == 'mlx' else resolve_device(a.device)
dtype = resolve_dtype('auto', resolve_device('mps'))
pipe = Hunyuan3DOmniSiTFlowMatchingPipeline.from_pretrained(f'{HY}/weights/Hunyuan3D-Omni', variant=a.variant, device=dev, dtype=dtype)
load_s = time.time() - t0
print(f'LOAD {load_s:.1f}s', flush=True)
pdev, pdt = pipe.device, pipe.dtype


def load_points(path, n=40000, rot=True):
    if path.endswith('.npy'):
        pts = np.load(path).astype(np.float32)
    else:
        m = trimesh.load(path, force='mesh')
        pts = np.asarray(m.sample(n), dtype=np.float32)
    b0, b1 = pts.min(0), pts.max(0)
    pts = (pts - (b0 + b1) / 2) * (2 * 0.98 / (b1 - b0).max())
    if rot:
        pts[:, 0] *= -1; pts[:, 2] *= -1
    return pts


def pending():
    jobs = [json.loads(l) for l in open(a.jobs) if l.strip() and not l.startswith('#')]
    return [j for j in jobs if not os.path.exists(os.path.join(a.out, j['name'] + '.glb'))
            and not os.path.exists(os.path.join(a.out, j['name'] + '.fail'))]


while True:
    if os.path.exists(os.path.join(a.out, 'STOP')):
        print('STOP file'); break
    todo = pending()
    if not todo:
        break
    j = todo[0]
    name = j['name']
    kw = {}
    c = j['control']
    if c.startswith('bbox:'):
        s = [float(v) for v in c[5:].split(',')]
        kw['bbox'] = torch.tensor([s], dtype=pdt, device=pdev).unsqueeze(0)
    elif c.startswith('pose:'):
        kw['pose'] = torch.from_numpy(np.loadtxt(c[5:]).astype(np.float32)).to(device=pdev, dtype=pdt).unsqueeze(0)
    elif c.startswith('points:'):
        kw['point'] = torch.from_numpy(load_points(c[7:], j.get('npts', 40000), j.get('rot', False))).to(device=pdev, dtype=pdt).unsqueeze(0)
    elif c.startswith('voxel:'):
        kw['voxel'] = torch.from_numpy(load_points(c[6:], 81920, j.get('rot', False))).to(device=pdev, dtype=pdt).unsqueeze(0)
    else:
        raise ValueError(c)
    try:
        mx.reset_peak_memory()
    except Exception:
        pass
    t1 = time.time()
    try:
        res = pipe(image=j['image'], mc_level=0, guidance_scale=j.get('guidance', 4.5),
                   generator=make_generator(pdev, j.get('seed', 1234)), num_inference_steps=j.get('steps', 50),
                   octree_resolution=j.get('octree', 384), num_chunks=j.get('chunks', 8000), mc_mode='mc',
                   dino_image_size=j.get('dino'), **kw)
        mesh = res['shapes'][0][0]
    except Exception as e:
        print('FAIL', name, repr(e), flush=True)
        open(os.path.join(a.out, name + '.fail'), 'w').write(repr(e))
        continue
    dt = time.time() - t1
    if mesh is None or len(mesh.faces) == 0:
        print('EMPTY', name, flush=True)
        open(os.path.join(a.out, name + '.fail'), 'w').write('empty')
        continue
    mesh.export(os.path.join(a.out, name + '.glb'))
    try:
        peak = mx.get_peak_memory() / 1e9
    except Exception:
        peak = float('nan')
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e9
    row = dict(j, sec=round(dt, 1), raw_faces=int(len(mesh.faces)), mlx_peak_gb=round(peak, 1), rss_max_gb=round(rss, 1),
               load_s=round(load_s, 1), t=time.strftime('%H:%M:%S'))
    print('DONE', json.dumps(row), flush=True)
    with open(os.path.join(a.out, 'runs.jsonl'), 'a') as f:
        f.write(json.dumps(row) + '\n')
    if j.get('dino'):
        pipe.cond_encoder.image_encoder.setup_transform(518) if hasattr(pipe.cond_encoder, 'image_encoder') else None
print('RUNNER_EXIT', flush=True)
