"""charlab Blender stage: skinned character -> shared procedural walk -> per-frame passes (headless).
  Blender -b -P blender_walk.py -- MODEL.npz OUTDIR [VIEWS=SE,S,E] [FRAMES=8]
Builds the mesh (model.py output), one armature with standard humanoid bone names (+ tail/pack bones), vertex groups from
the automatic weights, an Armature modifier, then poses the shared 8-frame walk analytically (in-place treadmill, planted
feet via 2-bone IK, hip bob/sway/roll/yaw, chest counter-rotation, arm swing with elbow follow-through, level head with
a small nod, spring/lag parts as phase-lagged oscillators: loopable by construction).
Per frame and view it renders two passes at HI x HI (fixed ortho camera, 30 deg elevation, ground pivot at (HI/2, GROUND)):
  id : Workbench flat, AA off -> material index + line group per pixel (exact)
  nd : EEVEE emission EXR     -> camera-space normal x,y and camera depth
and stores them compactly in OUTDIR/<view>_fNN.npz (mat, grp uint8 at HI; nx, ny, dep float16 at HI/4), plus
OUTDIR/frames.json (eye/glint anchors per frame and view: px, depth, facing; camera scale)."""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix, Quaternion

argv = sys.argv[sys.argv.index('--') + 1:]
NPZ, OUT = argv[0], argv[1]
VIEWS = argv[2].split(',') if len(argv) > 2 else ['SE', 'S', 'E']
NF = int(argv[3]) if len(argv) > 3 else 8
HI, FIG, GROUND = 960, 768, 864
os.makedirs(OUT, exist_ok=True)
D = np.load(NPZ); META = json.load(open(os.path.splitext(NPZ)[0] + '.json'))
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

# ---------------------------------------------------------------------------------------------------------- mesh
V, F = D['V'].astype(np.float64), D['F']
me = bpy.data.meshes.new('body')
me.from_pydata(V.tolist(), [], F.tolist())
me.update()
try:
    me.shade_smooth()
except AttributeError:
    me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
if 'N' in D.files:   # toon normals from the blurred SDF (model.py)
    try:
        me.normals_split_custom_set_from_vertices(D['N'].astype(np.float64).tolist())
    except Exception as e:
        print('custom normals failed:', e)
body = bpy.data.objects.new('body', me); sc.collection.objects.link(body)


def srgb2lin(s):
    s = s / 255.0
    return s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4


fmat, fgrp = D['fmat'].astype(int), D['fgrp'].astype(int)
combo = sorted(set(zip(fmat.tolist(), fgrp.tolist())))
cidx = {c: i for i, c in enumerate(combo)}
for (m, g) in combo:
    mt = bpy.data.materials.new(f'id_{m}_{g}')
    mt.diffuse_color = (srgb2lin(20 + 10 * m), srgb2lin(20 + 22 * g), srgb2lin(128), 1.0)
    me.materials.append(mt)
me.polygons.foreach_set('material_index', [cidx[(m, g)] for m, g in zip(fmat.tolist(), fgrp.tolist())])

# ---------------------------------------------------------------------------------------------------------- armature
arm = bpy.data.armatures.new('rig'); rig = bpy.data.objects.new('rig', arm); sc.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
for b in META['bones']:
    eb = arm.edit_bones.new(b['name']); eb.head = b['head']; eb.tail = b['tail']; eb.roll = 0
for b in META['bones']:
    if b['parent']: arm.edit_bones[b['name']].parent = arm.edit_bones[b['parent']]
bpy.ops.object.mode_set(mode='OBJECT')
BN = [b['name'] for b in META['bones']]
widx, wval = D['widx'], D['wval']
groups = {n: body.vertex_groups.new(name=n) for n in BN}
# one add() call per (bone, quantised weight)
for k in range(widx.shape[1]):
    wq = np.round(wval[:, k] * 64).astype(int)
    for bi in np.unique(widx[:, k]):
        sel = widx[:, k] == bi
        for q in np.unique(wq[sel]):
            if q <= 0: continue
            vs = np.nonzero(sel & (wq == q))[0].tolist()
            groups[BN[bi]].add(vs, q / 64.0, 'ADD')
