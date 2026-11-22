"""An isolated cement fretwork panel with five measured openings and moulded rails."""
from pathlib import Path
import json,numpy as np
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
BASE=Path(__file__).parent;data=json.loads((BASE/'pierced-pattern.json').read_bytes());HOLES={k:Polygon(v)for k,v in data['outline_metres'].items()}
FACE='Cast cream mortar';REVEAL='Warm grey reveals';EDGE='Chamfer in sunlight';CAP='Grey upper rail';SHADOW='Lower edge shadow';PLINTH='Grey base moulding'
colors={FACE:(255,255,255),REVEAL:(148,141,123),EDGE:(198,189,167),CAP:(169,166,150),SHADOW:(120,120,105),PLINTH:(177,172,156)}
PALETTE={k:dict(color=[(v/255)**2.2 for v in c],roughness=.94)for k,c in colors.items()};PALETTE[FACE]['texture']=str(BASE/'cast-lime.png')
def slab(b,geom,front,back,mat,name):
 for piece in getattr(geom,'geoms',[geom]):
  if piece.geom_type=='Polygon'and piece.area>1.e-8:b.prism(piece,-back,-front,lambda x,z,j:(x,-j,z),mat,label=name)
def tile_uv(b):
 for p in b.parts:
  if p['material']!=FACE:continue
  prior=np.array(p['vertices']);vs=[];tri=[];uv=[]
  for seq in p['triangles']:
   pts=prior[np.asarray(seq)];n=len(vs);tri.append([n,n+1,n+2]);axis=np.argmax(np.abs(np.cross(pts[1]-pts[0],pts[2]-pts[0])));vs.extend(pts.tolist())
   for x,y,z in pts:uv.append([(x+.34)/.68 if axis!=0 else y/.12,1-z/.62])
  p.update(vertices=vs,triangles=tri,texcoords=uv)
def model(b,lod=False):
 holes={k:(v.simplify(.008,preserve_topology=True)if lod else v) for k,v in HOLES.items()}
 panel=box(-.34,.009,.34,.575);baseholes=unary_union(list(holes.values()));open_front={k:v.buffer(.0045,quad_segs=2,join_style='mitre')for k,v in holes.items()}
 slab(b,panel.difference(unary_union(list(open_front.values()))),0,.007,FACE,'Front cast surface')
 slab(b,panel.difference(baseholes),.007,.094,REVEAL,'Pierced body and aperture returns')
 for name,poly in holes.items():
  rim=open_front[name].difference(poly);slab(b,rim,.0035,.007,EDGE,name+' eased lip')
 slab(b,panel.difference(baseholes),.094,.099,FACE,'Back face around five openings')
 for lo,hi,f,back,mat,n in [(-.074,-.050,-.019,.118,PLINTH,'Base plinth'),(-.050,-.038,-.032,.132,SHADOW,'Lower fillet'),(-.038,-.009,-.026,.126,PLINTH,'Lower moulded bead'),(-.009,.018,-.013,.112,PLINTH,'Foot of cast field'),(.568,.581,-.016,.114,SHADOW,'Shadow below rail'),(.581,.610,-.030,.129,CAP,'Upper rail'),(.610,.619,-.023,.123,CAP,'Top arris')]:
  b.box((0,(f+back)/2,(lo+hi)/2),(.695,back-f,hi-lo),mat,label=n)
 tile_uv(b)
