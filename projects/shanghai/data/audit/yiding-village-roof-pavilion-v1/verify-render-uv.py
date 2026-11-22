"""Check physical stucco UV scale, wrap mode and the texture embedded in three decoded exports."""
import argparse,hashlib,json,runpy
from pathlib import Path
import numpy as np

AUDIT=Path(__file__).absolute().parent.parent
SRC=AUDIT.parents[1]/'source/precise/changning-yiding-village-roof-pavilion/source'
triangles=runpy.run_path(AUDIT/'postal-office-v1/independent-glb-review-helpers.py')['load_triangles']
textures=runpy.run_path(AUDIT/'fifth-textile-warehouse-river-front-v1/inspect-export.py')['load_textures']


def inspect(path):
    tri,index,names,_=triangles(path);loaded,embedded,coords,_=textures(path,index)
    m=names.index('Yiding pale roughcast');im=SRC/'yiding-cream-render.png'
    digest=hashlib.sha256(im.read_bytes()).hexdigest();assert set(embedded)=={m}
    info=embedded[m];assert info['embedded_sha256']==digest and info['texture_dimensions']==[160,160]
    sampler=loaded[m][1];assert all(sampler.get(k,10497)==10497 for k in ('wrapS','wrapT'))
    face=tri[index==m];uv=coords[index==m]
    ab=face[:,1]-face[:,0];ac=face[:,2]-face[:,0]
    normals=np.cross(ab,ac);horizon=np.linalg.norm(normals[:,:2],axis=1);vertical=horizon>abs(normals[:,2])
    x,y,z=face.transpose(2,0,1);u=x.copy();v=y.copy()
    # For a vertical reveal, either horizontal tangent sign is valid. Direct
    # per-edge differences test bond scale without magnifying FLOAT32 yaw noise.
    planar=np.stack([x,y],axis=-1);delta=planar[:,1:]-planar[:,:1]
    tangent=np.column_stack([-normals[:,1],normals[:,0]])/np.maximum(horizon[:,None],1e-16)
    along=np.einsum('nki,ni->nk',delta,tangent)
    actual=(uv[:,1:,0]-uv[:,:1,0])*.72
    ve=np.minimum(np.max(abs(along-actual),axis=1),np.max(abs(along+actual),axis=1))
    eu=np.where(vertical,ve,np.max(abs((x[:,1:]-x[:,:1])-actual),axis=1))
    elevations=np.where(vertical[:,None],z,y)
    ev=np.max(abs(elevations[:,1:]-elevations[:,:1]+(uv[:,1:,1]-uv[:,:1,1])*.72),axis=1)
    error=float(max(eu.max(),ev.max()));assert error<.00024,(error,eu.max(),ev.max())
    angles=np.degrees(np.arctan2(normals[:,1],normals[:,0]))%180
    bearings=set(int(a//5) for a in angles[vertical]);assert len(bearings)>=2 and (~vertical).sum()>=8
    return dict(triangles=len(face),vertical_triangles=int(vertical.sum()),horizontal_triangles=int((~vertical).sum()),
                vertical_orientation_bins_5_degrees=sorted(bearings),embedded_texture_sha256=digest,
                repeat_dimensions_m=[.72,.72],max_metric_error_m=error,repeat_s=True,repeat_t=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('raw','full','lod','output'):parser.add_argument(key,type=Path)
    opt=parser.parse_args();report={k:inspect(getattr(opt,k))for k in ('raw','full','lod')}
    opt.output.write_text(json.dumps(report,indent=2)+'\n')
