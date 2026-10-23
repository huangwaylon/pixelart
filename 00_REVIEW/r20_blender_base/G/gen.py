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
# S1: HEAD, NECK, EARS, AND FACE FEATURES
# ==============================================================================

def head_surface_point(P, x_norm, z_val):
    """
    Evaluates the front (-Y) surface of the anime head at a given height z_val
    and normalized lateral position x_norm = x / half_width in [-1, 1].
    Used to place eyes, brows, nose, mouth, and blush cleanly on the face plane.
    """
    H = P.H
    u = max(0.0, min(1.0, (z_val - P.z_chin) / H))

    # Width envelope from chin (u=0) to crown (u=1)
    if u < 0.14:
        t = u / 0.14
        rx = H * (0.09 + 0.18 * (t ** 0.75))
    elif u < 0.42:
        t = (u - 0.14) / 0.28
        rx = H * (0.27 + 0.135 * math.sin(t * math.pi * 0.5))
    elif u < 0.72:
        t = (u - 0.42) / 0.30
        rx = H * (0.405 + 0.010 * math.sin(t * math.pi))
    else:
        t = (u - 0.72) / 0.28
        rx = H * 0.405 * math.cos(t * math.pi * 0.46)

    # Front (-Y) centerline depth profile
    if u < 0.12:
        # Chin tip curve
        y_front = -H * (0.295 + 0.065 * (u / 0.12))
    elif u < 0.36:
        # Lower cheek / mouth plane
        t = (u - 0.12) / 0.24
        y_front = -H * (0.360 + 0.022 * math.sin(t * math.pi * 0.5))
    elif u < 0.55:
        # Eye socket slight recession in profile (c8)
        t = (u - 0.36) / 0.19
        y_front = -H * (0.382 - 0.018 * math.sin(t * math.pi))
    elif u < 0.80:
        # Forehead
        t = (u - 0.55) / 0.25
        y_front = -H * (0.378 - 0.045 * (t ** 1.3))
    else:
        t = (u - 0.80) / 0.20
        y_front = -H * (0.333 * math.cos(t * math.pi * 0.46))

    x_clamped = max(-0.98, min(0.98, x_norm))
    x = rx * x_clamped
    # Anime face front has a flatter front plane that curves back toward the temples/ears
    curve_back = H * 0.22 * (abs(x_clamped) ** 1.85)
    y = y_front + curve_back
    return Vector((x, y, z_val))


def build_head_and_neck(P, mats):
    """
    Builds the anime head (`head`), slender neck (`neck`), and ears (`ear_L`, `ear_R`).
    Matches ref4/ref5/ref6 anime face construction and c6/c7/c8 canon proportions:
    - Heart/oval front silhouette with full cheeks tapering to a small defined chin
    - Slight eye-plane inset and forward cheek curve in profile
    - Clean jawline from ear to chin
    """
    H = P.H
    bm = bmesh.new()

    # Vertical stations u in [0, 1] from chin to crown
    u_stations = [
        0.00, 0.04, 0.10, 0.18, 0.27, 0.36,
        0.44, 0.52, 0.62, 0.73, 0.84, 0.93, 1.00
    ]
    n_seg = 24
    loops = []

    for u in u_stations:
        z = P.z_chin + u * H
        if u <= 0.001:
            # Small chin cap ring
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
            # Half-width rx
            if u < 0.16:
                t = u / 0.16
                rx = H * (0.09 + 0.19 * (t ** 0.78))
            elif u < 0.42:
                t = (u - 0.16) / 0.26
                rx = H * (0.28 + 0.128 * math.sin(t * math.pi * 0.5))
            elif u < 0.72:
                t = (u - 0.42) / 0.30
                rx = H * (0.408 + 0.008 * math.sin(t * math.pi))
            else:
                t = (u - 0.72) / 0.28
                rx = H * 0.408 * math.cos(t * math.pi * 0.44)

            # Front (-Y) reach
            if u < 0.14:
                t = u / 0.14
                y_front = -H * (0.295 + 0.065 * (t ** 0.75))
            elif u < 0.36:
                t = (u - 0.14) / 0.22
                y_front = -H * (0.360 + 0.022 * math.sin(t * math.pi * 0.5))
            elif u < 0.55:
                t = (u - 0.36) / 0.19
                y_front = -H * (0.382 - 0.016 * math.sin(t * math.pi))
            elif u < 0.80:
                t = (u - 0.55) / 0.25
                y_front = -H * (0.378 - 0.045 * (t ** 1.25))
            else:
                t = (u - 0.80) / 0.20
                y_front = -H * (0.333 * math.cos(t * math.pi * 0.44))

            # Back (+Y) cranium reach (jaw rises from chin to back of skull)
            if u < 0.22:
                t = u / 0.22
                y_back = H * (-0.21 + 0.29 * (t ** 0.85))
            elif u < 0.65:
                t = (u - 0.22) / 0.43
                y_back = H * (0.08 + 0.36 * math.sin(t * math.pi * 0.5))
            else:
                t = (u - 0.65) / 0.35
                y_back = H * 0.44 * math.cos(t * math.pi * 0.44)

            y_center = 0.5 * (y_front + y_back)
            ry_f = abs(y_front - y_center)
            ry_b = abs(y_back - y_center)

        ring = []
        for i in range(n_seg):
            theta = 2.0 * math.pi * i / n_seg
            ca = math.cos(theta)
            sa = math.sin(theta)

            if sa < 0.0:
                # Front half of the head (-Y): flatter anime face plane with fuller cheeks
                front_t = abs(sa)
                # Square off the front slightly so the face has distinct front and side planes
                lat_x = rx * ca * (1.0 - 0.06 * (front_t ** 2) * (1.0 - abs(ca)))
                lat_y = y_center - ry_f * (front_t ** 0.78)
                # Cheek fullness around u ~ 0.25..0.38
                cheek_boost = math.exp(-((u - 0.31) / 0.12) ** 2) * (abs(ca) * (1.0 - abs(ca)) * 4.0)
                lat_y -= H * 0.018 * cheek_boost * front_t
                # Jawline vertical drop near the front-to-side transition
                z_mod = z
                if 0.05 < u < 0.28 and abs(ca) > 0.45:
                    z_mod -= H * 0.015 * (1.0 - u / 0.28) * (abs(ca) - 0.45)
            else:
                # Back cranium (+Y): smooth rounded skull
                lat_x = rx * ca
                lat_y = y_center + ry_b * (sa ** 0.92)
                z_mod = z

            ring.append(bm.verts.new((lat_x, lat_y, z_mod)))
        loops.append(ring)

    loft_loops(bm, loops, cap_start=True, cap_end=True, closed_loop=True)
    head_obj = new_mesh_obj("head", bm, mat=mats["skin"], shade_smooth=True)
    add_subsurf(head_obj, levels=2)

    # Neck (slender cylinder tapering slightly at mid-neck, tucked into head & scarf)
    bm_neck = bmesh.new()
    z_n0 = P.z_shoulder - 0.04 * H
    z_n1 = 0.5 * (P.z_shoulder + P.z_neck_top)
    z_n2 = P.z_neck_top + 0.10 * H
    y_neck = -0.05 * H
    neck_loops = [
        make_ellipse_ring(bm_neck, Vector((0.0, y_neck, z_n0)), 0.165 * H, 0.155 * H, n=16),
        make_ellipse_ring(bm_neck, Vector((0.0, y_neck, z_n1)), 0.140 * H, 0.135 * H, n=16),
        make_ellipse_ring(bm_neck, Vector((0.0, y_neck - 0.01 * H, z_n2)), 0.148 * H, 0.145 * H, n=16),
    ]
    loft_loops(bm_neck, neck_loops, cap_start=True, cap_end=True, closed_loop=True)
    neck_obj = new_mesh_obj("neck", bm_neck, mat=mats["skin"], shade_smooth=True)
    add_subsurf(neck_obj, levels=1)

    # Ears (small rounded anime ears at eye-to-nose height, mostly hidden behind side locks)
    for side, suffix in ((1.0, "L"), (-1.0, "R")):
        bm_ear = bmesh.new()
        bmesh.ops.create_uvsphere(bm_ear, u_segments=10, v_segments=8, radius=1.0)
        for v in bm_ear.verts:
            v.co.x *= 0.055 * H
            v.co.y *= 0.075 * H
            v.co.z *= 0.115 * H
        rot_ear = Euler((0.12, -0.18 * side, 0.25 * side), 'XYZ').to_matrix()
        center_ear = Vector((side * 0.405 * H, -0.04 * H, P.z_chin + 0.39 * H))
        for v in bm_ear.verts:
            v.co = center_ear + (rot_ear @ v.co)
        ear_obj = new_mesh_obj(f"ear_{suffix}", bm_ear, mat=mats["skin"], shade_smooth=True)
        add_subsurf(ear_obj, levels=1)

    return head_obj


