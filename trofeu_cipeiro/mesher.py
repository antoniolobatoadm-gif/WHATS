"""Gera as malhas de cada parte com particao por prioridade.

campo_k = max(d_k, -min_{j<k} d_j)  -> a parte k recebe exatamente o complemento
das partes anteriores; as faces de contato coincidem (mesmo zero do mesmo campo).
Uso: python3 mesher.py [fator_resolucao] [saida.npz]
"""
import sys
import time
import numpy as np
import trimesh
from skimage.measure import marching_cubes

import model

DOMAIN = (np.array([-70.0, -45.0, -1.0]), np.array([70.0, 45.0, 203.0]))


def eval_box(fn, lo, h, shape):
    xs = lo[0] + h * np.arange(shape[0], dtype=np.float32)
    ys = lo[1] + h * np.arange(shape[1], dtype=np.float32)
    zs = lo[2] + h * np.arange(shape[2], dtype=np.float32)
    X, Y, Z = np.meshgrid(xs, ys, zs, indexing="ij")
    return fn(X, Y, Z).astype(np.float32)


def coarse_bbox(fn, step=0.8, thr=1.6, pad=1.5):
    lo, hi = DOMAIN
    shape = np.ceil((hi - lo) / step).astype(int) + 1
    out_lo, out_hi = None, None
    # avalia por fatias em Z para limitar memoria
    for k0 in range(0, shape[2], 40):
        nz = min(40, shape[2] - k0)
        lo_k = lo + np.array([0, 0, k0 * step])
        d = eval_box(fn, lo_k, step, (shape[0], shape[1], nz))
        idx = np.argwhere(d < thr)
        if len(idx):
            a = lo_k + idx.min(0) * step
            b = lo_k + idx.max(0) * step
            out_lo = a if out_lo is None else np.minimum(out_lo, a)
            out_hi = b if out_hi is None else np.maximum(out_hi, b)
    return out_lo - pad, out_hi + pad


def repair(tm):
    """Fecha furos residuais do marching cubes (empate do campo exatamente sobre um plano da grade)."""
    tm.merge_vertices()
    trimesh.repair.fill_holes(tm)
    trimesh.repair.fix_normals(tm)
    if not tm.is_watertight:
        raise RuntimeError("malha nao estanque apos reparo")
    return tm


def build(res_scale=1.0, verbose=True, only=None):
    parts = model.PARTS
    boxes = []
    t0 = time.time()
    for name, mat, fn, h in parts:
        boxes.append(coarse_bbox(fn))
    if verbose:
        print(f"bboxes: {time.time()-t0:.1f}s", flush=True)
    meshes = []
    for k, (name, mat, fn, h) in enumerate(parts):
        if only is not None and name not in only:
            meshes.append(None)
            continue
        t1 = time.time()
        h = h * res_scale
        lo, hi = boxes[k]
        shape = np.ceil((hi - lo) / h).astype(int) + 1
        field = np.empty(shape, np.float32)
        zs_chunk = max(1, int(6e6 // (shape[0] * shape[1])))
        for k0 in range(0, shape[2], zs_chunk):
            nz = min(zs_chunk, shape[2] - k0)
            lo_k = lo + np.array([0, 0, k0 * h])
            sub_hi = lo_k + (np.array([shape[0], shape[1], nz]) - 1) * h
            d = eval_box(fn, lo_k, h, (shape[0], shape[1], nz))
            m = np.full(d.shape, np.inf, np.float32)
            for j in range(k):
                blo, bhi = boxes[j]
                if np.any(bhi < lo_k) or np.any(blo > sub_hi):
                    continue
                i0 = np.maximum(np.ceil((blo - lo_k) / h).astype(int), 0)
                i1 = np.minimum(np.floor((bhi - lo_k) / h).astype(int) + 1, d.shape)
                if np.any(i1 <= i0):
                    continue
                dj = eval_box(parts[j][2], lo_k + i0 * h, h, tuple(i1 - i0))
                sl = tuple(slice(a, b) for a, b in zip(i0, i1))
                m[sl] = np.minimum(m[sl], dj)
            field[:, :, k0:k0 + nz] = np.maximum(d, -m)
        field[field == 0] = 1e-7
        # garante superficie fechada na borda da caixa
        field[0, :, :] = field[-1, :, :] = np.maximum(field[0], 1e-3)
        field[:, 0, :] = field[:, -1, :] = np.maximum(field[:, 0], 1e-3)
        field[:, :, 0] = field[:, :, -1] = np.maximum(field[:, :, 0], 1e-3)
        if field.min() >= 0:
            print(f"  !! {name}: regiao vazia")
            meshes.append(None)
            continue
        v, f, _, _ = marching_cubes(field, 0.0, spacing=(h, h, h), allow_degenerate=False)
        v = v + lo
        tm = trimesh.Trimesh(v, f, process=True)
        tm.update_faces(tm.nondegenerate_faces(height=1e-9))
        tm.remove_unreferenced_vertices()
        # mantem apenas componentes com volume relevante (remove fragmentos < 1 mm3)
        comps = tm.split(only_watertight=False)
        keep = [c for c in comps if abs(c.volume) > 1.0]
        tm = trimesh.util.concatenate(keep) if len(keep) > 1 else keep[0]
        if not tm.is_watertight:
            tm = repair(tm)
        if tm.volume < 0:
            tm.invert()
        meshes.append(tm)
        if verbose:
            print(f"{k:2d} {name:28s} h={h:.3f} grid={tuple(shape)} tris={len(tm.faces):8d} "
                  f"vol={tm.volume:9.1f} wt={tm.is_watertight} comps={len(keep)} "
                  f"({time.time()-t1:.1f}s)", flush=True)
    return meshes


if __name__ == "__main__":
    rs = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
    out = sys.argv[2] if len(sys.argv) > 2 else "meshes.npz"
    ms = build(rs)
    data = {}
    for (name, mat, fn, h), m in zip(model.PARTS, ms):
        if m is None:
            continue
        data[f"{name}__v"] = m.vertices.astype(np.float64)
        data[f"{name}__f"] = m.faces.astype(np.int32)
    np.savez_compressed(out, **data)
    print("salvo", out)
