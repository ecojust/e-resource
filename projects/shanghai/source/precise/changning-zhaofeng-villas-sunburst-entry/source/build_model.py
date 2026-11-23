"""Measured street-side relief of the east name wall at the entrance of Jessfield Villas."""
from pathlib import Path
import argparse,json,math,sys
import numpy as np
from shapely.geometry import LineString,Polygon,box
HERE=Path(__file__).absolute().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-general-post-office/source/common'))
from photo_architecture import Builder
import street_gate
ID='changning-zhaofeng-villas-sunburst-entry'
META={'id':ID,'heritage_id':'sh-historic-b3-099','name':'兆丰别墅长宁路弄口题名墙','address':'长宁路712弄','scope':'长宁路入口东西灰墙、开向弄内的两扇铁门、两盏半圆壁灯、东侧花台和阶梯日升纹题名墙。','viewer_page':'zhaofeng-villas-sunburst-entry.html','geometry_license':'MIT','photos_embedded':False}
PLASTER='grey-pink aggregate plaster';EDGE='worn pale cement';IRON='patinated cast letters';BRASS='bronze lamp frame';GLASS='warm opal lamp';MARBLE='heritage plaque stone';ENAMEL='interpretive enamel'
PALETTE={name:{'color':color,'roughness':rough}for name,color,rough in [(PLASTER,[.51,.481,.483],.91),(EDGE,[.59,.566,.55],.86),(IRON,[.113,.106,.114],.46),(BRASS,[.338,.263,.166],.54),(GLASS,[.823,.747,.533],.38),(MARBLE,[.695,.683,.625],.82),(ENAMEL,[.773,.690,.517],.57)]}
data=json.loads((HERE/'registered-name.json').read_bytes());H=np.asarray(data['image_to_initial_xz'])
def measured(pixel):
 p=H@[*pixel,1];return tuple(p[:2]/p[2])
def face(x,z,d):return (x,-d,z)
def build(lod=False):
 b=Builder(PALETTE)
 def sculpt(shape,low,high,material,group):
  if not shape.is_empty:b.prism(shape,low,high,face,material,group)
 def profile(uv,low,high,material,group):
  sculpt(Polygon([measured(p)for p in uv]),low,high,material,group)
 def edge(uv,width,back,front,group):
  poly=LineString([measured(p)for p in uv]).buffer(width/2,cap_style='flat',join_style='mitre')
  sculpt(poly,back,front,EDGE,group)
 # The stepped silhouette, five downward chevrons and radial ornament belong to
 # the masonry name wall. The separate western traffic pier is outside this study.
 sky=[(399,205),(400,200),(477,189),(478,157),(559,145),(559,108),(648,95),(655,133),(744,119),(752,160),(856,146),(861,121),(908,110)]
 low=[(915,606),(400,637)]
 profile(sky+low,-.23,0,PLASTER,'wall/stepped sunburst silhouette')
 # Relief shapes are separated by genuine shallow recessed channels.
 sun=[(566,230),(568,218),(572,211),(576,204),(581,200),(590,195),(598,192),(609,191),(619,192),(632,195),(643,202),(652,212),(657,222)]
 profile(sun,-.004,.030,EDGE,'sun/half disk')
 rays=[[(482,196),(516,192),(568,216),(567,224),(484,226)],
       [(520,190),(559,153),(577,204),(571,212)],
       [(564,151),(602,146),(607,190),(589,195)],
       [(610,145),(648,140),(626,194),(613,190)],
       [(651,146),(654,178),(684,175),(643,202),(634,196)],
       [(655,182),(694,176),(737,166),(655,212),(647,205)],
       [(660,215),(746,197),(746,210),(661,224)]]
 for i,uv in enumerate(rays):profile(uv,-.003,.026,EDGE,f'sun/radial facet {i+1:02}')
 for i,uv in enumerate([[(403,207),(438,236),(476,197)],[(483,160),(521,185),(555,149)],[(563,110),(605,139),(646,99)],[(656,134),(701,164),(742,123)],[(754,164),(810,194),(852,149)]]):
  edge(uv,.018,-.002,.029,f'crown/chevron {i+1:02}')
 for name,quad,depth in [('cap',[(478,247),(758,216),(763,231),(482,260)],.086),('lower lip',[(483,261),(765,237),(761,244),(484,270)],.051),('name sill',[(486,359),(779,339),(782,350),(489,371)],.058)]:
  profile(quad,-.003,depth,EDGE,'cornices/'+name)
 for i,glyph in enumerate(data['glyphs']):
  for j,(shell,*holes) in enumerate(glyph['loops']):
   glyph_poly=Polygon(shell,holes).buffer(-.0007,join_style='mitre').simplify(.0032 if lod else .0003,preserve_topology=True)
   sculpt(glyph_poly,-.004,.041,IRON,f'cast name/character {i+1} stroke {j+1:02}')
 # Flutes below the name sill are shallow relief, including the longer returns at either end.
 for i in range(21):
  t=i/20;x=491+278*t;y=370-19*t
  length=(132 if i<3 or i>18 else 31)*(1+.09*t)
  profile([(x,y+1),(x+6,y+.5),(x+6.5+length*.064,y+length),(x+length*.064,y+length+.3)],-.003,.018,EDGE,f'plaque field/flute {i+1:02}')
 profile([(531,405),(618,399),(625,472),(536,477)],-.005,.030,MARBLE,'plaques/municipal designation')
 profile([(651,412),(658,409),(670,406),(675,399),(682,394),(695,393),(703,398),(713,405),(725,407),(732,471),(719,473),(714,486),(695,497),(675,494),(672,482),(655,481)],-.005,.029,ENAMEL,'plaques/lane history plate')
 # Wall-mounted half-round lantern with two end caps, ring mouldings and vertical ribs.
 center_x,center_z=measured((442,389));height=abs(measured((442,342))[1]-measured((442,438))[1]);radius=abs(measured((454,389))[0]-center_x)
 base=center_z-.5*height
 def lantern_part(z0,z1,r0,r1,material,label):
  n=6 if lod else 16;verts=[]
  for zz,rr in ((z0,r0),(z1,r1)):
   verts.append((center_x,-.009,zz))
   verts.extend((center_x+rr*math.cos(t),-.009-rr*math.sin(t),zz)for t in np.linspace(0,math.pi,n+1))
  k=n+2;faces=[]
  for i in range(1,n+1):
   faces.extend([(0,i,i+1),(k,k+i+1,k+i)])
  for i in range(k):
   j=(i+1)%k
   faces.append((i,i+k,j+k,j))
  b.add(verts,faces,material,label)
 lantern_part(base+.06*height,base+.94*height,radius*.84,radius*.84,GLASS,'lantern/opal semicylinder')
 for i,t in enumerate([0,.08,.23,.76,.91,.97]):
  lantern_part(base+t*height,base+(t+.027)*height,radius*(.82 if i in (0,5)else .91),radius*.93,BRASS,f'lantern/horizontal frame {i+1}')
 for i,t in enumerate([.18,.5,.82]):
  theta=t*math.pi
  x=center_x+radius*.89*math.cos(theta);y=-.009-radius*.89*math.sin(theta)
  b.box((x,y,base+.5*height),(.010,.012,height*.86),BRASS,label=f'lantern/vertical rib {i+1}')
 return street_gate.assemble(b,lod)
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True,type=Path);parser.add_argument('--lod',action='store_true');args=parser.parse_args()
 result=build(args.lod).save(args.output,META);print(result['sha256'])
