"""The upper projecting bay photographed at Cooper Apartments in Shanghai on 19 August 2017."""
from pathlib import Path
from math import sin,cos,pi
from shapely.geometry import box
import numpy as np
from PIL import Image

ID='jingan-cooper-apartments-open-casements'
WALL='Rough ivory render';REVEAL='Light ochre reveal';DARK='Recessed interior';SASH='Varnished left casement';RIGHT='Grey painted right casement';GLASS='Sky on glass';GLASS2='Shaded glass';EAVE='Green grey fascia';WOOD='Rafter tips';ROOF='Umber roof covering';CAP='Weathered flashing'
PALETTE={n:dict(color=c,roughness=r)for n,c,r in [(WALL,[1,1,1],.95),(REVEAL,[.55,.51,.42],.91),(DARK,[.13,.109,.095],.96),(SASH,[.39,.246,.12],.78),(RIGHT,[.49,.51,.475],.73),(GLASS,[.657,.718,.723],.34),(GLASS2,[.345,.408,.416],.38),(EAVE,[.26,.343,.312],.83),(WOOD,[.44,.386,.295],.91),(ROOF,[.269,.205,.168],.94),(CAP,[.317,.323,.291],.78)]}
def texture():
 p=Path(__file__).with_name('rough-ochre-render.png')
 if not p.exists():
  rng=np.random.default_rng(607);base=rng.normal(0,5,(480,480))
  for i in range(10000):
   x,y=rng.integers(1,475,2);base[y,x]+=8;base[y+1,x+1]-=15;base[y+1,x+2]-=7
  rgb=np.array([198,184,153])+base[:,:,None];Image.fromarray(rgb.clip(0,255).astype('u1')).quantize(105).save(p)
 PALETTE[WALL]['texture']=str(p)
def add_building(b,far=False):
 texture()
 def face(x,z,d):return x,-d,z
 def rect(x0,x1,z0,z1,d0,d1,material,name):b.prism(box(x0,z0,x1,z1),d0,d1,face,material,name)
 opening=box(-.783,.29,.783,1.731)
 b.prism(box(-1.49,0,1.49,2.60).difference(opening),-.40,0,face,WALL,'Upper level of pale rendered projecting bay')
 surround=box(-.826,.25,.826,1.778).difference(opening);b.prism(surround,-.04,.035,face,REVEAL,'Slim rim around dark opening')
 rect(-.783,.783,.29,1.731,-.365,-.359,DARK,'Shadowed room behind the open leaves')
 for hand,angle,timber,glass in [(-1,59,SASH,GLASS2),(1,37,RIGHT,GLASS)]:
  theta=angle*pi/180
  def swing(u,z,d):return hand*(.764-u*cos(theta))+hand*d*sin(theta),.102-u*sin(theta)-d*cos(theta),z
  def leaf(u0,u1,z0,z1,d0,d1,mat,name):
   # Signed horizontal coordinate keeps both mirrored leaf cross-sections right handed.
   axis=-hand
   a,c=sorted([axis*u0,axis*u1])
   b.prism(box(a,z0,c,z1),d0,d1,lambda u,z,d:swing(axis*u,z,d),mat,name)
  leaf(.025,.733,.319,1.701,0,.013,glass,'Reflecting pane carried by opening casement')
  for u in [.019,.735]:leaf(u-.022,u+.022,.29,1.731,-.012,.047,timber,'Upright side rail of each open leaf')
  for z in [.31,.758,1.216,1.712]:leaf(0,.756,z-.018,z+.018,-.012,.048,timber,'Two cross rails between three lights')
 rect(-1.616,1.616,2.475,2.633,-.195,.426,EAVE,'Continuous dark painted fascia under the roof edge')
 for x in [-1.368,-.694,.004,.704,1.365]:
  rect(x-.034,x+.034,2.379,2.492,-.042,.384,WOOD,'Short exposed rafter below fascia')
 # Wave ridges run down the shallow roof towards its front edge. Their proportions come from its silhouette.
 start=-1.64;step=.154;nx=22;phases=5 if far else 12
 for bay in range(nx):
  x0=start+bay*step
  for tick in range(phases):
   u0=tick/phases;u1=(tick+1)/phases
   def z(u,d):return 2.705-.125*d+.026*cos(u*2*pi)
   ax=x0+u0*step;bx=x0+u1*step;front=.48;back=-.34
   pts=[face(ax,z(u0,back),back),face(bx,z(u1,back),back),face(bx,z(u1,front),front),face(ax,z(u0,front),front),face(ax,z(u0,front)-.027,front),face(bx,z(u1,front)-.027,front)]
   b.add(pts,[(3,2,1,0),(2,3,4,5)],ROOF,'Undulating tiled roof edge and visible thickness')
 for p in b.parts:
  if p['material']==WALL:p['texcoords']=[[(x+.73*y+1.49)/3.29,z/2.60]for x,y,z in p['vertices']]
