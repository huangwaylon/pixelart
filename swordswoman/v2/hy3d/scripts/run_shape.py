# Usage: python -I run_shape.py <repo_src> <weights_dir> <inputs_dir> <out.glb> mini|mv [steps] [octree] [flashvdm 0/1] [img]
import os, sys, time
src, wdir, idir, out, kind = sys.argv[1:6]
steps = int(sys.argv[6]) if len(sys.argv) > 6 else 5
octree = int(sys.argv[7]) if len(sys.argv) > 7 else 256
fvdm = (sys.argv[8] == "1") if len(sys.argv) > 8 else True
img = sys.argv[9] if len(sys.argv) > 9 else "front.png"
os.environ["HY3DGEN_MODELS"] = wdir
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
sys.path.insert(0, src)
import torch
from PIL import Image
from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline, FloaterRemover, DegenerateFaceRemover
dev = "mps" if torch.backends.mps.is_available() else "cpu"
t0 = time.time()
if kind == "mini":
    pipe = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained("tencent/Hunyuan3D-2mini", subfolder="hunyuan3d-dit-v2-mini-turbo", variant="fp16", device=dev)
    image = Image.open(os.path.join(idir, img)).convert("RGBA")
else:
    pipe = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained("tencent/Hunyuan3D-2mv", subfolder="hunyuan3d-dit-v2-mv-turbo", variant="fp16", device=dev)
    image = {k: Image.open(os.path.join(idir, k + ".png")).convert("RGBA") for k in os.environ.get("MV_VIEWS", "front,left,back").split(",")}
if fvdm:
    pipe.enable_flashvdm(mc_algo="mc")
print(f"load {time.time()-t0:.1f}s on {dev}", flush=True)
t1 = time.time()
mesh = pipe(image=image, num_inference_steps=steps, octree_resolution=octree, num_chunks=20000,
            generator=torch.manual_seed(12345), output_type="trimesh")[0]
print(f"gen {time.time()-t1:.1f}s", flush=True)
mesh = FloaterRemover()(mesh); mesh = DegenerateFaceRemover()(mesh)
mesh.export(out)
print("verts", len(mesh.vertices), "faces", len(mesh.faces), "watertight", mesh.is_watertight, "bounds", mesh.bounds.tolist())
