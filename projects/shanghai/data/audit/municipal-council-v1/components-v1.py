"""Original Municipal Council facade components. MIT.

The source photographs guide construction types and rhythm. All dimensions
passed to these helpers are author estimates; no image pixels are embedded.
"""
import math
import numpy as np
from shapely.geometry import Polygon,box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from common.photo_architecture import opening

PALETTE={
 'warm limestone':{'color':[.61,.565,.465],'roughness':.86},
 'cut limestone':{'color':[.70,.66,.56],'roughness':.79},
 'recessed mortar':{'color':[.49,.465,.405],'roughness':.91},
 'courtyard plaster':{'color':[.78,.76,.67],'roughness':.91},
 'recessed glass':{'color':[.105,.165,.18],'roughness':.27,'metallic':.16},
 'dark window frame':{'color':[.13,.155,.145],'roughness':.63},
 'stone base':{'color':[.45,.435,.38],'roughness':.86},
 'roof closure estimate':{'color':[.25,.27,.25],'roughness':.93},
 'wrought iron':{'color':[.12,.14,.13],'roughness':.60,'metallic':.25},
 'unverified join closure':{'color':[.66,.64,.57],'roughness':.9},
}


def miter_mapper(f,previous,following,reference=.42):
 n=f.n[:2];t=f.t[:2]
 def inset(point,other):
  axes=np.array([n,other])
  return point-n*reference if abs(np.linalg.det(axes))<1e-10 else np.linalg.solve(axes,[n@point-reference,other@point-reference])
 left=(inset(f.a[:2],previous.n[:2])-f.a[:2])@t/reference
 right=(inset(f.b[:2],following.n[:2])-f.b[:2])@t/reference
 return lambda u,z,d:f.point(u-d*(left+(u+f.length/2)/f.length*(right-left)),z,d)


def opened_wall(f,previous,following,bottom,top,holes,*,rusticated=False,
                material='warm limestone',course=.64,label='wall'):
 surface=box(-f.length/2,bottom,f.length/2,top)
 apertures=unary_union(holes) if holes else Polygon()
 surface=surface.difference(apertures)
 mapper=miter_mapper(f,previous,following)
 f.builder.prism(surface,-.42,-.035 if rusticated else 0.,mapper,
                 'recessed mortar' if rusticated else material,f.label+'/'+label+'-opened-closed-solid')
 if rusticated:
  # Each stone course has genuine shallow horizontal joints. The structural
  # backing is opened too, so no plaster/stone sheet blocks the windows.
  start=math.floor(bottom/course)*course
  for row,z in enumerate(np.arange(start,top,course)):
   low=max(bottom,z+.018);high=min(top,z+course-.018)
   if high-low<=.015:continue
   band=box(-f.length/2,low,f.length/2,high).difference(apertures)
   f.builder.prism(band,-.025,.025,mapper,material,f.label+f'/{label}-rusticated-course-{row}')


def window(f,shape,lod,label,*,columns=3,rows=4,depth=.32,
           surround=True,arch=False,frame='dark window frame'):
 inner=shape.buffer(-.066,join_style=2)
 f.prism(inner,-depth-.027,-depth,'recessed glass',label+'-recessed-glass')
 x0,z0,x1,z1=shape.bounds;bars=[]
 if not lod:
  for i in range(1,columns):
   u=x0+(x1-x0)*i/columns;bars.append(box(u-.023,z0,u+.023,z1))
  for i in range(1,rows):
   z=z0+(z1-z0)*i/rows;bars.append(box(x0,z-.023,x1,z+.023))
 panes=inner.difference(unary_union(bars)) if bars else inner
 f.prism(shape.buffer(-.018,join_style=2).difference(panes),-depth+.04,-depth+.12,frame,label+'-real-frame')
 if surround:
  f.prism(shape.buffer(.145,join_style=2).difference(shape),-.018,.10,'cut limestone',label+'-stone-surround')
  f.box((x0+x1)/2,z0-.075,x1-x0+.33,.15,.37,.055,'cut limestone',label+'-projecting-sill')
  if arch:
   middle=(x0+x1)/2
   key=Polygon([(middle-.13,z1-.04),(middle+.13,z1-.04),(middle+.21,z1+.32),(middle-.21,z1+.32)])
   f.prism(key,.09,.22,'cut limestone',label+'-arch-keystone')


def cornice(f,z,lod,*,dentils=True,project=.72,label='strong-cornice'):
 for dz,h,depth in [(-.35,.19,.20),(-.15,.14,.37),(.04,.18,project),(.20,.11,project+.12)]:
  f.box(0,z+dz,f.length-.035,h,depth+.25,(depth-.25)/2,'cut limestone',label+'-layer')
 if dentils:
  pitch=.64 if not lod else 1.28
  for u in np.arange(-f.length/2+.27,f.length/2-.15,pitch):
   f.box(float(u),z-.19,.29 if not lod else .42,.24,.37,.27,'cut limestone',label+'-dentil')


def column(builder,xy,bottom,top,radius,lod,label,*,ionic=False):
 height=top-bottom
 profile=[(bottom,radius*1.37),(bottom+.12,radius*1.37),(bottom+.19,radius*1.16),
          (bottom+.30,radius*1.10),(bottom+.38,radius),
          (top-.39,radius*.91),(top-.28,radius*1.02),(top-.20,radius*1.22),
          (top-.08,radius*1.32),(top,radius*1.32)]
 assert height>1.0
 builder.lathe(xy,profile,'cut limestone',segments=16 if lod else 28,label=label+'-shaft-base-capital')
 builder.box((*xy,top+.045),(radius*2.85,radius*2.85,.09),'cut limestone',label=label+'-abacus')
 if ionic:
  # Original simplified solid scroll caps; they are geometric approximations
  # of the photographed Ionic order, not measured carved reproductions.
  for sign in [-1,1]:
   center=np.array([xy[0]+sign*radius*.96,xy[1],top-.13])
   start=len(builder.parts)
   builder.lathe((0.,0.),[(-radius*.27,radius*.37),(radius*.27,radius*.37)],
                 'cut limestone',segments=12 if lod else 24,label=label+'-ionic-scroll')
   for part in builder.parts[start:]:
    part['vertices']=[(center+np.array([v[0],v[2],-v[1]])).tolist() for v in part['vertices']]


def squared_pier(f,u,bottom,top,width,depth,lod,label):
 f.box(u,(bottom+top)/2,width,top-bottom,depth,depth/2-.10,'warm limestone',label+'-core')
 if not lod:
  for z in np.arange(bottom+.15,top-.08,.57):
   f.box(u,float(z),width+.045,.034,depth+.055,depth/2-.10,'recessed mortar',label+'-horizontal-joint')
 f.box(u,top+.08,width+.30,.16,depth+.28,depth/2-.10,'cut limestone',label+'-pier-cap')


def plain_door(f,u,bottom,width,height,lod,label,depth=.70,arch=0.):
 shape=opening(u,bottom,width,height,arch=arch,segments=20 if not lod else 12)
 window(f,shape,lod,label,columns=2,rows=4,depth=depth,surround=True,arch=bool(arch))
 return shape
