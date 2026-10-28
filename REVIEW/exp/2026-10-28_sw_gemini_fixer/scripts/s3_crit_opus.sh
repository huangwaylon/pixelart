#!/bin/zsh
# Opus critics, sequential (parallel claude-as launches failed: proxy port exhaustion). Prompts = s3_crit.sh.
E=${0:A:h:h}; B=$E/boards
eval "$(sed -n '/^P_SE=/p;/^P_POSE=/p' $E/scripts/s3_crit.sh)"
cd /Users/waylonhuang/Documents/other/pixelart/swordswoman
zsh -ic "claude-as be_system --dangerously-skip-permissions --model claude-opus-5-5 -p \"Read the image $B/b2_SE.png with the Read tool. $P_SE\"" > $E/crit/opus_SE.txt 2>&1
zsh -ic "claude-as be_system --dangerously-skip-permissions --model claude-opus-5-5 -p \"Read image 1 $B/b4_consistency_hn.png and image 2 $B/b3_poses_hn.png with the Read tool. $P_POSE\"" > $E/crit/opus_poses.txt 2>&1
wc -c $E/crit/opus_*.txt
