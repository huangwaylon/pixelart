#!/bin/sh
# Make sure pi/Gemini (Apple Floodgate) auth works before a Gemini call.
#   pipeline/tools/gemini_auth.sh            -> exit 0 when Gemini answers
#   . pipeline/tools/gemini_env.sh           -> (sourced) sets up the env for direct `pi` calls
#
# ROOT CAUSE of the recurring "No authentication method found" (found 2026-10-23):
#   apple-pi tries Narrative mTLS first and only then an appleconnect bearer
#   (~/.pi/versions/*/app/node_modules/@apple/pi-apple-provider/src/auth.ts, narrativePaths()).
#   Inside Claude Code, CLAUDE_TLS_CERT_PATH / CLAUDE_TLS_KEY_PATH are set (Claude Code's own client cert); pi picks
#   them up as its lowest-precedence mTLS source, Floodgate does not accept that identity for Gemini, and no bearer is
#   sent. It only *seemed* to work for ~50 min after the user ran pi in a normal terminal because pi reused the bearer
#   token that run had cached in the Keychain; once it expired, pi re-acquired via the Claude cert and failed.
# FIX: run pi with those two variables unset -> pi mints the bearer silently with appleconnect (no prompt needed while
#   the AppleConnect session is alive). If the AppleConnect session itself ever lapses, fall back to a GUI sign-in.
CRED=hvys3fcwcteqrvw3qzkvtk86viuoqv
SCOPES=openid,dsid,accountname,profile,groups
gem_ping() { env -u CLAUDE_TLS_CERT_PATH -u CLAUDE_TLS_KEY_PATH perl -e 'alarm 90; exec @ARGV' \
         pi -p --model apple-gemini/gemini-4-argon --no-session --no-context-files \
         --no-tools "Reply with: ok" 2>&1 | grep -v "^$" | tail -1; }
is_ok() { [ "$(printf %s "$1" | tr -d '[:space:].!' | tr '[:upper:]' '[:lower:]')" = ok ]; }   # NB "token" contains "ok"
r=$(gem_ping); is_ok "$r" && exit 0; sleep 5; r=$(gem_ping); is_ok "$r" && exit 0
echo "gemini auth: silent mint failed ($r); requesting AppleConnect sign-in (GUI)..." >&2
appleconnect getToken -C $CRED --token-type=oauth --interactivity-type=gui -E prod -G pkce -o $SCOPES -O json \
  >/dev/null 2>&1 || { echo "gemini auth: AppleConnect sign-in failed or was cancelled" >&2; exit 1; }
r=$(gem_ping); is_ok "$r" && exit 0; sleep 5; r=$(gem_ping); is_ok "$r" && exit 0
echo "gemini auth: still failing after sign-in: $r" >&2; exit 1
