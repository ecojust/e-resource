"""The inscribed balcony at Lane 553, Middle Fuxing Road. X increases to a viewer's right."""
from pathlib import Path
from math import hypot
import json
from shapely.geometry import box, Polygon, shape
from shapely import affinity

PALETTE={
 'grey balcony concrete':dict(color=[.375,.356,.325],roughness=.91),
 'light stone frame':dict(color=[.548,.511,.444],roughness=.90),
 'title panel stone':dict(color=[.638,.598,.510],roughness=.87),
 'recessed side panel':dict(color=[.43,.401,.353],roughness=.90),
 'lower concrete drip':dict(color=[.295,.279,.246],roughness=.93),
 'red painted inscription':dict(color=[.54,.077,.063],roughness=.79),
 'dark shutter timber':dict(color=[.115,.071,.053],roughness=.81),
 'shutter blade':dict(color=[.172,.102,.072],roughness=.79),
 'timber reveal':dict(color=[.082,.059,.046],roughness=.89),
 'stone opening surround':dict(color=[.48,.451,.393],roughness=.90),
 'brick mortar':dict(color=[.34,.255,.205],roughness=.95),
 'red facing brick':dict(color=[.407,.191,.127],roughness=.93),
 'weathered facing brick':dict(color=[.366,.161,.112],roughness=.94),
 'iron shutter hinge':dict(color=[.133,.122,.102],metallic=.28,roughness=.72),
}
FRONT=[(-1.22,.35),(-.85,0),(.85,0),(1.22,.35)]
def section(b,foot,z0,z1,mat,name):
 b.prism(foot,z0,z1,lambda x,y,z:(x,y,z),mat,name)
def vertical(b,x0,x1,z0,z1,y0,y1,mat,name):
 b.prism(box(x0,z0,x1,z1),-y1,-y0,lambda x,z,d:(x,-d,z),mat,name)
def facet(b,a,c,g,d0,d1,mat,name):
 dx,dy=c[0]-a[0],c[1]-a[1];n=hypot(dx,dy);ux,uy=dx/n,dy/n
 b.prism(g,d0,d1,lambda u,z,d:(a[0]+u*ux+d*uy,a[1]+u*uy-d*ux,z),mat,name)
def band(b,path,z0,z1,thickness,outset,material,label):
 shell=Polygon([*path,(path[-1][0],1.0),(path[0][0],1.0)])
 # An outward mitred edge, cut off behind the squared returns at the wall.
 cross=shell.buffer(outset,join_style=2).difference(shell.buffer(-thickness,join_style=2))
 cross=cross.intersection(box(-1.5,-.2,1.5,.96))
 section(b,cross,z0,z1,material,label)
