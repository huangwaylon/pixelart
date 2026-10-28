import sys; from PIL import Image
im = Image.open(sys.argv[1]); b = tuple(map(int, sys.argv[3].split(','))); c = im.crop(b); c.thumbnail((800, 800)); c.save(sys.argv[2]); print(c.size)
