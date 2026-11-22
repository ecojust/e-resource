"""Paint a repeating running bond and clay interlocking tile in metric UV space."""
from pathlib import Path
import math
import numpy as np
from PIL import Image, ImageDraw
from gongyi_frontage import COURSE, LIGHT, TILE

HERE=Path(__file__).resolve().parent
REPEAT={COURSE:(1.92,1.024),LIGHT:(1.92,.80),TILE:(1.60,1.44)}
def produce_textures():
 files={}
 for mid,(name,base,mortar) in enumerate(((COURSE,[158,103,82],[169,157,137]),(LIGHT,[203,180,155],[179,164,142]),(TILE,[148,86,67],[85,60,49]))):
  f=HERE/['gallery-running-bond.jpg','south-buff-face.jpg','south-clay-pantiles.jpg'][mid];files[name]=f
  if f.is_file():continue
  choice=np.random.default_rng(501+mid);width,height=384,256
  im=Image.new('RGB',(width,height),tuple(mortar));d=ImageDraw.Draw(im)
  if mid<2:
   cw,ch=48,16
   for r in range(16):
    for c in range(-1,9):
     x=c*cw+(r%2)*24;y=r*ch
     variation=int(choice.integers(-9,10))
     color=tuple(max(0,min(255,v+variation)) for v in base)
     d.rectangle((x+1,y+1,x+cw-1,y+ch-1),fill=color)
  else:
   x=np.arange(width)[None,:];y=np.arange(height)[:,None];rho=2*math.pi*(x/48+.05*np.sin(y*2*math.pi/64))
   wave=7*np.cos(rho)-9*np.cos(2*rho)-17*(np.mod(y+3*np.sin(rho),64)<3)
   im=Image.fromarray(np.uint8(np.clip(np.asarray(base)+wave[:,:,None],0,255)))
  pixels=np.asarray(im,dtype=float);grain=choice.normal(0,1.95,(height,width,1));Image.fromarray(np.uint8(np.clip(pixels+grain,0,255))).save(f,quality=87,subsampling=0)
 return files
def map_faces(builder):
 for p in builder.parts:
  if p['material'] not in REPEAT:continue
  arr=np.asarray(p['vertices']);new=[];uv=[];tris=[];lookup={}
  w,h=REPEAT[p['material']]
  for face in p['triangles']:
   a,b,c=arr[list(face)];norm=np.cross(b-a,c-a);norm/=np.linalg.norm(norm)
   horizontal=np.cross([0,0,1],norm)
   if np.linalg.norm(horizontal)<.00001:horizontal=np.array([1.,0.,0.])
   else:horizontal/=np.linalg.norm(horizontal)
   vertical=np.cross(norm,horizontal);basis=tuple(np.round(np.r_[horizontal,vertical],6));face_out=[]
   for vid in face:
    key=(basis,vid)
    if key not in lookup:
     lookup[key]=len(new);pos=arr[vid];new.append(pos.tolist());uv.append([float(pos@horizontal/w),float(-pos@vertical/h)])
    face_out.append(lookup[key])
   tris.append(tuple(face_out))
  p.update(vertices=new,texcoords=uv,triangles=tris)
