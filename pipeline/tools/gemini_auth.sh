#!/bin/sh
# Make sure pi/Gemini (Apple Floodgate) auth works before a Gemini call.
#   pipeline/tools/gemini_auth.sh            -> exit 0 when Gemini answers
# How auth works (apple-pi docs: ~/.pi/versions/*/app/node_modules/@apple/pi-apple-provider/docs/auth.md):
#   pi mints an IDMS id_token with `appleconnect getToken ... --interactivity-type=none`, caches it in the Keychain
#   (service PiAppleProvider) for ~50 min and re-mints silently while the AppleConnect *session* is alive.
#   "No authentication method found" = the AppleConnect session lapsed, so the silent mint failed.
# Fix here: on failure, ask AppleConnect for the token with --interactivity-type=gui (pops the normal
#   AppleConnect sign-in / Touch ID window on the user's screen, like Claude Code does), then retry.
# Permanent alternative: a Narrative mTLS client cert (FLOODGATE_NARRATIVE_CERTPATH / _KEYPATH) needs no session.
CRED=hvys3fcwcteqrvw3qzkvtk86viuoqv
SCOPES=openid,dsid,accountname,profile,groups
gem_ping() { perl -e 'alarm 90; exec @ARGV' pi -p --model apple-gemini/gemini-4-argon --no-session --no-context-files \
         --no-tools "Reply with: ok" 2>&1 | grep -v "^$" | tail -1; }
is_ok() { [ "$(printf %s "$1" | tr -d '[:space:].!' | tr '[:upper:]' '[:lower:]')" = ok ]; }   # NB "token" contains "ok"
r=$(gem_ping); is_ok "$r" && exit 0
echo "gemini auth: silent mint failed ($r); requesting AppleConnect sign-in (GUI)..." >&2
appleconnect getToken -C $CRED --token-type=oauth --interactivity-type=gui -E prod -G pkce -o $SCOPES -O json \
  >/dev/null 2>&1 || { echo "gemini auth: AppleConnect sign-in failed or was cancelled" >&2; exit 1; }
r=$(gem_ping); is_ok "$r" && exit 0
echo "gemini auth: still failing after sign-in: $r" >&2; exit 1
