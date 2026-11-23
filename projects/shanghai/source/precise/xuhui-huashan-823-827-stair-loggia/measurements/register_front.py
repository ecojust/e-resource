"""Rectify the 2018 street photograph of the three-gabled front residence at Huashan Road.

Coordinates are metres in an initial unscaled frame. The central loggia plane
is Y=0, +X follows the frontage to image right and +Y enters the house.
"""
from pathlib import Path
import argparse,json
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
# Individually visible parallel edges, then corresponding levels on both outer gables.
HORIZONTAL=[(169,284,262,287),(955,298,1018,299),(385,240,478,242),
            (589,275,685,278),(598,307,677,308),(759,365,803,366),
            (205,285,987,299),(219,327,991,332),(215,373,983,356)]
VERTICAL=[(170,215,167,281),(262,217,263,282),(381,188,384,236),
          (482,145,490,398),(575,145,588,365),(840,199,866,436),
          (951,235,956,294),(1009,239,1016,295),(859,217,865,257),
          (87,215,82,376)]
SIZE=(1300,731)
def fitted():
    cx,cy=(SIZE[0]-1)/2,(SIZE[1]-1)/2
    reference=28*np.hypot(*SIZE)/np.hypot(36,24)
    def axes(v):
        r=Rotation.from_rotvec(v[:3]).as_matrix();f=np.exp(v[3])
        k=np.array([[f,0,cx],[0,f,cy],[0,0,1.]])
        return k,r
    def errors(v):
        k,r=axes(v);vp=k@r;d=[]
        for axis,lines in ((0,HORIZONTAL),(2,VERTICAL)):
            for x,y,a,b in lines:
                direction=vp[:2,axis]-vp[2,axis]*np.array([(x+a)/2,(y+b)/2])
                direction/=np.linalg.norm(direction)
                d.append((a-x)*direction[1]-(b-y)*direction[0])
        return np.r_[d,(np.exp(v[3])-reference)/9]
    initial=Rotation.from_matrix(np.array([[.97,-.22,0.],[.03,.15,-.99],[.22,.97,.15]])).as_rotvec()
    result=least_squares(errors,[*initial,np.log(reference)],loss='soft_l1',f_scale=1.7)
    k,r=axes(result.x)
    return k,r,errors(result.x)
class Camera:
    def __init__(self):
        self.K,self.R,self.residual=fitted()
        self.I=np.linalg.inv(self.K)
        self.C=np.array([0.,-1.,1.66])
        endpoints=[self.wall(p)[0] for p in [(585,224),(770,220)]]
        self.C[1]*=4.70/(endpoints[1]-endpoints[0])
        self.C[0]-=sum(self.wall(p)[0]for p in [(585,224),(770,220)])/2

    def wall(self,p,d=0):
        ray=self.R.T@self.I@[*p,1.]
        return self.C+ray*(d-self.C[1])/ray[1]

    def pixel(self,point):
        q=self.K@self.R@(np.array(point)-self.C)
        return q[:2]/q[2]

def report(c):
    return dict(source='Antigng, 2018-02-10; 5312 × 2988 master raster',working_size=SIZE,
                focal_35mm_equivalent=28,horizontal_edges=HORIZONTAL,vertical_edges=VERTICAL,
                intrinsic=c.K.tolist(),world_to_camera=c.R.tolist(),camera_centre=c.C.tolist(),
                horizontal_then_vertical_direction_residuals_px=c.residual[:-1].tolist(),
                scale='Provisional 4.70 m central arch width and 1.66 m camera height, prior to the street-survey scale.')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('output',type=Path)
    args=parser.parse_args();args.output.write_text(json.dumps(report(Camera()),indent=2)+'\n')
