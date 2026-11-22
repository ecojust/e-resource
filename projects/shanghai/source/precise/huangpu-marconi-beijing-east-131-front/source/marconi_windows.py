"""Visible upper casements and paired low windows on the frontage at 131 Beijing East Road."""
from pathlib import Path
import json
import math
import numpy as np
from scipy.optimize import minimize_scalar
from shapely.geometry import Polygon,box as rectangle
from marconi_photo_plane import on_wall,pixel
BASE=Path(__file__).resolve().parents[1]
MEASURED=json.loads((BASE/'measurements/marconi-window-pixels.json').read_text())
TIMBER='Marconi | weathered casement timber'
FIXED='Marconi | dark fixed timber casing'
BEAD='Marconi | narrow timber putty bead'
GLASS='Marconi | muted street reflection'
IRON='Marconi | existing dark steel window bars'
LIGHT='Marconi | off-white sill stone'
SOFFIT='Marconi | shaded brick behind the segmental head'
DARK='Marconi | deep shade behind open leaves'
def colour(v,r,m=0):
 c=np.array(v)/255
 return dict(color=np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4).tolist(),roughness=r,metallic=m)
PALETTE={TIMBER:colour((91,75,71),.77),FIXED:colour((77,69,68),.79),BEAD:colour((110,95,87),.77),GLASS:colour((100,112,115),.28,.26),IRON:colour((72,67,66),.65,.25),LIGHT:colour((177,171,154),.89),SOFFIT:colour((66,61,56),.95),DARK:colour((38,41,44),.97)}
def strip(data,depth):
 return np.array([on_wall(*uv,depth)[::2] for uv in data])
def openings():
 rows=[]
 for witness in MEASURED['openings']:
  curve=strip(witness['curve_px'],witness['aperture_y']);sill=strip(witness['base_px'],witness['aperture_y'])
  left=float(sill[0,0]);right=float(sill[1,0]);bottom=float(sill[:,1].mean())
  # The top and bottom of each jamb are different pixel columns in the upward view.
  left=float((left+curve[0,0])/2);right=float((right+curve[-1,0])/2)
  knots=np.polyfit(curve[:,0],curve[:,1],2)
  xx=np.linspace(left,right,29);heads=np.polyval(knots,xx);outline=[[left,bottom],[right,bottom],*np.column_stack([xx,heads])[::-1].tolist()]
  rows.append(dict(key=witness['id'],id=witness['id'],left=left,right=right,bottom=bottom,top=float(max(heads)),outline_xz=outline,polygon=outline,front_y=witness['aperture_y'],frame_y=witness['inner_frame_y']))
 return rows
def fixed_extent(witness):
 uv=strip(witness['frame_corners_px'],witness['inner_frame_y'])
 return (float(uv[[0,3],0].mean()),float(uv[[1,2],0].mean()),float(uv[[2,3],1].mean()),float(uv[[0,1],1].mean()))
def leaf_frame(witness,index):
 l,r,b,t=fixed_extent(witness);width=(r-l-.10)/4
 hinge_x=l+.05 if index==0 else l+.05+2*width
 sign=1. if index==0 else -1.; target=witness['free_tops_px'][index]
 def direction(a):return np.array([sign*math.cos(a),-math.sin(a),0.])
 hinge=np.array([hinge_x,witness['inner_frame_y']-.053,0.])
 def loss(a):return np.linalg.norm(np.array(pixel(hinge+width*direction(a)+[0,0,t-.045]))-target)
 angle=minimize_scalar(loss,bounds=(.12,math.pi-.06),method='bounded').x
 d=direction(angle)
 return hinge,d,np.array([-d[1],d[0],0]),float(width),float(angle),float(loss(angle))
