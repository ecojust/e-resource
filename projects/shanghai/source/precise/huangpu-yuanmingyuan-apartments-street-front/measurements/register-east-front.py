"""Register the 2014 oblique street image and the 2016 frontal reference to the measured east frontage."""
import json
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

HERE=Path(__file__).resolve().parent


def homography(a,b):
    def normalise(p):
        mid=p.mean(axis=0);scale=np.sqrt(2.)/np.mean(np.linalg.norm(p-mid,axis=1))
        t=np.array([[scale,0.,-scale*mid[0]],[0.,scale,-scale*mid[1]],[0.,0.,1.]])
        return (p-mid)*scale,t
    a,ta=normalise(a);b,tb=normalise(b)
    A=[]
    for (x,y),(u,v) in zip(a,b):
        A.extend([[-x,-y,-1.,0.,0.,0.,u*x,u*y,u],[0.,0.,0.,-x,-y,-1.,v*x,v*y,v]])
    h=np.linalg.svd(A,full_matrices=len(A)<9)[2][-1].reshape(3,3)
    h=np.linalg.inv(tb)@h@ta
    return h/h[-1,-1]


def project(h,p):
    q=np.c_[p,np.ones(len(p))]@h.T
    return q[:,:2]/q[:,2,None]


def camera(h,f,center):
    k=np.array([[f,0.,center[0]],[0.,f,center[1]],[0.,0.,1.]])
    p=np.linalg.solve(k,h);sx,sz=np.linalg.norm(p[:,:2],axis=0)
    inside=np.cross(p[:,1]/sz,p[:,0]/sx)
    inside/=np.linalg.norm(inside)
    return np.column_stack([h[:,0],k@inside*(sx+sz)/2.,h[:,1],h[:,2]])


def solve():
    src=json.loads((HERE/'east-photograph-controls.json').read_bytes());pairs=np.array(src['wing_tie_points_archive_then_street_px'])
    a,b=pairs[:,:2],pairs[:,2:];h=homography(a,b)
    def refine(v):return np.r_[v,1.].reshape(3,3)
    h=refine(least_squares(lambda v:(project(refine(v),a)-b).ravel(),h.ravel()[:8],loss='soft_l1',f_scale=2.,x_scale='jac').x)
    delta=np.linalg.norm(project(h,a)-b,axis=1)
    street=np.array(src['street_photo']['size']);cv=street/2
    vh,vz=[np.array(src['orientation'][direction]['vanishing_native_px']) for direction in ['horizontal','vertical']]
    f=np.sqrt(-(vh-cv)@(vz-cv));span=src['span']['estimated_principal_face_m'];z=src['edge_references']['storey_cornice_elevation_estimated_m']
    anchors=np.array([[-span/2,0.],[span/2,0.],[span/2,z],[-span/2,z]])
    primary=homography(anchors,np.array(src['edge_references']['archive_front_px']))
    # The observed planar mappings preserve the exact pavement and fascia lines
    # in both exposures. The estimated normal direction is used only for relief.
    oblique=camera(h@primary,f,cv)
    headon=camera(primary,1200*17/36.,[600.,400.])
    # The front photograph's effective principal point moved in the architectural
    # correction. Off-plane points constrain the height of its perspective centre.
    stereo=json.loads((HERE/'entrance-and-spandrel-stereo-controls.json').read_bytes())['controls']
    eye=-np.linalg.solve(headon[:,:3],headon[:,3])
    street_eye=-np.linalg.solve(oblique[:,:3],oblique[:,3])
    def off_plane(row):
        ray=np.linalg.solve(oblique[:,:3],np.r_[row['street_px'],1.])
        on_face=street_eye-ray*street_eye[1]/ray[1]
        tangent=ray/ray[1]
        a=headon[:,:3]@on_face+headon[:,3];b=headon[:,:3]@tangent
        u=row['archive_px'][0]
        y=(a[0]-u*a[2])/(u*b[2]-b[0])
        return on_face+y*tangent
    points=[off_plane(row) for row in stereo]
    def front_camera(z_eye):
        origin=np.array([eye[0],eye[1],float(z_eye)])
        adjusted=headon.copy()
        adjusted[:,1]=-(primary[:,0]*origin[0]+primary[:,1]*origin[2]+primary[:,2])/origin[1]
        return adjusted
    def v_error(cam,point,row):
        q=cam[:,:3]@point+cam[:,3];return q[1]/q[2]-row['archive_px'][1]
    zfit=least_squares(lambda z:[v_error(front_camera(z[0]),p,row) for p,row in zip(points,stereo)
                                  if row['role']=='fit'],[2.],loss='soft_l1',f_scale=.5).x[0]
    headon=front_camera(zfit)
    checks=[dict(feature=r['feature'],role=r['role'],depth_m=round(float(p[1]),4),
                 vertical_residual_native_px=round(float(v_error(headon,p,r)),3)) for p,r in zip(points,stereo)]
    def rec(matrix):return {'matrix':matrix.tolist(),'eye_m':(-np.linalg.solve(matrix[:,:3],matrix[:,3])).tolist()}
    return {'axes':'X positive north along the east wall, Y positive into the building, Z up. Y=0 on the flanking main masonry. X=0 on the main entrance axis.',
            '2014_oblique':rec(oblique),'2016_front':rec(headon),'2016_to_2014_plane_matrix':h.tolist(),
            'focal_2014_estimated_px':float(f),'street_plane_ties':len(a),'median_tie_error_street_px':float(np.median(delta)),
            'p90_tie_error_street_px':float(np.percentile(delta,90)),'off_plane_registration':checks,
            'nominal_frontage_m':span,'estimated_cornice_elevation_m':z,
            'limitations':'The cameras register the east frontage. The reference photographs have different cropping and lens corrections. Relief, the southern clipped corner and all absolute dimensions are estimated.'}

if __name__=='__main__':
    out=solve();(HERE/'east-front-cameras.json').write_text(json.dumps(out,indent=1)+'\n')
