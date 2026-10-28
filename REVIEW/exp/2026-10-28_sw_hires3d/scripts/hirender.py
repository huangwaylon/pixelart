# hirender.py (HIRES3D experiment): Blender -b --factory-startup -P hirender.py -- PARTS_DIR JOBS.json OUT_DIR
# = v2/motion/scripts/mrender.py (rig H2 + springs, exec'd from its source, NOT modified) with
#   * render resolution CELL1 * SCH (env SCH, default 8 -> 192 cell = 1536 px; in-game 128 cell = crop 256..1280)
#   * extra passes (env KINDS): guide (matid, AA off), shade (existing EEVEE toon + hull outline),
#     lum (white diffuse lit by the view's screen-space sun, Raw, 16 bit), nrm (camera-space normal, Raw), dep (camera depth, Raw 16 bit)
import bpy, sys, os
MR = "/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/motion/scripts/mrender.py"
src = open(MR).read()
SCH = int(os.environ.get("SCH", "8"))
src = src.replace("sc.render.resolution_x = sc.render.resolution_y = CELL1 * SC", f"sc.render.resolution_x = sc.render.resolution_y = CELL1 * {SCH}")
assert f"CELL1 * {SCH}" in src
src = src.replace("def rpass(path, kind):", "def rpass_orig(path, kind):")
INJ = r'''
def _mk(kind):
    m = bpy.data.materials.new("hx_" + kind); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; L = nt.links
    for n in list(N): N.remove(n)
    out = N.new("ShaderNodeOutputMaterial"); em = N.new("ShaderNodeEmission"); L.new(em.outputs[0], out.inputs[0])
    if kind == "lum":
        df = N.new("ShaderNodeBsdfDiffuse"); df.inputs[0].default_value = (1, 1, 1, 1)
        s2r = N.new("ShaderNodeShaderToRGB"); L.new(df.outputs[0], s2r.inputs[0]); L.new(s2r.outputs[0], em.inputs[0])
    else:
        g = N.new("ShaderNodeNewGeometry"); vt = N.new("ShaderNodeVectorTransform"); vt.convert_from = "WORLD"; vt.convert_to = "CAMERA"
        if kind == "nrm":
            vt.vector_type = "NORMAL"; L.new(g.outputs["Normal"], vt.inputs[0])
            mp = N.new("ShaderNodeVectorMath"); mp.operation = "MULTIPLY_ADD"; mp.inputs[1].default_value = (0.5, 0.5, 0.5); mp.inputs[2].default_value = (0.5, 0.5, 0.5)
            L.new(vt.outputs[0], mp.inputs[0]); L.new(mp.outputs[0], em.inputs[0])
        else:
            vt.vector_type = "POINT"; L.new(g.outputs["Position"], vt.inputs[0])
            sp = N.new("ShaderNodeSeparateXYZ"); L.new(vt.outputs[0], sp.inputs[0])
            ma = N.new("ShaderNodeMath"); ma.operation = "MULTIPLY_ADD"; ma.inputs[1].default_value = 0.25; ma.inputs[2].default_value = -2.0  # camera z (forward +) in [8,12] -> [0,1]
            L.new(sp.outputs["Z"], ma.inputs[0]); L.new(ma.outputs[0], em.inputs[0])
    return m
HXM = {k: _mk(k) for k in ("lum", "nrm", "dep")}
def rpass(path, kind):
    sc.view_settings.view_transform = "Standard"; sc.render.image_settings.color_depth = "8"
    if kind in ("shade", "guide", "matid"):
        return rpass_orig(path, "shade" if kind == "shade" else "guide")
    sc.render.engine = "BLENDER_EEVEE"; sc.eevee.taa_render_samples = 16
    sc.view_settings.view_transform = "Raw"; sc.render.image_settings.color_depth = "16"
    saved = []
    for o in ALL:
        o.modifiers["outline"].show_render = False
        if o.data and hasattr(o.data, "materials") and len(o.data.materials):
            saved.append((o, o.data.materials[0])); o.data.materials[0] = HXM[kind]
    sc.render.filepath = path; bpy.ops.render.render(write_still=True)
    for o, mt in saved: o.data.materials[0] = mt
    sc.view_settings.view_transform = "Standard"; sc.render.image_settings.color_depth = "8"
'''
mark = "# ============================================================== jobs"
src = src.replace(mark, INJ + "\n" + mark)
exec(compile(src, "mrender_hires.py", "exec"))
