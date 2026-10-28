"""list body orphans exactly as metrics.py counts them: orph.py files..."""
import sys, os
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/tools/hybrid'); sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/tools/pixel')
import metrics as M
H, L = M.H, M.L
def orphans(path):
    a = H.load_rgba(path); idx = H.index_of(a)
    flags, _, _ = L.lint_frame(a, H.palette(), None, None)
    sword = H.disk_op(H.base_mask(idx, 'steel'), 1)
    return [(f['x'], f['y'], f.get('detail')) for f in flags if f['type'] == 'orphan' and f.get('detail') not in H.ORPHAN_OK and not sword[f['y'], f['x']]]
if __name__ == '__main__':
    for p in sys.argv[1:]: print(os.path.basename(p), orphans(p))
