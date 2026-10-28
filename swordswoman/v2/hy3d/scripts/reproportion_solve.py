# reproportion_solve.py SPEC.json IN_PARTS SKEL.txt OUT_PARTS
# If SPEC has "targets" (heads_tall, shoulder_over_headw, waist_over_headw, legs_frac_of_height, neck_gap), solve the multipliers
# (head.scale, arms.shoulder_x, torso.waist, legs.length, neck.extra) by fixed-point iteration over reproportion.py, starting from
# the explicit values in SPEC. Writes OUT_PARTS (final) + OUT_PARTS/spec_solved.json. Without "targets" it just runs reproportion.py.
import sys, os, json, subprocess, copy, tempfile
spec_p, idir, skp, odir = sys.argv[1:5]
HERE = os.path.dirname(os.path.abspath(__file__)); PY = sys.executable
SP = json.load(open(spec_p)); T = SP.get("targets", {})
def run(sp, out):
    fd, tp = tempfile.mkstemp(suffix=".json"); os.close(fd); json.dump(sp, open(tp, "w"))
    r = subprocess.run([PY, "-I", os.path.join(HERE, "reproportion.py"), tp, idir, skp, out], capture_output=True, text=True); os.remove(tp)
    if r.returncode: print(r.stderr[-800:]); sys.exit(1)
    return json.load(open(os.path.join(out, "pivots.json")))["_reproportion"]["measure"]
def get(sp, a, b, d): return float(sp.get(a, {}).get(b, d))
def put(sp, a, b, v): sp.setdefault(a, {})[b] = round(float(v), 4)
sp = copy.deepcopy(SP); sp.pop("targets", None)
if not T: print(run(sp, odir)); sys.exit(0)
tmp = odir + "_solve"
for it in range(8):
    m = run(sp, tmp); err = {}
    if "legs_frac_of_height" in T:
        e = T["legs_frac_of_height"] / m["legs_frac_of_height"]; put(sp, "legs", "length", get(sp, "legs", "length", 1) * e ** 1.6); err["legs"] = e
    if "heads_tall" in T:
        e = m["heads_tall"] / T["heads_tall"]; put(sp, "head", "scale", get(sp, "head", "scale", 1) * e ** 0.9); err["heads"] = e
    if "shoulder_over_headw" in T:
        e = T["shoulder_over_headw"] / m["shoulder_over_headw"]; put(sp, "arms", "shoulder_x", get(sp, "arms", "shoulder_x", 1) * e); err["sh"] = e
    if "waist_over_headw" in T:
        e = T["waist_over_headw"] / m["waist_over_headw"]; put(sp, "torso", "waist", get(sp, "torso", "waist", 1) * e); err["waist"] = e
    if "neck_gap" in T:
        put(sp, "neck", "extra", get(sp, "neck", "extra", 0) + (T["neck_gap"] - m["neck_gap"])); err["neck"] = T["neck_gap"] - m["neck_gap"]
    print("iter", it, {k: round(v, 3) for k, v in m.items() if k in ("heads_tall", "shoulder_over_headw", "waist_over_headw", "legs_frac_of_height", "neck_gap")}, flush=True)
    if all(abs(v - 1) < 0.01 if k != "neck" else abs(v) < 0.003 for k, v in err.items()): break
m = run(sp, odir); sp["targets"] = T; sp["measure"] = m
json.dump(sp, open(os.path.join(odir, "spec_solved.json"), "w"), indent=1)
import shutil; shutil.rmtree(tmp, ignore_errors=True)
print("final", m)
