"""Build the photographed west entrance of the garden residence at 602 West Jianguo Road."""
import argparse
import json
import os
import sys
from pathlib import Path
from math import cos,pi,sin
import numpy as np
from shapely.geometry import Polygon,LineString,box
from shapely.ops import unary_union

SOURCE=Path(__file__).resolve().parent
PROJECT=next(p for p in SOURCE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'tools'))
import package_architectural_model as package
sys.path.insert(0,str(PROJECT/'source/precise/huangpu-somekh-building-street-corner/source'))
from aggregate_mesh import AggregateBuilder
from photo_architecture import Facade,opening
from metal_canopy import build_canopy,SHEET,SEAM,EDGE,SOFFIT
from plaster import PLASTER,texture_coordinates

ID='xuhui-jianguo-602-west-canopy'
META=dict(id=ID,name='建国西路602号花园住宅西门与攒尖雨厦',viewer_page='jianguo-602-west-canopy.html',
          heritage_group='4D035',heritage_address='建国西路602号',status='western-entrance-photographic-study',
          scope='西面退台下的开放门洞、绿色攒尖铁雨厦、凹线门框与两级弧形石阶。')
M=SOURCE.parent/'measurements'
D=json.loads((M/'building-dimensions.json').read_bytes())['model_parameters_m']
PHOTO=json.loads((M/'canopy-profile-and-eave.json').read_bytes())
STONE='Grey dressed granite';GROOVE='Cut stone grooves';JAMB='Cream moulded portal';BASE='Grey cement plinth'
INNER='Shadowed entry reveal';IRON='Deep green iron gate';GLASS='Smoky interior transom';CLAY='Old square clay tiles'
def tone(rgb,roughness=.85,metallic=0.):
    channels=np.asarray(rgb)/255
    linear=np.where(channels<=.04045,channels/12.92,((channels+.055)/1.055)**2.4)
    return dict(color=linear.tolist(),roughness=roughness,metallic=metallic)
PALETTE={PLASTER:dict(color=[1.,1.,1.],roughness=.94,texture=str(SOURCE/'ochre-dragged-render.png')),
     SHEET:tone((68,109,85),.55,.32),SEAM:tone((43,72,56),.53,.37),EDGE:tone((72,104,81),.60,.28),SOFFIT:tone((64,73,55)),
     STONE:tone((157,151,139)),GROOVE:tone((96,89,75)),JAMB:tone((222,212,188)),BASE:tone((132,132,122)),
     INNER:tone((81,78,68)),IRON:tone((39,77,63),.59,.32),GLASS:tone((78,83,73),.31,.17),CLAY:tone((153,85,64)),
     'Terrazzo mortar':tone((106,99,88)),'Black rainwater pipe':tone((57,58,52),.71,.23),
     'Yellow clay tile':tone((163,99,72)),'Dark steel hardware':tone((58,62,55),.65,.33)}

def staircase(b,lod):
    levels=[(.012,.145,D['lower_step_width']/2,'Lower'),(.145,D['upper_step'],D['inner_step_width']/2,'Upper')]
    for low,high,rad,label in levels:
        ts=np.linspace(0,pi,35 if lod else 73)
        plan=Polygon([(rad*cos(t),-.010-rad*sin(t))for t in ts])
        b.plan_prism(plan,low,high,STONE,label+' step / half-round granite')
        pts=[(rad*.995*cos(t),-.010-rad*.995*sin(t),high-.012) for t in ts]
        b.tube(pts,.012,STONE,6 if lod else 10,label+' step / eased nosing')
    from radial_stone import build_radial_stone
    build_radial_stone(b,D['inner_step_width']/2,top=D['upper_step'],center_x=0.,threshold_y=0.,lod=lod,material=GROOVE)

def iron_leaf(b,hand,face):
    # Open leaves turn into the vestibule, as photographed at the engraved stone sill.
    width=D['aperture_width']/2-.023;z=D['upper_step'];x=hand*(D['aperture_width']/2-.037)
    angle=pi*78/180.;end=(x-hand*width*cos(angle),.085+width*sin(angle))
    ends=((x,.085),end) if hand<0 else (end,(x,.085))
    leaf=Facade(b,*ends,'Open gate '+('left' if hand<0 else 'right'))
    hw=leaf.length/2;high=z+2.34
    leaf.box(0,z+.19,2*hw,.38,.044,0,IRON,'sheeted kick panel')
    for side in (-1,1):
        leaf.box(side*(hw-.022),(z+high)/2,.044,high-z,.044,0,IRON,'hinge and latch stiles')
    for y in (z+.369,z+.89,high-.026):
        leaf.box(0,y,2*hw,.050,.047,0,IRON,'horizontal rails')
    for u in (-hw*.56,0,hw*.56):
        leaf.box(u,z+1.43,.018,1.73,.024,0,IRON,'vertical pickets')
    for u in (-hw*.48,hw*.48):
        for side in (-1,1):
            path=[]
            for t in np.linspace(0,1,24):
                a=pi*(-.52+1.67*t);r=.060*(1-.68*t)
                path.append(leaf.point(u+side*(.027+r*cos(a)),z+.50+r*sin(a),.021))
            b.tube(path,.009,IRON,5,'Open gate / lower opposed scrolls')
    return leaf

