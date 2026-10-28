# tmpltry.py "r0" "r1" "r2" : apply front_left rows 0-2 (cols 0-4; '_' keep) to masters (S both eyes mirrored, SE near, E) and print face_ssim per view
import sys, subprocess
M = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/m96/masters/EC0_%s_96'
EY = {'S': [(56, 49, 1), (66, 49, -1)], 'SE': [(62, 50, 1)], 'E': [(72, 49, 1)]}
rows = sys.argv[1:4]; IR = set('@')
out = {}
for v in EY:
    ed = []
    for x0, y0, d in EY[v]:
        for j, r in enumerate(rows):
            for c, ch in enumerate(r):
                if ch == '_': continue
                if d == -1 and ch in 'hW@' and j >= 1 and 1 <= c <= 4 and ch != 'K': 
                    # right eye iris px stay unmirrored: write iris at the same template col
                    x = x0 + c
                else: x = x0 + c if d == 1 else x0 + 5 - c
                ed.append('%d,%d,%s' % (x, y0 + j, {'.': 's', '@': 'W'}.get(ch, ch)))
    out[v] = subprocess.run(['python3', 'eyes4/pxtry_n.py', M % v, v] + ed, capture_output=True, text=True).stdout.split()[-1]
print(' '.join(rows), out)
