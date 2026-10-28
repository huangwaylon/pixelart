# Gemini 4 Argon: r17_s1_head

_Images sent:_ refs ref2 ref3 ref5 ref6 ref8 ref9 (user references, not in repo)

## Prompt

You are an expert technical artist writing a procedural numpy-only generator for a stylised anime 3D character, in SECTIONS. SECTION 0 (core helpers, mesher, LM landmarks, main) is already written and is given below. Now write ONLY the section defining `build_head()` - HEAD, FACE AND NECK: anime head construction (cranium, cheek planes turning into a narrow jaw, small pointed chin, slim neck to the collarbones), the face features as separate material parts: eye_white almond recesses/inset discs, iris discs with a darker pupil area (use 'iris' and 'lash'), a thick winged upper lash ('lash') and a thin lower lash, brows ('hair_shadow'), small nose with a defined tip (part of skin), small full lips ('mouth'). Ears hidden under hair (small or omitted). Use fine cells (0.0015-0.002) for the face features.

Rules: one ~~~python block, at most ~170 lines; use only numpy/math and the SECTION 0 helpers (add_part, sd_*, smin/smax/ssub, rotate_axis, sd_swept_ribbon, catmull_rom, LM); do not redefine SECTION 0 names (prefix your own helpers with _head_); no file or network access. Give every add_part a tight bbox and a sensible cell size (0.002-0.004) so the whole section meshes in under ~60 s and yields roughly 10k-40k triangles. Respect the axes: +Y up, she faces +Z, +X is HER LEFT, feet at y=0, height ~1.0. Make every shape designed and appealing (anime toon, smooth, no lumps). The attached images are style references (see the description). After the code block, give at most 5 lines of notes.

===== SECTION 0 (already written) =====
~~~python
import numpy as np, sys, os, math

# --- 1. SDF Primitives & Operations (all accept p: (N,3) float array, return (N,) float array) ---
def smin(a, b, k=0.01):
    h = np.clip(0.5 + 0.5 * (b - a) / np.maximum(k, 1e-8), 0.0, 1.0)
    return b * (1.0 - h) + a * h - k * h * (1.0 - h)

def smax(a, b, k=0.01): return -smin(-a, -b, k)
def ssub(a, b, k=0.01): return smax(a, -b, k) # subtract b from a

def translate(p, offset): return p - np.asarray(offset, dtype=np.float32)

def rotate_axis(p, axis, angle_rad):
    axis = np.asarray(axis, dtype=np.float32)
    axis = axis / (np.linalg.norm(axis) + 1e-12)
    c, s = math.cos(-angle_rad), math.sin(-angle_rad)
    return p * c + np.cross(axis, p) * s + np.outer(p @ axis, axis) * (1.0 - c)

def sd_sphere(p, c, r):
    return np.linalg.norm(p - np.asarray(c, dtype=np.float32), axis=-1) - r

def sd_ellipsoid(p, c, r):
    q = p - np.asarray(c, dtype=np.float32)
    r = np.asarray(r, dtype=np.float32)
    k0 = np.linalg.norm(q / r, axis=-1)
    k1 = np.linalg.norm(q / (r * r), axis=-1)
    return k0 * (k0 - 1.0) / np.maximum(k1, 1e-8)

def sd_round_box(p, c, b, r=0.005):
    q = np.abs(p - np.asarray(c, dtype=np.float32)) - np.asarray(b, dtype=np.float32)
    return np.linalg.norm(np.maximum(q, 0.0), axis=-1) + np.minimum(np.max(q, axis=-1), 0.0) - r

def sd_capsule(p, a, b, r):
    a, b = np.asarray(a, dtype=np.float32), np.asarray(b, dtype=np.float32)
    pa, ba = p - a, b - a
    h = np.clip((pa @ ba) / (np.dot(ba, ba) + 1e-12), 0.0, 1.0)
    return np.linalg.norm(pa - np.outer(h, ba), axis=-1) - r

