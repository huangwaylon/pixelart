# rl_r7eyes.py (I, round 9 A/B for F): run R's render/render_motion.py unchanged except, IN MEMORY, the expression illustrations come from
# F's archived face/illus/out_r7/ and the composited expression textures are cached under release/work/r7expr/ (never in rig/).
#   <blender> -b rig/rig.blend -P release/rl_r7eyes.py -- <render_motion args...>
import os, sys
EXP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = open(os.path.join(EXP, "render", "render_motion.py")).read()
a = '"face", "illus", "out", sv'; b = 'os.path.join(EXP, "rig", "tex_illus", "expr", view, name + ".png")'
assert a in src and b in src, "render_motion.py changed: A/B wrapper needs updating"
src = src.replace(a, '"face", "illus", "out_r7", sv').replace(b, 'os.path.join(EXP, "release", "work", "r7expr", view, name + ".png")')
fn = os.path.join(EXP, "render", "render_motion.py")
exec(compile(src, fn, "exec"), {"__name__": "__main__", "__file__": fn})
