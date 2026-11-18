"""Escultura procedural do trofeu "CIPEIRO DO MES" (unidade: mm).

As posicoes sao derivadas da imagem de referencia (1536x1024):
  vista frontal  -> X = (px - 340) * S , Z = (985 - py) * S
  vista de perfil-> Y = (px - 812) * S   (personagem olha para -Y)
  S = 200 / 967 mm/px  (base py=985 ate topo do capacete py=18)
A ordem da lista PARTS define prioridade: uma parte anterior "vence" a regiao
compartilhada; as posteriores recebem a cavidade complementar (interfaces coincidentes).
"""
import numpy as np
from sdf import *  # noqa

S = 200.0 / 967.0
fx = lambda px: (px - 340.0) * S
fz = lambda py: (985.0 - py) * S

FONT_BIG = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
FONT_SMALL = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"

MAT = {  # id do material no projeto -> (nome, cor de visualizacao)
    1: ("PLA Verde Medio Masterprint (KRYOU ID 31)", "#2DA84A"),
    2: ("PLA Preto Matte Black Soleyin (KRYOU ID 42)", "#1C1C1C"),
    3: ("PLA Branco GTMax3D (KRYOU ID 02)", "#F4F4F2"),
    4: ("PLA Nude GTMax3D (KRYOU ID 01)", "#E9B994"),
}
GREEN, BLACK, WHITE, NUDE = 1, 2, 3, 4

# ======================================================================= BASE
BZ1 = fz(800)                 # topo do pedestal  (~38.3)
BHX0, BHY0 = 260 * S, 172.5 * S   # meia-largura / meia-profundidade embaixo
BHX1, BHY1 = 217.5 * S, 115 * S   # no topo


def base_sdf(x, y, z):
    d = np.maximum(-z, z - BZ1)
    for coord, h0, h1 in ((x, BHX0, BHX1), (y, BHY0, BHY1)):
        L = np.hypot(BZ1, h0 - h1)
        d = smax(d, (np.abs(coord) * BZ1 + (h0 - h1) * z - h0 * BZ1) / L, 0.8)
    return np.maximum(d, np.maximum(-z, z - BZ1))


_LF = np.hypot(BZ1, BHY0 - BHY1)
FN = np.array([0.0, -BZ1, BHY0 - BHY1]) / _LF          # normal da face frontal
FT = np.array([0.0, BHY0 - BHY1, BZ1]) / _LF           # direcao "para cima" na face


def face_coords(x, y, z):
    """(u, v, w) na face frontal inclinada: u=X, v=ao longo da face, w=altura sobre a face."""
    py_, pz_ = y + BHY0, z
    w = py_ * FN[1] + pz_ * FN[2]
    v = py_ * FT[1] + pz_ * FT[2]
    return x, v, w


VK = _LF / BZ1   # converte Z da vista frontal -> v na face


def vz(py):
    return fz(py) * VK


TXT_CIPEIRO = Text2D("CIPEIRO", FONT_BIG, (fx(258), fx(510), vz(906), vz(856)))
TXT_DOMES = Text2D("DO MÊS", FONT_BIG, (fx(287), fx(500), vz(966), vz(925)), ref_text="DO MES")
EMB_C = (fx(195), vz(905))
EMB_R = 55 * S


def letreiro_cipeiro(x, y, z):
    u, v, w = face_coords(x, y, z)
    return np.maximum(TXT_CIPEIRO(u, v), band(w, -0.6, 0.8))


def letreiro_domes(x, y, z):
    u, v, w = face_coords(x, y, z)
    vm = vz(945)
    d = TXT_DOMES(u, v)
    d = np.minimum(d, rrect2(u, v, (fx(268), vm), (0.5 * 27 * S, 0.95), 0.4))   # traco esq.
    d = np.minimum(d, rrect2(u, v, (fx(525), vm), (0.5 * 40 * S, 0.95), 0.4))   # traco dir.
    return np.maximum(d, band(w, -0.6, 0.8))


