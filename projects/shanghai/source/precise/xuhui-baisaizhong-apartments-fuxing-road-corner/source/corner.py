"""Boissezon Apartments: the cut corner, four recessed balconies and the paired street entrance."""
from pathlib import Path
import json
import numpy as np
from shapely.geometry import Polygon, box

HERE=Path(__file__).resolve().parent
STUDY=json.loads((HERE.parent/'measurements/corner-camera-and-levels.json').read_text())
CREAM='Corner | ivory cement render'
SHADOW='Corner | sheltered warm plaster'
STONE='Corner | fine grey cast stone'
BAND='Corner | pale coping'
SHOE='Corner | charcoal plinth'
FRAME='Corner | painted dark frames'
GLASS='Corner | recessed grey-green glazing'
IRON='Corner | dark metal'
WOOD='Corner | dark timber handrail'

def finish(rgb,roughness):
    return {'color':[v/255 for v in rgb],'roughness':roughness}

PALETTE={CREAM:finish((211,204,182),.89),SHADOW:finish((180,170,145),.96),
         STONE:finish((163,160,148),.83),BAND:finish((221,215,195),.78),
         SHOE:finish((77,75,69),.94),FRAME:finish((62,66,61),.63),
         GLASS:finish((74,88,86),.38),IRON:finish((54,59,55),.61),WOOD:finish((91,66,48),.64)}

def envelope(layout=None):
    override=(layout or {}).get('corner',{})
    width=override.get('width',8.25)
    underside=override.get('balcony_undersides',STUDY['balcony_undersides_m'])
    scale=width/STUDY['front_width_m']
    return {'width':width,'half_bay':override.get('balcony_halfwidth',STUDY['balcony_halfwidth_m']*scale),
            'lower':underside,'height_to_coping':override.get('height_to_coping',STUDY['overall_underside_to_coping_m']),
            'soffit':override.get('terrace_soffit',16.4),'depth':override.get('balcony_depth',1.52*scale),
            'entrance_depth':.87*scale,'slab_thickness':.16,'front_balcony_y':-.13*scale}

def cuboid(b,x0,x1,y0,y1,z0,z1,material,label):
    if min(x1-x0,y1-y0,z1-z0)<=0:return
    b.box([(x0+x1)/2,(y0+y1)/2,(z0+z1)/2],[x1-x0,y1-y0,z1-z0],material,label='740 | '+label)

def xz(b,points,y,thick,material,label):
    b.prism(Polygon(points),-y-thick,-y,lambda x,z,d:(x,-d,z),material,'740 | '+label)

def line_wall(b,a,c,low,high,depth,material,label):
    a=np.asarray(a);c=np.asarray(c);diff=c-a;length=np.linalg.norm(diff);u=diff/length
    n=np.array([u[1],-u[0]])
    b.box([*(.5*(a+c)),.5*(low+high)],[length,depth,high-low],material,
          basis=[[u[0],u[1],0],[n[0],n[1],0],[0,0,1]],label='740 | '+label)

def entrance(b,lod,g):
    half=g['width']/2
    scale=g['width']/8.25
    inside=g['entrance_depth'];floor=g['lower'][0]
    # The plan records the rake of the stepped reveal on each side of the doorway.
    # Each block has a different front edge. The return continues behind its neighbour.
    clear=1.37*scale;outer=2.58*scale
    off=[0,.17,.33,.51,.72,.87]
    for sg,side in [(-1,'left'),(1,'right')]:
        for i in range(5):
            x0=outer-(outer-clear)*i/5
            x1=outer-(outer-clear)*(i+1)/5
            lo,hi=sorted([sg*x0,sg*x1]);y=off[i]*scale
            cuboid(b,lo,hi,y,inside+.24,0,floor,CREAM,f'{side} door reveal {i+1}')
            cuboid(b,lo,hi,y-.018,y+.052,0,.29,SHOE,f'{side} reveal foot {i+1}')
        lo,hi=sorted([sg*half,sg*outer])
        cuboid(b,lo,hi,0,.38,0,floor,CREAM,side+' ground end wall')
        cuboid(b,lo,hi,-.018,.04,0,.29,SHOE,side+' tapered base')
    # The survey text describes two glazed doors with geometric grilles and a diamond-plan pier.
    # The finer iron pattern is hidden by the later street gates in the available photograph.
    pier=.073*scale
    b.plan_prism(Polygon([(-pier,inside),(0,inside-.11),(pier,inside),(0,inside+.11)]),.02,floor-.11,STONE,'740 | central diamond door post')
    z0=.055;zt=floor-.16;bar=.044
    for sg,side in [(-1,'left'),(1,'right')]:
        lo,hi=sorted([sg*clear,sg*pier]);middle=(lo+hi)/2
        cuboid(b,lo,hi,inside+.09,inside+.126,z0,zt,GLASS,side+' entrance glass')
        for x in [lo+.5*bar,hi-.5*bar,middle]:
            cuboid(b,x-bar/2,x+bar/2,inside+.012,inside+.085,z0,zt,FRAME,side+' door stile')
        for z in [z0+.027,.55*zt,zt-.04]:
            cuboid(b,lo,hi,inside,inside+.07,z-.027,z+.027,FRAME,side+' door rail')
        for t in ([.12,.26,.38,.62,.75,.87] if not lod else [.23,.38,.62,.77]):
            x=lo+t*(hi-lo)
            cuboid(b,x-.011,x+.011,inside-.029,inside-.007,z0+.1,zt-.14,IRON,side+' metal grille')
        length=(hi-lo)*.22
        cuboid(b,middle-length,middle+length,inside-.105,inside-.05,.91,.95,WOOD,side+' entrance pull')
    cuboid(b,-clear,clear,inside+.006,inside+.17,zt,floor,FRAME,'entrance head')
    cuboid(b,-outer,outer,-.025,inside+.18,-.055,.019,STONE,'ground threshold')
    cuboid(b,-outer,outer,.045,inside+.18,floor-.10,floor+.022,SHADOW,'stepped entry head soffit')

