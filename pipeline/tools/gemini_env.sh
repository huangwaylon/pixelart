# Source before calling `pi` for Gemini from inside Claude Code: stops pi from using Claude Code's mTLS cert
# (see gemini_auth.sh for the root cause).   . pipeline/tools/gemini_env.sh
unset CLAUDE_TLS_CERT_PATH CLAUDE_TLS_KEY_PATH