def make_conforming_patch(P, x_center_norm, z_center, half_w_norm, half_h, y_offset, nx=8, nz=8, shape="ellipse"):
    """
    Builds a 3D surface patch that conforms to the curved anime face (`head_surface_point`),
    offset outward in -Y by `y_offset` so it turns cleanly in front, 3/4, and side views.
    """
    bm = bmesh.new()
    if shape == "ellipse":
        rings = []
        radii = [0.22, 0.60, 1.00]
        n_ang = 20
        # Center vertex
        c_pt = head_surface_point(P, x_center_norm, z_center)
        c_pt.y -= y_offset
        c_vert = bm.verts.new(c_pt)

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

        # Connect center to inner ring
        for i in range(n_ang):
            i_next = (i + 1) % n_ang
            bm.faces.new((c_vert, rings[0][i], rings[0][i_next]))
        loft_loops(bm, rings, cap_start=False, cap_end=False, closed_loop=True)
        return bm

    # Grid patch for rounded rectangles / half-ellipses
    grid = []
    for iz in range(nz + 1):
        vz = -1.0 + 2.0 * iz / nz
        row = []
        for ix in range(nx + 1):
            vx = -1.0 + 2.0 * ix / nx
            # Softly round the corners of the grid
            r2 = vx * vx + vz * vz
            scale = 1.0 / math.sqrt(max(1.0, r2 * 0.65))
            xn = x_center_norm + vx * scale * half_w_norm
            zv = z_center + vz * scale * half_h
            pt = head_surface_point(P, xn, zv)
            pt.y -= y_offset
            row.append(bm.verts.new(pt))
        grid.append(row)

    for iz in range(nz):
        for ix in range(nx):
            bm.faces.new((
                grid[iz][ix],
                grid[iz][ix + 1],
                grid[iz + 1][ix + 1],
                grid[iz + 1][ix],
            ))
    return bm


def build_face_features(P, mats):
    """
    Constructs Koyuki's facial features to match c2, c6, c7, c8:
    - Large tare-me eyes (~0.22 H tall) set low on the face, 1 eye-width apart:
      - White sclera (`eye_white`)
      - Teal lower/full iris (`iris`)
      - Dark teal upper iris + pupil (`iris_dark`)
      - Thick dark upper lash line with outer flick (`lash`)
      - Crisp white catchlight on upper-inner iris (`catchlight`)
    - Thin arched eyebrows just under the bangs (`brow`)
    - Tiny nose tip (`skin_shadow` / `skin`)
    - Cute small smile (`mouth`)
    - Soft pink blush ovals directly beneath the eyes (`blush`)
    """
    H = P.H
    z_eye = P.z_eye
    eye_half_h = 0.112 * H     # Total eye height ~0.224 H
    eye_x_norm = 0.43          # Center of each eye in normalized face width
    eye_w_norm = 0.215         # Half-width in normalized face coordinates

    for side, suffix in ((1.0, "L"), (-1.0, "R")):
        xc = side * eye_x_norm

        # 1. Sclera (white eye base, rounded squircle/oval with tare-me droop)
        bm_sclera = bmesh.new()
        n_ang = 24
        radii = [0.25, 0.65, 1.0]
        c_pt = head_surface_point(P, xc, z_eye)
        c_pt.y -= 0.0055 * H
        c_vert = bm_sclera.verts.new(c_pt)
        rings = []
        for rf in radii:
            ring = []
            for i in range(n_ang):
                ang = 2.0 * math.pi * i / n_ang
                ca = math.cos(ang)
                sa = math.sin(ang)
                # Slightly squircle shape + gentle outer corner droop (tare-me)
                sq = 1.0 + 0.12 * (ca * ca * sa * sa)
                outer_ness = ca * side  # +1 at outer corner, -1 at inner corner
                droop_z = -0.014 * H * max(0.0, outer_ness) * rf
                xn = xc + ca * eye_w_norm * rf * sq
                zv = z_eye + sa * eye_half_h * rf * sq + droop_z
                pt = head_surface_point(P, xn, zv)
                # Slight 3D convexity on the eyeball
                pt.y -= (0.0055 + 0.0025 * (1.0 - rf * rf)) * H
                ring.append(bm_sclera.verts.new(pt))
            rings.append(ring)
        for i in range(n_ang):
            bm_sclera.faces.new((c_vert, rings[0][i], rings[0][(i + 1) % n_ang]))
        loft_loops(bm_sclera, rings, closed_loop=True)
        sclera_obj = new_mesh_obj(f"eye_{suffix}", bm_sclera, mat=mats["eye_white"], shade_smooth=True)
        add_solidify(sclera_obj, thickness=0.003 * H, offset=-1.0)

        # 2. Main Teal Iris (#2C9696) - fills most of the center/inner eye width
        iris_xc = xc - side * 0.018
        iris_w = eye_w_norm * 0.78
        iris_h = eye_half_h * 0.90
        bm_iris = make_conforming_patch(
            P, iris_xc, z_eye - 0.005 * H,
            iris_w, iris_h, y_offset=0.0095 * H, shape="ellipse"
        )
        iris_obj = new_mesh_obj(f"iris_{suffix}", bm_iris, mat=mats["iris"], shade_smooth=True)
        add_solidify(iris_obj, thickness=0.0025 * H, offset=-1.0)

        # 3. Upper Dark Teal Iris & Pupil (#1C4C54) - top half of iris + central pupil core
        bm_dark = bmesh.new()
        n_ang_d = 20
        c_d = head_surface_point(P, iris_xc, z_eye + 0.018 * H)
        c_d.y -= 0.0120 * H
        cv_d = bm_dark.verts.new(c_d)
        d_rings = []
        for rf in (0.35, 0.72, 1.0):
            ring = []
            for i in range(n_ang_d):
                ang = 2.0 * math.pi * i / n_ang_d
                ca = math.cos(ang)
                sa = math.sin(ang)
                # Covers upper 60% of iris + dips down in the center for the pupil
                zv_rel = (0.20 + 0.78 * sa) if sa >= 0.0 else (0.20 + 0.52 * sa)
                xn = iris_xc + ca * (iris_w * 0.94) * rf
                zv = z_eye + zv_rel * iris_h * rf
                pt = head_surface_point(P, xn, zv)
                pt.y -= 0.0120 * H
                ring.append(bm_dark.verts.new(pt))
            d_rings.append(ring)
        for i in range(n_ang_d):
            bm_dark.faces.new((cv_d, d_rings[0][i], d_rings[0][(i + 1) % n_ang_d]))
        loft_loops(bm_dark, d_rings, closed_loop=True)
        dark_obj = new_mesh_obj(f"iris_dark_{suffix}", bm_dark, mat=mats["iris_dark"], shade_smooth=True)
        add_solidify(dark_obj, thickness=0.002 * H, offset=-1.0)

        # 4. Thick Upper Lash Line with Tare-Me Outer Flick (#20223E)
        bm_lash = bmesh.new()
        n_u = 16
        lash_top = []
        lash_bot = []
        for i in range(n_u + 1):
            t = i / n_u  # 0 = inner corner, 1 = outer flick tip
            u_span = -0.95 + 2.12 * t  # Extends past outer corner (t=1 -> +1.17)
            xn = xc + side * u_span * eye_w_norm
            # Arch over the top of the eye and flick gently outward/downward
            if u_span <= 0.85:
                arch = math.cos((u_span / 1.05) * math.pi * 0.48)
                z_base = z_eye + eye_half_h * (0.62 + 0.36 * arch)
                thick = H * (0.026 + 0.016 * math.sin(t * math.pi))
            else:
                # Outer flick past the eye corner (c7, c8)
                over = (u_span - 0.85) / 0.32
                z_base = z_eye + eye_half_h * (0.72 - 0.16 * over)
                thick = H * 0.028 * (1.0 - 0.55 * over)

            pt_bot = head_surface_point(P, xn, z_base - 0.35 * thick)
            pt_top = head_surface_point(P, xn, z_base + 0.65 * thick)
            pt_bot.y -= 0.0145 * H
            pt_top.y -= 0.0155 * H
            lash_bot.append(bm_lash.verts.new(pt_bot))
            lash_top.append(bm_lash.verts.new(pt_top))

        loft_loops(bm_lash, [lash_bot, lash_top], closed_loop=False)
        lash_obj = new_mesh_obj(f"lash_{suffix}", bm_lash, mat=mats["lash"], shade_smooth=True)
        add_solidify(lash_obj, thickness=0.0055 * H, offset=-1.0)

        # 5. White Catchlight (upper-left of each iris in front view, i.e. -X shift, +Z shift)
        cl_xn = iris_xc - 0.055  # Viewer's left (-X) in front view on both eyes, matching c6/c7
        cl_z = z_eye + 0.032 * H
        bm_cl = make_conforming_patch(
            P, cl_xn, cl_z,
            0.048, 0.024 * H, y_offset=0.0155 * H, shape="ellipse"
        )
        cl_obj = new_mesh_obj(f"catchlight_{suffix}", bm_cl, mat=mats["catchlight"], shade_smooth=True)
        add_solidify(cl_obj, thickness=0.002 * H, offset=-1.0)

        # 6. Eyebrow (thin warm-brown stroke just below the bang cut line)
        bm_brow = bmesh.new()
        b_top = []
        b_bot = []
        for i in range(9):
            t = i / 8.0
            u_b = -0.80 + 1.65 * t
            xn = xc + side * u_b * eye_w_norm
            arch = math.sin(t * math.pi) * 0.012 * H - 0.006 * H * t
            zb = P.z_brow + arch
            thick = 0.018 * H * (1.0 - 0.25 * abs(2.0 * t - 1.0))
            p0 = head_surface_point(P, xn, zb - 0.5 * thick)
            p1 = head_surface_point(P, xn, zb + 0.5 * thick)
            p0.y -= 0.009 * H
            p1.y -= 0.009 * H
            b_bot.append(bm_brow.verts.new(p0))
            b_top.append(bm_brow.verts.new(p1))
        loft_loops(bm_brow, [b_bot, b_top], closed_loop=False)
        brow_obj = new_mesh_obj(f"brow_{suffix}", bm_brow, mat=mats["brow"], shade_smooth=True)
        add_solidify(brow_obj, thickness=0.0035 * H, offset=-1.0)

        # 7. Blush Ovals (horizontal pink oval under the outer-lower half of each eye)
        blush_xn = xc + side * 0.05
        blush_z = z_eye - eye_half_h - 0.026 * H
        bm_blush = make_conforming_patch(
            P, blush_xn, blush_z,
            0.155, 0.022 * H, y_offset=0.0065 * H, shape="ellipse"
        )
        blush_obj = new_mesh_obj(f"blush_{suffix}", bm_blush, mat=mats["blush"], shade_smooth=True)
        add_solidify(blush_obj, thickness=0.0018 * H, offset=-1.0)

    # 8. Tiny Button Nose Tip (visible in profile c8 and as a delicate point in front c7)
    bm_nose = bmesh.new()
    bmesh.ops.create_uvsphere(bm_nose, u_segments=10, v_segments=8, radius=1.0)
    nose_base = head_surface_point(P, 0.0, P.z_nose)
    for v in bm_nose.verts:
        v.co.x *= 0.022 * H
        # Project forward (-Y) into a crisp little anime nose tip
        if v.co.y < 0:
            v.co.y *= 0.042 * H
        else:
            v.co.y *= 0.018 * H
        v.co.z *= 0.026 * H
        v.co += nose_base + Vector((0.0, -0.006 * H, 0.0))
    nose_obj = new_mesh_obj("nose", bm_nose, mat=mats["skin_shadow"], shade_smooth=True)
    add_subsurf(nose_obj, levels=1)

    # 9. Cute Small Smile Mouth (U-curved stroke in `mouth` #8E2C4A, c2/c7)
    bm_mouth = bmesh.new()
    m_bot = []
    m_top = []
    n_m = 10
    for i in range(n_m + 1):
        t = -1.0 + 2.0 * i / n_m
        xn = t * 0.145
        smile_curve = 0.022 * H * (t * t)
        zm = P.z_mouth + smile_curve
        thick = 0.016 * H * (1.0 - 0.35 * (t * t))
        p0 = head_surface_point(P, xn, zm - 0.5 * thick)
        p1 = head_surface_point(P, xn, zm + 0.5 * thick)
        p0.y -= 0.0085 * H
        p1.y -= 0.0085 * H
        m_bot.append(bm_mouth.verts.new(p0))
        m_top.append(bm_mouth.verts.new(p1))
    loft_loops(bm_mouth, [m_bot, m_top], closed_loop=False)
    mouth_obj = new_mesh_obj("mouth", bm_mouth, mat=mats["mouth"], shade_smooth=True)
    add_solidify(mouth_obj, thickness=0.003 * H, offset=-1.0)
