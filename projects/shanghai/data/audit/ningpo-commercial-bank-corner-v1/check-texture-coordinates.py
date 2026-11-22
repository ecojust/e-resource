"""Compare the embedded UV coordinate of every granite vertex with its metre-space mapping."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
from tempfile import TemporaryDirectory

import numpy as np

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
MODEL='huangpu-ningpo-commercial-bank-corner'


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
    index=next(i for i,m in enumerate(doc['materials'])if m['name']=='bush-hammered granite')
    count=0
    maximum=0.
    for mesh in doc['meshes']:
        for part in mesh['primitives']:
            if part.get('material')!=index:continue
            a=part['attributes']
            pos=values(a['POSITION'],3).astype(float)
            uv=values(a['TEXCOORD_0'],2)
            x,y,z=pos[:,0],-pos[:,2],pos[:,1]
            expected=np.column_stack(((x+.73*y)/.83,1-(z/.83+.27*y)))
            err=float(np.max(np.abs(expected-uv)))
            assert np.isfinite(err) and err<.000015,(path,err)
            maximum=max(maximum,err)
            count+=len(uv)
    assert count>100
    return {'vertices_checked':count,'max_abs_uv_error':maximum}


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--manifest',type=Path,required=True)
    ap.add_argument('--out',type=Path,default=HERE/'effective-uv.json')
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
