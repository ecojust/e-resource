"""Register Antigng's licensed street photo to the cast gate and test first visible surfaces."""
from pathlib import Path
import json,sys,argparse
import numpy as np
from scipy.spatial.transform import Rotation
HERE=Path(__file__).resolve().parent
PROJECT=next((p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file()),None)
if PROJECT is None:
    import os
    PROJECT=Path(os.environ['E_RESOURCE_SHANGHAI'])
SRC=PROJECT/'source/precise/xuhui-wuyuan-289-garden-houses/source'
sys.path[:0]=[str(SRC),str(PROJECT/'source/precise/xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact')]
from placement import Facade
from lane_gate import FIELD,CAST,EDGE
from glb_triangles import SerialScene
W,H=2.80,2.16
corners=np.array([(30,75),(489,72),(493,425),(39,432)])
def project(P,world):
 p=np.c_[world,np.ones(len(world))]@P.T
 return p[:,:2]/p[:,2,None]
def homography(xy,pixel):
 rows=[];target=[]
 for (x,z),(u,v) in zip(xy,pixel):
  rows.extend([[x,z,1,0,0,0,-u*x,-u*z],[0,0,0,x,z,1,-v*x,-v*z]]);target.extend([u,v])
 return np.r_[np.linalg.solve(rows,target),1.].reshape(3,3)
Hgate=homography([(0,H),(W,H),(W,.04),(0,.04)],corners)
def gate_picture():
 # A 28mm-equivalent phone camera is a starting approximation. The
 # homography retains the actual four photographed corners for the front-plane tests.
 K=np.array([[2180,0,316],[0,2180,263],[0,0,1]])
 ch=np.linalg.solve(K,Hgate)
 ch*=2/(np.linalg.norm(ch[:,0])+np.linalg.norm(ch[:,1]))
 rot=np.column_stack([ch[:,0],np.cross(ch[:,1],ch[:,0]),ch[:,1]])
 a,_,b=np.linalg.svd(rot);R=a@np.diag([1,1,np.linalg.det(a@b)])@b
 return K@np.column_stack((R,ch[:,2]))
def inspect(mesh):
 r=SerialScene(mesh)
 gate=Facade(None,'1-2').face(11.77,-3.19,0,1)
 obs=[('left wicket upright',105,244,(EDGE,CAST,FIELD)),('left pull rose',233,246,(EDGE,CAST,FIELD)),('right pull rose',273,236,(EDGE,CAST,FIELD)),('right outer edge',480,187,(EDGE,CAST,FIELD))]
 for row,y in [('upper',161),('lower',333)]:
  for n,x in enumerate([70,140,190,306,351,395,438],start=1):obs.append((row+' relief field '+str(n),x,y,(CAST,FIELD)))
 for name,x,y in [('central slit',252,124),('central slit at foot',257,391)]:
  obs.append((name,x,y,()))
 tests=[]
 for name,x,y,expected in obs:
  p=np.linalg.solve(Hgate,[x,y,1]);u,z=(p/p[2])[:2]
  start=np.array(gate.point(u,-.60,z));target=np.array(gate.point(u,.12,z))
  hit=r.ray(start,target-start,.80)
  matched=bool(hit and hit['material'] in expected)if expected else not hit
  tests.append({'feature':name,'study_pixel':[x,y],'rectified_uz_m':[float(u),float(z)],'expected':expected,'hit':hit,'matched':matched})
 return {'mesh':r.asset,'source':'Antigng, 2017-08-19, CC BY-SA 4.0','source_page':'https://commons.wikimedia.org/wiki/File:五原路289弄住宅.jpg','comparison_crop_upright_px':[914,2175,1880,3060],'comparison_size':[526,482],'upright_image_size':[2988,5312],'observed_gate_corners':corners.tolist(),'gate_uz_to_crop':Hgate.tolist(),'approximate_width_height_ratio':1.30,'tests':tests,'tested':len(tests),'matched':sum(t['matched']for t in tests)}
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mesh',type=Path);parser.add_argument('out',type=Path);a=parser.parse_args();d=inspect(a.mesh);a.out.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');print(d['matched'],d['tested'],[t['feature']for t in d['tests']if not t['matched']])
