"""Humanoid armature + secondary chains (ponytail 4, side locks 3, bow tails 2, scarf tail 3), weights, UVs."""
import bpy, math
import numpy as np
from mathutils import Vector, Matrix
import body

HUMAN = []

def _centroids(V, mask, zs, band=0.03):
    out = []
    for z in zs:
        m = mask & (np.abs(V[:, 2] - z) < band)
        out.append(V[m].mean(0) if m.any() else None)
    return out

def build_armature(objs, coll):
    arm_d = bpy.data.armatures.new('Rig'); arm = bpy.data.objects.new('Rig', arm_d)
    coll.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    for o in bpy.context.selected_objects:
        o.select_set(False)
    arm.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    eb = arm_d.edit_bones
    def B(name, h, t, parent=None, deform=True):
        b = eb.new(name); b.head = Vector(h); b.tail = Vector(t); b.use_deform = deform
        if parent:
            b.parent = eb[parent]; b.use_connect = False
        return b
    B('root', (0, 0, 0), (0, 0.12, 0), deform=False)
    B('hips', (0, 0.005, 0.86), (0, 0.005, 0.975), 'root')
    B('spine', (0, 0.005, 0.975), (0, 0.000, 1.10), 'hips')
    B('chest', (0, 0.000, 1.10), (0, 0.006, 1.235), 'spine')
    B('neck', (0, 0.012, 1.235), (0, 0.010, 1.33), 'chest')
    B('head', (0, 0.010, 1.33), (0, 0.010, 1.575), 'neck')
    for sx, s in ((1, 'L'), (-1, 'R')):
        S = body.S_L * [sx, 1, 1]; E = body.E_L * [sx, 1, 1]; W = body.W_L * [sx, 1, 1]; D3 = body.D3 * [sx, 1, 1]
        B(f'shoulder.{s}', (sx * 0.020, 0.004, 1.215), S, 'chest')
        B(f'upper_arm.{s}', S, E, f'shoulder.{s}')
        B(f'forearm.{s}', E, W, f'upper_arm.{s}')
        B(f'hand.{s}', W, W + D3 * 0.11, f'forearm.{s}')
        B(f'thigh.{s}', (sx * 0.078, 0.004, 0.845), (sx * 0.072, 0.004, 0.445), 'hips')
        B(f'shin.{s}', (sx * 0.072, 0.004, 0.445), (sx * 0.077, 0.014, 0.080), f'thigh.{s}')
        B(f'foot.{s}', (sx * 0.077, 0.014, 0.080), (sx * 0.081, -0.085, 0.030), f'shin.{s}')
        B(f'toe.{s}', (sx * 0.081, -0.085, 0.030), (sx * 0.083, -0.150, 0.028), f'foot.{s}')
    global HUMAN
    HUMAN = [b.name for b in eb if b.use_deform]
    chains = {}
    # ponytail (4) along the stored axis
    ax = np.array(objs['Hair_Ponytail']['axis'])
    idx = np.linspace(4, len(ax) - 1, 5).astype(int)
    pts = ax[idx]
    par = 'head'
    names = []
    for i in range(4):
        n = f'ponytail.{i + 1:02d}'; B(n, pts[i], pts[i + 1], par); par = n; names.append(n)
    chains['ponytail'] = (names, pts)
    # side locks (3 each), from mesh centroids
    V = np.array([v.co[:] for v in objs['Hair_SideLocks'].data.vertices])
    for sx, s in ((1, 'L'), (-1, 'R')):
        c = _centroids(V, V[:, 0] * sx > 0.06, [1.40, 1.33, 1.26, 1.16], 0.02)
        names = []; par = 'head'
        for i in range(3):
            n = f'sidelock.{s}.{i + 1:02d}'; B(n, c[i], c[i + 1], par); par = n; names.append(n)
        chains[f'sidelock.{s}'] = (names, np.array(c))
    # bow tails (2 each)
    V = np.array([v.co[:] for v in objs['Bow'].data.vertices])
    zk = V[:, 2].max() - 0.10
    for sx, s in ((1, 'L'), (-1, 'R')):
        m = (V[:, 0] * sx > 0.004) & (V[:, 2] < zk + 0.035) & (np.abs(V[:, 0]) < 0.11)
        top = V[m][:, 2].max(); bot = V[m][:, 2].min()
        c = _centroids(V, m, np.linspace(top - 0.005, bot + 0.01, 3), 0.012)
        names = []; par = 'head'
        for i in range(2):
            n = f'bowtail.{s}.{i + 1:02d}'; B(n, c[i], c[i + 1], par); par = n; names.append(n)
        chains[f'bowtail.{s}'] = (names, np.array(c))
    # scarf tail (3)
    V = np.array([v.co[:] for v in objs['Scarf'].data.vertices])
    m = (V[:, 0] > 0.03) & (V[:, 1] < -0.06) & (V[:, 2] < 1.235)
    c = _centroids(V, m, [1.22, 1.13, 1.04, 0.95], 0.02)
    names = []; par = 'chest'
    for i in range(3):
        n = f'scarf_tail.{i + 1:02d}'; B(n, c[i], c[i + 1], par); par = n; names.append(n)
    chains['scarf_tail'] = (names, np.array(c))
    bpy.ops.object.mode_set(mode='OBJECT')
    return arm, chains

