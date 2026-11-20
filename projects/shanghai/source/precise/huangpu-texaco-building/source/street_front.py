"""2020 curved glazed-brick street wall at 110 East Yan'an Road."""
from pathlib import Path
import json
import math
import numpy as np
from scipy.interpolate import PchipInterpolator
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade, opening

BRICK='buff glazed facing tile'
DARK='brown glazed tile'
JOINT='fine ochre mortar'
STONE='pale window-band concrete'
FRAME='dark metal window sash'
GLASS='smoke grey glazing'
GROUND='tan fluted stone'
WOOD='bronze entrance frames'
ROOF='weathered roof surface'
PALETTE={
    BRICK:dict(color=[.61,.529,.424],roughness=.67), DARK:dict(color=[.499,.417,.329],roughness=.69),
    JOINT:dict(color=[.481,.405,.328],roughness=.87),STONE:dict(color=[.725,.701,.648],roughness=.70),
    FRAME:dict(color=[.157,.166,.164],roughness=.54,metallic=.35),GLASS:dict(color=[.215,.260,.28],roughness=.28,metallic=.32),
    GROUND:dict(color=[.568,.502,.405],roughness=.80),WOOD:dict(color=[.272,.228,.158],roughness=.45,metallic=.43),
    ROOF:dict(color=[.392,.371,.331],roughness=.88)}
SOURCE=json.loads((Path(__file__).resolve().parents[1]/'footprint-review.json').read_bytes())
frame=SOURCE['local_frame']
control=np.array(frame['author_plan_coords_xy_m'])[frame['front_path_source_indices_west_to_north']]
curve=PchipInterpolator(control[:,0],control[:,1])
xx=np.linspace(control[0,0],control[-1,0],1601)
ss=np.r_[0,np.linalg.norm(np.diff(np.column_stack((xx,curve(xx))),axis=0),axis=1).cumsum()]
UNIT=ss[-1]/22.8
DEPTH=2.65
SILLS=(1.10,5.05,8.71,12.37,16.03,19.69)
SOUTH_EAVE=19.00
EAST_EAVE=22.67

def point_at(station,depth=0):
    x=np.interp(station,ss,xx)
    y=float(curve(x))
    slope=curve.derivative()(x)
    normal=np.array([-slope,1.])/math.hypot(slope,1.)
    return (np.array([x,y])+depth*normal).tolist()

def panel(f,x,z,w,h,back,front,material,name):
    f.box(x,z,w,h,front-back,(back+front)/2,material,name)

def sash(f,x,z,w,h,lod,name,primary=False):
    aperture=opening(x,z,w,h)
    depth=.29 if not primary else .78
    f.prism(aperture.buffer(.008,join_style=2),-depth-.15,-depth-.10,GLASS,name+' glazing')
    internal=aperture.buffer(-.058,join_style=2)
    transom=z+h*(.71 if not primary else .77)
    bars=[box(x-w/2,transom-.036,x+w/2,transom+.036)]
    for u in (-w/6,w/6):
        bars.append(box(x+u-.033,z,x+u+.033,transom))
    bars.append(box(x-.033,transom,x+.033,z+h))
    if primary:
        bars.extend([box(x-.038,z,x+.038,z+h),box(x-w/2,z+.96,x+w/2,z+1.015)])
    frame_shape=aperture.buffer(-.008,join_style=2).difference(internal.difference(unary_union(bars)))
    f.prism(frame_shape,-depth-.055,-depth+.025,WOOD if primary else FRAME,name+' casement')
    if primary and not lod:
        for side in (-1,1):
            panel(f,x+side*.14,z+1.11,.041,.51,-depth+.02,-depth+.108,WOOD,'door pull')
    return aperture

def facing(f,level,z0,z1,lod,central=False):
    # Tile joints are narrow surface strips. They leave the recessed glass and
    # the continuous white horizontal window surrounds completely clear.
    if lod:return
    width=f.length-.08
    for k in range(1,6):
        z=z0+(z1-z0)*k/6
        panel(f,0,z,width,.015,0,.009,JOINT,'horizontal tile joints')
    step=.33 if central else .385
    for i,x in enumerate(np.arange(-width/2+.20,width/2-.1,step)):
        for half in (0,1):
            lo=z0+(z1-z0)*half*.5+.04
            hi=lo+(z1-z0)*.5-.08
            offset=.085*((i+level+half)%2)
            panel(f,x+offset,(lo+hi)/2,.013,hi-lo,0,.009,JOINT,'vertical tile joints')

