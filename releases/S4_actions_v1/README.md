
## Post-release note (r12)
`data/props/crate.json` snow mound was flattened in r12 (HD model work). Body sheets for all carry clips are
byte-identical to this release; only the crate `*_prop_front/back.png` strips change slightly (flatter snow cap).
Rebuild with `python -m pipeline.build --variant S4_halfup_bow --anim <clip>` to get the updated strips.
