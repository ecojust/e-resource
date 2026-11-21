"""Verify the repeated grey brick image and the projector on all decoded masonry faces."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy

import numpy as np

AUDIT=Path(__file__).resolve().parent.parent
SOURCE=AUDIT.parents[1]/'source/precise/xuhui-zikawei-observatory-1908/source'
read_triangles=runpy.run_path(AUDIT/'postal-office-v1/independent-glb-review-helpers.py')['load_triangles']
read_tex=runpy.run_path(AUDIT/'fifth-textile-warehouse-river-front-v1/inspect-export.py')['load_textures']


def inspect(mesh):
    tri,materials,names,_=read_triangles(mesh)
    loaded,embedded,coords,_=read_tex(mesh,materials)
    mat=names.index('Observatory grey brick');img=SOURCE/'observatory-grey-brick.png'
    sha=hashlib.sha256(img.read_bytes()).hexdigest()
    assert set(embedded)=={mat} and embedded[mat]['embedded_sha256']==sha
    assert embedded[mat]['texture_dimensions']==[640,256]
    sampler=loaded[mat][1]
    assert all(sampler.get(k,10497)==10497 for k in ['wrapS','wrapT'])
    faces=tri[materials==mat];uv=coords[materials==mat]
    normals=np.abs(np.cross(faces[:,1]-faces[:,0],faces[:,2]-faces[:,0]))
    nx,ny,nz=faces.transpose(2,0,1)
    err=[]
    for axis in range(3):
        u=(ny if axis==0 else nx)/1.60
        v=1-(ny if axis==2 else nz)/.64
        expected=np.stack([u,v],axis=-1)
        e=np.max(np.abs(uv-expected),axis=(1,2))
        # A diagonal reveal can have two equal dominant axial components. Its
        # exact double-precision classification can change after GLB FLOAT32.
        allowed=normals[:,axis]>=normals.max(axis=1)*.99985
        err.append(np.where(allowed,e,np.inf))
    errors=np.min(err,axis=0);directions=np.argmin(err,axis=0)
    worst=float(np.max(errors));counts={str(i):int(np.sum(directions==i)) for i in range(3)}
    assert min(counts.values())>8 and worst<.00012,(worst,counts)
    return dict(triangles=len(faces),orientations=counts,embedded_texture_sha256=sha,
                repeat_dimensions_m=[1.60,.64],max_uv_error=worst,repeat_s=True,repeat_t=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['raw','full','lod','output']:parser.add_argument(name,type=Path)
    opt=parser.parse_args();data={k:inspect(getattr(opt,k))for k in ('raw','full','lod')}
    opt.output.write_text(json.dumps(data,indent=2)+'\n')
