"""The numbered porch and five curving approach steps of Building 3 in Dingxiang Garden."""
from math import cos, sin, pi, sqrt
from pathlib import Path
import argparse
import json
import os
import sys

import numpy as np
from shapely.geometry import LineString, Point, Polygon, box as rectangle

SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
import package_architectural_model as package
sys.path.insert(0,str(SOURCE.parents[1]/'huangpu-somekh-building-street-corner/source'))
from aggregate_mesh import AggregateBuilder
from photo_architecture import Facade
from pebble_wall import STONE, texture_coordinates

ID='xuhui-dingxiang-three-numbered-porch'
META=dict(id=ID,name='丁香花园三号楼门廊与弧形石阶',viewer_page='dingxiang-three-numbered-porch.html',
          heritage_group='4D023',heritage_address='华山路849号',status='documented-building-three-porch',
          scope='三号牌、木构门架、红瓦雨檐、廊后偏置拱门、五道弧形踏步与双侧铁艺扶手。')
D=json.loads((SOURCE.parent/'measurements/porch-and-steps.json').read_bytes())['adopted_m']
RISE=D['riser'];FLOOR=5*RISE;THROAT=D['top_landing_width']/2;HEIGHT=D['front_under_lintel']
GRANITE='Grey granolithic treads';JOINT='Darker stone joints';IRON='Black twisted iron';GRIP='Mahogany handrails'
WOOD='Brown porch timber';PINK='Rose tile insets';LINE='Pale tile joints';BASE='Muted red brick plinth';MORTAR='Lime mortar'
TRIM='Deep green eaves';GUTTER='Brown metal gutters';CLAY='Rounded red clay tiles';TILE='Clay troughs';BRASS='Number and brass plates'
DARK='Shadow inside rear doorway';FRAME='Dark stained doorframe';CEILING='Warm porch soffit';LIGHT='Opal ceiling bowl'


def color(rgb,rough=.8,metal=0.):
    def channel(value):
        n=value/255
        return n/12.92 if n<=.04045 else ((n+.055)/1.055)**2.4
    return dict(color=[channel(c)for c in rgb],roughness=rough,metallic=metal)


PALETTE={STONE:dict(color=[1,1,1],roughness=.91,texture=str(SOURCE/'river-pebble-wall.png')),
         GRANITE:color((167,163,149),.83),JOINT:color((100,99,88)),IRON:color((55,57,54),.62,.38),
         GRIP:color((130,62,47),.51),WOOD:color((124,96,80)),PINK:color((191,147,144)),LINE:color((221,206,185)),
         BASE:color((157,107,99)),MORTAR:color((186,180,163)),TRIM:color((63,101,82)),GUTTER:color((82,78,68),.64,.15),
         CLAY:color((175,111,88)),TILE:color((151,94,77)),BRASS:color((175,166,111),.56,.18),
         DARK:color((29,31,31)),FRAME:color((86,66,58)),CEILING:color((141,130,110)),LIGHT:color((194,191,170),.42)}


def xy(x,y,z):return (x,y,z)


def step_outline(course,samples):
    # The five front edges are concentric arcs. The exposed sides flare out from the top landing.
    radius=4.27+course*D['going'];centre_y=3.85
    half=THROAT+(D['outer_step_width']/2-THROAT)*course/4
    curve=[]
    for i in range(samples+1):
        u=half*(1-2*i/samples)
        curve.append((u,centre_y-sqrt(radius*radius-u*u)))
    return Polygon([(-THROAT,0),(THROAT,0),*curve])


def stone_steps(b,lod):
    for course in range(5):
        outline=step_outline(course,20 if lod else 54)
        high=FLOOR-course*RISE
        b.prism(outline.buffer(-.004,join_style=2),high-RISE,high-.012,xy,JOINT,'Mortared tread joints')
        # Recessed joints follow different radial planes on alternate courses, like the photograph.
        cuts=[-1.25,-.235,.044,.275,1.25] if course%2==0 else [-1.25,-.19,.125,1.25]
        for index,(a,c) in enumerate(zip(cuts,cuts[1:])):
            wedge=Polygon([(0,3.85),(24*sin(a),3.85-24*cos(a)),(24*sin(c),3.85-24*cos(c))])
            block=outline.intersection(wedge).buffer(-.003,join_style=2)
            if not block.is_empty:
                b.prism(block,high-RISE+.002,high,xy,GRANITE,f'Step {5-course}/stone {index+1}')


