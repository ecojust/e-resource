"""Clip a project GLB at a photographic camera's near plane, retaining its materials and UVs."""
import json
from pathlib import Path
import struct

import numpy as np


def clip_near_plane(source, target, camera, near_m=.08):
    raw = source.read_bytes()
    json_length = struct.unpack_from('<I', raw, 12)[0]
    doc = json.loads(raw[20:20+json_length])
    data = bytearray(raw[28+json_length:][:doc['buffers'][0]['byteLength']])
    shapes = {'VEC3':3, 'VEC2':2, 'SCALAR':1}
    dtypes = {5126:'<f4', 5125:'<u4', 5123:'<u2', 5121:'u1'}
    def read(index):
        a = doc['accessors'][index]
        b = doc['bufferViews'][a['bufferView']]
        dtype = np.dtype(dtypes[a['componentType']])
        dim = shapes[a['type']]
        return np.ndarray((a['count'],dim),dtype=dtype,buffer=data,
                          offset=b.get('byteOffset',0)+a.get('byteOffset',0),
                          strides=(b.get('byteStride',dim*dtype.itemsize),dtype.itemsize)).copy()

    def add(array, component, kind):
        data.extend(b'\0'*(-len(data)%4))
        raw_array = np.ascontiguousarray(array, dtype=dtypes[component])
        start = len(data)
        data.extend(raw_array.tobytes())
        index = len(doc['bufferViews'])
        doc['bufferViews'].append(dict(buffer=0, byteOffset=start, byteLength=raw_array.nbytes))
        doc['accessors'].append(dict(bufferView=index,componentType=component,count=len(array),type=kind,
                                     min=raw_array.min(axis=0).reshape(-1).tolist(),
                                     max=raw_array.max(axis=0).reshape(-1).tolist()))
        return len(doc['accessors'])-1

    plane = camera[2] / np.linalg.norm(camera[2,:3])
    traversed = removed = clipped = emitted = 0
    for mesh in doc['meshes']:
        result = []
        for primitive in mesh['primitives']:
            attributes = primitive['attributes']
            p = read(attributes['POSITION'])
            indices = read(primitive['indices']).reshape(-1,3)
            traversed += len(indices)
            enu = p[:,[0,2,1]] * [1,-1,1]
            depth = enu @ plane[:3] + plane[3]
            if depth.min() > near_m:
                result.append(primitive)
                emitted += len(indices)
                continue
            keep = depth[indices] >= near_m
            entirely_in = keep.all(axis=1)
            mixed = keep.any(axis=1) & ~entirely_in
            removed += len(indices)-int(entirely_in.sum())-int(mixed.sum())
            clipped += int(mixed.sum())
            if not np.any(keep):
                continue
            names = list(attributes)
            streams = [read(attributes[n]) for n in names]
            spans = np.cumsum([0]+[a.shape[1] for a in streams])
            points = np.column_stack([*streams, depth])
            # Keep the native vertex order and attributes for all uncut triangles.
            used, compact = np.unique(indices[entirely_in].reshape(-1), return_inverse=True)
            vertices = list(points[used])
            triangles = compact.reshape(-1,3).tolist()
            for face in indices[mixed]:
                polygon = []
                for ia, ib in zip(face, np.roll(face,-1)):
                    a, b = points[ia], points[ib]
                    if a[-1] >= near_m:
                        polygon.append(a)
                    if (a[-1] < near_m) != (b[-1] < near_m):
                        f = (near_m-a[-1])/(b[-1]-a[-1])
                        polygon.append(a + (b-a)*f)
                first = len(vertices)
                vertices.extend(polygon)
                triangles.extend([first, first+i, first+i+1] for i in range(1,len(polygon)-1))
            verts = np.array(vertices)
            out = dict(primitive)
            out['attributes'] = {
                name: add(verts[:,spans[i]:spans[i+1]],5126,doc['accessors'][attributes[name]]['type'])
                for i,name in enumerate(names)}
            out['indices'] = add(np.asarray(triangles).reshape(-1,1),5125,'SCALAR')
            result.append(out)
            emitted += len(triangles)
        mesh['primitives'] = result
    doc['buffers'][0]['byteLength'] = len(data)
    header = json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode()
    header += b' '*(-len(header)%4)
    data.extend(b'\0'*(-len(data)%4))
    with target.open('wb') as out:
        out.write(struct.pack('<4sIIII',b'glTF',2,28+len(header)+len(data),len(header),0x4e4f534a))
        out.write(header)
        out.write(struct.pack('<II',len(data),0x004e4942))
        out.write(data)
    return dict(near_clip_m=near_m,source_triangles=traversed,fully_behind=removed,
                intersecting_plane=clipped,triangles_after_clipping=emitted)