def emblema_base_circ(x, y, z):
    u, v, w = face_coords(x, y, z)
    disc = np.maximum(circle2(u, v, EMB_C, EMB_R), band(w, -0.6, 0.8))
    ring = np.maximum(np.abs(circle2(u, v, EMB_C, EMB_R - 0.9)) - 0.9, band(w, 0.0, 1.3))
    return np.minimum(disc, ring)


def emblema_base_cruz(x, y, z):
    u, v, w = face_coords(x, y, z)
    return np.maximum(cross2(u, v, EMB_C, 2.7, 7.3, 0.7), band(w, 0.2, 1.5))


# ======================================================================= CABECA
HCX, HCY, HCZ = fx(312), -7.0, 166.5      # centro da cabeca (rosto)
HRX, HRY, HRZ = 19.0, 14.0, 18.5


def head_base(x, y, z):
    cran = ellipsoid(x, y, z, (HCX, HCY, HCZ), (HRX, HRY, HRZ))
    jaw = ellipsoid(x, y, z, (HCX, -10.6, 156.6), (15.6, 11.0, 9.0))
    d = smin(cran, jaw, 5.0)
    for sx in (-1, 1):
        d = smin(d, ellipsoid(x, y, z, (HCX + sx * 9.6, -13.6, 157.6), (7.4, 7.0, 6.4)), 3.0)
    return d


# mapeamento cilindrico -> "x frontal equivalente" s (corrige a projecao da vista frontal)
_th = np.linspace(0, np.pi, 2001)
_r = HRX * HRY / np.sqrt((HRY * np.sin(_th)) ** 2 + (HRX * np.cos(_th)) ** 2)
_s = _r * np.sin(_th)
_k = np.searchsorted(_th, np.radians(72))
_slope = (_s[_k] - _s[_k - 5]) / (_th[_k] - _th[_k - 5])
_s[_k:] = _s[_k] + np.maximum(_slope, 6.0) * (_th[_k:] - _th[_k])


def head_s(x, y):
    th = np.arctan2(x - HCX, -(y - HCY))
    return np.sign(th) * np.interp(np.abs(th), _th, _s), th


def fs(px):
    return (px - 312.0) * S


def face_decal(shape2d, lo, hi):
    def f(x, y, z):
        s, th = head_s(x, y)
        d = np.maximum(shape2d(s, z), band(head_base(x, y, z), lo, hi))
        return np.maximum(d, (np.abs(th) - np.radians(115)) * 10)
    return f


# --- olhos / oculos (coordenadas s,z em mm)
EYE_Z = fz(173)
LENS = [(fs(260.5), fz(172.5)), (fs(365.5), fz(172.5))]
LENS_H = (9.7, 5.6)


def glasses2d(s, z):
    d = None
    for c in LENS:
        outer = rrect2(s, z, c, LENS_H, 3.6)
        inner = rrect2(s, z, c, (LENS_H[0] - 1.8, LENS_H[1] - 1.8), 2.0)
        ring = np.maximum(outer, -inner)
        d = ring if d is None else np.minimum(d, ring)
    d = np.minimum(d, rrect2(s, z, (0.2, LENS[0][1] + 1.6), (2.2, 1.1), 0.5))   # ponte
    for sg in (-1, 1):                                                         # hastes
        d = np.minimum(d, rrect2(s, z, (sg * 24.5, LENS[0][1] + 3.6), (5.0, 1.0), 0.5))
    return d


def eyes2d(s, z):
    return np.minimum(ellipse2(s, z, (fs(262), EYE_Z), (4.7, 4.0)),
                      ellipse2(s, z, (fs(362), EYE_Z), (4.7, 4.0)))


PUP = [(fs(268), fz(180)), (fs(353), fz(180))]


def pupils2d(s, z):
    return np.minimum(circle2(s, z, PUP[0], 2.3), circle2(s, z, PUP[1], 2.3))


