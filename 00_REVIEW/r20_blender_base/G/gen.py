# ==============================================================================
# S0: CORE (Imports, CLI Args, Proportions, Materials, Helpers)
# ==============================================================================
import sys
import os
import math
import bpy
import bmesh
from mathutils import Vector, Matrix, Euler


def parse_args():
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []

    outdir = "."
    build_mode = "base"
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--build" and i + 1 < len(argv):
            build_mode = argv[i + 1].strip().lower()
            i += 2
        elif not arg.startswith("-"):
            outdir = arg
            i += 1
        else:
            i += 1
    if build_mode not in ("base", "sprite"):
        build_mode = "base"
    return outdir, build_mode


PALETTE_HEX = {
    "skin": "#FCD6B4",
    "skin_shadow": "#EBA586",
    "blush": "#F4A0A0",
    "mouth": "#8E2C4A",
    "eye_white": "#FFFFFF",
    "iris": "#2C9696",
    "iris_dark": "#1C4C54",
    "lash": "#20223E",
    "brow": "#6E3C3A",
    "catchlight": "#FFFFFF",
    "hair": "#A85A3A",
    "hair_shadow": "#6E3C3A",
    "hair_hi": "#D08658",
    "teal": "#2A8C8E",
    "teal_dark": "#1C4C54",
    "teal_light": "#6ACBB6",
    "coat": "#F2E6CE",
    "coat_shadow": "#D2BFA4",
    "rust": "#A85A3A",
    "belt": "#6E3C3A",
    "gold": "#E2A434",
    "tights": "#45435E",
    "boots": "#6E3C3A",
    "fur": "#F2E6CE",
}


def srgb_to_linear(c):
    if c <= 0.04045:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4


def hex_to_rgba(hex_str, alpha=1.0):
    h = hex_str.lstrip("#")
    r = srgb_to_linear(int(h[0:2], 16) / 255.0)
    g = srgb_to_linear(int(h[2:4], 16) / 255.0)
    b = srgb_to_linear(int(h[4:6], 16) / 255.0)
    return (r, g, b, alpha)


def create_materials():
    mats = {}
    for name, hex_val in PALETTE_HEX.items():
        mat = bpy.data.materials.new(name=name)
        rgba = hex_to_rgba(hex_val, 1.0)
        mat.diffuse_color = rgba
        mat.specular_intensity = 0.05
        mat.roughness = 0.85
        mat.use_nodes = True
        if mat.node_tree:
            bsdf = mat.node_tree.nodes.get("Principled BSDF")
            if bsdf:
                bsdf.inputs["Base Color"].default_value = rgba
                if "Roughness" in bsdf.inputs:
                    bsdf.inputs["Roughness"].default_value = 0.85
                if "Specular IOR Level" in bsdf.inputs:
                    bsdf.inputs["Specular IOR Level"].default_value = 0.1
        mats[name] = mat
    return mats


class Proportions:
    """
    Computes exact metric coordinates for either 'base' (5.4 H) or 'sprite' (3.4 H),
    normalized so the top of the hair crown (excluding the bow) is at z = 1.0
    and the soles of the boots are at z = 0.0.
    """
    def __init__(self, build_mode="base"):
        self.build = build_mode
        self.hair_top_pad_h = 0.12  # Hair volume above skull crown in H units

        if build_mode == "base":
            # 5.4 H from skull crown to sole + 0.12 H hair crown pad = 5.52 H total
            self.body_h_units = 5.40
            self.total_h_units = self.body_h_units + self.hair_top_pad_h
            self.H = 1.0 / self.total_h_units  # ~0.18116 m

            H = self.H
            self.z_sole = 0.0
            self.z_hair_crown = 1.0
            self.z_crown = 1.0 - self.hair_top_pad_h * H
            self.z_chin = self.z_crown - 1.0 * H
            self.z_head_center = 0.5 * (self.z_crown + self.z_chin)

            # Vertical landmarks (from crown downwards)
            self.z_eye = self.z_chin + 0.44 * H
            self.z_brow = self.z_chin + 0.61 * H
            self.z_nose = self.z_chin + 0.27 * H
            self.z_mouth = self.z_chin + 0.15 * H

            self.z_neck_top = self.z_chin + 0.04 * H
            self.z_shoulder = self.z_crown - 1.24 * H
            self.z_bust = self.z_crown - 1.62 * H
            self.z_belt = self.z_crown - 2.05 * H
            self.z_hip = self.z_Sole_hip = 2.40 * H
            self.z_hem = 1.88 * H
            self.z_knee = 1.22 * H
            self.z_boot_top = 0.86 * H
            self.z_ankle = 0.22 * H

            # Horizontal widths (full widths in metres, half-width is w/2)
            self.head_w = 0.82 * H
            self.head_d = 0.84 * H
            self.shoulder_w = 0.90 * H
            self.bust_w = 0.84 * H
            self.waist_w = 0.75 * H
            self.hip_w = 1.00 * H
            self.hem_w = 1.60 * H
            self.hem_d = 1.02 * H

            self.leg_spacing = 0.23 * H
            self.thigh_r = 0.165 * H
            self.knee_r = 0.115 * H
            self.calf_r = 0.130 * H
            self.ankle_r = 0.090 * H

            self.arm_angle_deg = 14.0
            self.sleeve_len = (self.z_shoulder - self.z_hem) * 0.86
            self.mitten_r = 0.145 * H

            self.z_back_hair_tip = self.z_hip + 0.05 * H
            self.z_ponytail_tip = self.z_belt - 0.08 * H

        else:
            # SPRITE BUILD: 3.4 H from skull crown to sole + 0.12 H hair crown pad
            self.body_h_units = 3.40
            self.total_h_units = self.body_h_units + self.hair_top_pad_h
            self.H = 1.0 / self.total_h_units  # ~0.28409 m

            H = self.H
            self.z_sole = 0.0
            self.z_hair_crown = 1.0
            self.z_crown = 1.0 - self.hair_top_pad_h * H
            self.z_chin = self.z_crown - 1.0 * H
            self.z_head_center = 0.5 * (self.z_crown + self.z_chin)

            # Face landmarks stay identical in H-relative proportions
            self.z_eye = self.z_chin + 0.44 * H
            self.z_brow = self.z_chin + 0.61 * H
            self.z_nose = self.z_chin + 0.27 * H
            self.z_mouth = self.z_chin + 0.15 * H

            self.z_neck_top = self.z_chin + 0.04 * H
            self.z_shoulder = self.z_crown - 1.15 * H
            self.z_bust = self.z_crown - 1.40 * H
            self.z_belt = self.z_crown - 1.68 * H
            self.z_hip = 1.10 * H
            self.z_hem = 0.82 * H
            self.z_knee = 0.56 * H
            self.z_boot_top = 0.46 * H
            self.z_ankle = 0.14 * H

            self.head_w = 0.82 * H
            self.head_d = 0.84 * H
            self.shoulder_w = 0.94 * H
            self.bust_w = 0.90 * H
            self.waist_w = 0.86 * H
            self.hip_w = 1.08 * H
            self.hem_w = 1.70 * H
            self.hem_d = 1.12 * H

            self.leg_spacing = 0.24 * H
            self.thigh_r = 0.175 * H
            self.knee_r = 0.125 * H
            self.calf_r = 0.135 * H
            self.ankle_r = 0.100 * H

            self.arm_angle_deg = 15.0
            self.sleeve_len = (self.z_shoulder - self.z_hem) * 0.84
            self.mitten_r = 0.155 * H

            # Shorter back hair and ponytail so coat & sleeves read clearly at 44px
            self.z_back_hair_tip = self.z_belt + 0.02 * H
            self.z_ponytail_tip = self.z_belt + 0.04 * H


# ==============================================================================
# GEOMETRY & MODIFIER HELPERS
# ==============================================================================

def link_obj(obj):
    bpy.context.collection.objects.link(obj)
    return obj


def new_mesh_obj(name, bm, mat=None, shade_smooth=True):
    mesh = bpy.data.meshes.new(name)
    bm.normal_update()
    bm.to_mesh(mesh)
    bm.free()
    if shade_smooth:
        for p in mesh.polygons:
            p.use_smooth = True
    obj = bpy.data.objects.new(name, mesh)
    link_obj(obj)
    if mat is not None:
        obj.data.materials.append(mat)
    return obj


def add_subsurf(obj, levels=2, boundary_smooth='ALL'):
    mod = obj.modifiers.new(name="Subsurf", type='SUBSURF')
    mod.levels = levels
    mod.render_levels = levels
    if hasattr(mod, "boundary_smooth"):
        mod.boundary_smooth = boundary_smooth
    return mod


def add_solidify(obj, thickness=0.005, offset=1.0, even=True):
    mod = obj.modifiers.new(name="Solidify", type='SOLIDIFY')
    mod.thickness = thickness
    mod.offset = offset
    mod.use_even_offset = even
    mod.use_rim = True
    return mod


def add_mirror(obj, use_x=True, merge_thresh=0.0005):
    mod = obj.modifiers.new(name="Mirror", type='MIRROR')
    mod.use_axis[0] = use_x
    mod.use_clip = True
    mod.merge_threshold = merge_thresh
    return mod


def loft_loops(bm, loops, cap_start=False, cap_end=False, closed_loop=True):
    """
    Given a list of vertex loops (each loop a list of BMVerts of equal length),
    bridges them with quad faces and optionally caps ends.
    """
    n_rings = len(loops)
    if n_rings < 2:
        return
    n_verts = len(loops[0])
    for r in range(n_rings - 1):
        ring_a = loops[r]
        ring_b = loops[r + 1]
        limit = n_verts if closed_loop else (n_verts - 1)
        for i in range(limit):
            i_next = (i + 1) % n_verts
            v1 = ring_a[i]
            v2 = ring_a[i_next]
            v3 = ring_b[i_next]
            v4 = ring_b[i]
            try:
                bm.faces.new((v1, v2, v3, v4))
            except ValueError:
                pass

    if cap_start and closed_loop and n_verts >= 3:
        try:
            bm.faces.new(list(reversed(loops[0])))
        except ValueError:
            pass
    if cap_end and closed_loop and n_verts >= 3:
        try:
            bm.faces.new(loops[-1])
        except ValueError:
            pass


def make_ellipse_ring(bm, center, rx, ry, n=16, tilt_x=0.0, front_flatten=1.0, back_flatten=1.0):
    """
    Creates a horizontal ring of BMVerts in XY around `center` (Vector).
    Angle 0 is +X, pi/2 is +Y (back), -pi/2 is -Y (front).
    """
    verts = []
    rot = Euler((tilt_x, 0.0, 0.0), 'XYZ').to_matrix()
    for i in range(n):
        theta = 2.0 * math.pi * i / n
        ca = math.cos(theta)
        sa = math.sin(theta)
        y_scale = ry * (front_flatten if sa < 0 else back_flatten)
        local = Vector((rx * ca, y_scale * sa, 0.0))
        pt = center + (rot @ local)
        verts.append(bm.verts.new(pt))
    return verts


def create_head_center_empty(P):
    empty = bpy.data.objects.new("head_center", None)
    empty.empty_display_type = 'PLAIN_AXES'
    empty.empty_display_size = 0.25 * P.H
    empty.location = (0.0, 0.0, P.z_head_center)
    empty["head_h"] = float(P.H)
    link_obj(empty)
    return empty


