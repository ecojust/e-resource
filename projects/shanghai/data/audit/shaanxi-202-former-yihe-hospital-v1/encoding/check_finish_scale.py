"""Read an uncompressed or decoded GLB and measure the real texture period on every face edge."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import numpy as np

PERIODS={'Yihe | buff courtyard masonry':1.84,'Yihe | grey granite ashlar':1.26,'Yihe | grey step granite':1.52}
TYPES={5126:'<f4',5123:'<u2',5125:'<u4',5121:'u1'}
def measure(path):
    blob=path.read_bytes();size=struct.unpack_from('<I',blob,12)[0];doc=json.loads(blob[20:20+size])
    payload=memoryview(blob)[28+size:];names=[x['name'] for x in doc['materials']]
    def read(i):
        a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']];n={'VEC2':2,'VEC3':3,'SCALAR':1}[a['type']]
        dtype=np.dtype(TYPES[a['componentType']]);base=v.get('byteOffset',0)+a.get('byteOffset',0)
        return np.ndarray((a['count'],n),dtype=dtype,buffer=payload,offset=base,
                          strides=(v.get('byteStride',dtype.itemsize*n),dtype.itemsize))
    measurements={n:[] for n in PERIODS}
    def node(i,parent):
        item=doc['nodes'][i]
        if 'matrix' in item:m=np.array(item['matrix']).reshape(4,4).T
        else:
            assert 'rotation' not in item
            m=np.eye(4);m[:3,:3]=np.diag(item.get('scale',[1,1,1]));m[:3,3]=item.get('translation',[0,0,0])
        m=parent@m
        for prim in doc['meshes'][item['mesh']]['primitives'] if 'mesh' in item else []:
            name=names[prim['material']]
            if name not in PERIODS:continue
            ix=read(prim['indices']).reshape(-1,3);xyz=read(prim['attributes']['POSITION']).astype(np.float64)@m[:3,:3].T
            uv=read(prim['attributes']['TEXCOORD_0']).astype(np.float64)
            world=np.linalg.norm(xyz[ix]-xyz[np.roll(ix,1,axis=1)],axis=2)
            texture=np.linalg.norm(uv[ix]-uv[np.roll(ix,1,axis=1)],axis=2)*PERIODS[name]
            measurements[name].append(np.abs(texture-world))
        for c in item.get('children',[]):node(c,m)
    for i in doc['scenes'][doc.get('scene',0)]['nodes']:node(i,np.eye(4))
    out={}
    for name,groups in measurements.items():
        e=np.concatenate(groups,axis=0);out[name]={'triangles':len(e),'triangle_edges':e.size,'uv_cycle_m':PERIODS[name],
              'max_edge_error_m':float(e.max()),'p99_edge_error_m':float(np.percentile(e,99))}
        if e.max()>.00001:raise ValueError(out[name])
    return {'mesh_sha256':hashlib.sha256(blob).hexdigest(),'materials':out}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mesh',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    r=measure(a.mesh);a.output.write_text(json.dumps(r,indent=2)+'\n')