def highlights2d(s, z):
    return np.minimum(circle2(s, z, (PUP[0][0] + 0.75, PUP[0][1] + 0.85), 0.8),
                      circle2(s, z, (PUP[1][0] + 0.75, PUP[1][1] + 0.85), 0.8))


def brows2d(s, z):
    zb = fz(148)
    L = polyline2(s, z, quad_curve((fs(232), zb - 0.6), (fs(262), zb + 1.7), (fs(292), zb + 0.1)), 1.0)
    R = polyline2(s, z, quad_curve((fs(332), zb + 0.1), (fs(362), zb + 1.7), (fs(392), zb - 0.6)), 1.0)
    return np.minimum(L, R)


MZ_TOP = fz(206)


def mouth2d(s, z):
    sc = fs(311)
    top = z - (MZ_TOP + 0.022 * (s - sc) ** 2)
    ell = ellipse2(s, z, (sc, MZ_TOP + 0.3), (9.4, 9.4))
    return smax(ell, top, 0.8)


def teeth2d(s, z):
    sc = fs(311)
    return np.maximum(mouth2d(s, z) + 0.15, (MZ_TOP - 2.6 + 0.022 * (s - sc) ** 2) - z)


def nose(x, y, z):
    return ellipsoid(x, y, z, (HCX + 0.3, -21.2, fz(195) + 0.4), (3.5, 2.7, 2.9))


def neck(x, y, z):
    return capsule(x, y, z, (HCX + 2.4, -5.5, 139.0), (HCX + 1.4, -7.5, 153.0), 6.4)


def mouth_carve(x, y, z):
    s, th = head_s(x, y)
    return np.maximum(np.maximum(mouth2d(s, z), -(head_base(x, y, z) + 1.7)), y - HCY)


def pele_rosto(x, y, z):
    d = smin(head_base(x, y, z), neck(x, y, z), 3.0)
    d = smin(d, nose(x, y, z), 1.3)
    return np.maximum(d, -mouth_carve(x, y, z))


olhos_brancos = face_decal(eyes2d, -0.9, 0.9)
pupilas = face_decal(pupils2d, -0.9, 1.2)
brilho = face_decal(highlights2d, -0.9, 1.45)
armacao = face_decal(glasses2d, -1.0, 2.1)
sobrancelhas = face_decal(brows2d, -0.8, 1.5)


def boca_interior(x, y, z):
    s, th = head_s(x, y)
    return np.maximum(np.maximum(mouth2d(s, z), band(head_base(x, y, z), -3.2, -1.6)), y - HCY)


def dentes(x, y, z):
    s, th = head_s(x, y)
    return np.maximum(np.maximum(teeth2d(s, z), band(head_base(x, y, z), -3.2, -0.55)), y - HCY)


def cabelo(x, y, z):
    s, th = head_s(x, y)
    hair = ellipsoid(x, y, z, (HCX, -5.8, 170.0), (20.4, 16.4, 14.6))
    hair = smax(hair, 159.5 - z, 1.0)
    side = (np.radians(60) - np.abs(th)) * 12.0
    return smax(hair, side, 0.8)


# --- capacete
CXH, CYH, ZR = HCX + 1.0, -6.0, 175.4
HXR, HYR, HZR = 21.6, 17.2, 24.7


