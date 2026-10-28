# Gemini 4 Argon: r17_s4_body

_Images sent:_ refs ref2 ref5

## Prompt

You are an expert technical artist writing a procedural numpy-only generator for a stylised anime 3D character, in SECTIONS. SECTION 0 (core helpers, mesher, LM landmarks, main) is already written and is given below. Now write ONLY the section defining `build_body()` - TORSO, COAT AND SCARF: slim petite torso with a modest bust, small defined waist, soft hips; the cream coat ('coat') as a fitted bodice with a small rounded Peter Pan collar, a thin brown belt ('belt') with a small gold buckle ('gold'), 6 small gold buttons (3 above, 3 below the belt), an A-line skirt with soft folds/pleats flaring to mid-thigh with a curved hem and a rust trim band ('rust'); 'coat_shadow' for the inner skirt / fold recesses; chunky teal knit scarf ('teal', ribs in 'teal_dark') as one thick roll around the neck with ONE tail down the front on HER LEFT (+X) to the waist with a fringe ('teal_light').

Rules: one ~~~python block, at most ~170 lines; use only numpy/math and the SECTION 0 helpers (add_part, sd_*, smin/smax/ssub, rotate_axis, sd_swept_ribbon, catmull_rom, LM); do not redefine SECTION 0 names (prefix your own helpers with _body_); no file or network access. Give every add_part a tight bbox and a sensible cell size (0.002-0.004) so the whole section meshes in under ~60 s and yields roughly 10k-40k triangles. Respect the axes: +Y up, she faces +Z, +X is HER LEFT, feet at y=0, height ~1.0. Make every shape designed and appealing (anime toon, smooth, no lumps). The attached images are style references (see the description). After the code block, give at most 5 lines of notes.

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
def _body_skirt_env(p, dr=0.0):
    x, y, z = p[:, 0], p[:, 1], p[:, 2]
    t = np.clip((0.562 - y) / 0.197, 0.0, 1.0)
    rx = 0.068 + 0.074 * (t ** 0.88) + dr
    rz = 0.052 + 0.056 * (t ** 0.88) + dr
    zc = -0.003 - 0.004 * t
    return (np.hypot(x / rx, (z - zc) / rz) - 1.0) * 0.06

def _body_coat_sdf(p):
    x, y, z = p[:, 0], p[:, 1], p[:, 2]
    # Fitted upper bodice
    d_up = sd_round_cone(p, (0.0, 0.720, -0.005), (0.0, 0.560, 0.0), 0.072, 0.058)
    d_up = smin(d_up, sd_capsule(p, (-0.068, 0.710, -0.005), (0.068, 0.710, -0.005), 0.032), 0.018)
    # Modest anime bust
    d_bust = smin(sd_ellipsoid(p, (-0.033, 0.652, 0.032), (0.037, 0.040, 0.038)),
                  sd_ellipsoid(p, ( 0.033, 0.652, 0.032), (0.037, 0.040, 0.038)), 0.022)
    d_up = smin(d_up, d_bust, 0.020)
    # Tapered waist
    d_waist = sd_ellipsoid(p, (0.0, 0.562, -0.001), (0.066, 0.042, 0.051))
    d_bodice = smax(smin(d_up, d_waist, 0.020), np.maximum(0.545 - y, y - 0.735), 0.008)
    # Rounded Peter Pan collar
    d_col = sd_torus(p, (0.0, 0.724, 0.002), 0.055, 0.013, axis=(0.0, 1.0, 0.16))
    d_col = ssub(d_col, sd_round_box(p, (0.0, 0.720, 0.058), (0.010, 0.030, 0.030), 0.004), 0.004)
    d_bodice = smin(d_bodice, d_col, 0.006)
    # A-line skirt with 10 soft pleats and curved hem
    t = np.clip((0.562 - y) / 0.197, 0.0, 1.0)
    ang = np.arctan2(x, z + 0.004)
    pleat = (0.001 + 0.0065 * (t ** 1.15)) * np.cos(10.0 * ang) + 0.0025 * t * np.cos(6.0 * ang)
    r_o = _body_skirt_env(p, pleat)
    r_i = _body_skirt_env(p, pleat * 0.4 - 0.013)
    d_sk_wall = smax(r_o, -r_i, 0.003)
    hem_y = 0.365 - 0.007 * np.cos(2.0 * ang) + 0.002 * np.cos(10.0 * ang)
    d_skirt = smax(d_sk_wall, np.maximum(hem_y - y, y - 0.570), 0.005)
    # Center front lapel seam
    d_seam = sd_capsule(p, (0.0, 0.372, 0.062), (0.0, 0.712, 0.052), 0.003)
    return smin(smin(d_bodice, d_skirt, 0.012), d_seam, 0.004)