def normalize_crown_to_unit_z(P):
    """
    Ensures the highest vertex of the hair crown/bangs/head (excluding the bow)
    sits at z = 1.0 and the lowest sole vertex sits at z = 0.0.
    Also updates `head_center` location and `head_h` accordingly.
    """
    depsgraph = bpy.context.evaluated_depsgraph_get()
    crown_objs = {"head", "hair_crown", "bangs", "back_hair", "sidelock_L", "sidelock_R"}
    sole_objs = {"boot_L", "boot_R"}

    max_crown_z = None
    min_sole_z = None

    for obj in bpy.context.scene.objects:
        if obj.type != 'MESH':
            continue
        eval_obj = obj.evaluated_get(depsgraph)
        mesh = eval_obj.to_mesh()
        mw = eval_obj.matrix_world
        if obj.name in crown_objs:
            for v in mesh.vertices:
                wz = (mw @ v.co).z
                if max_crown_z is None or wz > max_crown_z:
                    max_crown_z = wz
        if obj.name in sole_objs:
            for v in mesh.vertices:
                wz = (mw @ v.co).z
                if min_sole_z is None or wz < min_sole_z:
                    min_sole_z = wz
        eval_obj.to_mesh_clear()

    if max_crown_z is None or min_sole_z is None:
        return

    current_span = max_crown_z - min_sole_z
    if current_span <= 1e-5:
        return

    scale_factor = 1.0 / current_span
    z_offset = -min_sole_z * scale_factor

    for obj in bpy.context.scene.objects:
        if obj.parent is None:
            obj.location.x *= scale_factor
            obj.location.y *= scale_factor
            obj.location.z = obj.location.z * scale_factor + z_offset
            obj.scale *= scale_factor

    hc = bpy.data.objects.get("head_center")
    if hc is not None:
        hc["head_h"] = float(P.H * scale_factor)
# ==============================================================================
# S1: HEAD, NECK, EARS, AND FACE FEATURES (REVISED FOR R2)
# ==============================================================================

def head_surface_point(P, x_norm, z_val):
    """
    Evaluates the exact outer front (-Y) surface of the evaluated `head` mesh
    at height `z_val` and normalized lateral position `x_norm` = x / half_width in [-1, 1].
    Accounts for Subsurf smoothing so conforming facial features sit cleanly
    on the exterior of the face without ever sinking inside or floating away.
    """
    H = P.H
    u = max(0.0, min(1.0, (z_val - P.z_chin) / H))

    # Half-width rx from chin (u=0) to crown (u=1)
    if u < 0.15:
        t = u / 0.15
        rx = H * (0.095 + 0.185 * (t ** 0.78))
    elif u < 0.44:
        t = (u - 0.15) / 0.29
        rx = H * (0.280 + 0.125 * math.sin(t * math.pi * 0.5))
    elif u < 0.74:
        t = (u - 0.44) / 0.30
        rx = H * (0.405 + 0.008 * math.sin(t * math.pi))
    else:
        t = (u - 0.74) / 0.26
        rx = H * 0.405 * math.cos(t * math.pi * 0.44)

    # Centerline front (-Y) profile
    if u < 0.12:
        t = u / 0.12
        y_front = -H * (0.305 + 0.062 * (t ** 0.75))
    elif u < 0.35:
        t = (u - 0.12) / 0.23
        y_front = -H * (0.367 + 0.018 * math.sin(t * math.pi * 0.5))
    elif u < 0.58:
        # Gentle anime eye-plane flatness
        t = (u - 0.35) / 0.23
        y_front = -H * (0.382 - 0.010 * math.sin(t * math.pi))
    elif u < 0.82:
        t = (u - 0.58) / 0.24
        y_front = -H * (0.380 - 0.042 * (t ** 1.25))
    else:
        t = (u - 0.82) / 0.18
        y_front = -H * (0.338 * math.cos(t * math.pi * 0.44))

    x_clamped = max(-0.98, min(0.98, x_norm))
    x = rx * x_clamped

    # Transverse curvature across the front of the face (matches head loop formula)
    # Using power 1.75 matches the Subsurf-evaluated front curvature of the head cage
    curve_back = H * 0.195 * (abs(x_clamped) ** 1.75)
    y = y_front + curve_back
    return Vector((x, y, z_val))


def build_head_and_neck(P, mats):
    """
    Builds the anime head (`head`), slender neck (`neck`), and ears (`ear_L`, `ear_R`).
    Includes an integrated, delicate anime nose ridge/tip on the head centerline
    plus a subtle shadow underside (`nose`), matching c6, c7, c8 and ref4/ref5.
    """
    H = P.H
    bm = bmesh.new()

    u_stations = [
        0.00, 0.04, 0.09, 0.15, 0.22, 0.27, 0.33,
        0.40, 0.48, 0.56, 0.65, 0.75, 0.85, 0.93, 1.00
    ]
    n_seg = 28
    loops = []

    for u in u_stations:
        z = P.z_chin + u * H
        if u <= 0.001:
            rx = 0.055 * H
            ry_f = 0.055 * H
            ry_b = 0.055 * H
            y_center = -0.275 * H
        elif u >= 0.999:
            rx = 0.065 * H
            ry_f = 0.065 * H
            ry_b = 0.065 * H
            y_center = 0.02 * H
        else:
            if u < 0.15:
                t = u / 0.15
                rx = H * (0.095 + 0.185 * (t ** 0.78))
            elif u < 0.44:
                t = (u - 0.15) / 0.29
                rx = H * (0.280 + 0.125 * math.sin(t * math.pi * 0.5))
            elif u < 0.74:
                t = (u - 0.44) / 0.30
                rx = H * (0.405 + 0.008 * math.sin(t * math.pi))
            else:
                t = (u - 0.74) / 0.26
                rx = H * 0.405 * math.cos(t * math.pi * 0.44)

            if u < 0.12:
                t = u / 0.12
                y_front = -H * (0.305 + 0.062 * (t ** 0.75))
            elif u < 0.35:
                t = (u - 0.12) / 0.23
                y_front = -H * (0.367 + 0.018 * math.sin(t * math.pi * 0.5))
            elif u < 0.58:
                t = (u - 0.35) / 0.23
                y_front = -H * (0.382 - 0.010 * math.sin(t * math.pi))
            elif u < 0.82:
                t = (u - 0.58) / 0.24
                y_front = -H * (0.380 - 0.042 * (t ** 1.25))
            else:
                t = (u - 0.82) / 0.18
                y_front = -H * (0.338 * math.cos(t * math.pi * 0.44))

            if u < 0.22:
                t = u / 0.22
                y_back = H * (-0.21 + 0.29 * (t ** 0.85))
            elif u < 0.65:
                t = u - 0.22
                y_back = H * (0.08 + 0.35 * math.sin((t / 0.43) * math.pi * 0.5))
            else:
                t = (u - 0.65) / 0.35
                y_back = H * 0.43 * math.cos(t * math.pi * 0.44)

            y_center = 0.5 * (y_front + y_back)
            ry_f = abs(y_front - y_center)
            ry_b = abs(y_back - y_center)

        ring = []
        for i in range(n_seg):
            theta = 2.0 * math.pi * i / n_seg
            ca = math.cos(theta)
            sa = math.sin(theta)

            if sa < 0.0:
                front_t = abs(sa)
                lat_x = rx * ca
                # Smooth anime face plane across the front (-Y)
                curve_back = H * 0.195 * (abs(ca) ** 1.75)
                lat_y = (y_center - ry_f) + curve_back * front_t + (ry_f * (1.0 - front_t))

                # Integrated delicate anime nose tip on the front centerline around u = 0.27 (z_nose)
                if abs(ca) < 0.18 and 0.20 <= u <= 0.36:
                    nose_u = 1.0 - abs(u - 0.275) / 0.085
                    nose_x = 1.0 - abs(ca) / 0.18
                    if nose_u > 0.0 and nose_x > 0.0:
                        lat_y -= H * 0.028 * (nose_u ** 1.4) * (nose_x ** 1.6)

                z_mod = z
                if 0.05 < u < 0.28 and abs(ca) > 0.48:
                    z_mod -= H * 0.014 * (1.0 - u / 0.28) * (abs(ca) - 0.48)
            else:
                lat_x = rx * ca
                lat_y = y_center + ry_b * (sa ** 0.92)
                z_mod = z

            ring.append(bm.verts.new((lat_x, lat_y, z_mod)))
        loops.append(ring)

    loft_loops(bm, loops, cap_start=True, cap_end=True, closed_loop=True)
    head_obj = new_mesh_obj("head", bm, mat=mats["skin"], shade_smooth=True)
    add_subsurf(head_obj, levels=2)

    # Neck
    bm_neck = bmesh.new()
    z_n0 = P.z_shoulder - 0.04 * H
    z_n1 = 0.5 * (P.z_shoulder + P.z_neck_top)
    z_n2 = P.z_neck_top + 0.10 * H
    y_neck = -0.05 * H
    neck_loops = [
        make_ellipse_ring(bm_neck, Vector((0.0, y_neck, z_n0)), 0.160 * H, 0.150 * H, n=16),
        make_ellipse_ring(bm_neck, Vector((0.0, y_neck, z_n1)), 0.138 * H, 0.132 * H, n=16),
        make_ellipse_ring(bm_neck, Vector((0.0, y_neck - 0.01 * H, z_n2)), 0.145 * H, 0.140 * H, n=16),
    ]
    loft_loops(bm_neck, neck_loops, cap_start=True, cap_end=True, closed_loop=True)
    neck_obj = new_mesh_obj("neck", bm_neck, mat=mats["skin"], shade_smooth=True)
    add_subsurf(neck_obj, levels=1)

    # Ears
    for side, suffix in ((1.0, "L"), (-1.0, "R")):
        bm_ear = bmesh.new()
        bmesh.ops.create_uvsphere(bm_ear, u_segments=10, v_segments=8, radius=1.0)
        for v in bm_ear.verts:
            v.co.x *= 0.050 * H
            v.co.y *= 0.070 * H
            v.co.z *= 0.105 * H
        rot_ear = Euler((0.12, -0.18 * side, 0.25 * side), 'XYZ').to_matrix()
        center_ear = Vector((side * 0.395 * H, -0.03 * H, P.z_chin + 0.39 * H))
        for v in bm_ear.verts:
            v.co = center_ear + (rot_ear @ v.co)
        ear_obj = new_mesh_obj(f"ear_{suffix}", bm_ear, mat=mats["skin"], shade_smooth=True)
        add_subsurf(ear_obj, levels=1)

    return head_obj


def make_conforming_patch(P, x_center_norm, z_center, half_w_norm, half_h, y_offset, n_ang=24):
    """
    Builds a crisp, multi-ring conforming elliptical patch proud of the head surface
    by `y_offset` in -Y so it is 100% visible outside the Subsurf head mesh.
    """
    bm = bmesh.new()
    radii = [0.25, 0.62, 1.00]
    c_pt = head_surface_point(P, x_center_norm, z_center)
    c_pt.y -= y_offset
    c_vert = bm.verts.new(c_pt)

    rings = []
    for r_fac in radii:
        ring = []
        for i in range(n_ang):
            ang = 2.0 * math.pi * i / n_ang
            xn = x_center_norm + math.cos(ang) * half_w_norm * r_fac
            zv = z_center + math.sin(ang) * half_h * r_fac
            pt = head_surface_point(P, xn, zv)
            pt.y -= y_offset
            ring.append(bm.verts.new(pt))
        rings.append(ring)

    for i in range(n_ang):
        bm.faces.new((c_vert, rings[0][i], rings[0][(i + 1) % n_ang]))
    loft_loops(bm, rings, cap_start=False, cap_end=False, closed_loop=True)
    return bm


