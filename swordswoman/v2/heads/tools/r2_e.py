#!/usr/bin/env python3
"""r2 E (true profile, facing screen right) head set. Writes e/*.txt."""
from r2_se import H, write, put, hair, shade, insert_col

EXT = [(8, 13), (5, 16), (3, 18), (2, 19), (1, 20), (1, 20), (0, 20), (0, 20), (0, 21), (0, 21), (0, 21),
       (0, 20), (0, 20), (0, 20), (1, 20), (1, 21), (1, 20), (2, 20), (3, 19), (4, 18), (5, 11), (6, 7)]
N = hair(EXT, 22)
put(N, 0, 8, '######')
put(N, 1, 5, '###'); put(N, 1, 14, '###'); put(N, 2, 3, '##'); put(N, 2, 17, '##')
put(N, 20, 5, '#hh####'); put(N, 21, 6, '##')
N = shade(N)
N = [r[:4] + r[4:20].replace('j', 'H') + r[20:] if y < 5 else r for y, r in enumerate(N)]
# face (profile): fringe shelf juts 1px past the forehead, brow+lash+eye in the SE style, nose bump, soft chin
put(N, 10, 13, 'hHHHHhh#')                       # shelf underside row
put(N, 11, 12, 'hHHH33H2#')                      # brow row (fringe tips, brow peeking)
put(N, 12, 12, 'hhh###22#')                      # lash line
put(N, 13, 12, 'hH22wi22#')
put(N, 14, 12, 'hH22iI22#')
put(N, 15, 12, 'hH22II222#')                     # nose bump
put(N, 16, 12, 'hH222222#')
put(N, 17, 12, 'hH222221#')                      # mouth
put(N, 18, 4, 'hhhhHHHHhh22221#')               # small soft chin
put(N, 19, 5, 'hhhhhhh#######')                  # jaw underside / neck row
put(N, 9, 15, 'h'); put(N, 10, 15, 'h')          # fringe strand splits
put(N, 16, 9, 'hhh'); put(N, 17, 8, 'hhhh'); put(N, 18, 8, 'hhhh')  # nape shadow under the side lock
META_N = ['; pivot 15 19', '; anchor bow 11 3', '; anchor bun 4 -1']

BOW = [  # foreshortened: far loop (dark, behind/left), knot, near loop (bright, front/right)
    '.##....####.',
    '#ER#..#eeeE#',
    '#ERR#EeEEER#',
    '#RRr#EEEERR#',
    '.##.#RRRRRr#',
    '.....#rrr##.',
    '......###...',
]
BUN = ['..###..', '.#jHH#.', '#jHHHh#', '#HHHHh#', '#HHHhh#', '.#hhh#.', '..###..']

B = N[:]
U = N[:]
put(U, 9, 13, 'hHHHHhh#'); put(U, 10, 12, 'hHHH33H2#'); put(U, 11, 12, 'hhh22222#')
put(U, 13, 16, 'wI'); put(U, 14, 16, 'II'); put(U, 15, 16, 'ww')
L = ['.' + r for r in N]
L = L[:10] + [L[9]] + L[10:]
S = insert_col(insert_col(N, 14), 4)
S = S[:3] + S[4:6] + S[7:]
BOWS = [r[:2] + r[1:8] + r[7:] for r in BOW]
BOWS = BOWS[:2] + BOWS[3:]
if __name__ == '__main__':
    write('e/head_neutral.txt', N, META_N)
    write('e/head_lookup.txt', U, META_N)
    write('e/head_lean.txt', L, ['; pivot 15 19', '; anchor bow 12 3', '; anchor bun 5 -1'])
    write('e/head_squash.txt', S, ['; pivot 16 17', '; anchor bow 12 2', '; anchor bun 5 -2'])
    write('e/bow.txt', BOW, ['; pivot 6 6'])
    write('e/bow_squash.txt', BOWS, ['; pivot 7 5'])
    write('e/bun.txt', BUN, ['; pivot 3 3'])
    print('ok')
