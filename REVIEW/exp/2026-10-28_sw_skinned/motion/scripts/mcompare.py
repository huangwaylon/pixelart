"""mcompare.py (M): side-by-side GIF  OLD (hires3d grid, cel_kc_hs column) | NEW (skinned rig + new motion, R's pixel chain, head stamp).
usage: python mcompare.py ACT NEW_GIF OUT_GIF [old_col]"""
import sys
from PIL import Image, ImageSequence, ImageDraw

OLD = "/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_hires3d/gifs/grid_{}_SE.gif"


def frames(p):
    im = Image.open(p); out = []
    for f in ImageSequence.Iterator(im): out.append((f.convert("RGB").copy(), f.info.get("duration", 100)))
    return out


def main(act, new_gif, out, col=1):
    old = [(f.crop((252 * col, 14, 252 * (col + 1), 356)), d) for f, d in frames(OLD.format(act))]
    new = frames(new_gif); H = old[0][0].height
    new = [(f.resize((int(f.width * H / f.height), H), Image.NEAREST), d) for f, d in new]
    # common timeline (10 ms ticks), 2 loops of the longer clip
    def at(seq, t):
        T = sum(d for _, d in seq); t %= T
        for i, (_, d) in enumerate(seq):
            if t < d: return i
            t -= d
        return len(seq) - 1
    L = 2 * max(sum(d for _, d in old), sum(d for _, d in new)); ev = []
    for t in range(0, L, 10):
        k = (at(old, t), at(new, t))
        if ev and ev[-1][0] == k: ev[-1][1] += 10
        else: ev.append([k, 10])
    W = old[0][0].width + new[0][0].width + 8; imgs = []
    for (i, j), d in ev:
        c = Image.new("RGB", (W, H + 18), (110, 110, 110)); c.paste(old[i][0], (0, 18)); c.paste(new[j][0], (old[0][0].width + 8, 18))
        dr = ImageDraw.Draw(c); dr.text((4, 3), f"OLD (H2 rigid rig) f{i}", fill=(255, 255, 255)); dr.text((old[0][0].width + 12, 3), f"NEW (skinned + new motion) f{j}", fill=(255, 255, 160))
        imgs.append(c)
    imgs[0].save(out, save_all=True, append_images=imgs[1:], duration=[d for _, d in ev], loop=0)
    print(out, len(imgs))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else 1)


def abboard(act, out):
    """A/B still board: row A = OLD frames (hires3d grid, cel_kc_hs), row B = NEW pixel frames (R chain + head stamp), numbered."""
    import os, json
    E = "/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_skinned/motion"
    old = [f.crop((252, 14, 504, 356)) for f, d in frames(OLD.format(act))]
    od = [d for f, d in frames(OLD.format(act))]
    pdir = f"{E}/prev/px/{act}/{act}_SE_px_hs"; m = json.load(open(f"{E}/{act}.json"))
    new = [Image.open(f"{pdir}/f{k:02d}.png").convert("RGBA") for k in range(len(m["frames"]))]
    S = 3; new2 = []
    bb = None
    for im in new:
        b_ = im.getchannel("A").getbbox(); bb = b_ if bb is None else (min(bb[0], b_[0]), min(bb[1], b_[1]), max(bb[2], b_[2]), max(bb[3], b_[3]))
    cx = (bb[0] + bb[2]) // 2; yb = bb[3] + 3
    for im in new:
        bg = Image.new("RGBA", im.size, (110, 110, 110, 255)); bg.alpha_composite(im); im = bg.convert("RGB")
        im = im.crop((cx - 42, yb - 114, cx + 42, yb)).resize((252, 342), Image.NEAREST); new2.append(im)
    cw = 252; W = cw * max(len(old), len(new2)); H = 342 * 2 + 60
    B = Image.new("RGB", (W, H), (50, 50, 50)); d = ImageDraw.Draw(B)
    d.text((4, 2), f"A = OLD {act} (rejected: stiff)  frames f0..f{len(old)-1}, ms {od}", fill=(255, 255, 255))
    for k, im in enumerate(old): B.paste(im, (k * cw, 16)); d.text((k * cw + 4, 18), f"A f{k}", fill=(255, 255, 0))
    y = 342 + 40; d.text((4, y - 18), f"B = NEW {act}  frames f0..f{len(new2)-1}, ms {m['timing_ms']}", fill=(255, 255, 255))
    for k, im in enumerate(new2): B.paste(im, (k * cw, y)); d.text((k * cw + 4, y + 2), f"B f{k} {m['frames'][k].get('key','')}", fill=(255, 255, 0))
    B.save(out); print(out)


def sbs(ga, gb, out, la="ROUND 1", lb="ROUND 2"):
    """side-by-side GIF of two GIFs on a common 10 ms timeline (2 loops of the longer)."""
    A = frames(ga); Bf = frames(gb); H = max(A[0][0].height, Bf[0][0].height)
    def at(seq, t):
        T = sum(d for _, d in seq); t %= T
        for i, (_, d) in enumerate(seq):
            if t < d: return i
            t -= d
        return len(seq) - 1
    L = 2 * max(sum(d for _, d in A), sum(d for _, d in Bf)); ev = []
    for t in range(0, L, 10):
        k = (at(A, t), at(Bf, t))
        if ev and ev[-1][0] == k: ev[-1][1] += 10
        else: ev.append([k, 10])
    W = A[0][0].width + Bf[0][0].width + 8; ims = []
    for (i, j), d in ev:
        c = Image.new("RGB", (W, H + 18), (110, 110, 110)); c.paste(A[i][0], (0, 18)); c.paste(Bf[j][0], (A[0][0].width + 8, 18))
        dr = ImageDraw.Draw(c); dr.text((4, 3), f"{la} f{i}", fill=(255, 255, 255)); dr.text((A[0][0].width + 12, 3), f"{lb} f{j}", fill=(255, 255, 160)); ims.append(c)
    ims[0].save(out, save_all=True, append_images=ims[1:], duration=[d for _, d in ev], loop=0); print(out)
