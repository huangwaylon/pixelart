#!/bin/zsh
# art.sh TASK ACCOUNT -> work/out_TASK.txt
cd /Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/masters
for i in 1 2 3; do
  zsh -ic "claude-as $2 --dangerously-skip-permissions --model claude-opus-5-5 -p \"\$(cat work/SPEC.txt work/task_$1.txt)\"" < /dev/null > work/out_$1.txt 2>&1
  grep -qE "API Error|Proxy startup failed|ECONNREFUSED" work/out_$1.txt || break
  sleep 60
done