def add_windows(builder,lod=False):
 low=lod in (True,'lod');up=np.array([0.,0.,1.])
 for w,row in zip(MEASURED['openings'],openings()):
  key=row['key'];front=row['front_y'];fy=row['frame_y'];l,r,b,t=fixed_extent(w)
  def box(x0,x1,y0,y1,z0,z1,m,label):
   builder.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),m,label=key+' | '+label)
  def slab(shape,y0,y1,m,label):
   builder.prism(shape,-y1,-y0,lambda x,z,d:(x,-d,z),m,key+' | '+label)
  aperture=Polygon(row['outline_xz'])
  frame_rect=rectangle(l,b,r,t)
  # A shaded masonry return at the rear of the real aperture surrounds the inset rectangle.
  slab(aperture.difference(frame_rect),fy+.035,fy+.115,SOFFIT,'rear arched spandrel and jamb returns')
  box(row['left']-.018,row['right']+.018,front-.085,fy+.055,row['bottom']-.044,row['bottom']+.003,LIGHT,'sill stone')
  for s0,s1 in ((l,l+.04),(r-.04,r)):box(s0,s1,fy-.014,fy+.054,b,t,FIXED,'fixed jamb')
  for z0,z1 in ((b,b+.034),(t-.047,t)):box(l+.04,r-.04,fy-.014,fy+.054,z0,z1,FIXED,'fixed head or sill')
  if key=='upper':
   width=(r-l-.10)/4
   for ix in range(4):
    if ix<2:hinge,d,n,_,_,_=leaf_frame(w,ix)
    else:hinge=np.array([l+.05+ix*width,fy-.053,0.]);d=np.array([1.,0.,0.]);n=np.array([0.,1.,0.])
    tag=f'leaf {ix+1} | '
    def leaf_box(a,c,y0,y1,z0,z1,m,label):
     origin=hinge+d*((a+c)/2)+n*((y0+y1)/2)+up*((z0+z1)/2)
     builder.box(origin,(c-a,y1-y0,z1-z0),m,basis=[d,n,up],label=key+' | '+tag+label)
    z0,z1=b+.028,t-.046
    for a,c in ((0,.033),(width-.033,width)):leaf_box(a,c,-.018,.020,z0,z1,TIMBER,'stile')
    for a,c in ((z0,z0+.04),(z1-.046,z1)):leaf_box(.033,width-.033,-.018,.020,a,c,TIMBER,'head or bottom rail')
    a=z0+.04;c=z1-.046
    for k in (1,2):
     z=a+(c-a)*k/3;leaf_box(.033,width-.033,-.012,.013,z-.008,z+.008,TIMBER,'horizontal glazing bar')
    for k in range(3):
     za=a+(c-a)*k/3+(0 if k==0 else .008);zb=a+(c-a)*(k+1)/3-(0 if k==2 else .008)
     if ix==3 and k in (0,2):
      if k==0:leaf_box(.033,width-.033,.017,.022,za+(zb-za)*.60,zb,GLASS,'remaining pane above dark lower gap')
      else:leaf_box(.033,width-.033,.017,.022,za,zb-(zb-za)*.25,GLASS,'remaining pane below dark upper gap')
     else:leaf_box(.033,width-.033,-.002,.002,za,zb,GLASS,'glazed pane')
     if not low:
      for a0,a1 in ((.033,.039),(width-.039,width-.033)):leaf_box(a0,a1,-.007,-.002,za,zb,BEAD,'moulded glazing bead')
   for f in (.12,.24):box(l+.045,r-.045,fy+.084,fy+.110,b+(t-b)*f-.012,b+(t-b)*f+.012,IRON,'guard rail behind opened eastern pair')
   # The inclined street views see the top and side of the dark recess behind the open sashes.
   # The back and reveals meet without an external cap across the open part.
   recess_front,recess_back=fy+.055,fy+1.08
   box(l-.014,r+.014,recess_back,recess_back+.014,b-.014,t+.014,DARK,'recess rear panel')
   for a,c in ((l-.014,l),(r,r+.014)):
    box(a,c,recess_front,recess_back,b-.014,t+.014,DARK,'recess side reveal')
   for a,c in ((b-.014,b),(t,t+.014)):
    box(l,r,recess_front,recess_back,a,c,DARK,'recess head or underside')
  else:
   grid=w['grid_px'];xmin,xmax,head,foot=grid['outer']
   coords=[on_wall(x, (head+foot)/2,fy) for x in [xmin,*grid['vertical'],xmax]]
   zs=[on_wall((xmin+xmax)/2,y,fy)[2] for y in [foot,grid['horizontal'][1],grid['horizontal'][0],head]]
   xs=[p[0] for p in coords]
   box(l+.041,r-.041,fy+.020,fy+.035,b+.033,t-.046,TIMBER,'broad timber panel behind the glazing grid')
   for i,(x0,x1) in enumerate(zip(xs,xs[1:])):
    for k,(z0,z1) in enumerate(zip(zs,zs[1:])):
     box(x0+.005,x1-.005,fy-.005,fy,z0+.005,z1-.005,GLASS,'glazing cell')
     if not low:
      box(x0+.005,x1-.005,fy-.010,fy-.005,z0+.005,z0+.011,BEAD,'bottom glazing bead')
   for x in xs:box(x-.006,x+.006,fy-.021,fy-.002,zs[0]-.006,zs[-1]+.006,IRON,'vertical glazing strip')
   for z in zs:
    for x0,x1 in zip(xs,xs[1:]):box(x0+.006,x1-.006,fy-.021,fy-.002,z-.006,z+.006,IRON,'horizontal glazing strip')