def capacete(x, y, z):
    dome = ellipsoid(x, y, z, (CXH, CYH, ZR - 0.2), (HXR, HYR, HZR))
    dome = np.maximum(dome, ZR - z)
    rim = np.maximum(ellipse2(x, y, (CXH, CYH), (HXR + 1.5, HYR + 1.5)), np.abs(z - (ZR + 1.0)) - 1.0)
    visor = ellipse2(x, y, (CXH, CYH - 2.0), (HXR * 0.78, HYR + 5.6))
    visor = np.maximum(visor, (y - (CYH - 7.0)))
    visor = np.maximum(visor, np.abs(z - (ZR + 1.15)) - 1.15)
    d = smin(dome, rim, 1.0)
    d = smin(d, visor, 1.0)
    # relevos moldados: nervura central e duas laterais
    shell = band(dome, -1.0, 1.2)
    rib_c = np.maximum(np.abs(x - CXH) - 1.6, shell)
    rib_c = np.maximum(rib_c, -(y - (CYH - 9.0)) - 0.0)
    rib_c = np.maximum(rib_c, (ZR + 9.0) - z)
    d = np.minimum(d, rib_c)
    for sg in (-1, 1):
        rib = np.maximum(np.abs(x - (CXH + sg * 9.0)) - 1.0, band(dome, -1.0, 0.8))
        rib = np.maximum(rib, (ZR + 14.0) - z)
        d = np.minimum(d, rib)
    return d


def helmet_dome(x, y, z):
    return ellipsoid(x, y, z, (CXH, CYH, ZR - 0.2), (HXR, HYR, HZR))


HEMB_C = (CXH + 2.0, fz(52))
TXT_CIPAA_H = Text2D("CIPAA", FONT_SMALL, (CXH + 2.0 - 9.0, CXH + 2.0 + 9.0, fz(100), fz(76)),
                     dilate=0.04, open_counters=0.22)


def emb_cap_circ(x, y, z):
    d = np.maximum(circle2(x, z, HEMB_C, 5.5), band(helmet_dome(x, y, z), -0.6, 0.6))
    return np.maximum(d, y - (CYH - 6.0))


def emb_cap_cruz(x, y, z):
    d = np.maximum(cross2(x, z, HEMB_C, 1.35, 3.8, 0.35), band(helmet_dome(x, y, z), -0.2, 1.1))
    return np.maximum(d, y - (CYH - 6.0))


def txt_cap(x, y, z):
    d = np.maximum(TXT_CIPAA_H(x, z), band(helmet_dome(x, y, z), -0.6, 0.6))
    return np.maximum(d, y - (CYH - 6.0))


# --- abafadores
CUP_Z, CUP_Y = 168.4, -0.6
CUP_X = [HCX - 24.4, HCX + 24.4]


def rcyl_x(x, y, z, cx, cy, cz, ry, rz, hx, r):
    a = ellipse2(y, z, (cy, cz), (ry, rz)) + r
    b = np.abs(x - cx) - hx + r
    return length(np.maximum(a, 0), np.maximum(b, 0)) + np.minimum(np.maximum(a, b), 0) - r


def conchas(x, y, z):
    d = None
    for cx in CUP_X:
        di = rcyl_x(x, y, z, cx, CUP_Y, CUP_Z, 7.6, 11.6, 3.9, 1.8)
        d = di if d is None else np.minimum(d, di)
    return d


def almofadas(x, y, z):
    d = None
    for sg, cx in zip((-1, 1), CUP_X):
        di = rcyl_x(x, y, z, cx - sg * 5.1, CUP_Y, CUP_Z, 6.9, 10.9, 1.9, 1.0)
        d = di if d is None else np.minimum(d, di)
    return d


def suportes(x, y, z):
    d = None
    for sg, cx in zip((-1, 1), CUP_X):
        arm = rbox(x, y, z, (cx + sg * 0.6, CUP_Y, CUP_Z + 11.8), (2.4, 2.6, 2.6), 0.8)
        slot = rbox(x, y, z, (CXH + sg * (HXR - 0.6), CUP_Y, ZR + 4.3), (2.0, 3.6, 3.3), 0.8)
        pivot = capsule(x, y, z, (cx + sg * 0.6, CUP_Y, CUP_Z + 11.8), (CXH + sg * (HXR - 0.6), CUP_Y, ZR + 4.3), 2.0)
        di = np.minimum(np.minimum(arm, slot), pivot)
        d = di if d is None else np.minimum(d, di)
    return d


# ======================================================================= TRONCO
TCX = -1.5


