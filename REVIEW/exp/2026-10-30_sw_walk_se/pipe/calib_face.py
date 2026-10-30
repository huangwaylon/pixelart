"""calib_face.py -> face_calib.json  (step 4 calibration, run once; read-only on the round-10 release passes).
facesys option b': the rest-space SURFACE point of each SE eye (surfanchor.calib: centroid of the drawn eye on the head surface,
idle SE f00 of build 20261030_66119a7, snapped onto the mesh; far eye = mirror of the near eye) and the fixed offset from that
point to the template origin (master layout). The pipeline then only needs these numbers: the point is re-found on the posed
mesh every frame by the renderer (nearest rest vertex, deformed), so placement follows the 3D head exactly."""
import sys, json, os
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/docs/team_review/2026-10-30/face_palette/scripts')
import surfanchor as SA
from facesys import LAYOUT
res = SA.calib('SE')
out = {'_doc': __doc__, 'view': 'SE', 'eyes': []}
for c, ((ox, oy), side, kind) in zip(res, LAYOUT['SE']):
    out['eyes'].append({'key': c['key'], 'rest_m': [round(float(v), 5) for v in c['P']], 'off_px': [round(float(v), 3) for v in c['off']],
                        'side': side, 'kind': kind})
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'face_calib.json'), 'w'), indent=1)
print(json.dumps(out['eyes']))
