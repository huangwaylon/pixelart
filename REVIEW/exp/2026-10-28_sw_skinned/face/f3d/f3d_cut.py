# f3d_cut.py (F, round 5, TEST STAND-IN ONLY): preview the agreed hairline before R re-sculpts it.  In memory, deletes the fringe hair polygons
# in front of the face below the agreed fringe line (m96 S row F3D_CUTROW, default 46.5), then runs R's render_motion.py (mode render) or
# P's p_parts.py (mode parts) unchanged on that mesh.  rig.blend is never saved.
#   <blender> -b rig/rig.blend -P face/f3d/f3d_cut.py -- render|parts <motion> <view> <outdir> [flags]
import bpy, bmesh, sys, os, json
argv = sys.argv[sys.argv.index("--") + 1:]
HERE = os.path.dirname(os.path.abspath(__file__)); EXP = os.path.dirname(os.path.dirname(HERE))
mode = argv[0]; rest = argv[1:]
sys.path.insert(0, HERE)
fit = json.load(open(os.path.join(HERE, "uvfit.json")))
row = float(os.environ.get("F3D_CUTROW", "46.5"))
def tex_v(col, r):
    x, y = col - 64, r - 52; f = [1, x, y, x * x, x * y, y * y, x ** 3, x * x * y, x * y * y, y ** 3]
    return sum(a * b for a, b in zip(f, fit["cv"]))
v = 1 - tex_v(64, row) / 1024; z_cut = 1.0695 + 0.341 * v   # R's face_uv (measured from rig/face_anchors.json uv vs rest): v = (z - 1.0695) / 0.341
body = bpy.data.objects["body"]; me = body.data; col = me.color_attributes["Color"]
lin = lambda u: u / 12.92 if u <= 0.04045 else ((u + 0.055) / 1.055) ** 2.4
HAIR = [c / 255 for c in (61, 50, 53)]   # bmesh byte colours are sRGB
bm = bmesh.new(); bm.from_mesh(me)
lay = bm.loops.layers.color.get("Color") or bm.loops.layers.float_color.get("Color")
gi = body.vertex_groups["head"].index; dl = bm.verts.layers.deform.active
kill = []
for f in bm.faces:
    c = f.loops[0][lay]
    if not all(abs(c[k] - HAIR[k]) < 0.02 for k in range(3)): continue
    p = f.calc_center_median()
    if p.z < z_cut and abs(p.x) < 0.125 and p.y > 0.10 and p.z > z_cut - 0.20: kill.append(f)
bmesh.ops.delete(bm, geom=kill, context="FACES"); bm.to_mesh(me); bm.free(); me.update()
print("F3D_CUT fringe polys removed", len(kill), "z_cut", round(z_cut, 4), flush=True)
script = {"render": os.path.join(EXP, "render", "render_motion.py"), "parts": os.path.join(EXP, "render", "p_parts.py")}[mode]
sys.argv = [sys.argv[0], "--"] + rest
exec(compile(open(script).read(), script, "exec"), {"__name__": "__main__", "__file__": script})
