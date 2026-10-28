"""f3d_chain.py (F, round 5): P's STANDARD pixel chain (render/pixel_chain.py, unchanged) on an f3d_render.py stem, with F's face materials
registered as ordinary materials (matid colour + flat ramp + thin-feature class) until R's rig/matids.json and P's ramps carry them.
  python f3d_chain.py <stem>.json      (pixtools venv)"""
import os, sys, json, importlib.util
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); EXP = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import f3d_lib as L
spec = importlib.util.spec_from_file_location('pixel_chain', os.path.join(EXP, 'render', 'pixel_chain.py'))
pc = importlib.util.module_from_spec(spec); spec.loader.exec_module(pc)
for m, (c, r) in L.MATS.items():
    if m not in pc.MATS or os.environ.get('F3D_FORCE_COL') == '1': pc.MATS[m] = tuple(c)
    pc.RAMP[m] = r   # F's flat ramps (P's 'iris' hgL lum bands put light L on the lit iris side)
pc.THINF.update({k: v for k, v in {'iris_top': 1, 'iris_low': 1, 'brow': 1, 'mouth_in': 1, 'nose': 1}.items() if k not in pc.THINF})
pc.MN = list(pc.MATS); pc.NM = len(pc.MN); pc.MI = {n: i for i, n in enumerate(pc.MN)}; pc.MCOL = np.array([pc.MATS[k] for k in pc.MN], float)
pc.NS = pc.NM * pc.NP; pc.SEG_M = np.arange(pc.NS) // pc.NP; pc.SEG_P = np.arange(pc.NS) % pc.NP
for k in L.MATS: pc.hx.CLS.setdefault(L.PV[k], 'face')
sys.argv = [sys.argv[0]] + sys.argv[1:]
pc.main()