mod = body.modifiers.new('arm', 'ARMATURE'); mod.object = rig
REST = {b.name: b.matrix_local.copy() for b in arm.bones}
PARENT = {b['name']: b['parent'] for b in META['bones']}
for pb in rig.pose.bones: pb.rotation_mode = 'QUATERNION'


# ---------------------------------------------------------------------------------------------------------- walk
def Rx(d): return Quaternion((1, 0, 0), math.radians(d))
def Ry(d): return Quaternion((0, 1, 0), math.radians(d))
def Rz(d): return Quaternion((0, 0, 1), math.radians(d))
def ss(u): u = min(max(u, 0.0), 1.0); return u * u * (3 - 2 * u)


W = META['walk']; PRE = META['preset']
LEG = W['thigh'] + W['shin']
STEP = {'chibi': 0.50, 'compact': 0.44, 'slim': 0.42}[PRE] * LEG
LIFT = {'chibi': 0.16, 'compact': 0.13, 'slim': 0.12}[PRE] * LEG
BETA = 0.6
SWAY = 0.030 * LEG; BOB = 0.022 * LEG
ROLL, YAW, CYAW, LEAN = 5.0, 7.0, 6.0, 3.0
HEAD_UP = float(os.environ.get('CHARLAB_HEAD_UP', 12.0))
SWING = {'chibi': 20.0, 'compact': 19.0, 'slim': 17.0}[PRE]
# arm abduction during the walk: enough to clear the hips
ab_need = math.degrees(math.asin(max(0.0, min(0.9, (W['hip_half'] + 2 * W.get('cloth', 0) + W['hand_r'] * 1.2 - W['sh_x']) / W['arm']))))
ABDUCT = min(max(W['abduct'], ab_need + 3), W['abduct'] + 10)
FOOT_X = 0.85
B = {n: (Vector(b['head']), Vector(b['tail'])) for n, b in zip(BN, META['bones'])}


def foot_state(phi):
    """ankle target (y, z offset) and foot pitch for one leg at its own phase phi in [0,1)."""
    phi %= 1.0
    if phi < BETA:
        u = phi / BETA; y = -STEP / 2 + STEP * u; z = 0.0
        pitch = -8.0 * (1 - ss(u / 0.15)) if u < 0.15 else (22.0 * ss((u - 0.80) / 0.20) if u > 0.80 else 0.0)
    else:
        u = (phi - BETA) / (1 - BETA); y = STEP / 2 - STEP * ss(u); z = LIFT * math.sin(math.pi * u) ** 1.2
        pitch = 22.0 * (1 - ss(u / 0.45)) - 8.0 * ss((u - 0.6) / 0.4)
    return y, z, pitch


def pelvis(t):
    return Vector((SWAY * math.sin(2 * math.pi * t), 0.0, -BOB * math.cos(4 * math.pi * t)))


def pose_world(t, drop):
    """world-space rotation deltas (absolute, relative to rest) and translations for every bone at phase t."""
    R, T = {}, {}
    c2, s2 = math.cos(2 * math.pi * t), math.sin(2 * math.pi * t)
    hips = Rz(-YAW * c2) @ Ry(-ROLL * s2) @ Rx(1.0)
    off = pelvis(t); off.z -= drop
    R['root'] = Quaternion(); T['root'] = Vector((0, 0, 0))
    R['hips'] = hips; T['hips'] = off
    R['spine'] = Rz(-YAW * 0.3 * c2) @ Ry(-ROLL * 0.4 * s2) @ Rx(LEAN * 0.6)
    chest = Rz(CYAW * c2) @ Ry(ROLL * 0.35 * s2) @ Rx(LEAN)
    R['chest'] = chest
    R['neck'] = Rz(CYAW * 0.4 * c2) @ Rx(LEAN * 0.3)
    nod = 2.0 + 1.5 * math.cos(4 * math.pi * (t - 0.06))
    R['head'] = Rx(nod - 1.0 - HEAD_UP)   # HEAD_UP: pitch-up cheat so the face reads under the 30 deg camera
    for s, sx in (('L', 1), ('R', -1)):
        R['shoulder.' + s] = chest
        lag = t - 0.04
        sw = -SWING * math.cos(2 * math.pi * lag) * sx * 1.0  # L arm back when L leg forward
        sw = sw if sx > 0 else -SWING * math.cos(2 * math.pi * (lag + 0.5))
        sw -= 3.0
        abd = Ry(sx * (25.0 - ABDUCT))
        up = chest @ Rx(-sw) @ abd
        bend = 10.0 + 16.0 * max(0.0, sw / SWING)
        fo = chest @ Rx(-(sw + bend)) @ abd
        R['upper_arm.' + s] = up; R['forearm.' + s] = fo; R['hand.' + s] = fo @ Rx(-4)
    return R, T


