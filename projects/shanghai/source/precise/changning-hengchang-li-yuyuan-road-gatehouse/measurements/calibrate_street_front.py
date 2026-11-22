"""Recompute the image-plane matrices from the 10 February 2018 street photograph."""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

ROOT=Path(__file__).resolve().parents[1]
# Coordinates below use the 1100 x 619 upright study of the 5312 x 2988 original.
D=np.diag([1100/5312,619/2988,1])
SECTIONS=[
    ('x','first and last visible lower tile lip',(1492.62*D[0,0],879.82*D[1,1]),(4848.9*D[0,0],1280.25*D[1,1]),1.2),
    ('x','underside of the tile shoulder',(1520.4*D[0,0],902.07*D[1,1]),(3454.15*D[0,0],1141.21*D[1,1]),1.2),
    ('x','road curb',(530,609),(1068,547),2.8),
    ('x','street shop thresholds',(329,586),(995,528),4.3),
    ('x','lower edge of gate name-tablet band',(35,341),(300,344),1.05),
    ('x','stone portal soffit',(60,383),(249,381),1.0),
    ('z','west inner upright in doorway',(53,395),(45,595),1.15),
]


def matrices(q):
    vx,vy,roll,f=q[:4]
    a=(vx-550)/f
    b=(vy-309.5)/f
    x=np.array([a,b,1]);x/=np.linalg.norm(x)
    z=np.array([roll,-1,b-a*roll]);z/=np.linalg.norm(z)
    R=np.stack([x,np.cross(z,x),z],axis=1)
    K=np.array([[f,0,550],[0,f,309.5],[0,0,1.]])
    return K@np.column_stack([R,q[4:7]]),-R.T@q[4:7]


def pixel(P, xyz):
    pt=P@[*xyz,1]
    return pt[:2]/pt[2]


def residual(q):
    P,eye=matrices(q)
    out=[]
    for axis,_,a,b,weight in SECTIONS:
        v=P[:,0 if axis=='x' else 2]
        midpoint=(np.array(a)+b)*.5
        along=v[:2]/v[2]-midpoint
        delta=np.subtract(b,a)
        out.append((delta[0]*along[1]-delta[1]*along[0])/np.linalg.norm(along)/weight)
    for anchor,uv,sigma in [((0,0,q[7]),(14,341),2),((6.34,0,q[7]),(304,344),2),
                            ((6.34,0,0),(309,593),3.5)]:
        out.extend((pixel(P,anchor)-uv)/sigma)
    # Equivalent focal length from EXIF and a photographer-height prior.
    return np.r_[out,(q[3]-817)/10,(eye[2]-1.65)/.32]


def fit():
    q=least_squares(residual,[2120,379,.005,817,-11,5,15,5],max_nfev=1200,
                    loss='soft_l1',x_scale='jac',bounds=([1250,300,-.17,779,-40,-8,4,2],
                                                        [3900,495,.17,854,0,25,45,9])).x
    small,eye=matrices(q)
    P=np.linalg.inv(D)@small
    def plane(y):
        A=P[:,[0,2,3]].copy()
        A[:,2]+=P[:,1]*y
        H=np.linalg.inv(A)
        return H/H[2,2]
    def point(uv):
        h=plane(0)@np.linalg.solve(D,[*uv,1])
        return h[:2]/h[2]
    left,zleft=point((53.5,383))
    right,zright=point((261,381))
    return {'native_camera':P.tolist(),'native_to_xz':{key:plane(y).tolist() for key,y in [('tower',0),('east',.55)]},
            'portal':dict(left=round(left,3),right=round(right,3),head=round((zleft+zright)/2,3),
                          width=6.34,clear_width=round(round(right,3)-round(left,3),3),west_height=round(zleft,3),east_height=round(zright,3)),
            'control':{'study_pixels':[1100,619],'focal_length_study_px':q[3],'eye_metres':eye.tolist(),
                'line_controls':[{'edge':r[1],'from':r[2],'to':r[3],'signed_cross_line_error_study_px':e*r[4]}
                                 for r,e in zip(SECTIONS,residual(q))],
                'reconstruction':'门面净宽以屋盖南端约6.34米标定。带通摄影高度先验，路缘、门头、檐线并非完全平行。摄影位置与各高度均为估值。'}} 


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    result=fit()
    if args.check:
        current=json.loads((ROOT/'source/gatehouse-layout.json').read_bytes())
        for key in ('tower','east'):
            assert np.allclose(current['native_to_xz'][key],result['native_to_xz'][key],atol=2e-7)
        assert current['portal']==result['portal']
    print(json.dumps(result,ensure_ascii=False,indent=2))
