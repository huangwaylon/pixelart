#!/bin/zsh
# full replay: compose (turns first: actions take their scale) -> retone -> erase k1 smear -> auto -> hand -> assemble
export DOWN=mode BODY_PX=${BODY_PX:-31}
for a in turn_S turn_SE turn_E turn_NE turn_N turn_NW turn_W turn_SW; do .venv/bin/python tools/hybrid/s3/compose.py $a & done; wait
for a in walk_SE_k0 walk_SE_k1:2 walk_SE_k2 walk_SE_k3 slash_SE_k0:1 slash_SE_k1 slash_SE_k2:1 slash_SE_k3 jump_E_crouch:2 jump_E_apex jump_E_land:2; do .venv/bin/python tools/hybrid/s3/compose.py $a & done; wait
.venv/bin/python tools/hybrid/s3/p_retone.py && .venv/bin/python tools/hybrid/s3/p_slash.py k1 && .venv/bin/python tools/hybrid/s3/p_auto.py && .venv/bin/python tools/hybrid/s3/p_hand.py && .venv/bin/python tools/hybrid/s3/assemble.py