def build_hall(b,front,width,head,lod):
    z=D['upper_step']
    front.prism(box(-width/2,z,width/2,head),-1.18,-1.168,INNER,'shaded depth of vestibule')
    # The red square paving is visible beyond the inscribed stone threshold.
    b.box((0,.558,z-.023),(width,1.14,.042),'Terrazzo mortar',label='Vestibule / mortar bed')
    step=.148
    for row in range(8):
        for col in range(-5,5):
            l=max(-width/2,col*step);r=min(width/2,(col+1)*step)
            a=max(0,row*step);c=min(1.14,(row+1)*step)
            if r-l>.006 and c-a>.006:
                b.box(((l+r)/2,(a+c)/2,z+.001),(r-l-.005,c-a-.005,.005),CLAY if (row+col)%5 else 'Yellow clay tile',label='Vestibule / individual floor tiles')
    b.box((0,-.010,z+.001),(width+.015,.104,.026),'Dark steel hardware',label='Entry / dark threshold strip')
    for s in (-1,1):
        iron_leaf(b,s,front)
    window=box(-width/2+.025,z+2.42,width/2-.025,head-.025)
    front.prism(window,-.32,-.307,GLASS,'fixed upper transom glass')
    bars=[box(-.016,z+2.38,.016,head)]
    for i in (-1,1):
        a=i*width*.265;bars.append(box(a-.010,z+2.42,a+.010,head))
    frame=window.difference(window.buffer(-.041,join_style=2).difference(unary_union(bars)))
    front.prism(frame,-.297,-.255,IRON,'upper transom mullions')
    front.box(0,z+2.406,width-.035,.056,.082,-.28,IRON,'upper transom bottom rail')
    # The close view shows three stepped recesses ending on deep, squared plinth blocks.
    inner=box(-width/2,z,width/2,head)
    current=inner
    for i,(side,up,offset,depth) in enumerate(((.042,.050,-.115,.070),(.055,.065,-.045,.061),(.064,.076,.016,.040))):
        nxt=box(current.bounds[0]-side,z,current.bounds[2]+side,current.bounds[3]+up)
        front.prism(nxt.difference(current),offset,offset+depth,JAMB,f'Portal / returned stepped bead {i+1}')
        current=nxt
    for hand in (-1,1):
        front.box(hand*(width/2+.096),z+.222,.193,.444,.172,-.009,JAMB,'Portal / squared jamb plinth')
    # A broad segmental reveal rises behind the canopy, above the straight transom.
    top=head+.44;span=width+.35
    inner=opening(0,z,span,top-z,.35,segments=21 if lod else 37)
    surround=inner.buffer(.077,join_style=1).difference(inner).intersection(box(-span,head+.061,span,top+.14))
    front.prism(surround,-.033,.100,JAMB,'Portal / rounded outer hood moulding')
    return current

def add_building(b,lod):
    W=D['wall_width'];left=-D['wall_left_of_door'];right=left+W;top=D['wall_top'];z=D['upper_step']
    glass=D['aperture_width'];head=z+D['aperture_height']
    # This facade uses the west door axis as local zero, independent of the site's outer wall width.
    front=Facade(b,(-W/2,0),(W/2,0),'West wall')
    surround=build_hall(b,front,glass,head,lod)
    outline=box(left,.017,right,top-.095).difference(surround)
    front.prism(outline,-.34,0,PLASTER,'terrace wall around west entrance')
    for a,c in ((left,-glass/2-.16),(glass/2+.16,right)):
        front.box((a+c)/2,.29,c-a,.54,.060,.015,BASE,'grey wall foot')
        front.box((a+c)/2,.557,c-a,.051,.095,.026,JAMB,'plinth top bead')
    for offset,h,depth in ((-.19,.13,.105),(-.098,.047,.131),(-.022,.103,.176)):
        front.box((left+right)/2,top+offset,W+.024,h,depth,.038,JAMB,'terrace parapet cornice')
    front.box((left+right)/2,top-.56,W,.49,.11,-.035,PLASTER,'terrace parapet')
    for a,sign in ((left,-1),(right,1)):
        ends=((a,1.08),(a,0))if sign<0 else((a,0),(a,1.08))
        flank=Facade(b,*ends,'Left return' if sign<0 else 'Right return')
        flank.wall(.018,top-.10,(),.22,PLASTER)
        flank.box(0,.29,1.08,.54,.045,.014,BASE,'return plinth')
        flank.box(0,top-.031,1.13,.095,.176,.026,JAMB,'return cornice cap')
    b.box(((left+right)/2,.60,top-.55),(W,1.05,.10),BASE,label='Terrace / floor behind parapet')
    x=left+.16
    b.tube([(x,-.070,.08),(x,-.112,.20),(x,-.100,.47),(x,-.10,top-.45),(x+.049,-.10,top-.24),(x+.03,-.113,top-.14)],
           .048,'Black rainwater pipe',8 if lod else 16,'Left end / rainwater downpipe')
    for level in (.61,2.10,3.86,5.00):
        b.box((x,-.08,level),(.124,.16,.030),'Dark steel hardware',label='Left end / pipe straps')
    staircase(b,lod)
    build_canopy(b,D,PHOTO,lod)
    texture_coordinates(b)

if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False);parser.add_argument('--blender',default='blender')
    options,args=parser.parse_known_args();os.environ['JIANGUO_CANOPY_BLENDER']=options.blender
    sys.argv[1:]=[*args,'--blender',str(SOURCE/'native_blender.py')]
    package.Builder=AggregateBuilder
    package.build(SOURCE,META,PALETTE,add_building)
