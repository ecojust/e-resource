"""Paired windows on successive storeys and their projecting brick pier, Pass Apartments."""
from pathlib import Path
from shapely.geometry import box
from PIL import Image
import numpy as np
ID='jingan-pass-apartments-brick-steel-bay'
BRICK='Brown running-bond brick';LINTEL='Darker soldier brick';JOINT='Mortar joint';STEEL='Rolled steel section';GLASS='Daylight glazing';SHADE='Glass in shade';SILL='Sloping brick sill';EDGE='Mullion edge'
PALETTE={m:dict(color=c,roughness=r)for m,c,r in [(BRICK,[1,1,1],.96),(LINTEL,[.337,.186,.114],.92),(JOINT,[.43,.36,.29],.95),(STEEL,[.133,.14,.137],.71),(GLASS,[.38,.444,.457],.38),(SHADE,[.26,.297,.306],.38),(SILL,[.364,.22,.144],.88),(EDGE,[.21,.21,.19],.77)]}
def texture():
 p=Path(__file__).with_name('brown-running-bond.png')
 if not p.exists():
  rng=np.random.default_rng(591);a=np.full((512,512,3),[128,109,82],dtype='f4')
  for row in range(32):
   for col in range(-1,9):
    y=row*16;x=col*64+(row%2)*32;l=max(0,x+1);r=min(512,x+64)
    if r>l:a[y+1:y+15,l:r]=[146,95,60]+rng.normal(0,7,(1,1,1))+rng.normal(0,3,(14,r-l,1))
  Image.fromarray(a.clip(0,255).astype('u1')).quantize(122).save(p)
 PALETTE[BRICK]['texture']=str(p)
def add_building(b,far=False):
 texture();face=lambda x,z,d:(x,-d,z)
 def rect(x0,x1,z0,z1,d0,d1,mat,name):b.prism(box(x0,z0,x1,z1),d0,d1,face,mat,name)
 wall=box(-1.67,0,1.60,5.90);width=1.142
 for s in (.47,3.39):wall=wall.difference(box(-width,s,width,s+1.66))
 b.prism(wall,-.42,0,face,BRICK,'Two storeys at the recesses of the steel windows')
 rect(1.60,2.25,0,5.90,-.46,.138,BRICK,'Wider adjoining brick pilaster standing forward of the windows')
 for s in (.47,3.39):
  rect(-width-.06,width+.06,s-.069,s+.018,0,.081,SILL,'Shallow projecting brick sill')
  rect(-width-.04,width+.04,s+1.664,s+1.865,.005,.032,JOINT,'Mortar behind individually laid soldiers')
  for i in range(27):
   l=-width+i*2*width/27
   rect(l+.004,l+2*width/27-.003,s+1.67,s+1.856,.023,.046,LINTEL,'Soldier brick above the flat opening')
  x0,x1=-1.056,1.056;z0,z1=s+.048,s+1.591
  rect(x0,x1,z0,z1,-.203,-.194,SHADE,'Continuous rear glazing plane')
  for i in range(4):
   for j in range(3):
    l=x0+(x1-x0)*i/4;r=x0+(x1-x0)*(i+1)/4;lo=z0+(z1-z0)*j/3;hi=z0+(z1-z0)*(j+1)/3
    rect(l+.021,r-.021,lo+.021,hi-.02,-.181,-.167,GLASS if (i+j)%3 else SHADE,'Rectangular window light')
  for x in np.linspace(x0,x1,5):
   rect(x-.022,x+.022,z0-.018,z1+.02,-.201,-.134,STEEL,'Vertical rolled steel bars')
   if not far:rect(x-.019,x-.014,z0,z1,-.134,-.129,EDGE,'Outer flange of the rolled steel bar')
  for z in np.linspace(z0,z1,4):rect(x0-.023,x1+.024,z-.016,z+.016,-.193,-.131,STEEL,'Horizontal steel transoms')
 for p in b.parts:
  if p['material']==BRICK:p['texcoords']=[[(x+.8*y+1.92)/4.39,z/5.95]for x,y,z in p['vertices']]