def torso(x, y, z):
    chest = ellipsoid(x, y, z, (TCX, -5.0, 132.0), (21.5, 11.0, 14.5))
    waist = ellipsoid(x, y, z, (TCX, -4.5, 113.0), (18.5, 10.2, 12.5))
    d = smin(chest, waist, 6.0)
    for sg in (-1, 1):
        d = smin(d, sphere(x, y, z, (TCX + sg * 18.6, -4.2, 138.4), 7.4), 4.0)
    return d


def waist_sdf(x, y, z):
    waist = ellipsoid(x, y, z, (TCX, -4.5, 113.0), (18.5, 10.2, 12.5))
    hip = ellipsoid(x, y, z, (TCX, -4.6, 99.0), (19.0, 10.8, 8.6))
    return smin(waist, hip, 4.0)


NECK_C = (HCX + 2.4, -5.5)

# bracos: ombro, cotovelo, punho
SH_R = np.array([TCX - 19.0, -4.5, 138.6])
EL_R = np.array([fx(165), -9.0, fz(328)])
WR_R = np.array([fx(148), -18.5, fz(238)])
SH_L = np.array([TCX + 19.0, -4.5, 138.6])
EL_L = np.array([fx(470), -2.5, fz(386)])
WR_L = np.array([fx(432), -9.5, fz(430)])
SLEEVE_R = SH_R + 0.80 * (EL_R - SH_R)
SLEEVE_L = SH_L + 0.70 * (EL_L - SH_L)


def sleeves(x, y, z):
    d = None
    for sh, end in ((SH_R, SLEEVE_R), (SH_L, SLEEVE_L)):
        t, L = axis_t(x, y, z, sh, end)
        c = capsule(x, y, z, sh - 0.25 * (end - sh), end, 7.2, 6.6)
        c = np.maximum(c, t - L)                      # punho reto
        cuff = np.maximum(capsule(x, y, z, sh, end, 7.6, 7.0), np.abs(t - (L - 0.9)) - 0.9)
        c = np.minimum(c, np.maximum(cuff, t - L))
        d = c if d is None else np.minimum(d, c)
    return d


def camisa(x, y, z):
    d = torso(x, y, z)
    d = smin(d, sleeves(x, y, z), 2.5)
    d = np.maximum(d, 102.6 - z)
    # gola polo
    rn = length(x - NECK_C[0], y - NECK_C[1])
    thn = np.arctan2(x - NECK_C[0], -(y - NECK_C[1]))
    ztop = 146.3 + 2.4 * (1 - np.cos(thn)) * 0.5
    collar = np.maximum(np.abs(rn - 7.2) - 1.1, np.maximum(142.0 - z, z - ztop))
    opening = np.maximum(np.abs(x - NECK_C[0]) - 1.3, y - NECK_C[1])
    collar = np.maximum(collar, -opening)
    d = np.minimum(d, collar)
    tor = torso(x, y, z)
    fr = y - (-5.0)
    lap = None
    for sg in (-1, 1):
        t2 = tri2(x, z, (NECK_C[0] + sg * 1.0, 146.6), (NECK_C[0] + sg * 8.6, 145.6), (NECK_C[0] + sg * 3.6, 139.6))
        lap_i = np.maximum(t2 - 0.4, band(tor, -0.6, 1.1))
        lap = lap_i if lap is None else np.minimum(lap, lap_i)
    d = np.minimum(d, np.maximum(lap, fr))
    plk = np.maximum(rrect2(x, z, (NECK_C[0] - 0.2, 139.6), (1.7, 5.6), 0.5), band(tor, -0.6, 0.55))
    btn = np.minimum(circle2(x, z, (NECK_C[0] - 0.2, 141.8), 0.95), circle2(x, z, (NECK_C[0] - 0.2, 137.4), 0.95))
    btn = np.maximum(btn, band(tor, -0.6, 1.05))
    d = np.minimum(d, np.maximum(np.minimum(plk, btn), fr))
    return d