def facet(b,a,c,floor,ceiling,label,lod):
    a,c=np.asarray(a,float),np.asarray(c,float)
    d=c-a;length=float(np.linalg.norm(d));t=d/length
    # Segments run from left to right. The streetward normal is the right-hand normal.
    normal=np.array([t[1],-t[0]])
    def xyz(u,depth):
        return a+t*u+normal*depth
    def map_point(u,z,depth):
        p=xyz(u,depth);return (p[0],p[1],z)
    sill=floor+.095
    observed_head=[2.64,2.74,2.72,2.58][int(label.split()[1])-2]
    top=min(ceiling-.32,floor+observed_head)
    left=length*.283;right=length*.738
    cavity=box(left,sill,right,top)
    wall=box(0,floor,length,ceiling).difference(cavity)
    b.prism(wall,-.24,0,map_point,SHADOW,'740 | '+label+' angled balcony wall')
    g=box(left,sill,right,top)
    b.prism(g,-.185,-.151,map_point,GLASS,'740 | '+label+' dark glazing')
    width=.043
    for u in [left+width/2,(left+right)/2,right-width/2]:
        b.prism(box(u-width/2,sill,u+width/2,top),-.146,-.083,map_point,FRAME,'740 | '+label+' glazing upright')
    for z in [sill+.023,top-.325,top-.023]:
        b.prism(box(left,z-.023,right,z+.023),-.142,-.078,map_point,FRAME,'740 | '+label+' transom')
    if not lod:
        for t in [.25,.75]:
            x=left+t*(right-left)
            b.prism(box(x-.012,top-.305,x+.012,top-.03),-.14,-.095,map_point,FRAME,'740 | '+label+' upper light')

def decoration(b,lod,x0,x1,y,low,top,label):
    height=top-low
    cuboid(b,x0,x1,y-.023,y+.006,low,top,STONE,label+' central cast field')
    width=x1-x0
    mx=(x0+x1)/2
    for sign in [-1,1]:
        ax=mx+sign*.265*width
        cuboid(b,ax-.013,ax+.013,y-.054,y-.018,low,top,BAND,label+' vertical relief')
    for i in range(3):
        z=low+(i+.5)*height/3
        # Each of three raised square bosses has an offset lower lip and two flanking chevrons.
        span=width*.086
        cuboid(b,mx-span,mx+span,y-.062,y-.018,z-span,z+span,STONE,label+' raised square')
        if not lod:cuboid(b,mx-span*1.13,mx+span*1.13,y-.072,y-.04,z-span-.011,z-span+.004,BAND,label+' square lower lip')
        for sign in [-1,1]:
            edge=mx+sign*width*.487;inner=mx+sign*width*.353
            xz(b,[(edge,z-height*.123),(inner,z),(edge,z+height*.123)],y-.052,.026,STONE,label+' folded cheek')
def balcony(b,lod,g,num):
    z=g['lower'][num];floor=z+g['slab_thickness'];rail=z+g['height_to_coping'];h=g['half_bay']
    y=g['front_balcony_y'];back=g['depth']
    high=g['lower'][num+1] if num<3 else g['soffit']
    label=f'level {num+2}'
    edge=.10;ends=.19
    front=-.015
    xy=[(-h,y),(h,y),(h,front+.34),(0,back+.26),(-h,front+.34)]
    b.plan_prism(Polygon(xy),z,floor,CREAM,'740 | '+label+' triangular floor')
    # Rear apartment walls retreat toward their shared centre and leave an open V-plan balcony.
    facet(b,[-h+.015,front+.15],[0,back],floor,high,label+' left',lod)
    facet(b,[0,back],[h-.015,front+.15],floor,high,label+' right',lod)
    cuboid(b,-.062,.062,front+.027,back+.16,floor,rail+.55,CREAM,label+' dividing wall')
    cuboid(b,-h,h,y,y+.155,floor,rail-.034,CREAM,label+' front parapet')
    cuboid(b,-h-.02,h+.02,y-.022,y+.188,rail-.044,rail,BAND,label+' coping')
    for sign,side in [(-1,'left'),(1,'right')]:
        lo,hi=sorted([sign*(h-ends),sign*h])
        cuboid(b,lo,hi,y+.13,front+.33,floor,rail-.035,CREAM,label+' '+side+' return')
        strip=sign*(h-.15)
        cuboid(b,strip-.037,strip+.037,y-.024,y+.002,floor+.02,rail-.05,BAND,label+' '+side+' end relief')
    decoration(b,lod,-.39,.39,y,floor+.003,rail-.043,label)

def add_corner(b,lod=False,layout=None):
    g=envelope(layout);half=g['width']/2;h=g['half_bay'];z=g['lower'][0]
    entrance(b,lod,g)
    for sign,side in [(-1,'left'),(1,'right')]:
        lo,hi=sorted([sign*h,sign*half])
        cuboid(b,lo,hi,0,.35,z,g['soffit'],CREAM,side+' corner wall')
        u=sign*(h+.115)
        cuboid(b,u-.056,u+.056,-.048,.12,z,g['soffit']-.20,BAND,side+' vertical reveal')
        for k in [-1,0,1]:
            x=sign*(half-.37)+k*.074
            cuboid(b,x-.024,x+.024,-.034,.035,g['soffit']-.51,g['soffit']-.074,STONE,side+' fluted head')
    for i in range(4):balcony(b,lod,g,i)
