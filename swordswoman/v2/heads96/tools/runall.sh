#!/bin/zsh
# runall.sh JOBFILE : <=6 concurrent artjob.py, round-robin over 3 accounts
cd /Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/heads96/tools
ACC=(bni_requests nsystem4 be_system); i=0
while read -r k v p; do
  a=${ACC[$((i % 3 + 1))]}; i=$((i+1))
  while [ $(jobs -r | wc -l) -ge 6 ]; do sleep 5; done
  /Users/waylonhuang/Documents/other/pixelart/swordswoman/.venv/bin/python artjob.py $k $v $p $a >> ../art/runall.log 2>&1 &
done < $1
wait; echo ALLDONE >> ../art/runall.log