def build_face_features(P, mats):
    """
    Constructs Koyuki's facial features to match c2, c6, c7, c8:
    - Positionedproud of the evaluated Subsurf head surface (`y_offset = 0.012 H .. 0.024 H`)
      with outward solidify (`offset = +1.0`) so no layer ever clips inside the head.
    - Large tare-me anime eyes (~0.23 H tall), set low on the face, 1 eye-width apart:
      - White sclera (`eye_white`)
      - Vibrant teal lower/main iris (`iris` #2C9696)
      - Deep teal upper iris + central pupil (`iris_dark` #1C4C54)
      - Thick dark-navy upper lash arch with tare-me outer flick (`lash` #20223E)
      - Bright white catchlight on upper-left of each iris (`catchlight` #FFFFFF)
    - Arched eyebrows (`brow` #6E3C3A) clearly visible between eyes and bangs
    - Subtle nose shadow accent (`nose` in `skin_shadow`) under the integrated nose tip
    - Small cute smile (`mouth` #8E2C4A)
    - Distinct horizontal pink blush ovals (`blush` #F4A0A0) directly beneath the eyes
    """
    H = P.H
    z_eye = P.z_eye
    eye_half_h = 0.115 * H     # Total eye height = 0.23 H
    eye_x_norm = 0.42          # Center of each eye in normalized face width
    eye_w_norm = 0.225         # Half-width in normalized face coordinates

    for side, suffix in ((1.0, "L"), (-1.0, "R")):
        xc = side * eye_x_norm

        # 1. Sclera (`eye_L/R` in `eye_white`)
        bm_sclera = bmesh.new()
        n_ang = 28
        radii = [0.28, 0.65, 1.0]
        c_pt = head_surface_point(P, xc, z_eye)
        c_pt.y -= 0.012 * H
        c_vert = bm_sclera.verts.new(c_pt)
        rings = []
        for rf in radii:
            ring = []
            for i in range(n_ang):
                ang = 2.0 * math.pi * i / n_ang
                ca = math.cos(ang)
                sa = math.sin(ang)
                # Rounded anime squircle eye shape + gentle tare-me outer corner droop
                sq = 1.0 + 0.16 * (ca * ca * sa * sa)
                outer_ness = ca * side
                droop_z = -0.014 * H * max(0.0, outer_ness) * rf
                xn = xc + ca * eye_w_norm * rf * sq
                zv = z_eye + sa * eye_half_h * rf * sq + droop_z
                pt = head_surface_point(P, xn, zv)
                pt.y -= (0.012 + 0.002 * (1.0 - rf * rf)) * H
                ring.append(bm_sclera.verts.new(pt))
            rings.append(ring)
        for i in range(n_ang):
            bm_sclera.faces.new((c_vert, rings[0][i], rings[0][(i + 1) % n_ang]))
        loft_loops(bm_sclera, rings, closed_loop=True)
        sclera_obj = new_mesh_obj(f"eye_{suffix}", bm_sclera, mat=mats["eye_white"], shade_smooth=True)
        add_solidify(sclera_obj, thickness=0.003 * H, offset=1.0)

        # 2. Main Teal Iris (`iris_L/R` in `iris` #2C9696)
        # Large anime iris filling ~82% of eye width and ~92% of eye height (c6, c7)
        iris_xc = xc - side * 0.012
        iris_w = eye_w_norm * 0.82
        iris_h = eye_half_h * 0.92
        bm_iris = bmesh.new()
        c_ir = head_surface_point(P, iris_xc, z_eye - 0.003 * H)
        c_ir.y -= 0.0165 * H
        cv_ir = bm_iris.verts.new(c_ir)
        ir_rings = []
        for rf in (0.30, 0.68, 1.0):
            ring = []
            for i in range(n_ang):
                ang = 2.0 * math.pi * i / n_ang
                ca = math.cos(ang)
                sa = math.sin(ang)
                sq = 1.0 + 0.14 * (ca * ca * sa * sa)
                xn = iris_xc + ca * iris_w * rf * sq
                zv = (z_eye - 0.003 * H) + sa * iris_h * rf * sq
                pt = head_surface_point(P, xn, zv)
                pt.y -= 0.0165 * H
                ring.append(bm_iris.verts.new(pt))
            ir_rings.append(ring)
        for i in range(n_ang):
            bm_iris.faces.new((cv_ir, ir_rings[0][i], ir_rings[0][(i + 1) % n_ang]))
        loft_loops(bm_iris, ir_rings, closed_loop=True)
        iris_obj = new_mesh_obj(f"iris_{suffix}", bm_iris, mat=mats["iris"], shade_smooth=True)
        add_solidify(iris_obj, thickness=0.0025 * H, offset=1.0)

        # 3. Upper Dark Teal Iris & Pupil (`iris_dark_L/R` in `iris_dark` #1C4C54)
        # Covers upper half of iris + central pupil core (leaving bright #2C9696 crescent below, c6/c7)
        bm_dark = bmesh.new()
        n_ang_d = 24
        c_d = head_surface_point(P, iris_xc, z_eye + 0.016 * H)
        c_d.y -= 0.020 * H
        cv_d = bm_dark.verts.new(c_d)
        d_rings = []
        for rf in (0.35, 0.72, 1.0):
            ring = []
            for i in range(n_ang_d):
                ang = 2.0 * math.pi * i / n_ang_d
                ca = math.cos(ang)
                sa = math.sin(ang)
                # Upper half follows top of iris; lower half dips in center to form pupil
                if sa >= 0.0:
                    zv_rel = 0.08 + 0.88 * sa
                else:
                    pupil_dip = 0.55 * (1.0 - 0.55 * (ca * ca))
                    zv_rel = 0.08 + pupil_dip * sa
                xn = iris_xc + ca * (iris_w * 0.96) * rf
                zv = z_eye + zv_rel * iris_h * rf
                pt = head_surface_point(P, xn, zv)
                pt.y -= 0.020 * H
                ring.append(bm_dark.verts.new(pt))
            d_rings.append(ring)
        for i in range(n_ang_d):
            bm_dark.faces.new((cv_d, d_rings[0][i], d_rings[0][(i + 1) % n_ang_d]))
        loft_loops(bm_dark, d_rings, closed_loop=True)
        dark_obj = new_mesh_obj(f"iris_dark_{suffix}", bm_dark, mat=mats["iris_dark"], shade_smooth=True)
        add_solidify(dark_obj, thickness=0.0025 * H, offset=1.0)

        # 4. Thick Upper Lash Line with Tare-Me Outer Flick (`lash_L/R` in `lash` #20223E)
        bm_lash = bmesh.new()
        n_u = 18
        lash_top = []
        lash_bot = []
        for i in range(n_u + 1):
            t = i / n_u  # 0 = inner corner, 1 = outer flick tip
            u_span = -1.02 + 2.22 * t
            xn = xc + side * u_span * eye_w_norm

            if u_span <= 0.88:
                arch = math.cos((u_span / 1.08) * math.pi * 0.46)
                z_base = z_eye + eye_half_h * (0.64 + 0.38 * arch)
                thick = H * (0.034 + 0.020 * math.sin(t * math.pi))
            else:
                over = (u_span - 0.88) / 0.32
                z_base = z_eye + eye_half_h * (0.74 - 0.18 * over)
                thick = H * 0.036 * (1.0 - 0.45 * over)

            pt_bot = head_surface_point(P, xn, z_base - 0.42 * thick)
            pt_top = head_surface_point(P, xn, z_base + 0.58 * thick)
            pt_bot.y -= 0.0235 * H
            pt_top.y -= 0.0245 * H
            lash_bot.append(bm_lash.verts.new(pt_bot))
            lash_top.append(bm_lash.verts.new(pt_top))

        loft_loops(bm_lash, [lash_bot, lash_top], closed_loop=False)
        lash_obj = new_mesh_obj(f"lash_{suffix}", bm_lash, mat=mats["lash"], shade_smooth=True)
        add_solidify(lash_obj, thickness=0.005 * H, offset=1.0)

        # 5. Bright White Catchlight (`catchlight_L/R` in `catchlight` #FFFFFF)
        # Upper-left of each iris in front view (c2, c6, c7)
        cl_xn = iris_xc - 0.062
        cl_z = z_eye + 0.036 * H
        bm_cl = make_conforming_patch(
            P, cl_xn, cl_z,
            0.058, 0.030 * H, y_offset=0.025 * H, n_ang=16
        )
        cl_obj = new_mesh_obj(f"catchlight_{suffix}", bm_cl, mat=mats["catchlight"], shade_smooth=True)
        add_solidify(cl_obj, thickness=0.002 * H, offset=1.0)

        # 6. Eyebrow (`brow_L/R` in `brow` #6E3C3A)
        # Sits just below the bang cut line at z_brow (~z_chin + 0.59 H)
        bm_brow = bmesh.new()
        b_top = []
        b_bot = []
        z_brow_pos = P.z_chin + 0.585 * H
        for i in range(9):
            t = i / 8.0
            u_b = -0.82 + 1.68 * t
            xn = xc + side * u_b * eye_w_norm
            arch = math.sin(t * math.pi) * 0.012 * H - 0.005 * H * t
            zb = z_brow_pos + arch
            thick = 0.022 * H * (1.0 - 0.25 * abs(2.0 * t - 1.0))
            p0 = head_surface_point(P, xn, zb - 0.5 * thick)
            p1 = head_surface_point(P, xn, zb + 0.5 * thick)
            p0.y -= 0.016 * H
            p1.y -= 0.016 * H
            b_bot.append(bm_brow.verts.new(p0))
            b_top.append(bm_brow.verts.new(p1))
        loft_loops(bm_brow, [b_bot, b_top], closed_loop=False)
        brow_obj = new_mesh_obj(f"brow_{suffix}", bm_brow, mat=mats["brow"], shade_smooth=True)
        add_solidify(brow_obj, thickness=0.003 * H, offset=1.0)

        # 7. Blush Ovals (`blush_L/R` in `blush` #F4A0A0)
        # Distinct horizontal pink ovals right below the outer lower eye rim (c2, c6, c7)
        blush_xn = xc + side * 0.035
        blush_z = z_eye - eye_half_h - 0.022 * H
        bm_blush = make_conforming_patch(
            P, blush_xn, blush_z,
            0.165, 0.025 * H, y_offset=0.013 * H, n_ang=20
        )
        blush_obj = new_mesh_obj(f"blush_{suffix}", bm_blush, mat=mats["blush"], shade_smooth=True)
        add_solidify(blush_obj, thickness=0.002 * H, offset=1.0)

    # 8. Delicate Nose Accent (`nose` in `skin_shadow` #EBA586)
    # Small subtle shadow dot/wedge right on the underside of the integrated nose tip (c6, c7)
    bm_nose = make_conforming_patch(
        P, 0.0, P.z_nose - 0.008 * H,
        0.032, 0.014 * H, y_offset=0.026 * H, n_ang=12
    )
    nose_obj = new_mesh_obj("nose", bm_nose, mat=mats["skin_shadow"], shade_smooth=True)
    add_solidify(nose_obj, thickness=0.002 * H, offset=1.0)

    # 9. Cute Small Smile Mouth (`mouth` in `mouth` #8E2C4A)
    bm_mouth = bmesh.new()
    m_bot = []
    m_top = []
    n_m = 10
    for i in range(n_m + 1):
        t = -1.0 + 2.0 * i / n_m
        xn = t * 0.155
        smile_curve = 0.024 * H * (t * t)
        zm = P.z_mouth + smile_curve
        thick = 0.019 * H * (1.0 - 0.30 * (t * t))
        p0 = head_surface_point(P, xn, zm - 0.5 * thick)
        p1 = head_surface_point(P, xn, zm + 0.5 * thick)
        p0.y -= 0.014 * H
        p1.y -= 0.014 * H
        m_bot.append(bm_mouth.verts.new(p0))
        m_top.append(bm_mouth.verts.new(p1))
    loft_loops(bm_mouth, [m_bot, m_top], closed_loop=False)
    mouth_obj = new_mesh_obj("mouth", bm_mouth, mat=mats["mouth"], shade_smooth=True)
    add_solidify(mouth_obj, thickness=0.003 * H, offset=1.0)
# ==============================================================================
# S2: HAIR (Crown Dome, 3-Panel Hime Bangs, Side Locks, Back Hair, Ponytail)
# ==============================================================================

