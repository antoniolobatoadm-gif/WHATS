"""Converte malhas (npz do mesher ou o .3mf final) em GLB colorido para renderizacao."""
import sys, zipfile, re
import numpy as np, trimesh
import xml.etree.ElementTree as ET

def from_npz(path):
    import model
    d = np.load(path)
    out = []
    for name, mat, fn, h in model.PARTS:
        if f"{name}__v" in d:
            out.append((name, model.MAT[mat][1], d[f"{name}__v"], d[f"{name}__f"]))
    return out

def from_3mf(path):
    """Le o 3MF de forma independente do gerador: objetos, componentes e basematerials."""
    ns = {"m": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"}
    z = zipfile.ZipFile(path)
    root = ET.fromstring(z.read("3D/3dmodel.model"))
    res = root.find("m:resources", ns)
    colors = {}
    for bm in res.findall("m:basematerials", ns):
        colors[bm.get("id")] = [b.get("displaycolor")[:7] for b in bm.findall("m:base", ns)]
    objs = {}
    for o in res.findall("m:object", ns):
        objs[o.get("id")] = o
    out = []
    for o in objs.values():
        mesh = o.find("m:mesh", ns)
        if mesh is None:
            continue
        vs = mesh.find("m:vertices", ns)
        v = np.array([[float(e.get("x")), float(e.get("y")), float(e.get("z"))] for e in vs], float)
        f = np.array([[int(e.get("v1")), int(e.get("v2")), int(e.get("v3"))] for e in mesh.find("m:triangles", ns)], int)
        col = colors[o.get("pid")][int(o.get("pindex"))]
        out.append((o.get("name"), col, v, f))
    return out

def write_glb(parts, out):
    sc = trimesh.Scene()
    for name, col, v, f in parts:
        m = trimesh.Trimesh(v, f, process=False)
        c = [int(col[i:i+2], 16) for i in (1, 3, 5)]
        m.visual = trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(
            baseColorFactor=c + [255], metallicFactor=0.0, roughnessFactor=0.65))
        sc.add_geometry(m, node_name=name, geom_name=name)
    sc.export(out)

if __name__ == "__main__":
    src, out = sys.argv[1], sys.argv[2]
    parts = from_3mf(src) if src.endswith(".3mf") else from_npz(src)
    write_glb(parts, out)
    print("glb", out, len(parts), "partes")
