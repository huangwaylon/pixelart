# codes.py MEAS.json VIEW Y0 Y1 [X0 X1]: print rig class rows from a cal96 meas.json
import sys, json
m = json.load(open(sys.argv[1])); v = sys.argv[2]; y0, y1 = int(sys.argv[3]), int(sys.argv[4]); x0, x1 = (int(sys.argv[5]), int(sys.argv[6])) if len(sys.argv) > 6 else (36, 96)
print(v, {k: (round(float(x), 1) if x is not None else None) for k, x in m[v]["rows"].items()}, {k: float(x) for k, x in m[v]["widths"].items()})
for y in range(y0, y1): print("%3d %s" % (y, m[v]["codes"][y][x0:x1]))
