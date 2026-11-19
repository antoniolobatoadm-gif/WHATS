"""Validacao do 3MF exportado. Uso: python3 validate.py arquivo.3mf meshes.npz pasta_saida"""
import sys
import json
import numpy as np
import trimesh
import lib3mf
import manifold3d as mf
import model

path, npz, outdir = sys.argv[1:4]
rep = {}

# ------------------------------------------------ 1. releitura independente (lib3mf)
w = lib3mf.get_wrapper()
m3 = w.CreateModel()
m3.QueryReader("3mf").ReadFromFile(path)
mats = []
it = m3.GetBaseMaterialGroups()
while it.MoveNext():
    g = it.GetCurrentBaseMaterialGroup()
    for pid in g.GetAllPropertyIDs():
        c = g.GetDisplayColor(pid)
        mats.append((pid, g.GetName(pid), "#%02X%02X%02X" % (c.Red, c.Green, c.Blue)))
rep["materiais"] = mats
parts = []
oit = m3.GetMeshObjects()
while oit.MoveNext():
    o = oit.GetCurrentMeshObject()
    rid, pid, ok = o.GetObjectLevelProperty()
    v = np.array([list(p.Coordinates) for p in o.GetVertices()])
    f = np.array([list(t.Indices) for t in o.GetTriangleIndices()])
    parts.append((o.GetName(), pid, v, f))
comp = []
cit = m3.GetComponentsObjects()
while cit.MoveNext():
    c = cit.GetCurrentComponentsObject()
    comp.append((c.GetName(), c.GetComponentCount()))
bit = m3.GetBuildItems()
n_items = 0
while bit.MoveNext():
    n_items += 1
rep["objetos_montagem"] = comp
rep["itens_build"] = n_items
rep["partes"] = len(parts)

allv = np.vstack([p[2] for p in parts])
mn, mx = allv.min(0), allv.max(0)
rep["bbox_min"] = mn.round(3).tolist()
rep["bbox_max"] = mx.round(3).tolist()
rep["dimensoes_XYZ_mm"] = (mx - mn).round(2).tolist()
base = [p for p in parts if p[0] == "BASE_PRETA"][0]
bv, bf = base[2], base[3]
tb = trimesh.Trimesh(bv, bf, process=False)
bottom = tb.faces[np.all(np.abs(tb.vertices[tb.faces][:, :, 2]) < 1e-6, axis=1)]
rep["area_apoio_z0_mm2"] = round(float(trimesh.Trimesh(bv, bottom, process=False).area), 1)

# ------------------------------------------------ 2. integridade por malha
names_mat = {}
integ = []
mans = {}
for name, pid, v, f in parts:
    t = trimesh.Trimesh(v, f, process=False)
    e = t.edges_sorted
    _, cnt = np.unique(e, axis=0, return_counts=True)
    deg = int((t.area_faces < 1e-10).sum())
    comps = t.split(only_watertight=False)
    integ.append(dict(parte=name, material=int(pid), tris=len(f), fechada=bool(t.is_watertight),
                      normais_coerentes=bool(t.is_winding_consistent), volume=round(float(t.volume), 2),
                      arestas_nao_manifold=int((cnt != 2).sum()), faces_degeneradas=deg,
                      componentes=len(comps)))
    names_mat[name] = int(pid)
    mm = mf.Manifold(mf.Mesh(vert_properties=np.asarray(v, np.float32), tri_verts=np.asarray(f, np.uint32)))
    mans[name] = mm
    integ[-1]["manifold_ok"] = str(mm.status()) .split(".")[-1]
    # auto-intersecao: o booleano de si mesmo deve preservar o volume
rep["integridade"] = integ

# ------------------------------------------------ 3. sobreposicao entre volumes (booleana exata)
names = [p[0] for p in parts]
bbs = {p[0]: (p[2].min(0), p[2].max(0)) for p in parts}
ov = []
for i in range(len(names)):
    for j in range(i + 1, len(names)):
        a, b = bbs[names[i]], bbs[names[j]]
        if np.any(a[1] < b[0]) or np.any(b[1] < a[0]):
            continue
        vol = (mans[names[i]] ^ mans[names[j]]).volume()
        if vol > 1e-4:
            ov.append((names[i], names[j], round(vol, 4)))
rep["sobreposicoes_mm3"] = sorted(ov, key=lambda t: -t[2])
rep["sobreposicao_total_mm3"] = round(sum(t[2] for t in ov), 3)
rep["volume_total_mm3"] = round(sum(x["volume"] for x in integ), 1)

# ------------------------------------------------ 4. contato / continuidade fisica (campo analitico)
d = np.load(npz)
P = model.PARTS
fns = {n: fn for n, _, fn, _ in P}
order = [n for n, *_ in P]
tol = 0.04
contact = {}
nodes = []
for k, (n, mat, fn, h) in enumerate(P):
    t = trimesh.Trimesh(d[f"{n}__v"], d[f"{n}__f"], process=False)
    for ci, c in enumerate(t.split(only_watertight=False)):
        cen = c.triangles_center
        ar = c.area_faces
        lo, hi = cen.min(0) - 1, cen.max(0) + 1
        node = f"{n}#{ci}"
        nodes.append(node)
        for j, (nj, _, fj, _) in enumerate(P):
            if j == k:
                continue
            dv = d[f"{nj}__v"]
            if np.any(dv.max(0) < lo) or np.any(dv.min(0) > hi):
                continue
            dj = fj(cen[:, 0], cen[:, 1], cen[:, 2])
            sel = (np.abs(dj) < tol) if j < k else (dj < tol)
            a = float(ar[sel].sum())
            if a > 0.05:
                contact[(node, nj)] = a
