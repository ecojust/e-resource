"""Compare the embedded UV coordinate of every stone vertex with its metre-space mapping."""
import argparse
import hashlib
from io import BytesIO
import json
from PIL import Image
from pathlib import Path
import struct
import subprocess
from tempfile import TemporaryDirectory

import numpy as np

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
MODEL='huangpu-zhongxing-bank-curved-front'


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
    index=next(i for i,m in enumerate(doc['materials'])if m['name']=='cream jointed facing')
    texture_index=doc['materials'][index]['pbrMetallicRoughness']['baseColorTexture']['index']
    texture=doc['textures'][texture_index]
    sampler=doc['samplers'][texture['sampler']] if 'sampler' in texture else {}
    wraps=[sampler.get(axis,10497) for axis in ('wrapS','wrapT')]
    assert wraps==[10497,10497], (path,wraps)
    view=doc['bufferViews'][doc['images'][texture['source']]['bufferView']]
    image_bytes=bytes(binary[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']])
    pixels=np.asarray(Image.open(BytesIO(image_bytes)).convert('RGB'))
    height,width=pixels.shape[:2]
    differences=0
    outside=0
    count=0
    maximum=0.
    for mesh in doc['meshes']:
        for part in mesh['primitives']:
            if part.get('material')!=index:continue
            a=part['attributes']
            pos=values(a['POSITION'],3).astype(float)
            uv=values(a['TEXCOORD_0'],2)
            x,y,z=pos[:,0],-pos[:,2],pos[:,1]
            import sys
            sys.path.insert(0,str(PROJECT/'source/precise/huangpu-zhongxing-bank-curved-front/source'))
            from stone import wall_uv
            expected=np.array([wall_uv(*v) for v in zip(x,y,z)])
            err=float(np.max(np.abs(expected-uv)))
            assert np.isfinite(err) and err<.000015,(path,err)
            maximum=max(maximum,err)
            outside+=int(np.count_nonzero(np.any((uv<0)|(uv>1),axis=1)))
            indices=lambda values,sz:np.clip((values*sz).astype(int),0,sz-1)
            repeat_uv=uv-np.floor(uv)
            tile=pixels[indices(repeat_uv[:,1],height),indices(repeat_uv[:,0],width)]
            clamp=pixels[indices(np.clip(uv[:,1],0,1),height),indices(np.clip(uv[:,0],0,1),width)]
            differences+=int(np.count_nonzero(np.any(tile!=clamp,axis=1)))
            count+=len(uv)
    assert count>100
    assert differences>40 and outside>40
    return {'vertices_checked':count,'max_abs_uv_error':maximum,'wrap_s_t':wraps,'embedded_image_sha256':hashlib.sha256(image_bytes).hexdigest(),'outside_first_tile':outside,'distinct_repeat_vs_clamp_vertex_samples':differences}


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
