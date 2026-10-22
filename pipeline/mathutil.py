"""Small 4x4 affine helpers. Convention: right-handed, +Y up, character faces +Z, character's left is +X."""
import math
import numpy as np


def translate(x, y, z):
    m = np.eye(4)
    m[:3, 3] = (x, y, z)
    return m


def scale(x, y, z):
    return np.diag([x, y, z, 1.0])


def rot_x(deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    m = np.eye(4)
    m[1, 1], m[1, 2], m[2, 1], m[2, 2] = c, -s, s, c
    return m


def rot_y(deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    m = np.eye(4)
    m[0, 0], m[0, 2], m[2, 0], m[2, 2] = c, s, -s, c
    return m


def rot_z(deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    m = np.eye(4)
    m[0, 0], m[0, 1], m[1, 0], m[1, 1] = c, -s, s, c
    return m


def euler(rx, ry, rz):
    """Rotation applied as yaw(Y) * pitch(X) * roll(Z)."""
    return rot_y(ry) @ rot_x(rx) @ rot_z(rz)


def xform_point(m, p):
    return m[:3, :3] @ np.asarray(p, float) + m[:3, 3]


def align_y_to(direction, up_hint=(0, 0, 1)):
    """Rotation matrix (4x4) whose local +Y maps to `direction`."""
    y = np.asarray(direction, float)
    n = np.linalg.norm(y)
    y = y / n if n > 1e-9 else np.array([0, 1.0, 0])
    h = np.asarray(up_hint, float)
    if abs(np.dot(h, y)) > 0.95:
        h = np.array([1.0, 0, 0])
    x = np.cross(y, h)
    x /= np.linalg.norm(x)
    z = np.cross(x, y)
    m = np.eye(4)
    m[:3, 0], m[:3, 1], m[:3, 2] = x, y, z
    return m


def lerp(a, b, t):
    return a + (b - a) * t