def twist(b,start,end,thickness,turns,lod,label):
    a,c=np.array(start),np.array(end);axis=c-a;axis/=np.linalg.norm(axis)
    helper=np.array([0.,0.,1.]) if abs(axis[2])<.85 else np.array([1.,0.,0.])
    first=np.cross(axis,helper);first/=np.linalg.norm(first);second=np.cross(axis,first)
    n=4 if lod else max(10,round(turns*12));points=[];faces=[]
    for i in range(n+1):
        t=i/n;centre=(1-t)*a+t*c
        for j in range(4):
            rot=2*pi*(turns*t+j/4)
            points.append(tuple(centre+thickness*(cos(rot)*first+sin(rot)*second)))
    for i in range(n):
        for j in range(4):
            a0=4*i+j;a1=4*i+(j+1)%4;faces.append((a0,a1,a1+4,a0+4))
    faces.extend([(3,2,1,0),tuple(4*n+j for j in range(4))]);b.add(points,faces,IRON,label)


def rail_point(side,t,relative_z=0):
    x=THROAT-.032+(.91*t+.075*t*t);y=-.018-1.32*t-.047*sin(t*pi)
    return np.array([side*x,y,FLOOR+D['rail_height']-.76*t+relative_z])


def railing(b,side,lod):
    # Sweep the broad, flat wood grip around the bowed plan line. Its four corners have short chamfers.
    n=8 if lod else 22;verts=[];faces=[]
    section=[(-.049,.035),(.049,.035),(.063,.021),(.063,-.020),(.049,-.032),(-.049,-.032),(-.063,-.020),(-.063,.021)]
    for i in range(n+1):
        t=i/n;centre=rail_point(side,t);delta=rail_point(side,t+.001)-rail_point(side,t-.001)
        out=np.array([-delta[1],delta[0],0]);out/=np.linalg.norm(out)
        for u,v in section:verts.append(tuple(centre+u*out+[0,0,v]))
        if i:
            for j in range(8):
                k=(i-1)*8+j;l=(i-1)*8+(j+1)%8;faces.append((k,l,l+8,k+8))
    faces.extend([tuple(reversed(range(8))),tuple(range(n*8,n*8+8))]);b.add(verts,faces,GRIP,'Curved varnished handrail')
    stations=(0.,.52,1.)
    feet=[]
    for t in stations:
        anchor=Point(rail_point(side,t)[:2])
        surface=next((FLOOR-i*RISE for i in range(5) if step_outline(i,54).covers(anchor)),0.)
        feet.append(surface+.024)
    for t,foot in zip(stations,feet):
        top=rail_point(side,t,-.035);pos=top.copy();pos[2]=foot
        b.box(tuple(pos-[0,0,.012]),(.116,.105,.024),IRON,label='Square rail footplates')
        twist(b,pos,top,.019,1.3,lod,'Twisted upright posts')
    for i,(ta,tb) in enumerate(zip(stations,stations[1:])):
        start,end=rail_point(side,ta,-.09),rail_point(side,tb,-.09)
        low_a=start.copy();low_a[2]=feet[i]+.12;low_b=end.copy();low_b[2]=feet[i+1]+.12
        b.tube([tuple(low_a),tuple(low_b)],.013,IRON,5 if lod else 8,'Lower iron rail')
        horizontal=end-start;horizontal[2]=0.;horizontal/=np.linalg.norm(horizontal)
        ring=(start+end+low_a+low_b)/4;radius=.093
        loop=[tuple(ring+horizontal*radius*cos(2*pi*j/20)+[0,0,radius*sin(2*pi*j/20)])for j in range(21)]
        b.tube(loop,.011,IRON,5 if lod else 8,'Ring at centre of ironwork')
        for k,pt in enumerate((start,end,low_a,low_b)):
            axis=pt-ring;axis/=np.linalg.norm(axis)
            twist(b,ring+axis*radius,pt,.012,2.5,lod,'Twisted diagonals to ring')


