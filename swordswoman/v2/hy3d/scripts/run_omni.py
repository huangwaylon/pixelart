"""Run Hunyuan3D-Omni (cbun MLX fork) on our image with several pose / bbox controls.

Usage: venv/bin/python -I scripts/run_omni.py OMNI_SRC WEIGHTS IMAGE OUT_DIR [--device mlx|mps]
       [--steps 50] [--octree 384] [--seed 1234] [--guidance 4.5] CONTROL...
CONTROL is a pose .txt (51x6 bone file) or "bbox:<sx>,<sy>,<sz>" (full extents in [-1,1] box).
"""
import argparse, os, sys, time, json

ap = argparse.ArgumentParser()
ap.add_argument('src'); ap.add_argument('weights'); ap.add_argument('image'); ap.add_argument('out')
ap.add_argument('controls', nargs='+')
ap.add_argument('--device', default='mlx'); ap.add_argument('--steps', type=int, default=50)
ap.add_argument('--octree', type=int, default=384); ap.add_argument('--seed', type=int, default=1234)
ap.add_argument('--guidance', type=float, default=4.5); ap.add_argument('--tag', default='')
ap.add_argument('--variant', default='ema', help='ema | none')
a = ap.parse_args()

os.environ.setdefault('PYTORCH_ENABLE_MPS_FALLBACK', '1')
sys.path.insert(0, a.src)
import numpy as np, torch, trimesh
from hy3dshape.pipelines import Hunyuan3DOmniSiTFlowMatchingPipeline
from hy3dshape.postprocessors import FloaterRemover, DegenerateFaceRemover
from hy3dshape.runtime import make_generator, resolve_device, resolve_dtype

os.makedirs(a.out, exist_ok=True)
t0 = time.time()
dev = 'mlx' if a.device == 'mlx' else resolve_device(a.device)
dtype = resolve_dtype('auto', resolve_device('mps'))
pipe = Hunyuan3DOmniSiTFlowMatchingPipeline.from_pretrained(a.weights, variant=(None if a.variant == 'none' else a.variant), device=dev, dtype=dtype)
print(f'LOAD {time.time() - t0:.1f}s device={a.device} dtype={dtype}', flush=True)
pdev, pdt = pipe.device, pipe.dtype

log = []
for c in a.controls:
    kw = {}
    if c.startswith('bbox:'):
        s = [float(v) for v in c[5:].split(',')]
        kw['bbox'] = torch.tensor([s], dtype=pdt, device=pdev).unsqueeze(0)
        name = 'bbox_' + '_'.join(f'{v:g}' for v in s)
    elif c.startswith('points:'):
        m = trimesh.load(c[7:], force='mesh'); b = m.bounds
        m.apply_translation(-(b[0] + b[1]) / 2); m.apply_scale(2 * 0.98 / (b[1] - b[0]).max())
        pts = np.asarray(m.sample(int(os.environ.get('NPTS', '40000'))), dtype=np.float32)
        if os.environ.get('PT_ROT180'): pts[:, 0] *= -1; pts[:, 2] *= -1
        kw['point'] = torch.from_numpy(pts).to(device=pdev, dtype=pdt).unsqueeze(0)
        name = 'points_' + os.path.splitext(os.path.basename(c[7:]))[0]
    else:
        kw['pose'] = torch.from_numpy(np.loadtxt(c).astype(np.float32)).to(device=pdev, dtype=pdt).unsqueeze(0)
        name = os.path.splitext(os.path.basename(c))[0]
    name = name + a.tag
    if torch.backends.mps.is_available():
        torch.mps.reset_peak_memory_stats() if hasattr(torch.mps, 'reset_peak_memory_stats') else None
    t1 = time.time()
    res = pipe(image=a.image, mc_level=0, guidance_scale=a.guidance, generator=make_generator(pdev, a.seed),
               num_inference_steps=a.steps, octree_resolution=a.octree, num_chunks=8000, mc_mode='mc', **kw)
    mesh = res['shapes'][0][0]
    dt = time.time() - t1
    if mesh is None or len(mesh.faces) == 0:
        print('EMPTY', name); log.append({'name': name, 'sec': dt, 'faces': 0}); continue
    raw_parts = mesh.split(only_watertight=False)
    raw_faces = len(mesh.faces); big = max(len(p.faces) for p in raw_parts)
    raw_info = {'raw_components': len(raw_parts), 'raw_faces': raw_faces, 'raw_frac_outside_main': round(1 - big / raw_faces, 4)}
    print('RAW', name, raw_info, flush=True)
    if os.environ.get('SAVE_RAW'): mesh.export(os.path.join(a.out, name + '_raw.glb'))
    mesh = DegenerateFaceRemover()(FloaterRemover()(mesh))
    mesh.export(os.path.join(a.out, name + '.glb'))
    try:
        import mlx.core as mx
        peak = mx.get_peak_memory() / 1e9
    except Exception:
        peak = float('nan')
    print(f'DONE {name} {dt:.1f}s faces={len(mesh.faces)} mlx_peak={peak:.1f}GB', flush=True)
    log.append({'name': name, 'sec': round(dt, 1), 'faces': int(len(mesh.faces)), 'mlx_peak_gb': round(peak, 1), **raw_info})
json.dump(log, open(os.path.join(a.out, f'log{a.tag}.json'), 'w'), indent=1)