CHEST_C = (fx(383), fz(350))
TXT_CIPAA_P = Text2D("CIPAA", FONT_SMALL, (fx(347), fx(414), fz(398), fz(375)), dilate=0.05,
                     open_counters=0.22)


def _front(y):
    return y - (-5.0)


def emb_peito_circ(x, y, z):
    return np.maximum(np.maximum(circle2(x, z, CHEST_C, 4.6), band(torso(x, y, z), -0.5, 0.6)), _front(y))


def emb_peito_cruz(x, y, z):
    return np.maximum(np.maximum(cross2(x, z, CHEST_C, 1.05, 3.25, 0.3), band(torso(x, y, z), -0.5, 0.9)), _front(y))


def txt_peito(x, y, z):
    return np.maximum(np.maximum(TXT_CIPAA_P(x, z), band(torso(x, y, z), -0.5, 0.6)), _front(y))


# ======================================================================= BRACOS / MAOS
def hand_v(x, y, z):
    H = (fx(141), -21.0, fz(205))
    fist = rbox(x, y, z, H, (6.9, 4.7, 5.6), 3.0)
    thumb = capsule(x, y, z, (H[0] + 6.0, -22.0, H[2] - 3.4), (H[0] - 2.6, -25.6, H[2] - 1.2), 2.25, 2.0)
    curl = np.minimum(capsule(x, y, z, (H[0] - 5.2, -24.0, H[2] + 2.0), (H[0] + 0.5, -24.6, H[2] + 2.2), 2.1),
                      capsule(x, y, z, (H[0] - 5.0, -24.0, H[2] - 1.6), (H[0] + 0.5, -24.6, H[2] - 1.0), 2.0))
    d = smin(fist, curl, 1.0)
    d = smin(d, thumb, 0.8)
    zroot = H[2] + 3.6
    f1 = capsule(x, y, z, (H[0] - 3.6, -21.2, zroot), (fx(118), -21.6, fz(108)), 2.95, 2.55)
    f2 = capsule(x, y, z, (H[0] + 3.6, -21.2, zroot), (fx(169), -21.6, fz(112)), 2.95, 2.55)
    d = smin(d, f1, 1.6)
    d = smin(d, f2, 1.6)
    return d


def hand_hip(x, y, z):
    H = WR_L + np.array([-1.8, -1.6, -4.4])
    fist = rbox(x, y, z, H, (4.4, 5.2, 5.4), 2.6)
    knuck = capsule(x, y, z, (H[0] - 1.0, H[1] - 4.6, H[2] + 3.0), (H[0] - 1.0, H[1] - 4.8, H[2] - 3.4), 2.2)
    thumb = capsule(x, y, z, (H[0] + 1.0, H[1] - 3.0, H[2] + 4.2), (H[0] - 2.8, H[1] - 6.2, H[2] + 1.8), 2.0)
    return smin(smin(fist, knuck, 1.2), thumb, 0.8)


def pele_bracos(x, y, z):
    d = None
    for sh, el, wr, slv in ((SH_R, EL_R, WR_R, SLEEVE_R), (SH_L, EL_L, WR_L, SLEEVE_L)):
        upper = capsule(x, y, z, sh, el, 5.5, 5.4)
        fore = capsule(x, y, z, el, wr, 5.7, 4.7)
        arm = smin(upper, fore, 1.5)
        t, L = axis_t(x, y, z, sh, slv)
        arm = np.maximum(arm, (L - 2.0) - t)      # pele so a partir de 2 mm dentro da manga
        d = arm if d is None else np.minimum(d, arm)
    d = smin(d, hand_v(x, y, z), 1.6)
    d = smin(d, hand_hip(x, y, z), 1.6)
    return d


# ======================================================================= CINTURA / PERNAS
def cinto(x, y, z):
    return np.maximum(band(waist_sdf(x, y, z), -1.5, 1.0), np.abs(z - 103.6) - 3.0)


