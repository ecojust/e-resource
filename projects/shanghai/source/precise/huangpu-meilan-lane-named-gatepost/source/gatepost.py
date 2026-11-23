"""Street face of the left named pier and plaque wall at 596 South Huangpi Road."""
from pathlib import Path
from math import sin,cos,pi
import json
from shapely import affinity
from shapely.geometry import box,Polygon,Point,shape,LineString
from shapely.ops import unary_union
SOURCE=Path(__file__).parent
PALETTE={
 'grey dressed stone':{'color':[.38,.36,.32],'roughness':.92},'recessed stone':{'color':[.31,.30,.27],'roughness':.92},
 'cap stone':{'color':[.47,.45,.40],'roughness':.83},'weathered plinth':{'color':[.31,.29,.265],'roughness':.93},
 'gilt lettering':{'color':[.80,.52,.18],'metallic':.41,'roughness':.48},
 'dark carved mark':{'color':[.22,.21,.19],'roughness':.91},'nameplate green':{'color':[.035,.195,.126],'roughness':.46},
 'white enamel':{'color':[.88,.86,.76],'roughness':.54},'pale metal plaque':{'color':[.69,.665,.58],'roughness':.63,'metallic':.18},
 'dark raised text':{'color':[.13,.124,.105],'roughness':.81},'antique brass':{'color':[.47,.335,.21],'metallic':.34,'roughness':.57},
 'case dark metal':{'color':[.28,.255,.21],'metallic':.26,'roughness':.63},
 'notice under glass':{'color':[.45,.50,.46],'roughness':.50},'notice backing':{'color':[.65,.63,.55],'roughness':.87},
 'red lamp lens':{'color':[.44,.065,.064],'roughness':.38},'lamp silver bezel':{'color':[.51,.50,.44],'roughness':.43,'metallic':.42},
}
def panel(b,outline,front,back,material,label):
 b.prism(outline,-back,-front,lambda x,z,d:(x,-d,z),material,label)
def rect(b,x,z,width,height,front,back,material,label):
 panel(b,box(x-width/2,z-height/2,x+width/2,z+height/2),front,back,material,label)
def edge(b,x,z,width,height,thick,front,back,mat,label):
 outer=box(x-width/2,z-height/2,x+width/2,z+height/2)
 panel(b,outer.difference(outer.buffer(-thick,join_style=2)),front,back,mat,label)
def tiers(b,levels,material,name):
 verts=[];faces=[(3,2,1,0)]
 for i,(width,depth,z,center_y)in enumerate(levels):
  verts.extend([(xx*width/2,center_y+yy*depth/2,z)for xx,yy in [(-1,-1),(1,-1),(1,1),(-1,1)]])
  if i:
   k=4*(i-1);faces.extend((k+j,k+(j+1)%4,k+(j+1)%4+4,k+j+4)for j in range(4))
 k=len(verts)-4;faces.append((k,k+1,k+2,k+3));b.add(verts,faces,material,name)
def title(b,txt,x,z,width,height,front,back,mat,label,lod):
 from sign_lettering import lettering_shapes
 for i,(_,glyph) in enumerate(lettering_shapes(txt,width,height,font=SOURCE/'fonts/MeilanPlaque.otf')):
  glyph=affinity.translate(glyph.simplify(.00048 if lod else .00022,preserve_topology=True),xoff=x,yoff=z)
  panel(b,glyph,front,back,mat,label+' '+str(i))
