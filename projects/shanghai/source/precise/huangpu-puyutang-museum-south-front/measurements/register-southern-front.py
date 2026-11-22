"""Fit the south court photo with EXIF intrinsics and register the close view to the portal."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

# Image 4, Nikon D610, landscape 28mm equivalent. Left boundary is partly screened.
# On the facade the rightmost wall is 23.8155m from the central axis. The left boundary
# is assigned lower weight. Vertical heights and the camera pose are fitted jointly.
WIDE_F=28*1200/36
CLOSE_F=45*1200/36
WIDTH=47.631
edge_samples={
    'eave':[(48.,236.),(167.,239.),(553.,246.),(897.,258.),(1152.,269.)],
    'belt':[(50.,358.),(167.,357.),(550.,356.),(898.,355.),(1147.,353.)],
    'lower_window_sill':[(111.,463.),(246.,457.),(604.,443.),(902.,429.)],
}
# The frames, keystone cornice, pinnacles and door recess are homologous material
# corners. Assign their photographed depth separately; they do not lie on one plane.
pairs=[
 ('upper wood TL',[700.7,278.2],[345.,393.],-.03),('upper wood TR',[728.8,279.4],[440.,405.],-.03),
 ('upper wood BR',[729.8,327.8],[444.,572.],-.03),('upper wood BL',[702.0,327.4],[351.,565.],-.03),
 ('upper sill TL',[698.7,328.4],[338.,566.],-.29),('upper sill TR',[732.6,328.8],[457.,575.],-.29),
 ('large gable peak',[709.5,182.5],[384.,83.],-.28),('west pinnacle peak',[654.5,213.7],[186.,139.],-.31),
 ('east pinnacle peak',[768.0,218.4],[575.,220.],-.31),('west gable cornice',[676.8,228.0],[271.,201.],-.33),
 ('east gable cornice',[746.7,230.3],[502.,247.],-.33),
 ('door TL',[681.8,388.8],[267.,780.],-.025),('door TR',[751.5,388.3],[510.,779.],-.025),
 ('door BR',[751.8,462.7],[522.,1062.],-.025),('door BL',[683.1,465.4],[272.,1083.],-.025),
 ('lintel left',[677.7,382.1],[257.,761.],-.34),('lintel right',[757.1,381.6],[533.,760.],-.34),
]
def camera(eye,angles,f,center):
    yaw,pitch,roll=angles
    forward=np.array([np.sin(yaw)*np.cos(pitch),np.cos(yaw)*np.cos(pitch),np.sin(pitch)])
    right=np.cross(forward,[0.,0.,1.]);right/=np.linalg.norm(right)
    up=np.cross(right,forward);frame=np.stack([right*np.cos(roll)+up*np.sin(roll),right*np.sin(roll)-up*np.cos(roll),forward])
    K=np.array([[f,0,center[0]],[0,f,center[1]],[0,0,1.]])
    return K@np.column_stack((frame,-frame@np.asarray(eye)))
def project(P,xyz):
    q=P@np.r_[xyz,1.];return q[:2]/q[2]
def invert(P,uv,y):
    H=P[:,[0,2,3]].copy();H[:,2]+=P[:,1]*y
    q=np.linalg.solve(H,[*uv,1.]);return np.array([q[0]/q[2],y,q[1]/q[2]])
def main(out):
    def matrix(v):return camera(v[:3],v[3:6],WIDE_F,[600.,400.])
    def error(v):
        P=matrix(v);r=[]
        for xyz,point,sigma in [([0.,-.025,0.],[717.4,464.0],1.2),([WIDTH/2,0,0.],[1153.,424.],4.),([-WIDTH/2,0,0.],[40.,499.],7.)]:
            r.extend((project(P,xyz)-point)/sigma)
        for index,(_,points) in enumerate(edge_samples.items()):
            a,b=(np.r_[project(P,[x,0,v[6+index]]),1.]for x in (-20.,20.))
            line=np.cross(a,b);line/=np.linalg.norm(line[:2])
            r.extend(np.dot(line,[*p,1.])/1.6 for p in points)
        # The entrance threshold is raised over the court. A standing photographer
        # observed it from across the lawn; the small prior regularises the partly hidden floor.
        r.append((v[2]-2.0)/1.0)
        return r
    sol=least_squares(error,[-13.,-34.,2.,.23,.09,0.,7.9,3.7,.8],loss='soft_l1',f_scale=1.5,max_nfev=8000)
    p=matrix(sol.x)
    xyz=np.array([invert(p,wide,y) for _,wide,_,y in pairs]);uv=np.array([close for _,_,close,_ in pairs])
    def close_camera(v):return camera(v[:3],v[3:6],CLOSE_F,[400.,600.])
    def close_error(v):return np.ravel([project(close_camera(v),x)-u for x,u in zip(xyz,uv)])
    opt=least_squares(close_error,[-3.,-16.,2.,.14,.16,0.],loss='soft_l1',f_scale=4,max_nfev=8000)
    cp=close_camera(opt.x)
    controls=[dict(feature=n,wide_px=w,close_px=c,assumed_y_m=y,close_error_px=np.linalg.norm(project(cp,x)-c)) for (n,w,c,y),x in zip(pairs,xyz)]
    result=dict(dates='2014-08-16',width_basis_m=WIDTH,section_heights_m=dict(zip(edge_samples,sol.x[6:])),wide=dict(size=[1200,800],equivalent_focal_mm=28,camera_3x4=p.tolist(),eye_m=sol.x[:3].tolist(),line_pixels=edge_samples),
                close=dict(size=[800,1200],equivalent_focal_mm=45,camera_3x4=cp.tolist(),controls=controls,median_residual_close_px=float(np.median([i['close_error_px']for i in controls]))),
                scope='The registered outline supplies the nominal width. Porch offsets and partly obscured facade ends are estimates. Both cameras constrain the visible front, without establishing survey-grade dimensions.')
    out.write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('output',type=Path)
    main(parser.parse_args().output)
