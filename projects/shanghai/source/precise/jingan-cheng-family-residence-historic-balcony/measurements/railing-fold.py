"""Fit visible changes in projected rail direction to two traces on the period print."""
import argparse,json,hashlib
from pathlib import Path
from PIL import Image
import numpy as np
from scipy.ndimage import gaussian_filter
from scipy.optimize import least_squares
from importlib.util import spec_from_file_location,module_from_spec
m=spec_from_file_location('measure_rail',Path(__file__).with_name('measure-rail.py'));lib=module_from_spec(m);m.loader.exec_module(lib)
def folded(x,knots,beta):
 return beta[0]+beta[1]*(x-90)+sum(c*np.maximum(0,x-k)for c,k in zip(beta[2:],knots))
def trace(im,pts):
 ax,ay=np.array(pts).T;xp=np.arange(max(82,ax.min()),ax.max()+1);yp=np.interp(xp,ax,ay);curve=gaussian_filter(im,.82)
 def lines(i):
  ux=xp[i];ys=np.arange(yp[i]-3,yp[i]+3.001,.125)
  v=lib.sample(curve,np.stack((np.full_like(ys,ux),ys),axis=1))
  best=np.argmin(np.gradient(v,ys)[3:-3])+3;besty=ys[best]
  low,high=lib.sample(im,np.array([[ux,besty-2],[ux,besty+2]]))
  return (ux,besty,low-high)
 r=np.array([lines(i)for i in range(len(xp))]);r=r[r[:,2]>48]
 return r
def fit(r,line):
 x,y=r[:,:2].T
 initial=np.array([126.,192.,239.]);bounds=([106,175,224],[148,208,253])
 def solve(rr):
  u,v=rr[:,:2].T
  def res(par):return folded(u,par[:3],par[3:])-v
  fit=least_squares(res,[*initial,y[0],0,0,.01,.1],bounds=([*bounds[0],150,-1,-2,-2,-2],[*bounds[1],260,1,2,2,2]),loss='soft_l1',f_scale=.55)
  return fit.x
 p=solve(r);return p,np.median(np.abs(folded(x,p[:3],p[3:])-y)),[solve(r[j::3])for j in range(3)]
def main(fine,reg,measurements,out):
 im=np.asarray(Image.open(fine).convert('L'),float);m=json.loads(measurements.read_text());H=json.loads(reg.read_text())['matrix_323_to_640'];inv=np.linalg.inv(H)
 record=dict(source=hashlib.sha256(fine.read_bytes()).hexdigest(),method='沿原照中已量出的栏顶、栏底分别采逐列实边。仅保留上下4像素亮差超过48/255的列，再对三处可疑转向区域作连续折线软L1拟合。每三列分组独立拟合，用组间差和两条边各自的斜率差标识分辨能力。转折点是断线交会估计，不是照片中见到的石件接缝。',traces=[])
 for label,j in [('帽石上缘',0),('栏身底边接线',1)]:
  pts=[x['pixel_640']for x in m['rail_edge_samples']if x['label']==label];r=trace(im,pts);p,med,cross=fit(r,j);slopes=np.cumsum(p[4:]);recs=[]
  for k,xx in enumerate(p[:3]):
   yy=folded(xx,p[:3],p[3:]);low=lib.project(inv,[xx,yy]);xxs=[q[k]for q in cross]
   recs.append(dict(pixel_640=lib.rounded([xx,yy]),mapped_pixel_323=lib.rounded(low),slope_before_after=lib.rounded(slopes[k:k+2]),third_split_x_range_640=lib.rounded([min(xxs),max(xxs)]),model_dependent=True))
  record['traces'].append(dict(name=label,observed_edge_pixels_640=lib.rounded(r[:,:2]),strong_columns=len(r),median_line_to_measured_pixel_640=round(float(med),3),intersections=recs))
 out.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();[p.add_argument(a,type=Path)for a in ['fine','reg','measurements','out']];a=p.parse_args();main(a.fine,a.reg,a.measurements,a.out)
