"""Recover the two directions of the photographed garden corner at 159 Yanqing Road.

Pixel origin is top left of the 600 by 401 photograph. The subject corner is
the intersection of the left-hand entrance plane (Y=0) and return (X=0).
Local X increases toward the corner and local Y away along the right wall.
"""
from pathlib import Path
import argparse,json
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

# Segment axes are independent of whether the particular edge lies on the main plane.
AXES = [
    [[17,161,71,31],[78,161,98,143],[116,143,138,124],
     [176,161,264,102],[197,369,240,373],[190,225,227,211]],
    [[456,3,548,104],[461,83,496,115],[478,126,507,147],
     [388,248,451,254],[406,360,467,349],[521,134,534,144]],
    [[275,6,298,393],[193,369,193,237],[233,367,232,280],
     [382,46,391,121],[410,246,421,352],[518,149,532,211],
     [92,86,76,308],[134,90,124,307],[55,168,43,296]]
]
CENTER=np.array([299.5,200.])
def errors(v):
    rot=Rotation.from_rotvec(v[:3]).as_matrix()
    f=np.exp(v[3]);cx,cy=v[4:]
    k=np.array([[f,0,cx],[0,f,cy],[0,0,1.]])
    vp=k@rot
    residual=[]
    for i,spans in enumerate(AXES):
        for ax,ay,bx,by in spans:
            a,b=np.array([ax,ay]),np.array([bx,by])
            direction=vp[:2,i]-vp[2,i]*(a+b)/2
            direction/=np.linalg.norm(direction)
            residual.append((b[0]-a[0])*direction[1]-(b[1]-a[1])*direction[0])
    return np.r_[residual,(cx-CENTER[0])/.8,(cy-CENTER[1])/.8]
def solve():
    # Image axes: right/down/forward. X approaches camera; Y recedes; up points up.
    approx=np.array([[.70,.70,0.], [-.28,.28,-.92],[-.65,.65,.39]])
    r=Rotation.from_matrix(approx).as_rotvec();v=least_squares(errors,[*r,np.log(415),*CENTER],
                 loss='soft_l1',f_scale=1.5,max_nfev=2500)
    rot=Rotation.from_rotvec(v.x[:3]).as_matrix();f=np.exp(v.x[3]);cx,cy=v.x[4:];K=np.array([[f,0,cx],[0,f,cy],[0,0,1]])
    return K,rot,errors(v.x)
class GardenStation:
    def __init__(self):
        self.K,self.R,_=solve()
        self.I=np.linalg.inv(self.K)
        self.C=np.array([0.,-1.,0.])
        # Use left and right sides of the arched reveal below the spring.
        # A 0.96 m clear width is an assumed door reference with ±0.15 m uncertainty.
        door=[self.intersect('entrance',p)[0] for p in [(109,273),(128,267)]]
        self.C[1]*=.96/(door[1]-door[0])
        # Pale quoins meet at this edge in the 190 image. Base datum is the
        # photographed elevated landing, taken at 0.61 m above the garden.
        self.C[0]-=self.intersect('entrance',(306,200))[0]
        self.C[2]+=.61-self.intersect('entrance',(116,352))[2]

    def intersect(self,plane,p):
        ray=self.R.T@self.I@[*p,1.]
        axis=1 if plane=='entrance' else 0
        return self.C-ray*self.C[axis]/ray[axis]

    def point(self,plane,p):
        a=self.intersect(plane,p)
        return a[[0 if plane=='entrance' else 1,2]]

    def pixel(self,xyz):
        q=self.K@self.R@(np.asarray(xyz)-self.C)
        return q[:2]/q[2]


def report():
    station=GardenStation()
    k,r,e=solve()
    return {'raster':[600,401], 'station':'Sina 190 garden, reference-only',
            'axes':{'X':'toward the street corner along the entrance wall',
                    'Y':'toward the last shuttered bay along the street elevation','Z':'up'},
            'direction_segments_xyxy':AXES,'residuals_px':e[:-2].tolist(),
            'pinhole':k.tolist(),'world_to_camera_rotation':r.tolist(),
            'camera_centre_in_authored_frame':station.C.tolist(),
            'intrinsic_assumptions':'Square pixels, zero skew, no explicit radial distortion; principal point softly constrained to raster centre.',
            'initial_scale':'Door width 0.96 m provisional; doorstep elevation 0.61 m estimated. Garden photo alone does not determine physical scale.'}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    args.output.write_text(json.dumps(report(),indent=2)+'\n')
