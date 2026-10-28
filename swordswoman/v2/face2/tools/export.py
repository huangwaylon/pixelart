"""export.py: write out/sprite/<VIEW>_<expr>.txt (+ _1x/_8x png) for S SE E NE N, and anchors.json (head-local + 64-cell coords)."""
import sys, json; sys.path.insert(0,'/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/face2/tools'); import kit, pal
O='/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/face2/'
DX,DY=24,9     # head-local (tile) -> 64 cell: tile row 4 (crown) = cell row 13, tile col 0 = cell col 24 (head 16 px: cols 24-39)
for v in ['S','SE','E','NE','N']:
    for e in kit.EXPR if v!='N' else ['neutral']:
        rows=kit.build(v,e); open(O+f'out/sprite/{v}_{e}.txt','w').write('\n'.join(rows)+'\n')
        pal.to_img(rows).save(O+f'out/sprite/{v}_{e}_1x.png'); pal.to_img(rows,8).save(O+f'out/sprite/{v}_{e}_8x.png')
A={'_doc':"FACE2 anchors. Tile = 19x22 char map (out/sprite/<VIEW>_<expr>.txt, '.' = transparent). Head: crown tile row 4, chin outline tile row 18 (15 px), neck from row 19; hair mass cols 0-15 (16 px). "
 "To place on a 64-cell master: cell = tile + (dx,dy) = (+24,+9) -> crown row 13, chin outline row 27, neck row 28 (prop/blockout/head_region.json: crown may rise to 13, chin line 28, cols 24-39). "
 "Eye stamp = kit.EYE[expr] (5 cols x 6 rows: c0 lash wing, c1-3 eye, c4 inner margin; r0 brow row, r1-5 eye), right/far eye mirrored; far SE eye = kit.far(); profile = kit.PROF_E (4 cols). "
 "Mouth stamp = 4x3 (row0 cheek, row1 mouth, row2 jaw) at 'mouth'; profile mouths kit.MOUTH_E2 (3x3, '_' cuts the silhouette). Blush = BLUSH[expr] px of k from 'blush'.",
 'offset_tile_to_cell':[DX,DY],'views':{}}
for v,H in kit.HEADS.items():
    if v not in ('S','SE','E','NE','N'): continue
    ent={'eyes':[{'stamp_x0':x,'brow_row':y,'eye_rows':[y+1,y+5],'mirror':m,'far':H.get('far')==i} for i,(x,y,m) in enumerate(H['eyes'])],
         'mouth_xy':H.get('mouth'),'blush_xy':H.get('blush'),'lash_cue_px':H.get('lash')}
    ent['cell']={'eyes':[{'stamp_x0':e['stamp_x0']+DX,'brow_row':e['brow_row']+DY} for e in ent['eyes']],'mouth_xy':[H['mouth'][0]+DX,H['mouth'][1]+DY] if H.get('mouth') else None}
    A['views'][v]=ent
A['eye_boxes_S_cell']={'left':[28,19,3,5],'right':[33,19,3,5],'note':'x,y,w,h; eye centre row 21 = 0.57 of the head (<=0.66 rule)'}
json.dump(A,open(O+'anchors.json','w'),indent=1); print('ok', len(kit.HEADS))
