"""Original per-pane CC0 glass with an independent real T-frame per opening."""
from pathlib import Path
import hashlib,json
import numpy as np
from shapely.geometry import box
from shapely.ops import unary_union
HERE=Path(__file__).resolve().parent

def homography(quad):
 a=[];b=[]
 for (u,v),(x,y) in zip([(0,0),(1,0),(1,1),(0,1)],quad):
  a.extend([[u,v,1,0,0,0,-u*x,-v*x],[0,0,0,u,v,1,-u*y,-v*y]]);b.extend([x,y])
 return np.r_[np.linalg.solve(a,b),1].reshape(3,3)

class RegisteredGlazing:
 def __init__(self):
  self.controls=json.loads((HERE/'photo-glass-controls.json').read_text());self.image=HERE/self.controls['image'];raw=self.image.read_bytes()
  if len(raw)!=self.controls['image_bytes'] or hashlib.sha256(raw).hexdigest()!=self.controls['image_sha256']:raise ValueError('Reference JPEG changed')
  self.windows={w['label']:w for w in self.controls['windows']};self.evidence=[]
 def window(self,f,shape,label):
  ctl=self.windows[label];inner=shape.buffer(-.09,join_style=2);x0,z0,x1,z1=inner.bounds;u=(x0+x1)/2;split=z1-(z1-z0)*ctl['top_pane_fraction_of_inner_height'];mx=x0+(x1-x0)*ctl['lower_middle_mullion_fraction']
  shapes=[box(x0,split+.042,x1,z1),box(x0,z0,mx-.030,split-.042),box(mx+.030,z0,x1,split-.042)];ids=[]
  for q,pane in zip(shapes,ctl['panes']):
   a,b,c,d=q.bounds;plabel=label+'-registered-pane-'+pane['id'];f.prism(q,-.20,-.18,'recessed glass light',plabel);selected=f.builder.parts[-1];h=homography(pane['source_quad_px'])
   def uv(p,h=h,a=a,b=b,c=c,d=d):
    p=np.asarray(p);u=float(np.dot(p-f.center,f.t));s=(u-a)/(c-a);t=(d-p[2])/(d-b);v=h@np.array([s,t,1.]);return [v[0]/v[2]/5184,v[1]/v[2]/3456]
   f.builder.photograph_parts(self.image,uv,lambda p:p is selected,name='PhotoFacade_Bund07_RegisteredGlass',roughness=.53,orientation={'rawSize':[5184,3456],'exifOrientation':1,'uvConvention':'stored-pixels'})
   self.evidence.append({'part':selected['label'],'window':label,'pane':pane['id'],'bounds_facade_uz_m':[a,b,c,d],'depth_m':[-.20,-.18],'source_quad_px':pane['source_quad_px'],'stored_uv_corners':[uv(f.point(x,z,-.18)) for x,z in [(a,d),(c,d),(c,b),(a,b)]]})
  outer=shape.buffer(-.025,join_style=2);f.prism(outer.difference(unary_union(shapes)),-.27,-.16,'bronze window frame',label+'-registered-T-frame-grid')
  f.prism(shape.buffer(.16,join_style=2).difference(shape),-.025,.105,'carved pale stone',label+'-surround');a,b,c,d=shape.bounds;f.box((a+c)/2,b-.07,c-a+.30,.14,.60,.10,label=label+'-sill')
 def report(self):
  return {'schema':'bund07-photo-uv-evidence-v1','source':{k:self.controls[k] for k in ['image','image_sha256','image_bytes','source_url','author','license','date','coordinate_contract','scope','limitations']},'window_count':len(set(p['window'] for p in self.evidence)),'glazing_parts':len(self.evidence),'mapped_material':'PhotoFacade_Bund07_RegisteredGlass','controls_sha256':hashlib.sha256((HERE/'photo-glass-controls.json').read_bytes()).hexdigest(),'original_pixels_unchanged':True,'stone_and_frames_textured':False,'per_pane':self.evidence}