def strip(f,lod,south,index,start,end):
    height=SOUTH_EAVE if south else EAST_EAVE
    count=5 if south else 6
    apertures=[]
    for level,z in enumerate(SILLS[:count]):
        w=f.length*(.769 if level==0 else .848)
        h=1.84 if level==0 else 1.61
        apertures.append(sash(f,0,z,w,h,lod,'ground' if level==0 else 'ribbon'))
        if level:
            for bound in (z-.06,z+h+.06):
                panel(f,0,bound,f.length+.010,.115,-.03,.115,STONE,'continuous pale ribbon')
            for x,visible in ((-f.length/2+.13,start),(f.length/2-.13,end)):
                if visible:
                    panel(f,x,z+h/2,.13,h+.18,-.035,.112,STONE,'band end return')
        if level+1<count:
            facing(f,level,z+h+.13,SILLS[level+1]-.13,lod)
    facing(f,count,SILLS[count-1]+1.76,height-.13,lod)
    f.wall(0,height,apertures,.34,BRICK)
    panel(f,0,height+.012,f.length+.006,.11,-.20,.055,DARK,'thin coping')
    if not lod:
        for edge in (-1,1):
            panel(f,edge*(f.length*.5-.08),2.01,.013,1.65,0,.011,JOINT,'ground pier joint')

def entry(f,lod):
    # Two separate doors and paired upper windows, flanked by vertical reeds.
    # Figure 19 shows the rounded shared central post and the deeper portal.
    width=f.length
    apertures=[]
    for level,z in enumerate(SILLS):
        if not level:
            for side in (-1,1):
                x=side*width*.234
                sash(f,x,.12,width*.407,3.36,lod,'entrance door',True)
                # Carry the two recesses down to the pavement. A low wall
                # across their mouths would incorrectly block both entries.
                apertures.append(opening(x,0,width*.407,3.48))
        else:
            for side in (-1,1):
                x=side*width*.174
                apertures.append(sash(f,x,z,width*.269,1.61,lod,'paired window'))
                panel(f,x,z-.045,width*.280,.086,-.04,.082,STONE,'short paired sill')
            if level in (4,5):
                panel(f,0,z-.064,width,.125,-.015,.108,STONE,'upper continuous band')
        top=z+1.61 if level else 3.57
        if level+1<len(SILLS):facing(f,level,top+.14,SILLS[level+1]-.18,lod,True)
    f.wall(0,EAST_EAVE,apertures,.46,BRICK)
    panel(f,0,3.75,width,.48,-.05,.21,GROUND,'entrance lintel')
    f.line((0,.04,.05),(0,3.48,.05),.165,GROUND,10 if lod else 28,'round entrance post')
    for side in (-1,1):
        for n in range(3):
            x=side*(width*.430+n*.123)
            panel(f,x,(3.93+EAST_EAVE)/2,.079,EAST_EAVE-3.93,-.002,.085+.018*(n%2),DARK,'reeds at entry edges')
        panel(f,side*width*.459,1.77,.23,3.48,-.09,.17,GROUND,'fluted portal edge')
    facing(f,6,SILLS[-1]+1.76,EAST_EAVE-.15,lod,True)
    panel(f,0,EAST_EAVE+.012,width,.11,-.20,.055,DARK,'thin coping')

def add_front(b,lod):
    left=9*UNIT;right=left+2.8*UNIT
    spans=[(i*UNIT,(i+1)*UNIT,'South',i)for i in range(9)]
    spans.append((left,right,'Entry',0))
    spans.extend((right+i*UNIT,right+(i+1)*UNIT,'East',i)for i in range(11))
    for begin,end,side,i in spans:
        a,c=point_at(begin),point_at(end)
        backing_a,backing_c=point_at(begin,DEPTH),point_at(end,DEPTH)
        f=Facade(b,a,c,side+(' bay '+str(i+1) if side!='Entry' else ''))
        if side=='Entry':entry(f,lod)
        else:strip(f,lod,side=='South',i,i==0,i==(8 if side=='South' else 10))
        h=SOUTH_EAVE if side=='South' else EAST_EAVE
        # The flat strips cap only the photographed front wall. The deep
        # source roof, rear facade and old rooftop work remain in the city.
        shape=Polygon([a,c,backing_c,backing_a])
        b.plan_prism(shape,h-.11,h-.015,ROOF,side+'/roof edge strip')
        floor=shape
        if side=='Entry':
            for side_sign in (-1,1):
                x=side_sign*f.length*.234
                half=f.length*.407/2
                recess=Polygon([f.point(u,0,d)[:2]for u,d in
                    ((x-half,.04),(x+half,.04),(x+half,-.77),(x-half,-.77))])
                floor=floor.difference(recess)
        b.plan_prism(floor,.035,.075,GROUND,side+'/ground slab behind street wall')
        rear=Facade(b,backing_c,backing_a,side+' rear')
        rear.wall(0,h,(),.15,GROUND)
        if side=='South' and i==0:Facade(b,backing_a,a,'South end').wall(0,h,(),.21,BRICK)
        if side=='East' and i==10:Facade(b,c,backing_c,'East end').wall(0,h,(),.21,BRICK)
        if side=='Entry':Facade(b,backing_a,a,'Step at entrance').wall(SOUTH_EAVE,EAST_EAVE,(),.23,BRICK)
