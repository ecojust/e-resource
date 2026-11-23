"""Set the archive picture's metric scale from the measured stair lights and fit independent cameras."""
from pathlib import Path
import json,numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
HERE=Path(__file__).absolute().parent
read=lambda name:json.loads((HERE/name).read_bytes())
def planar_transform(image,points):
    a=[];b=[]
    for (u,v),(x,z) in zip(image,points):
        a.extend([[u,v,1,0,0,0,-u*x,-v*x],[0,0,0,u,v,1,-u*z,-v*z]]);b.extend([x,z])
    return np.r_[np.linalg.lstsq(a,b,rcond=None)[0],1].reshape(3,3)
def archive_pose(uv,xyz,w,h):
    # The scene is planar. An interior focal prior regularizes the nearly frontal newspaper image.
    pts=np.array(xyz,float);uv=np.array(uv,float);H=planar_transform(pts[:,[0,2]],uv)
    K=np.array([[w*.95,0,w/2],[0,w*.95,h/2],[0,0,1]]);v=np.linalg.solve(K,H)
    scale=2/(np.linalg.norm(v[:,0])+np.linalg.norm(v[:,1]));vx=v[:,0]*scale;vz=v[:,1]*scale;t=v[:,2]*scale
    U,_,V=np.linalg.svd(np.column_stack([vx,np.cross(vz,vx),vz]));R=U@V
    def project(x):
        k=K.copy();k[0,0]=k[1,1]=np.exp(x[6]);r=Rotation.from_rotvec(x[:3]).as_matrix();p=(k@(r@pts.T+x[3:6,None])).T;return p[:,:2]/p[:,2:],r,k
    x0=np.r_[Rotation.from_matrix(R).as_rotvec(),t,np.log(w*.95)]
    r=least_squares(lambda x:np.r_[(project(x)[0]-uv).ravel(),(x[6]-x0[6])*5],x0,max_nfev=2000)
    fit,rotation,k=project(r.x)
    return dict(K=k.tolist(),R=rotation.tolist(),C=(-rotation.T@r.x[3:6]).tolist(),width=w,height=h,crop=[0,0,w,h],residuals_px=np.linalg.norm(fit-uv,axis=1).round(3).tolist())
def main():
    a=read('plate-readings.json');street=read('three-street-readings.json');survey=read('stair-survey-result.json');H=planar_transform(a['facade_control_pixels'],a['facade_control_local_xz'])
    source=np.array([[r['edge_u'][0],r['top_v'][0],r['edge_u'][3],r['top_v'][2]] for r in a['ascending_sashes_bottom_to_top'][:3]]).reshape(-1,2);temp=(H@np.c_[source,np.ones(len(source))].T).T
    plane=temp[:,:2]/temp[:,2,None];real=np.array([r['xyz_from_poi']for r in survey['corners']]);v=(real[1::2,:2]-real[::2,:2]).mean(0);axis=v/np.linalg.norm(v);normal=np.array([-axis[1],axis[0]])
    sx=np.linalg.norm(v)/np.mean(plane[1::2,0]-plane[::2,0]);sz,offset=np.polyfit(plane[:,1],real[:,2],1)
    origin=(real[:,:2]-plane[:,:1]*sx*axis).mean(0);basis=np.array([[*axis,0],[*normal,0],[0,0,1]]).T
    p=np.array(a['facade_control_local_xz'])*[sx,sz]+[0,offset];xyz=np.c_[p[:,0],np.zeros(len(p)),p[:,1]]
    district=archive_pose(a['facade_control_pixels'],xyz,1035,735)
    press_uv=[[242,11],[375,14],[374,411],[232,413]]
    press=archive_pose(press_uv,xyz,750,526)
    result=dict(plate_x_scale=sx,plate_z_scale=sz,plate_z_offset=offset,corner_origin_enu=origin.tolist(),basis_model_to_enu=basis.tolist(),positive_x_bearing_deg=survey['positive_x_bearing_deg'],new_control_xz=p.tolist(),press_parapet_and_plinth=press_uv,notes='2019 hospital-history article contains an independent frontal photograph. Its tree obscures part of the low openings. All three 2020 street views show the same staircase above a later commercial canopy. The GLB depicts the archival lower facade.')
    (HERE/'street-metric-facade.json').write_text(json.dumps(result,indent=2)+'\n')
    cams={'district-archive':district,'press-archive':press}
    for tag,cam in street['stations'].items():
        c=np.r_[origin,0];R=np.array(cam['R'])@basis
        cams['road-'+tag]=dict(K=cam['K'],R=R.tolist(),C=(basis.T@(np.array(cam['C'])-c)).tolist(),width=cam['width'],height=cam['height'],crop=[150,0,600,380],date=cam['date'])
    cams['district-archive']['crop']=[380,4,690,723]
    cams['press-archive']['crop']=[178,0,410,515]
    cams['road-centre']['crop']=[245,0,408,384]
    (HERE/'registered-stair-stations.json').write_text(json.dumps(dict(stations=cams),indent=2)+'\n');print(sx,sz,offset,district['residuals_px'],press['residuals_px'])
if __name__=='__main__':main()