# ------------------------------------------------------------------ weights
def _seg_dist(P, a, b):
    ab = b - a; t = np.clip(((P - a) @ ab) / max(ab @ ab, 1e-12), 0, 1)
    return np.linalg.norm(P - (a + t[:, None] * ab), axis=1), t

def envelope_weights(ob, arm, bones, power=6.0):
    """Distance-falloff weights (normalised, top-3)."""
    V = np.array([ob.matrix_world @ v.co for v in ob.data.vertices])
    D = []
    for bn in bones:
        b = arm.data.bones[bn]
        d, _ = _seg_dist(V, np.array(b.head_local), np.array(b.tail_local))
        D.append(d)
    D = np.array(D).T + 1e-4
    W = 1.0 / D ** power
    keep = np.argsort(-W, axis=1)[:, :3]
    M = np.zeros_like(W); np.put_along_axis(M, keep, 1.0, axis=1)
    W = W * M; W /= W.sum(1, keepdims=True)
    return V, W

def set_weights(ob, bones, W, thresh=0.01):
    for g in list(ob.vertex_groups):
        if g.name in bones or g.name.split('.')[0] in ('ponytail', 'sidelock', 'bowtail', 'scarf_tail'):
            ob.vertex_groups.remove(g)
    groups = {bn: ob.vertex_groups.new(name=bn) for bn in bones}
    for k, bn in enumerate(bones):
        col = W[:, k]
        for i in np.nonzero(col > thresh)[0]:
            groups[bn].add([int(i)], float(col[i]), 'REPLACE')

def chain_weights(V, pts, names, root, root_until=0.08, along=None):
    """Weights for a chain: project onto polyline, blend between neighbouring bones."""
    seg = np.array([np.linalg.norm(pts[i + 1] - pts[i]) for i in range(len(pts) - 1)])
    L = np.r_[0, np.cumsum(seg)]
    best = np.full(len(V), 1e9); s = np.zeros(len(V))
    for i in range(len(pts) - 1):
        d, t = _seg_dist(V, pts[i], pts[i + 1])
        better = d < best
        best = np.where(better, d, best); s = np.where(better, (L[i] + t * seg[i]) / L[-1], s)
    if along is not None:
        s = along
    n = len(names)
    W = np.zeros((len(V), n + 1))
    pos = s * n
    for k in range(n):
        W[:, k + 1] = np.clip(1 - np.abs(pos - (k + 0.5)), 0, 1)
    W[:, 1] = np.where(pos < 0.5, 1.0, W[:, 1])
    W[:, n] = np.where(pos > n - 0.5, 1.0, W[:, n])
    r = np.clip(1 - s / max(root_until, 1e-6), 0, 1)
    W[:, 1:] *= (1 - r)[:, None]
    W[:, 0] = r
    W /= np.maximum(W.sum(1, keepdims=True), 1e-9)
    return [root] + names, W