# ==============================================================================
# S2: HAIR (Crown Dome, 3-Panel Hime Bangs, Side Locks, Back Hair, Ponytail)
# ==============================================================================

def build_hair_crown_and_bangs(P, mats):
    """
    Builds:
    1. `hair_crown`: Upper skull hair cap adding ~0.12 H on top and ~0.10 H on sides,
       with a subtle center whorl/part groove at the top crown (`z_hair_crown = 1.0`).
    2. `bangs`: Voluminous 3-panel hime blunt bangs with 2 inverted-V notches just
       above the brows (c6, c7) and a clear forward shell overhang in profile (c8).
    """
    H = P.H

    # --- 1. Hair Crown Cap ---
    bm_crown = bmesh.new()
    u_vals = [0.32, 0.45, 0.58, 0.72, 0.85, 0.95, 1.04, 1.10, 1.12]
    n_seg = 28
    loops = []
    for idx, u in enumerate(u_vals):
        z = P.z_chin + u * H
        t_norm = idx / (len(u_vals) - 1)
        if t_norm < 0.55:
            s = t_norm / 0.55
            rx = H * (0.455 + 0.045 * math.sin(s * math.pi * 0.65))
            ry_f = H * (0.405 + 0.045 * math.sin(s * math.pi * 0.65))
            ry_b = H * (0.465 + 0.055 * math.sin(s * math.pi * 0.65))
        else:
            s = (t_norm - 0.55) / 0.45
            cos_s = math.cos(s * math.pi * 0.48)
            rx = H * 0.495 * cos_s
            ry_f = H * 0.445 * cos_s
            ry_b = H * 0.515 * cos_s

        ring = []
        for i in range(n_seg):
            theta = 2.0 * math.pi * i / n_seg
            ca = math.cos(theta)
            sa = math.sin(theta)
            x = rx * ca
            y = (ry_b * sa) if sa >= 0.0 else (ry_f * sa)

            # Open the front face area below the forehead so face is uncovered
            z_mod = z
            if sa < -0.15 and u < 0.72:
                lift = (0.72 - u) * (-sa - 0.15) / 0.85
                z_mod += lift * 0.52 * H
                y -= 0.025 * H * (-sa - 0.15)
            # Subtle crown part dip right on the centerline at top
            if u > 0.95 and abs(ca) < 0.18:
                z_mod -= 0.012 * H * (1.0 - abs(ca) / 0.18)

            ring.append(bm_crown.verts.new((x, y, z_mod)))
        loops.append(ring)

    loft_loops(bm_crown, loops, cap_start=False, cap_end=True, closed_loop=True)
    crown_obj = new_mesh_obj("hair_crown", bm_crown, mat=mats["hair"], shade_smooth=True)
    add_solidify(crown_obj, thickness=0.022 * H, offset=-1.0)
    add_subsurf(crown_obj, levels=2)

    # --- 2. 3-Panel Hime Bangs ---
    # Three distinct blunt panels (Left outer, Center widest, Right outer)
    # separated by two clean inverted-V notches at |x| ~ 0.175 H (c6, c7).
    # Each panel curves forward from the crown like a thick shell (c8).
    bm_bangs = bmesh.new()
    panels = [
        # (x_min, x_max, bottom_z_offset, forward_boost)
        (-0.375 * H, -0.185 * H, -0.008 * H, 0.96),   # Her Right outer panel
        (-0.160 * H,  0.160 * H, -0.015 * H, 1.02),   # Center widest panel
        ( 0.185 * H,  0.375 * H, -0.008 * H, 0.96),   # Her Left outer panel
    ]

    z_root = P.z_crown + 0.08 * H
    z_cut_base = P.z_brow + 0.042 * H

    for x0, x1, z_drop, fwd_mul in panels:
        nx = 8
        nv = 9
        panel_loops = []
        xm = 0.5 * (x0 + x1)
        half_span = 0.5 * (x1 - x0)

        for iv in range(nv):
            v = iv / (nv - 1)  # 0 = crown root, 1 = blunt cut bottom edge
            row = []
            for ix in range(nx):
                u = -1.0 + 2.0 * ix / (nx - 1)  # -1..1 across panel width
                # Slight taper at root, full width at bottom cut, tiny inward bevel at very tip
                w_scale = 0.78 + 0.22 * (v ** 0.55)
                if v > 0.88:
                    w_scale *= 1.0 - 0.03 * ((v - 0.88) / 0.12)
                x = xm + u * half_span * w_scale

                # Bottom blunt edge has a very slight convex curve
                z_bot = z_cut_base + z_drop - 0.012 * H * (1.0 - u * u)
                # Shell trajectory from crown root down over forehead
                z = z_root * (1.0 - v) + z_bot * v + 0.045 * H * math.sin(v * math.pi * 0.75)

                # Forward overhang profile (c8: projects out past forehead, then tucks slightly at tip)
                r_x_norm = abs(x) / (0.45 * H)
                y_head_wrap = 0.14 * H * (r_x_norm ** 1.85)
                shell_bulge = math.sin(v * math.pi * 0.72) * 0.095 * H * fwd_mul
                tip_tuck = max(0.0, (v - 0.78) / 0.22) ** 1.5 * 0.022 * H
                # Puff each panel slightly across its own width so the 3 panels read distinctly
                panel_puff = 0.012 * H * (1.0 - u * u) * math.sin(v * math.pi)

                y = -0.345 * H - shell_bulge + tip_tuck + y_head_wrap - panel_puff
                row.append(bm_bangs.verts.new((x, y, z)))
            panel_loops.append(row)

        loft_loops(bm_bangs, panel_loops, cap_start=False, cap_end=False, closed_loop=False)

    # Also add an upper bridge strip connecting the tops of the 3 panels above the notches
    # so the notches have a realistic height (~0.09 H tall inverted-V cutouts, matching c7)
    bridge_loops = []
    for iv in range(5):
        v = iv / 4.0  # covers upper 65% of the bangs height
        row = []
        for ix in range(17):
            u = -1.0 + 2.0 * ix / 16.0
            x = u * 0.385 * H
            z_bot_bridge = z_cut_base + 0.085 * H
            z = z_root * (1.0 - v) + z_bot_bridge * v + 0.035 * H * math.sin(v * math.pi * 0.75)
            r_x_norm = abs(x) / (0.45 * H)
            y = -0.340 * H - math.sin(v * math.pi * 0.72) * 0.088 * H + 0.14 * H * (r_x_norm ** 1.85)
            row.append(bm_bangs.verts.new((x, y, z)))
        bridge_loops.append(row)
    loft_loops(bm_bangs, bridge_loops, closed_loop=False)

    bangs_obj = new_mesh_obj("bangs", bm_bangs, mat=mats["hair"], shade_smooth=True)
    add_solidify(bangs_obj, thickness=0.038 * H, offset=0.6)
    add_subsurf(bangs_obj, levels=2)

    return crown_obj, bangs_obj


