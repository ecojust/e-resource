"""Left-hand pediment measured in Fayhoo's May 2017 photograph of 450 Fengyang Road."""
from math import sin,cos,pi
from pathlib import Path
import numpy as np
from PIL import Image
from shapely.geometry import Polygon,box
ID='huangpu-fengyang-450-garland-pediment'
FIELD='Weathered ivory plaster';RIM='Cream moulding';RIB='Carved yellow-grey plaster'
INSIDE='Recessed dark beige stone';SHADOW='Weathered groove';RELIEF='Raised festoon and ribbon'
PALETTE={m:dict(color=col,roughness=rough) for m,col,rough in [
 (FIELD,[1,1,1],.94),(RIM,[.78,.739,.628],.88),(RIB,[.605,.578,.470],.94),
 (INSIDE,[.547,.533,.458],.97),(SHADOW,[.405,.398,.317],.95),(RELIEF,[.703,.672,.553],.92)]}
# All source coordinates refer to the 463 x 421 crop named in the reference note.
# Vertical is measured up from the underside of the lowest ledge included here.
def local(x,v,d=0):return (x-234)*.016,-d,(207-v)*.016
def mapping(x,z,d):return (x,-d,z)
def texture():
 p=Path(__file__).with_name('stucco.png')
 if not p.exists():
  rng=np.random.default_rng(579)
  patches=Image.fromarray(rng.integers(0,255,(53,66),dtype='u1')).resize((479,465),Image.Resampling.BICUBIC)
  mottling=(np.asarray(patches,float)-124)*.066+rng.normal(0,1.95,(465,479))
  Image.fromarray(np.clip([181,175,152]+mottling[:,:,None],0,255).astype('u1')).quantize(127).save(p)
 PALETTE[FIELD]['texture']=str(p)
def arc_points(mid_x,mid_y,rx,ry,start,end,count):
 return [(mid_x+rx*cos(t),mid_y+ry*sin(t)) for t in np.linspace(start,end,count)]
def add_building(b,far=False):
 texture()
 def slab(points,rear,front,material,label):
  b.prism(Polygon([(local(x,v)[0],local(x,v)[2])for x,v in points]),rear,front,mapping,material,label)
 def panel(l,t,r,bt,rear,front,material,label):
  slab([(l,t),(r,t),(r,bt),(l,bt)],rear,front,material,label)
 def line(points,d,r,mat,label):
  b.tube([local(x,y,d)for x,y in points],r,mat,sides=7 if far else 12,label=label)
 def xycurve(control,count):
  p=np.asarray(control);return [tuple((1-t)**3*p[0]+3*t*(1-t)**2*p[1]+3*t*t*(1-t)*p[2]+t**3*p[3]) for t in np.linspace(0,1,count)]
 def disc(x,y,rx,ry,depth,mat,label):
  slab(arc_points(x,y,rx,ry,0,2*pi,18 if far else 40)[:-1],depth-.033,depth,mat,label)
 steps=17 if far else 43
 # Horizontal perspective in the crop is removed with a shared linear vertical correction.
 crown=arc_points(238,79,83,68,pi,2*pi,steps)
 outline=[(44,177),(96,143),(141,116),(153,87)]+crown+[(325,93),(342,116),(402,158),(420,165),(420,206),(44,206)]
 slab(outline,-.35,.00,FIELD,'Continuous parapet, with both descending shoulders')
 # The dark inset and crown mouldings have their own physical depths.
 tympanum=arc_points(238,77,72,56,pi,2*pi,steps)
 slab(tympanum,-.008,.026,INSIDE,'Recess in semicircular crown')
 line(crown,.067,.051,RIM,'Crowning roll across full semicircle')
 line(arc_points(238,78,77.5,63,pi,2*pi,steps),.051,.024,RIB,'Second band following crown')
 panel(145,77,330,84,-.012,.141,RIM,'Base ledge under curved hood')
 panel(142,72,332,77,-.012,.177,RIM,'Projecting cap below tympanum')
 for side in (-1,1):
  def mir(points):return [(238+side*x,y)for x,y in points]
  slab(mir([(51,194),(55,94),(78,93),(80,195)]),-.015,.085,RIB,'Pier flanking relief field')
  for x in (58,68,77):
   line(mir([(x,96),(x-1,190)]),.084,.02,RIM,'Vertical bead on side pier')
  panel_x=238+side*69
  panel(panel_x-15,80,panel_x+14,92,-.01,.105,RIM,'Cornice over fluted pier')
  spiral=[(104+(2+9*t)*cos(.75*pi+1.85*pi*t),112+(2+9*t)*sin(.75*pi+1.85*pi*t))for t in np.linspace(0,1,14 if far else 35)]
  line(mir(spiral),.084,.041,RIB,'Volute at foot of upper hood')
  line(mir(xycurve([(95,114),(117,126),(124,145),(174,160)],15 if far else 33)),.050,.044,RIM,'Rolling sloped shoulder')
  # Smaller double scrolls and leaf terminals beside the central oval.
  crown_scroll=[(25+(2+7*t)*cos(-.20*pi+1.8*pi*t),60+(2+7*t)*sin(-.20*pi+1.8*pi*t))for t in np.linspace(0,1,12 if far else 26)]
  line(mir(crown_scroll),.084,.023,RELIEF,'Incurved leaf beside cartouche')
  line(mir(xycurve([(20,65),(25,74),(40,68),(51,62)],13 if far else 27)),.075,.026,RELIEF,'Sweeping lower crown leaf')
  line(mir(xycurve([(47,61),(44,49),(39,52),(39,57)],9 if far else 17)),.080,.022,RELIEF,'Reverse leaf terminal')
  # The two tie knots are visible in the original, the individual petals are approximated.
  x=238+side*29
  disc(x,113,4.8,6,.171,RELIEF,'Raised tie-knot')
  for points in [[(29,114),(39,91),(55,106),(32,117)],[(29,113),(16,98),(16,112),(27,119)],[(32,117),(42,125),(42,137),(50,128)]]:
   line(mir(xycurve(points,12 if far else 20)),.151,.034,RELIEF,'Bent ribbon at suspension')
 for height,depth,rad in [(145,.113,.079),(181,.131,.061)]:
  band=xycurve([(209,117),(213,height),(257,height),(267,117)],25 if far else 55)
  line(band,depth,rad,RELIEF,'Hanging carved festoon')
  for i in range(4,len(band)-4,4 if far else 5):
   x,y=band[i]
   line([(x-1.9,y-1.6),(x+1.9,y+2.2)],depth+rad*.85,.015,RIB,'Narrow leaf ribbing on festoon')
 disc(247,53,11.5,16,.096,RELIEF,'Oval shield')
 line(arc_points(247,53,13.7,18,0,2*pi,steps),.102,.032,RIM,'Ring framing the oval shield')
 panel(157,191,318,199,-.008,.118,RIM,'Long tread below festoon panel')
 panel(150,199,323,205,-.008,.173,RIM,'Projecting lower sill edge')
 for part in b.parts:
  if part['material']==FIELD:part['texcoords']=[[(x+3.1)/6.1,z/3.45]for x,y,z in part['vertices']]
