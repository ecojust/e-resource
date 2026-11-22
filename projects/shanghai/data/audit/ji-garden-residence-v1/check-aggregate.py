"""Compare the embedded UV coordinate of every roughcast vertex with its metre-space mapping."""
import argparse
import hashlib
import os
import json
from pathlib import Path
import struct
import subprocess
from tempfile import TemporaryDirectory

import numpy as np

HERE=Path(__file__).resolve().parent
if 'SHANGHAI_PROJECT_ROOT' in os.environ:
    PROJECT = Path(os.environ['SHANGHAI_PROJECT_ROOT']).resolve()
else:
    PROJECT = HERE.parents[2]

MODEL='jingan-ji-garden-residence-south-bay'


def coordinates(path):
    data=path.read_bytes()
    length=struct.unpack_from('<I',data,12)[0]
    doc=json.loads(data[20:20+length])
    binary=memoryview(data)[28+length:]
    assert not any(set(node)&{'matrix','scale','rotation','translation'} for node in doc['nodes'])
    def values(index,width):
        accessor=doc['accessors'][index]
        assert accessor['componentType']==5126 and accessor['type']==f'VEC{width}'
        view=doc['bufferViews'][accessor['bufferView']]
        offset=view.get('byteOffset',0)+accessor.get('byteOffset',0)
        return np.ndarray((accessor['count'],width),dtype='<f4',buffer=binary,offset=offset,
                          strides=(view.get('byteStride',4*width),4))
    index=next(i for i,m in enumerate(doc['materials'])if m['name']=='grey bush-hammered render')
    material=doc['materials'][index]
    texture=doc['textures'][material['pbrMetallicRoughness']['baseColorTexture']['index']]
    im=doc['images'][texture['source']]
    assert im['mimeType']=='image/png'
    bv=doc['bufferViews'][im['bufferView']]
    start=bv.get('byteOffset',0);embedded=binary[start:start+bv['byteLength']]
    original=(PROJECT/'source/precise'/MODEL/'source/street-aggregate.png').read_bytes()
    assert bytes(embedded)==original
    count=0
    maximum=0.
    for mesh in doc['meshes']:
        for part in mesh['primitives']:
            if part.get('material')!=index:continue
            a=part['attributes']
            pos=values(a['POSITION'],3).astype(float)
            uv=values(a['TEXCOORD_0'],2)
            x,y,z=pos[:,0],-pos[:,2],pos[:,1]
            expected=np.column_stack((np.clip((.81*x+.48*y+5)/12,0,1),1-np.clip(z/17.8,0,1)))
            err=float(np.max(np.abs(expected-uv)))
            assert np.isfinite(err) and err<.000015,(path,err)
            maximum=max(maximum,err)
            count+=len(uv)
    assert count>100
    return {'embedded_png_sha256':hashlib.sha256(original).hexdigest(),'vertices_checked':count,'max_abs_uv_error':maximum}


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--manifest',type=Path,required=True)
    ap.add_argument('--out',type=Path,default=PROJECT/'data/audit/ji-garden-residence-v1/effective-uv.json')
    args=ap.parse_args()
    manifest=json.loads(args.manifest.read_bytes())
    assert manifest['id']==MODEL
    output={}
    with TemporaryDirectory()as tmp:
        for role in ('raw','full','lod'):
            asset=manifest['assets'][role]
            src=args.manifest.parent/asset['file']
            digest=hashlib.sha256(src.read_bytes()).hexdigest()
            assert digest==asset['sha256']
            if role!='raw':
                decoded=Path(tmp)/(role+'.glb')
                subprocess.run(['node',PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs',src,decoded,PROJECT/'vendor/meshopt_decoder.module.js'],check=True)
            else:
                decoded=src
            output[role]={'sha256':digest,**coordinates(decoded)}
    args.out.write_text(json.dumps(output,indent=2)+'\n')