def build_side_locks(P, mats):
    """
    Builds `sidelock_L` and `sidelock_R`:
    - Flat, thick hime side locks (~0.18 H wide) running vertically in front of the ears
      from the temple down to the collarbone/top of the scarf, ending in a crisp blunt cut.
    - Frames the cheeks in front and 3/4 views without hiding the eyes or blush (c2, c6, c7, c8).
    """
    H = P.H
    z_top = P.z_brow + 0.16 * H
    z_bot = P.z_shoulder + 0.02 * H  # Reaches collarbone / scarf top wrap

    for side, suffix in ((1.0, "L"), (-1.0, "R")):
        bm = bmesh.new()
        nv = 12
        nu = 6
        loops = []

        for iv in range(nv):
            v = iv / (nv - 1)  # 0 = temple root, 1 = blunt bottom cut
            z = z_top * (1.0 - v) + z_bot * v

            # Center X stays just outside the cheek silhouette (~0.415 H)
            xc = side * H * (0.415 + 0.018 * math.sin(v * math.pi * 0.8))
            # Center Y sits in front of the ear (~ -0.22 H at top, -0.24 H down by the cheek/scarf)
            yc = -H * (0.235 + 0.025 * math.sin(v * math.pi * 0.6))

            # Width is ~0.18 H, angled slightly to wrap around the front-side plane of the cheek
            half_w = 0.090 * H * (0.92 + 0.08 * math.sin(v * math.pi * 0.7))
            if v > 0.90:
                # Very slight blunt-tip taper for clean subsurf edge
                half_w *= 1.0 - 0.06 * ((v - 0.90) / 0.10)

            row = []
            for iu in range(nu):
                u = -1.0 + 2.0 * iu / (nu - 1)  # -1 = front/inner edge, +1 = back/outer edge
                # Angle the ribbon ~48 degrees so its broad face shows in both front and side views
                dx = side * u * half_w * 0.55
                dy = u * half_w * 0.88
                # Gentle outward camber across the lock
                camber = 0.012 * H * (1.0 - u * u)
                px = xc + dx + side * camber * 0.7
                py = yc + dy - camber * 0.5
                row.append(bm.verts.new((px, py, z)))
            loops.append(row)

        loft_loops(bm, loops, closed_loop=False)
        obj = new_mesh_obj(f"sidelock_{suffix}", bm, mat=mats["hair"], shade_smooth=True)
        add_solidify(obj, thickness=0.036 * H, offset=0.0)
        add_subsurf(obj, levels=2)


def build_back_hair(P, mats):
    """
    Builds `back_hair` and `back_hair_inner`:
    - Broad, smooth, layered hair curtain flowing down from the crown behind the head
      and shoulders (`y > +0.08 H`), ending in a blunt slight-V cut at `P.z_back_hair_tip`.
    - Strictly stays BEHIND the shoulders and sleeves so the cream coat, scarf, and arms
      are 100% unobstructed in front and 3/4 views (c1, c2, c3, c5).
    """
    H = P.H
    bm = bmesh.new()

    z_top = P.z_crown + 0.02 * H
    z_bot = P.z_back_hair_tip
    nv = 16
    nu = 15
    loops = []

    for iv in range(nv):
        v = iv / (nv - 1)  # 0 = crown, 1 = bottom hem
        row = []
        for iu in range(nu):
            u = -1.0 + 2.0 * iu / (nu - 1)  # -1 = Her Right (-X), +1 = Her Left (+X)
            abs_u = abs(u)

            # Slight V-cut at the bottom hem + subtle layered step on outer edges (c5)
            v_drop = 0.065 * H * (1.0 - abs_u ** 1.4)
            z_end = z_bot - v_drop
            z = z_top * (1.0 - v) + z_end * v

            # Width envelope: wraps the back of the head at top, widens gently behind shoulders,
            # but NEVER exceeds shoulder/sleeve silhouette in front view
            if v < 0.25:
                t = v / 0.25
                half_w = H * (0.44 + 0.06 * math.sin(t * math.pi * 0.5))
            else:
                t = (v - 0.25) / 0.75
                half_w = H * (0.50 + 0.03 * math.sin(t * math.pi * 0.6) - 0.03 * (t ** 1.8))

            x = u * half_w

            # Y depth: wraps around the back half of the skull at top, then drapes behind the coat/scarf
            if v < 0.28:
                wrap_depth = H * (0.36 * (1.0 - 0.85 * (abs_u ** 1.6)))
                y_base = 0.10 * H + wrap_depth
            else:
                t = (v - 0.28) / 0.72
                # Drape cleanly behind scarf (+0.26 H) and back of coat
                curve_back = H * (0.28 + 0.06 * math.sin(t * math.pi * 0.8))
                edge_cup = H * 0.16 * (abs_u ** 1.7)
                # Subtle vertical sheet ridges (3 broad panels across the back, c5)
                sheet_wave = 0.012 * H * math.cos(u * math.pi * 3.0) * math.sin(v * math.pi)
                y_base = curve_back - edge_cup + sheet_wave

            row.append(bm.verts.new((x, y_base, z)))
        loops.append(row)

    loft_loops(bm, loops, closed_loop=False)
    back_obj = new_mesh_obj("back_hair", bm, mat=mats["hair"], shade_smooth=True)
    add_solidify(back_obj, thickness=0.045 * H, offset=-1.0)
    add_subsurf(back_obj, levels=2)

    # Inner shadow layer (`hair_shadow` #6E3C3A) just inside the back hair so neck/side views
    # show rich dark-brown depth behind the neck and side locks (c3, c4, c6, c10)
    bm_in = bmesh.new()
    in_loops = []
    for iv in range(10):
        v = iv / 9.0
        z = (z_top - 0.08 * H) * (1.0 - v) + (z_bot + 0.03 * H) * v
        half_w = H * (0.45 - 0.03 * v)
        row = []
        for iu in range(9):
            u = -1.0 + 2.0 * iu / 8.0
            x = u * half_w
            y = H * (0.18 + 0.06 * v - 0.12 * (abs(u) ** 1.5))
            row.append(bm_in.verts.new((x, y, z)))
        in_loops.append(row)
    loft_loops(bm_in, in_loops, closed_loop=False)
    in_obj = new_mesh_obj("back_hair_inner", bm_in, mat=mats["hair_shadow"], shade_smooth=True)
    add_solidify(in_obj, thickness=0.025 * H, offset=-1.0)
    add_subsurf(in_obj, levels=1)

    return back_obj


def build_ponytail(P, mats):
    """
    Builds `ponytail`:
    - Gathers high at the back of the crown (`z ~ z_brow + 0.12 H`) directly under the bow knot.
    - Swells to ~0.48 H thick, arches backward in a clear S-curve behind the back hair (c3, c4),
      and tapers to a single sharp point at `P.z_ponytail_tip` down the center of the back (c5).
    - Constructed with 6 fluted clump lobes around the cross-section so it reads as layered
      anime hair clumps rather than a plain tube.
    """
    H = P.H
    bm = bmesh.new()

    z_root = P.z_brow + 0.12 * H
    z_tip = P.z_ponytail_tip
    y_root = 0.43 * H

    n_rings = 18
    n_seg = 24
    loops = []

    for ir in range(n_rings):
        t = ir / (n_rings - 1)  # 0 = knot root, 1 = sharp bottom tip

        # S-curve trajectory in YZ plane:
        # Rises slightly out of the knot, arcs backward (+Y), then sweeps down to a sharp tip
        z = z_root * (1.0 - t) + z_tip * t + 0.055 * H * math.sin(t * math.pi * 0.65) * (1.0 - t)
        s_arch = math.sin(t * math.pi * 0.72) * 0.18 * H
        tip_flick = (max(0.0, t - 0.70) / 0.30) ** 2 * 0.035 * H
        yc = y_root + s_arch + tip_flick

        # Radius envelope: pinched at root under bow knot (t=0), swells to ~0.23 H radius
        # (~0.46 H total thickness) around t=0.28, then tapers smoothly to a sharp point at t=1
        if t < 0.28:
            s = t / 0.28
            rad = H * (0.085 + 0.140 * math.sin(s * math.pi * 0.5))
        else:
            s = (t - 0.28) / 0.72
            rad = H * 0.225 * ((1.0 - s) ** 1.35)
        rad = max(0.004 * H, rad)

        # Tilt the cross-section ring along the tangent of the ponytail curve
        tilt = 0.35 * (1.0 - 2.0 * t)
        rot = Euler((tilt, 0.0, 0.0), 'XYZ').to_matrix()

        ring = []
        for i in range(n_seg):
            theta = 2.0 * math.pi * i / n_seg
            # 5-lobe fluted clump profile so layered hair strands read in lighting & silhouette
            clump_flute = 1.0 + 0.10 * math.cos(5.0 * theta + 0.6 * t) * math.sin(t * math.pi)
            rx = rad * 1.05 * clump_flute
            ry = rad * 0.85 * clump_flute
            local = Vector((rx * math.cos(theta), ry * math.sin(theta), 0.0))
            pt = Vector((0.0, yc, z)) + (rot @ local)
            ring.append(bm.verts.new(pt))
        loops.append(ring)

    loft_loops(bm, loops, cap_start=True, cap_end=True, closed_loop=True)
    pt_obj = new_mesh_obj("ponytail", bm, mat=mats["hair"], shade_smooth=True)
    add_subsurf(pt_obj, levels=2)
    return pt_obj
# ==============================================================================
# S3: SIGNATURE TEAL BOW (Center Knot, Puffy Teardrop Loops, Hollow Core, Tails)
# ==============================================================================