# grafo: componente de parte -> parte vizinha
import collections
adj = collections.defaultdict(set)
for (node, nj), a in contact.items():
    if a >= 1.0:
        adj[node].add(nj + "*")
        adj[nj + "*"].add(node)
for node in nodes:
    adj[node.split("#")[0] + "*"].add(node)
    adj[node].add(node.split("#")[0] + "*")
seen, st = set(), ["BASE_PRETA*"]
while st:
    x = st.pop()
    if x in seen:
        continue
    seen.add(x)
    st.extend(adj[x] - seen)
rep["componentes_total"] = len(nodes)
rep["componentes_desconectados_da_base"] = [n for n in nodes if n not in seen]
mincont = {}
for node in nodes:
    tot = sum(a for (nd, nj), a in contact.items() if nd == node)
    mincont[node] = round(tot, 2)
rep["menor_area_contato_por_componente_mm2"] = sorted(mincont.items(), key=lambda t: t[1])[:8]

# ------------------------------------------------ 5. textos
for nm, T in (("CIPEIRO", model.TXT_CIPEIRO), ("DO_MES", model.TXT_DOMES),
              ("CIPAA_capacete", model.TXT_CIPAA_H), ("CIPAA_peito", model.TXT_CIPAA_P)):
    p5, med, mn_ = T.stroke_stats()
    rep[f"traco_{nm}_mm(p5,mediana)"] = (round(p5, 2), round(med, 2))
    g = T.gap_stats()
    rep[f"contraforma_{nm}_mm(p5,min)"] = None if g is None else (round(g[0], 2), round(g[1], 2))
    rep[f"caixa_{nm}_mm"] = [round(x, 2) for x in T.ink_box]

# ------------------------------------------------ 6. espessura local (raio para dentro a partir da superficie)
# Para cada parte critica: amostra pontos na superficie, lanca um raio na direcao -normal e mede
# a distancia ate a proxima face da mesma malha (= espessura local da parede/peca).
crit = ["BRACOS_MAOS_PELE", "CAPA_VERDE", "OCULOS_PRETOS", "SOBRANCELHAS_PRETAS", "CAPACETE_TEXTO_CIPAA",
        "CAMISA_TEXTO_CIPAA_BRANCO", "BASE_TEXTO_DO_MES_VERDE", "PROTETORES_HASTES_PRETAS", "FAIXAS_BRANCAS"]
rng = np.random.default_rng(1)
esp = {}
for name, pid, v, f in parts:
    if name not in crit:
        continue
    t = trimesh.Trimesh(v, f, process=False)
    pts, fi = trimesh.sample.sample_surface(t, 4000, seed=1)
    nrm = t.face_normals[fi]
    org = pts - nrm * 1e-3
    loc, ri, _ = t.ray.intersects_location(org, -nrm, multiple_hits=False)
    th = np.full(len(pts), np.nan)
    th[ri] = np.linalg.norm(loc - org[ri], axis=1)
    th = th[np.isfinite(th)]
    esp[name] = dict(p1=round(float(np.percentile(th, 1)), 2), p5=round(float(np.percentile(th, 5)), 2),
                     mediana=round(float(np.median(th)), 2),
                     frac_abaixo_0_8mm=round(float((th < 0.8).mean()), 4))
rep["espessura_local_mm"] = esp

json.dump(rep, open(f"{outdir}/validacao.json", "w"), indent=1, ensure_ascii=False)
for k, vv in rep.items():
    if k != "integridade":
        print(k, ":", vv)
bad = [x for x in integ if not (x["fechada"] and x["normais_coerentes"] and x["arestas_nao_manifold"] == 0)]
print("partes com problema de malha:", bad)
print("componentes por parte:", {x["parte"]: x["componentes"] for x in integ if x["componentes"] > 1})

# ------------------------------------------------ 6. cortes por camada (secoes horizontais)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
cols = {int(pid): c for pid, _, c in mats}
cuts = [("dedos_V", 180.0, None), ("oculos_olhos", 167.5, None), ("boca_dentes", 155.0, None),
        ("CIPAA_capacete", 184.5, None), ("CIPAA_peito", 124.0, None), ("acento_MES", 16.4, None),
        ("letreiro_DO_MES", 8.6, None), ("barra_capa", 58.0, None)]
fig, axs = plt.subplots(2, 4, figsize=(20, 10))
for ax, (lbl, z, _) in zip(axs.ravel(), cuts):
    for name, pid, v, f in parts:
        if v[:, 2].min() > z or v[:, 2].max() < z:
            continue
        t = trimesh.Trimesh(v, f, process=False)
        sec = t.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
        if sec is None:
            continue
        for e in sec.discrete:
            ax.fill(e[:, 0], e[:, 1], color=cols[int(pid)], ec="#888", lw=0.3)
    ax.set_title(f"{lbl}  Z={z} mm")
    ax.set_aspect("equal")
    ax.invert_yaxis()
plt.tight_layout()
plt.savefig(f"{outdir}/cortes_camadas.png", dpi=110)
print("cortes salvos")
