#!/bin/zsh
# artist.sh NAME ACCOUNT PROMPTFILE(abs) -> final/work/out_NAME.txt (retries on API errors)
cd /Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/final
for i in 1 2 3; do
  zsh -ic "claude-as $2 --dangerously-skip-permissions --model claude-opus-5-5 -p \"\$(cat $3)\"" < /dev/null > work/out_$1.txt 2>&1
  grep -qE "API Error|Proxy startup failed|ECONNREFUSED|usage limit|rate limit" work/out_$1.txt || break
  sleep 60
done