def _body_coat_shadow_sdf(p):
    x, y, z = p[:, 0], p[:, 1], p[:, 2]
    ang = np.arctan2(x, z + 0.004)
    t = np.clip((0.562 - y) / 0.197, 0.0, 1.0)
    # Inner dark dome & deep pleat recesses
    r_o = _body_skirt_env(p, -0.011)
    r_i = _body_skirt_env(p, -0.028)
    hem_y = 0.372 - 0.007 * np.cos(2.0 * ang)
    d_liner = smax(smax(r_o, -r_i, 0.003), np.maximum(hem_y - y, y - 0.490), 0.004)
    # Outer fold groove shadows
    pleat_in = -0.0045 * (t ** 1.1) * np.maximum(0.0, -np.cos(10.0 * ang))
    r_fold = np.abs(_body_skirt_env(p, pleat_in - 0.002)) - 0.0025
    d_folds = smax(r_fold, np.maximum(hem_y + 0.008 - y, y - 0.545), 0.003)
    return smin(d_liner, d_folds, 0.005)

def _body_rust_trim_sdf(p):
    x, y, z = p[:, 0], p[:, 1], p[:, 2]
    t = np.clip((0.562 - y) / 0.197, 0.0, 1.0)
    ang = np.arctan2(x, z + 0.004)
    pleat = (0.001 + 0.0065 * (t ** 1.15)) * np.cos(10.0 * ang) + 0.0025 * t * np.cos(6.0 * ang)
    r_o = _body_skirt_env(p, pleat + 0.0018)
    r_i = _body_skirt_env(p, pleat - 0.011)
    hem_y = 0.365 - 0.007 * np.cos(2.0 * ang) + 0.002 * np.cos(10.0 * ang)
    return smax(smax(r_o, -r_i, 0.002), np.maximum((hem_y - 0.003) - y, y - (hem_y + 0.017)), 0.003)

def _body_belt_sdf(p):
    x, y, z = p[:, 0], p[:, 1], p[:, 2]
    r_ell = (np.hypot(x / 0.0685, (z + 0.001) / 0.0535) - 1.0) * 0.055
    return smax(np.abs(r_ell) - 0.0045, np.abs(y - 0.560) - 0.0105, 0.002)

def _body_gold_sdf(p):
    # Belt buckle + prong
    d_b = ssub(sd_round_box(p, (0.0, 0.560, 0.054), (0.014, 0.013, 0.004), 0.002),
               sd_round_box(p, (0.0, 0.560, 0.054), (0.008, 0.007, 0.008), 0.001), 0.001)
    d_b = smin(d_b, sd_capsule(p, (0.0, 0.560, 0.052), (0.006, 0.560, 0.058), 0.0018), 0.001)
    # 6 small gold buttons: 3 above belt, 3 below belt
    btns = [(0.0, 0.682, 0.053), (0.0, 0.642, 0.064), (0.0, 0.600, 0.057),
            (0.0, 0.520, 0.056), (0.0, 0.475, 0.066), (0.0, 0.430, 0.075)]
    for bx, by, bz in btns:
        d_b = np.minimum(d_b, sd_ellipsoid(p, (bx, by, bz), (0.0065, 0.0065, 0.004)))
    return d_b

def _body_scarf_sdf(p):
    # Thick cozy neck roll
    d_roll = smin(sd_torus(p, (0.0, 0.742, 0.002), 0.056, 0.027, axis=(0.0, 1.0, 0.14)),
                  sd_torus(p, (0.0, 0.724, 0.006), 0.060, 0.023, axis=(0.04, 1.0, 0.10)), 0.012)
    # One tail hanging down front on HER LEFT (+X) to waist
    tail_pts = [(0.028, 0.728, 0.048), (0.044, 0.690, 0.068), (0.050, 0.640, 0.073),
                (0.052, 0.592, 0.068), (0.049, 0.552, 0.066)]
    tail_rads = [0.023, 0.025, 0.026, 0.025, 0.023]
    d_tail = sd_swept_ribbon(p, tail_pts, tail_rads, flatten=0.45, flat_normal=(0.15, 0.0, 1.0), n_sub=6, k=0.008)
    return smin(d_roll, d_tail, 0.012)

