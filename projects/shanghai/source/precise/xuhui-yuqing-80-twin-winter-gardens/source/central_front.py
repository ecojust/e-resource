"""The two recessed ground-floor casements, garden balcony and roof terrace between the rounded winter gardens."""
from pathlib import Path
import json
import sys

import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'measurements'))
from register_garden import Camera

PLASTER = 'Garden | cream roughcast'
COPING = 'Garden | pale edged concrete'
FRAME = 'Garden | dark casement frame'
GLASS = 'Garden | reflected blue grey glass'
PANEL = 'Garden | dark lower panel'
TERRACE = 'Garden | weathered terrace'
RAILING = 'Garden | dark painted rail'
PIPE = 'Garden | cast downpipe'
CERAMIC = 'Garden | warm white column'

def material(rgb, rough, metallic=0):
    srgb=np.asarray(rgb,dtype=float)/255
    linear=np.where(srgb<=.04045,srgb/12.92,((srgb+.055)/1.055)**2.4)
    return dict(color=linear.tolist(), roughness=rough, metallic=metallic)

PALETTE = {PLASTER:material((209,202,176),.96), COPING:material((214,211,192),.88),
           FRAME:material((55,55,49),.58,.22), GLASS:material((101,114,116),.32,.1),
           PANEL:material((65,55,48),.79), TERRACE:material((155,151,134),.90),
           RAILING:material((61,58,52),.65,.15), PIPE:material((63,62,55),.75,.18),
           CERAMIC:material((221,216,193),.87)}

def solid(b,x0,x1,y0,y1,z0,z1,mat,label):
    if min(x1-x0,y1-y0,z1-z0)>0:
        b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),mat,label=label)

def face(b,shape,y,depth,mat,label):
    if not shape.is_empty:
        b.prism(shape,-y-depth,-y,lambda x,z,d:(x,-d,z),mat,label)

def bounds(cam,record,y):
    v=np.asarray([cam.wall(p,y) for p in record['clockwise_from_upper_left']])
    left,right=v[[0,3],0].mean(),v[[1,2],0].mean()
    bottom,top=v[[2,3],2].mean(),v[[0,1],2].mean()
    if record['storey']=='ground':
        bottom=.045
    return left,bottom,right,top

def make_window(b,record,limits,y,lod):
    l,base,r,top=limits
    name='Center | '+record['label']
    border=.048;inside=box(l+border,base+border,r-border,top-border)
    face(b,box(l,base,r,top).difference(inside),y+.03,.066,FRAME,name+' | rolled perimeter')
    solid(b,l+border,r-border,y+.13,y+.15,base+border,top-border,GLASS,name+' | daylight')
    for ratio in record['width_divisions']:
        x=l+ratio*(r-l)
        solid(b,x-.018,x+.018,y+.055,y+.087,base+.035,top-.035,FRAME,name+' | upright')
    for ratio in record['transom_above_sill']:
        z=base+ratio*(top-base)
        solid(b,l+.035,r-.035,y+.039,y+.080,z-.015,z+.015,FRAME,name+' | transom')
    if record['storey']=='ground':
        z=base+.25*(top-base)
        solid(b,l+.04,r-.04,y+.096,y+.117,base+.043,z,PANEL,name+' | lower infill')
        if not lod:
            for x in np.arange(l+.22,r-.13,.27):
                solid(b,x-.007,x+.007,y+.021,y+.038,z,top-.05,FRAME,name+' | narrow interior bar')
    solid(b,l-.035,r+.035,y-.042,y+.055,base-.029,base+.012,COPING,name+' | sill')

def central_column(b,cam,points,lod,soffit):
    foot=cam.at_height(points['foot'],0)
    y=foot[1]
    a=cam.wall(points['left_at_middle'],y);c=cam.wall(points['right_at_middle'],y)
    radius=float(np.clip(abs(c[0]-a[0])/2,.19,.34))
    x=foot[0]
    b.tube([(x,y,0),(x,y,soffit-.20)],radius,CERAMIC,12 if lod else 32,'Center | round garden support')
    upper=x+radius
    q=[(x-radius,soffit-.62),(upper,soffit-.62),(upper,soffit-.16),(upper+.20,soffit-.04),
       (upper+.20,soffit),(x-radius-.59,soffit),(x-radius-.39,soffit-.083),
       (x-radius-.20,soffit-.19),(x-radius-.09,soffit-.32)]
    face(b,Polygon(q),y-radius,.62,CERAMIC,'Center | scooped haunch below the terrace')

