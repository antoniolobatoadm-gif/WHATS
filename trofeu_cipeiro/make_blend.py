"""Gera o arquivo-fonte Blender (.blend) a partir do 3MF final.

Executar com o modulo bpy (Blender 5.x como biblioteca Python):
    python make_blend.py ../entrega/KRYOU_CIPEIRO_DO_MES_200MM_4CORES.3mf ../entrega/KRYOU_CIPEIRO_DO_MES_FONTE.blend

Organizacao do .blend:
  - Colecao "PERSONAGEM_CIPEIRO" com 4 subcolecoes, uma por cabecote/filamento
    (T0_VERDE, T1_BRANCO, T2_PRETO, T3_PELE).
  - Um objeto por volume do 3MF, com o mesmo nome e o material do filamento.
  - Unidades da cena em milimetros (1 unidade Blender = 1 mm).
Para trocar a cor de um grupo, edite o material (Base Color); para mover uma parte para
outro filamento, troque o material do objeto e mova-o para a colecao correspondente.
"""
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

import bpy
import numpy as np

NS = {"m": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"}
GROUPS = {0: "T0_VERDE", 1: "T1_BRANCO", 2: "T2_PRETO", 3: "T3_PELE"}


def read_3mf(path):
    z = zipfile.ZipFile(path)
    xml = z.read("3D/3dmodel.model").decode("utf-8")
    root = ET.fromstring(xml)
    res = root.find("m:resources", NS)
    mats = []
    for bm in res.findall("m:basematerials", NS):
        for b in bm.findall("m:base", NS):
            mats.append((b.get("name"), b.get("displaycolor")))
    objs = []
    for o in res.findall("m:object", NS):
        mesh = o.find("m:mesh", NS)
        if mesh is None:
            continue
        vtxt = ET.tostring(mesh.find("m:vertices", NS)).decode()
        ttxt = ET.tostring(mesh.find("m:triangles", NS)).decode()
        v = np.array(re.findall(r'x="([-\d.e]+)" y="([-\d.e]+)" z="([-\d.e]+)"', vtxt), float)
        f = np.array(re.findall(r'v1="(\d+)" v2="(\d+)" v3="(\d+)"', ttxt), int)
        objs.append((o.get("name"), int(o.get("pindex")), v, f))
    return mats, objs


def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def main(src, out):
    mats, objs = read_3mf(src)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = "METRIC"
    sc.unit_settings.scale_length = 0.001
    sc.unit_settings.length_unit = "MILLIMETERS"

    root = bpy.data.collections.new("PERSONAGEM_CIPEIRO")
    sc.collection.children.link(root)
    cols, bmats = {}, {}
    for i, (name, col) in enumerate(mats):
        c = bpy.data.collections.new(GROUPS[i])
        root.children.link(c)
        cols[i] = c
        m = bpy.data.materials.new(GROUPS[i] + " | " + name.split(" - ", 1)[-1])
        rgb = [srgb_to_linear(int(col[k:k + 2], 16) / 255) for k in (1, 3, 5)]
        m.diffuse_color = rgb + [1.0]
        m.use_nodes = True
        bsdf = m.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = rgb + [1.0]
            bsdf.inputs["Roughness"].default_value = 0.55
        bmats[i] = m

    for name, pi, v, f in objs:
        me = bpy.data.meshes.new(name)
        me.from_pydata(v.tolist(), [], f.tolist())
        me.validate(clean_customdata=False)
        me.update()
        me.materials.append(bmats[pi])
        ob = bpy.data.objects.new(name, me)
        cols[pi].objects.link(ob)

    # camera e luz de inspecao (vista frontal)
    cam = bpy.data.cameras.new("CAM_FRENTE")
    cam.type = "ORTHO"
    cam.ortho_scale = 230
    co = bpy.data.objects.new("CAM_FRENTE", cam)
    co.location = (0, -400, 100)
    co.rotation_euler = (np.pi / 2, 0, 0)
    sc.collection.objects.link(co)
    sc.camera = co
    li = bpy.data.lights.new("SOL", "SUN")
    li.energy = 3.0
    lo = bpy.data.objects.new("SOL", li)
    lo.rotation_euler = (0.9, 0.2, -0.5)
    sc.collection.objects.link(lo)

    bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
    print("blend salvo", out, len(objs), "objetos")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