def build_bow(P, mats):
    """
    Constructs Koyuki's signature oversized teal satin bow at the ponytail root:
    - `bow_knot`: Pinched vertical ribbon knot at the back of the crown (`teal` + `teal_dark` band).
    - `bow_loop_L`, `bow_loop_R`: Two large puffy teardrop loops spanning ~1.96x head width
      (`|x| = 0.80 H` tip-to-tip = `1.60 H`), angled slightly up and back so in front view (c1, c2, c7, c10)
      the rounded wing tips project boldly out past both sides of the head and read unmistakably
      as a ribbon bow (never cat/bear ears).
    - `bow_hollow_L`, `bow_hollow_R`: Deep `teal_dark` (#1C4C54) inner loop openings & center crease
      visible from front, 3/4, side, and back views (c6, c7, c8, c9).
    - `bow_tail_L`, `bow_tail_R`: Two long swallowtail (V-notched) ribbon tails draping down
      over the upper back hair on either side of the ponytail to shoulder-blade level (c5, c6, c9).
    """
    H = P.H
    z_knot = P.z_brow + 0.17 * H
    y_knot = 0.44 * H

    # --- 1. Center Pinched Ribbon Knot (`bow_knot`) ---
    bm_knot = bmesh.new()
    knot_w = 0.085 * H
    knot_d = 0.070 * H
    knot_h = 0.115 * H
    n_seg = 16
    knot_loops = []
    for iv, v in enumerate((-1.0, -0.5, 0.0, 0.5, 1.0)):
        z = z_knot + v * knot_h
        # Bulge slightly in the middle of the knot wrap
        bulge = 1.0 + 0.14 * (1.0 - v * v)
        if abs(v) > 0.9:
            bulge *= 0.82
        rx = knot_w * bulge
        ry = knot_d * bulge
        ring = []
        for i in range(n_seg):
            theta = 2.0 * math.pi * i / n_seg
            ca = math.cos(theta)
            sa = math.sin(theta)
            # Squared-off satin ribbon knot cross-section
            sq = 1.0 + 0.18 * (ca * ca * sa * sa)
            x = rx * ca * sq
            y = y_knot + ry * sa * sq
            ring.append(bm_knot.verts.new((x, y, z)))
        knot_loops.append(ring)

    loft_loops(bm_knot, knot_loops, cap_start=True, cap_end=True, closed_loop=True)
    knot_obj = new_mesh_obj("bow_knot", bm_knot, mat=mats["teal"], shade_smooth=True)
    add_subsurf(knot_obj, levels=2)

    # --- 2. Puffy Teardrop Ribbon Loops + Dark Inner Hollows ---
    # Each loop starts pinched inside the knot (`|x| = 0.05 H`) and flares outward to `|x| = 0.80 H`
    # (~1.95x head width total span = 1.60 H), matching c7 and c9.
    for side, suffix in ((1.0, "L"), (-1.0, "R")):
        bm_loop = bmesh.new()
        n_stations = 14
        n_ring = 24
        loop_rings = []

        for ist in range(n_stations):
            u = ist / (n_stations - 1)  # 0 = pinched knot root, 1 = outer rounded wing tip

            # Horizontal reach from knot out past head silhouette (head hair half-width is ~0.49 H)
            x = side * H * (0.045 + 0.765 * (u ** 0.90))

            # Vertical & depth centerline trajectory:
            # Rises gently as it goes outward (matching the upward-tilted bow wings in c7/c9)
            # and sweeps slightly forward toward the outer tip so it frames the head in 3/4 & side views (c6, c8)
            z_center = z_knot + H * (0.075 * (u ** 0.85) - 0.020 * (u ** 3))
            y_center = y_knot - H * (0.115 * math.sin(u * math.pi * 0.60))

            # Vertical height of teardrop loop: pinched at knot, tall and puffy near outer wing
            if u < 0.84:
                s = u / 0.84
                half_h = H * (0.052 + 0.175 * (s ** 0.72))
            else:
                s = (u - 0.84) / 0.16
                half_h = H * 0.227 * math.cos(s * math.pi * 0.47)

            # Front-to-back thickness of the puffy ribbon loop
            if u < 0.84:
                s = u / 0.84
                half_d = H * (0.042 + 0.095 * math.sin(s * math.pi * 0.65))
            else:
                s = (u - 0.84) / 0.16
                half_d = H * 0.125 * math.cos(s * math.pi * 0.47)

            # Hollow pinch in the middle of the loop (between u = 0.25 and u = 0.82)
            # creates the classic folded ribbon rim + central crease
            hollow_strength = 0.0
            if 0.20 < u < 0.86:
                hu = (u - 0.20) / 0.66
                hollow_strength = math.sin(hu * math.pi) ** 1.2

            ring = []
            for i in range(n_ring):
                theta = 2.0 * math.pi * i / n_ring
                ca = math.cos(theta)  # front/back (-1 = front -Y, +1 = back +Y)
                sa = math.sin(theta)  # top/bottom (+1 = top +Z, -1 = bottom -Z)

                # Puffy top and bottom rims, pinched inward at the horizontal midline (sa ~ 0)
                mid_pinch = 1.0 - 0.48 * hollow_strength * ((1.0 - sa * sa) ** 1.6)
                # Slight flattening at outer top/bottom so the loop reads as folded broad ribbon
                rim_bulge = 1.0 + 0.18 * (sa * sa)

                dy = ca * half_d * mid_pinch * rim_bulge
                dz = sa * half_h

                # Tilt the loop cross-section slightly around Z/X so the hollow is visible in front, side, and back
                px = x - side * 0.025 * H * (1.0 - sa * sa) * hollow_strength
                py = y_center + dy
                pz = z_center + dz
                ring.append(bm_loop.verts.new((px, py, pz)))
            loop_rings.append(ring)

        loft_loops(bm_loop, loop_rings, cap_start=True, cap_end=True, closed_loop=True)
        loop_obj = new_mesh_obj(f"bow_loop_{suffix}", bm_loop, mat=mats["teal"], shade_smooth=True)
        add_subsurf(loop_obj, levels=2)

        # --- 3. Deep Teal-Dark Inner Loop Hollow (`bow_hollow_L/R`) ---
        # Explicit geometry in `teal_dark` (#1C4C54) nestled in the front, back, and side hollow of each loop
        # so the dark inner opening & ribbon crease read crisply in flat Workbench shading (c7, c8, c9).
        bm_hol = bmesh.new()
        hol_rings = []
        for ist in range(8):
            u = 0.22 + 0.62 * (ist / 7.0)
            x = side * H * (0.045 + 0.765 * (u ** 0.90))
            z_center = z_knot + H * (0.070 * (u ** 0.85) - 0.018 * (u ** 3))
            y_center = y_knot - H * (0.115 * math.sin(u * math.pi * 0.60))

            hu = (u - 0.22) / 0.62
            env = math.sin(hu * math.pi) ** 0.75
            # Teardrop-shaped dark hollow core that pokes slightly through the pinched waist
            # and out the outer side opening (matching c8 side view dark square & c7/c9 dark crease)
            h_z = H * (0.022 + 0.058 * (u ** 0.9)) * env
            h_y = H * (0.048 + 0.055 * math.sin(u * math.pi * 0.65)) * (0.65 + 0.35 * env)

            ring = []
            for i in range(16):
                theta = 2.0 * math.pi * i / 16
                ca = math.cos(theta)
                sa = math.sin(theta)
                px = x + side * (0.018 * H * u)
                py = y_center + ca * h_y
                pz = z_center + sa * h_z
                ring.append(bm_hol.verts.new((px, py, pz)))
            hol_rings.append(ring)

        loft_loops(bm_hol, hol_rings, cap_start=True, cap_end=True, closed_loop=True)
        hol_obj = new_mesh_obj(f"bow_hollow_{suffix}", bm_hol, mat=mats["teal_dark"], shade_smooth=True)
        add_subsurf(hol_obj, levels=1)

        # --- 4. Swallowtail Ribbon Tails (`bow_tail_L/R`) ---
        # Hang down from under the knot on either side of the ponytail down to shoulder-blade level,
        # ending in an inverted V-notch swallowtail cut (c5, c6, c9).
        bm_tail = bmesh.new()
        z_t_top = z_knot - 0.05 * H
        z_t_bot = P.z_shoulder - 0.28 * H
        if P.build == "sprite":
            z_t_bot = P.z_shoulder - 0.20 * H

        nv_t = 12
        nu_t = 7  # odd count so center vertex forms the sharp V-notch at the bottom
        t_grid = []

        for iv in range(nv_t):
            v = iv / (nv_t - 1)  # 0 = under knot, 1 = bottom V-cut tips
            row = []
            # Center X of the ribbon tail diverges gently from the knot down the sides of the ponytail (c9)
            xc = side * H * (0.075 + 0.145 * (v ** 0.88))
            # Center Y drapes over the upper back hair alongside the ponytail root
            yc = y_knot + H * (0.035 + 0.065 * math.sin(v * math.pi * 0.70) - 0.02 * v)
            half_w = H * (0.052 + 0.024 * v)

            for iu in range(nu_t):
                u = -1.0 + 2.0 * iu / (nu_t - 1)  # -1..+1 across ribbon width
                # Swallowtail V-notch at bottom edge: center (u=0) is notched upward by 0.065 H
                v_notch = (1.0 - abs(u)) * 0.070 * H * (v ** 2.2)
                z = z_t_top * (1.0 - v) + z_t_bot * v + v_notch

                # Ribbon faces mostly backward (+Y) and slightly outward (+X/-X)
                px = xc + side * u * half_w * 0.88
                py = yc - abs(u) * 0.012 * H + side * u * half_w * 0.35
                row.append(bm_tail.verts.new((px, py, z)))
            t_grid.append(row)

        loft_loops(bm_tail, t_grid, closed_loop=False)
        tail_obj = new_mesh_obj(f"bow_tail_{suffix}", bm_tail, mat=mats["teal"], shade_smooth=False)
        add_solidify(tail_obj, thickness=0.022 * H, offset=0.0)
        add_subsurf(tail_obj, levels=1)