def two_bone(Hp, A, l1, l2, pole):
    d = (A - Hp); dl = d.length; dl = min(max(dl, 1e-4), l1 + l2 - 1e-4)
    dirv = d.normalized()
    ca = (l1 * l1 + dl * dl - l2 * l2) / (2 * l1 * dl); ca = max(-1.0, min(1.0, ca))
    pp = (pole - dirv * pole.dot(dirv)).normalized()
    knee = Hp + (dirv * ca + pp * math.sqrt(1 - ca * ca)) * l1
    ank = Hp + dirv * dl
    return knee, ank


def frame_rot(y_rest, y_new, pole):
    def F(y):
        y = y.normalized(); z = (pole - y * pole.dot(y)).normalized(); x = y.cross(z)
        return Matrix((x, y, z)).transposed()
    return (F(y_new) @ F(y_rest).transposed()).to_quaternion()


def fk(t, drop, apply=True):
    """returns posed armature-space matrices for every bone (and applies them as matrix_basis)."""
    R, T = pose_world(t, drop)
    P = {}
    order = BN

    def place(n, rot, extra=Vector((0, 0, 0))):
        par = PARENT[n]
        if par is None: hp = REST[n].translation + T.get(n, Vector((0, 0, 0)))
        else: hp = (P[par] @ REST[par].inverted()) @ REST[n].translation
        hp = hp + extra + (T.get(n, Vector((0, 0, 0))) if par else Vector((0, 0, 0)))
        P[n] = Matrix.Translation(hp) @ rot.to_matrix().to_4x4() @ REST[n].to_3x3().to_4x4()

    legs = {}
    for n in order:
        par = PARENT[n]
        if n.startswith('thigh.'):
            s = n[-1]; sx = 1 if s == 'L' else -1
            ph = t + (0.0 if s == 'L' else 0.5)
            y, z, pitch = foot_state(ph)
            hipm = P['hips'] @ REST['hips'].inverted()
            Hp = hipm @ B[n][0]
            ank_rest = B['shin.' + s][1]; ball = B['foot.' + s][1]
            # ankle target with heel/toe pivots
            base = Vector((sx * W['hip_x'] * FOOT_X, y, ank_rest.z + z))
            if pitch > 0:  # heel up: rotate about the ball
                piv = Vector((0, ball.y - ank_rest.y, ball.z - ank_rest.z))
                q = Rx(pitch); base = base + piv - q @ piv
            elif pitch < 0:  # toe up: rotate about the heel
                piv = Vector((0, W['foot_len'] * 0.26, -ank_rest.z * 0.9))
                q = Rx(pitch); base = base + piv - q @ piv
            l1, l2 = W['thigh'], W['shin']
            yawq = Rz(-YAW * math.cos(2 * math.pi * t) * 0.5)
            pole = yawq @ Vector((0, -1, 0.0))
            knee, ank = two_bone(Hp, base, l1, l2, pole)
            legs[s] = (Hp, knee, ank, pitch, (base - ank).length)
            rq = frame_rot(B[n][1] - B[n][0], knee - Hp, Vector((0, -1, 0)))
            rq = frame_rot(B[n][1] - B[n][0], knee - Hp, pole) if True else rq
            P[n] = Matrix.Translation(Hp) @ rq.to_matrix().to_4x4() @ REST[n].to_3x3().to_4x4()
            continue
        if n.startswith('shin.'):
            s = n[-1]; Hp, knee, ank, pitch, _ = legs[s]
            yawq = Rz(-YAW * math.cos(2 * math.pi * t) * 0.5); pole = yawq @ Vector((0, -1, 0))
            rq = frame_rot(B[n][1] - B[n][0], ank - knee, pole)
            P[n] = Matrix.Translation(knee) @ rq.to_matrix().to_4x4() @ REST[n].to_3x3().to_4x4()
            continue
        if n.startswith('foot.'):
            s = n[-1]; pitch = legs[s][3]
            place(n, Rx(pitch)); continue
        if n.startswith('toe.'):
            place(n, Rx(min(legs[n[-1]][3], 0))); continue
        if n.startswith('tail.'):
            k = int(n.split('.')[1]); place(n, tail_rot(t, k, R)); continue
        if n in SEC:
            place(n, *sec_rot(n, t, R)); continue
        rot = R.get(n)
        if rot is None:
            rot = R.get(par, Quaternion()) if par else Quaternion()
            R[n] = rot
        place(n, rot)
    if apply:
        for n in order:
            par = PARENT[n]
            if par is None: mb = REST[n].inverted() @ P[n]
            else: mb = REST[n].inverted() @ REST[par] @ P[par].inverted() @ P[n]
            rig.pose.bones[n].matrix_basis = mb
    return P, legs


