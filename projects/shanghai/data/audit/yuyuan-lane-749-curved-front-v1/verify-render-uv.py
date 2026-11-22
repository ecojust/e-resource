"""Check true arc length on the rotated aggregate faces and depth on radial reveals."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import numpy as np

AUDIT=Path(__file__).absolute().parent.parent
SOURCE=AUDIT.parents[1]/'source/precise/changning-yuyuan-lane-749-curved-front/source'
get_triangles=runpy.run_path(AUDIT/'postal-office-v1/independent-glb-review-helpers.py')['load_triangles']
get_textures=runpy.run_path(AUDIT/'fifth-textile-warehouse-river-front-v1/inspect-export.py')['load_textures']

def inspect(path):
    triangles,index,names,_=get_triangles(path);loaded,embedded,coords,_=get_textures(path,index)
    material=names.index('Yuyuan grey washed aggregate');info=embedded[material]
    digest=hashlib.sha256((SOURCE/'yuyuan-washed-aggregate.png').read_bytes()).hexdigest()
    assert set(embedded)=={material} and info['embedded_sha256']==digest and info['texture_dimensions']==[160,160]
    sampler=loaded[material][1];assert all(sampler.get(k,10497)==10497 for k in ('wrapS','wrapT'))
    face=triangles[index==material];uv=coords[index==material];r=json.loads((SOURCE/'dimensions.json').read_bytes())['radius_m']
    edges=face[:,1:]-face[:,:1]
    normal=np.cross(edges[:,0],edges[:,1])
    vertical=np.linalg.norm(normal[:,:2],axis=1)>np.abs(normal[:,2])
    x,y,z=face.transpose(2,0,1);radii=np.hypot(x,r-y);angle=np.arctan2(x,r-y)
    on_curve=vertical&(np.ptp(radii,axis=1)<.00005)
    on_jamb=vertical&(~on_curve)
    measured_u=(uv[:,:,0]-uv[:,:1,0])*.72
    measured_v=(uv[:,:1,1]-uv[:,:,1])*.72
    predicted_u=x-x[:,:1]
    predicted_u[on_curve]=(radii[on_curve]*angle[on_curve])-(radii[on_curve]*angle[on_curve])[:,:1]
    predicted_u[on_jamb]=radii[on_jamb]-radii[on_jamb,:1]
    height=np.where(vertical[:,None],z,y)
    error=max(np.abs(measured_u-predicted_u).max(),np.abs(measured_v-height+height[:,:1]).max())
    assert error<.000025,error
    assert on_curve.sum()>360 and on_jamb.sum()>=24 and (~vertical).sum()>70
    return dict(triangles=len(face),curved_face_triangles=int(on_curve.sum()),radial_edge_triangles=int(on_jamb.sum()),
                horizontal_triangles=int((~vertical).sum()),repeat_dimensions_m=[.72,.72],max_metric_error_m=float(error),
                embedded_texture_sha256=digest,repeat_s=True,repeat_t=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for k in ['raw','full','lod','output']:parser.add_argument(k,type=Path)
    p=parser.parse_args();r={k:inspect(getattr(p,k))for k in ['raw','full','lod']}
    p.output.write_text(json.dumps(r,indent=2)+'\n')
