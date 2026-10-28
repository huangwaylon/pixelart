# run_partcrafter.py IMG_RGBA.png OUT_DIR NUM_PARTS [steps=50] [seed=0] [num_tokens=1024]   (MPS port, no rmbg/pyrender)
import os, sys, time, numpy as np, torch, trimesh
R = '/Users/waylonhuang/Documents/other/pixelart/.models/parts/PartCrafter'; sys.path.insert(0, R)
from PIL import Image
from src.pipelines.pipeline_partcrafter import PartCrafterPipeline
img, od, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
steps = int(sys.argv[4]) if len(sys.argv) > 4 else 50; seed = int(sys.argv[5]) if len(sys.argv) > 5 else 0
ntok = int(sys.argv[6]) if len(sys.argv) > 6 else 1024
dt = torch.float16 if os.environ.get('FP32') is None else torch.float32
os.makedirs(od, exist_ok=True)
t0 = time.time()
pipe = PartCrafterPipeline.from_pretrained(R + '/pretrained_weights/PartCrafter').to('mps', dt)
print(f'load {time.time()-t0:.1f}s', flush=True)
# RGBA -> white bg, square, 10% pad
im = Image.open(img).convert('RGBA'); a = im.split()[3].point(lambda v: 0 if v < 30 else v); im.putalpha(a); im = im.crop(im.getbbox())
s = int(max(im.size) / 0.8); c = Image.new('RGB', (s, s), (255, 255, 255)); c.paste(im, ((s - im.width) // 2, (s - im.height) // 2), im)
c = c.resize((512, 512), Image.LANCZOS); c.save(f'{od}/input.png')
t1 = time.time()
out = pipe(image=[c] * n, attention_kwargs={"num_parts": n}, num_tokens=ntok, generator=torch.Generator(device=pipe.device).manual_seed(seed),
           num_inference_steps=steps, guidance_scale=7.0, max_num_expanded_coords=int(1e9), use_flash_decoder=False).meshes
print(f'gen {time.time()-t1:.1f}s', flush=True)
for i, m in enumerate(out):
    if m is None: print('part', i, 'None'); continue
    m.export(f'{od}/part_{i:02}.glb'); print('part', i, len(m.faces), (m.bounds[1] - m.bounds[0]).round(3).tolist())