SEC = {s['bone']: s for s in META.get('secondary', []) if s['type'] in ('rigid_lag', 'pendulum', 'rigid_flare')}
STIFF = {'soft': 1.4, 'medium-soft': 1.2, 'medium': 1.0, 'stiff': 0.6}
chain = [s for s in META.get('secondary', []) if s['type'] == 'spring_chain']
CH_K = STIFF.get(chain[0].get('stiffness', 'medium'), 1.0) if chain else 0.0


def tail_rot(t, k, R):
    """spring chain as a phase-lagged oscillator per bone (vertical bounce at 2x, lateral at 1x), amplitude grows to the tip."""
    head = R.get('head', Quaternion())
    if not chain: return head
    lag = 0.07 * k
    a = CH_K * k
    pitch = a * 5.0 * math.sin(4 * math.pi * (t - lag) + 0.8)
    side = a * 6.0 * math.sin(2 * math.pi * (t - lag))
    pitch = max(-25, min(25, pitch)); side = max(-25, min(25, side))
    return head @ Ry(side) @ Rx(pitch)


def sec_rot(n, t, R):
    s = SEC[n]; par = PARENT[n]; base = R.get(par, Quaternion())
    if s['type'] == 'pendulum':
        return (base @ Rx(9.0 * math.sin(2 * math.pi * (t - 0.18))) @ Ry(5.0 * math.sin(2 * math.pi * (t - 0.18))),)
    if s['type'] == 'rigid_lag':
        _, _ = None, None
        Rl, _ = pose_world(t - 1.0 / NF, 0.0)
        bounce = Vector((0, 0, -0.012 * math.cos(4 * math.pi * (t - 1.0 / NF))))
        return (Rl.get(par, Quaternion()), bounce)
    return (base,)


# pelvis drop so that the planted leg never over-extends (keeps the feet planted)
def reach_drop():
    drop = 0.02 * LEG
    for _ in range(30):
        worst = 0.0
        for i in range(NF):
            _, legs = fk(i / NF, drop, apply=False)
            for s in 'LR': worst = max(worst, legs[s][4])
        if worst < 1e-4: break
        drop += max(worst, 0.002)
    return drop


DROP = reach_drop()

# ---------------------------------------------------------------------------------------------------------- camera
AZ = {'S': (0, -1), 'SE': (-1, -1), 'E': (-1, 0), 'SW': (1, -1), 'W': (1, 0)}
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.clip_start = 0.1; cam.data.clip_end = 200
EL = math.radians(30); DIST = 40.0


def cam_basis(view):
    ax, ay = AZ[view]; n = math.hypot(ax, ay); ax, ay = ax / n, ay / n
    d = Vector((ax * math.cos(EL), ay * math.cos(EL), math.sin(EL)))   # from target toward camera
    q = (-d).to_track_quat('-Z', 'Y')
    M = q.to_matrix()
    return d, q, M.col[0].copy(), M.col[1].copy()


# ortho scale from the rest mesh projected in the S view (same scale for every view and frame)
_, _, rS, uS = cam_basis('S')
ys = V @ np.array(uS)
ORTHO = float(ys.max() - ys.min()) * HI / FIG
cam.data.ortho_scale = ORTHO
PPU = HI / ORTHO  # hi-res px per H unit


