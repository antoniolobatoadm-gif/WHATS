"""Exporta o 3MF multicomponente (1 objeto de impressao, N volumes nomeados, 4 materiais).

Estrutura:
  3D/3dmodel.model  -> <basematerials> com 4 filamentos; um <object type="model"> de malha por
                       parte (pid/pindex = material); um objeto montagem com <components>
                       referenciando todas as partes; um unico <item> na build.
  Metadata/model_settings.config -> nomes das partes e "extruder" (1..4) no formato lido
                       pelo OrcaSlicer/Bambu Studio e derivados (Orca-FlashForge).
Uso: python3 export_3mf.py meshes.npz saida.3mf
"""
import io
import sys
import uuid
import zipfile
import numpy as np
import model
import manifold3d as mf

SIMPLIFY_MM = 0.01   # tolerancia geometrica da simplificacao (desvio medido < 0.02 mm)

ALTURA = 200.0


def load(npz):
    d = np.load(npz)
    parts = []
    for name, mat, fn, h in model.PARTS:
        if f"{name}__v" in d:
            m = mf.Manifold(mf.Mesh(vert_properties=d[f"{name}__v"].astype(np.float32),
                                    tri_verts=d[f"{name}__f"].astype(np.uint32))).simplify(SIMPLIFY_MM)
            me = m.to_mesh()
            parts.append([name, mat, me.vert_properties[:, :3].astype(np.float64), me.tri_verts.astype(np.int64)])
    return parts


def normalize(parts):
    allv = np.vstack([p[2] for p in parts])
    zmin, zmax = allv[:, 2].min(), allv[:, 2].max()
    s = ALTURA / (zmax - zmin)
    base = [p for p in parts if p[0] == "BASE_PRETA"][0][2]
    cx = 0.5 * (base[:, 0].min() + base[:, 0].max())
    cy = 0.5 * (base[:, 1].min() + base[:, 1].max())
    for p in parts:
        v = p[2]
        v[:, 0] = (v[:, 0] - cx) * s
        v[:, 1] = (v[:, 1] - cy) * s
        v[:, 2] = (v[:, 2] - zmin) * s
        if p[0] == "BASE_PRETA":
            v[v[:, 2] < 0.03, 2] = 0.0      # face de apoio exatamente plana em Z = 0
    return s


def resolve_overlaps(parts):
    """Subtrai de cada parte a uniao das partes de maior prioridade (booleana exata, manifold3d).
    Remove a sobreposicao residual causada pelas resolucoes diferentes de cada malha."""
    mans, boxes = [], []
    for p in parts:
        mans.append(mf.Manifold(mf.Mesh(vert_properties=p[2].astype(np.float32),
                                        tri_verts=p[3].astype(np.uint32))))
        boxes.append((p[2].min(0), p[2].max(0)))
    for k in range(len(parts)):
        lo, hi = boxes[k]
        prev = [mans[j] for j in range(k) if not (np.any(boxes[j][1] < lo) or np.any(boxes[j][0] > hi))]
        if prev:
            u = mf.Manifold.batch_boolean(prev, mf.OpType.Add) if len(prev) > 1 else prev[0]
            mk = mans[k] - u
            comps = [c for c in mk.decompose() if c.volume() > 0.05]
            mk = mf.Manifold.compose(comps)
            mans[k] = mk
        # remove faces de area nula (lascas colineares deixadas pela booleana); desvio <= 0,0001 mm
        mans[k] = mans[k].simplify(1e-4)
        me = mans[k].to_mesh()
        parts[k][2] = me.vert_properties[:, :3].astype(np.float64)
        parts[k][3] = me.tri_verts.astype(np.int64)


