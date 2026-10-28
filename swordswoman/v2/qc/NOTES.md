# QC strand NOTES
- 13:08 step0: created v2/qc/, surveying tools
- step1: surveyed colorcheck/lint_style/ff_redraw.validate/post.colors; palette mats K|hHgL hair+boots|sSmk skin|eER dress+bow|QOo obi|W eyes|Dd socks. top1 S eye row uses Q (obi) + D (sock) chars = ramp swap. eyecheck.py/EYE_SPEC not in m96 yet -> stub.
- step2: design: qc_gate.py modes masters|stamps|clip|all|frame; module hooks validate_hook(path,fj,stamp,master) for ff_redraw, main([...]) for post.py; parts() measures rows/head/bow/eyes from char maps by material+location; eye stub until m96/tools/eyecheck.py exposes qc_hook(g,view,ref,pal)->(metrics,fixes). writing code.
- step3: wrote v2/qc/qc_gate.py (first draft), testing on top1
- step4: parts() fixed (shoulder by collar band, bow knot = red groups above shoulder in top 40% of head, hem = dress run at body centre, eye stub excludes hair-only px)
- step5: masters mode runs clean of parse artefacts; testing clip mode next
- step6: clip/stamps/all/frame modes + validate_hook tested on synthetic clip (/tmp/qct, from top1 SE: 1px head recolour, bow move, +2px drift, sock flicker -> all caught; identical frame PASS) and synthetic stamps
- step7: test outputs deleted (/tmp/qct). Old clip anim_cut/frames/{idle,run}_SE ran OK (legacy pixel/palette.json, '#' outline -> noisy O1, as expected).

## USAGE (v2/qc/qc_gate.py; run with /Users/waylonhuang/Documents/other/pixelart/swordswoman/.venv/bin/python)
  qc_gate.py masters [MDIR]                    5 views (default first of m96/final, m96/masters, pixelize/top1)
  qc_gate.py stamps SDIR [--masters MDIR]      <VIEW>_<expr>.txt vs <VIEW>_neutral.txt + master
  qc_gate.py clip CDIR [--view SE] [--masters MDIR|--master M.txt] [--stamp S] [--rest 0,4] [--contacts 0,4] [--noloop]
  qc_gate.py all ROOT|CDIR... [--masters MDIR]  every clip dir + cross-clip table
  qc_gate.py frame F.txt --view SE [--masters MDIR] [--stamp S] [--rest-frame]
  opts: --palette P (default pixelize/palette.json) --out DIR ('-' none; default v2/qc/out/<mode>_<name>) --quiet --json --no-overlay
  out: report.txt, report.json, ov_<item>_<check>.png (<=800px). exit 0 PASS / 1 FAIL. Frame meta: '; rest' '; contact' '; overlap' '; shift x0 y0 x1 y1' '; air'.
  Frames vs master: outline faults already in the master are not repeated (aligned +-4px); eyes compared in screen space after the head offset.
  Eye hook: if v2/m96/tools/eyecheck.py defines qc_hook(grid, view, ref_grid, pal_path) -> (metrics, fixes) it is called; else built-in stub.
  Tolerances: SPEC dict at the top of qc_gate.py.
## HOOKS (documented, NOT applied; paste by file owners)
  ff_redraw.validate, before 'return fx':  sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/qc'); import qc_gate; fx += qc_gate.validate_hook(path, fj, stamp, master)
  post.py main:  elif c == 'qc': sys.path.insert(0, V2 + '/qc'); import qc_gate; sys.exit(qc_gate.main(['clip', wdir(sys.argv[2], sys.argv[3])] + sys.argv[4:]))
## FINDINGS current pixelize/top1 (FAIL)
  palette: no off-palette, no ramp swaps. bow: S/N centred (asym 0/+1) OK; SE/E/NE knot -7.5/-8/-8 px left of midline (master ref).
  outline: S O1 2 + S4 17 (face S/m specks); SE S4 9; E 4; NE 4; N 8.
  eyes: only S has catchlights (1 W per eye); SE eyes = one merged black blob, E eye 3x2 black, no W; SE/E iris lacks g/L.
  xview: head H S35 SE36 E29 NE31 N34; W S26 vs N31; crown E33 vs 30-32; SE chin/shoulder +2-3; SE/NE hem/sock rows 92-94 vs 89-91;
         eye-top-to-crown S21 SE19 E16. WARN: SE thighs use blush k (31% of skin); obi ramp S/E O-only, N o-only.