def build_hair_crown_and_bangs(P, mats):
    """
    Rebuilt for R2 to fix the #1 critique:
    1. `hair_crown`: Covers ONLY the top dome, back of the skull, and sides behind the ears.
       Its front opening stays high (`z >= z_chin + 0.88 H`) so it NEVER descends over the
       forehead, eyebrows, or eyes!
    2. `bangs`: True 3-panel hime blunt fringe (c6, c7, c8) flowing smoothly from the front
       of `hair_crown` down over the forehead and terminating cleanly ABOVE the eyebrows
       (`z_cut = z_chin + 0.635 H`, well above `z_brow = z_chin + 0.585 H` and `z_eye = z_chin + 0.44 H`),
       with two crisp inverted-V notches (`|x| ~ 0.165 H`) that arch up to `z_chin + 0.74 H`.
    """
    H = P.H

    # --- 1. Hair Crown Cap (`hair_crown`) ---
    # Built as a smooth hemispherical-to-back cap covering the upper cranium and back of skull,
    # while arching high over the front forehead so the face & bangs are completely unobstructed.
    bm_crown = bmesh.new()
    u_vals = [0.28, 0.40, 0.54, 0.68, 0.80, 0.90, 0.99, 1.06, 1.11, 1.12]
    n_seg = 28
    loops = []

    for idx, u in enumerate(u_vals):
        z_base = P.z_chin + u * H
        t_norm = idx / (len(u_vals) - 1)
        if t_norm < 0.55:
            s = t_norm / 0.55
            rx = H * (0.445 + 0.045 * math.sin(s * math.pi * 0.65))
            ry_f = H * (0.375 + 0.045 * math.sin(s * math.pi * 0.65))
            ry_b = H * (0.455 + 0.050 * math.sin(s * math.pi * 0.65))
        else:
            s = (t_norm - 0.55) / 0.45
            cos_s = math.cos(s * math.pi * 0.48)
            rx = H * 0.490 * cos_s
            ry_f = H * 0.420 * cos_s
            ry_b = H * 0.505 * cos_s

        ring = []
        for i in range(n_seg):
            theta = 2.0 * math.pi * i / n_seg
            ca = math.cos(theta)
            sa = math.sin(theta)
            x = rx * ca
            y = (ry_b * sa) if sa >= 0.0 else (ry_f * sa)

            z_mod = z_base
            # Lift the entire front (-Y) half of the crown cap high above the forehead (`z >= z_chin + 0.88 H`)
            # so `hair_crown` only forms the top/back/side skull volume and never blocks the face!
            if sa < 0.15:
                front_weight = max(0.0, min(1.0, (0.15 - sa) / 1.15)) ** 1.15
                min_front_u = 0.28 + 0.62 * front_weight  # rises to u = 0.90 at front center (sa = -1)
                if u < min_front_u:
                    z_mod = P.z_chin + (min_front_u + 0.16 * (u / min_front_u)) * H
                    # Also tuck front-lower rings slightly inward so they sit neatly under the bangs root
                    y += 0.025 * H * front_weight * (1.0 - u / min_front_u)

            # Subtle center part groove at the very top of the crown
            if u > 0.96 and abs(ca) < 0.16:
                z_mod -= 0.010 * H * (1.0 - abs(ca) / 0.16)

            ring.append(bm_crown.verts.new((x, y, z_mod)))
        loops.append(ring)

    loft_loops(bm_crown, loops, cap_start=False, cap_end=True, closed_loop=True)
    crown_obj = new_mesh_obj("hair_crown", bm_crown, mat=mats["hair"], shade_smooth=True)
    add_solidify(crown_obj, thickness=0.020 * H, offset=-1.0)
    add_subsurf(crown_obj, levels=1)

    # --- 2. Continuous 3-Panel Hime Bangs (`bangs`) ---
    # Built as a single unified, sculpted hair shell from the top-front crown (`z_root`)
    # down to the blunt hime cut line (`z_cut = z_chin + 0.635 H`, safely above brows & eyes),
    # with two sharp inverted-V notches carved into the lower edge at `|x| ~ 0.165 H` (c6, c7)
    # and a proud forward curve in profile (c8).
    bm_bangs = bmesh.new()
    z_root = P.z_chin + 1.05 * H
    z_cut = P.z_chin + 0.635 * H  # Eyebrows are at 0.585 H, eyes top at 0.555 H -> 100% clear!

    # Explicit lateral stations across the bangs [-0.38 H .. +0.38 H] including exact notch centers
    u_stations = [
        -1.00, -0.88, -0.74, -0.60,
        -0.50, -0.43, -0.36,   # Right notch at u = -0.43 (x ~ -0.163 H)
        -0.24, -0.12,  0.00,  0.12,  0.24,
         0.36,  0.43,  0.50,   # Left notch at u = +0.43 (x ~ +0.163 H)
         0.60,  0.74,  0.88,  1.00
    ]
    nv = 10
    bang_loops = []
    half_span_x = 0.385 * H

    for iv in range(nv):
        v = iv / (nv - 1)  # 0 = top crown root, 1 = bottom blunt cut edge
        row = []
        for u in u_stations:
            abs_u = abs(u)

            # Width tapers slightly toward top crown root and stays full at the hime cut edge
            w_scale = 0.80 + 0.20 * (v ** 0.65)
            x = u * half_span_x * w_scale

            # Compute the two inverted-V notches around |u| = 0.43 (c6, c7)
            notch_dist = abs(abs_u - 0.43)
            notch_width = 0.075
            if notch_dist < notch_width:
                notch_t = 1.0 - (notch_dist / notch_width)
                # Inverted-V cutout rises by 0.115 H at the bottom edge (v=1)
                notch_lift = (notch_t ** 1.25) * 0.115 * H * (v ** 1.6)
            else:
                notch_lift = 0.0

            # Gentle convex curve on each of the 3 panels (center panel slightly lower in middle)
            if abs_u < 0.36:
                panel_curve = -0.012 * H * (1.0 - (abs_u / 0.36) ** 2) * v
            elif abs_u > 0.50:
                p_u = (abs_u - 0.75) / 0.25
                panel_curve = -0.008 * H * max(0.0, 1.0 - p_u * p_u) * v
            else:
                panel_curve = 0.0

            z_bot_local = z_cut + notch_lift + panel_curve
            # Smooth arch from crown root down to the cut edge
            z = z_root * (1.0 - v) + z_bot_local * v + 0.032 * H * math.sin(v * math.pi * 0.70)

            # Forward shell overhang in profile (c8: projects forward past forehead, then tucks slightly at tip)
            # Wrap back around the sides of the forehead toward the temples (abs_u -> 1)
            y_wrap = 0.145 * H * (abs_u ** 1.85)
            shell_out = math.sin(v * math.pi * 0.68) * 0.075 * H
            tip_tuck = max(0.0, (v - 0.75) / 0.25) ** 1.4 * 0.018 * H
            # Slight groove depth at the two notch lines so the 3 panels read as distinct sheets
            groove_in = 0.014 * H * max(0.0, 1.0 - notch_dist / 0.09) * math.sin(v * math.pi * 0.8)

            y = -0.355 * H - shell_out + tip_tuck + y_wrap + groove_in
            row.append(bm_bangs.verts.new((x, y, z)))
        bang_loops.append(row)

    loft_loops(bm_bangs, bang_loops, cap_start=False, cap_end=False, closed_loop=False)
    bangs_obj = new_mesh_obj("bangs", bm_bangs, mat=mats["hair"], shade_smooth=True)
    # Offset -1.0 thickens inward toward the forehead so the outer cut edge stays crisp at z_cut
    add_solidify(bangs_obj, thickness=0.034 * H, offset=-1.0)
    add_subsurf(bangs_obj, levels=1)

    return crown_obj, bangs_obj


def build_side_locks(P, mats):
    """
    Rebuilt for R2 to match the brief ("about 0.18 H wide") and c2/c6/c7/c8:
    - Each lock sits in front of the ear and frames the cheek from the outer edge of the bangs
      (`|x| ~ 0.31 H` to `0.49 H`, full width = `0.18 H` in front view!) down to the top of the scarf.
    - Oriented so its broad flat surface faces forward (`-Y`) and slightly outward (`±X`),
      with a crisp blunt horizontal cut at the bottom.
    """
    H = P.H
    z_top = P.z_chin + 0.82 * H
    z_bot = P.z_shoulder + 0.005 * H  # Rests cleanly on top of the collarbone/scarf

    for side, suffix in ((1.0, "L"), (-1.0, "R")):
        bm = bmesh.new()
        nv = 14
        nu = 7
        loops = []

        for iv in range(nv):
            v = iv / (nv - 1)  # 0 = temple root under bangs/crown, 1 = blunt bottom cut
            z = z_top * (1.0 - v) + z_bot * v

            # Inner edge X ~ 0.315 H (frames outer cheek without touching eye),
            # Outer edge X ~ 0.495 H -> width = 0.180 H in front view!
            x_inner = 0.315 * H + 0.008 * H * v
            x_outer = 0.495 * H + 0.005 * H * math.sin(v * math.pi * 0.7)
            if v > 0.92:
                # Tiny bevel at bottom blunt cut so Subsurf keeps a square hime tip
                t_tip = (v - 0.92) / 0.08
                x_inner += 0.006 * H * t_tip
                x_outer -= 0.006 * H * t_tip

            row = []
            for iu in range(nu):
                u = iu / (nu - 1)  # 0 = inner cheek-side edge, 1 = outer silhouette edge
                px = side * (x_inner * (1.0 - u) + x_outer * u)

                # Y wraps gently from front-cheek plane (-0.285 H at inner edge) back toward ear (-0.175 H at outer edge)
                y_inner = -0.285 * H - 0.015 * H * math.sin(v * math.pi * 0.6)
                y_outer = -0.175 * H - 0.010 * H * math.sin(v * math.pi * 0.6)
                camber = -0.014 * H * math.sin(u * math.pi)
                py = y_inner * (1.0 - u) + y_outer * u + camber

                row.append(bm.verts.new((px, py, z)))
            loops.append(row)

        loft_loops(bm, loops, closed_loop=False)
        obj = new_mesh_obj(f"sidelock_{suffix}", bm, mat=mats["hair"], shade_smooth=True)
        add_solidify(obj, thickness=0.042 * H, offset=0.0)
        add_subsurf(obj, levels=1)


def build_back_hair(P, mats):
    """
    Builds `back_hair` and `back_hair_inner`:
    - Flows smoothly from `hair_crown` down behind the shoulders (`y > +0.08 H`),
      staying strictly behind the sleeves and scarf in front and 3/4 views (c1, c2, c3, c5).
    - Features clean vertical sheet flutes and a subtle V-cut blunt hem at `P.z_back_hair_tip`.
    """
    H = P.H
    bm = bmesh.new()

    z_top = P.z_crown + 0.02 * H
    z_bot = P.z_back_hair_tip
    nv = 16
    nu = 15
    loops = []

    for iv in range(nv):
        v = iv / (nv - 1)
        row = []
        for iu in range(nu):
            u = -1.0 + 2.0 * iu / (nu - 1)
            abs_u = abs(u)

            # Gentle V-cut at the bottom hem (c5)
            v_drop = 0.045 * H * (1.0 - abs_u ** 1.5)
            z_end = z_bot - v_drop
            z = z_top * (1.0 - v) + z_end * v

            # Width envelope: frames behind the head/neck and stays narrower than the outer sleeves
            if v < 0.25:
                t = v / 0.25
                half_w = H * (0.45 + 0.04 * math.sin(t * math.pi * 0.5))
            else:
                t = (v - 0.25) / 0.75
                half_w = H * (0.49 + 0.02 * math.sin(t * math.pi * 0.6) - 0.03 * (t ** 1.6))

            x = u * half_w

            if v < 0.28:
                wrap_depth = H * (0.35 * (1.0 - 0.82 * (abs_u ** 1.6)))
                y_base = 0.10 * H + wrap_depth
            else:
                t = (v - 0.28) / 0.72
                curve_back = H * (0.28 + 0.055 * math.sin(t * math.pi * 0.8))
                edge_cup = H * 0.15 * (abs_u ** 1.7)
                sheet_wave = 0.010 * H * math.cos(u * math.pi * 3.0) * math.sin(v * math.pi)
                y_base = curve_back - edge_cup + sheet_wave

            row.append(bm.verts.new((x, y_base, z)))
        loops.append(row)

    loft_loops(bm, loops, closed_loop=False)
    back_obj = new_mesh_obj("back_hair", bm, mat=mats["hair"], shade_smooth=True)
    add_solidify(back_obj, thickness=0.045 * H, offset=-1.0)
    add_subsurf(back_obj, levels=1)

    # Inner dark-brown shadow curtain (`back_hair_inner` in `hair_shadow` #6E3C3A)
    # Visible behind the neck and side locks in front, 3/4, and side views (c2, c3, c6, c10)
    bm_in = bmesh.new()
    in_loops = []
    for iv in range(10):
        v = iv / 9.0
        z = (z_top - 0.08 * H) * (1.0 - v) + (z_bot + 0.04 * H) * v
        half_w = H * (0.44 - 0.03 * v)
        row = []
        for iu in range(9):
            u = -1.0 + 2.0 * iu / 8.0
            x = u * half_w
            y = H * (0.16 + 0.06 * v - 0.12 * (abs(u) ** 1.5))
            row.append(bm_in.verts.new((x, y, z)))
        in_loops.append(row)
    loft_loops(bm_in, in_loops, closed_loop=False)
    in_obj = new_mesh_obj("back_hair_inner", bm_in, mat=mats["hair_shadow"], shade_smooth=True)
    add_solidify(in_obj, thickness=0.025 * H, offset=-1.0)
    add_subsurf(in_obj, levels=1)

    return back_obj


