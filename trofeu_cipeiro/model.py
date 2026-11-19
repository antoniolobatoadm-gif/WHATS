"""Escultura procedural do trofeu "CIPEIRO DO MES" (unidade: mm).

As posicoes sao derivadas da imagem de referencia (1536x1024):
  vista frontal  -> X = (px - 340) * S , Z = (985 - py) * S
  vista de perfil-> Y = (px - 812) * S   (personagem olha para -Y)
  S = 200 / 967 mm/px  (escala normalizada para 200 mm na exportacao)
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

MAT = {  # id do material no projeto -> (nome, cor de visualizacao). Cabecote: T(id-1)
    1: ("T0 Verde - PLA Verde Medio Masterprint (KRYOU ID 31)", "#22B33A"),
    2: ("T1 Branco - PLA Branco GTMax3D (KRYOU ID 02)", "#F4F4F2"),
    3: ("T2 Preto - PLA Preto Matte Black Soleyin (KRYOU ID 42)", "#1C1C1C"),
    4: ("T3 Pele - PLA Nude GTMax3D (KRYOU ID 01)", "#F0B489"),
}
GREEN, WHITE, BLACK, NUDE = 1, 2, 3, 4

# ======================================================================= BASE
BZ1 = fz(800)                 # topo do pedestal  (~38.3)
# referencia: base centrada em px 330,3 (frente) e px 800,5 (perfil);
# 106,6 x 66 mm embaixo, ~86 x 42 mm no topo
BXC, BYC = fx(330.3), (800.5 - 812.0) * S
BHX0, BHY0 = 53.3, 33.0      # meia-largura / meia-profundidade embaixo
BHX1, BHY1 = 43.0, 21.2      # no topo


def base_sdf(x, y, z):
    d = np.maximum(-z, z - BZ1)
    for coord, h0, h1 in ((x - BXC, BHX0, BHX1), (y - BYC, BHY0, BHY1)):
        L = np.hypot(BZ1, h0 - h1)
        d = smax(d, (np.abs(coord) * BZ1 + (h0 - h1) * z - h0 * BZ1) / L, 0.8)
    return np.maximum(d, np.maximum(-z, z - BZ1))


_LF = np.hypot(BZ1, BHY0 - BHY1)
FN = np.array([0.0, -BZ1, BHY0 - BHY1]) / _LF          # normal da face frontal
FT = np.array([0.0, BHY0 - BHY1, BZ1]) / _LF           # direcao "para cima" na face


def face_coords(x, y, z):
    """(u, v, w) na face frontal inclinada: u=X, v=ao longo da face, w=altura sobre a face."""
    py_, pz_ = (y - BYC) + BHY0, z
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
# Medidas da vista frontal (px) relativas ao eixo do rosto em px 336 (centro do nariz,
# da boca e do capacete na referencia). Profundidade (Y) medida na vista de perfil.
HCX, HCY, HCZ = fx(336), -3.0, 167.0      # centro da cabeca
HRX, HRY, HRZ = 16.0, 17.0, 19.0


def head_base(x, y, z):
    cran = ellipsoid(x, y, z, (HCX, HCY, HCZ), (HRX, HRY, HRZ))
    jaw = ellipsoid(x, y, z, (HCX, HCY - 4.2, 156.4), (14.6, 12.6, 9.4))
    d = smin(cran, jaw, 5.0)
    for sx in (-1, 1):                     # bochechas volumosas
        d = smin(d, ellipsoid(x, y, z, (HCX + sx * 8.4, HCY - 10.6, 157.8), (6.6, 6.4, 6.0)), 3.0)
    d = smin(d, ellipsoid(x, y, z, (HCX, HCY - 11.2, 150.6), (6.2, 5.6, 4.6)), 2.5)   # queixo
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
    return (px - 336.0) * S


def face_decal(shape2d, lo, hi):
    def f(x, y, z):
        s, th = head_s(x, y)
        d = np.maximum(shape2d(s, z), band(head_base(x, y, z), lo, hi))
        return np.maximum(d, (np.abs(th) - np.radians(115)) * 10)
    return f


# --- olhos / oculos (coordenadas s,z em mm) -- medidas da referencia:
# aros: x 255-335 / 347-418, y 142-198 ; brancos dos olhos: x 280-313 / 353-388, y 155-187
# pupilas: (302,173) e (367,173) r=12 px ; sobrancelhas y 130-140 ; nariz (334,200)
EYE_Z = fz(171)
LENS = [(fs(294), fz(170)), (fs(382), fz(170))]
LENS_H = (8.1, 5.9)          # meia largura / meia altura externas do aro
FRAME_T = 1.75               # espessura de face do aro (>= 4 linhas de 0,42 mm)


def glasses2d(s, z):
    d = None
    for c in LENS:
        outer = rrect2(s, z, c, LENS_H, 3.4)
        inner = rrect2(s, z, c, (LENS_H[0] - FRAME_T, LENS_H[1] - FRAME_T), 2.0)
        ring = np.maximum(outer, -inner)
        d = ring if d is None else np.minimum(d, ring)
    d = np.minimum(d, rrect2(s, z, (0.5 * (LENS[0][0] + LENS[1][0]), LENS[0][1] + 3.2), (2.6, 1.15), 0.5))  # ponte
    for sg in (-1, 1):                                                         # hastes
        d = np.minimum(d, rrect2(s, z, (sg * 21.5, LENS[0][1] + 3.4), (4.8, 0.95), 0.45))
    return d


EYES = [(fs(296.5), EYE_Z), (fs(370.5), EYE_Z)]


def eyes2d(s, z):
    return np.minimum(ellipse2(s, z, EYES[0], (3.75, 3.55)), ellipse2(s, z, EYES[1], (3.75, 3.55)))


PUP = [(fs(302), fz(173)), (fs(367), fz(173))]


def pupils2d(s, z):
    return np.minimum(circle2(s, z, PUP[0], 2.35), circle2(s, z, PUP[1], 2.35))


def highlights2d(s, z):
    return np.minimum(circle2(s, z, (PUP[0][0] - 0.8, PUP[0][1] + 0.9), 0.7),
                      circle2(s, z, (PUP[1][0] - 0.8, PUP[1][1] + 0.9), 0.7))


def brows2d(s, z):
    L = polyline2(s, z, quad_curve((fs(278), fz(140)), (fs(296), fz(127)), (fs(316), fz(136))), 1.05)
    R = polyline2(s, z, quad_curve((fs(356), fz(136)), (fs(376), fz(127)), (fs(398), fz(140))), 1.05)
    return np.minimum(L, R)


# --- sorriso aberto: x 290-378 ; borda superior y 217 (cantos y 213) ; fundo y 252
MZ_TOP = fz(217)
M_HW = 9.0
M_K = 0.85 / M_HW ** 2


def _mouth_top(s):
    return MZ_TOP + M_K * s ** 2


def mouth2d(s, z):
    sc = fs(334)
    top = z - _mouth_top(s - sc)
    zc = _mouth_top(M_HW)              # altura dos cantos
    low = ellipse2(s, z, (sc, zc), (M_HW, zc - fz(252)))
    return smax(low, top, 0.6)


def teeth2d(s, z):
    sc = fs(334)
    return np.maximum(mouth2d(s, z) + 0.15, (_mouth_top(s - sc) - (fz(217) - fz(237))) - z)


def nose(x, y, z):
    return ellipsoid(x, y, z, (HCX - 0.3, HCY - HRY - 0.6, fz(200)), (3.6, 3.0, 2.6))


NECK_C = (fx(336), -5.5)


def neck(x, y, z):
    return capsule(x, y, z, (NECK_C[0], NECK_C[1], 139.0), (HCX, -5.0, 154.0), 6.6)


def mouth_carve(x, y, z):
    s, th = head_s(x, y)
    return np.maximum(np.maximum(mouth2d(s, z), -(head_base(x, y, z) + 1.9)), y - HCY)


def pele_rosto(x, y, z):
    d = smin(head_base(x, y, z), neck(x, y, z), 3.0)
    d = smin(d, nose(x, y, z), 1.4)
    return np.maximum(d, -mouth_carve(x, y, z))


olhos_brancos = face_decal(eyes2d, -0.9, 0.95)
pupilas = face_decal(pupils2d, -0.9, 1.25)
brilho = face_decal(highlights2d, -0.9, 1.5)
armacao = face_decal(glasses2d, -1.0, 2.2)
sobrancelhas = face_decal(brows2d, -0.8, 1.6)


def boca_interior(x, y, z):
    s, th = head_s(x, y)
    return np.maximum(np.maximum(mouth2d(s, z), band(head_base(x, y, z), -3.4, -1.8)), y - HCY)


def dentes(x, y, z):
    s, th = head_s(x, y)
    return np.maximum(np.maximum(teeth2d(s, z), band(head_base(x, y, z), -3.4, -0.6)), y - HCY)


def cabelo(x, y, z):
    s, th = head_s(x, y)
    hair = ellipsoid(x, y, z, (HCX, HCY + 1.6, 170.0), (17.4, 18.6, 15.8))
    # nuca: o cabelo desce mais atras (vista de perfil, y ~250 px)
    zcut = 160.0 - 7.0 * np.clip((y - HCY) / HRY, 0.0, 1.0)
    hair = smax(hair, zcut - z, 1.0)
    side = (np.radians(62) - np.abs(th)) * 12.0
    return smax(hair, side, 0.8)


# --- capacete: largura 225-450 px na frente ; perfil: aba frontal em px 680, nuca em px 935,
# topo em py 10 ; aba mais baixa atras -> casco inclinado ~8 graus para tras.
CXH, CYH, ZR = fx(334), -0.6, 176.0
HXR, HYR, HZR = 19.6, 21.6, 25.0
TILT = np.radians(8.0)
_CT, _ST = np.cos(TILT), np.sin(TILT)


def htilt(y, z):
    """Coordenadas locais do capacete (y, z) sem a inclinacao."""
    dy, dz = y - CYH, z - ZR
    return CYH + _CT * dy - _ST * dz, ZR + _ST * dy + _CT * dz


def _capacete_local(x, y, z):
    dome = ellipsoid(x, y, z, (CXH, CYH, ZR - 0.2), (HXR, HYR, HZR))
    dome = np.maximum(dome, ZR - z)
    rim = np.maximum(ellipse2(x, y, (CXH, CYH + 0.6), (HXR + 1.7, HYR + 2.4)), np.abs(z - (ZR + 1.0)) - 1.0)
    visor = ellipse2(x, y, (CXH, CYH - 2.0), (HXR * 0.80, HYR + 5.2))
    visor = np.maximum(visor, (y - (CYH - 7.0)))
    visor = np.maximum(visor, np.abs(z - (ZR + 1.2)) - 1.2)
    d = smin(dome, rim, 1.0)
    d = smin(d, visor, 1.0)
    # relevos moldados: nervura central e duas laterais
    shell = band(dome, -1.0, 1.2)
    rib_c = np.maximum(np.abs(x - CXH) - 1.6, shell)
    rib_c = np.maximum(rib_c, -(y - (CYH - 9.0)))
    rib_c = np.maximum(rib_c, (ZR + 9.0) - z)
    d = np.minimum(d, rib_c)
    for sg in (-1, 1):
        rib = np.maximum(np.abs(x - (CXH + sg * 8.6)) - 1.0, band(dome, -1.0, 0.8))
        rib = np.maximum(rib, (ZR + 14.0) - z)
        rib = np.maximum(rib, -(y - (CYH - 4.0)))
        d = np.minimum(d, rib)
    return d


def capacete(x, y, z):
    yl, zl = htilt(y, z)
    return _capacete_local(x, yl, zl)


def helmet_dome(x, y, z):
    yl, zl = htilt(y, z)
    return ellipsoid(x, yl, zl, (CXH, CYH, ZR - 0.2), (HXR, HYR, HZR))


# logomarca: circulo (335,52) r=28 px ; "CIPAA" x 292-377, y 80-100
HEMB_C = (fx(335), fz(52))
TXT_CIPAA_H = Text2D("CIPAA", FONT_SMALL, (fx(292.5), fx(376.5), fz(99), fz(80)),
                     dilate=0.04, open_counters=0.22)


def _front_h(y):
    return y - (CYH - 6.0)


def emb_cap_circ(x, y, z):
    d = np.maximum(circle2(x, z, HEMB_C, 28 * S), band(helmet_dome(x, y, z), -0.6, 0.6))
    return np.maximum(d, _front_h(y))


def emb_cap_cruz(x, y, z):
    d = np.maximum(cross2(x, z, HEMB_C, 1.45, 4.1, 0.35), band(helmet_dome(x, y, z), -0.2, 1.1))
    return np.maximum(d, _front_h(y))


def txt_cap(x, y, z):
    d = np.maximum(TXT_CIPAA_H(x, z), band(helmet_dome(x, y, z), -0.6, 0.6))
    return np.maximum(d, _front_h(y))


# --- abafadores: frente x 200-262 / 410-473 px, centro y ~198 ; perfil: px 765-870, py 125-245
CUP_Z, CUP_Y = 164.5, 0.4
CUP_X = [HCX - 23.7, HCX + 23.7]


def rcyl_x(x, y, z, cx, cy, cz, ry, rz, hx, r):
    a = ellipse2(y, z, (cy, cz), (ry, rz)) + r
    b = np.abs(x - cx) - hx + r
    return length(np.maximum(a, 0), np.maximum(b, 0)) + np.minimum(np.maximum(a, b), 0) - r


def conchas(x, y, z):
    d = None
    for cx in CUP_X:
        di = rcyl_x(x, y, z, cx, CUP_Y, CUP_Z, 9.6, 12.0, 3.9, 2.2)
        d = di if d is None else np.minimum(d, di)
    return d


def almofadas(x, y, z):
    d = None
    for sg, cx in zip((-1, 1), CUP_X):
        di = rcyl_x(x, y, z, cx - sg * 5.1, CUP_Y, CUP_Z, 9.0, 11.3, 1.9, 1.0)
        d = di if d is None else np.minimum(d, di)
    return d


def suportes(x, y, z):
    d = None
    for sg, cx in zip((-1, 1), CUP_X):
        top = (cx + sg * 0.6, CUP_Y, CUP_Z + 12.2)
        slot_c = (CXH + sg * (HXR - 0.4), CUP_Y + 0.4, ZR + 4.0)
        arm = rbox(x, y, z, top, (2.4, 2.8, 2.6), 0.8)
        slot = rbox(x, y, z, slot_c, (2.0, 3.8, 3.4), 0.8)
        pivot = capsule(x, y, z, top, slot_c, 2.0)
        di = np.minimum(np.minimum(arm, slot), pivot)
        d = di if d is None else np.minimum(d, di)
    return d


# ======================================================================= TRONCO
TCX = -1.5


def torso(x, y, z):
    chest = ellipsoid(x, y, z, (TCX, -5.5, 132.0), (21.5, 12.0, 14.5))
    waist = ellipsoid(x, y, z, (TCX, -5.5, 113.0), (18.5, 12.0, 12.5))   # barriga: perfil px 718
    d = smin(chest, waist, 6.0)
    for sg in (-1, 1):
        d = smin(d, sphere(x, y, z, (TCX + sg * 18.6, -4.2, 138.4), 7.4), 4.0)
    return d


def waist_sdf(x, y, z):
    waist = ellipsoid(x, y, z, (TCX, -5.5, 113.0), (18.5, 12.0, 12.5))
    hip = ellipsoid(x, y, z, (TCX, -5.0, 99.0), (19.0, 11.4, 8.6))
    return smin(waist, hip, 4.0)



# bracos: ombro, cotovelo, punho
SH_R = np.array([TCX - 19.0, -4.5, 138.6])
EL_R = np.array([fx(165), -9.0, fz(328)])
WR_R = np.array([fx(148), -21.5, fz(238)])
SH_L = np.array([TCX + 19.0, -4.5, 138.6])
EL_L = np.array([fx(470), 2.5, fz(412)])
WR_L = np.array([fx(434), -10.5, fz(468)])   # punho apoiado no cinto (py ~490)
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
    H = (fx(141), -24.5, fz(205))       # perfil: mao a frente do rosto (px 680-745)
    fist = rbox(x, y, z, H, (6.9, 4.7, 5.6), 3.0)
    dy = H[1] + 21.0
    thumb = capsule(x, y, z, (H[0] + 6.0, -22.0 + dy, H[2] - 3.4), (H[0] - 2.6, -25.6 + dy, H[2] - 1.2), 2.3, 2.05)
    curl = np.minimum(capsule(x, y, z, (H[0] - 5.2, -24.0 + dy, H[2] + 2.0), (H[0] + 0.5, -24.6 + dy, H[2] + 2.2), 2.15),
                      capsule(x, y, z, (H[0] - 5.0, -24.0 + dy, H[2] - 1.6), (H[0] + 0.5, -24.6 + dy, H[2] - 1.0), 2.05))
    d = smin(fist, curl, 1.0)
    d = smin(d, thumb, 0.8)
    zroot = H[2] + 3.6
    f1 = capsule(x, y, z, (H[0] - 3.6, H[1] - 0.2, zroot), (fx(120), H[1] - 0.6, fz(110)), 3.15, 2.75)
    f2 = capsule(x, y, z, (H[0] + 3.6, H[1] - 0.2, zroot), (fx(169), H[1] - 0.6, fz(114)), 3.15, 2.75)
    d = smin(d, f1, 1.6)
    d = smin(d, f2, 1.6)
    return d


def hand_hip(x, y, z):
    H = WR_L + np.array([-1.8, -1.6, -4.4])
    fist = rbox(x, y, z, H, (5.0, 5.6, 6.0), 2.8)
    knuck = capsule(x, y, z, (H[0] - 1.0, H[1] - 4.6, H[2] + 3.0), (H[0] - 1.0, H[1] - 4.8, H[2] - 3.4), 2.2)
    thumb = capsule(x, y, z, (H[0] + 1.0, H[1] - 3.0, H[2] + 4.2), (H[0] - 2.8, H[1] - 6.2, H[2] + 1.8), 2.0)
    return smin(smin(fist, knuck, 1.2), thumb, 0.8)


def pele_bracos(x, y, z):
    d = None
    for sh, el, wr, slv in ((SH_R, EL_R, WR_R, SLEEVE_R), (SH_L, EL_L, WR_L, SLEEVE_L)):
        upper = capsule(x, y, z, sh, el, 6.2, 5.8)
        fore = capsule(x, y, z, el, wr, 6.0, 4.9)
        arm = smin(upper, fore, 1.8)
        # biceps arredondado (estilo colecionavel): volume a frente e acima do eixo do braco
        bc = sh + 0.80 * (el - sh) + np.array([0.0, -2.2, 1.4])
        arm = smin(arm, sphere(x, y, z, bc, 5.6), 2.5)
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
ANK = [np.array([fx(212), -4.5, 57.0]), np.array([fx(446), -4.5, 57.0])]


def legs(x, y, z):
    d = None
    for h, a in zip(HIP_J, ANK):
        di = capsule(x, y, z, h, a, 11.4, 10.8)
        d = di if d is None else np.minimum(d, di)
    return d


def calca(x, y, z):
    hip = ellipsoid(x, y, z, (TCX, -5.0, 99.0), (19.0, 11.4, 8.6))
    waist = ellipsoid(x, y, z, (TCX, -5.5, 113.0), (18.5, 12.0, 12.5))
    top = np.maximum(smin(hip, waist, 4.0), z - 104.6)
    d = smin(top, legs(x, y, z), 3.0)
    d = np.maximum(d, 55.0 - z)
    return np.minimum(d, bolsos(x, y, z))


def bolsos(x, y, z):
    """Bolsos cargo nas laterais das coxas (volume proprio, mesma cor da calca)."""
    d = None
    for sg, h, a in zip((-1, 1), HIP_J, ANK):
        t = 0.44
        c = h + t * (a - h)
        cx = c[0] + sg * 10.4
        pocket = rbox(x, y, z, (cx, c[1] - 0.5, c[2] - 1.0), (2.1, 5.6, 6.6), 1.2)
        flap = rbox(x, y, z, (cx + sg * 0.6, c[1] - 0.5, c[2] + 5.6), (1.9, 6.1, 1.4), 0.6)
        di = np.minimum(pocket, flap)
        d = di if d is None else np.minimum(d, di)
    return d


def faixas(x, y, z):
    return np.maximum(band(legs(x, y, z), -1.2, 0.45), np.abs(z - 64.4) - 2.8)   # faixas py 655-695


def botas(x, y, z):
    """Botas de seguranca: frente x 140-275 / 380-520 px (~27,5 mm cada);
    perfil: bico em px 705 e calcanhar em px 880 (~35 mm), topo do cano em py ~720."""
    d = None
    for sg, a in zip((-1, 1), ANK):
        bx, by = a[0] + sg * 1.0, -4.0
        xr, yr = rot_z(x, y, (bx, by), sg * 6.0)
        sole = rbox(xr, yr, z, (bx, by, BZ1 + 1.9), (13.4, 18.0, 1.9), 1.5)
        toe = ellipsoid(xr, yr, z, (bx, by - 8.0, BZ1 + 5.4), (12.8, 10.0, 6.2))
        heel = ellipsoid(xr, yr, z, (bx, by + 6.0, BZ1 + 8.0), (12.6, 10.0, 8.8))
        shaft = capsule(xr, yr, z, (bx, by + 2.5, BZ1 + 9.0), (a[0], a[1], 60.0), 10.9, 10.5)
        up = smin(smin(toe, heel, 4.5), shaft, 3.5)
        up = np.maximum(up, BZ1 + 3.0 - z)
        b = smin(sole, up, 0.6)
        # sulco da sola (vira)
        groove = np.maximum(np.abs(z - (BZ1 + 2.0)) - 0.4, -(sole + 0.65))
        b = np.maximum(b, -groove)
        # biqueira: friso de 0,6 mm em volta do bico
        cap = np.maximum(np.abs(ellipsoid(xr, yr, z, (bx, by - 8.6, BZ1 + 5.0), (12.2, 9.4, 5.6))) - 0.45,
                         yr - (by - 9.0))
        b = np.minimum(b, np.maximum(cap, band(up, -0.8, 0.55)))
        # cadarcos sobre o peito do pe
        for k in range(4):
            ly, lz = by - 7.4 + k * 2.4, BZ1 + 9.6 + k * 2.3
            lace = capsule(xr, yr, z, (bx - 3.6, ly, lz), (bx + 3.6, ly, lz), 0.75)
            b = np.minimum(b, np.maximum(lace, band(up, -0.8, 0.75)))
        b = np.maximum(b, BZ1 - 0.4 - z)
        d = b if d is None else np.minimum(d, b)
    return d


# ======================================================================= CAPA
CAPE_TOP, CAPE_HEM = 146.0, 50.5     # barra mais baixa atras: py ~745 no perfil


def capa(x, y, z):
    t = np.clip((CAPE_TOP - z) / (CAPE_TOP - CAPE_HEM), 0.0, 1.0)
    cx = -3.5 - 3.0 * t
    cy = -4.6 + 3.5 * t
    a = 22.5 + 32.0 * t ** 0.7
    b = 14.0 + 18.5 * t ** 0.7          # perfil: costas da capa em +14 mm (ombro) ate +32 mm (barra)
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
    zhem = CAPE_HEM + 3.5 * (np.abs(phi) / phimax) ** 2 + 1.0 * np.sin(n * phi + ph + 1.2)
    d = np.maximum(sheet, edge)
    d = smax(d, zhem - z, 0.8)
    d = smax(d, z - CAPE_TOP, 2.0)
    return d


# ======================================================================= LISTA DE PARTES
# (nome, material, funcao sdf, resolucao de malha em mm)
PARTS = [
    ("OLHOS_BRILHO_BRANCO", WHITE, brilho, 0.10),
    ("PUPILAS_PRETAS", BLACK, pupilas, 0.10),
    ("OCULOS_PRETOS", BLACK, armacao, 0.12),
    ("OLHOS_BRANCOS", WHITE, olhos_brancos, 0.12),
    ("SOBRANCELHAS_PRETAS", BLACK, sobrancelhas, 0.12),
    ("DENTES_BRANCOS", WHITE, dentes, 0.12),
    ("BOCA_PRETA", BLACK, boca_interior, 0.12),
    ("CAPACETE_CRUZ_BRANCA", WHITE, emb_cap_cruz, 0.10),
    ("CAPACETE_LOGO_VERDE", GREEN, emb_cap_circ, 0.12),
    ("CAPACETE_TEXTO_CIPAA", GREEN, txt_cap, 0.08),
    ("CAPACETE_BRANCO", WHITE, capacete, 0.2),
    ("PROTETORES_HASTES_PRETAS", BLACK, suportes, 0.13),
    ("PROTETORES_VERDES", GREEN, conchas, 0.18),
    ("PROTETORES_ESTRUTURA_PRETA", BLACK, almofadas, 0.15),
    ("CABELO_PRETO", BLACK, cabelo, 0.18),
    ("ROSTO_PELE", NUDE, pele_rosto, 0.15),
    ("CAMISA_LOGO_CRUZ_VERDE", GREEN, emb_peito_cruz, 0.08),
    ("CAMISA_LOGO_BRANCA", WHITE, emb_peito_circ, 0.10),
    ("CAMISA_TEXTO_CIPAA_BRANCO", WHITE, txt_peito, 0.07),
    ("BRACOS_MAOS_PELE", NUDE, pele_bracos, 0.15),
    ("FIVELA_BRANCA", WHITE, fivela, 0.12),
    ("CINTO_PRETO", BLACK, cinto, 0.18),
    ("CAMISA_VERDE", GREEN, camisa, 0.2),
    ("CAPA_VERDE", GREEN, capa, 0.22),
    ("FAIXAS_BRANCAS", WHITE, faixas, 0.18),
    ("BOLSOS_PRETOS", BLACK, bolsos, 0.15),
    ("CALCA_PRETA", BLACK, calca, 0.22),
    ("BOTAS_PRETAS", BLACK, botas, 0.2),
    ("BASE_CRUZ_BRANCA", WHITE, emblema_base_cruz, 0.12),
    ("BASE_LOGO_VERDE", GREEN, emblema_base_circ, 0.15),
    ("BASE_TEXTO_CIPEIRO_BRANCO", WHITE, letreiro_cipeiro, 0.12),
    ("BASE_TEXTO_DO_MES_VERDE", GREEN, letreiro_domes, 0.12),
    ("BASE_PRETA", BLACK, base_sdf, 0.3),
]