def mesh_xml(buf, oid, name, mat, v, f):
    buf.write(f'  <object id="{oid}" name="{name}" type="model" pid="1" pindex="{mat - 1}" '
              f'p:UUID="{uuid.uuid5(uuid.NAMESPACE_URL, "kryou-cipeiro/" + name)}">\n   <mesh>\n    <vertices>\n')
    np.savetxt(buf, v, fmt='     <vertex x="%.4f" y="%.4f" z="%.4f"/>')
    buf.write('    </vertices>\n    <triangles>\n')
    np.savetxt(buf, f, fmt='     <triangle v1="%d" v2="%d" v3="%d"/>')
    buf.write('    </triangles>\n   </mesh>\n  </object>\n')


def write(parts, out):
    asm_id = len(parts) + 1
    buf = io.StringIO()
    buf.write('<?xml version="1.0" encoding="UTF-8"?>\n'
              '<model unit="millimeter" xml:lang="pt-BR" '
              'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
              'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06">\n'
              ' <metadata name="Title">KRYOU - Trofeu Cipeiro do Mes 200 mm (4 cores)</metadata>\n'
              ' <metadata name="Designer">KRYOU</metadata>\n'
              ' <metadata name="Description">Trofeu unico, 4 filamentos PLA: T0/1 Verde Medio Masterprint ID31, '
              'T1/2 Branco GTMax3D ID02, T2/3 Preto Matte Black Soleyin ID42, T3/4 Nude GTMax3D ID01</metadata>\n'
              ' <resources>\n  <basematerials id="1">\n')
    for k in sorted(model.MAT):
        nm, col = model.MAT[k]
        buf.write(f'   <base name="{k} - {nm}" displaycolor="{col}FF"/>\n')
    buf.write('  </basematerials>\n')
    for i, (name, mat, v, f) in enumerate(parts):
        mesh_xml(buf, i + 2, name, mat, v, f)
    asm = asm_id + 1
    buf.write(f'  <object id="{asm}" name="PERSONAGEM_CIPEIRO" type="model" '
              f'p:UUID="{uuid.uuid5(uuid.NAMESPACE_URL, "kryou-cipeiro/asm")}">\n   <components>\n')
    for i in range(len(parts)):
        buf.write(f'    <component objectid="{i + 2}" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>\n')
    buf.write('   </components>\n  </object>\n </resources>\n'
              f' <build p:UUID="{uuid.uuid5(uuid.NAMESPACE_URL, "kryou-cipeiro/build")}">\n'
              f'  <item objectid="{asm}" transform="1 0 0 0 1 0 0 0 1 0 0 0" printable="1"/>\n </build>\n</model>\n')

    cfg = io.StringIO()
    cfg.write('<?xml version="1.0" encoding="UTF-8"?>\n<config>\n'
              f'  <object id="{asm}">\n    <metadata key="name" value="PERSONAGEM_CIPEIRO"/>\n'
              '    <metadata key="extruder" value="3"/>\n')
    for i, (name, mat, v, f) in enumerate(parts):
        cfg.write(f'    <part id="{i + 2}" subtype="normal_part">\n'
                  f'      <metadata key="name" value="{name}"/>\n'
                  '      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>\n'
                  f'      <metadata key="extruder" value="{mat}"/>\n'
                  f'      <mesh_stat face_count="{len(f)}" edges_fixed="0" degenerate_facets="0" '
                  'facets_removed="0" facets_reversed="0" backwards_edges="0"/>\n    </part>\n')
    cfg.write('  </object>\n</config>\n')

    ctypes = ('<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
              ' <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
              ' <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>\n'
              ' <Default Extension="config" ContentType="text/xml"/>\n</Types>\n')
    rels = ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
            ' <Relationship Target="/3D/3dmodel.model" Id="rel0" '
            'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n</Relationships>\n')
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr("[Content_Types].xml", ctypes)
        z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", buf.getvalue())
        z.writestr("Metadata/model_settings.config", cfg.getvalue())


if __name__ == "__main__":
    parts = load(sys.argv[1])
    s = normalize(parts)
    resolve_overlaps(parts)
    write(parts, sys.argv[2])
    print(f"escala uniforme aplicada: {s:.6f}; partes: {len(parts)}; "
          f"triangulos: {sum(len(p[3]) for p in parts)}")
