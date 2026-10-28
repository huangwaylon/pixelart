# run_mv_parts.py IN_ROOT OUT_DIR part1 part2 ...   (Hunyuan3D-2mv turbo, flashvdm, 5 steps, octree 384; loads once)
import os, sys, time
R = '/Users/waylonhuang/Documents/other/pixelart/.models/hunyuan'
os.environ["HY3DGEN_MODELS"] = R + '/weights'; os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
sys.path.insert(0, R + '/src')
import torch
from PIL import Image
from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline, FloaterRemover, DegenerateFaceRemover
ir, od, parts = sys.argv[1], sys.argv[2], sys.argv[3:]
os.makedirs(od, exist_ok=True)
steps = int(os.environ.get('STEPS', 5)); seed = int(os.environ.get('SEED', 12345))
t0 = time.time()
pipe = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained("tencent/Hunyuan3D-2mv", subfolder="hunyuan3d-dit-v2-mv-turbo", variant="fp16", device="mps")
pipe.enable_flashvdm(mc_algo="mc"); print(f"load {time.time()-t0:.1f}s", flush=True)
for p in parts:
    t1 = time.time()
    image = {k: Image.open(f'{ir}/{p}/{k}.png').convert("RGBA") for k in ("front", "left", "back")}
    mesh = pipe(image=image, num_inference_steps=steps, octree_resolution=384, num_chunks=20000, generator=torch.manual_seed(seed), output_type="trimesh")[0]
    mesh = FloaterRemover()(mesh); mesh = DegenerateFaceRemover()(mesh)
    mesh.export(f'{od}/{p}.glb')
    print(p, f"gen {time.time()-t1:.1f}s faces", len(mesh.faces), "wt", mesh.is_watertight, "ext", (mesh.bounds[1]-mesh.bounds[0]).round(3).tolist(), flush=True)