def build_ponytail(P, mats):
    """
    Rebuilt for R2 to match c3, c4, c5, c8, c9:
    - Gathers high at the back of the crown under the bow knot (`z_root = z_chin + 0.72 H`).
    - Arches backward in a fuller S-curve (`~0.50 H` wide/thick in upper-mid section) and stays
      voluminous through its lower half before tapering to a single crisp point at `P.z_ponytail_tip` (c5).
    """
    H = P.H
    bm = bmesh.new()

    z_root = P.z_chin + 0.73 * H
    z_tip = P.z_ponytail_tip
    y_root = 0.44 * H

    n_rings = 18
    n_seg = 24
    loops = []

    for ir in range(n_rings):
        t = ir / (n_rings - 1)  # 0 = root under bow knot, 1 = bottom pointed tip

        # S-curve trajectory: emerges high behind the bow and drapes proudly over the back hair
        z = z_root * (1.0 - t) + z_tip * t + 0.045 * H * math.sin(t * math.pi * 0.60) * (1.0 - t)
        s_arch = math.sin(t * math.pi * 0.68) * 0.175 * H
        yc = y_root + s_arch

        # Fuller radius envelope: swells to ~0.245 H radius (~0.49 H thick), holds fuller volume down to t=0.68,
        # then tapers cleanly to a sharp V-point at the waist (matching c4 side & c5 back views)
        if t < 0.25:
            s = t / 0.25
            rad = H * (0.095 + 0.150 * math.sin(s * math.pi * 0.5))
        elif t < 0.65:
            s = (t - 0.25) / 0.40
            rad = H * (0.245 - 0.035 * (s ** 1.2))
        else:
            s = (t - 0.65) / 0.35
            rad = H * 0.210 * ((1.0 - s) ** 1.15)
        rad = max(0.005 * H, rad)

        tilt = 0.28 * (1.0 - 1.8 * t)
        rot = Euler((tilt, 0.0, 0.0), 'XYZ').to_matrix()

        ring = []
        for i in range(n_seg):
            theta = 2.0 * math.pi * i / n_seg
            # Layered clump flutes around circumference
            clump_flute = 1.0 + 0.11 * math.cos(5.0 * theta + 0.4 * t) * math.sin(t * math.pi)
            rx = rad * 1.02 * clump_flute
            ry = rad * 0.86 * clump_flute
            local = Vector((rx * math.cos(theta), ry * math.sin(theta), 0.0))
            pt = Vector((0.0, yc, z)) + (rot @ local)
            ring.append(bm.verts.new(pt))
        loops.append(ring)

    loft_loops(bm, loops, cap_start=True, cap_end=True, closed_loop=True)
    pt_obj = new_mesh_obj("ponytail", bm, mat=mats["hair"], shade_smooth=True)
    add_subsurf(pt_obj, levels=1)
    return pt_obj
# ==============================================================================
# S3: SIGNATURE TEAL BOW (REVISED FOR R2)
# ==============================================================================

def build_bow(P, mats):
    """
    Rebuilt for R2 to match c1, c2, c5, c6, c7, c8, c9, c10:
    - `bow_knot`: Crisp vertical rectangular ribbon knot (`teal` with `teal_dark` side/inner wrap)
      positioned cleanly proud of `hair_crown` at the back (`y_knot = 0.485 H`) so it is 100%
      unobstructed in back and side views (c8, c9).
    - `bow_loop_L`, `bow_loop_R`: Broad, puffy flared triangular-teardrop ribbon wings spanning
      ~2.0x head width (`|x| = 0.82 H`, total span = `1.64 H`), pinched tightly into the knot
      and flaring vertically toward the outer wing tips (c7, c9).
    - `bow_hollow_L`, `bow_hollow_R`: Bold `teal_dark` (#1C4C54) inner loop hollows + center fold
      crease clearly visible on the front face (`c7`), 3/4 view (`c6`), side view (`c8`), and back view (`c9`).
    - `bow_tail_L`, `bow_tail_R`: Two long swallowtail (V-notched) ribbon tails draping down
      over the back hair on either side of the ponytail (`c5`, `c9`).
    """
    H = P.H
    z_knot = P.z_chin + 0.78 * H
    y_knot = 0.485 * H  # Proud of `hair_crown` back surface (~0.45 H) so knot never clips into hair

    # --- 1. Center Pinched Ribbon Knot (`bow_knot`) ---
    bm_knot = bmesh.new()
    knot_w = 0.088 * H
    knot_d = 0.075 * H
    knot_h = 0.125 * H
    n_seg = 16
    knot_loops = []
    for v in (-1.0, -0.6, 0.0, 0.6, 1.0):
        z = z_knot + v * knot_h
        bulge = 1.0 + 0.12 * (1.0 - v * v)
        if abs(v) > 0.85:
            bulge *= 0.86
        rx = knot_w * bulge
        ry = knot_d * bulge
        ring = []
        for i in range(n_seg):
            theta = 2.0 * math.pi * i / n_seg
            ca = math.cos(theta)
            sa = math.sin(theta)
            sq = 1.0 + 0.22 * (ca * ca * sa * sa)
            x = rx * ca * sq
            y = y_knot + ry * sa * sq
            ring.append(bm_knot.verts.new((x, y, z)))
        knot_loops.append(ring)

    loft_loops(bm_knot, knot_loops, cap_start=True, cap_end=True, closed_loop=True)
    knot_obj = new_mesh_obj("bow_knot", bm_knot, mat=mats["teal"], shade_smooth=True)
    add_subsurf(knot_obj, levels=1)

    # --- 2. Broad Flared Teardrop Ribbon Loops (`bow_loop_L/R`) ---
    for side, suffix in ((1.0, "L"), (-1.0, "R")):
        bm_loop = bmesh.new()
        n_stations = 15
        n_ring = 24
        loop_rings = []

        for ist in range(n_stations):
            u = ist / (n_stations - 1)  # 0 = pinched knot root, 1 = outer flared wing tip

            # Horizontal reach out to |x| = 0.82 H (total span = 1.64 H = 2.0x head width)
            x = side * H * (0.055 + 0.765 * (u ** 0.92))

            # Centerline rises gently toward the outer wing tip and angles slightly forward
            # so the bow sits behind the head and frames it cleanly in front, 3/4, and side views
            z_center = z_knot + H * (0.065 * (u ** 0.85) - 0.015 * (u ** 3))
            y_center = y_knot - H * (0.145 * (u ** 0.82))

            # Vertical height flares like a classic anime ribbon bow (c7, c9):
            # narrow waist at knot (u=0), flaring tall at u=0.86, then rounding off at the outer rim
            if u < 0.86:
                s = u / 0.86
                half_h = H * (0.055 + 0.195 * (s ** 0.80))
            else:
                s = (u - 0.86) / 0.14
                half_h = H * 0.250 * math.cos(s * math.pi * 0.46)

            # Front-to-back depth of the puffy loop
            if u < 0.86:
                s = u / 0.86
                half_d = H * (0.045 + 0.105 * math.sin(s * math.pi * 0.65))
            else:
                s = (u - 0.86) / 0.14
                half_d = H * 0.135 * math.cos(s * math.pi * 0.46)

            # Central horizontal crease pinch on front, back, and outer side
            crease_env = math.sin(min(1.0, u / 0.92) * math.pi) ** 0.9

            ring = []
            for i in range(n_ring):
                theta = 2.0 * math.pi * i / n_ring
                ca = math.cos(theta)  # -1 = front (-Y), +1 = back (+Y)
                sa = math.sin(theta)  # +1 = top (+Z), -1 = bottom (-Z)

                # Pinch the waist at the horizontal midline (sa ~ 0) to form top & bottom puffy lobes
                mid_pinch = 1.0 - 0.36 * crease_env * ((1.0 - sa * sa) ** 1.5)
                # Slightly square off the outer top and bottom corners of the wing (c7, c9)
                corner_boost = 1.0 + 0.16 * (sa * sa) * (u ** 0.7)

                dy = ca * half_d * mid_pinch
                dz = sa * half_h * corner_boost

                px = x
                py = y_center + dy
                pz = z_center + dz
                ring.append(bm_loop.verts.new((px, py, pz)))
            loop_rings.append(ring)

        loft_loops(bm_loop, loop_rings, cap_start=True, cap_end=True, closed_loop=True)
        loop_obj = new_mesh_obj(f"bow_loop_{suffix}", bm_loop, mat=mats["teal"], shade_smooth=True)
        add_subsurf(loop_obj, levels=1)

        # --- 3. Deep Teal-Dark Inner Hollow & Crease (`bow_hollow_L/R` in `teal_dark`) ---
        # Explicitly protrudes slightly through the front, back, and outer side midline of the loop
        # so the dark inner ribbon shadow & hollow opening read in front (c7), 3/4 (c6), side (c8), and back (c9)!
        bm_hol = bmesh.new()
        hol_rings = []
        n_hst = 10
        for ist in range(n_hst):
            t_h = ist / (n_hst - 1)
            u = 0.14 + 0.82 * t_h  # spans from near knot out to u = 0.96 (outer hollow opening)

            x = side * H * (0.055 + 0.765 * (u ** 0.92))
            z_center = z_knot + H * (0.065 * (u ** 0.85) - 0.015 * (u ** 3))
            y_center = y_knot - H * (0.145 * (u ** 0.82))

            if u < 0.86:
                s = u / 0.86
                loop_d = H * (0.045 + 0.105 * math.sin(s * math.pi * 0.65))
            else:
                s = (u - 0.86) / 0.14
                loop_d = H * 0.135 * math.cos(s * math.pi * 0.46)

            # Vertical height of dark crease/hollow flares toward the outer wing (matching c7 & c9)
            env = math.sin(t_h * math.pi) ** 0.55
            if t_h > 0.88:
                env *= math.cos(((t_h - 0.88) / 0.12) * math.pi * 0.45)

            hz = H * (0.018 + 0.068 * (t_h ** 0.85)) * env
            # Depth exceeds the pinched midline of `bow_loop` so the dark crease is visible on both front & back!
            hy = loop_d * 0.82 * (0.70 + 0.30 * env)

            ring = []
            for i in range(16):
                theta = 2.0 * math.pi * i / 16
                ca = math.cos(theta)
                sa = math.sin(theta)
                sq = 1.0 + 0.20 * (ca * ca * sa * sa)
                px = x + side * (0.012 * H * t_h)
                py = y_center + ca * hy * sq
                pz = z_center + sa * hz * sq
                ring.append(bm_hol.verts.new((px, py, pz)))
            hol_rings.append(ring)

        loft_loops(bm_hol, hol_rings, cap_start=True, cap_end=True, closed_loop=True)
        hol_obj = new_mesh_obj(f"bow_hollow_{suffix}", bm_hol, mat=mats["teal_dark"], shade_smooth=True)
        add_subsurf(hol_obj, levels=1)

        # --- 4. Swallowtail Ribbon Tails (`bow_tail_L/R`) ---
        # Emerge from under the knot and drape down over the upper back hair on either side of the ponytail,
        # also visible peeking behind the neck/hair in 3/4 and side views (c3, c4, c5, c6, c8, c9).
        bm_tail = bmesh.new()
        z_t_top = z_knot - 0.04 * H
        z_t_bot = P.z_shoulder - 0.28 * H
        if P.build == "sprite":
            z_t_bot = P.z_shoulder - 0.18 * H

        nv_t = 12
        nu_t = 7
        t_grid = []

        for iv in range(nv_t):
            v = iv / (nv_t - 1)
            row = []
            xc = side * H * (0.085 + 0.165 * (v ** 0.85))
            yc = y_knot + H * (0.025 + 0.055 * math.sin(v * math.pi * 0.70) - 0.025 * v)
            half_w = H * (0.056 + 0.026 * v)

            for iu in range(nu_t):
                u = -1.0 + 2.0 * iu / (nu_t - 1)
                # Crisp swallowtail V-notch at the bottom end (c5)
                v_notch = (1.0 - abs(u)) * 0.075 * H * (v ** 2.2)
                z = z_t_top * (1.0 - v) + z_t_bot * v + v_notch

                px = xc + side * u * half_w * 0.86
                py = yc - abs(u) * 0.012 * H + side * u * half_w * 0.35
                row.append(bm_tail.verts.new((px, py, z)))
            t_grid.append(row)

        loft_loops(bm_tail, t_grid, closed_loop=False)
        tail_obj = new_mesh_obj(f"bow_tail_{suffix}", bm_tail, mat=mats["teal"], shade_smooth=False)
        add_solidify(tail_obj, thickness=0.024 * H, offset=0.0)
        add_subsurf(tail_obj, levels=1)