def sd_round_cone(p, a, b, r1, r2):
    a, b = np.asarray(a, dtype=np.float32), np.asarray(b, dtype=np.float32)
    ba = b - a
    l2 = float(np.dot(ba, ba))
    if l2 < 1e-12: return sd_sphere(p, a, max(r1, r2))
    rr, a2 = float(r1 - r2), l2 - float(r1 - r2)**2
    il2 = 1.0 / l2
    pa = p - a
    y = pa @ ba
    z = y - l2
    x2 = np.sum(pa * pa, axis=-1) * l2 - y * y
    y2, z2 = y * y * l2, z * z * l2
    k = np.sign(rr) * rr * rr * x2
    d = np.sqrt(np.maximum(a2 * (x2 + z2) - 2.0 * rr * np.sqrt(np.maximum(x2, 0.0)) * z * il2 * l2, 0.0)) * il2 - r2
    m1 = np.sqrt(np.maximum(x2 + z2, 0.0)) * il2 - r2
    m2 = np.sqrt(np.maximum(x2 + y2, 0.0)) * il2 - r1
    return np.where(np.sign(z) * a2 * z2 > k, m1, np.where(np.sign(y) * a2 * y2 < k, m2,
           (np.sqrt(np.maximum(x2 * a2 * il2, 0.0)) + y * rr) * il2 - r1))

def sd_torus(p, c, R, r, axis=(0,1,0)):
    q = p - np.asarray(c, dtype=np.float32)
    ax = np.asarray(axis, dtype=np.float32); ax = ax / (np.linalg.norm(ax) + 1e-12)
    py = q @ ax
    px = np.linalg.norm(q - np.outer(py, ax), axis=-1)
    return np.hypot(px - R, py) - r

# --- 2. Catmull-Rom Swept Tube / Ribbon SDF ---
def catmull_rom(pts, n_sub=6):
    pts = np.asarray(pts, dtype=np.float32)
    if len(pts) < 2: return pts
    P = np.vstack([2*pts[0]-pts[1], pts, 2*pts[-1]-pts[-2]])
    out = []
    t = np.linspace(0, 1, n_sub, endpoint=False, dtype=np.float32)[:, None]
    for i in range(len(pts) - 1):
        p0, p1, p2, p3 = P[i], P[i+1], P[i+2], P[i+3]
        c = 0.5 * ((2*p1) + (-p0+p2)*t + (2*p0-5*p1+4*p2-p3)*(t**2) + (-p0+3*p1-3*p2+p3)*(t**3))
        out.append(c)
    out.append(pts[-1:])
    return np.vstack(out)

def sd_swept_ribbon(p, ctrl_pts, radii, flatten=1.0, flat_normal=None, n_sub=5, k=0.004):
    cr = np.column_stack([ np.asarray(ctrl_pts, dtype=np.float32), np.asarray(radii, dtype=np.float32) ])
    sampled = catmull_rom(cr, n_sub=n_sub)
    pts, rads = sampled[:, :3], np.maximum(sampled[:, 3], 0.0008)
    d = np.full(len(p), 1e6, dtype=np.float32)
    fn = None if flat_normal is None else np.asarray(flat_normal, dtype=np.float32)
    if fn is not None: fn = fn / (np.linalg.norm(fn) + 1e-12)
    for i in range(len(pts) - 1):
        a, b, r1, r2 = pts[i], pts[i+1], rads[i], rads[i+1]
        if flatten != 1.0 and fn is not None:
            mid = 0.5 * (a + b)
            q = p - mid
            q_f = q + np.outer(q @ fn, fn) * (1.0 / flatten - 1.0)
            seg_d = sd_round_cone(q_f + mid, a, b, r1, r2) * min(1.0, flatten)
        else:
            seg_d = sd_round_cone(p, a, b, r1, r2)
        d = seg_d if i == 0 else smin(d, seg_d, k)
    return d

# --- 3. Vectorised Marching Tetrahedra Mesher ---
_TETS = np.array([[0,5,1,6],[0,1,2,6],[0,2,3,6],[0,3,7,6],[0,7,4,6],[0,4,5,6]], dtype=np.int32)
_TET_EDGES = np.array([[0,1],[0,2],[0,3],[1,2],[1,3],[2,3]], dtype=np.int32)
_CORNERS = np.array([[0,0,0],[1,0,0],[1,1,0],[0,1,0],[0,0,1],[1,0,1],[1,1,1],[0,1,1]], dtype=np.int32)
_TET_TRIS = [
    [], [[0,2,1]], [[0,3,4]], [[1,4,2],[1,3,4]], [[1,5,3]], [[0,2,5],[0,5,3]], [[0,5,4],[0,1,5]], [[2,5,4]],
    [[2,4,5]], [[0,5,1],[0,4,5]], [[0,3,5],[0,5,2]], [[1,3,5]], [[1,4,3],[1,2,4]], [[0,4,3]], [[0,1,2]], []
]