def fivela(x, y, z):
    c = (fx(332), 103.6)
    fr = np.maximum(rrect2(x, z, c, (4.6, 3.1), 1.0), -rrect2(x, z, c, (2.35, 1.0), 0.4))
    return np.maximum(np.maximum(fr, band(waist_sdf(x, y, z), -0.5, 2.0)), y - (-5))


HIP_J = [np.array([TCX - 9.8, -5.0, 96.0]), np.array([TCX + 9.8, -5.0, 96.0])]
ANK = [np.array([TCX - 22.2, -6.5, 57.0]), np.array([TCX + 21.6, -6.5, 57.0])]


def legs(x, y, z):
    d = None
    for h, a in zip(HIP_J, ANK):
        di = capsule(x, y, z, h, a, 11.0, 10.2)
        d = di if d is None else np.minimum(d, di)
    return d


def calca(x, y, z):
    hip = ellipsoid(x, y, z, (TCX, -4.6, 99.0), (19.0, 10.8, 8.6))
    waist = ellipsoid(x, y, z, (TCX, -4.5, 113.0), (18.5, 10.2, 12.5))
    top = np.maximum(smin(hip, waist, 4.0), z - 104.6)
    d = smin(top, legs(x, y, z), 3.0)
    d = np.maximum(d, 55.0 - z)
    # bolsos cargo nas laterais das coxas
    for sg, h, a in zip((-1, 1), HIP_J, ANK):
        t = 0.44
        c = h + t * (a - h)
        cx = c[0] + sg * 10.4
        pocket = rbox(x, y, z, (cx, c[1] - 0.5, c[2] - 1.0), (1.9, 5.3, 6.4), 1.2)
        flap = rbox(x, y, z, (cx + sg * 0.5, c[1] - 0.5, c[2] + 5.4), (1.8, 5.8, 1.3), 0.6)
        d = np.minimum(d, np.minimum(pocket, flap))
    return d


def faixas(x, y, z):
    return np.maximum(band(legs(x, y, z), -1.2, 0.45), np.abs(z - 63.8) - 2.1)


def botas(x, y, z):
    d = None
    for sg, a in zip((-1, 1), ANK):
        bx, by = a[0] + sg * 1.4, -8.0
        xr, yr = rot_z(x, y, (bx, by), sg * 8.0)
        sole = rbox(xr, yr, z, (bx, by - 2.4, BZ1 + 1.6), (11.6, 15.8, 2.2), 1.6)
        toe = ellipsoid(xr, yr, z, (bx, by - 9.0, BZ1 + 6.0), (11.4, 9.6, 6.6))
        heel = ellipsoid(xr, yr, z, (bx, by + 4.6, BZ1 + 8.4), (11.0, 9.4, 9.2))
        shaft = capsule(xr, yr, z, (bx, by + 1.0, BZ1 + 8.0), (a[0], a[1], 60.0), 9.6, 9.4)
        up = smin(smin(toe, heel, 4.0), shaft, 3.0)
        up = np.maximum(up, BZ1 + 2.6 - z)
        b = smin(sole, up, 0.6)
        # sulco da sola
        groove = np.maximum(np.abs(z - (BZ1 + 1.8)) - 0.38, -(sole + 0.65))
        b = np.maximum(b, -groove)
        # cadarcos
        for k in range(3):
            lz = BZ1 + 9.0 + k * 2.6
            lace = capsule(xr, yr, z, (bx - 3.2, by - 9.0 + k * 1.9, lz), (bx + 3.2, by - 9.0 + k * 1.9, lz), 0.75)
            b = np.minimum(b, np.maximum(lace, band(up, -0.8, 0.7)))
        b = np.maximum(b, BZ1 - 0.4 - z)
        d = b if d is None else np.minimum(d, b)
    return d


# ======================================================================= CAPA
CAPE_TOP, CAPE_HEM = 143.5, fz(690)