def auto_or_envelope(ob, arm, bones):
    """Try Blender's heat (automatic) weights; fall back to envelope weights for any vertex left unweighted."""
    ok = False
    try:
        for o in bpy.context.selected_objects:
            o.select_set(False)
        ob.select_set(True); arm.select_set(True)
        bpy.context.view_layer.objects.active = arm
        bpy.ops.object.parent_set(type='ARMATURE_AUTO')
        ok = True
    except Exception as e:
        print('AUTO failed', ob.name, e)
    # drop groups for non-allowed bones, renormalise, fill gaps from envelope
    V, We = envelope_weights(ob, arm, bones)
    gi = {g.index: g.name for g in ob.vertex_groups}
    W = np.zeros((len(ob.data.vertices), len(bones)))
    col = {b: k for k, b in enumerate(bones)}
    for v in ob.data.vertices:
        for g in v.groups:
            n = gi.get(g.group)
            if n in col:
                W[v.index, col[n]] = g.weight
    s = W.sum(1)
    bad = s < 1e-3
    W[bad] = We[bad]
    W /= np.maximum(W.sum(1, keepdims=True), 1e-9)
    for g in list(ob.vertex_groups):
        if g.name in [b.name for b in arm.data.bones]:
            ob.vertex_groups.remove(g)
    return V, W, int(bad.sum()), ok

def smooth_mix(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)

