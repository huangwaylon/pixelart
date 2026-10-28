# MOTION strand NOTES
- start 2026-10-27 18:40:51
- step1 refs: added animation-ref domains to the allowlist CSV (idleworm cert broken; bulbagarden/spriters-resource 403 Cloudflare). Wikipedia 12 principles OK. PMD SpriteCollab (GitHub raw) AnimData timings + Walk sheets saved in motion/refs/pmd (Gardevoir 0282, Lopunny 0428, Lucario 0448).
- step1 MECHANICS.md written (Williams/12 principles/PMD timings + measured mocap bob/sway/yaw table)
- step2 design: new Blender renderer motion/scripts/mrender.py (execs throw/scripts/rig_lib.py like render_jobs.py) + rig extension: hair_side.L/R + hair_back bones (head mesh -> armature-deformed, weights by height x azimuth), skirt hem bones hem0-5 (skirt deformed), ribbon tails (new strip meshes, bow colour, 2-bone chains under bow), bow/bun springs. Motion = key states captured from pose(), dense 120 Hz Hermite interpolation (quats), head/forearm lag (overlap), damped-spring particle chains (inertia + travel drag + gravity rel. to rest + head collision). Driver motion/scripts/frames_M.py (as g96 frames_H.py). Key picks: walk bandai 58,61,65,69,74,77,81,86 (cycle ->90); run CMU 02_03 11,22,33,48,57,68,79,93 (->104).
- step2 built: scripts/mact.py (key tables -> work/act_M.json; tune overrides work/tune.json), scripts/mrender.py (secondary rig + springs; ribbon tails RIB_LEN .42 hang back from the bow knot), scripts/frames_M.py (prev -> motion/prev/<tag>/<act>_<view>/{game.gif,shade2x.gif,cmp.gif (old vs new same clock),crit.png,strip.png,frames.json}). walk tune amp 1.1 / bob 1.4 (1.3 read as a stomp).
- step3 (resumed by new instance 21:05): r1 prev for 7 acts SE+E rendered, r1 crits in crit/ exist
- step4 (new instance 21:34): read r1 crits. Common: springs too weak (<1.2px), ribbons straight stiff 1px spikes, head nod/drift too big, settle not neutral, bob uneven. Fixing in mact/mrender.
- step5: heads96 contract = per-frame 'head' block {expr,tilt,nod,turn (-1/0/1), dx,dy px, sec:{B,l,r,w,t: rest|lagL|lagR|lift|drop}} (compose_head.py docstring). Will emit 'head' + raw head_xf/secondary in final frames.json.
- step6: frames_M.py post layer added (tune.json <act>.post {'*'|name|name@VIEW|last}: head_k, sq, lift, roll, off, lean, arm_in, rest_k). backups /tmp/*.r1bak
- step7: mrender r2 springs: softer DEF, GAIN (angular exaggeration hair 2.2-2.4, hem 2, rib 1.4), HANG rib .55 (gravity hang), ribbons wider/spread; tune.json r2 posts per act (backup /tmp/tune.r1.json). walk SE r2 rendered (6 s/view). rendering all r2 SE,E
- step8: fixed loop sample alignment bug (frame 0 secondary missing in run); post keys hx_to/hyz; run head x -> -34; idle weight shift via per-view roll (SE/S -, NE/N +). r2 all re-rendered
- step9: vs_r1.gif (r1 vs r2 same clock) in prev/r2/*; running r2 crits
- step10: r2 scores walk 7/6 run 7/6 idle 7/6 (argon/opus)
  jump 7/6 dash 7/5 hurt 7/5 throw 6/6
- step11: r3 changes: ribbons shorter (.32), hang .75, gain 1, max 45, more tip lag; per-key spring 'kick' [fwd,up] (post key -> pose _kick -> mrender); post 'hx' add; tune r3 for all acts (walk SE roll fix 2nd half, run halves, idle roll x.6, dash skid kick, hurt hit chin back+kick, throw off back + head_k .3). arm_in only moves R hand (L wide = fwd swing in SE)
- step12: r3 rendered all (dash skid kick 6, trav skid 1) + vs_r2.gif; running r3 crits
