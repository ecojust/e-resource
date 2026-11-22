"""Editable entrance lintel and upper parts of its two red-brick piers."""
from pathlib import Path
import json,math
import numpy as np
from PIL import Image
from shapely.geometry import shape,box
from shapely.affinity import translate,scale
HERE=Path(__file__).resolve().parent
GOLD='Weathered gold lettering'; WHITE='White aggregate tablet'; LEDGE='Grey cement cornice'; SHADE='Recessed grey moulding'; JOINT='Pink grey mortar';SOFFIT='Light grey soffit';BRICKS=['Red-brown brick','Grey-red brick','Dark kiln brick','Rose-brown brick']
PALETTE={k:dict(color=v,roughness=.9)for k,v in [(JOINT,[.43,.29,.265]),(LEDGE,[.55,.56,.48]),(SHADE,[.33,.35,.30]),(SOFFIT,[.77,.74,.68]),(GOLD,[.78,.48,.055]),(WHITE,[.96,.96,.94]),*zip(BRICKS,[[.51,.265,.213],[.50,.315,.275],[.37,.210,.17],[.60,.34,.28]])]}
PALETTE[WHITE]['texture']=str(HERE/'aggregate.png');PALETTE[GOLD]['roughness']=.57
def tex():
 p=HERE/'aggregate.png'
 if p.exists():return
 gen=np.random.default_rng(1088);a=gen.normal(236,4.5,(192,240));a+=gen.choice([-14,0,9],a.shape,p=[.06,.86,.08]);rgb=np.stack([a,a+.6,a+1.8],axis=2);Image.fromarray(np.uint8(np.clip(rgb,0,255))).quantize(100).save(p)
def solid(b,x,y,z,width,depth,height,mat,label):
 b.box((x,y,z),(width,depth,height),mat,label=label)
def bricks(b,left,right,bottom,top,front,back,far,label):
 solid(b,(left+right)/2,(front+back)/2,(bottom+top)/2,right-left,back-front,top-bottom,JOINT,label+' joint bed')
 levels=round((top-bottom)/.082);h=(top-bottom)/levels
 for j in range(levels):
  start=left-(j%2)*.124;i=0
  while start<right:
   lo=max(left,start)+.004;hi=min(right,start+.248)-.004
   if hi>lo+.015:
    z=bottom+(j+.5)*h;mat=BRICKS[(2*i+3*j+round((left+6)*7))%4];y=front-.01-(i%3)*.001
    if far:solid(b,(hi+lo)/2,(y+back)/2,z,hi-lo,back-y,h-.009,mat,label+' bricks')
    else:
     bevel=min(.004,(hi-lo)/5);geom=box(lo,z-h/2+.0045,hi,z+h/2-.0045).buffer(-bevel,join_style=2).buffer(bevel,quad_segs=1)
     b.prism(geom,-back,-y,lambda x,z,d:(x,-d,z),mat,label+' bricks')
   start+=.248;i+=1
def profiles(b,x,width,cy,depth,z,far,label):
 # The lower course casts the dark narrow shadow seen immediately below the wide cap.
 for j,(extra,off,height,mat)in enumerate([(0,.018,.036,SHADE),(.035,.051,.032,LEDGE),(.075,.091,.048,LEDGE),(.115,.131,.035,LEDGE)]):
  solid(b,x,cy,z+off,width+extra,depth+extra,height,mat,label+' course '+str(j+1))
def letters():
 data=json.loads((HERE/'gilt-outlines.json').read_bytes());z0=1.13
 for ch,x in zip('园花业宏',[-1.04,-.35,.35,1.04]):
  poly=shape(data[ch]);l,b,r,t=poly.bounds;factor=.285/(t-b)
  g=translate(scale(poly,xfact=factor,yfact=factor,origin=(l,b)),xoff=x-(l+(r-l)*factor/2),yoff=z0-b)
  yield ch,g
def add_building(b,far=False):
 tex()
 for x,side in [(-1.95,'Left'),(1.95,'Right')]:
  bricks(b,x-.302,x+.302,0,.83,.015,.59,far,side+' pier')
  # Raised pairs of edge strips enclose the narrow recessed pier faces.
  for sign in (-1,1):bricks(b,x+sign*.225-.065,x+sign*.225+.065,.0,.83,-.058,.04,far,side+' recessed shaft edge')
  profiles(b,x,.67,.28,.66,.815,far,side+' lintel crossing')
  bricks(b,x-.315,x+.315,.96,1.65,.011,.60,far,side+' upper pier')
  for sign in (-1,1):bricks(b,x+sign*.237-.078,x+sign*.237+.078,.971,1.584,-.074,.035,far,side+' cap shoulder')
  bricks(b,x-.165,x+.165,1.50,1.65,-.074,.0,far,side+' upper recess lintel')
  profiles(b,x,.70,.27,.69,1.645,far,side+' cap')
  for sign in (-1,1):bricks(b,x+sign*.182-.098,x+sign*.182+.098,1.796,1.90,.035,.47,far,side+' crown blocks')
 solid(b,0,.265,1.196,3.37,.505,.639,SOFFIT,'Entrance lintel beam')
 profiles(b,0,3.38,.24,.61,.815,far,'Main lower lintel')
 bricks(b,-1.64,1.64,1.484,1.655,.01,.59,far,'Upper red brick lintel')
 profiles(b,0,3.37,.27,.60,1.647,far,'Lintel cornice')
 solid(b,0,-.016,1.237,3.28,.066,.487,WHITE,'White aggregate sign field')
 part=b.parts[-1];part['texcoords']=[[(v[0]+1.641)/3.283,(1.482-v[2])/.489] for v in part['vertices']]
 for ch,geom in letters():
  for poly in getattr(geom,'geoms',[geom]):
   p=poly.simplify(.0015 if far else .00022,preserve_topology=True)
   b.prism(p,.05,.066,lambda x,z,d:(x,-d,z),GOLD,'Gilt character '+ch)