def mesh_sdf(sdf_func, bmin, bmax, cell=0.004, smooth_iters=1):
    bmin = np.asarray(bmin, dtype=np.float32) - cell * 2
    bmax = np.asarray(bmax, dtype=np.float32) + cell * 2
    dims = np.maximum(np.ceil((bmax - bmin) / cell).astype(int) + 1, 3)
    xs = bmin[0] + np.arange(dims[0], dtype=np.float32) * cell
    ys = bmin[1] + np.arange(dims[1], dtype=np.float32) * cell
    zs = bmin[2] + np.arange(dims[2], dtype=np.float32) * cell
    grid_pts = np.stack(np.meshgrid(xs, ys, zs, indexing='ij'), axis=-1).reshape(-1, 3)
    vals = np.empty(len(grid_pts), dtype=np.float32)
    for s in range(0, len(grid_pts), 150000):
        vals[s:s+150000] = sdf_func(grid_pts[s:s+150000])
    V = vals.reshape(dims)
    c_vals = [V[c[0]:dims[0]-1+c[0], c[1]:dims[1]-1+c[1], c[2]:dims[2]-1+c[2]] for c in _CORNERS]
    c_min = np.minimum.reduce(c_vals); c_max = np.maximum.reduce(c_vals)
    active = np.argwhere((c_min <= 0.0) & (c_max > 0.0))
    if len(active) == 0: return np.zeros((0,3), dtype=np.float32), np.zeros((0,3), dtype=np.int32)
    strides = np.array([dims[1]*dims[2], dims[2], 1], dtype=np.int64)
    base_idx = active @ strides
    corner_offsets = _CORNERS @ strides
    cube_v_idx = base_idx[:, None] + corner_offsets[None, :]
    cube_v_val = vals[cube_v_idx]
    all_e1, all_e2 = [], []
    for t in range(6):
        tv_idx = cube_v_idx[:, _TETS[t]]
        tv_val = cube_v_val[:, _TETS[t]]
        mask = (tv_val < 0.0).astype(np.int32)
        code = mask[:,0] | (mask[:,1]<<1) | (mask[:,2]<<2) | (mask[:,3]<<3)
        for c_code in range(1, 15):
            sel = np.nonzero(code == c_code)[0]
            if len(sel) == 0: continue
            for tri in _TET_TRIS[c_code]:
                for e_local in tri:
                    vA, vB = _TET_EDGES[e_local]
                    all_e1.append(tv_idx[sel, vA]); all_e2.append(tv_idx[sel, vB])
    if not all_e1: return np.zeros((0,3), dtype=np.float32), np.zeros((0,3), dtype=np.int32)
    e1 = np.concatenate(all_e1); e2 = np.concatenate(all_e2)
    emin, emax = np.minimum(e1, e2), np.maximum(e1, e2)
    keys = emin * np.int64(len(vals)) + emax
    u_keys, inv = np.unique(keys, return_inverse=True)
    u1 = u_keys // np.int64(len(vals)); u2 = u_keys % np.int64(len(vals))
    v1, v2 = vals[u1], vals[u2]
    t_interp = np.clip(-v1 / np.where(np.abs(v2 - v1) < 1e-12, 1e-12, v2 - v1), 0.0, 1.0)[:, None]
    verts = grid_pts[u1] + t_interp * (grid_pts[u2] - grid_pts[u1])
    tris = inv.reshape(-1, 3)
    valid = (tris[:,0] != tris[:,1]) & (tris[:,1] != tris[:,2]) & (tris[:,2] != tris[:,0])
    tris = tris[valid]
    for _ in range(smooth_iters):
        if len(verts) == 0 or len(tris) == 0: break
        acc = np.zeros_like(verts); cnt = np.zeros(len(verts), dtype=np.float32)
        for i, j in ((0,1),(1,2),(2,0)):
            np.add.at(acc, tris[:,i], verts[tris[:,j]]); np.add.at(cnt, tris[:,i], 1.0)
            np.add.at(acc, tris[:,j], verts[tris[:,i]]); np.add.at(cnt, tris[:,j], 1.0)
        verts = verts + 0.35 * (acc / np.maximum(cnt[:, None], 1.0) - verts)
    return verts, tris