def set_view(view):
    d, q, r, u = cam_basis(view)
    T = Vector((0, 0, 0)) + u * ((GROUND - HI / 2) / HI * ORTHO)
    cam.rotation_mode = 'QUATERNION'; cam.rotation_quaternion = q
    cam.location = T + d * DIST
    bpy.context.view_layer.update()


# ---------------------------------------------------------------------------------------------------------- render setup
sc.render.resolution_x = sc.render.resolution_y = HI; sc.render.resolution_percentage = 100
sc.render.film_transparent = True; sc.render.dither_intensity = 0.0
if not sc.world: sc.world = bpy.data.worlds.new('w')
sc.world.color = (0, 0, 0)


def emission_mat():
    m = bpy.data.materials.new('nd'); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    for n in list(N): N.remove(n)
    out = N.new('ShaderNodeOutputMaterial'); em = N.new('ShaderNodeEmission'); L.new(em.outputs[0], out.inputs[0])
    g = N.new('ShaderNodeNewGeometry')
    vn = N.new('ShaderNodeVectorTransform'); vn.vector_type = 'NORMAL'; vn.convert_from = 'WORLD'; vn.convert_to = 'CAMERA'
    vp = N.new('ShaderNodeVectorTransform'); vp.vector_type = 'POINT'; vp.convert_from = 'WORLD'; vp.convert_to = 'CAMERA'
    L.new(g.outputs['Normal'], vn.inputs[0]); L.new(g.outputs['Position'], vp.inputs[0])
    sn = N.new('ShaderNodeSeparateXYZ'); sp = N.new('ShaderNodeSeparateXYZ'); L.new(vn.outputs[0], sn.inputs[0]); L.new(vp.outputs[0], sp.inputs[0])
    cx = N.new('ShaderNodeMath'); cx.operation = 'MULTIPLY_ADD'; cx.inputs[1].default_value = .5; cx.inputs[2].default_value = .5
    cy = N.new('ShaderNodeMath'); cy.operation = 'MULTIPLY_ADD'; cy.inputs[1].default_value = .5; cy.inputs[2].default_value = .5
    cz = N.new('ShaderNodeMath'); cz.operation = 'MULTIPLY'; cz.inputs[1].default_value = 1.0 / 100.0
    L.new(sn.outputs['X'], cx.inputs[0]); L.new(sn.outputs['Y'], cy.inputs[0]); L.new(sp.outputs['Z'], cz.inputs[0])
    cb = N.new('ShaderNodeCombineXYZ'); L.new(cx.outputs[0], cb.inputs[0]); L.new(cy.outputs[0], cb.inputs[1]); L.new(cz.outputs[0], cb.inputs[2])
    L.new(cb.outputs[0], em.inputs[0])
    return m


ND = emission_mat()
TMP = os.path.join(OUT, '_tmp'); os.makedirs(TMP, exist_ok=True)


def read_img(path):
    img = bpy.data.images.load(path, check_existing=False)
    try: img.colorspace_settings.name = 'Non-Color'
    except Exception: pass
    w, h = img.size; a = np.empty(w * h * 4, np.float32); img.pixels.foreach_get(a)
    bpy.data.images.remove(img)
    return a.reshape(h, w, 4)[::-1]


def render_id(path):
    sc.render.engine = 'BLENDER_WORKBENCH'
    sh = sc.display.shading; sh.light = 'FLAT'; sh.color_type = 'MATERIAL'
    sh.show_object_outline = False; sh.show_cavity = False
    try: sh.show_specular_highlight = False
    except Exception: pass
    sc.display.render_aa = 'OFF'
    sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'; sc.view_settings.exposure = 0; sc.view_settings.gamma = 1
    bpy.context.view_layer.material_override = None
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'; sc.render.image_settings.color_depth = '8'
    sc.render.filepath = path; bpy.ops.render.render(write_still=True)


def render_nd(path):
    sc.render.engine = 'BLENDER_EEVEE'
    sc.eevee.taa_render_samples = 1
    try: sc.render.filter_size = 0.0
    except Exception: pass
    sc.view_settings.view_transform = 'Raw' if 'Raw' in [x.identifier for x in sc.view_settings.bl_rna.properties['view_transform'].enum_items] else 'Standard'
    bpy.context.view_layer.material_override = ND
    sc.render.image_settings.file_format = 'OPEN_EXR'; sc.render.image_settings.color_mode = 'RGBA'
    sc.render.image_settings.color_depth = '32'; sc.render.image_settings.exr_codec = 'ZIP'
    sc.render.filepath = path; bpy.ops.render.render(write_still=True)


