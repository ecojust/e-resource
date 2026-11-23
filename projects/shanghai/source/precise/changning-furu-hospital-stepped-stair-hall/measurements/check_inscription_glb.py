"""Check oriented GLB solids and project the archival relief into the three published viewpoints.

Run with the full or LOD source GLB, its matching geometry report and the desired output path.
The district image has individually observed character rectangles. The second historic image
and the contemporary road station are geometric projections, without independent glyph boxes.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import struct

HERE = Path(__file__).absolute().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decode_groups(mesh, order):
    data = mesh.read_bytes()
    assert data[:4] == b'glTF' and len(data) == struct.unpack_from('<I', data, 8)[0]
    length = struct.unpack_from('<I', data, 12)[0]
    doc = json.loads(data[20:20+length])
    binary = memoryview(data)[28+length:]
    def values(index):
        entry = doc['accessors'][index]
        view = doc['bufferViews'][entry['bufferView']]
        types = {5121:'B', 5123:'H', 5125:'I', 5126:'f'}
        n = {'SCALAR':1, 'VEC3':3}[entry['type']]
        fmt = struct.Struct('<'+types[entry['componentType']]*n)
        offset = view.get('byteOffset', 0) + entry.get('byteOffset', 0)
        stride = view.get('byteStride', fmt.size)
        return [fmt.unpack_from(binary, offset+i*stride) for i in range(entry['count'])]
    assert len(doc['meshes']) == len(doc['nodes']) == 1 and set(doc['nodes'][0]) <= {'mesh','name'}
    report = json.loads(order.read_bytes())
    assert report['sha256'] == digest(mesh)
    grouped = []
    for prim in doc['meshes'][0]['primitives']:
        material = doc['materials'][prim['material']]['name']
        verts = [(x,-z,y) for x,y,z in values(prim['attributes']['POSITION'])]
        indices = [i for i, in values(prim['indices'])]
        start = 0
        for part in report['part_summary']:
            if part['material'] != material:
                continue
            count = 3*part['triangles']
            triangles = [[verts[indices[i+j]] for j in range(3)] for i in range(start,start+count,3)]
            grouped.append((part['label'], material, triangles))
            start += count
        assert start == len(indices)
    assert len(grouped) == report['parts']
    return grouped


def dot(a,b):
    return sum(x*y for x,y in zip(a,b))


def sub(a,b):
    return [x-y for x,y in zip(a,b)]


def cross(a,b):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def solid(label, tris):
    edges = Counter()
    volume6 = 0.
    anchor = tris[0][0]
    for a,b,c in tris:
        edges.update([(a,b),(b,c),(c,a)])
        volume6 += dot(sub(a,anchor),cross(sub(b,anchor),sub(c,anchor)))
    unbalanced = sum(edges[a,b]!=edges[b,a] for a,b in edges)
    nonmanifold = sum(edges[a,b]!=1 for a,b in edges)
    return dict(label=label, triangles=len(tris), unbalanced_directed_edges=unbalanced,
                other_than_two_incident_faces=nonmanifold, signed_volume_m3=volume6/6)


def pixels(camera,p):
    v = sub(p,camera['C'])
    q = [dot(row,v) for row in camera['R']]
    h = [dot(row,q) for row in camera['K']]
    return (h[0]/h[2],h[1]/h[2],q[2])


def bounds(points):
    return [min(p[0] for p in points), min(p[1] for p in points),
            max(p[0] for p in points), max(p[1] for p in points)]


def compare(box,observed):
    cx,cy = (box[0]+box[2])/2, (box[1]+box[3])/2
    ox,oy = (observed[0]+observed[2])/2, (observed[1]+observed[3])/2
    dx = max(0, min(box[2],observed[2])-max(box[0],observed[0]))
    dy = max(0, min(box[3],observed[3])-max(box[1],observed[1]))
    area = lambda b: (b[2]-b[0])*(b[3]-b[1])
    return dict(observed_native_bounds=observed,centre_error_px=round(math.hypot(cx-ox,cy-oy),3),
                boxes_iou=round(dx*dy/(area(box)+area(observed)-dx*dy),4))


def inspect(mesh,order):
    groups = decode_groups(mesh,order)
    checks = [solid(name,triangles) for name,_,triangles in groups]
    assert all(r['unbalanced_directed_edges']==0 and r['signed_volume_m3']>0 for r in checks)
    stations_path = HERE/'registered-stair-stations.json'
    survey_path = HERE.parent/'source/archive-inscription.json'
    survey = json.loads(survey_path.read_bytes())
    cameras = json.loads(stations_path.read_bytes())['stations']
    signs = defaultdict(list)
    for name,material,tris in groups:
        if name.startswith('archival hospital name/'):
            assert material == 'Furu | chalk grey cement'
            signs[name.split('/')[-1]].extend(p for t in tris for p in t)
    assert set(signs) == set(survey['text']) and len(survey['glyphs'])==11
    result = {}
    for key in ('district-archive','press-archive','road-centre'):
        cam = cameras[key]
        rows = []
        for reading in survey['glyphs']:
            char = reading['character']
            pts = [pixels(cam,v) for v in set(signs[char])]
            assert min(p[2] for p in pts)>0
            box = bounds(pts)
            row = dict(character=char, projected_native_bounds=[round(x,3) for x in box],
                       wholly_in_image=box[0]>=0 and box[1]>=0 and box[2]<cam['width'] and box[3]<cam['height'])
            if key=='district-archive':
                row.update(compare(box,reading['native_bbox']))
            rows.append(row)
        result[key] = rows
    return dict(mesh_sha256=digest(mesh),order_sha256=digest(order),
                observations_sha256=digest(survey_path),cameras_sha256=digest(stations_path),
                closure=checks,glyphs=result,note='District rectangles constrain position and size. Letterforms use Noto Serif CJK, as documented. Other projections refer to the same archival phase; the street photograph is used for architectural checks.')
    

if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    for name in ('mesh','order','out'):
        cli.add_argument(name,type=Path)
    args = cli.parse_args()
    args.out.write_text(json.dumps(inspect(args.mesh,args.order),ensure_ascii=False,indent=2)+'\n')