# ==============================================================================
# S4: TORSO, COAT, BELT, BUTTONS, AND CHUNKY KNIT SCARF
# ==============================================================================

def coat_profile_at(P, u):
    """
    Returns (z, rx, ry_front, ry_back, pleat_amp) for the coat exterior at normalized
    vertical coordinate u in [0, 1] from bottom hem (u=0) to top collar/shoulder (u=1).
    Matches c1-c5 and ref4/ref5:
    - Crisp A-line skirt flare below the belt (`u < u_belt`)
    - Pinched waist at `z_belt`
    - Soft modest bust curve above the belt
    - Sloped shoulders at the top
    """
    H = P.H
    z_top = P.z_shoulder + 0.03 * H
    z_bot = P.z_hem
    z = z_bot + u * (z_top - z_bot)

    u_belt = (P.z_belt - z_bot) / (z_top - z_bot)
    u_bust = (P.z_bust - z_bot) / (z_top - z_bot)

    if u <= u_belt:
        # Skirt section: flares from waist_w at belt (s=1) down to hem_w at hem (s=0)
        s = u / max(1e-4, u_belt)  # 0 at hem, 1 at belt
        flare = (1.0 - s) ** 0.88
        rx = 0.5 * (P.waist_w + (P.hem_w - P.waist_w) * flare)
        ry_f = H * (0.235 + 0.255 * flare)
        ry_b = H * (0.225 + 0.255 * flare)
        pleat_amp = H * 0.022 * ((1.0 - s) ** 1.1)
    elif u <= u_bust:
        # Lower bodice from waist to bust
        s = (u - u_belt) / max(1e-4, (u_bust - u_belt))
        smooth_s = math.sin(s * math.pi * 0.5)
        rx = 0.5 * (P.waist_w + (P.bust_w - P.waist_w) * smooth_s)
        ry_f = H * (0.235 + 0.065 * smooth_s)
        ry_b = H * (0.225 + 0.025 * smooth_s)
        pleat_amp = 0.0
    else:
        # Upper chest to neck/shoulder base (tucks under the chunky scarf)
        s = (u - u_bust) / max(1e-4, (1.0 - u_bust))
        rx = 0.5 * (P.bust_w * (1.0 - 0.35 * (s ** 1.4)))
        ry_f = H * (0.300 * (1.0 - 0.38 * (s ** 1.3)))
        ry_b = H * (0.250 * (1.0 - 0.32 * (s ** 1.3)))
        pleat_amp = 0.0

    return z, rx, ry_f, ry_b, pleat_amp


