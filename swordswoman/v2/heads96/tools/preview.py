"""preview.py VIEW OUT.png [scale] [cols]: composites of the main poses for review"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cm import *
from compose_head import compose_stamp
from PIL import Image
POSES = [('rest', {}), ('tiltL', {'tilt': -1}), ('tiltR', {'tilt': 1}), ('nod dn', {'nod': 1}), ('nod up', {'nod': -1}), ('turnR', {'turn': 1}),
         ('lagL', {'sec': dict.fromkeys('Blrwt', 'lagL')}), ('lagR', {'sec': dict.fromkeys('Blrwt', 'lagR')}),
         ('lift', {'sec': dict.fromkeys('Blrwt', 'lift')}), ('drop', {'sec': dict.fromkeys('Blrwt', 'drop')}),
         ('tL+lagR joy', {'tilt': -1, 'expr': 'joy', 'sec': dict.fromkeys('Blrwt', 'lagR')}), ('tR+dn shout', {'tilt': 1, 'nod': 1, 'expr': 'shout', 'sec': dict.fromkeys('Blrwt', 'drop')})]
def main(v, out, sc=3, cols=6):
    ims = [to_img(compose_stamp(v, s)[0], sc, '#6e6e6e') for _, s in POSES]
    w, h = ims[0].size; rows = (len(ims) + cols - 1) // cols
    sh = Image.new('RGBA', (cols * (w + 2), rows * (h + 2)), (40, 40, 40, 255))
    for i, im in enumerate(ims): sh.paste(im, ((i % cols) * (w + 2), (i // cols) * (h + 2)))
    sh.save(out); print(out, sh.size)
if __name__ == '__main__':
    a = sys.argv[1:]; main(a[0], a[1], int(a[2]) if len(a) > 2 else 3, int(a[3]) if len(a) > 3 else 6)
