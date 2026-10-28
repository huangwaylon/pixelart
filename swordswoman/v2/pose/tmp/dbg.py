import bpy, sys, os
LIB = os.environ["RIG_LIB_PATH"]; src = open(LIB).read(); src = src[:src.index('if os.environ.get("RIG_LIB") == "1"')]
a0 = sys.argv[sys.argv.index("--") + 1:]
sys.argv = [sys.argv[0], "--", a0[0], a0[0] + "/skel.txt", os.path.join(os.path.dirname(LIB), "empty_keys.json"), "/tmp/dbgout"]
exec(compile(src, "rig_lib.py", "exec"))
set_view("E")
for kd in ({"scr": {"upper_arm.R": [92, 0]}, "katana": 1}, {"scr": {"upper_arm.R": [92, 0]}, "bs": {"upper_arm.R": 2.0}, "katana": 1}, {"scr": {"upper_arm.R": [-90, 0]}, "katana": 1}):
    pose(kd); W = ao.matrix_world
    print("UA", [round(x, 3) for x in W @ pbs["upper_arm.R"].head], [round(x, 3) for x in W @ pbs["upper_arm.R"].tail], "FA", [round(x, 3) for x in W @ pbs["forearm.R"].head], [round(x, 3) for x in W @ pbs["forearm.R"].tail], "HAND", [round(x, 3) for x in W @ pbs["hand.R"].head])
