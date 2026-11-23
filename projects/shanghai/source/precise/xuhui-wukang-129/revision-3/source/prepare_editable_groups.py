"""Regroup the exact float32 source triangles using the original per-part order.

The raw writer orders primitives by material, retaining the original triangle
sequence within each material. Only one architectural group is expanded at a
time. Vertices are welded within each original closed part, never across parts.
"""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import struct
import numpy as np


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def prepare_groups(out,raw,sidecar,metadata):
    index=json.loads(sidecar.read_bytes())
    if index['sha256']!=sha(raw):raise ValueError('Part order is from a different source mesh')
    blob=raw.read_bytes()
    header=struct.unpack_from('<I',blob,12)[0]
    doc=json.loads(blob[20:20+header]); binary=memoryview(blob)[28+header:]
    def array(accessor):
        a=doc['accessors'][accessor]; view=doc['bufferViews'][a['bufferView']]
        dtype=np.dtype({5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']])
        columns={'SCALAR':1,'VEC3':3}[a['type']]
        return np.ndarray((a['count'],columns),dtype,buffer=binary,offset=view.get('byteOffset',0)+a.get('byteOffset',0),
                          strides=(view.get('byteStride',dtype.itemsize*columns),dtype.itemsize))
    primitives={};palette={};image_counts={}
    for mesh in doc['meshes']:
        for p in mesh['primitives']:
            material=doc['materials'][p['material']]
            name=material['name'];pbr=material['pbrMetallicRoughness']
            if name in primitives:raise ValueError('Expected a single primitive per material')
            xyz=array(p['attributes']['POSITION'])
            triangles=array(p['indices']).reshape(-1,3)
            primitives[name]=xyz,triangles
            palette[name]={'color':pbr.get('baseColorFactor',[1,1,1,1])[:3],'metallic':pbr.get('metallicFactor',1.),'roughness':pbr.get('roughnessFactor',1.)}
            if 'baseColorTexture' in pbr:image_counts[name]=triangles.size
    offsets=defaultdict(int); groups=defaultdict(list)
    for part in index['part_summary']:
        label=part['label'];mat=part['material'];start=offsets[mat];stop=start+part['triangles']
        groups[label].append((mat,start,stop));offsets[mat]=stop
    for mat,(_,triangles) in primitives.items():
        if offsets[mat]!=len(triangles):raise ValueError('Triangle partition mismatch for '+mat)
    aliases={};names=[];dest=out/'editable-parts.json';partial=dest.with_suffix('.partial')
    with partial.open('w') as f:
        f.write('{"metadata":'+json.dumps(metadata,ensure_ascii=False)+',"palette":'+json.dumps(palette,ensure_ascii=False)+',"groups":{')
        for label,segments in groups.items():
            name=label
            if len(name.encode())>63:name=name.encode()[:50].decode(errors='ignore').rstrip()+' '+hashlib.sha256(label.encode()).hexdigest()[:9]
            if name in names:raise ValueError('Editable group name collision')
            if label!=name:aliases[name]=label
            if names:f.write(',')
            names.append(name)
            vertices=[];faces=[];materials=[];face_materials=[]
            for mat,start,stop in segments:
                xyz,indices=primitives[mat];points=xyz[indices[start:stop]].reshape(-1,3)
                unique,mapping=np.unique(points,axis=0,return_inverse=True)
                base=len(vertices)
                vertices.extend((unique[:,[0,2,1]]*np.array([1.,-1.,1.])).tolist())
                faces.extend((base+mapping.reshape(-1,3)).tolist())
                if mat not in materials:materials.append(mat)
                face_materials.extend([materials.index(mat)]*(stop-start))
            f.write(json.dumps(name,ensure_ascii=False)+':')
            json.dump(dict(v=vertices,f=faces,materials=materials,face_materials=face_materials),f,separators=(',',':'),ensure_ascii=False)
        f.write('}}\n')
    partial.replace(dest)
    return names,aliases,index['triangles'],image_counts
