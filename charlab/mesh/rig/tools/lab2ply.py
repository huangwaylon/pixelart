"""Export a charlab/lab primitive model (work/<id>/<tier>_<preset>/model.npz + model.json)
to a binary PLY with per-vertex colour (face material palette colour, splatted to vertices).
usage: python lab2ply.py <model_dir> <out.ply>"""
import sys, json, struct
import numpy as np
d, out = sys.argv[1], sys.argv[2]
m = np.load(f"{d}/model.npz"); j = json.load(open(f"{d}/model.json"))
V, F, fm = m["V"], m["F"], m["fmat"]
pal = j["palette"]
def hx(h): return [int(h[i:i+2], 16) for i in (1, 3, 5)]
mc = np.array([hx(pal[mm[0]]) for mm in j["mats"]], np.uint8)
col = np.zeros((len(V), 3), np.uint8); col[F[:, 0]] = mc[fm]; col[F[:, 1]] = mc[fm]; col[F[:, 2]] = mc[fm]
with open(out, "wb") as f:
    f.write((f"ply\nformat binary_little_endian 1.0\nelement vertex {len(V)}\nproperty float x\nproperty float y\nproperty float z\n"
             f"property uchar red\nproperty uchar green\nproperty uchar blue\nelement face {len(F)}\nproperty list uchar int vertex_indices\nend_header\n").encode())
    vd = np.zeros(len(V), dtype=[("p", "<f4", 3), ("c", "u1", 3)]); vd["p"] = V; vd["c"] = col; f.write(vd.tobytes())
    fd = np.zeros(len(F), dtype=[("n", "u1"), ("i", "<i4", 3)]); fd["n"] = 3; fd["i"] = F; f.write(fd.tobytes())
print(out, len(V), len(F))
