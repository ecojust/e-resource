import numpy as np,struct,json
def read_mesh(path):
    raw=path.read_bytes();length=struct.unpack_from('<I',raw,12)[0]
    doc=json.loads(raw[20:20+length]);bin=memoryview(raw)[28+length:]
    def array(index):
        a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']]
        kind={5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']]
        count={'SCALAR':1,'VEC3':3}[a['type']];size=np.dtype(kind).itemsize
        return np.ndarray((a['count'],count),kind,buffer=bin,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',count*size),size))
    for node in doc['nodes']:
        assert set(node).issubset({'name','mesh'}), 'Unbaked parent/transform in this input'
        for p in doc['meshes'][node['mesh']]['primitives']:
            v=array(p['attributes']['POSITION']).astype(float)
            triangles=v[array(p['indices']).reshape(-1,3)]
            xyz=triangles[:,:,[0,2,1]]
            xyz[:,:,1]*=-1
            yield doc['materials'][p['material']]['name'],xyz
