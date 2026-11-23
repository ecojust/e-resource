"""Estimate visible roof pitch from 39 red-clay silhouette columns in the reduced 2019 photograph.

Run with the unmodified Wikimedia file. All coordinates are local display coordinates.
The inferred pitch is conditional on the assumed upper-wall distance and roof section.
"""
import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'source'))
from rear_elevation import footprint,SURVEY,SECTION
from photo_plane import P
from PIL import Image
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('original',type=Path);parser.add_argument('output',type=Path);args=parser.parse_args()
assert hashlib.sha256(args.original.read_bytes()).hexdigest()=='70ef2cc3dc44d891242d01dff8d18687b7d039e78162998e39ca8ed64f30ae21'
rgb=np.asarray(Image.open(args.original).resize((800,600))).astype(int);results={}
def project(coords):
 z=np.c_[coords,np.ones(len(coords))]@P.T;return z[:,:2]/z[:,2:3]
for wing,rx,ry in [('low',range(262,382,5),[123,141]),('high',range(584,642,4),[95,108])]:
 row=next(r for r in SURVEY['wings']if r['key']==wing);a,b,h,_=footprint(row);d=row['d']; x0=a-.28;x1=b+.28;y0=d-.40;y1=d+SECTION
 xr=[];upper=[];lower=[]
 for x in rx:
  pix=rgb[ry[0]:ry[1],x];reds=(pix[:,0]-pix[:,1]>12)&(pix[:,0]-pix[:,2]>15)&(pix[:,0]>58)
  y=np.flatnonzero(reds)+ry[0]
  if not y.size or y[-1]-y[0]+1>len(y)+3:continue
  upper.append(float(y[0]));lower.append(float(y[-1]));xr.append(x)
 def pred(par):
  add,slope,hip=par;z0=h+.138+add;ridge=z0+(y1-y0)*slope;inset=(y1-y0)*hip;u=np.linspace(x0,x1,301)
  hi=np.minimum(np.minimum((u-x0)/hip,(x1-u)/hip),y1-y0);px=project(np.array([u,y0+hi,z0+.033+hi*slope]).T)
  bottom=project(np.array([[x0,y0,z0-.020],[x1,y0,z0-.020]]))
  return np.interp(xr,px[:,0],px[:,1]),np.interp(xr,bottom[:,0],bottom[:,1])
 def cost(par):
  p,q=pred(par);return np.r_[p-upper,q-lower]
 res=least_squares(cost,[.13,.63,1.1],bounds=([-.2,.53,.45],[.6,1.05,1.8]),loss='soft_l1')
 residuals=cost(res.x)
 results[wing]={'columns':xr,'top':upper,'bottom':lower,'edge_raise_m':float(res.x[0]),'front_slope':float(res.x[1]),'hip_inset_per_m_of_depth':float(res.x[2]),'angle_degrees':float(np.rad2deg(np.arctan(res.x[1]))),'mean_absolute_residual_px':float(np.mean(abs(residuals))),'max_abs_residual_px':float(max(abs(residuals)))}
args.output.write_text(json.dumps(results,indent=2)+'\n')
