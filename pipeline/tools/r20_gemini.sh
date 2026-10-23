#!/bin/sh
# r20: one turn of a persistent Gemini 4 Argon conversation (Track G). Tools off: Gemini only writes text/code.
#   pipeline/tools/r20_gemini.sh <session-id> <prompt-file> <reply-file> [img1.png ...]
# Session files live in work/r20/gemini/sessions (so later turns remember earlier ones).
set -e
pipeline/tools/gemini_auth.sh || exit 1
sid="$1"; prompt="$2"; reply="$3"; shift 3
files=""
for f in "$@"; do files="$files @$f"; done
mkdir -p work/r20/gemini/sessions
env -u CLAUDE_TLS_CERT_PATH -u CLAUDE_TLS_KEY_PATH perl -e "alarm 1500; exec @ARGV" \
  pi -p --model apple-gemini/gemini-4-argon --session-dir work/r20/gemini/sessions --session-id "$sid" \
     --no-context-files --no-tools $files "$(cat "$prompt")" > "$reply" 2>&1
echo "wrote $reply ($(wc -c < "$reply") bytes)"