# ==============================================================================
# S4: TORSO, COAT, BELT, BUTTONS, AND CHUNKY KNIT SCARF (REVISED FOR R2)
# ==============================================================================

def coat_profile_at(P, u):
    """
    Returns (z, rx, ry_front, ry_back, pleat_amp) for the coat exterior at normalized
    vertical coordinate u in [0, 1] from bottom hem (u=0) to top collar/shoulder (u=1).
    """
    H = P.H
    z_top = P.z_shoulder + 0.03 * H
    z_bot = P.z_hem
    z = z_bot + u * (z_top - z_bot)

    u_belt = (P.z_belt - z_bot) / (z_top - z_bot)
    u_bust = (P.z_bust - z_bot) / (z_top - z_bot)

    if u <= u_belt:
        s = u / max(1e-4, u_belt)  # 0 at hem, 1 at belt
        flare = (1.0 - s) ** 0.90
        rx = 0.5 * (P.waist_w + (P.hem_w - P.waist_w) * flare)
        ry_f = H * (0.235 + 0.245 * flare)
        ry_b = H * (0.225 + 0.245 * flare)
        pleat_amp = H * 0.020 * ((1.0 - s) ** 1.1)
    elif u <= u_bust:
        s = (u - u_belt) / max(1e-4, (u_bust - u_belt))
        smooth_s = math.sin(s * math.pi * 0.5)
        rx = 0.5 * (P.waist_w + (P.bust_w - P.waist_w) * smooth_s)
        ry_f = H * (0.235 + 0.060 * smooth_s)
        ry_b = H * (0.225 + 0.025 * smooth_s)
        pleat_amp = 0.0
    else:
        s = (u - u_bust) / max(1e-4, (1.0 - u_bust))
        rx = 0.5 * (P.bust_w * (1.0 - 0.34 * (s ** 1.4)))
        ry_f = H * (0.295 * (1.0 - 0.36 * (s ** 1.3)))
        ry_b = H * (0.250 * (1.0 - 0.32 * (s ** 1.3)))
        pleat_amp = 0.0

    return z, rx, ry_f, ry_b, pleat_amp


def build_coat_and_details(P, mats):
    """
    Rebuilt for R2:
    - `coat`: Fitted cream bodice + flared A-line pleated skirt.
    - `coat_trim`: Rust-brown bottom hem trim band.
    - `coat_inside`: Darker inner underside closing the bottom of the skirt.
    - `belt` & `buckle`: Dark-brown waist belt with a centered gold rectangular buckle.
    - `buttons`: 6 gold buttons embedded directly into the evaluated front centerline of `coat`
      (fixes the R1 side-view floating buttons bug!).
    """
    H = P.H
    z_top = P.z_shoulder + 0.03 * H
    z_bot = P.z_hem
    u_belt = (P.z_belt - z_bot) / (z_top - z_bot)

    # --- 1. Main Cream Coat Body (`coat`) ---
    bm_coat = bmesh.new()
    u_stations = [
        0.00, 0.05, 0.12, 0.22, 0.33, 0.44,
        u_belt - 0.03, u_belt, u_belt + 0.03,
        0.64, 0.76, 0.88, 0.96, 1.00
    ]
    u_stations = sorted(list(set([max(0.0, min(1.0, round(val, 4))) for val in u_stations])))
    n_seg = 32
    coat_loops = []

    for u in u_stations:
        z, rx, ry_f, ry_b, pleat_amp = coat_profile_at(P, u)
        ring = []
        for i in range(n_seg):
            theta = 2.0 * math.pi * i / n_seg
            ca = math.cos(theta)
            sa = math.sin(theta)
            # Use -cos(6*theta) so the front centerline (theta = -pi/2, 6*theta = -3*pi)
            # has cos(6*theta) = -1, and pleat at front centerline is 0 rather than sticking out
            pleat = pleat_amp * math.sin(6.0 * theta)
            r_x = rx + pleat * 0.65
            r_y = (ry_b if sa >= 0.0 else ry_f) + pleat * 0.80

            x = r_x * ca
            y = r_y * sa - 0.02 * H
            z_hem_curve = -0.016 * H * (1.0 - u) * (sa * sa)
            ring.append(bm_coat.verts.new((x, y, z + z_hem_curve)))
        coat_loops.append(ring)

    loft_loops(bm_coat, coat_loops, cap_start=False, cap_end=True, closed_loop=True)
    coat_obj = new_mesh_obj("coat", bm_coat, mat=mats["coat"], shade_smooth=True)
    add_subsurf(coat_obj, levels=2)

    # --- 2. Coat Underside Cap (`coat_inside`) ---
    bm_in = bmesh.new()
    _, rx0, ry_f0, ry_b0, pleat0 = coat_profile_at(P, 0.02)
    in_rings = []
    for rf in (0.35, 0.70, 0.95):
        ring = []
        for i in range(n_seg):
            theta = 2.0 * math.pi * i / n_seg
            ca = math.cos(theta)
            sa = math.sin(theta)
            pleat = pleat0 * math.sin(6.0 * theta) * rf
            x = (rx0 * rf + pleat * 0.5) * ca
            y = ((ry_b0 if sa >= 0.0 else ry_f0) * rf + pleat * 0.7) * sa - 0.02 * H
            z = z_bot + 0.025 * H + (1.0 - rf) * 0.06 * H
            ring.append(bm_in.verts.new((x, y, z)))
        in_rings.append(ring)
    c_in = bm_in.verts.new((0.0, -0.02 * H, z_bot + 0.09 * H))
    for i in range(n_seg):
        bm_in.faces.new((c_in, in_rings[0][(i + 1) % n_seg], in_rings[0][i]))
    loft_loops(bm_in, in_rings, closed_loop=True)
    in_obj = new_mesh_obj("coat_inside", bm_in, mat=mats["coat_shadow"], shade_smooth=True)
    add_subsurf(in_obj, levels=1)

    # --- 3. Rust-Brown Hem Trim Band (`coat_trim`) ---
    bm_trim = bmesh.new()
    trim_u_vals = [0.0, 0.028, 0.058]
    trim_loops = []
    for u in trim_u_vals:
        z, rx, ry_f, ry_b, pleat_amp = coat_profile_at(P, u)
        ring = []
        for i in range(n_seg):
            theta = 2.0 * math.pi * i / n_seg
            ca = math.cos(theta)
            sa = math.sin(theta)
            pleat = pleat_amp * math.sin(6.0 * theta)
            r_x = rx + pleat * 0.65 + 0.005 * H
            r_y = (ry_b if sa >= 0.0 else ry_f) + pleat * 0.80 + 0.005 * H
            x = r_x * ca
            y = r_y * sa - 0.02 * H
            z_hem_curve = -0.016 * H * (1.0 - u) * (sa * sa)
            ring.append(bm_trim.verts.new((x, y, z + z_hem_curve - 0.006 * H)))
        trim_loops.append(ring)
    loft_loops(bm_trim, trim_loops, cap_start=False, cap_end=False, closed_loop=True)
    trim_obj = new_mesh_obj("coat_trim", bm_trim, mat=mats["rust"], shade_smooth=True)
    add_solidify(trim_obj, thickness=0.015 * H, offset=0.5)
    add_subsurf(trim_obj, levels=1)

    # --- 4. Dark-Brown Waist Belt (`belt`) + Gold Buckle (`buckle`) ---
    bm_belt = bmesh.new()
    _, rx_b, ry_fb, ry_bb, _ = coat_profile_at(P, u_belt)
    belt_half_h = 0.036 * H
    belt_loops = []
    for dz in (-belt_half_h, 0.0, belt_half_h):
        ring = []
        for i in range(n_seg):
            theta = 2.0 * math.pi * i / n_seg
            ca = math.cos(theta)
            sa = math.sin(theta)
            x = (rx_b + 0.008 * H) * ca
            y = ((ry_bb if sa >= 0.0 else ry_fb) + 0.008 * H) * sa - 0.02 * H
            ring.append(bm_belt.verts.new((x, y, P.z_belt + dz)))
        belt_loops.append(ring)
    loft_loops(bm_belt, belt_loops, closed_loop=True)
    belt_obj = new_mesh_obj("belt", bm_belt, mat=mats["belt"], shade_smooth=True)
    add_solidify(belt_obj, thickness=0.014 * H, offset=1.0)
    add_subsurf(belt_obj, levels=1)

    # Gold Buckle centered on front (-Y) of belt
    bm_buckle = bmesh.new()
    bw = 0.056 * H
    bh = 0.048 * H
    bd = 0.020 * H
    y_buck = -(ry_fb + 0.018 * H) - 0.02 * H
    bmesh.ops.create_cube(bm_buckle, size=1.0)
    for v in bm_buckle.verts:
        v.co.x *= 2.0 * bw
        v.co.y = y_buck + v.co.y * bd
        v.co.z = P.z_belt + v.co.z * (2.0 * bh)
    buckle_obj = new_mesh_obj("buckle", bm_buckle, mat=mats["gold"], shade_smooth=False)
    add_subsurf(buckle_obj, levels=1)

    # --- 5. Six Small Gold Buttons (`buttons`) ---
    # Placed flush with the Subsurf-evaluated front surface of `coat` so they never float in side view!
    z_scarf_bot = P.z_shoulder - 0.09 * H
    above_span = z_scarf_bot - (P.z_belt + belt_half_h)
    below_span = (P.z_belt - belt_half_h) - (P.z_hem + 0.06 * H)

    btn_z_list = [
        P.z_belt + belt_half_h + above_span * 0.22,
        P.z_belt + belt_half_h + above_span * 0.52,
        P.z_belt + belt_half_h + above_span * 0.80,
        P.z_belt - belt_half_h - below_span * 0.22,
        P.z_belt - belt_half_h - below_span * 0.52,
        P.z_belt - belt_half_h - below_span * 0.80,
    ]

    bm_btns = bmesh.new()
    btn_r = 0.024 * H
    for zb in btn_z_list:
        u_b = max(0.0, min(1.0, (zb - z_bot) / (z_top - z_bot)))
        _, _, ry_f_btn, _, _ = coat_profile_at(P, u_b)
        # Subsurf shrinks the 32-gon radial distance by ~0.985; embed the button center slightly inside
        # the coat surface so only its front cap protrudes cleanly by ~0.006 H
        y_surf = -(ry_f_btn * 0.982) - 0.02 * H
        ret = bmesh.ops.create_uvsphere(bm_btns, u_segments=10, v_segments=8, radius=1.0)
        for v in ret["verts"]:
            v.co.x = v.co.x * btn_r
            v.co.y = y_surf + v.co.y * (0.45 * btn_r) - 0.002 * H
            v.co.z = zb + v.co.z * btn_r
    btns_obj = new_mesh_obj("buttons", bm_btns, mat=mats["gold"], shade_smooth=True)

    return coat_obj


