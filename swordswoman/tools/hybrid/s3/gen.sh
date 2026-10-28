#!/bin/zsh
# usage: gen.sh OUT PROMPTFILE ref1 ref2 ... ; retries 3, logs to OUT.log
out=$1; pf=$2; shift 2
for i in 1 2 3; do
  .venv/bin/python tools/gemini.py image "$(cat $pf)" $out "$@" > ${out%.png}.log 2>&1 && exit 0
  sleep 5
done
exit 1
