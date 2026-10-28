#!/bin/zsh
# artist.sh NAME ACCOUNT PROMPTFILE -> mastersF/work/out_NAME.txt (retries on API errors)
cd /Users/waylonhuang/Documents/other/pixelart/swordswoman
for i in 1 2 3; do
  zsh -ic "claude-as $2 --dangerously-skip-permissions --model claude-opus-5-5 -p \"\$(cat $3)\"" < /dev/null > v2/mastersF/work/out_$1.txt 2>&1
  grep -qE "API Error|Proxy startup failed|ECONNREFUSED" v2/mastersF/work/out_$1.txt || break
  sleep 60
done