# --- 4. Material Palette, Part Registry & Exporter ---
PALETTE = {
    'skin': '#FCD6B4', 'hair_shadow': '#6E3C3A', 'hair': '#A85A3A', 'hair_hi': '#D08658',
    'teal_dark': '#1C4C54', 'teal': '#2A8C8E', 'teal_light': '#6ACBB6', 'coat': '#F2E6CE',
    'coat_shadow': '#D2BFA4', 'rust': '#A85A3A', 'belt': '#6E3C3A', 'gold': '#E2A434',
    'tights': '#45435E', 'boots': '#6E3C3A', 'fur': '#F2E6CE', 'iris': '#2C9696',
    'lash': '#20223E', 'eye_white': '#FFFFFF', 'mouth': '#8E2C4A'
}
PARTS = {}

def add_part(material, sdf_func, bbox_min, bbox_max, cell=0.004, smooth_iters=1):
    v, t = mesh_sdf(sdf_func, bbox_min, bbox_max, cell=cell, smooth_iters=smooth_iters)
    if len(t) > 0: PARTS.setdefault(material, []).append((v, t))

def write_obj_mtl(outdir):
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, 'model.mtl'), 'w') as mf:
        for mat, hx in PALETTE.items():
            r, g, b = [int(hx[i:i+2], 16)/255.0 for i in (1, 3, 5)]
            mf.write(f"newmtl {mat}\nKd {r:.4f} {g:.4f} {b:.4f}\nKa 0.15 0.15 0.15\nKs 0.08 0.08 0.08\nNs 20\n\n")
    with open(os.path.join(outdir, 'model.obj'), 'w') as of:
        of.write("mtllib model.mtl\n")
        v_off = 1
        for mat, mesh_list in PARTS.items():
            of.write(f"o {mat}\ng {mat}\nusemtl {mat}\n")
            for v, t in mesh_list:
                for p in v: of.write(f"v {p[0]:.5f} {p[1]:.5f} {p[2]:.5f}\n")
                for f in (t + v_off): of.write(f"f {f[0]} {f[1]} {f[2]}\n")
                v_off += len(v)

# --- 5. Proportional Landmarks (5.0 heads tall, total height ~1.0m, feet at y=0, +Z forward, +X = HER left) ---
LM = {
    'crown': (0.0, 0.96, 0.0), 'head_center': (0.0, 0.865, 0.005), 'eye_y': 0.842, 'chin': (0.0, 0.772, 0.068),
    'neck_top': (0.0, 0.785, -0.005), 'neck_base': (0.0, 0.735, -0.005),
    'shoulder_L': (0.092, 0.715, -0.005), 'shoulder_R': (-0.092, 0.715, -0.005),
    'elbow_L': (0.145, 0.595, -0.010), 'elbow_R': (-0.145, 0.595, -0.010),
    'wrist_L': (0.195, 0.485, 0.012), 'wrist_R': (-0.195, 0.485, 0.012),
    'chest': (0.0, 0.655, 0.015), 'waist': (0.0, 0.560, 0.0), 'hip': (0.0, 0.470, -0.005),
    'thigh_L': (0.052, 0.455, 0.0), 'thigh_R': (-0.052, 0.455, 0.0),
    'knee_L': (0.054, 0.265, 0.005), 'knee_R': (-0.054, 0.265, 0.005),
    'ankle_L': (0.055, 0.065, -0.005), 'ankle_R': (-0.055, 0.065, -0.005),
    'toe_L': (0.058, 0.018, 0.065), 'toe_R': (-0.058, 0.018, 0.065),
}

def main(outdir):
    for fn in ('build_head', 'build_hair', 'build_bow', 'build_body', 'build_limbs'):
        if fn in globals(): globals()[fn]()
    write_obj_mtl(outdir)

~~~
===== CHARACTER DESCRIPTION AND CONTRACT =====
## Character description

**Who she is.** The heroine of a cosy mobile isometric game set in snowy mountains. She is a cheerful, plucky young woman
of about 19-20 with a little clumsiness. She is cute and feminine, with soft gentle curves, and she should read as
"adorable anime heroine" in a single glance.

**Style.** Japanese anime, semi-chibi. Think a modern cute JRPG field model (Atelier, Ni no Kuni, Pokémon
Legends-era humans, Genshin-style chibi figurines): clean stylised forms with smooth surfaces, no realism, no
muscles. Every shape should be appealing and designed, with no lumpy blobs.

**Proportions.** About 5.0 heads tall (head about 20% of the height): a slim young woman in anime proportions, with slim limbs, a small defined waist and long tapered legs.
- Neck: short and slender.
- Shoulders: narrow and sloped, about 1.1 head-widths across.
- Torso: small, with a gently defined waist that is the narrowest point, and a modest bust and soft hips. The hips flare
  slightly wider than the waist and carry the coat's A-line.
