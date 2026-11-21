"""Measure the UV coordinates of the joint model in each block's original wall frame."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import runpy

import numpy as np

AUDIT=Path(__file__).resolve().parent.parent
SOURCE=AUDIT.parents[1]/'source/precise/xuhui-foncim-apartments-d-e'
read_mesh=runpy.run_path(AUDIT/'postal-office-v1/independent-glb-review-helpers.py')['load_triangles']
read_tex=runpy.run_path(AUDIT/'fifth-textile-warehouse-river-front-v1/inspect-export.py')['load_textures']

def inspect(file):
    triangles, material_ids, names, _=read_mesh(file)
    textures, embedded, coordinates, _=read_tex(file,material_ids)
    mat=names.index('Chestnut and warm ochre horizontal render')
    sig=hashlib.sha256((SOURCE/'source/chestnut-ochre-courses.png').read_bytes()).hexdigest()
    assert embedded[mat]['embedded_sha256']==sig
    samp=textures[mat][1]
    assert samp.get('wrapS',10497)==samp.get('wrapT',10497)==10497
    tex=material_ids==mat; faces=triangles[tex]; uv=coordinates[tex]
    south=faces[:,:,1].mean(axis=1)>24
    report={}
    for name,wanted in [('D',~south),('E',south)]:
        block=faces[wanted].copy()
        if name=='E':
            ref=json.loads((SOURCE/'measurements/site-frame.json').read_bytes())['old_floorplates']['E']
            angle=math.radians(ref['local_rotation_degrees']);co,si=math.cos(angle),math.sin(angle)
            block[:,:,:2]=(block[:,:,:2]-np.array(ref['local_origin_xy']))@np.array([[co,-si],[si,co]])
            head,pitch=3.05+.71,3.40
        else:
            north=json.loads((SOURCE/'measurements/d-north-plan.json').read_bytes())
            head,pitch=north['ground_head_m']+.79,north['upper_storey_m']
        normal=np.abs(np.cross(block[:,1]-block[:,0],block[:,2]-block[:,0]))
        axis=(normal>=normal.max(axis=1,keepdims=True)*(1-1.e-5)).argmax(axis=1)
        x,y,z=block.transpose(2,0,1)
        u=np.where(axis[:,None]==0,y,x)/2.08
        v=np.where(axis[:,None]==2,y/2.08,(z-head)/pitch)
        expected=np.stack([u,1-v],axis=-1)
        error=float(np.abs(uv[wanted]-expected).max())
        assert len(block)>500 and set(axis)=={0,1,2} and error<.00015,(name,len(block),error)
        report[name]=dict(triangles=len(block),period_m=[2.08,pitch],sill_m=head,max_uv_error=error)
    return dict(triangles=len(faces),embedded_texture_sha256=sig,repeat_s=True,repeat_t=True,
                max_uv_error=max(v['max_uv_error']for v in report.values()),blocks=report)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for label in ['raw','full','lod','output']:parser.add_argument(label,type=Path)
    p=parser.parse_args();r={k:inspect(getattr(p,k))for k in ['raw','full','lod']}
    p.output.write_text(json.dumps(r,indent=2)+'\n')
