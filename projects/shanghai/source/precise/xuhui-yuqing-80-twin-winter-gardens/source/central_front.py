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
    # A projected vertical through each photographed shaft centre constrains a vertical plane.
    # These planes intersect in the physical centre line, independent of approximate floor height.
    normals=[];constants=[];cameras={'4':cam,'6':Camera(6)}
    for view,c in cameras.items():
        ray=c.ray(points['centre_pixels'][view])
        n=np.cross(ray,[0,0,1])[:2];normals.append(n);constants.append(n@c.c[:2])
    xy=np.linalg.solve(normals,constants);x,y=xy;radii=[]
    for view,c in cameras.items():
        for p in points['opposed_shaft_edges'][view]:
            v=c.ray(p)[:2];v/=np.linalg.norm(v);offset=xy-c.c[:2]
            radii.append(abs(v[0]*offset[1]-v[1]*offset[0]))
    radius=float(np.median(radii))
    b.tube([(x,y,-.015),(x,y,soffit-.41)],radius,CERAMIC,12 if lod else 32,'Center | round garden support')
    c=cameras['6'];west=x-radius;profile=[]
    for p in points['photo6_front_haunch_underside']:
        ray=c.ray(p);v=c.c+ray*((west-c.c[0])/ray[0]);profile.append((v[1],v[2]))
    yz=[(y+radius,soffit-.77),*profile,(profile[-1][0]-.10,soffit),(y+radius,soffit)]
    b.prism(Polygon(yz),west,x+radius,lambda v,z,x:(x,v,z),CERAMIC,'Center | scooped front haunch')

def roof_edge(b,left,right,roof,lod):
    # Two notches in the roof slab can both be followed in the 2013 northeast photograph.
    edges=[(left,-.62),(-5.19,-.62),(-5.19,-1.24),(6.23,-.94),(6.23,-.37),(right,-.15)]
    deck=Polygon([*edges,(right,1.55),(left,1.55)])
    b.plan_prism(deck,roof,roof+.22,COPING,'Upper roof | twice-stepped eave')
    for (a,ay),(c,cy) in zip(edges,edges[1:]):
        length=np.hypot(c-a,cy-ay)
        if length<.01:continue
        dx,dy=(c-a)/length,(cy-ay)/length
        # A narrow curb follows the two actual returns as well as the long reaches.
        q=Polygon([(a,ay+.13),(c,cy+.13),(c-dy*.15,cy+.13+dx*.15),(a-dy*.15,ay+.13+dx*.15)])
        b.plan_prism(q,roof+.22,roof+.49,PLASTER,'Upper roof | curb following eaves')
        for z in [roof+.59,roof+1.08]:
            b.tube([(a,ay+.23,z),(c,cy+.23,z)],.019,RAILING,6 if lod else 10,'Upper roof | terrace rail')
        count=max(2,int(round(length/(.27 if lod else .14))))
        for i,f in enumerate(np.linspace(0,1,count,endpoint=False)):
            x=a+(c-a)*f;y=ay+.23+(cy-ay)*f
            w=.041 if i%13==0 else .017
            solid(b,x-w,x+w,y-.020,y+.020,roof+.49,roof+1.10,RAILING,'Upper roof | vertical guard')

def cooling_unit(b,cam,survey):
    # The square unit and its circular fan occur in both principal views.
    xy=cam.wall(survey['air_conditioner_center']['4'],-.02)
    x,z=xy[0],xy[2];front=-.10
    solid(b,x-.39,x+.39,front,.25,z-.30,z+.30,COPING,'Upper garden wall | air conditioner')
    radial=np.linspace(0,2*np.pi,33)
    ring=[(x-.065+.195*np.cos(t),front-.022,z+.19*np.sin(t))for t in radial]
    b.tube(ring,.013,FRAME,6,'Upper garden wall | circular fan grille')
    for dz in np.linspace(-.16,.16,7):
        half=np.sqrt(.19**2-dz**2)
        solid(b,x-.065-half,x-.065+half,front-.022,front-.010,z+dz-.006,z+dz+.006,FRAME,'Upper garden wall | fan guard slats')

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
    # The upper parapet is considerably shorter than the uninterrupted lower bridge.
    # Corner rays from both garden photographs place its southwest end almost on X=0.
    # Its floor projects further forward and to the southwest of that parapet.
    upper=[(-.58,-2.36),(5.67,-2.29),(right,-1.87),(right,.91),(-.58,.91)]
    from shapely.geometry import Point
    visible_deck=Polygon(upper).difference(Point(right,0).buffer(ne,resolution=42).intersection(box(right-ne,-ne,right+ne,0)))
    b.plan_prism(visible_deck,6.23,6.49,COPING,'Garden | shorter upper deck with projecting rim')
    wallfront=Polygon([(.10,-1.18),(5.93,-1.17),(right,-1.13),(right,-.96),(.10,-.98)])
    parapet=wallfront.difference(Point(right,0).buffer(ne-.61,resolution=42).intersection(box(right-ne,-ne,right+ne,0)))
    b.plan_prism(parapet,6.49,7.80,PLASTER,'Garden | upper terrace parapet')
    b.plan_prism(parapet.buffer(.018,join_style=2),7.80,7.835,RAILING,'Garden | thin dark upper coping')
    solid(b,.10,.27,-1.18,.64,6.49,7.80,PLASTER,'Upper terrace | southwest parapet return')
    solid(b,.084,.286,-1.19,.65,7.80,7.835,RAILING,'Upper terrace | coping on west return')
    solid(b,.02,.26,-2.35,.82,sills-.06,6.255,PLASTER,'Gallery | transverse support of the shorter upper deck')
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
    cooling_unit(b,cam,survey)
    for p in survey['upper_drain_heads']:
        v=cam.wall(p,.27);x=v[0]
        b.tube([(x,.240,sills+.03),(x,.240,roof-.08)],.057,PIPE,8 if lod else 12,'Upper roof | rainwater leader')
        b.tube([(x,.215,roof-.47),(x,.215,roof-.22)],.089,PIPE,8 if lod else 16,'Upper roof | collector socket')
    return dict(sw_center=left,ne_center=right,soffit=soffit,roof=roof)