def numeral(face,cx,z):
    # Trace the two lobes and the small inward waist of the number plate from the front photograph.
    controls=[(-.14,.118),(-.035,.226),(.195,.171),(.086,.035),(.024,.008),(.182,-.010),(.137,-.136),(.052,-.192),(-.070,-.188),(-.143,-.120)]
    points=[];a=np.array(controls[0])
    for j in (1,4,7):
        b,c,d=[np.array(v)for v in controls[j:j+3]]
        for k in range(13):
            t=k/12;pt=(1-t)**3*a+3*(1-t)**2*t*b+3*(1-t)*t*t*c+t**3*d
            points.append((cx+pt[0],z+pt[1]))
        a=d
    face.prism(LineString(points).buffer(.031,resolution=6),.161,.172,DARK,'Raised number 3')


def front_screen(b,front,side):
    width=.79;inner=D['clear_span']/2;cx=side*(inner+width/2);sill=FLOOR+1.03
    front.box(cx,FLOOR+.065,width+.045,.13,.45,0,GRANITE,'Stone post bases')
    front.box(cx,FLOOR+.58,width,.90,.27,0,WOOD,'Panelled post feet')
    face=rectangle(cx-.25,FLOOR+.15,cx+.25,sill-.045)
    front.prism(face,.137,.148,PINK,'Rose herringbone panels')
    for j in range(-8,11):
        z=FLOOR+.11*j
        for sign in (-1,1):
            stroke=LineString([(cx,z),(cx+sign*.29,z+sign*.29 if j%4<2 else z-sign*.29)]).buffer(.0045,cap_style=2)
            joint=stroke.intersection(face)
            if not joint.is_empty and joint.area>1e-8:front.prism(joint,.1485,.151,LINE,'Fine joints across rose tiles')
    for i in range(4):
        u=cx+(i-1.5)*.20
        front.box(u,(sill+HEIGHT)/2,.12 if i in(0,3)else .074,HEIGHT-sill,.28,0,WOOD,'Tall slotted timber screens')
    front.box(cx,sill-.018,width,.13,.285,0,WOOD,'Screen bottom cross rail')
    if side<0:
        z=HEIGHT-.34
        front.box(cx,z,.55,.55,.035,.1425,BRASS,'Square brass address plaque');numeral(front,cx,z)
        front.box(cx,sill+.39,.42,.32,.027,.15,BRASS,'Smaller brass name plate')
    # Concave quarter braces are open to the porch below the head beam.
    nose=side*inner;points=[(nose,HEIGHT),(nose-side*.33,HEIGHT)]
    for j in range(13):
        t=pi*j/24;points.append((nose-side*.33*(1-sin(t)),HEIGHT-.74*(1-cos(t))))
    front.prism(Polygon(points).buffer(0),-.19,.14,WOOD,'Curved brackets at inner corners')


def rear_door(b,front,lod):
    depth=D['recess_depth'];wall=Facade(b,(-2.74,depth),(2.74,depth),'Rear wall of porch')
    cx=.78;radius=D['doorway_width']/2;spring=D['doorway_head']-radius
    def arch(r,foot):
        arc=[(cx+r*cos(i*pi/30),spring+r*sin(i*pi/30))for i in range(31)]
        return Polygon([(cx-r,foot),(cx+r,foot),*arc])
    hole=arch(radius+.059,FLOOR-.003)
    wall.wall(FLOOR,HEIGHT+.13,[hole],.23,STONE)
    wall.prism(hole.difference(arch(radius-.018,FLOOR-.004)),-.007,.046,FRAME,'Architrave of off-centre doorway')
    wall.prism(arch(radius+.01,FLOOR-.006),-.253,-.226,DARK,'Dark door at rear of loggia')
    wall.box(cx,FLOOR+.028,2*radius+.086,.056,.39,-.034,GRANITE,'Rear door threshold')
    front.box(0,FLOOR-.046,2*THROAT, .092,depth,-depth/2,GRANITE,'Porch paving')
    # The same bench and hanging bowl are visible in both views of the covered space.
    for i in range(4):
        b.box((-.76,depth-.19,FLOOR+.49+i*.074),(1.14,.042,.055),WOOD,label='Bench back slats')
    b.box((-.76,depth-.32,FLOOR+.39),(1.19,.32,.057),WOOD,label='Simple bench seat')
    for x in (-1.22,-.30):
        for y in (depth-.18,depth-.46):
            b.box((x,y,FLOOR+.198),(.032,.039,.396),IRON,label='Bench legs')
    for x in (-.18,.18):
        b.tube([(x*.31,.81,HEIGHT+.015),(x,.81,HEIGHT-.26)],.007,IRON,5,'Lamp suspension')
    b.lathe((0,.81),[(HEIGHT-.33,.016),(HEIGHT-.318,.086),(HEIGHT-.286,.154),(HEIGHT-.245,.174)],LIGHT,12 if lod else 24,'Hanging opal bowl')


