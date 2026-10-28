#!/usr/bin/env python3
"""Force-add every image/GIF referenced by REVIEW/entries/*.json, so hub media is always committed even when it
lives inside an ignored intermediate folder. Run from anywhere: python3 REVIEW/stage_media.py"""
import glob, json, os, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
paths = []
for p in glob.glob(os.path.join(HERE, 'entries', '*.json')):
    for m in json.load(open(p)).get('media', []):
        f = os.path.normpath(os.path.join(HERE, m['src']))
        if os.path.exists(f):
            paths.append(f)
if paths:
    subprocess.run(['git', '-C', HERE, 'add', '-f', '--'] + sorted(set(paths)), check=True)
print(f'staged {len(set(paths))} hub media files')
