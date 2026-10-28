#!/bin/bash
# Kill all detached lead tasks listed in detached.txt (whole process groups) and clear the registry.
f=/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/_lead/detached.txt
while read pid name t; do [ -n "$pid" ] && kill -- -$pid 2>/dev/null || kill $pid 2>/dev/null; echo "killed $pid $name"; done < $f
: > $f