def roof_edge(b,left,right,roof,lod):
    solid(b,left,right,-.34,1.55,roof,roof+.22,COPING,'Upper roof | projecting eave')
    solid(b,left+.24,right-.24,.18,.36,roof+.22,roof+.53,PLASTER,'Upper roof | garden curb')
    for z in [roof+.62,roof+1.08]:
        solid(b,left+.31,right-.31,.28,.33,z-.019,z+.019,RAILING,'Upper roof | terrace rail')
    for i,x in enumerate(np.linspace(left+.35,right-.35,47 if lod else 94)):
        solid(b,x-.020,x+.020,.277,.328,roof+.50,roof+1.1,RAILING,'Upper roof | vertical guard')
        if not lod and i%10==0:
            solid(b,x-.057,x+.057,.23,.36,roof+.22,roof+1.12,RAILING,'Upper roof | principal post')

def add_central_front(b,lod=False):
    cam=Camera(4);survey=json.loads((HERE.parent/'measurements/central-front-controls.json').read_bytes())
    d=cam.data;soffit=d['middle_slab_underside_z'];eave=d['eave_soffit_z']
    left,right=(d['centres_m'][side] for side in ('SW','NE'))
    sw,ne=(d['outer_radii_m'][side] for side in ('SW','NE'))
    roof=9.43
    west_web,east_web=left+sw-.10,right-ne+.10
    sills=d['window_sill_z']
    ranges={'ground':(west_web,east_web,0,soffit),
            'middle':(west_web,east_web,soffit+.05,eave+.30),
            'upper':(left-sw+.10,right+ne-.08,eave+.27,roof+.05),
            'northeast_return':(right+ne-1.22,right+ne+1.95,0,7.05)}
    for storey,(l,r,z,h) in ranges.items():
        y=survey['inside_render_planes_m'][storey]
        records=[(v,bounds(cam,v,y)) for v in survey['windows'] if v['storey']==storey]
        field=box(l,z,r,h)
        openings=unary_union([box(*limits) for _,limits in records]);face(b,field.difference(openings),y,.22,PLASTER,'Garden | '+storey+' wall with real openings')
        for v,rect in records:make_window(b,v,rect,y,lod)
    # The central bridges meet the round slabs at their quarter arcs. The two levels have different extensions.
    solid(b,left,right,-3.065,.91,soffit,soffit+.15,COPING,'Garden | broad lower bridge slab')
    solid(b,left,right,-3.065,-2.84,soffit+.15,sills-.075,PLASTER,'Garden | long first-floor parapet')
    solid(b,left,right,-3.10,-2.81,sills-.075,sills-.033,COPING,'Garden | first-floor coping')
    solid(b,left+sw+.04,right,-1.47,.84,eave+.02,eave+.22,COPING,'Garden | recessed upper bridge')
    solid(b,left+sw+.04,right,-1.46,-1.26,eave+.22,d['upper_parapet_z']-.04,PLASTER,'Garden | upper bridge solid edge')
    solid(b,left+sw+.04,right,-1.49,-1.23,d['upper_parapet_z']-.04,d['upper_parapet_z'],COPING,'Garden | upper coping')
    # A perpendicular cheek marks the southwest end of the shortened upper bridge in photo 6.
    solid(b,left+sw+.04,left+sw+.24,-1.45,.81,sills-.02,eave+.11,PLASTER,'Gallery | upper bridge end return')
    solid(b,right+ne-1.25,right+ne+2.0,.78,1.42,6.06,6.19,COPING,'Northeast end | hood over the square upper window')
    solid(b,right+ne-1.15,right+ne+1.95,.96,1.22,6.98,7.08,COPING,'Northeast end | roof coping')
    solid(b,east_web,5.54,.68,.90,0,soffit,PLASTER,'Ground | recessed wall adjoining the eastern curve')
    solid(b,5.40,5.54,.29,.89,0,soffit,PLASTER,'Ground | inner jamb of the eastern curve')
    solid(b,10.79,10.93,.29,1.05,0,soffit,PLASTER,'Ground | outer jamb returning to square wing')
    central_column(b,cam,survey['central_column'],lod,soffit)
    solid(b,west_web,east_web,-3.02,.90,-.13,0,TERRACE,'Ground | sheltered terrace floor')
    solid(b,west_web,east_web,-3.31,-3.05,-.40,.30,COPING,'Ground | low garden wall')
    for z in [.36,.58,.79,1.00]:
        b.tube([(west_web,-3.17,z),(east_web,-3.17,z)],.018,RAILING,6 if lod else 10,'Ground | long tubular garden rail')
    for x in np.linspace(west_web+.10,east_web-.10,7):
        b.tube([(x,-3.17,.285),(x,-3.17,1.02)],.025,RAILING,8,'Ground | garden rail post')
    roof_edge(b,left-sw+.04,right+ne+.12,roof,lod)
    for p in survey['upper_drain_heads']:
        v=cam.wall(p,.27);x=v[0]
        b.tube([(x,.240,eave+.18),(x,.240,roof-.08)],.057,PIPE,8 if lod else 12,'Upper roof | rainwater leader')
        b.tube([(x,.215,roof-.47),(x,.215,roof-.22)],.089,PIPE,8 if lod else 16,'Upper roof | collector socket')
    return dict(sw_center=left,ne_center=right,soffit=soffit,roof=roof)
