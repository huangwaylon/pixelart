# ov_S.py: per-view overrides for view S (owned by the S sub-strand). PRE = before VIEW_XFORM (SE screen terms; S/N: stride x becomes depth), POST = final pose keys after VIEW_XFORM (N: screen angles already mirrored).
from poses_src_helpers import P, legs, arms, ML
PRE = {
 "run": {"contact": legs([0.60, -0.84], [-0.60, -0.36]), "contact2": ML(legs([0.60, -0.84], [-0.60, -0.36]))},
 "dash": {"burst": {"+sq": 0.12, "+lean": 6, "head": [-14, 0, 0]}, "smear": {"+sq": 0.14, "lift": 0.0, "absz": 0, "+lean": 8, "head": [-10, 0, 0]}},
 "slash": {"impact": P(arms(R=[-20, -10], blade=[-15, 0]), {"bs": {"upper_arm.R": 1.4}})},
}
POST = {
 "walk": {k: {"blade_scr": [-140, 0]} for k in ("contact", "down", "pass", "contact2", "down2", "pass2")},
 "hurt": {"stagger": {"roll": -14}},
}
