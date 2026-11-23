"""Verify original embedded colour/relief and each UV corner against actual metre-space triangles."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np

HERE=Path(__file__).resolve().parent
src=HERE.parent/'source'
sys.path.insert(0,str(src))
from court_finishes import BRICK,FILENAMES,NORMAL_FILENAMES,REPEAT_METRES,PHASE_X,PHASE_V,BED_DRIFT

shared=HERE.parents[1]/'xuhui-yanqing-121-brick-front/measurements/check_brick_uv.py'
spec=importlib.util.spec_from_file_location('serial_dafuli_finish_reader',shared)
reader=importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)


def verify(mesh):
    doc,blob,digest=reader.glb(mesh)
    materials={}
    for m in doc['meshes']:
        for prim in m['primitives']:
            mat=doc['materials'][prim['material']]
            name=mat['name']
            if name not in REPEAT_METRES:
                continue
            row={}
            for key,info,filename in [('base',mat['pbrMetallicRoughness']['baseColorTexture'],FILENAMES[name]),
                                      ('normal',mat['normalTexture'],NORMAL_FILENAMES[name])]:
                tex=doc['textures'][info['index']]
                sam=doc.get('samplers',[{}])[tex.get('sampler',0)]
                img=doc['images'][tex['source']]
                v=doc['bufferViews'][img['bufferView']]
                off=v.get('byteOffset',0)
                exact=blob[off:off+v['byteLength']]==(src/filename).read_bytes()
                assert exact and img['mimeType']=='image/png' and info.get('texCoord',0)==0
                assert sam.get('wrapS',10497)==sam.get('wrapT',10497)==10497 and info.get('scale',1.)==1.
                row[key]=dict(original_png_sha256=hashlib.sha256((src/filename).read_bytes()).hexdigest(),exact=exact)
            idx=reader.read_accessor(doc,blob,prim['indices']).reshape(-1,3)
            verts=reader.read_accessor(doc,blob,prim['attributes']['POSITION']).astype(float)
            p=(verts[:,[0,2,1]]*[1,-1,1])[idx]
            uv=reader.read_accessor(doc,blob,prim['attributes']['TEXCOORD_0']).astype(float)[idx]
            n=np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0])
            n/=np.linalg.norm(n,axis=1)[:,None]
            t=np.stack([-n[:,1],n[:,0],np.zeros(len(n))],axis=-1)
            wall=abs(n[:,2])<=.9
            t[wall]/=np.linalg.norm(t[wall],axis=1)[:,None]
            up=np.cross(n,t)
            t[~wall]=[1,0,0];up[~wall]=[0,1,0]
            reference=np.stack([np.einsum('tpi,ti->tp',p,axis)for axis in (t,up)],axis=-1)
            if name==BRICK:
                reference+=np.array([PHASE_X,PHASE_V])
                vertical=abs(n[:,2])<.1
                reference[vertical,:,1]+=BED_DRIFT*p[vertical,:,0]
            err=abs(uv*REPEAT_METRES[name]-reference)
            row.update(oriented_corners=int(idx.size),maximum_position_error_m=float(err.max()),repeat_u_v_m=REPEAT_METRES[name])
            assert err.max()<.00002
            materials[name]=row
    assert set(materials)==set(REPEAT_METRES)
    return dict(file=mesh.name,sha256=digest,checks='Embedded colour and tangent-normal PNGs, shared UV set and REPEAT sampler, all triangle corners including metric pitch, intercept and measured mortar drift.',materials=materials)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mesh',type=Path)
    p.add_argument('output',type=Path)
    a=p.parse_args()
    report=verify(a.mesh)
    a.output.write_text(json.dumps(report,indent=2)+'\n')
    print(report['sha256'],sum(v['oriented_corners'] for v in report['materials'].values()))