def add_balcony(b,lod=False):
 deck=Polygon([*FRONT,(1.22,1.07),(-1.22,1.07)])
 section(b,deck,3.905,4.015,'lower concrete drip','projecting balcony soffit')
 for index,x in enumerate([-.62,.62]):
  # The two downstands beneath the street-facing edge are visible in the 2015 oblique.
  profile=Polygon([(.06,3.82),(.30,3.82),(.83,3.68),(1.00,3.68),(1.,3.905),(.06,3.905)])
  b.prism(profile,x-.064,x+.064,lambda y,z,u:(u,y,z),'grey balcony concrete','short underside bracket '+str(index+1))
 band(b,FRONT,4.014,4.082,.115,.045,'light stone frame','three-sided projecting base nosing')
 band(b,FRONT,4.082,4.115,.11,.020,'grey balcony concrete','lower bevelled shadow course')
 for i,(a,c) in enumerate(zip(FRONT,FRONT[1:])):
  width=hypot(c[0]-a[0],c[1]-a[1]);name='facet '+str(i+1)
  outer=box(0,4.114,width,4.916)
  inner=box(.064,4.173,width-.064,4.856)
  insert=outer.difference(inner)
  facet(b,a,c,insert,-.102,.012,'light stone frame',name+' solid border')
  facet(b,a,c,inner,-.105,-.011,'title panel stone' if i==1 else 'recessed side panel',name+' recessed stone')
  fine=inner.difference(inner.buffer(-.013,join_style=2))
  facet(b,a,c,fine,-.012,-.003,'grey balcony concrete',name+' inner stone fillet')
 for i,x in enumerate((-1.22,1.22)):
  section(b,box(x-.047,.35,x+.047,.97),4.022,4.918,'grey balcony concrete','side return '+str(i+1))
 band(b,FRONT,4.916,4.954,.115,.015,'grey balcony concrete','under-coping fillet')
 band(b,FRONT,4.954,4.994,.12,.052,'light stone frame','projecting top coping')
 band(b,FRONT,4.994,5.012,.115,.038,'grey balcony concrete','coping flat top')
 g=json.loads((Path(__file__).with_name('painted-title.json')).read_bytes())['letters']
 for ch,outline in g.items():
  glyph=affinity.translate(shape(outline).simplify(.0022 if lod else .0008,preserve_topology=True),xoff=.85,yoff=4.516)
  facet(b,FRONT[1],FRONT[2],glyph,-.0112,-.0082,'red painted inscription','red painted character '+ch)
 # The rear window is restricted to the central pair and the adjacent returns visible from the street.
 xmin,xmax=-.40,.68;outer=box(xmin,5.128,xmax,6.82);aperture=box(xmin+.092,5.220,xmax-.092,6.718)
 b.prism(outer.difference(aperture),-1.15,-.91,lambda x,z,d:(x,-d,z),'stone opening surround','four-sided stone window reveal')
 b.prism(aperture,-1.15,-1.09,lambda x,z,d:(x,-d,z),'timber reveal','recess behind louvers')
 for k,(left,right) in enumerate([(-.94,xmin),(xmax,1.06)]):
  vertical(b,left,right,4.97,6.82,.957,1.15,'brick mortar','brick strip bedding '+str(k))
  for row in range(23):
   h=.0875;bottom=4.978+row*h;top=min(6.82,bottom+h-.008)
   if top<=bottom:break
   x=left-(row%2)*.112
   while x<right:
    l,r=max(left,x+.003),min(right,x+.223)
    if r>l+.009:vertical(b,l,r,bottom,top,.945,.958,'red facing brick' if (row+int(x*18))%7 else 'weathered facing brick','running-bond pier '+str(k))
    x+=.228
 for leaf,(left,right) in enumerate([(-.308,.137),(.143,.588)]):
  outside=box(left,5.220,right,6.718);inside=box(left+.043,5.262,right-.043,6.667)
  b.prism(outside.difference(inside),-1.066,-.973,lambda x,z,d:(x,-d,z),'dark shutter timber','shutter leaf frame '+str(leaf+1))
  # Pitch and the upper overlap follow the photographed slats. Keep every opening at both distances.
  for j in range(24):
   z=5.263+j*.0585
   yz=Polygon([(.992,z+.012),(1.031,z+.063),(1.045,z+.058),(1.006,z+.007)])
   b.prism(yz,left+.04,right-.04,lambda y,h,x:(x,y,h),'shutter blade','inclined louver leaf '+str(leaf+1))
  for z in (5.35,6.54):
   x=left+.025 if leaf==0 else right-.025
   vertical(b,x-.014,x+.014,z-.033,z+.033,.965,.976,'iron shutter hinge','hinge of shutter '+str(leaf+1))
 vertical(b,-.43,.71,5.128,5.173,.887,1.14,'stone opening surround','projecting stone threshold')

 if lod:
  # The brick backs terminate inside mortar. Louver end caps sit 3 mm inside
  # each leaf frame, and the back of the red paint lies in the stone panel.
  for part in b.parts:
   material=part['material'];label=part['label'];vertices=part['vertices']
   if label.startswith('running-bond pier'):
    axis=1;interior=[.958]
   elif label.startswith('inclined louver leaf'):
    axis=0;xs=[point[0] for point in vertices];interior=[min(xs),max(xs)]
   elif material=='red painted inscription':
    axis=1;interior=[.0112]
   else:continue
   part['triangles']=[face for face in part['triangles'] if not any(
       all(abs(vertices[k][axis]-plane)<1e-7 for k in face) for plane in interior)]