def _body_scarf_ribs_sdf(p):
    x, y, z = p[:, 0], p[:, 1], p[:, 2]
    d_base = _body_scarf_sdf(p)
    ang = np.arctan2(x, z - 0.002)
    rib_neck = np.sin(18.0 * ang)
    rib_tail = np.sin((x - 0.050) * 230.0) * np.cos((y - 0.60) * 45.0)
    w = np.clip((0.715 - y) / 0.035, 0.0, 1.0)
    rib = (1.0 - w) * rib_neck + w * rib_tail
    return smax(np.abs(d_base + 0.0005) - 0.0022, 0.35 - rib, 0.0015)

def _body_fringe_sdf(p):
    d = np.full(len(p), 1e6, dtype=np.float32)
    for i, ox in enumerate(np.linspace(-0.020, 0.020, 6)):
        bx = 0.049 + ox
        bz = 0.066 - 0.15 * ox + (0.0015 if i % 2 == 0 else -0.0015)
        d = smin(d, sd_capsule(p, (bx, 0.550, bz), (bx + ox * 0.12, 0.520, bz + 0.003), 0.0036), 0.002)
    return d

def build_body():
    # Neck and upper chest skin + petite hips base
    def skin_sdf(p):
        d_neck = sd_round_cone(p, LM['neck_base'], LM['neck_top'], 0.027, 0.024)
        d_chest = sd_round_cone(p, (0.0, 0.700, -0.005), LM['neck_base'], 0.048, 0.028)
        d_pelvis = sd_ellipsoid(p, LM['hip'], (0.066, 0.045, 0.048))
        return smin(smin(d_neck, d_chest, 0.012), d_pelvis, 0.020)

    add_part('skin', skin_sdf, (-0.08, 0.42, -0.06), (0.08, 0.80, 0.06), cell=0.003, smooth_iters=2)
    add_part('coat', _body_coat_sdf, (-0.16, 0.35, -0.13), (0.16, 0.75, 0.13), cell=0.003, smooth_iters=2)
    add_part('coat_shadow', _body_coat_shadow_sdf, (-0.15, 0.36, -0.12), (0.15, 0.56, 0.12), cell=0.0032, smooth_iters=1)
    add_part('rust', _body_rust_trim_sdf, (-0.16, 0.35, -0.13), (0.16, 0.39, 0.13), cell=0.0025, smooth_iters=1)
    add_part('belt', _body_belt_sdf, (-0.08, 0.54, -0.07), (0.08, 0.58, 0.07), cell=0.0022, smooth_iters=1)
    add_part('gold', _body_gold_sdf, (-0.03, 0.41, 0.04), (0.03, 0.70, 0.09), cell=0.002, smooth_iters=1)
    add_part('teal', _body_scarf_sdf, (-0.10, 0.54, -0.09), (0.11, 0.78, 0.11), cell=0.0026, smooth_iters=2)
    add_part('teal_dark', _body_scarf_ribs_sdf, (-0.10, 0.54, -0.09), (0.11, 0.78, 0.11), cell=0.0025, smooth_iters=1)
    add_part('teal_light', _body_fringe_sdf, (0.01, 0.51, 0.04), (0.09, 0.56, 0.09), cell=0.002, smooth_iters=1)
```

- **Coat & Silhouette:** Built with a slim fitted bodice, modest anime bust, rounded Peter Pan collar, defined waist at `y=0.56`, and a 10-pleat flared A-line skirt ending at mid-thigh (`y~0.365`) with a curved hem and `rust` trim band.
- **Details:** Added `coat_shadow` for the inner skirt dome and pleat recesses, a thin `belt` at the waist, and `gold` buckle + 6 buttons (3 above, 3 below the belt).
- **Scarf:** Thick double-torus knit neck roll (`teal`) with a flattened Catmull-Rom ribbon tail on her left (`+X`) down to the waist, accented with cable ribs (`teal_dark`) and 6 fringe tassels (`teal_light`).
