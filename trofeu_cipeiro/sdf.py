"""Primitivas SDF vetorizadas (numpy) e utilitarios 2D/texto.

Convencao: distancia negativa = dentro. Unidades: mm.
Eixos: X = direita de quem olha de frente, Y = profundidade (+Y = costas), Z = altura.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

F = np.float32


def length(*c):
    s = c[0] * c[0]
    for v in c[1:]:
        s = s + v * v
    return np.sqrt(s)


def smin(a, b, k):
    if k <= 0:
        return np.minimum(a, b)
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0.0, 1.0)
    return b * (1 - h) + a * h - k * h * (1 - h)


def smax(a, b, k):
    return -smin(-a, -b, k)


def band(d, lo, hi):
    """Regiao entre as cascas d=lo e d=hi de um hospedeiro (lo<hi)."""
    return np.maximum(lo - d, d - hi)


# ---------------------------------------------------------------- 3D
def sphere(x, y, z, c, r):
    return length(x - c[0], y - c[1], z - c[2]) - r


def ellipsoid(x, y, z, c, r):
    qx, qy, qz = (x - c[0]) / r[0], (y - c[1]) / r[1], (z - c[2]) / r[2]
    k0 = length(qx, qy, qz)
    k1 = length(qx / r[0], qy / r[1], qz / r[2])
    k1 = np.maximum(k1, 1e-6)
    return k0 * (k0 - 1.0) / k1


def capsule(x, y, z, a, b, ra, rb=None):
    """Capsula conica aproximada (raio interpolado ao longo do eixo)."""
    if rb is None:
        rb = ra
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    ba = b - a
    L2 = float(ba @ ba)
    px, py, pz = x - a[0], y - a[1], z - a[2]
    t = np.clip((px * ba[0] + py * ba[1] + pz * ba[2]) / L2, 0.0, 1.0)
    dx, dy, dz = px - ba[0] * t, py - ba[1] * t, pz - ba[2] * t
    return length(dx, dy, dz) - (ra + (rb - ra) * t)


def axis_t(x, y, z, a, b):
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    ba = b - a
    L = float(np.sqrt(ba @ ba))
    return ((x - a[0]) * ba[0] + (y - a[1]) * ba[1] + (z - a[2]) * ba[2]) / L, L


def rot_z(x, y, c, ang_deg):
    a = np.radians(ang_deg)
    ca, sa = np.cos(a), np.sin(a)
    dx, dy = x - c[0], y - c[1]
    return c[0] + ca * dx + sa * dy, c[1] - sa * dx + ca * dy


def rbox(x, y, z, c, h, r=0.0):
    qx = np.abs(x - c[0]) - (h[0] - r)
    qy = np.abs(y - c[1]) - (h[1] - r)
    qz = np.abs(z - c[2]) - (h[2] - r)
    out = length(np.maximum(qx, 0), np.maximum(qy, 0), np.maximum(qz, 0))
    ins = np.minimum(np.maximum(qx, np.maximum(qy, qz)), 0)
    return out + ins - r


# ---------------------------------------------------------------- 2D
def circle2(u, v, c, r):
    return length(u - c[0], v - c[1]) - r


def ellipse2(u, v, c, r):
    qx, qy = (u - c[0]) / r[0], (v - c[1]) / r[1]
    k0 = length(qx, qy)
    k1 = np.maximum(length(qx / r[0], qy / r[1]), 1e-6)
    return k0 * (k0 - 1.0) / k1


def rrect2(u, v, c, h, r=0.0):
    qx = np.abs(u - c[0]) - (h[0] - r)
    qy = np.abs(v - c[1]) - (h[1] - r)
    return length(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r


def seg2(u, v, a, b, r):
    ax, ay = a
    bx, by = b
    ex, ey = bx - ax, by - ay
    t = np.clip(((u - ax) * ex + (v - ay) * ey) / (ex * ex + ey * ey), 0, 1)
    return length(u - ax - ex * t, v - ay - ey * t) - r


def polyline2(u, v, pts, r):
    d = None
    for a, b in zip(pts[:-1], pts[1:]):
        di = seg2(u, v, a, b, r)
        d = di if d is None else np.minimum(d, di)
    return d


def quad_curve(p0, p1, p2, n=12):
    t = np.linspace(0, 1, n)[:, None]
    p0, p1, p2 = map(np.asarray, (p0, p1, p2))
    return list((1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t * t * p2)


def cross2(u, v, c, half_w, half_l, r=0.4):
    return np.minimum(rrect2(u, v, c, (half_w, half_l), r), rrect2(u, v, c, (half_l, half_w), r))


def tri2(u, v, a, b, c):
    """SDF exata de triangulo 2D (iq)."""
    P = [np.asarray(a, float), np.asarray(b, float), np.asarray(c, float)]
    E = [P[1] - P[0], P[2] - P[1], P[0] - P[2]]
    s = np.sign(E[0][0] * E[2][1] - E[0][1] * E[2][0])
    dmin = None
    smin_ = None
    for Pi, ei in zip(P, E):
        wx, wy = u - Pi[0], v - Pi[1]
        t = np.clip((wx * ei[0] + wy * ei[1]) / (ei @ ei), 0, 1)
        qx, qy = wx - ei[0] * t, wy - ei[1] * t
        dd = qx * qx + qy * qy
        ss = s * (wx * ei[1] - wy * ei[0])
        dmin = dd if dmin is None else np.minimum(dmin, dd)
        smin_ = ss if smin_ is None else np.minimum(smin_, ss)
    return -np.sqrt(dmin) * np.sign(smin_)


# ---------------------------------------------------------------- texto
class Text2D:
    """Campo de distancia 2D (mm) de um texto rasterizado.

    box = (u0, u1, v0, v1): caixa alvo das letras maiusculas (sem acentos).
    ref_text: texto usado para medir a caixa (ex.: 'DO MES' para 'DO MES' com acento).
    """

    def __init__(self, text, font_path, box, ref_text=None, font_px=700, dilate=0.0,
                 keep_aspect=False, open_counters=0.0):
        font = ImageFont.truetype(font_path, font_px)
        ref = ref_text or text
        W = int(font_px * (len(text) + 2) * 0.9)
        H = int(font_px * 2.0)

        def render(t):
            img = Image.new("L", (W, H), 0)
            ImageDraw.Draw(img).text((font_px // 2, font_px // 2), t, font=font, fill=255)
            return np.array(img) > 127

        m = render(text)
        mr = render(ref)
        rows = np.where(mr.any(1))[0]
        cols = np.where(mr.any(0))[0]
        r0, r1, c0, c1 = rows[0], rows[-1] + 1, cols[0], cols[-1] + 1
        u0, u1, v0, v1 = box
        sx = (u1 - u0) / (c1 - c0)
        sy = (v1 - v0) / (r1 - r0)
        if keep_aspect:
            sy = sx
            vc = 0.5 * (v0 + v1)
            v0, v1 = vc - 0.5 * sy * (r1 - r0), vc + 0.5 * sy * (r1 - r0)
        self.sx, self.sy = sx, sy
        self.aspect = sx / sy
        # sdf em pixels anisotropicos -> converter usando escala media (sx~sy)
        pad = 60
        m = np.pad(m, pad)
        r0 += pad; r1 += pad; c0 += pad; c1 += pad
        s = 0.5 * (sx + sy)
        din = ndimage.distance_transform_edt(m, sampling=(sy, sx))
        dout = ndimage.distance_transform_edt(~m, sampling=(sy, sx))
        sdf = (dout - din).astype(np.float32) - dilate
        if open_counters > 0:
            # abre contraformas fechadas (A, P...) para o bico de 0,4 mm
            m2 = sdf < 0
            lab, n = ndimage.label(~m2)
            border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])))
            holes = np.isin(lab, [i for i in range(1, n + 1) if i not in border])
            dh = ndimage.distance_transform_edt(~holes, sampling=(sy, sx))
            m2 = m2 & (dh > open_counters)
            din = ndimage.distance_transform_edt(m2, sampling=(sy, sx))
            dout = ndimage.distance_transform_edt(~m2, sampling=(sy, sx))
            sdf = (dout - din).astype(np.float32)
            m = m2
        self.sdf = sdf
        self.mask = m
        self.c0, self.r1 = c0, r1
        self.u0, self.v0 = u0, v0
        self.box = (u0, u1, v0, v1)
        self.ink_box = self._ink_box()

    def _ink_box(self):
        rows = np.where(self.mask.any(1))[0]
        cols = np.where(self.mask.any(0))[0]
        u = self.u0 + (np.array([cols[0], cols[-1]]) - self.c0) * self.sx
        v = self.v0 + (self.r1 - np.array([rows[-1], rows[0]])) * self.sy
        return (u[0], u[1], v[0], v[1])

    def __call__(self, u, v):
        col = (u - self.u0) / self.sx + self.c0
        row = self.r1 - (v - self.v0) / self.sy
        d = ndimage.map_coordinates(self.sdf, [np.ravel(row), np.ravel(col)], order=1,
                                    mode="nearest")
        return d.reshape(np.shape(u)).astype(np.float32)

    def stroke_stats(self):
        """Largura de traco (mm) amostrada no esqueleto das letras."""
        from skimage.morphology import skeletonize
        inside = self.sdf < 0
        sk = skeletonize(inside)
        w = -2 * self.sdf[sk]
        return float(np.percentile(w, 5)), float(np.median(w)), float(w.min())

    def gap_stats(self):
        """Menor vao interno (contraforma) em mm, via esqueleto do fundo limitado."""
        from skimage.morphology import skeletonize
        outside = self.sdf > 0
        lab, n = ndimage.label(outside)
        # componentes que nao tocam a borda = contraformas fechadas (A, P, O, R...)
        border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])))
        holes = np.isin(lab, [i for i in range(1, n + 1) if i not in border])
        if not holes.any():
            return None
        sk = skeletonize(holes)
        w = 2 * self.sdf[sk]
        return float(np.percentile(w, 5)), float(w.min())