def add_gatepost(b,lod=False):
 # The relief at y=0 faces the street. Positive Y lies behind the plaque.
 tiers(b,[(.70,.75,.00,.32),(.70,.75,.37,.32),(.696,.743,.405,.32),(.643,.706,.44,.32)],'weathered plinth','pier square plinth and chamfer')
 outer=box(-.301,.44,.301,3.38)
 inset=box(-.24,.50,.24,3.26)
 panel(b,outer.difference(inset),-.010,.65,'grey dressed stone','stone uprights and recessed name panel')
 panel(b,inset,.008,.65,'recessed stone','sunken panel ground')
 edge(b,0,1.88,.504,2.82,.013,-.016,.009,'cap stone','narrow panel edge')
 tiers(b,[(.61,.675,3.38,.32),(.64,.71,3.414,.32),(.674,.738,3.434,.32),(.674,.738,3.467,.32)],'cap stone','under-cap tablet and drip')
 tiers(b,[(.651,.715,3.467,.32),(.687,.748,3.515,.32),(.763,.785,3.55,.32),(.763,.785,3.616,.32),(.716,.755,3.643,.32),(.687,.727,3.71,.32)],'grey dressed stone','stepped stone cap')
 # The upper panel carries the linked recessed ornaments visible in the traveller close-up.
 for i,(x,z)in enumerate([(-.085,2.985),(.020,2.995),(.095,2.989),(-.035,2.907),(.066,2.909)]):
  pts=[(x+.041*cos(pi+(k/14)*pi),.003,z+.059*sin(pi+(k/14)*pi)) for k in range(15)]
  b.tube(pts,.006,'dark carved mark',sides=5 if lod else 8,label='linked carving '+str(i))
 letters=json.loads((SOURCE/'named-letter-shapes.json').read_bytes())['letters']
 for i,(char,z)in enumerate([('梅',2.256),('兰',1.856),('坊',1.355)]):
  outline=shape(letters[char]['geometry']).simplify(.0011 if lod else .00035,preserve_topology=True)
  outline=affinity.translate(outline,xoff=0,zoff=0,yoff=z)
  panel(b,outline,-.022,.008,'gilt lettering','raised gilt name '+char)
 # The present southern plaque wall ends at the edge of the older banded street pier.
 rect(b,-.878,1.143,1.154,2.286,.052,.335,'grey dressed stone','plaque wall body')
 rect(b,-.88,.226,1.148,.452,.040,.052,'weathered plinth','plaque wall splash base')
 rect(b,-.88,2.316,1.183,.062,.019,.35,'cap stone','shallow wall coping')
 rect(b,-.692,2.121,.518,.164,.008,.052,'nameplate green','green enamel street address')
 title(b,'596弄1–58号',-.692,2.145,.469,.067,.003,.008,'white enamel','number plate top',lod)
 title(b,'黄陂南路',-.692,2.087,.297,.045,.003,.008,'white enamel','number plate lower line',lod)
 rect(b,-.573,1.751,.465,.409,.019,.052,'case dark metal','shadow of heritage plaque')
 rect(b,-.573,1.758,.457,.398,.005,.019,'pale metal plaque','Shanghai heritage plaque')
 title(b,'优秀历史建筑',-.573,1.829,.305,.039,.001,.005,'dark raised text','heritage title Chinese',lod)
 if not lod:title(b,'HERITAGE ARCHITECTURE',-.573,1.793,.323,.020,.001,.005,'dark raised text','heritage title English',lod)
 for i,(x,z)in enumerate([(-.77,1.92),(-.376,1.92),(-.77,1.596),(-.376,1.596)]):
  panel(b,Point(x,z).buffer(.0055,quad_segs=4),.002,.005,'case dark metal','plaque fixing '+str(i))
 # The display is glazed. Smaller text and its temporary notice are unresolved.
 rect(b,-.555,1.105,.291,.555,.022,.052,'case dark metal','recess of information case')
 edge(b,-.555,1.105,.296,.558,.023,-.002,.022,'antique brass','notice case brass surround')
 rect(b,-.555,1.105,.25,.512,.012,.022,'notice under glass','grey notice glass')
 rect(b,-.555,1.043,.209,.265,.009,.012,'notice backing','notice light lower sheet')
 # The ochre plate to the south is visible in the 2015, 2019 and 2020 road series.
 rect(b,-1.14,1.805,.375,.235,.006,.052,'antique brass','adjacent unlettered rectangular plate')
 for x,z,rad,front,back,mat,label in [(-.373,2.241,.057,-.007,.052,'lamp silver bezel','round alarm rim'),(-.373,2.241,.046,-.026,-.007,'red lamp lens','red alarm cap')]:
  panel(b,Point(x,z).buffer(rad,quad_segs=8 if lod else 20),front,back,mat,label)
