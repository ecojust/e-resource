"""Photographic study of Wenyuan Building's entrance, Tongji University."""
from math import cos,sin,pi
RGB={'warm plaster':(210,196,166),'rain-darkened fascia':(167,157,135),'soffit':(177,172,155),'concrete columns':(193,191,178),'granite treads':(157,150,130),'granite risers':(132,123,105),'pale door stiles':(157,144,112),'lower door panels':(157,147,115),'steel green glass':(48,63,59),'entrance shadow':(62,62,54),'soffit lights':(99,95,82),'light faces':(202,194,167),'pull hardware':(165,153,126),'rainwater seam':(140,135,122)}
def linear(c):
 s=c/255
 return s/12.92 if s<=.04045 else ((s+.055)/1.055)**2.4
PALETTE={k:{'color':[linear(c) for c in rgb],'roughness':.65 if k=='steel green glass' else .84}for k,rgb in RGB.items()}
X=(-1.85,0,1.85)
FRONT=0.0
BACK=2.90
BASE=.39
SOFFIT=3.68
def add_building(b,lod=False):
 seg=12 if lod else 44
 def rect(label,x0,x1,y0,y1,z0,z1,mat):
  b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),mat,label=label)
 for j in range(3):
  nose=-.83+j*.23;top=.13*(j+1)
  rect('granite step '+str(j+1),-2.22,2.28,nose,3.07,top-.125,top-.021,'granite risers')
  rect('tread edge '+str(j+1),-2.22,2.28,nose-.012,3.07,top-.021,top,'granite treads')
 columns=[(x,0,'front column '+str(i+1))for i,x in enumerate(X)]
 columns.extend([(X[-1],y,'right return column '+str(i+1))for i,y in enumerate((.96,1.92,2.66))])
 for x,y,label in columns:
  profile=[(BASE,.156),(BASE+.026,.157),(SOFFIT-.021,.157),(SOFFIT,.157)]
  if lod:profile=[profile[0],profile[-1]]
  b.lathe((x,y),profile,'concrete columns',seg,label)
 rect('projecting flat canopy',-2.22,2.30,-.36,3.10,SOFFIT+.08,4.35,'warm plaster')
 rect('horizontal fascia drip',-2.23,2.31,-.374,3.10,SOFFIT+.047,SOFFIT+.083,'rain-darkened fascia')
 rect('canopy underside',-2.205,2.285,-.343,3.088,SOFFIT,SOFFIT+.047,'soffit')
 # Two front light openings and their visible repetitions under the rectangular slab.
 for k,(x,y)in enumerate([(-1.13,.19),(.70,.19),(.70,1.09),(.70,1.90)]):
  b.lathe((x,y),[(SOFFIT-.013,.076),(SOFFIT+.002,.076)],'soffit lights',seg,'downlight rim '+str(k+1))
  b.lathe((x,y),[(SOFFIT-.019,.053),(SOFFIT-.013,.053)],'light faces',seg,'downlight centre '+str(k+1))
 # Two paired glazed doors seen closed in the 2015 view. The fixed transom spans both.
 left=-2.08;right=.28;mid=(left+right)/2
 rect('entrance backing',-2.20,2.24,BACK+.04,BACK+.17,BASE,SOFFIT,'entrance shadow')
 rect('right shelter wall',1.91,2.20,BACK,3.05,BASE,SOFFIT,'warm plaster')
 for i,(lo,hi)in enumerate([(left,mid),(mid,right)]):
  prefix='leaf '+str(i+1)+' '
  rect(prefix+'lower panel',lo+.05,hi-.05,BACK-.026,BACK,BASE+.07,1.18,'lower door panels')
  rect(prefix+'glazing',lo+.05,hi-.05,BACK-.018,BACK+.021,1.24,2.52,'steel green glass')
  for k,x in enumerate((lo+.025,hi-.025)):
   rect(prefix+'jamb '+str(k+1),x-.025,x+.025,BACK-.070,BACK+.014,BASE,2.58,'pale door stiles')
  for k,z in enumerate((BASE+.034,1.21,2.55)):
   rect(prefix+'rail '+str(k+1),lo+.048,hi-.048,BACK-.066,BACK+.010,z-.032,z+.032,'pale door stiles')
  x=mid+(-.13 if i==0 else .13);yb=BACK-.10
  points=[(x,yb,1.36),(x,yb-.073,1.36),(x,yb-.073,1.73),(x,yb,1.73)]
  b.tube(points,.014,'pull hardware',6 if lod else 14,prefix+'bent pull')
 rect('upper fixed transom glass',left,right,BACK-.020,BACK+.015,2.58,3.49,'steel green glass')
 for i,x in enumerate((left+.026,left+.40,mid,right-.39,right-.026)):
  rect('transom stile '+str(i+1),x-.023,x+.023,BACK-.065,BACK+.01,2.58,3.53,'pale door stiles')
 for i,z in enumerate((2.61,2.90,3.50)):
  rect('transom rail '+str(i+1),left,right,BACK-.066,BACK+.01,z-.022,z+.022,'pale door stiles')
 for i,x in enumerate((-1.44,-.29,.90)):
  rect('front fascia vertical joint '+str(i+1),x-.003,x+.003,-.362,-.357,SOFFIT+.10,4.33,'rainwater seam')
