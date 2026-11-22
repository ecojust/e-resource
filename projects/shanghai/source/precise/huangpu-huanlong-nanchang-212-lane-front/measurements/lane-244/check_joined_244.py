"""Check the photographed Lane 244 surfaces and open gates in an exported joined GLB."""
import hashlib
import json
from pathlib import Path
import struct
import sys

import numpy as np

folder = Path(__file__).resolve().parent
if not (folder/'photogrammetry.json').is_file():
    folder = Path(sys.argv[1])
    paths = list(map(Path, sys.argv[2:]))
else:
    paths = list(map(Path, sys.argv[1:]))
sys.path.insert(0, str(folder))
sys.path.insert(0, str(folder.parents[1]/'source'))
from check_component import ray, transform
from separate_entries import location

def read_scene(p):
    blob = p.read_bytes()
    magic, version, length, size, section = struct.unpack_from('<4sIIII', blob)
    assert magic == b'glTF' and version == 2 and length == len(blob) and section == 0x4E4F534A
    doc = json.loads(blob[20:20+size])
    assert doc['nodes'] == [{'name': doc['nodes'][0]['name'], 'mesh': 0}]
    start = 28 + size
    types = {5121: '<u1',5123: '<u2',5125: '<u4',5126: '<f4'}
    def array(i):
        a = doc['accessors'][i]
        v = doc['bufferViews'][a['bufferView']]
        dt = np.dtype(types[a['componentType']])
        width = {'SCALAR': 1,'VEC3': 3}[a['type']]
        return np.ndarray((a['count'],width),dtype=dt,buffer=blob,offset=start+v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',width*dt.itemsize),dt.itemsize))
    inverse = np.linalg.inv(location())
    triangles, materials, names = [], [], []
    all_bounds = []
    for prim in doc['meshes'][0]['primitives']:
        pos = array(prim['attributes']['POSITION']).astype(np.float64)
        xyz = np.stack((pos[:,0],-pos[:,2],pos[:,1]),axis=1)
        local = xyz @ inverse[:3,:3].T + inverse[:3,3]
        material = doc['materials'][prim['material']]['name']
        # 212 and 244 have different local coordinates. Include any other geometry
        # whose projected bounds reach this same doorway and could obscure a ray.
        all_bounds.append((material,float(local[:,0].min()),float(local[:,0].max())))
        if local[:,0].max() < -12 or local[:,0].min() > 12:continue
        if local[:,1].max() < -12 or local[:,1].min() > 12:continue
        tr = local[array(prim['indices']).reshape((-1,3))]
        materials.extend([len(names)]*len(tr))
        names.append(material)
        triangles.append(tr)
    return np.concatenate(triangles), np.array(materials), names, len(all_bounds), hashlib.sha256(blob).hexdigest()

def check(p):
    tris,ids,names,nm,digest = read_scene(p)
    base = json.loads((folder/'component-check.json').read_bytes())['full']
    tests = []
    for record in base['rays']:
        eye, camera, _ = transform(record['view'])
        hit = ray(tris,eye,np.linalg.solve(camera,[*record['pixel'],1.]))
        label = names[ids[hit]] if hit is not None else None
        assert label and label.split(' | ')[-1] == record['expected'], (p,record,label)
        tests.append([record['view'],record['pixel'],label])
    sections=[]
    for record in base['gate_sections']:
        k=ray(tris,np.array([3.,record['y'],record['z']]),np.array([-1.,0.,0.]))
        label=names[ids[k]] if k is not None else None
        assert ('dark iron gate' in (label or ''))==(record['expected']=='iron'), (record,label)
        sections.append([record['y'],record['z'],record['expected'],label])
    return dict(file=p.name,sha256=digest,scene_material_primitives=nm,local_triangles=len(tris),local_materials=names,photograph_rays=tests,grille_rays=sections)

if __name__=='__main__':
    a=location()
    assert np.allclose(a[:3,:3].T@a[:3,:3],np.eye(3),atol=2e-8)
    print(json.dumps(dict(assembly_transform_xyz=a.tolist(),doors_separation_m=float(np.linalg.norm(a[:2,3])),roles=[check(p)for p in paths]),ensure_ascii=False,indent=2))
