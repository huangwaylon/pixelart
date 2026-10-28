#!/bin/zsh
# artist.sh TASKNAME ACCOUNT  -> runs SPEC+task with retries, output crit/task_NAME_out.txt
cd /Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/anim_cut
for i in 1 2 3 4; do
  zsh -ic "claude-as $2 --dangerously-skip-permissions --model claude-opus-5-5 -p \"\$(cat work/SPEC.txt work/task_$1.txt)\"" < /dev/null > crit/task_$1_out.txt 2>&1
  grep -qE "API Error|Proxy startup failed|ECONNREFUSED" crit/task_$1_out.txt || break
  sleep 60
done
