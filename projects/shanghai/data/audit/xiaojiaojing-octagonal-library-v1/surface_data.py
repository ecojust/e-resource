"""Read indexed triangles and material slots from the raw or independently decoded GLB."""
from pathlib import Path
import json,struct
import numpy as np
def triangles(path):
    data=Path(path).read_bytes();length,typ=struct.unpack_from('<II',data,12)
    assert data[:4]==b'glTF' and typ==0x4e4f534a
    scene=json.loads(data[20:20+length]);start=28+length
    def array(i):
        a=scene['accessors'][i];v=scene['bufferViews'][a['bufferView']]
        dtype=np.dtype({5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']])
        width={'SCALAR':1,'VEC3':3}[a['type']]
        off=start+v.get('byteOffset',0)+a.get('byteOffset',0)
        return np.ndarray((a['count'],width),dtype=dtype,buffer=data,offset=off,strides=(v.get('byteStride',dtype.itemsize*width),dtype.itemsize))
    geometry=[];slots=[]
    for node in scene['nodes']:
        if 'mesh' not in node:continue
        assert all(k not in node for k in ['rotation','translation','scale','matrix'])
        for primitive in scene['meshes'][node['mesh']]['primitives']:
            positions=array(primitive['attributes']['POSITION'])
            indices=array(primitive['indices']).reshape(-1,3)
            xyz=positions[indices][:,:,[0,2,1]].astype(np.float64)
            xyz[:,:,1]*=-1
            geometry.append(xyz);slots.append(np.full(len(xyz),primitive['material'],np.int16))
    return np.concatenate(geometry),np.concatenate(slots),scene['materials']