def masonry_jamb(b,front,side,lod):
    outer=2.76;inner=D['clear_span']/2+.80;width=outer-inner;cx=side*(inner+outer)/2
    front.box(cx,(FLOOR+HEIGHT)/2,width,HEIGHT-FLOOR,.46,-.115,STONE,'Outer pebble wall')
    front.box(cx,FLOOR/2,width,FLOOR,.46,-.115,MORTAR,'Brick footing joints')
    course=.063;brick_width=.223
    for row in range(int(FLOOR/course)+1):
        bottom=row*course;high=min((row+1)*course,FLOOR)
        if high-bottom<.008:continue
        left=cx-width/2;edge=left-(row%2)*brick_width/2
        while edge<cx+width/2:
            x0=max(left,edge+.004);x1=min(cx+width/2,edge+brick_width-.004)
            if x1>x0:front.box((x0+x1)/2,(bottom+high)/2,x1-x0,high-bottom-.006,.016,.123,BASE,'Brick plinth courses')
            edge+=brick_width
    cheek=Facade(b,(side*outer,0),(side*outer,D['recess_depth']),'Cut end of porch')
    cheek.wall(0,HEIGHT,(),.10,STONE)
    x=side*(outer-.079);high=HEIGHT+.28
    b.box((x,-.178,high/2),(.102,.082,high),GUTTER,label='Square downpipes')
    b.box((x,-.186,HEIGHT-.27),(.25,.212,.22),GUTTER,label='Rainwater hoppers')


def red_tile_canopy(b,front,lod):
    half=D['canopy_width']/2;back=D['recess_depth'];eave=HEIGHT+.285;rise=.83
    def tile_point(t,y,extra=0):
        k=(y+.28)/(back+.28);span=half-.57*k
        return (t*span,y,eave+k*rise+extra)
    corners=[tile_point(-1,-.28),tile_point(1,-.28),tile_point(1,back),tile_point(-1,back)]
    b.add([(x,y,z-.10)for x,y,z in corners]+corners,
          [(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],TILE,'Hipped red porch roof')
    count=31 if lod else 44;rows=8 if lod else 13
    for i in range(count):
        t=-1+(i+.5)*2/count
        b.tube([tile_point(t,-.28,.025),tile_point(t,back,.025)],.031,CLAY,6 if lod else 8,'Rounded tile rolls')
    for j in range(1,rows):
        y=-.28+j*(back+.28)/rows
        b.tube([tile_point(-1,y,.014),tile_point(1,y,.014)],.013,CLAY,5 if lod else 8,'Tapered rows of clay tiles')
    for height,width,thick,depth in [(eave-.07,half*2+.05,.12,.32),(eave-.161,half*2-.086,.071,.29)]:
        front.box(0,height,width,thick,depth,.18,TRIM,'Stepped green fascia')
    front.box(0,eave+.009,half*2+.17,.071,.14,.29,GUTTER,'Continuous dark gutter')
    front.box(0,HEIGHT-.033,2*(D['clear_span']/2+.79),.164,.37,0,WOOD,'Head beam over screens')
    front.box(0,HEIGHT+.062,half*2-.31,.105,back+.18,-(back-.18)/2,CEILING,'Underside of porch ceiling')
    for x in (-.86,0,.86):
        b.box((x,back/2,HEIGHT+.002),(.083,back,.12),WOOD,label='Exposed ceiling joists')


def add_building(b,lod):
    front=Facade(b,(-3.3,0),(3.3,0),'Numbered entrance')
    stone_steps(b,lod)
    rear_door(b,front,lod)
    for side in (-1,1):
        front_screen(b,front,side)
        masonry_jamb(b,front,side,lod)
        railing(b,side,lod)
    red_tile_canopy(b,front,lod)
    texture_coordinates(b)


if __name__=='__main__':
    ap=argparse.ArgumentParser(add_help=False);ap.add_argument('--blender',default='blender');args,other=ap.parse_known_args()
    os.environ['DINGXIANG_PORCH_BLENDER']=args.blender
    sys.argv[1:]=[*other,'--blender',str(SOURCE/'native_blender.py')]
    package.Builder=AggregateBuilder
    package.build(SOURCE,META,PALETTE,add_building)
