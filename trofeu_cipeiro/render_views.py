"""Renderiza as 10 vistas de inspecao a partir do 3MF final (lido de forma independente).

Uso: NODE_PATH=$(npm root -g) python3 render_views.py arquivo.3mf pasta_saida
Requer: three (npm, nesta pasta) e Playwright/Chromium.
Camera ortografica; az=0 = frente, az=90 = lado esquerdo do personagem (igual a vista de perfil da
referencia), az=180 = costas. tx/ty deslocam o alvo (mm) a partir do centro da caixa envolvente.
"""
import os
import subprocess
import sys

import numpy as np

import to_glb

src, outdir = sys.argv[1], sys.argv[2]
os.makedirs(outdir, exist_ok=True)
parts = to_glb.from_3mf(src)
glb = os.path.join(outdir, "_modelo.glb")
to_glb.write_glb(parts, glb)

allv = np.vstack([p[2] for p in parts])
c = 0.5 * (allv.min(0) + allv.max(0))


def at(name):
    """Centro (x, z) da parte, como deslocamento a partir do centro da caixa envolvente."""
    v = [p[2] for p in parts if p[0] == name][0]
    m = 0.5 * (v.min(0) + v.max(0))
    return m[0] - c[0], m[2] - c[2]


fx, fz = at("OCULOS_PRETOS")
hx, hz = at("CAPACETE_BRANCO")
cx, cz = at("CAMISA_LOGO_BRANCA")
bx, bz = at("BASE_PRETA")
arm = [p[2] for p in parts if p[0] == "BRACOS_MAOS_PELE"][0]
top = arm[arm[:, 2] > np.percentile(arm[:, 2], 97)]
vx, vz = top[:, 0].mean() - c[0], top[:, 2].mean() - c[2] - 6

views = [
    ("01_frente", 0, 0, 1, 0, 0),
    ("02_perfil", 90, 0, 1, 0, 0),
    ("03_perspectiva", 28, 12, 1, 0, 0),
    ("04_costas", 180, 0, 1, 0, 0),
    ("05_close_rosto", 0, 0, 3.6, fx, fz - 4),
    ("06_close_capacete", 0, 8, 3.6, hx, hz + 2),
    ("07_close_oculos", 0, 0, 6.0, fx, fz + 1.5),
    ("08_close_sinal_vitoria", 20, 0, 4.5, vx, vz),
    ("09_close_camisa", 0, 0, 2.6, cx - 3, cz - 3),
    ("10_close_base", 0, 10, 1.7, bx, bz - 4),
]
spec = ";".join(f"{n}:{a}:{e}:{z}:{x:.2f}:{y:.2f}" for n, a, e, z, x, y in views)
env = dict(os.environ, VIEWS=spec)
here = os.path.dirname(os.path.abspath(__file__))
subprocess.run(["node", os.path.join(here, "shoot.js"), glb, os.path.join(outdir, "render"), "800", "1000"],
               check=True, env=env)
os.remove(glb)
