"""Build independently framed, individually registered glazing panes.

The source JPEG is embedded byte-for-byte. Geometry and UV use the actual
flat central facade; no canted bay is projected through the front-plane fit.
"""
import json,hashlib
from pathlib import Path
import numpy as np
from shapely.geometry import box
from shapely.ops import unary_union
HERE=Path(__file__).resolve().parent

def pane_homography(quad):
 a=[];b=[]
 for (u,v),(x,y) in zip([(0,0),(1,0),(1,1),(0,1)],quad):
  a.extend([[u,v,1,0,0,0,-u*x,-v*x],[0,0,0,u,v,1,-u*y,-v*y]]);b.extend([x,y])
 return np.r_[np.linalg.solve(a,b),1].reshape(3,3)

class RegisteredGlazing:
 def __init__(self):
  self.controls=json.loads((HERE/'photo-glass-controls.json').read_text())
  self.image=HERE/self.controls['image'];raw=self.image.read_bytes()
  if len(raw)!=self.controls['image_bytes'] or hashlib.sha256(raw).hexdigest()!=self.controls['image_sha256']:raise ValueError('Reference photo changed')
  self.evidence=[]
 def window(self,f,shape,label):
  x0,z0,x1,z1=shape.bounds;u=(x0+x1)/2
  floor=int(label.rsplit('-',1)[1]);side='left' if u<0 else 'right'
  ctl=next(w for w in self.controls['windows'] if w['floor']==floor and w['side']==side)
  inner=shape.buffer(-.09,join_style=2);ix0,iz0,ix1,iz1=inner.bounds
  outer=shape.buffer(-.025,join_style=2)
  # Measured relative bar positions are preserved as fractions of each opening.
  # Shape dimensions/reveal depth still follow the separate geometry calibration.
  xs=[ix0]+[ix0+(ix1-ix0)*q['center'] for q in ctl['vertical_bar_observations']]+[ix1]
  ys=[iz1]+[iz1-(iz1-iz0)*q['center'] for q in ctl['horizontal_bar_observations']]+[iz0]
  xb=[0]+[.049 if k==1 else .024 for k in range(3)]+[0]
  heavy_row=1 if floor==5 else 2
  yb=[0]+[.048 if k==heavy_row else .024 for k in range(1,ctl['rows'])]+[0]
  polygons=[]
  for pane in ctl['panes']:
   r=pane['row_from_top'];c=pane['column_from_left']
   l=xs[c]+xb[c];right=xs[c+1]-xb[c+1];top=ys[r]-yb[r];bottom=ys[r+1]+yb[r+1]
   q=box(l,bottom,right,top);polygons.append(q)
   plabel=f'{label}-{side}-pane-{r}-{c}'
   f.prism(q,-.20,-.18,'recessed glass',plabel)
   selected=f.builder.parts[-1];h=pane_homography(pane['source_oriented_quad_px'])
   def uv(p,h=h,l=l,right=right,top=top,bottom=bottom):
    p=np.asarray(p);pu=float(np.dot(p-f.center,f.t));v=(top-p[2])/(top-bottom);s=(pu-l)/(right-l)
    out=h@np.array([s,v,1]);x,y=out[:2]/out[2]
    return [y/5184,(3455-x)/3456]
   result=f.builder.photograph_parts(self.image,uv,lambda p:p is selected,name='PhotoFacade_Bund05_RegisteredGlass',roughness=.48,orientation={'rawSize':[5184,3456],'exifOrientation':6,'uvConvention':'stored-pixels'})
   self.evidence.append({'part':selected['label'],'window':ctl['id'],'pane':[r,c],'bounds_facade_uz_m':[l,bottom,right,top],'depth_m':[-.20,-.18],'source_oriented_quad_px':pane['source_oriented_quad_px'],'stored_uv_corners':[uv(f.point(a,b,-.18)) for a,b in [(l,top),(right,top),(right,bottom),(l,bottom)]]})
  # One closed, shared-grid frame per window, without intersecting bar boxes.
  f.prism(outer.difference(unary_union(polygons)),-.27,-.16,'bronze window frame',label+'-'+side+'-registered-frame-grid')
  f.prism(shape.buffer(.16,join_style=2).difference(shape),-.025,.105,'carved pale stone',label+'-'+side+'-surround')
  f.box(u,z0-.07,x1-x0+.30,.14,.60,.10,'carved pale stone',label+'-'+side+'-sill')
 def report(self):
  return {'schema':'bund05-photo-uv-evidence-v1','source':{k:self.controls[k] for k in ['image','image_sha256','image_bytes','author','license','date','source_url','coordinate_contract','scope','limitations']},'window_count':6,'glazing_parts':len(self.evidence),'mapped_material':'PhotoFacade_Bund05_RegisteredGlass','photograph_controls_sha256':hashlib.sha256((HERE/'photo-glass-controls.json').read_bytes()).hexdigest(),'source_pixels_resampled':False,'stone_and_frames_textured':False,'per_pane':self.evidence}
