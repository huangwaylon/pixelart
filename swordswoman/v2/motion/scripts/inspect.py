import bpy, sys, os, json, math
LIB = "/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/throw/scripts/rig_lib.py"
a0 = sys.argv[sys.argv.index("--") + 1:]; pdir_ = a0[0]
src = open(LIB).read(); src = src[:src.index('if os.environ.get("RIG_LIB") == "1"')]
os.environ.setdefault("CHEAT", "0")
sys.argv = [sys.argv[0], "--", pdir_, pdir_ + "/skel.txt", "/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/throw/scripts/empty_keys.json", "/tmp/m_insp"]
exec(compile(src, "rig_lib.py", "exec"))
import numpy as np
from collections import Counter
for o in BIND:
    me = o.data; ca = me.color_attributes["Color"]; M = o.matrix_world
    vs = np.array([(M @ v.co)[:] for v in me.vertices])
    if ca.domain == "CORNER":
        col = {}
        for l in me.loops: col[l.vertex_index] = tuple(round(x * 255) for x in ca.data[l.index].color_srgb[:3])
        cols = [col.get(i, (0, 0, 0)) for i in range(len(vs))]
    else: cols = [tuple(round(x * 255) for x in d.color_srgb[:3]) for d in ca.data]
    cc = Counter(cols).most_common(4)
    print("PART", o.name, BIND[o], len(vs), "min", vs.min(0).round(3), "max", vs.max(0).round(3), cc)
for b in arm.bones: print("BONE", b.name, [round(x, 3) for x in b.head_local], [round(x, 3) for x in b.tail_local], b.parent.name if b.parent else None)