def build_scarf(P, mats):
    """
    Rebuilt for R2 to eliminate the floating `scarf_ribs` fragments in 3/4 and side views:
    - `scarf`: Chunky double-wrapped teal knit collar around the neck (`~0.30 H` thick).
    - `scarf_ribs`: Clean conformal `teal_dark` (#1C4C54) horizontal seam & vertical knit rib bands
      that hug the exact contour of the scarf tiers without ever sticking out past the scarf bbox!
    - `scarf_tail`: Single hanging tail on **HER LEFT (+X, viewer's right in front view)** reaching the belt.
    - `scarf_tail_ribs`: Flush `teal_dark` horizontal knit stripes across the hanging tail.
    - `scarf_fringe`: Light-teal (`teal_light` #6ACBB6) tassel fringe along the bottom edge of the tail.
    """
    H = P.H
    z_wrap_bot = P.z_shoulder - 0.07 * H
    z_wrap_top = P.z_chin + 0.04 * H
    if z_wrap_top - z_wrap_bot < 0.28 * H:
        z_wrap_bot = z_wrap_top - 0.29 * H
    z_wrap_mid = 0.5 * (z_wrap_bot + z_wrap_top)

    # --- 1. Two-Tier Bulky Neck Wrap (`scarf`) ---
    bm_scarf = bmesh.new()
    n_seg = 32

    tiers_spec = [
        (z_wrap_bot, z_wrap_mid + 0.006 * H, 1.03, 1.03),  # Lower wrap tier
        (z_wrap_mid - 0.004 * H, z_wrap_top, 0.98, 0.98),  # Upper wrap tier
    ]

    for tier_z0, tier_z1, rx_mul, ry_mul in tiers_spec:
        tier_loops = []
        v_steps = [0.0, 0.18, 0.50, 0.82, 1.0]
        for v in v_steps:
            z = tier_z0 + v * (tier_z1 - tier_z0)
            profile = math.sin(v * math.pi)
            rx = H * (0.32 + 0.140 * (profile ** 0.55)) * rx_mul
            ry_f = H * (0.24 + 0.120 * (profile ** 0.55)) * ry_mul
            ry_b = H * (0.22 + 0.110 * (profile ** 0.55)) * ry_mul

            ring = []
            for i in range(n_seg):
                theta = 2.0 * math.pi * i / n_seg
                ca = math.cos(theta)
                sa = math.sin(theta)
                x = rx * ca
                y = (ry_b if sa >= 0.0 else ry_f) * sa - 0.03 * H
                ring.append(bm_scarf.verts.new((x, y, z)))
            tier_loops.append(ring)
        loft_loops(bm_scarf, tier_loops, cap_start=True, cap_end=True, closed_loop=True)

    scarf_obj = new_mesh_obj("scarf", bm_scarf, mat=mats["teal"], shade_smooth=True)
    add_subsurf(scarf_obj, levels=1)

    # --- 2. Conformal Knit Rib Grooves & Mid-Seam (`scarf_ribs` in `teal_dark`) ---
    # Each vertical rib is a curvedconforming strap following the exact `profile` curve of its tier
    # from `v = 0.15` to `v = 0.85`, so it NEVER pokes out at top/bottom or floats in side view!
    bm_ribs = bmesh.new()

    # Horizontal seam ring nestled in the valley between the two wraps
    seam_loops = []
    for dz in (-0.012 * H, 0.012 * H):
        ring = []
        for i in range(n_seg):
            theta = 2.0 * math.pi * i / n_seg
            ca = math.cos(theta)
            sa = math.sin(theta)
            rx = H * 0.425
            ry = H * (0.305 if sa >= 0.0 else 0.335)
            ring.append(bm_ribs.verts.new((rx * ca, ry * sa - 0.03 * H, z_wrap_mid + dz)))
        seam_loops.append(ring)
    loft_loops(bm_ribs, seam_loops, closed_loop=True)

    # Curved vertical rib straps on the front half (-Y) of both scarf tiers
    n_ribs = 9
    for ir in range(n_ribs):
        # Span only the front face (-0.75*pi to -0.25*pi) so ribs never stick out on the side silhouette
        theta_c = -math.pi * 0.80 + (math.pi * 0.60) * (ir / (n_ribs - 1))
        d_theta = 0.032
        for tier_z0, tier_z1, rx_mul, ry_mul in tiers_spec:
            strap_loops = []
            for v in (0.18, 0.38, 0.62, 0.82):
                z = tier_z0 + v * (tier_z1 - tier_z0)
                profile = math.sin(v * math.pi)
                # Sit just 0.002 H proud of the scarf surface at the equator and taper in at ends
                out_pad = 0.0025 * H * math.sin(((v - 0.18) / 0.64) * math.pi)
                rx = H * (0.32 + 0.140 * (profile ** 0.55)) * rx_mul + out_pad
                ry_f = H * (0.24 + 0.120 * (profile ** 0.55)) * ry_mul + out_pad
                row = []
                for th in (theta_c - d_theta, theta_c + d_theta):
                    ca = math.cos(th)
                    sa = math.sin(th)
                    row.append(bm_ribs.verts.new((rx * ca, ry_f * sa - 0.03 * H, z)))
                strap_loops.append(row)
            loft_loops(bm_ribs, strap_loops, closed_loop=False)

    ribs_obj = new_mesh_obj("scarf_ribs", bm_ribs, mat=mats["teal_dark"], shade_smooth=True)
    add_solidify(ribs_obj, thickness=0.004 * H, offset=-1.0)

    # --- 3. Front Hanging Scarf Tail on HER LEFT (+X) (`scarf_tail`) ---
    bm_tail = bmesh.new()
    z_tail_top = z_wrap_bot + 0.04 * H
    z_tail_bot = P.z_belt - 0.008 * H
    x_tail = +0.200 * H  # Strictly on HER LEFT (+X, viewer's right in front view)
    tail_half_w = 0.105 * H
    tail_thick = 0.058 * H

    nv_t = 12
    n_ring_t = 16
    tail_loops = []
    for iv in range(nv_t):
        v = iv / (nv_t - 1)
        z = z_tail_top * (1.0 - v) + z_tail_bot * v
        y_center = -H * (0.330 + 0.018 * math.sin(v * math.pi * 0.7))
        w_scale = 0.95 + 0.06 * v

        ring = []
        for i in range(n_ring_t):
            theta = 2.0 * math.pi * i / n_ring_t
            ca = math.cos(theta)
            sa = math.sin(theta)
            sq = 1.0 + 0.22 * (ca * ca * sa * sa)
            px = x_tail + ca * tail_half_w * w_scale * sq
            py = y_center + sa * (0.5 * tail_thick) * sq
            ring.append(bm_tail.verts.new((px, py, z)))
        tail_loops.append(ring)

    loft_loops(bm_tail, tail_loops, cap_start=True, cap_end=True, closed_loop=True)
    tail_obj = new_mesh_obj("scarf_tail", bm_tail, mat=mats["teal"], shade_smooth=True)
    add_subsurf(tail_obj, levels=1)

    # Flush horizontal knit rib bands on the scarf tail (`scarf_tail_ribs` in `teal_dark`)
    bm_tribs = bmesh.new()
    n_stripes = 5 if P.build == "base" else 4
    for ist in range(n_stripes):
        vt = 0.16 + 0.72 * (ist / max(1, n_stripes - 1))
        zt = z_tail_top * (1.0 - vt) + z_tail_bot * vt
        yt = -H * (0.330 + 0.018 * math.sin(vt * math.pi * 0.7))
        w_s = (0.95 + 0.06 * vt) * tail_half_w * 0.96
        band_loops = []
        for dz in (-0.008 * H, 0.008 * H):
            ring = []
            for i in range(n_ring_t):
                theta = 2.0 * math.pi * i / n_ring_t
                ca = math.cos(theta)
                sa = math.sin(theta)
                sq = 1.0 + 0.22 * (ca * ca * sa * sa)
                px = x_tail + ca * w_s * sq
                py = yt + sa * (0.5 * tail_thick + 0.002 * H) * sq
                ring.append(bm_tribs.verts.new((px, py, zt + dz)))
            band_loops.append(ring)
        loft_loops(bm_tribs, band_loops, closed_loop=True)
    tribs_obj = new_mesh_obj("scarf_tail_ribs", bm_tribs, mat=mats["teal_dark"], shade_smooth=True)

    # --- 4. Light-Teal Tassel Fringe (`scarf_fringe` in `teal_light`) ---
    bm_fringe = bmesh.new()
    n_tassels = 4
    fringe_h = 0.052 * H
    z_f_mid = z_tail_bot - 0.45 * fringe_h
    y_f_mid = -H * 0.332
    for it in range(n_tassels):
        u_f = -0.76 + 1.52 * (it / (n_tassels - 1))
        xf = x_tail + u_f * tail_half_w
        ret = bmesh.ops.create_cube(bm_fringe, size=1.0)
        for v in ret["verts"]:
            v.co.x = xf + v.co.x * (0.042 * H)
            v.co.y = y_f_mid + v.co.y * (0.044 * H)
            v.co.z = z_f_mid + v.co.z * fringe_h
    fringe_obj = new_mesh_obj("scarf_fringe", bm_fringe, mat=mats["teal_light"], shade_smooth=True)
    add_subsurf(fringe_obj, levels=1)

    return scarf_obj
# ==============================================================================
# S5: ARMS, SLEEVES, MITTENS, LEGS, BOOTS, AND MAIN ENTRYPOINT (REVISED FOR R2)
# ==============================================================================

def set_origin_to_point(obj, world_pt):
    """
    Moves the object's origin to `world_pt` (e.g. shoulder or hip joint) while
    keeping its world-space vertex positions unchanged, so future rigging is easy.
    """
    local_shift = obj.matrix_world.inverted() @ world_pt
    for v in obj.data.vertices:
        v.co -= local_shift
    obj.data.update()
    obj.location = world_pt