- Legs: slim, straight and tapered, about 2.3 heads long (hip to sole). The thighs are slightly full, the knees small and the calves slender,
  with small feet in chunky boots.
- Arms: slim, and the hands are small (mittens).
- Overall silhouette: head and hair on top, a small waist, the coat flaring into an A-line skirt over slim legs.

**Head and face (most important).**
- **Head shape:** NOT a sphere. Use anime head construction:
  - a rounded cranium;
  - cheeks that narrow below the eye line;
  - a soft but clearly POINTED, small chin (a V-taper);
  - a jaw line that curves from below the ear to the chin, visible in 3/4 and profile.

  The face is slim and heart-shaped. The profile shows a slight forward cheek curve, a tiny nose bump and a small chin.
- **Eyes:** large anime eyes, modelled as shallow almond-shaped recesses or inset discs so that their perspective
  reads in 3/4 view.
  - Shape: slightly tare-me (gently drooping outer corners) with a rounded top lid.
  - Placement: set on the lower half of the head, with about one eye-width between them.
  - Colours: iris teal, lash line dark.
- **Rest of the face:** a tiny nose (a small ridge), a small mouth and slight cheek fullness. Ears are mostly hidden by
  the hair.

**Hair (signature).** Warm chestnut brown, built as designed, layered clumps, never a smooth helmet.
- **Bangs:**
  - Full hime-style bangs that are voluminous and LIFT OFF the forehead.
  - Layered: a back layer and a front layer of pointed clumps with staggered lengths. The tips curve and flick slightly,
    and a few cross over others.
  - The centre bangs reach just above the brows. The side bangs slope gently longer toward the temples and blend into
    the side locks, so no bare forehead shows at the sides.
  - There are small gaps between clumps.
- **Side locks:** one flat, slightly curved lock per side framing the cheeks, down to the collarbone, cut in a soft
  point.
- **Back hair:** long, falling down the back to about mid-back, as 4-6 broad tapering clumps with soft pointed tips, and
  slight volume at the crown.
- **Half-up ponytail:** the upper hair is gathered at the back of the crown into ONE ponytail that tapers to a single
  point at about the shoulder blades, with a gentle S-curve.

**Bow (signature).** A BIG teal satin ribbon bow tied at the back of the head where the ponytail is gathered.
- **Loops:** two puffy, voluminous teardrop loops, about 1.5x the head width tip to tip, drooping slightly at the
  outer ends.
- **Knot and tails:** a pinched centre knot, and two tails hanging down to the shoulders with V-cut ends.
- **Seen from the front:** only the loop tips peek out behind the head on each side, and they must not read as cat ears.

**Outfit (cosy winter).**
- **Scarf:** a chunky teal knit scarf (cable ribs), one thick roll around the neck. One tail hangs down the front on
  HER LEFT side, to the waist, with a fringe.
- **Coat:** a cream/oatmeal winter coat.
  - Cut: fitted bodice, a small rounded (Peter Pan) collar under the scarf, and a gently defined waist with a thin
    brown belt and a small gold buckle.
  - Front: 6 small gold buttons, 3 above the belt and 3 below.
  - Skirt: below the waist it flares into an A-line skirt with soft folds, ending at mid-thigh in a curved hem with a
    rust-red trim band.
  - Sleeves: long, slightly puffy, with rust-red cuffs.
- **Mittens:** teal, with a visible thumb.
- **Legs and boots:** dark plum-charcoal tights on slim legs, and brown winter boots to mid-calf with a cream fur
  cuff, a rounded toe and a small heel.

**Colours (palette roles).**

| Part | Colours |
|---|---|
| hair | #6E3C3A shadow, #A85A3A base, #D08658 highlight |
| skin | #FCD6B4 light, #EBA586 mid, #D07C74 shadow |
| teal (bow/scarf/mittens) | #1C4C54, #2A8C8E, #6ACBB6 |
| coat | #F2E6CE, #D2BFA4 |
| rust trim | #A85A3A |
| tights | #45435E |
| boots | #6E3C3A |
| fur cuff | #F2E6CE |
| iris | #2C9696 |
| lash | #20223E |

**Pose for the model.** A relaxed A-pose standing rest, arms slightly away from the body (about 20-25°) so the arms and
waist read separately. The feet are slightly apart and the toes point forward.

## Technical contract (Gemini output)

