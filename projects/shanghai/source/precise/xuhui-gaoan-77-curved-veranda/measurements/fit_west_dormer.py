"""Register the western flat-capped dormer to the independent west photograph."""
import numpy as np,json,sys
from pathlib import Path
import argparse
S=Path(__file__).resolve().parents[1];sys.path.insert(0,str(S/'source'))
from west_wing import WEST_CAL,ORIGIN,SEAT,SOFFIT
from curved_veranda import veranda_interface
from house_layout import LAYOUT
A=json.loads((S/'measurements/west-eave-photo-control.json').read_text())
cam=A['cameras']['sina26'];h=np.asarray(cam['plane_to_pixel']);w,hpx=cam['native_size'];K=np.array([[720,0,w/2],[0,720,hpx/2],[0,0,1]]);ki=np.linalg.inv(K);u=ki@h[:,0];z=ki@h[:,1];n=np.cross(u,z);n*=np.sqrt(np.linalg.norm(u)*np.linalg.norm(z))/np.linalg.norm(n);P=np.column_stack([h[:,0],K@n,h[:,1],h[:,2]])
if (-np.linalg.solve(P[:,:3],P[:,3]))[1]<0:P[:,1]*=-1
T=np.array([[0,-1/WEST_CAL,0,ORIGIN],[-1/WEST_CAL,0,0,0],[0,0,1/WEST_CAL,-SEAT],[0,0,0,1]])
P=P@T;eye=-np.linalg.solve(P[:,:3],P[:,3])
def hit(x,p):
 ray=np.linalg.solve(P[:,:3],[*p,1]);return eye+ray*(x-eye[0])/ray[0]
sec=veranda_interface(LAYOUT)['rear_roof_section'];heights=[(x,z) for x,d,z in sec];
def ht(x):return np.interp(x,[x for x,z in heights],[z for x,z in heights]);
def fit():
    # The glass sill in this oblique view is hidden by the front eave. The lower two points give its visible limits.
    features={'glass top':[(320.,110.),(354.6,102.4)],'visible glass base':[(320.2,126.2),(354.6,119.2)],'outer coping':[(307.4,99.2),(360.,86.8)]}
    x=.17
    return {'reference':'Sina photograph 26, 2012-11-05; coordinates on the 690 by 528 rendition. See west-eave-photo-control.json for the photo hash and original reference.',
            'front_plane_x_m':x, 'observations':{k:[{'xy':p,'model_xyz_m':hit(x,p).round(4).tolist()} for p in points] for k,points in features.items()},
            'datum':'Horizontal face setback estimated by intersection of the photographed glass base with the western roof pitch. The plane estimates and absolute height use the street-scaled frame.',
            'limits':'Single oblique view; top corners and four narrow lights visible. The sill, rear dormer edge and depth of its cheeks are estimated.'}
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('output',type=Path);args=ap.parse_args()
    args.output.write_text(json.dumps(fit(),indent=2)+'\n')