def build_coat_and_details(P, mats):
    """
    Constructs:
    - `coat`: Fitted cream bodice + flared A-line pleated skirt with slight curved hem.
    - `coat_trim`: Rust-brown (`#A85A3A`) border band along the bottom hem of the skirt.
    - `coat_inside`: Darker inner underside (`coat_shadow` `#D2BFA4`) closing the bottom of the skirt.
    - `belt` & `buckle`: Dark-brown waist belt (`#6E3C3A`) with a centered gold rectangular buckle (`#E2A434`).
    - `buttons`: 6 small gold buttons down the front centerline (3 above the belt, 3 below).
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

            # 6 soft vertical box-pleat waves around the skirt (strongest on front and back, c2/c5)
            pleat = pleat_amp * math.cos(6.0 * theta)
            r_x = rx + pleat * 0.65
            r_y = (ry_b if sa >= 0.0 else ry_f) + pleat * 0.85

            x = r_x * ca
            y = r_y * sa - 0.02 * H  # slight forward bias for torso posture

            # Gentle downward curve on front/back hem (c2, c3, c4)
            z_hem_curve = -0.018 * H * (1.0 - u) * (sa * sa)
            ring.append(bm_coat.verts.new((x, y, z + z_hem_curve)))
        coat_loops.append(ring)

    loft_loops(bm_coat, coat_loops, cap_start=False, cap_end=True, closed_loop=True)
    coat_obj = new_mesh_obj("coat", bm_coat, mat=mats["coat"], shade_smooth=True)
    add_subsurf(coat_obj, levels=2)

    # --- 2. Coat Underside Cap (`coat_inside`) ---
    # Closes the hollow inside the A-line skirt hem with `coat_shadow` (#D2BFA4)
    bm_in = bmesh.new()
    _, rx0, ry_f0, ry_b0, pleat0 = coat_profile_at(P, 0.02)
    in_rings = []
    for rf in (0.35, 0.70, 0.96):
        ring = []
        for i in range(n_seg):
            theta = 2.0 * math.pi * i / n_seg
            ca = math.cos(theta)
            sa = math.sin(theta)
            pleat = pleat0 * math.cos(6.0 * theta) * rf
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
    trim_u_vals = [0.0, 0.025, 0.055]
    trim_loops = []
    for u in trim_u_vals:
        z, rx, ry_f, ry_b, pleat_amp = coat_profile_at(P, u)
        ring = []
        for i in range(n_seg):
            theta = 2.0 * math.pi * i / n_seg
            ca = math.cos(theta)
            sa = math.sin(theta)
            pleat = pleat_amp * math.cos(6.0 * theta)
            r_x = rx + pleat * 0.65 + 0.006 * H
            r_y = (ry_b if sa >= 0.0 else ry_f) + pleat * 0.85 + 0.006 * H
            x = r_x * ca
            y = r_y * sa - 0.02 * H
            z_hem_curve = -0.018 * H * (1.0 - u) * (sa * sa)
            ring.append(bm_trim.verts.new((x, y, z + z_hem_curve - 0.008 * H)))
        trim_loops.append(ring)
    loft_loops(bm_trim, trim_loops, cap_start=False, cap_end=False, closed_loop=True)
    trim_obj = new_mesh_obj("coat_trim", bm_trim, mat=mats["rust"], shade_smooth=True)
    add_solidify(trim_obj, thickness=0.016 * H, offset=0.5)
    add_subsurf(trim_obj, levels=2)

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
            x = (rx_b + 0.010 * H) * ca
            y = ((ry_bb if sa >= 0.0 else ry_fb) + 0.010 * H) * sa - 0.02 * H
            ring.append(bm_belt.verts.new((x, y, P.z_belt + dz)))
        belt_loops.append(ring)
    loft_loops(bm_belt, belt_loops, closed_loop=True)
    belt_obj = new_mesh_obj("belt", bm_belt, mat=mats["belt"], shade_smooth=True)
    add_solidify(belt_obj, thickness=0.015 * H, offset=1.0)
    add_subsurf(belt_obj, levels=1)

    # Gold Buckle centered on front (-Y) of belt (c2, c3, c10)
    bm_buckle = bmesh.new()
    bw = 0.055 * H
    bh = 0.048 * H
    bd = 0.022 * H
    y_buck = -(ry_fb + 0.024 * H) - 0.02 * H
    bmesh.ops.create_cube(bm_buckle, size=1.0)
    for v in bm_buckle.verts:
        v.co.x *= 2.0 * bw
        v.co.y = y_buck + v.co.y * bd
        v.co.z = P.z_belt + v.co.z * (2.0 * bh)
    buckle_obj = new_mesh_obj("buckle", bm_buckle, mat=mats["gold"], shade_smooth=False)
    add_subsurf(buckle_obj, levels=1)

    # --- 5. Six Small Gold Buttons (`buttons`) ---
    # 3 above the belt (between belt and scarf bottom) and 3 below the belt (between belt and hem trim)
    z_scarf_bot = P.z_shoulder - 0.09 * H
    above_span = z_scarf_bot - (P.z_belt + belt_half_h)
    below_span = (P.z_belt - belt_half_h) - (P.z_hem + 0.06 * H)

    btn_z_list = [
        P.z_belt + belt_half_h + above_span * 0.22,
        P.z_belt + belt_half_h + above_span * 0.52,
        P.z_belt + belt_half_h + above_span * 0.82,
        P.z_belt - belt_half_h - below_span * 0.22,
        P.z_belt - belt_half_h - below_span * 0.52,
        P.z_belt - belt_half_h - below_span * 0.82,
    ]

    bm_btns = bmesh.new()
    btn_r = 0.022 * H
    for zb in btn_z_list:
        u_b = max(0.0, min(1.0, (zb - z_bot) / (z_top - z_bot)))
        _, _, ry_f_btn, _, pleat_b = coat_profile_at(P, u_b)
        yb = -(ry_f_btn + pleat_b * 0.85) - 0.02 * H - 0.008 * H
        ret = bmesh.ops.create_uvsphere(bm_btns, u_segments=10, v_segments=8, radius=1.0)
        for v in ret["verts"]:
            v.co.x = v.co.x * btn_r
            v.co.y = yb + v.co.y * (0.55 * btn_r)
            v.co.z = zb + v.co.z * btn_r
    btns_obj = new_mesh_obj("buttons", bm_btns, mat=mats["gold"], shade_smooth=True)

    return coat_obj


def build_scarf(P, mats):
    """
    Constructs the chunky winter teal knit scarf (`scarf`, `scarf_ribs`, `scarf_tail`, `scarf_fringe`):
    - Double-wrapped high around the neck (~0.30 H thick vertically, wider than the head/neck)
      hiding the coat collar completely in all views (c1-c6).
    - Distinct dark-teal (`teal_dark` #1C4C54) horizontal division between the upper and lower wraps
      plus vertical knit rib grooves across the wrap (c2, c6, c7, c8).
    - ONE tail hangs down the front on **HER LEFT (+X, viewer's right in front view)** from the wrap
      down to the belt (`z_belt`), with horizontal knit rib stripes and a short fringe of
      light-teal (`teal_light` #6ACBB6) tassels at the tip.
    """
    H = P.H
    z_wrap_bot = P.z_shoulder - 0.07 * H
    z_wrap_top = P.z_chin + 0.05 * H
    if z_wrap_top - z_wrap_bot < 0.28 * H:
        z_wrap_bot = z_wrap_top - 0.29 * H
    z_wrap_mid = 0.5 * (z_wrap_bot + z_wrap_top)

    # --- 1. Two-Tier Bulky Neck Wrap (`scarf`) ---
    bm_scarf = bmesh.new()
    n_seg = 32

    for tier_z0, tier_z1, rx_mul, ry_mul in (
        (z_wrap_bot, z_wrap_mid + 0.008 * H, 1.04, 1.04),  # Lower wrap tier (slightly wider)
        (z_wrap_mid - 0.005 * H, z_wrap_top, 0.98, 0.98),  # Upper wrap tier
    ):
        tier_loops = []
        v_steps = [0.0, 0.18, 0.50, 0.82, 1.0]
        for v in v_steps:
            z = tier_z0 + v * (tier_z1 - tier_z0)
            # Rounded pillowy profile for each wrap coil
            profile = math.sin(v * math.pi)
            rx = H * (0.32 + 0.145 * (profile ** 0.55)) * rx_mul
            ry_f = H * (0.24 + 0.125 * (profile ** 0.55)) * ry_mul
            ry_b = H * (0.22 + 0.115 * (profile ** 0.55)) * ry_mul

            ring = []
            for i in range(n_seg):
                theta = 2.0 * math.pi * i / n_seg
                ca = math.cos(theta)
                sa = math.sin(theta)
                # Subtle knit rib undulation around circumference (14 ribs)
                rib_wave = 1.0 + 0.018 * math.cos(14.0 * theta) * profile
                x = rx * ca * rib_wave
                y = (ry_b if sa >= 0.0 else ry_f) * sa * rib_wave - 0.03 * H
                ring.append(bm_scarf.verts.new((x, y, z)))
            tier_loops.append(ring)
        loft_loops(bm_scarf, tier_loops, cap_start=True, cap_end=True, closed_loop=True)

    scarf_obj = new_mesh_obj("scarf", bm_scarf, mat=mats["teal"], shade_smooth=True)
    add_subsurf(scarf_obj, levels=2)

    # --- 2. Knit Ribbing Grooves & Seam Accents (`scarf_ribs` in `teal_dark`) ---
    # Ensures the horizontal wrap division and vertical knit ribs read clearly in flat Workbench renders (c2, c6, c7, c8)
    bm_ribs = bmesh.new()
    # Horizontal mid-seam ring between the two wraps
    seam_loops = []
    for dz in (-0.010 * H, 0.010 * H):
        ring = []
        for i in range(n_seg):
            theta = 2.0 * math.pi * i / n_seg
            ca = math.cos(theta)
            sa = math.sin(theta)
            rx = H * 0.455
            ry = H * (0.325 if sa >= 0.0 else 0.355)
            ring.append(bm_ribs.verts.new((rx * ca, ry * sa - 0.03 * H, z_wrap_mid + dz)))
        seam_loops.append(ring)
    loft_loops(bm_ribs, seam_loops, closed_loop=True)

    # Vertical rib bars along the front and sides of both tiers
    n_ribs = 12
    for ir in range(n_ribs):
        # Distribute ribs around front/sides
        theta = -math.pi * 0.92 + (math.pi * 0.84) * (ir / (n_ribs - 1))
        ca = math.cos(theta)
        sa = math.sin(theta)
        for tier_z0, tier_z1, r_scale in (
            (z_wrap_bot + 0.022 * H, z_wrap_mid - 0.014 * H, 1.04),
            (z_wrap_mid + 0.014 * H, z_wrap_top - 0.022 * H, 0.98),
        ):
            rx = H * 0.468 * r_scale
            ry = H * 0.368 * r_scale
            xc = rx * ca
            yc = ry * sa - 0.03 * H
            zm = 0.5 * (tier_z0 + tier_z1)
            hz = 0.5 * (tier_z1 - tier_z0)
            ret = bmesh.ops.create_cube(bm_ribs, size=1.0)
            for v in ret["verts"]:
                v.co.x = xc + v.co.x * (0.016 * H)
                v.co.y = yc + v.co.y * (0.016 * H)
                v.co.z = zm + v.co.z * (2.0 * hz)

    ribs_obj = new_mesh_obj("scarf_ribs", bm_ribs, mat=mats["teal_dark"], shade_smooth=False)
    add_subsurf(ribs_obj, levels=1)

    # --- 3. Front Hanging Scarf Tail on HER LEFT (+X) (`scarf_tail`) ---
    # Hangs from the lower wrap at x = +0.20 H down to the belt (`z_belt`), matching c1, c2, c3, c6
    bm_tail = bmesh.new()
    z_tail_top = z_wrap_bot + 0.04 * H
    z_tail_bot = P.z_belt - 0.01 * H
    x_tail = +0.205 * H  # Strictly on HER LEFT (+X, viewer's right in front view)
    tail_half_w = 0.105 * H
    tail_thick = 0.065 * H

    nv_t = 12
    n_ring_t = 16
    tail_loops = []
    for iv in range(nv_t):
        v = iv / (nv_t - 1)  # 0 = top under wrap, 1 = bottom at belt
        z = z_tail_top * (1.0 - v) + z_tail_bot * v

        # Slight forward drape over the chest/bodice so it sits cleanly in front of the coat
        y_center = -H * (0.335 + 0.020 * math.sin(v * math.pi * 0.7))
        w_scale = 0.94 + 0.08 * v

        ring = []
        for i in range(n_ring_t):
            theta = 2.0 * math.pi * i / n_ring_t
            ca = math.cos(theta)
            sa = math.sin(theta)
            # Flat rectangular knit strip with rounded edges
            sq = 1.0 + 0.22 * (ca * ca * sa * sa)
            px = x_tail + ca * tail_half_w * w_scale * sq
            py = y_center + sa * (0.5 * tail_thick) * sq
            ring.append(bm_tail.verts.new((px, py, z)))
        tail_loops.append(ring)

    loft_loops(bm_tail, tail_loops, cap_start=True, cap_end=True, closed_loop=True)
    tail_obj = new_mesh_obj("scarf_tail", bm_tail, mat=mats["teal"], shade_smooth=True)
    add_subsurf(tail_obj, levels=2)

    # Horizontal knit rib stripes across the hanging scarf tail (`scarf_tail_ribs` in `teal_dark`, c2/c6)
    bm_tribs = bmesh.new()
    n_stripes = 5 if P.build == "base" else 4
    for ist in range(n_stripes):
        vt = 0.16 + 0.72 * (ist / max(1, n_stripes - 1))
        zt = z_tail_top * (1.0 - vt) + z_tail_bot * vt
        yt = -H * (0.335 + 0.020 * math.sin(vt * math.pi * 0.7))
        w_s = (0.94 + 0.08 * vt) * tail_half_w * 1.04
        ret = bmesh.ops.create_cube(bm_tribs, size=1.0)
        for v in ret["verts"]:
            v.co.x = x_tail + v.co.x * (2.0 * w_s)
            v.co.y = yt + v.co.y * (tail_thick * 1.12)
            v.co.z = zt + v.co.z * (0.018 * H)
    tribs_obj = new_mesh_obj("scarf_tail_ribs", bm_tribs, mat=mats["teal_dark"], shade_smooth=False)
    add_subsurf(tribs_obj, levels=1)

    # --- 4. Light-Teal Tassel Fringe at Bottom of Scarf Tail (`scarf_fringe` in `teal_light`) ---
    bm_fringe = bmesh.new()
    n_tassels = 4
    fringe_h = 0.052 * H
    z_f_mid = z_tail_bot - 0.45 * fringe_h
    y_f_mid = -H * 0.338
    for it in range(n_tassels):
        u_f = -0.78 + 1.56 * (it / (n_tassels - 1))
        xf = x_tail + u_f * tail_half_w
        ret = bmesh.ops.create_cube(bm_fringe, size=1.0)
        for v in ret["verts"]:
            v.co.x = xf + v.co.x * (0.040 * H)
            v.co.y = y_f_mid + v.co.y * (0.048 * H)
            v.co.z = z_f_mid + v.co.z * fringe_h
    fringe_obj = new_mesh_obj("scarf_fringe", bm_fringe, mat=mats["teal_light"], shade_smooth=True)
    add_subsurf(fringe_obj, levels=1)

    return scarf_obj
# ==============================================================================
# S5: ARMS, SLEEVES, MITTENS, LEGS, BOOTS, AND MAIN ENTRYPOINT
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
    Constructs:
    - `sleeve_L`, `sleeve_R`: Long, slightly puffy cream coat sleeves held ~14 degrees away
      from the body so the waist pinch and sleeve silhouette read clearly (c1, c2, c3, c5).
    - `cuff_L`, `cuff_R`: Rust-brown (`#A85A3A`) cuffs at the wrist end of each sleeve.
    - `mitten_L`, `mitten_R`: Cute rounded teal winter mittens (`#2A8C8E`) reaching the coat hem,
      with a distinct inward-facing thumb lobe and subtle `teal_dark` wrist/palm crease.
    """
    H = P.H
    ang_rad = math.radians(P.arm_angle_deg)

    for side, suffix in ((1.0, "L"), (-1.0, "R")):
        # Shoulder joint origin
        sh_pt = Vector((
            side * (0.5 * P.shoulder_w - 0.04 * H),
            -0.02 * H,
            P.z_shoulder - 0.04 * H
        ))

        # Wrist center sits just above the coat hem, angled outward so a gap separates
        # the inner arm from the waist/bodice
        wrist_z = P.z_hem + 0.22 * H
        arm_drop = sh_pt.z - wrist_z
        wrist_x = sh_pt.x + side * arm_drop * math.tan(ang_rad)
        wrist_y = sh_pt.y - 0.045 * H  # very slight forward elbow bend

        # --- 1. Slightly Puffy Coat Sleeve (`sleeve_L/R`) ---
        bm_slv = bmesh.new()
        n_stations = 12
        n_seg = 18
        slv_loops = []

        for ist in range(n_stations):
            t = ist / (n_stations - 1)  # 0 = shoulder cap, 1 = wrist cuff
            # Centerline with slight outward bow at elbow (t ~ 0.5) and gentle forward bend
            elbow_bow_x = side * 0.022 * H * math.sin(t * math.pi)
            elbow_bow_y = -0.028 * H * math.sin(t * math.pi * 0.85)

            cx = sh_pt.x * (1.0 - t) + wrist_x * t + elbow_bow_x
            cy = sh_pt.y * (1.0 - t) + wrist_y * t + elbow_bow_y
            cz = sh_pt.z * (1.0 - t) + wrist_z * t

            # Sleeve radius profile: smooth shoulder cap -> slim upper arm -> puffy lower sleeve -> gathered wrist
            if t < 0.12:
                s = t / 0.12
                rx = H * (0.095 + 0.045 * (s ** 0.6))
                ry = H * (0.105 + 0.045 * (s ** 0.6))
            elif t < 0.88:
                s = (t - 0.12) / 0.76
                puff = math.sin(s * math.pi * 0.82)
                rx = H * (0.140 + 0.028 * puff)
                ry = H * (0.150 + 0.028 * puff)
            else:
                s = (t - 0.88) / 0.12
                rx = H * (0.155 - 0.022 * s)
                ry = H * (0.165 - 0.022 * s)

            # Rotate cross-section slightly to follow the arm angle
            rot = Euler((0.06, -side * ang_rad * 0.85, 0.0), 'XYZ').to_matrix()
            ring = []
            for i in range(n_seg):
                theta = 2.0 * math.pi * i / n_seg
                local = Vector((rx * math.cos(theta), ry * math.sin(theta), 0.0))
                pt = Vector((cx, cy, cz)) + (rot @ local)
                ring.append(bm_slv.verts.new(pt))
            slv_loops.append(ring)

        loft_loops(bm_slv, slv_loops, cap_start=True, cap_end=True, closed_loop=True)
        slv_obj = new_mesh_obj(f"sleeve_{suffix}", bm_slv, mat=mats["coat"], shade_smooth=True)
        add_subsurf(slv_obj, levels=2)
        set_origin_to_point(slv_obj, sh_pt)

        # --- 2. Rust-Brown Sleeve Cuff (`cuff_L/R`) ---
        bm_cuff = bmesh.new()
        cuff_loops = []
        cuff_h = 0.075 * H
        rot_c = Euler((0.06, -side * ang_rad * 0.85, 0.0), 'XYZ').to_matrix()
        for v in (0.0, 0.35, 0.70, 1.0):
            cz = wrist_z + (0.45 - v) * cuff_h
            cx = wrist_x + side * (v - 0.45) * cuff_h * math.tan(ang_rad * 0.75)
            cy = wrist_y - (v - 0.45) * 0.008 * H
            bulge = 1.0 + 0.08 * math.sin(v * math.pi)
            rx = H * 0.148 * bulge
            ry = H * 0.156 * bulge
            ring = []
            for i in range(n_seg):
                theta = 2.0 * math.pi * i / n_seg
                local = Vector((rx * math.cos(theta), ry * math.sin(theta), 0.0))
                pt = Vector((cx, cy, cz)) + (rot_c @ local)
                ring.append(bm_cuff.verts.new(pt))
            cuff_loops.append(ring)
        loft_loops(bm_cuff, cuff_loops, cap_start=True, cap_end=True, closed_loop=True)
        cuff_obj = new_mesh_obj(f"cuff_{suffix}", bm_cuff, mat=mats["rust"], shade_smooth=True)
        add_subsurf(cuff_obj, levels=2)
        set_origin_to_point(cuff_obj, sh_pt)

        # --- 3. Rounded Teal Mitten + Thumb (`mitten_L/R`) ---
        # Centered just below the cuff so the bottom of the mitten aligns with the coat hem (`z_hem`)
        bm_mit = bmesh.new()
        mit_center = Vector((
            wrist_x + side * 0.018 * H,
            wrist_y - 0.010 * H,
            wrist_z - 0.115 * H
        ))

        # Main rounded mitten body
        ret_m = bmesh.ops.create_uvsphere(bm_mit, u_segments=16, v_segments=12, radius=1.0)
        rot_m = Euler((0.08, -side * ang_rad * 0.65, 0.0), 'XYZ').to_matrix()
        for v in ret_m["verts"]:
            v.co.x *= P.mitten_r * 0.96
            v.co.y *= P.mitten_r * 0.88
            v.co.z *= P.mitten_r * 1.12
            v.co = mit_center + (rot_m @ v.co)

        # Small rounded thumb lobe on the inner-front side of each mitten (c2, c3, c4)
        ret_t = bmesh.ops.create_uvsphere(bm_mit, u_segments=12, v_segments=10, radius=1.0)
        thumb_offset = Vector((
            -side * P.mitten_r * 0.88,
            -P.mitten_r * 0.35,
            P.mitten_r * 0.18
        ))
        rot_t = Euler((0.20, side * 0.55, -side * 0.25), 'XYZ').to_matrix()
        for v in ret_t["verts"]:
            v.co.x *= P.mitten_r * 0.42
            v.co.y *= P.mitten_r * 0.40
            v.co.z *= P.mitten_r * 0.58
            v.co = mit_center + thumb_offset + (rot_t @ v.co)

        mit_obj = new_mesh_obj(f"mitten_{suffix}", bm_mit, mat=mats["teal"], shade_smooth=True)
        add_subsurf(mit_obj, levels=1)
        set_origin_to_point(mit_obj, sh_pt)


def build_legs_and_boots(P, mats):
    """
    Constructs:
    - `leg_L`, `leg_R`: Slim anime legs in dark plum-charcoal tights (`tights` `#45435E`),
      spaced slightly apart (~1 fist gap between knees/calves) with fuller upper thighs,
      a clean knee transition, and a soft calf curve into the boot top (c1-c5, ref4/ref5).
    - `boot_L`, `boot_R`: Mid-calf brown winter boots (`boots` `#6E3C3A`) with a rounded toe
      pointing forward (-Y), a flat sole resting squarely on `z = 0.0`, and a subtle heel step.
    - `boot_cuff_L`, `boot_cuff_R`: Fluffy cream fur/knit cuffs (`fur` `#F2E6CE`) topping each boot.
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
            u = ist / (n_stations - 1)  # 0 = ankle inside boot, 1 = hip inside skirt
            z = z_bot + u * (z_top - z_bot)

            u_knee = (P.z_knee - z_bot) / max(1e-4, (z_top - z_bot))
            u_boot = (P.z_boot_top - z_bot) / max(1e-4, (z_top - z_bot))

            # Radius envelope: ankle -> calf curve -> knee -> full upper thigh
            if u < u_knee:
                s = u / max(1e-4, u_knee)
                # Soft calf swell between boot top and knee
                calf_bump = math.sin(s * math.pi * 0.85) ** 1.2
                rad = P.ankle_r + (P.calf_r - P.ankle_r) * calf_bump + (P.knee_r - P.ankle_r) * (s * 0.45)
            else:
                s = (u - u_knee) / max(1e-4, (1.0 - u_knee))
                rad = P.knee_r + (P.thigh_r - P.knee_r) * (s ** 0.82)

            # Subtle anime leg centerline curve in X and Y
            xc = side * (P.leg_spacing * (0.90 + 0.10 * u))
            # Knee slightly forward, calf curves gently back (+Y)
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
        add_subsurf(leg_obj, levels=2)
        set_origin_to_point(leg_obj, hip_pt)

        # --- 2. Brown Mid-Calf Winter Boot (`boot_L/R`) ---
        bm_boot = bmesh.new()
        xc_b = side * (P.leg_spacing * 0.91)
        z_b_top = P.z_boot_top - 0.02 * H
        z_ankle = P.z_ankle

        # Boot stations from sole (z = 0.0) up to mid-calf shaft top
        # Each station specifies: (z, y_front, y_back, half_width_x, squareness)
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
                # Slightly wider at the front ball of the foot than at the heel
                w_mod = 1.0 - 0.08 * sa if z_s < z_ankle else 1.0
                px = xc_b + hw * ca * sq * w_mod
                py = yc_s + ry_s * sa * sq
                # Keep the sole completely flat at z = 0.0
                pz = 0.0 if z_s <= 0.001 * H else z_s
                ring.append(bm_boot.verts.new((px, py, pz)))
            boot_loops.append(ring)

        loft_loops(bm_boot, boot_loops, cap_start=True, cap_end=True, closed_loop=True)
        boot_obj = new_mesh_obj(f"boot_{suffix}", bm_boot, mat=mats["boots"], shade_smooth=True)
        add_subsurf(boot_obj, levels=2)
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
        add_subsurf(fc_obj, levels=2)
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