def decode_id(a):
    rgb = np.round(a[..., :3] * 255).astype(int); al = a[..., 3] > 0.5
    mat = np.clip(np.round((rgb[..., 0] - 20) / 10), 0, 23).astype(np.uint8)
    grp = np.clip(np.round((rgb[..., 1] - 20) / 22), 0, 10).astype(np.uint8)
    ok = (np.abs(rgb[..., 0] - (20 + 10 * mat.astype(int))) <= 3) & (np.abs(rgb[..., 1] - (20 + 22 * grp.astype(int))) <= 3)
    grp[~al] = 0; mat[~al] = 0
    return mat, grp, al, int((al & ~ok).sum())


def block4(a, al, how):
    h, w = a.shape; a4 = a.reshape(h // 4, 4, w // 4, 4); m4 = al.reshape(h // 4, 4, w // 4, 4)
    cnt = m4.sum((1, 3))
    if how == 'mean':
        s = (a4 * m4).sum((1, 3)); return np.where(cnt > 0, s / np.maximum(cnt, 1), 0)
    big = np.where(m4, a4, 1e9); return np.where(cnt > 0, big.min((1, 3)), 0)


ANCH = META.get('anchors', {})
info = dict(id=META['id'], tier=META['tier'], preset=META['preset'], hi=HI, fig=FIG, ground=GROUND, ortho=ORTHO, ppu=PPU,
            views=VIEWS, nf=NF, drop=DROP, abduct=ABDUCT, step=STEP, frames=[])
bad_total = 0
for i in range(NF):
    t = i / NF
    fk(t, DROP)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(dg); em = ev.to_mesh()
    apos = {k: (em.vertices[v].co.copy(), em.vertices[v].normal.copy()) for k, v in ANCH.items()}
    ev.to_mesh_clear()
    fr = dict(i=i, ms=120, views={})
    for view in VIEWS:
        set_view(view)
        Ci = cam.matrix_world.inverted(); back = cam.matrix_world.to_3x3().col[2].normalized()
        an = {}
        for k, (p, nrm) in apos.items():
            pc = Ci @ p
            an[k] = dict(x=HI / 2 + pc.x / ORTHO * HI, y=HI / 2 - pc.y / ORTHO * HI, depth=-pc.z, facing=float(nrm.dot(back)))
        fr['views'][view] = dict(anchors=an)
        pid = os.path.join(TMP, f'{view}_f{i:02d}_id.png'); pnd = os.path.join(TMP, f'{view}_f{i:02d}_nd.exr')
        render_id(pid); render_nd(pnd)
        mat, grp, al, bad = decode_id(read_img(pid)); bad_total += bad
        nd = read_img(pnd)
        a = np.maximum(nd[..., 3], 1e-6)[..., None]
        ndv = np.where(nd[..., 3:4] > 0, nd[..., :3] / a, 0)
        nx = ndv[..., 0] * 2 - 1; ny = ndv[..., 1] * 2 - 1; dep = ndv[..., 2] * 100.0
        np.savez_compressed(os.path.join(OUT, f'{view}_f{i:02d}.npz'), mat=mat, grp=grp,
                            nx=block4(nx, al, 'mean').astype(np.float16), ny=block4(ny, al, 'mean').astype(np.float16),
                            dep=block4(dep, al, 'min').astype(np.float32))
        os.remove(pid); os.remove(pnd)
    info['frames'].append(fr)
info['id_decode_bad_px'] = bad_total
json.dump(info, open(os.path.join(OUT, 'frames.json'), 'w'), indent=1)
os.rmdir(TMP)
if os.environ.get('CHARLAB_SAVE_BLEND'):
    fk(0.0, DROP); bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'rig.blend'))
print(f'WALK_RENDERED {META["id"]} {META["tier"]} {META["preset"]} views={VIEWS} frames={NF} drop={DROP:.3f} abduct={ABDUCT:.1f} '
      f'ppu={PPU:.1f} id_bad={bad_total}', flush=True)
