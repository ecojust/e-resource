"""Intersect the two authored return meshes with the original city roof outside the retained cut.

Requirements: Python 3.10+, numpy, Shapely 2, and node. The Shanghai project
supplies vendor/meshopt_decoder.module.js. The mesh directory holds full-source.glb,
lod-source.glb and their matching .geometry.json files from the source rebuild.
The optional macro directory must preserve the original READY.json/far.glb/near layout.
"""
from pathlib import Path
from urllib.request import Request, urlopen
import argparse
import gzip
import hashlib
import json
import math
import struct
import subprocess
import tempfile
import numpy as np
from shapely.geometry import Polygon, LineString
from shapely import union_all
from probe_mesh import read

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("mesh_directory", type=Path)
parser.add_argument("output", type=Path)
parser.add_argument("--project", type=Path, required=True, help="Shanghai project root, containing vendor/meshopt_decoder.module.js")
parser.add_argument("--macro-directory", type=Path, help="Directory containing the original local macro files")
parser.add_argument("--controls", type=Path, default=Path(__file__).with_name("city-controls.json"))
args = parser.parse_args()
w = Path(__file__).absolute().parent
controls = json.loads(args.controls.read_bytes())
frame = controls["frame"]
A = math.radians(frame["positive_x_bearing"])
lon, lat = frame["origin"]
R = 6378137
def H(data):
    return hashlib.sha256(data).hexdigest()

def fetch(name, digest):
    if args.macro_directory:
        data = (args.macro_directory / name).read_bytes()
    else:
        url = controls["frozen_project_url"] + "assets/city-detail/macros/" + controls["macro_id"] + "/" + name
        with urlopen(Request(url, headers={"User-Agent": "Shanghai-architectural-research"}), timeout=60) as response:
            data = response.read()
    if H(data) != digest:
        raise ValueError("Unexpected city input SHA256: " + name)
    return data

ready = json.loads(fetch("READY.json", controls["ready_sha256"]))
owner = Polygon(controls["mapped_owner_local"])
cut = Polygon(controls["existing_display_cut_local"])
residual = owner.difference(cut)

def model(p):
    b = p.read_bytes()
    n = struct.unpack_from('<I', b, 12)[0]
    q = json.loads(b[20:20 + n])
    d = memoryview(b)[28 + n:]

    def arr(i):
        a = q['accessors'][i]
        v = q['bufferViews'][a['bufferView']]
        ty = {5126: '<f4', 5123: '<u2', 5125: '<u4'}[a['componentType']]
        size = {'SCALAR': 1, 'VEC3': 3}[a['type']]
        ss = np.dtype(ty).itemsize
        return np.ndarray((a['count'], size), ty, buffer=d, offset=v.get('byteOffset', 0) + a.get('byteOffset', 0), strides=(v.get('byteStride', ss * size), ss))
    shapes = []
    segs = []
    vert = []
    total = 0
    sel = 0
    cut_z = controls['roof_height_m']
    parts = json.loads(p.with_suffix('.geometry.json').read_bytes())['part_summary']
    for o in q['nodes']:
        if 'mesh' not in o:
            continue
        assert not {'matrix', 'translation', 'scale', 'rotation'}.intersection(o)
        m = q['meshes'][o['mesh']]
        for prim in m['primitives']:
            ids = arr(prim['indices']).reshape(-1, 3)
            v = arr(prim['attributes']['POSITION'])[:, [0, 2, 1]].copy()
            v[:, 1] *= -1
            total += len(ids)
            mat = q['materials'][prim['material']]['name']
            same = [s for s in parts if s['material'] == mat]
            assert sum((s['triangles'] for s in same)) == len(ids), (mat, len(ids))
            filtered = []
            ix = 0
            for part in same:
                end = ix + part['triangles']
                if part['label'].startswith(('southeast return', 'southeast lawn return')):
                    filtered.append(ids[ix:end])
                ix = end
            if not filtered:
                continue
            ids = np.concatenate(filtered)
            sel += len(ids)
            t = v[ids].astype(float)
            vert.append(v[np.unique(ids)])
            area = np.abs((t[:, 1, 0] - t[:, 0, 0]) * (t[:, 2, 1] - t[:, 0, 1]) - (t[:, 1, 1] - t[:, 0, 1]) * (t[:, 2, 0] - t[:, 0, 0]))
            ss = [Polygon(t[i, :, :2]) for i in np.nonzero(area > 1e-09)[0]]
            shapes.append(union_all(ss))
            for tr in t[(t[:, :, 2].min(1) < cut_z - 1e-05) & (t[:, :, 2].max(1) > cut_z + 1e-05)]:
                hit = []
                for a, c in zip(tr, tr[[1, 2, 0]]):
                    if (a[2] <= cut_z) != (c[2] <= cut_z):
                        hit.append((a + (c - a) * (cut_z - a[2]) / (c[2] - a[2]))[:2])
                if len(hit) == 2 and np.linalg.norm(hit[1] - hit[0]) > 1e-06:
                    segment = LineString(hit).intersection(residual)
                    if segment.length > 1e-05:
                        segs.append(segment)
    assert shapes
    footprint = union_all(shapes)
    rest = footprint.intersection(residual)
    v = np.concatenate(vert)
    probes = [list(s.interpolate(0.5, normalized=True).coords[0]) for s in sorted(segs, key=lambda s: -s.length)[:4]]
    return {'source': p.name, 'sha256': H(b), 'triangles': total, 'return_triangles': sel, 'return_bounds_m': [v.min(0).tolist(), v.max(0).tolist()], 'actual_return_projection_area_m2': footprint.area, 'inside_existing_cut_m2': footprint.intersection(cut).area, 'inside_retained_2885_m2': rest.area, 'independent_projected_area_outside_entire_2885_m2': footprint.difference(owner).area, 'new_triangles_crossing_coarse_roof_plane_in_uncut_area': len(segs), 'roof_level_m': cut_z, 'sample_crossings_xy_m': probes}

