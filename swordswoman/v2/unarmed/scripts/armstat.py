# armstat.py clip t0,t1,... [kw]: arm metrics at frames: wrist dist (L), R/L wrist fwd/up/side rel. chest in her yaw frame, elbow angle
import sys, os, math, numpy as np
sys.path.insert(0, "/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/mocap/scripts")
import retarget as RT
MC = "/Users/waylonhuang/Documents/other/pixelart/.models/mocap/"
def stat(path, ts, **kw):
    c = RT.prep(MC + path, **kw); L = c["_L"]; out = []
    for t in ts:
        hx = c["hip.L"][t] - c["hip.R"][t] + c["sh.L"][t] - c["sh.R"][t]; hx[2] = 0; hx /= np.linalg.norm(hx); fw = np.cross([0, 0, 1.0], hx)  # fw = her forward
        r = [round(float(np.linalg.norm(c["wr.R"][t] - c["wr.L"][t]) / L), 2)]
        for s in "RL":
            d = (c["wr." + s][t] - c["sh." + s][t]) / L; u = c["el." + s][t] - c["sh." + s][t]; f = c["wr." + s][t] - c["el." + s][t]
            el = math.degrees(math.acos(np.clip(u @ f / np.linalg.norm(u) / np.linalg.norm(f), -1, 1)))
            r.append((s, round(float(d @ fw), 2), round(float(d[2]), 2), round(float(d @ hx), 2), int(el)))
        out.append((t, r))
    return out
if __name__ == "__main__":
    ts = [int(x) for x in sys.argv[2].split(",")]
    for t, r in stat(sys.argv[1], ts, travel="travel" in sys.argv[3:]): print(t, r)
