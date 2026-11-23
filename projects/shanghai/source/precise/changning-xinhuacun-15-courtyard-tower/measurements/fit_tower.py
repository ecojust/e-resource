"""Fit the numbered courtyard photograph and the 2015 street photograph independently to one hipped tower."""
from pathlib import Path
from math import tan,radians
import json
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
HERE=Path(__file__).absolute().parent
ROWS=json.loads((HERE/'tower-pixels.json').read_bytes())
NAMES=['width','depth','wall_top','roof_top','overhang','ridge_half','front_window_x','north_window_x','south_width','north_width','south_top','south_sill','north_top','north_sill','south_z0']
START=np.array([5.55,4.75,12.65,14.80,.52,.75,-.13,-.08,1.58,1.52,12.03,10.73,12.15,10.99,-.40])
SIGMA=np.array([.64,1.5,.38,.74,.17,.72,.46,.48,.44,.11,.66,.66,.42,.40,.90])
KEYS=('numbered-court','street-2015')
def geometry(p):
 w,d,h,z,o,l,fx,rx,fw,rw,ft,fs,rt,rs,base=p
 a,b=-w/2,w/2
 out={}
 for name,k,y,s in [('f',fx,0,1),('r',rx,d,-1)]:
  ww,top,bot=(fw,ft,fs)if name=='f'else(rw,rt,rs)
  for tag,i,j in [('tl',-1,top),('tr',1,top),('br',1,bot),('bl',-1,bot)]:out[name+tag]=(k+s*i*ww/2,y,j)
 for k,x,y in [('fl',a,0),('fr',b,0),('rl',b,d),('rr',a,d)]:
  out[k+'-wall']=(x,y,h);out[k+'-foot']=(x,y,base)
  out[k+'-lip']=(x+np.sign(x)*o,y+(-o if y==0 else o),h+.14)
 out.update(peak_l=(-l,d/2,z),peak_r=(l,d/2,z));return out
def solve():
 def vecpose(c,t):
  z=t-c;z/=np.linalg.norm(z);x=np.cross(z,[0.,0.,1.]);x/=np.linalg.norm(x);return Rotation.from_matrix([x,np.cross(z,x),z]).as_rotvec()
 q=list(START);eyes=[[11.,-36.,2.3],[-16.,51.,2.32]];focals=[300.,800/(2*tan(radians(11)))];dims=[(281,270),(800,720)]
 for c,f in zip(eyes,focals):q.extend(c);q.extend(vecpose(np.array(c),np.array([0.,2.,7.6])));q.append(np.log(f))
 def calc(v,detail=False):
  p=v[:len(START)];pts=geometry(p);res=[];output={}
  for i,k in enumerate(KEYS):
   bar=len(START)+7*i;c=v[bar:bar+3];R=Rotation.from_rotvec(v[bar+3:bar+6]).as_matrix();f=np.exp(v[bar+6]);w,h=dims[i];K=np.array([[f,0,(w-1)/2],[0,f,(h-1)/2],[0,0,1.]])
   P=K@R@np.column_stack([np.eye(3),-c]);errors={}
   for name,(u,vv,err)in ROWS[k].items():
    x=P@[*pts[name],1.];delta=x[:2]/x[2]-[u,vv];res.extend(delta/err);errors[name]=delta.tolist()
   res.extend([(c[2]-eyes[i][2])/(1.2 if i==0 else .50),(np.log(f)-np.log(focals[i]))/(.45 if i==0 else .003)])
   output[k]=dict(size=dims[i],c=c.tolist(),K=K.tolist(),R=R.tolist(),P=P.tolist(),pixel_residuals=errors,median_px=float(np.median(np.linalg.norm(list(errors.values()),axis=1))))
  res.extend((p-START)/SIGMA)
  if detail:return dict(geometry=dict(zip(NAMES,p)),cameras=output,conditional_scale='Two December station rays and three April station rays independently give 1.49 and 1.57 m for the northern upper window; the common plan, courtyard paving elevation and hidden depth remain estimates.',right_handed_coordinates='X along the courtyard front toward its gallery, Y into the tower, Z above a local courtyard datum.')
  return res
 v=least_squares(calc,q,max_nfev=1300,loss='soft_l1',x_scale='jac').x
 return calc(v,True)
if __name__=='__main__':
 result=solve();(HERE/'registered-tower.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(result['geometry']);print([(k,c['median_px']) for k,c in result['cameras'].items()])
