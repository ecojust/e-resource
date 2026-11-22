"""Stepped round-headed windows with spiral colonnettes on the Chen garden house."""
from pathlib import Path
from math import pi,sin,cos
import numpy as np
from PIL import Image
from shapely.geometry import Point,LineString,Polygon,box
from shapely.ops import unary_union

HERE=Path(__file__).resolve().parent
ID='changning-chen-garden-house-stepped-arched-windows'
PLASTER='Warm ochre roughcast';TRIM='Warm pale window surround';REVEAL='Ochre reveals in shade';GREY='Pale painted steel frame';CAME='Light painted glazing bars';GLASS='Recessed dark glass';FAN='Shadowed fanlight glass';WEATHER='Pale carved spiral shaft';RIDGE='Illuminated spiral ribs';CAP='Carved capital and base';CAP_HI='Pale moulding edges';SILL='Projecting stone sills'
PALETTE={n:dict(color=c,roughness=r) for n,c,r in [(PLASTER,[1,1,1],.96),(TRIM,[.68,.506,.32],.91),(REVEAL,[.44,.326,.212],.95),(GREY,[.62,.575,.454],.79),(CAME,[.48,.467,.376],.76),(GLASS,[.187,.202,.164],.3),(FAN,[.162,.169,.139],.36),(WEATHER,[.72,.628,.463],.93),(RIDGE,[.80,.688,.521],.9),(CAP,[.68,.566,.405],.94),(CAP_HI,[.82,.71,.526],.91),(SILL,[.623,.525,.377],.91)]}
CENTERS=(-.92,0,.92);LEVELS=(.26,.88,1.51)
R=.317;SPRING=1.846;TURNS=2.4
def texture():
 f=HERE/'ochre-roughcast.png'
 if not f.exists():
  rng=np.random.default_rng(479);yy,xx=np.mgrid[:240,:280]
  cloud=np.asarray(Image.fromarray(rng.integers(0,255,(28,33),dtype=np.uint8)).resize((280,240),Image.Resampling.BICUBIC))/255
  value=23*(cloud-.5)+rng.normal(0,11,xx.shape)
  dim=rng.random(xx.shape)<.13;value[dim]-=rng.uniform(5,30,(dim.sum(),))
  rgb=np.array([222,194,150])[None,None,:]+value[:,:,None];Image.fromarray(np.uint8(np.clip(rgb,0,255))).quantize(108).save(f)
 PALETTE[PLASTER]['texture']=str(f)
def face(b,p,a,c,mat,label):
 b.prism(p,-c,-a,lambda x,z,d:(x,-d,z),mat,label)
 if mat==PLASTER:
  t=b.parts[-1];t['texcoords']=[[.05+.30*(x+1.44+.25*y),.055+.218*(3.998-z)]for x,y,z in t['vertices']]
def rect(b,l,r,low,top,a,c,mat,label):face(b,box(l,low,r,top),a,c,mat,label)
def arch(cx,bottom,sp,r,segments):
 pts=[(cx-r,bottom),(cx+r,bottom),(cx+r,sp)]
 pts.extend([(cx+r*cos(k*pi/segments),sp+r*sin(k*pi/segments)) for k in range(1,segments+1)])
 return Polygon(pts)
def band(b,points,width,y0,y1,mat,label):
 face(b,LineString(points).buffer(width/2,cap_style=2,join_style=2),y0,y1,mat,label)
def lathe(b,x,y,profile,seg,mat,label):
 vertices=[];faces=[]
 for z,r in profile:vertices.extend((x+r*cos(t*2*pi/seg),y+r*sin(t*2*pi/seg),z) for t in range(seg))
 for j in range(len(profile)-1):
  for k in range(seg):faces.append((j*seg+k,j*seg+(k+1)%seg,(j+1)*seg+(k+1)%seg,(j+1)*seg+k))
 faces.extend([list(reversed(range(seg))),list(range(len(vertices)-seg,len(vertices)))]);b.add(vertices,faces,mat,label)
