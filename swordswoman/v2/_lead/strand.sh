#!/bin/bash
# Supervised headless Claude strand that survives the lead session dying.
# Usage: strand.sh <name> <account>   (reads v2/<name>/TASK.md; stops when v2/<name>/DONE exists)
# Launch detached: .venv/bin/python v2/_lead/detach.py /bin/bash v2/_lead/strand.sh <name> <account>
# On exit (DONE, attempts exhausted, or TERM/INT) it kills its whole child tree and deregisters from detached.txt.
name=$1; acct=$2
root=/Users/waylonhuang/Documents/other/pixelart/swordswoman; v2=$root/v2; dir=$v2/$name; log=$v2/_lead/$name.log
reg=$v2/_lead/detached.txt
sidf=$v2/_lead/$name.sid; [ -f $sidf ] || uuidgen | tr A-Z a-z > $sidf; sid=$(cat $sidf)
d=$HOME/.passport/$acct
first="You are the $(echo $name | tr a-z A-Z) strand of a team making simplified chibi-swordswoman pixel-art sprites and animations. A lead coordinates; you run headless and autonomously, and nobody will answer questions, so make reasonable decisions. Read, in order: $v2/BRIEF.md, $dir/NOTES.md (your own past progress log; you are continuing that work), and $dir/TASK.md (your current task). Work from $root. Append to $dir/NOTES.md after every completed step: what was done, the image paths, and the scores. A crash must lose nothing. For critiques, call Opus with: claude-as <account> --dangerously-skip-permissions --model claude-opus-5-5 -p '...' (zsh function; use zsh -ic if needed), and Argon with: .venv/bin/python tools/gemini.py ask. Keep tool outputs small. Run long jobs in the foreground or wait for them. Before you stop, kill any background processes you started (Blender, python, gemini, claude-as) and delete temp files you made outside v2/. When TASK.md is fully done, write a short summary to $dir/DONE (results, GIF paths, scores, blockers) and stop."
first="$first Run long jobs in the foreground or wait for them. Before you stop, kill any background processes you started (Blender, python, gemini, claude-as) and delete temp files you made outside v2/."
killtree() { local c; for c in $(pgrep -P $1); do killtree $c; done; [ $1 != $$ ] && kill $1 2>/dev/null; }
cleanup() { trap - EXIT TERM INT; echo "=== cleanup $(date)" >> $log; killtree $$; sed -i '' "/^$$ strand:$name /d" $reg; exit 0; }
trap '' HUP
trap cleanup EXIT TERM INT
cd $root
echo "$$ strand:$name $(date +%FT%T)" >> $reg
for attempt in $(seq 1 30); do
  [ -f $dir/DONE ] && break
  # Wait (up to ~1h) for floodgate to be reachable instead of burning attempts during VPN drops.
  for w in $(seq 1 120); do curl -s -o /dev/null --max-time 10 https://floodgate.g.apple.com/ && break; sleep 30; done
  openssl x509 -checkend 7200 -noout -in "$d/cert.pem" >/dev/null 2>&1 || ~/.claude/claude-be/keepalive.sh >/dev/null 2>&1
  echo "=== attempt $attempt $(date)" >> $log
  if ! grep -q started $v2/_lead/$name.state 2>/dev/null; then
    echo started > $v2/_lead/$name.state
    args=(--session-id $sid -p "$first")
  else
    args=(--resume $sid -p "You were interrupted (crash, network drop or timeout). Re-read $dir/NOTES.md and $dir/TASK.md and continue where you left off. Write $dir/DONE when finished.")
  fi
  env -u APPLE_CLAUDE_CODE_PROXY_URL -u APPLE_CLAUDE_CODE_PORT APPLE_CLAUDE_CODE_API_BASE_URL=https://floodgate.g.apple.com \
    CLAUDE_TLS_CERT_PATH="$d/cert.pem" CLAUDE_TLS_KEY_PATH="$d/key.pem" \
    claude --dangerously-skip-permissions --model claude-opus-5-5 "${args[@]}" >> $log 2>&1 < /dev/null
  echo "=== exit $? $(date)" >> $log
  sleep 30
done
echo "=== supervisor end $(date)" >> $log
