#!/bin/zsh
# detach.sh LOG cmd...  -> runs cmd in a new session (survives lead restarts)
log=$1; shift
nohup perl -MPOSIX -e 'POSIX::setsid(); exec @ARGV' "$@" > "$log" 2>&1 < /dev/null &!