def skin_all(objs, arm, chains):
    body_bones = [b for b in HUMAN if b not in ('root',)]
    report = {}
    for n in ('Body', 'Tights', 'Coat', 'Boots', 'Mittens', 'Belt'):
        ob = objs[n]
        allowed = {'Body': body_bones, 'Tights': ['hips', 'thigh.L', 'shin.L', 'thigh.R', 'shin.R', 'foot.L', 'foot.R'],
                   'Coat': [b for b in body_bones if not b.startswith(('foot', 'toe', 'shin', 'hand', 'head'))],
                   'Boots': ['shin.L', 'foot.L', 'toe.L', 'shin.R', 'foot.R', 'toe.R'],
                   'Mittens': ['forearm.L', 'hand.L', 'forearm.R', 'hand.R'],
                   'Belt': ['hips', 'spine']}[n]
        V, W, nbad, ok = auto_or_envelope(ob, arm, allowed)
        if n == 'Coat':
            # hand-clean the skirt: mostly hips, gentle thigh follow, no left/right tearing
            z = V[:, 2]
            sk = smooth_mix(0.97, 0.90, z)
            fol = 0.40 * smooth_mix(0.90, 0.62, z)
            side = smooth_mix(-0.06, 0.06, V[:, 0])
            ci = {b: k for k, b in enumerate(allowed)}
            Wn = np.zeros_like(W)
            Wn[:, ci['hips']] = 1 - fol
            Wn[:, ci['thigh.L']] = fol * side
            Wn[:, ci['thigh.R']] = fol * (1 - side)
            sleeve = (np.abs(V[:, 0]) > 0.14) & (z > 0.70)
            m = (sk > 0) & ~sleeve
            W[m] = W[m] * (1 - sk[m, None]) + Wn[m] * sk[m, None]
        if n in ('Body', 'Coat'):
            # neck / collar: blend chest -> neck cleanly
            ci = {b: k for k, b in enumerate(allowed)}
            if 'neck' in ci:
                z = V[:, 2]
                nk = smooth_mix(1.235, 1.27, z) * (np.abs(V[:, 0]) < 0.06)
                for k in range(W.shape[1]):
                    W[:, k] *= (1 - nk)
                W[:, ci['neck']] += nk
        W /= np.maximum(W.sum(1, keepdims=True), 1e-9)
        set_weights(ob, allowed, W)
        report[n] = ('heat' if ok else 'envelope', nbad)
    # head + face parts: head with neck blend
    for n in ('Head', 'Eyes', 'FaceLines', 'Brows', 'Hair_Cap', 'Hair_Bangs', 'Hair_Highlight', 'Hair_Back', 'Hair_Strands'):
        ob = objs[n]
        V = np.array([ob.matrix_world @ v.co for v in ob.data.vertices])
        w = smooth_mix(1.30, 1.345, V[:, 2]) if n == 'Head' else np.ones(len(V))
        if n == 'Hair_Back':
            w = 1 - 0.35 * smooth_mix(1.25, 1.0, V[:, 2])     # lower back hair partly follows the chest
            set_weights(ob, ['head', 'chest'], np.stack([w, 1 - w], 1)); continue
        set_weights(ob, ['head', 'neck'], np.stack([w, 1 - w], 1))
    # ponytail chain
    ob = objs['Hair_Ponytail']; names, pts = chains['ponytail']
    V = np.array([v.co[:] for v in ob.data.vertices])
    bn, W = chain_weights(V, pts, names, 'head', 0.06)
    set_weights(ob, bn, W)
    # side locks
    ob = objs['Hair_SideLocks']; V = np.array([v.co[:] for v in ob.data.vertices])
    allb, allW = [], []
    WW = np.zeros((len(V), 7)); names_all = ['head']
    for k, s in enumerate(('L', 'R')):
        names, pts = chains[f'sidelock.{s}']
        bn, W = chain_weights(V, pts, names, 'head', 0.10)
        m = (V[:, 0] > 0) if s == 'L' else (V[:, 0] <= 0)
        WW[m, 0] = W[m, 0]; WW[m, 1 + 3 * k:4 + 3 * k] = W[m, 1:]
        names_all += names
    set_weights(ob, names_all, WW)
    # bow (knot+loops on head, tails on chains)
    ob = objs['Bow']; V = np.array([v.co[:] for v in ob.data.vertices])
    WW = np.zeros((len(V), 5)); WW[:, 0] = 1.0; names_all = ['head']
    for k, s in enumerate(('L', 'R')):
        names, pts = chains[f'bowtail.{s}']
        names_all += names
        sx = 1 if s == 'L' else -1
        m = (V[:, 0] * sx > 0) & (V[:, 2] < pts[0][2] + 0.004) & (np.abs(V[:, 0]) < 0.11)
        bn, W = chain_weights(V[m], pts, names, 'head', 0.15)
        WW[m] = 0; WW[m, 0] = W[:, 0]; WW[m, 1 + 2 * k:3 + 2 * k] = W[:, 1:]
    set_weights(ob, names_all, WW)
    # scarf: roll on neck/chest, tail on chain
    ob = objs['Scarf']; V = np.array([v.co[:] for v in ob.data.vertices])
    names, pts = chains['scarf_tail']
    bn, W = chain_weights(V, pts, names, 'chest', 0.08)
    tail = (V[:, 0] > 0.03) & (V[:, 1] < -0.06) & (V[:, 2] < 1.235)
    WW = np.zeros((len(V), 5)); names_all = ['neck', 'chest'] + names
    WW[:, 0] = 0.55; WW[:, 1] = 0.45
    WW[tail] = 0; WW[tail, 1] = W[tail, 0]; WW[tail, 2:] = W[tail, 1:]
    set_weights(ob, names_all, WW)
    # armature modifiers first in stack
    for n, ob in objs.items():
        if ob.type != 'MESH':
            continue
        if ob.parent != arm:
            mw = ob.matrix_world.copy(); ob.parent = arm; ob.matrix_world = mw
        am = None
        for m in ob.modifiers:
            if m.type == 'ARMATURE':
                am = m
        if am is None:
            am = ob.modifiers.new('Armature', 'ARMATURE')
        am.object = arm
        with bpy.context.temp_override(object=ob):
            while ob.modifiers.find(am.name) > 0:
                bpy.ops.object.modifier_move_up(modifier=am.name)
    return report

def parent_to_bone(ob, arm, bone):
    mw = ob.matrix_world.copy()
    ob.parent = arm; ob.parent_type = 'BONE'; ob.parent_bone = bone
    ob.matrix_world = mw

# ------------------------------------------------------------------ UVs
def unwrap(objs):
    hair = [o for n, o in objs.items() if n.startswith('Hair')]
    others = [o for n, o in objs.items() if not n.startswith('Hair') and n != 'Eyes']
    def proj(group):
        for o in bpy.context.selected_objects:
            o.select_set(False)
        for o in group:
            o.select_set(True)
            if not o.data.uv_layers:
                o.data.uv_layers.new(name='UVMap')
        bpy.context.view_layer.objects.active = group[0]
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.01, area_weight=0.0, scale_to_bounds=False)
        bpy.ops.object.mode_set(mode='OBJECT')
    proj(hair)                    # one shared hair atlas
    for o in others:
        proj([o])