- **Script:** one standalone Python 3 script, numpy only. No network access, and no file access outside the output dir.
  Run as `python gen.py <outdir>`.
- **Output files:** `model.obj` plus `model.mtl`. Use one material (`usemtl`) per part, named
  `skin`, `hair_shadow`, `hair`, `hair_hi`, `teal_dark`, `teal`, `teal_light`, `coat`, `coat_shadow`, `rust`, `belt`, `gold`, `tights`,
  `boots`, `fur`, `iris`, `lash`, `eye_white`, `mouth`.
- **Mesh:** triangulated, consistent outward winding, and watertight per part where possible. Aim for 40k-150k triangles:
  smooth but detailed.
- **Axes:** +Y is up, the character faces +Z, units are metres, the height is about 1.0 and the feet are at y=0.
- **Construction:** any technique Gemini wants, such as an SDF plus its own marching cubes, lofted or swept
  cross-sections, subdivided primitives, or deformed spheres and capsules. Hair clumps work well as swept tapered
  ribbons or tubes along curves.
- **Pose:** the rest pose above. No rig is needed.


## Reference images (attached)
- ref2, ref3 (stylised 3D women, A-pose): take the FACE from these: a slim oval-to-heart face with high soft cheekbones; a narrow jaw tapering to a small, defined chin, and a slim neck; large almond eyes with a winged upper lash; a small nose ridge and small full lips; soft wispy bangs that part slightly and lift off the forehead. Also take the body: slim limbs, a defined waist and long tapered legs.
- ref4, ref5 (anime cel-shaded toon model, side and front): take the overall MODEL LANGUAGE from these: clean anime toon forms; long straight hair as a few large smooth layered sheets with blunt-cut bangs and side locks; big anime eyes; a simple flat-shaded outfit with crisp folds; slim straight legs and small feet. This is the target look, with less detail allowed.
- Outfit, bow, ponytail and colours are as described above, NOT as in the references (the refs are only for face, body shape and modelling language).
- ref6 (profile) and ref7 (3/4 look-back), a hand-painted stylised anime 3D character: take the HAIR: big glossy sheets, blunt hime bangs, long hair falling as broad tapering sheets with a few loose thin strands, and a voluminous layered high ponytail with a scrunchie (use this as the model for her ponytail's volume, tied with her teal bow instead of a scrunchie). Take the FACE: small pointed chin, small nose, large eyes with a thick winged upper lash, slim neck. Take the BODY: petite, narrow shoulders. Do NOT take the goth styling or colours.
- ref8 (painted semi-realistic anime portrait) and ref9 (stylised 3D bust sculpt): use them ONLY for face construction and sculpt quality - general style, never anyone's likeness (our heroine is her own cute anime design): cheek planes that turn crisply into a narrow jaw, a small defined chin, a slender neck and soft collarbones; clean shaped brows and an eyelid crease; large eyes with a thick winged lash; a small nose with a defined tip and small full lips; hair as smooth sculpted sheets with a few loose strands.



## Response

```python
# --- SECTION 1: HEAD, FACE AND NECK ---
def _head_sym_x(p):
    q = p.copy()
    q[:, 0] = np.abs(q[:, 0])
    return q

def _head_skin_sdf(p):
    q = _head_sym_x(p)
    # 1. Cranium: rounded anime skull
    d_cran = sd_ellipsoid(p, (0.0, 0.875, -0.005), (0.073, 0.082, 0.078))
    
    # 2. Face & Jaw: heart-shaped frontal mask tapering to a small V-chin
    d_face_upper = sd_ellipsoid(p, (0.0, 0.848, 0.022), (0.064, 0.056, 0.058))
    d_jaw_core = sd_round_cone(p, (0.0, 0.838, 0.026), (0.0, 0.775, 0.062), 0.054, 0.011)
    d_jawline = sd_round_cone(q, (0.050, 0.822, 0.015), (0.0, 0.774, 0.064), 0.024, 0.010)
    d_chin = sd_ellipsoid(p, (0.0, 0.774, 0.064), (0.013, 0.010, 0.013))
    
    # 3. Cheek fullness (soft anime 3/4 profile curve)
    d_cheek = sd_ellipsoid(q, (0.036, 0.820, 0.048), (0.029, 0.024, 0.025))
    
    d_head = smin(d_cran, d_face_upper, 0.018)
    d_head = smin(d_head, d_jaw_core, 0.018)
    d_head = smin(d_head, d_jawline, 0.014)
    d_head = smin(d_head, d_chin, 0.010)
    d_head = smin(d_head, d_cheek, 0.018)
    
    # Flatten lateral temple/jaw planes slightly for crisp anime cheek-to-jaw turn
    d_side_clip = q[:, 0] - (0.073 - 0.18 * np.clip(0.845 - q[:, 1], 0.0, 0.08))
    d_head = smax(d_head, d_side_clip, 0.012)
    
    # 4. Carve shallow almond eye sockets so eyes sit recessed in 3/4 view
    q_eye = rotate_axis(q - np.array([0.031, 0.838, 0.062], dtype=np.float32), (0, 0, 1), -0.07)
    d_socket = sd_ellipsoid(q_eye, (0.0, 0.0, 0.0), (0.022, 0.014, 0.014))
    d_head = ssub(d_head, d_socket, 0.006)
    
    # 5. Small cute nose with defined tip and bridge
    d_nose_bridge = sd_round_cone(p, (0.0, 0.840, 0.067), (0.0, 0.817, 0.080), 0.004, 0.0055)
    d_nose_tip = sd_ellipsoid(p, (0.0, 0.816, 0.081), (0.0065, 0.0055, 0.0065))
    d_nose = smin(d_nose_bridge, d_nose_tip, 0.004)
    d_head = smin(d_head, d_nose, 0.005)
    
    # Subtle lip philtrum/muzzle volume under nose
    d_muzzle = sd_ellipsoid(p, (0.0, 0.799, 0.068), (0.016, 0.010, 0.010))
    d_head = smin(d_head, d_muzzle, 0.008)
    
    # 6. Small ears tucked at sides
    q_ear = rotate_axis(q - np.array([0.067, 0.832, -0.002], dtype=np.float32), (0, 1, 0), -0.35)
    d_ear = sd_ellipsoid(q_ear, (0.0, 0.0, 0.0), (0.007, 0.017, 0.011))
    d_head = smin(d_head, d_ear, 0.005)
    
    # 7. Slender neck, traps and collarbones
    d_neck = sd_round_cone(p, (0.0, 0.805, 0.002), (0.0, 0.725, -0.005), 0.025, 0.029)
    d_Shoulders = sd_round_cone(q, (0.0, 0.722, -0.005), (0.075, 0.712, -0.005), 0.032, 0.022)
    d_clav = sd_capsule(q, (0.008, 0.722, 0.018), (0.065, 0.718, 0.006), 0.0055)
    d_neck_all = smin(smin(d_neck, d_Shoulders, 0.015), d_clav, 0.008)
    
    # Clean under-chin transition
    return smin(d_head, d_neck_all, 0.010)

def _head_eye_white_sdf(p):
    q = _head_sym_x(p)
    # Tare-me (slightly drooping outer corner) almond scleras
    q_loc = rotate_axis(q - np.array([0.031, 0.837, 0.057], dtype=np.float32), (0, 1, 0), -0.22)
    q_loc = rotate_axis(q_loc, (0, 0, 1), -0.06)
    return sd_ellipsoid(q_loc, (0.0, 0.0, 0.0), (0.0195, 0.0125, 0.009))

def _head_iris_sdf(p):
    q = _head_sym_x(p)
    q_loc = rotate_axis(q - np.array([0.030, 0.837, 0.0635], dtype=np.float32), (0, 1, 0), -0.20)
    d_disc = sd_ellipsoid(q_loc, (0.0, 0.0, 0.0), (0.0115, 0.0120, 0.0035))
    # Carve central recess so the dark pupil ('lash') shows through cleanly
    d_pupil_cut = sd_ellipsoid(q_loc, (0.0, 0.0, 0.002), (0.0050, 0.0055, 0.0035))
    return ssub(d_disc, d_pupil_cut, 0.001)

def _head_lash_sdf(p):
    q = _head_sym_x(p)
    # 1. Dark pupil core + upper iris shadow/limbal ring
    q_loc = rotate_axis(q - np.array([0.030, 0.837, 0.0642], dtype=np.float32), (0, 1, 0), -0.20)
    d_pupil = sd_ellipsoid(q_loc, (0.0, 0.0, 0.0), (0.0052, 0.0058, 0.0030))
    
    # 2. Thick winged upper lash (arched top lid, tare-me outer drop with winged flick)
    u_pts = [
        (0.014, 0.835, 0.063),
        (0.022, 0.845, 0.066),
        (0.032, 0.846, 0.065),
        (0.043, 0.840, 0.060),
        (0.050, 0.836, 0.055),
        (0.054, 0.839, 0.051),
    ]
    u_rads = [0.0016, 0.0028, 0.0034, 0.0032, 0.0022, 0.0010]
    d_upper = sd_swept_ribbon(q, u_pts, u_rads, flatten=0.55, flat_normal=(0, 0.3, 1), n_sub=5, k=0.002)
    
    # Delicate eyelid crease line just above upper lash
    c_pts = [
        (0.017, 0.844, 0.065),
        (0.030, 0.851, 0.065),
        (0.045, 0.845, 0.059),
    ]
    c_rads = [0.0008, 0.0010, 0.0008]
    d_crease = sd_swept_ribbon(q, c_pts, c_rads, n_sub=4, k=0.0015)
    
    # 3. Thin lower lash line
    l_pts = [
        (0.018, 0.830, 0.063),
        (0.031, 0.826, 0.064),
        (0.046, 0.831, 0.057),
    ]
    l_rads = [0.0009, 0.0013, 0.0011]
    d_lower = sd_swept_ribbon(q, l_pts, l_rads, n_sub=4, k=0.0015)
    
    return np.minimum(np.minimum(d_pupil, d_upper), np.minimum(d_crease, d_lower))

def _head_brow_sdf(p):
    q = _head_sym_x(p)
    # Clean shaped feminine brows arched above eyes
    b_pts = [
        (0.013, 0.858, 0.066),
        (0.026, 0.863, 0.066),
        (0.040, 0.861, 0.061),
        (0.050, 0.855, 0.053),
    ]
    b_rads = [0.0020, 0.0024, 0.0019, 0.0010]
    return sd_swept_ribbon(q, b_pts, b_rads, flatten=0.5, flat_normal=(0, 0, 1), n_sub=5, k=0.002)

def _head_mouth_sdf(p):
    q = _head_sym_x(p)
    # Small full anime lips (cupid's bow upper lip + plush lower lip)
    u_pts = [(0.0, 0.7985, 0.0745), (0.0045, 0.7995, 0.0740), (0.0105, 0.7975, 0.0710)]
    u_rads = [0.0022, 0.0024, 0.0012]
    d_up = sd_swept_ribbon(q, u_pts, u_rads, flatten=0.65, flat_normal=(0, 0, 1), n_sub=4, k=0.002)
    d_low = sd_ellipsoid(p, (0.0, 0.7950, 0.0735), (0.0085, 0.0028, 0.0038))
    return smin(d_up, d_low, 0.002)

def build_head():
    # Head, face & neck skin
    add_part('skin', _head_skin_sdf, (-0.085, 0.700, -0.090), (0.085, 0.965, 0.095), cell=0.0025, smooth_iters=2)
    # Eye whites (almond sclera discs)
    add_part('eye_white', _head_eye_white_sdf, (-0.056, 0.820, 0.044), (0.056, 0.855, 0.072), cell=0.0016, smooth_iters=1)
    # Teal irises
    add_part('iris', _head_iris_sdf, (-0.048, 0.821, 0.056), (0.048, 0.853, 0.072), cell=0.0015, smooth_iters=1)
    # Dark lashes, pupils & lid crease
    add_part('lash', _head_lash_sdf, (-0.060, 0.822, 0.046), (0.060, 0.856, 0.072), cell=0.0015, smooth_iters=1)
    # Shaped eyebrows
    add_part('hair_shadow', _head_brow_sdf, (-0.056, 0.850, 0.048), (0.056, 0.869, 0.072), cell=0.0016, smooth_iters=1)
    # Small full lips
    add_part('mouth', _head_mouth_sdf, (-0.015, 0.790, 0.066), (0.015, 0.804, 0.080), cell=0.0015, smooth_iters=1)
```

### Notes
- **Anime Head & Jaw Construction:** Built from a rounded cranium blended into an upper face mask, cheek planes, and a swept jawline tapering to a small V-pointed chin (`y=0.774, z=0.064`), with lateral plane clipping for a clean cheek-to-jaw turn and recessed eye sockets for 3/4 view depth.
- **Facial Features & Resolution:** Separate high-res (`0.0015–0.0016` cell) parts for the tare-me almond `eye_white` insets, `iris` discs with carved pupil openings, `lash` (dark pupil core, winged upper lash, lid crease, and lower lash), arched `hair_shadow` brows, and small full `mouth` lips.
