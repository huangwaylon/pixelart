# rzip.py URL [list PATTERN | get NAME... OUTDIR]  - read a remote zip with HTTP range requests (no full download)
import sys, io, zipfile, urllib.request, re, os
class R(io.RawIOBase):
    def __init__(s, u):
        s.u = u; s.p = 0
        q = urllib.request.Request(u, method="HEAD"); r = urllib.request.urlopen(q); s.n = int(r.headers["Content-Length"]); s.u = r.url
    def seekable(s): return True
    def readable(s): return True
    def tell(s): return s.p
    def seek(s, o, w=0):
        s.p = o if w == 0 else s.p + o if w == 1 else s.n + o; return s.p
    def readinto(s, b):
        if s.p >= s.n: return 0
        e = min(s.n, s.p + len(b)) - 1
        d = urllib.request.urlopen(urllib.request.Request(s.u, headers={"Range": f"bytes={s.p}-{e}"})).read()
        b[:len(d)] = d; s.p += len(d); return len(d)
z = zipfile.ZipFile(io.BufferedReader(R(sys.argv[1]), 1 << 20))
if sys.argv[2] == "list":
    for i in z.infolist():
        if re.search(sys.argv[3], i.filename): print(i.filename, i.file_size)
else:
    out = sys.argv[-1]; os.makedirs(out, exist_ok=True)
    for n in sys.argv[3:-1]: open(os.path.join(out, os.path.basename(n)), "wb").write(z.read(n)); print("got", n)
