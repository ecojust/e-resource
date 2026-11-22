"""Verify UV area on each textured stone triangle in the actual decoded GLB."""
import hashlib
import io
import json
from pathlib import Path
import struct
import numpy as np


def check(path):
    data=path.read_bytes();size=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+size]);binary=data[28+size:]
    types={5120:'i1',5121:'u1',5122:'<i2',5123:'<u2',5125:'<u4',5126:'<f4'}
    def accessor(i):
        a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']];n={'SCALAR':1,'VEC2':2,'VEC3':3}[a['type']];typ=np.dtype(types[a['componentType']]);stride=v.get('byteStride',n*typ.itemsize)
        assert not a.get('sparse') and not a.get('normalized',False)
        return np.ndarray((a['count'],n),typ,binary,v.get('byteOffset',0)+a.get('byteOffset',0),strides=(stride,typ.itemsize))
    result={}
    for mesh in doc['meshes']:
        for p in mesh['primitives']:
            material=doc['materials'][p['material']];name=material['name'];t=material['pbrMetallicRoughness'].get('baseColorTexture');
            if not name.startswith('Tablet | ') or t is None:continue
            assert p.get('mode',4)==4
            uv=accessor(p['attributes']['TEXCOORD_0']).astype(float)
            idx=accessor(p['indices']).ravel().reshape(-1,3) if 'indices' in p else np.arange(len(uv)).reshape(-1,3)
            a,b,c=uv[idx].transpose(1,0,2);e=b-a;f=c-a;area=.5*abs(e[:,0]*f[:,1]-e[:,1]*f[:,0]);img=doc['images'][doc['textures'][t['index']]['source']];v=doc['bufferViews'][img['bufferView']];start=v.get('byteOffset',0);sha=hashlib.sha256(binary[start:start+v['byteLength']]).hexdigest()
            if name not in result:result[name]={'triangle_count':0,'zero_area_triangles':0,'minimum_uv_area':1e30,'embedded_image_sha256':sha}
            item=result[name];item['triangle_count']+=len(area);item['zero_area_triangles']+=int(np.sum(area<1e-12));item['minimum_uv_area']=min(item['minimum_uv_area'],float(area.min()));assert item['embedded_image_sha256']==sha
    assert set(result)=={'Tablet | exposed aggregate','Tablet | grey hood stone'}
    return {'sha256':hashlib.sha256(data).hexdigest(),'source':path.name,'materials':result,'passed':all(v['zero_area_triangles']==0 for v in result.values())}

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mesh',type=Path);p.add_argument('output',type=Path);a=p.parse_args();r=check(a.mesh);a.output.write_text(json.dumps(r,indent=1)+'\n');print(r);raise SystemExit(0 if r['passed'] else 1)