out = {k: model(args.mesh_directory / (k + "-source.glb")) for k in ("full","lod")}
probes = {f'{k}-{i}': p for k, r in out.items() for i, p in enumerate(r['sample_crossings_xy_m'])}

def city(p):
    x, y = p
    e = x * math.sin(A) - y * math.cos(A)
    n = x * math.cos(A) + y * math.sin(A)
    a = lon + math.degrees(e / (R * math.cos(math.radians(lat))))
    l = lat + math.degrees(n / R)
    s = R * math.cos(math.radians(ready['origin_latitude']))
    return [s * math.radians(a - ready['origin_longitude']), s * (math.asinh(math.tan(math.radians(ready['origin_latitude']))) - math.asinh(math.tan(math.radians(l))))]
original = {}
decoder = w / 'decode.mjs'
for row in [ready['far'], next((x for x in ready['near'] if 2885 in x['featureLocalIds']))]:
    b = fetch(row['file'], row['sha256'])
    with tempfile.TemporaryDirectory() as tmp:
        inp = Path(tmp) / 'encoded.glb'
        dst = Path(tmp) / 'decoded.glb'
        inp.write_bytes(gzip.decompress(b) if b[:2] == b'\x1f\x8b' else b)
        subprocess.run(['node', '--input-type=module', '-', inp, dst, args.project / 'vendor/meshopt_decoder.module.js'], input=decoder.read_bytes(), check=True)
        r = read(dst, {k: city(v) for k, v in probes.items()})
    original[row['file']] = {'sha256': row['sha256'], 'decoded_sha256': r['decoded_sha256'], 'sample_crossings_first_hits_z_owner': {k: v[0] if v else None for k, v in r['heights'].items()}}
report = {'scope': 'The original city retains its accepted partial-cut courtyard front. Both new source levels were tested only for meshes explicitly named southeast return. Concave projection is the union of each nonvertical projected triangle. Strict roof-height intersections are measured where the existing clip leaves source 2885 in the city.', 'source_owner': controls['source_key'], 'source_macro': controls['macro_id'], 'protected_other_owner': 733, 'existing_cut_areas_m2': controls['polygon_areas_m2'], 'final_models': out, 'original_mesh_probes': original, 'decision': 'Keep the signed courtyard entry in the city and leave the revised return as a separate exhibit until a new partial-cut residual, closed cap and near/far original-geometry test are available. Never replace all 2885.'}

args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