def capa(x, y, z):
    t = np.clip((CAPE_TOP - z) / (CAPE_TOP - CAPE_HEM), 0.0, 1.0)
    cx = -3.5 - 3.0 * t
    cy = -4.6 + 3.2 * t
    a = 21.5 + 33.0 * t ** 0.7
    b = 11.6 + 15.0 * t
    dx, dy = x - cx, y - cy
    phi = np.arctan2(dx / a, dy / b)
    rn = np.maximum(length(dx / a, dy / b), 1e-4)
    n, ph = 7.0, 0.6
    A = 0.075 * t ** 1.3
    Rn = 1.0 + A * np.sin(n * phi + ph)
    g = length(dx / a ** 2, dy / b ** 2) / rn
    gphi = 1.0 / (rn * 0.5 * (a + b))
    G = np.sqrt(g ** 2 + (A * n * np.cos(n * phi + ph) * gphi) ** 2)
    sheet = np.abs((rn - Rn) / G) - 1.1
    sheet = np.maximum(sheet, 0.5 - rn)
    phimax = np.radians(80.0 + 14.0 * t)
    edge = (np.abs(phi) - phimax) * length(dx, dy)
    zhem = CAPE_HEM + 5.5 * (np.abs(phi) / phimax) ** 2 + 1.0 * np.sin(n * phi + ph + 1.2)
    d = np.maximum(sheet, edge)
    d = smax(d, zhem - z, 0.8)
    d = smax(d, z - CAPE_TOP, 2.0)
    return d


# ======================================================================= LISTA DE PARTES
# (nome, material, funcao sdf, resolucao de malha em mm)
PARTS = [
    ("Brilho_Olhos", WHITE, brilho, 0.10),
    ("Pupilas", BLACK, pupilas, 0.10),
    ("Armacao_Oculos", BLACK, armacao, 0.12),
    ("Olhos_Brancos", WHITE, olhos_brancos, 0.12),
    ("Sobrancelhas", BLACK, sobrancelhas, 0.12),
    ("Dentes", WHITE, dentes, 0.12),
    ("Boca_Interior", BLACK, boca_interior, 0.12),
    ("Emblema_Capacete_Cruz", WHITE, emb_cap_cruz, 0.10),
    ("Emblema_Capacete_Circulo", GREEN, emb_cap_circ, 0.12),
    ("Texto_CIPAA_Capacete", GREEN, txt_cap, 0.08),
    ("Capacete", WHITE, capacete, 0.2),
    ("Suportes_Abafadores", BLACK, suportes, 0.15),
    ("Conchas_Abafadores", GREEN, conchas, 0.18),
    ("Almofadas_Abafadores", BLACK, almofadas, 0.15),
    ("Cabelo", BLACK, cabelo, 0.18),
    ("Pele_Rosto", NUDE, pele_rosto, 0.15),
    ("Emblema_Peito_Cruz", GREEN, emb_peito_cruz, 0.08),
    ("Emblema_Peito_Circulo", WHITE, emb_peito_circ, 0.10),
    ("Texto_CIPAA_Peito", WHITE, txt_peito, 0.07),
    ("Pele_Bracos_Maos", NUDE, pele_bracos, 0.15),
    ("Fivela", WHITE, fivela, 0.12),
    ("Cinto", BLACK, cinto, 0.18),
    ("Camisa", GREEN, camisa, 0.2),
    ("Capa", GREEN, capa, 0.22),
    ("Faixas_Calca", WHITE, faixas, 0.18),
    ("Calca", BLACK, calca, 0.22),
    ("Botas", BLACK, botas, 0.2),
    ("Emblema_Base_Cruz", WHITE, emblema_base_cruz, 0.12),
    ("Emblema_Base_Circulo", GREEN, emblema_base_circ, 0.15),
    ("Letreiro_CIPEIRO", WHITE, letreiro_cipeiro, 0.12),
    ("Letreiro_DO_MES", GREEN, letreiro_domes, 0.12),
    ("Base", BLACK, base_sdf, 0.3),
]