def build_arms_and_mittens(P, mats):
    """
    Rebuilt for R2 to match c1, c2, c3, c4, c5:
    - `sleeve_L`, `sleeve_R`: Held at a natural ~10 degree angle with a soft elbow curve
      so a clear negative-space gap separates the upper arm from the pinched waist (`z_belt`),
      while the wrists/mittens rest right along the outer edge of the coat hem (`|x| ~ 0.72 H`)
      rather than sticking out wide like rigid diagonal pipes.
    - `cuff_L`, `cuff_R`: Crisp rust-brown (`#A85A3A`) wrist cuffs.
    - `mitten_L`, `mitten_R`: Rounded teal mittens (`#2A8C8E`) with a distinct inward/front thumb lobe.
    """
    H = P.H
    ang_rad = math.radians(10.0 if P.build == "base" else 11.0)

    for side, suffix in ((1.0, "L"), (-1.0, "R")):
        sh_pt = Vector((
            side * (0.5 * P.shoulder_w - 0.03 * H),
            -0.015 * H,
            P.z_shoulder - 0.035 * H
        ))

        wrist_z = P.z_hem + 0.21 * H
        arm_drop = sh_pt.z - wrist_z
        # Wrist sits right near the outer edge of the skirt hem (c2, c3)
        wrist_x = sh_pt.x + side * arm_drop * math.tan(ang_rad)
        wrist_y = sh_pt.y - 0.035 * H

        # --- 1. Slightly Puffy Coat Sleeve (`sleeve_L/R`) ---
        bm_slv = bmesh.new()
        n_stations = 12
        n_seg = 18
        slv_loops = []

        for ist in range(n_stations):
            t = ist / (n_stations - 1)  # 0 = shoulder cap, 1 = wrist cuff
            # Gentle outward bow through the upper/mid arm so the waist silhouette separates cleanly,
            # then curving almost vertically down into the cuff (matching c2 front view)
            elbow_bow_x = side * 0.034 * H * math.sin(t * math.pi * 0.85)
            elbow_bow_y = -0.022 * H * math.sin(t * math.pi * 0.85)

            cx = sh_pt.x * (1.0 - t) + wrist_x * t + elbow_bow_x
            cy = sh_pt.y * (1.0 - t) + wrist_y * t + elbow_bow_y
            cz = sh_pt.z * (1.0 - t) + wrist_z * t

            if t < 0.14:
                s = t / 0.14
                rx = H * (0.092 + 0.042 * (s ** 0.65))
                ry = H * (0.102 + 0.042 * (s ** 0.65))
            elif t < 0.86:
                s = (t - 0.14) / 0.72
                puff = math.sin(s * math.pi * 0.80)
                rx = H * (0.134 + 0.026 * puff)
                ry = H * (0.144 + 0.026 * puff)
            else:
                s = (t - 0.86) / 0.14
                rx = H * (0.148 - 0.018 * s)
                ry = H * (0.158 - 0.018 * s)

            local_tilt = ang_rad * (1.2 - 0.8 * t)
            rot = Euler((0.05, -side * local_tilt, 0.0), 'XYZ').to_matrix()
            ring = []
            for i in range(n_seg):
                theta = 2.0 * math.pi * i / n_seg
                local = Vector((rx * math.cos(theta), ry * math.sin(theta), 0.0))
                pt = Vector((cx, cy, cz)) + (rot @ local)
                ring.append(bm_slv.verts.new(pt))
            slv_loops.append(ring)

        loft_loops(bm_slv, slv_loops, cap_start=True, cap_end=True, closed_loop=True)
        slv_obj = new_mesh_obj(f"sleeve_{suffix}", bm_slv, mat=mats["coat"], shade_smooth=True)
        add_subsurf(slv_obj, levels=1)
        set_origin_to_point(slv_obj, sh_pt)

        # --- 2. Rust-Brown Sleeve Cuff (`cuff_L/R`) ---
        bm_cuff = bmesh.new()
        cuff_loops = []
        cuff_h = 0.072 * H
        rot_c = Euler((0.05, -side * ang_rad * 0.45, 0.0), 'XYZ').to_matrix()
        for v in (0.0, 0.35, 0.70, 1.0):
            cz = wrist_z + (0.45 - v) * cuff_h
            cx = wrist_x + side * (v - 0.45) * cuff_h * math.tan(ang_rad * 0.45)
            cy = wrist_y - (v - 0.45) * 0.006 * H
            bulge = 1.0 + 0.07 * math.sin(v * math.pi)
            rx = H * 0.142 * bulge
            ry = H * 0.150 * bulge
            ring = []
            for i in range(n_seg):
                theta = 2.0 * math.pi * i / n_seg
                local = Vector((rx * math.cos(theta), ry * math.sin(theta), 0.0))
                pt = Vector((cx, cy, cz)) + (rot_c @ local)
                ring.append(bm_cuff.verts.new(pt))
            cuff_loops.append(ring)
        loft_loops(bm_cuff, cuff_loops, cap_start=True, cap_end=True, closed_loop=True)
        cuff_obj = new_mesh_obj(f"cuff_{suffix}", bm_cuff, mat=mats["rust"], shade_smooth=True)
        add_subsurf(cuff_obj, levels=1)
        set_origin_to_point(cuff_obj, sh_pt)

        # --- 3. Rounded Teal Mitten + Thumb (`mitten_L/R`) ---
        bm_mit = bmesh.new()
        mit_center = Vector((
            wrist_x + side * 0.008 * H,
            wrist_y - 0.008 * H,
            wrist_z - 0.110 * H
        ))

        ret_m = bmesh.ops.create_uvsphere(bm_mit, u_segments=16, v_segments=12, radius=1.0)
        rot_m = Euler((0.06, -side * ang_rad * 0.35, 0.0), 'XYZ').to_matrix()
        for v in ret_m["verts"]:
            v.co.x *= P.mitten_r * 0.95
            v.co.y *= P.mitten_r * 0.86
            v.co.z *= P.mitten_r * 1.10
            v.co = mit_center + (rot_m @ v.co)

        # Distinct thumb lobe on the inner-front side of the mitten (c2, c3, c4)
        ret_t = bmesh.ops.create_uvsphere(bm_mit, u_segments=12, v_segments=10, radius=1.0)
        thumb_offset = Vector((
            -side * P.mitten_r * 0.90,
            -P.mitten_r * 0.38,
            P.mitten_r * 0.18
        ))
        rot_t = Euler((0.20, side * 0.55, -side * 0.25), 'XYZ').to_matrix()
        for v in ret_t["verts"]:
            v.co.x *= P.mitten_r * 0.44
            v.co.y *= P.mitten_r * 0.42
            v.co.z *= P.mitten_r * 0.60
            v.co = mit_center + thumb_offset + (rot_t @ v.co)

        mit_obj = new_mesh_obj(f"mitten_{suffix}", bm_mit, mat=mats["teal"], shade_smooth=True)
        add_subsurf(mit_obj, levels=1)
        set_origin_to_point(mit_obj, sh_pt)


def build_legs_and_boots(P, mats):
    """
    Constructs:
    - `leg_L`, `leg_R`: Slim anime legs in dark plum-charcoal tights (`tights` `#45435E`).
    - `boot_L`, `boot_R`: Mid-calf brown winter boots (`boots` `#6E3C3A`) with rounded toe
      pointing forward (-Y) and flat sole resting on `z = 0.0`.
    - `boot_cuff_L`, `boot_cuff_R`: Fluffy cream fur cuffs (`fur` `#F2E6CE`).
    """
    H = P.H

    for side, suffix in ((1.0, "L"), (-1.0, "R")):
        hip_pt = Vector((side * P.leg_spacing, 0.0, P.z_hip))

        # --- 1. Tights Leg (`leg_L/R`) ---
        bm_leg = bmesh.new()
        z_top = P.z_hip + 0.08 * H
        z_bot = P.z_boot_top - 0.12 * H
        n_stations = 16
        n_seg = 20
        leg_loops = []

        for ist in range(n_stations):
            u = ist / (n_stations - 1)
            z = z_bot + u * (z_top - z_bot)

            u_knee = (P.z_knee - z_bot) / max(1e-4, (z_top - z_bot))

            if u < u_knee:
                s = u / max(1e-4, u_knee)
                calf_bump = math.sin(s * math.pi * 0.85) ** 1.2
                rad = P.ankle_r + (P.calf_r - P.ankle_r) * calf_bump + (P.knee_r - P.ankle_r) * (s * 0.45)
            else:
                s = (u - u_knee) / max(1e-4, (1.0 - u_knee))
                rad = P.knee_r + (P.thigh_r - P.knee_r) * (s ** 0.82)

            xc = side * (P.leg_spacing * (0.90 + 0.10 * u))
            yc = 0.0
            if u < u_knee:
                s = u / max(1e-4, u_knee)
                yc = 0.018 * H * math.sin(s * math.pi)
            else:
                s = (u - u_knee) / max(1e-4, (1.0 - u_knee))
                yc = -0.012 * H * math.sin(s * math.pi)

            ring = []
            for i in range(n_seg):
                theta = 2.0 * math.pi * i / n_seg
                ca = math.cos(theta)
                sa = math.sin(theta)
                rx = rad * 0.96
                ry = rad * (1.08 if sa >= 0.0 else 0.98)
                ring.append(bm_leg.verts.new((xc + rx * ca, yc + ry * sa, z)))
            leg_loops.append(ring)

        loft_loops(bm_leg, leg_loops, cap_start=True, cap_end=True, closed_loop=True)
        leg_obj = new_mesh_obj(f"leg_{suffix}", bm_leg, mat=mats["tights"], shade_smooth=True)
        add_subsurf(leg_obj, levels=1)
        set_origin_to_point(leg_obj, hip_pt)

        # --- 2. Brown Mid-Calf Winter Boot (`boot_L/R`) ---
        bm_boot = bmesh.new()
        xc_b = side * (P.leg_spacing * 0.91)
        z_b_top = P.z_boot_top - 0.02 * H
        z_ankle = P.z_ankle

        toe_reach = -0.355 * H
        heel_reach = 0.145 * H
        shaft_rf = -0.130 * H
        shaft_rb = 0.140 * H
        foot_w = 0.138 * H
        shaft_w = 0.125 * H

        boot_stations = [
            (0.000 * H, toe_reach * 0.95, heel_reach * 0.95, foot_w * 0.94, 0.25),
            (0.012 * H, toe_reach,        heel_reach,        foot_w,        0.25),
            (0.065 * H, toe_reach * 1.01, heel_reach,        foot_w * 1.02, 0.20),
            (0.135 * H, toe_reach * 0.86, heel_reach * 0.98, foot_w * 0.96, 0.14),
            (z_ankle,   shaft_rf * 1.18,  shaft_rb * 1.02,   shaft_w * 0.96, 0.08),
            (z_ankle + 0.35 * (z_b_top - z_ankle), shaft_rf, shaft_rb, shaft_w * 0.98, 0.05),
            (z_ankle + 0.72 * (z_b_top - z_ankle), shaft_rf * 1.03, shaft_rb * 1.03, shaft_w * 1.03, 0.05),
            (z_b_top,   shaft_rf * 1.04,  shaft_rb * 1.04,   shaft_w * 1.04, 0.05),
        ]

        n_b_seg = 24
        boot_loops = []
        for z_s, yf, yb, hw, sq_fac in boot_stations:
            yc_s = 0.5 * (yf + yb)
            ry_s = 0.5 * (yb - yf)
            ring = []
            for i in range(n_b_seg):
                theta = 2.0 * math.pi * i / n_b_seg
                ca = math.cos(theta)
                sa = math.sin(theta)
                sq = 1.0 + sq_fac * (ca * ca * sa * sa)
                w_mod = 1.0 - 0.08 * sa if z_s < z_ankle else 1.0
                px = xc_b + hw * ca * sq * w_mod
                py = yc_s + ry_s * sa * sq
                pz = 0.0 if z_s <= 0.001 * H else z_s
                ring.append(bm_boot.verts.new((px, py, pz)))
            boot_loops.append(ring)

        loft_loops(bm_boot, boot_loops, cap_start=True, cap_end=True, closed_loop=True)
        boot_obj = new_mesh_obj(f"boot_{suffix}", bm_boot, mat=mats["boots"], shade_smooth=True)
        add_subsurf(boot_obj, levels=1)
        set_origin_to_point(boot_obj, hip_pt)

        # --- 3. Cream Fur/Knit Boot Cuff (`boot_cuff_L/R`) ---
        bm_fc = bmesh.new()
        cuff_z0 = z_b_top - 0.035 * H
        cuff_z1 = P.z_boot_top + 0.055 * H
        fc_loops = []
        for v in (0.0, 0.25, 0.55, 0.82, 1.0):
            zc = cuff_z0 + v * (cuff_z1 - cuff_z0)
            puff = math.sin(v * math.pi) ** 0.65
            rx = shaft_w * (1.06 + 0.18 * puff)
            ry_f = abs(shaft_rf) * (1.06 + 0.18 * puff)
            ry_b = abs(shaft_rb) * (1.06 + 0.18 * puff)
            ring = []
            for i in range(20):
                theta = 2.0 * math.pi * i / 20
                ca = math.cos(theta)
                sa = math.sin(theta)
                fluff_wave = 1.0 + 0.025 * math.cos(10.0 * theta) * puff
                px = xc_b + rx * ca * fluff_wave
                py = (ry_b if sa >= 0.0 else ry_f) * sa * fluff_wave
                ring.append(bm_fc.verts.new((px, py, zc)))
            fc_loops.append(ring)

        loft_loops(bm_fc, fc_loops, cap_start=True, cap_end=True, closed_loop=True)
        fc_obj = new_mesh_obj(f"boot_cuff_{suffix}", bm_fc, mat=mats["fur"], shade_smooth=True)
        add_subsurf(fc_obj, levels=1)
        set_origin_to_point(fc_obj, hip_pt)


# ==============================================================================
# MAIN SCENE ASSEMBLY & SAVE
# ==============================================================================

def main():
    outdir, build_mode = parse_args()
    os.makedirs(outdir, exist_ok=True)

    # Reset to clean empty factory startup scene
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # Compute proportions and create palette materials
    P = Proportions(build_mode=build_mode)
    mats = create_materials()

    # Create required `head_center` Empty with `head_h` custom property
    create_head_center_empty(P)

    # Build character sections
    build_head_and_neck(P, mats)
    build_face_features(P, mats)
    build_hair_crown_and_bangs(P, mats)
    build_side_locks(P, mats)
    build_back_hair(P, mats)
    build_ponytail(P, mats)
    build_bow(P, mats)
    build_coat_and_details(P, mats)
    build_scarf(P, mats)
    build_arms_and_mittens(P, mats)
    build_legs_and_boots(P, mats)

    # Normalize so the top of the hair crown (excluding bow) is at z = 1.0 and soles at z = 0.0
    normalize_crown_to_unit_z(P)

    # Save output blend file
    out_blend = os.path.join(os.path.abspath(outdir), "model.blend")
    bpy.ops.wm.save_as_mainfile(filepath=out_blend)
    print(f"[r20] Saved {build_mode} build to {out_blend}")


if __name__ == "__main__":
    main()