def pillar(b,x,z0,z1,far):
 y=-.054;seg=12 if far else 24
 rect(b,x-.129,x+.129,z0-.082,z0-.039,-.153,.093,CAP,'Square colonnette plinth')
 lathe(b,x,y,[(z0-.039,.121),(z0-.018,.128),(z0+.006,.117),(z0+.035,.082),(z0+.061,.073)],seg,CAP_HI,'Round plinth moulding')
 bottom=z0+.054;top=z1-.111
 # Carve a double-start rope section into the stone, including the shadow in each groove.
 steps=53 if far else 83
 for side in (0,1):
  for start,stop,mat in [(-pi/2,-.52,WEATHER),(-.52,.52,RIDGE),(.52,pi/2,WEATHER)]:
   across=3 if far else 5;vertices=[];faces=[]
   for n in range(steps+1):
    u=n/steps;phase=pi/2+u*2*pi*TURNS+pi*side
    for offset in np.linspace(start,stop,across+1):
     radius=.064-.003*u+.0125*cos(2*offset)
     vertices.append((x+radius*cos(phase+offset),y+radius*sin(phase+offset),bottom+u*(top-bottom)))
   for n in range(steps):
    for k in range(across):
     a=n*(across+1)+k;faces.append([a,a+1,a+across+2,a+across+1])
   b.add(vertices,faces,mat,'Double-helical carved shaft')
 lathe(b,x,y,[(top-.017,.066),(top+.007,.078),(top+.025,.076),(z1-.049,.097),(z1-.034,.122),(z1-.009,.119)],seg,CAP,'Flared colonnette capital')
 for k in range(6):
  a=k*pi/3;axis=[(x+.074*cos(a),y+.074*sin(a),top+.013),(x+.100*cos(a),y+.100*sin(a),z1-.058),(x+.109*cos(a),y+.109*sin(a),z1-.048)]
  b.tube(axis,.011,CAP_HI,5 if far else 8,'Capital raised tips')
 rect(b,x-.125,x+.125,z1-.011,z1+.027,-.158,.090,CAP_HI,'Abacus edge')
def window(b,cx,bot,far):
 seg=16 if far else 36; sp=bot+SPRING
 outer=arch(cx,bot-.028,sp,R+.039,seg);inner=arch(cx,bot,sp,R,seg)
 face(b,outer.difference(inner),-.031,.03,TRIM,'Shallow arch surround')
 face(b,inner.difference(arch(cx,bot+.008,sp,R-.012,seg)),.003,.164,REVEAL,'Window reveal and soffit')
 rect(b,cx-R-.027,cx+R+.027,bot-.059,bot-.005,-.090,.063,SILL,'Stepped projecting sill')
 glass=arch(cx,bot+.025,sp,R-.018,seg);face(b,glass,.175,.200,GLASS,'Two-leaf window glazing')
 inset=R-.032
 fan=Point(cx,sp).buffer(inset,resolution=seg//2).intersection(box(cx-R,sp,cx+R,sp+R))
 face(b,fan,.150,.173,FAN,'Semicircular fanlight glass')
 # The arch's main horizontal member is broader than the three lower glazing bars.
 rect(b,cx-R,cx+R,sp-.027,sp+.029,.097,.176,GREY,'Transom below fanlight')
 rect(b,cx-R,cx+R,bot+.009,bot+.043,.105,.172,GREY,'Lower frame rail')
 for x in [cx-inset,cx+inset]:rect(b,x-.017,x+.017,bot+.024,sp+.006,.104,.174,GREY,'Outer window jamb')
 band(b,[(cx+inset*cos(t),sp+inset*sin(t))for t in np.linspace(0,pi,seg+1)],.025,.107,.168,GREY,'Curved fanlight rim')
 rect(b,cx-.010,cx+.010,bot+.032,sp-.018,.112,.177,CAME,'Centre steel glazing bar')
 for step in [.25,.50,.75]:
  z=bot+.040+(SPRING-.069)*step;rect(b,cx-inset,cx+inset,z-.009,z+.009,.111,.176,CAME,'Horizontal glazing bar')
 for t in [pi*.315,pi*.685]:
  band(b,[(cx,sp+.010),(cx+(inset-.012)*cos(t),sp+(inset-.012)*sin(t))],.012,.112,.161,CAME,'Fanlight radial divisions')
def add_building(b,far=False):
 texture();seg=16 if far else 36
 limits=(-1.44,1.44)
 wall=box(*[limits[0],0,limits[1],3.998]);holes=[arch(cx,z-.005,z+SPRING,R+.005,seg) for cx,z in zip(CENTERS,LEVELS)]
 face(b,wall.difference(unary_union(holes)),0,.22,PLASTER,'Roughcast wall with three stepped arched openings')
 for cx,base in zip(CENTERS,LEVELS):window(b,cx,base,far)
 for ix in (0,1):
  # Each short shaft belongs to the two adjacent window levels.
  pillar(b,(CENTERS[ix]+CENTERS[ix+1])/2,LEVELS[ix+1]-.027,LEVELS[ix]+SPRING+.017,far)
