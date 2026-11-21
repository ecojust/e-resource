"""The northern stair light, scallop canopy and flanking two-storey brickwork."""
from math import pi,sin,cos
import numpy as np
from shapely.geometry import Polygon,LineString,box as rectangle
from shapely.ops import unary_union
from photo_architecture import Facade,opening

BRICK='Pathe red stretchers'
STONE='Warm dressed stone'
WHITE='Warm white enamel'
FRAME='Dark window frames'
GLASS='Daylit glazing'
SHADOW='Inner opening'
IRON='Forged metal'
TIMBER='Dark eaves timber'
WOOD='Panelled entrance doors'
DARK='Stair flight behind the light'
FLAG='Green enamel plaque'


def sash(wall,center,bottom,width,height,lod,label,narrow=False):
    """Build the glass, iron lattice, canted masonry lintel and sill inside a real brick opening."""
    hole=opening(center,bottom,width,height);head=bottom+height
    inner=hole.buffer(-.034,join_style=2)
    columns=2 if narrow else 4;rows=6
    bars=[]
    for k in range(1,columns):
        x=center+width*(k/columns-.5);bars.append(rectangle(x-.009,bottom,x+.009,head))
    for k in range(1,rows):
        z=bottom+height*k/rows;d=.025 if k==4 else .009
        bars.append(rectangle(center-width,z-d,center+width,z+d))
    frame=hole.difference(inner.difference(unary_union(bars)))
    wall.prism(hole,-.157,-.147,GLASS,label+' • glass')
    wall.prism(frame,-.119,-.083,FRAME,label+' • casement and transom')
    wall.prism(hole.difference(inner),-.149,-.075,FRAME,label+' • frame lining')
    if not narrow:
        for i in range(7):
            z=bottom+i*height/7
            for hand in (-1,1):
                w=.089 if i%2 else .135
                wall.box(center+hand*(width/2+w/2),z+height/14,w,height/7-.006,.062,.012,STONE,label+' • jamb blocks')
    wall.box(center,bottom-.043,width+.19,.086,.165,.055,STONE,label+' • projecting sill')
    lintel_h=.13 if narrow else .17
    outline=Polygon([(center-width/2-.075,head),(center+width/2+.075,head),(center+width/2+.14,head+lintel_h),(center-width/2-.14,head+lintel_h)])
    pieces=[]
    for i in range(1,5 if narrow else 7):
        u=i/(5 if narrow else 7)-.5
        pieces.append(LineString([(center+width*u,head-.003),(center+(width+.27)*u,head+lintel_h+.003)]).buffer(.003,cap_style=2))
    blocks=outline.difference(unary_union(pieces))
    wall.prism(blocks,-.013,.032,STONE,label+' • splayed lintel joints')
    return hole


def segment(wall,u,z,width,height,material,label,depth=.035,d=.013):
    wall.box(u,z,width,height,depth,d,material,label)


def ribbed_canopy(b,wall,cx):
    width=4.20;reach=1.53;root=.035
    def edge(angle):
        return (cx+width/2*cos(angle),root+reach*sin(angle))
    points=[edge(t) for t in np.linspace(0,pi,57)]
    outline=Polygon([(cx-width/2,root),(cx+width/2,root),*points[1:-1]])
    canopy_plan=Polygon([wall.point(u,0,d)[:2] for u,d in outline.exterior.coords])
    b.plan_prism(canopy_plan,2.92,3.045,WHITE,'North entrance • oval rain canopy')
    # The broad, shallow ribs originate along the head and spread out under the slab.
    for angle in np.linspace(.10*pi,.90*pi,7):
        u,d=edge(angle)
        start=wall.point(cx+(u-cx)*.18,0,.015)
        end=wall.point(u,0,d-.025)
        along=end-start
        across=np.array([-along[1],along[0],0])/np.linalg.norm(along)
        # The 2013 underside photograph shows a continuous rectangular downstand.
        # Its lower edge rises towards the rim and its upper edge meets the slab.
        vertices=[]
        for fraction,base,radius in ((0,2.736,.061),(.38,2.827,.058),(1,2.890,.032)):
            at=start+fraction*along
            for side,z in ((-1,base),(1,base),(1,2.947),(-1,2.947)):
                vertices.append(at+side*radius*across+np.array([0,0,z]))
        sides=[(0,3,2,1),(8,9,10,11)]
        for i in (0,4):
            for j in range(4):
                k=(j+1)%4
                sides.append((i+j,i+k,i+4+k,i+4+j))
        b.add(vertices,sides,STONE,'North entrance • seven radiating ribs')
    edge_line=[wall.point(u,3.013,d)for u,d in points]
    b.tube(edge_line,.028,STONE,8,'North entrance • curved edge bead')


def door_and_lights(b,wall,cx,lod):
    z=.18;h=2.10;width=1.42;top=z+h
    hole=rectangle(cx-width/2,z,cx+width/2,top-.13).union(rectangle(cx-width/2+.13,z+.2,cx+width/2-.13,top))
    for hand in (-1,1):
        from shapely.geometry import Point
        hole=hole.union(Point(cx+hand*(width/2-.13),top-.13).buffer(.13,quad_segs=8))
    ring=hole.buffer(.103,join_style=1).difference(hole)
    wall.prism(ring,-.30,.035,STONE,'North entrance • rounded doorway and deep jambs')
    wall.prism(hole,-.325,-.31,SHADOW,'North entrance • door backing')
    leaf_width=width/2-.021
    for hand in (-1,1):
        x=cx+hand*width/4;label='North door • '+('left' if hand<0 else 'right')
        leaf=hole.intersection(rectangle(x-leaf_width/2,z,x+leaf_width/2,top))
        glazed=opening(x,z+.60,leaf_width-.135,1.35,.125)
        wall.prism(leaf.difference(glazed),-.295,-.244,WOOD,label+' • timber leaf')
        wall.prism(glazed,-.286,-.278,'Entrance glazing',label+' • glazed light')
        wall.prism(glazed.buffer(.022).difference(glazed),-.25,-.215,WOOD,label+' • arched bead')
        small=rectangle(x-leaf_width*.38,z+.085,x+leaf_width*.38,z+.48)
        wall.prism(small.difference(small.buffer(-.024,join_style=2)),-.246,-.223,WOOD,label+' • raised lower panel')
        for fraction in (.26,.79):
            level=z+.60+fraction*1.35
            bar=glazed.intersection(rectangle(x-leaf_width/2,level-.010,x+leaf_width/2,level+.010))
            wall.prism(bar,-.250,-.231,IRON,label+' • glass crossbars')
        waist=z+1.19
        dia=[(x,waist+.24),(x+.125,waist),(x,waist-.24),(x-.125,waist),(x,waist+.24)]
        b.tube([wall.point(u,v,-.226)for u,v in dia],.012,IRON,5,label+' • iron diamond')
        for end in (-1,1):
            for side in (-1,1):
                arc=np.linspace(-pi/2,1.55*pi,10 if lod else 18)
                path=[wall.point(x+side*(.105+.084*cos(t)),waist+end*(.27+.087*sin(t)),-.225)for t in arc]
                b.tube(path,.009,IRON,5,label+' • paired scrolls')
        for u in [x-leaf_width*.32,x+leaf_width*.32]:
            wall.box(u,z+1.27,.016,1.28,.025,-.232,IRON,label+' • side strap')
    wall.box(cx+.062,1.055,.092,.016,.039,-.196,'Bronze details','North entrance • handle')
    # Two narrow sidelights stay separate from the door and extend below the lamps.
    holes=[hole]
    for sign in (-1,1):
        x=cx+sign*1.19;sill=.81;head=2.03;small=opening(x,sill,.46,head-sill);holes.append(small)
        wall.prism(small,-.164,-.152,GLASS,'North entrance • sidelight glass')
        inner=small.buffer(-.025,join_style=2);bars=[rectangle(x-.012,sill,x+.012,head)]
        for j in range(1,4):
            cut=sill+(head-sill)*j/4;bars.append(rectangle(x-.25,cut-.012,x+.25,cut+.012))
        wall.prism(small.difference(inner.difference(unary_union(bars))),-.105,-.071,FRAME,'North entrance • sidelight iron bars')
        wall.prism(small.buffer(.051,join_style=2).difference(small),-.16,.021,STONE,'North entrance • sidelight reveals')
        wall.box(x,sill-.041,.65,.082,.17,.042,STONE,'North entrance • sidelight sill')
        lamp_x=cx+sign*.99;lamp_y=.16
        b.tube([wall.point(lamp_x,2.25,.025),wall.point(lamp_x,2.25,.21),wall.point(lamp_x,2.33,.26)],.020,IRON,8,'Northern wall lanterns • brackets')
        pos=wall.point(lamp_x,0,.26)[:2]
        b.lathe(pos,[(2.30,.037),(2.35,.088),(2.53,.116),(2.59,.103),(2.61,.042)],'Lantern glass',8,'Northern wall lanterns • glazing')
        for az in np.linspace(0,2*pi,5,endpoint=False):
            b.tube([wall.point(lamp_x+.083*cos(az),2.34,.26+.083*sin(az)),wall.point(lamp_x+.112*cos(az),2.57,.26+.112*sin(az))],.008,IRON,5,'Northern wall lanterns • metal cage')
        b.lathe(pos,[(2.55,.117),(2.59,.128),(2.62,.096),(2.67,.024)],IRON,10,'Northern wall lanterns • cap')
    step=[(cx+1.00*cos(t),.025+.58*sin(t))for t in np.linspace(0,pi,41 if lod else 65)]
    b.plan_prism(Polygon([wall.point(u,0,d)[:2] for u,d in step]),.017,.181,STONE,'North entrance • bowed stone step')
    u=cx-1.72
    wall.box(u,2.60,.25,.225,.026,.036,FLAG,'Northern wall • enamel number plaque')
    for offset,num in [(-.074,'8'),(.004,'1'),(.077,'1')]:
        x=u+offset
        if num=='8':
            for dz in (-.031,.031):
                pts=[wall.point(x+.022*cos(t),2.61+dz+.03*sin(t),.054)for t in np.linspace(0,2*pi,15)]
                b.tube(pts,.006,WHITE,5,'Northern wall • number 811')
        else:
            b.tube([wall.point(x-.015,2.65,.054),wall.point(x,2.668,.054),wall.point(x,2.553,.054)],.006,WHITE,5,'Northern wall • number 811')
    return holes


def stair_window(b,face,D,lod):
    x=D['north_tower_center'];w=D['stair_window_width'];bottom=D['stair_window_base'];head=D['stair_window_head']
    aperture=opening(x,bottom,w,head-bottom,.57,segments=28 if lod else 44)
    inside=aperture.buffer(-.047,join_style=2)
    face.prism(aperture,-.204,-.191,GLASS,'North stair • tall glazed light')
    rails=[]
    for k in range(1,8):
        u=x+w*(k/8-.5);g=.018 if k==4 else .009
        rails.append(rectangle(u-g,bottom,u+g,head))
    for z in np.arange(bottom+.24,head,.245):
        rails.append(rectangle(x-w*.57,z-.008,x+w*.57,z+.008))
    for z in (bottom+.19,bottom+1.55,bottom+3.08,bottom+4.59):
        rails.append(rectangle(x-w*.55,z-.026,x+w*.55,z+.026))
    face.prism(aperture.difference(inside.difference(unary_union(rails))),-.14,-.105,FRAME,'North stair • eight-light iron grid')
    face.prism(aperture.buffer(.098).difference(aperture),-.20,.028,STONE,'North stair • continuous arched reveal')
    for dz,thick in ((-.28,.33),(2.37,.66)):
        c=bottom+dz
        band=Polygon([(x-w/2,c+.42),(x+w/2,c-.43),(x+w/2,c-.43+thick),(x-w/2,c+.42+thick)]).intersection(inside)
        if band.area:
            face.prism(band,-.109,-.086,DARK,'North stair • visible inclined spandrels')
            border=band.boundary.buffer(.013,cap_style=2).intersection(band)
            face.prism(border,-.085,-.073,FRAME,'North stair • band edging')
    return aperture


def build_north(b,D,lod):
    width=D['width'];half=width/2;tower=D['north_tower_width'];cx=D['north_tower_center']
    facade=Facade(b,(-half,0),(half,0),'North brick')
    tower_front=-D['north_tower_projection']
    stone=Facade(b,(-half,tower_front),(half,tower_front),'North stair')
    brick_holes=[]
    for n,(u,w) in enumerate(((-4.75,.705),(-2.40,.41),(2.76,.38),(4.32,.38))):
        for level,z,h in [('lower',D['north_ground_sill'],D['north_ground_window_height']),('upper',D['north_upper_sill'],D['north_upper_window_height'])]:
            brick_holes.append(sash(facade,u,z,w,h,lod,f'North brick bay {n+1} {level}',n>0))
    for left,right in [(-half,cx-tower/2),(cx+tower/2,half)]:
        area=rectangle(left,.012,right,D['wall_eave'])
        for hole in brick_holes:
            if hole.intersects(area):area=area.difference(hole)
        facade.prism(area,-.29,0,BRICK,'North • brick flanks')
        center=(left+right)/2;span=right-left
        facade.box(center,.29,span,.54,.105,.024,STONE,'North brick field • plinth')
        for z,h,d in ((.56,.080,.14),(4.08,.10,.075),(4.16,.042,.095)):
            facade.box(center,z,span,h,d,.018,STONE,'North brick field • moulded stringcourses')
    holes=[stair_window(b,stone,D,lod),*door_and_lights(b,stone,cx,lod)]
    masonry=rectangle(cx-tower/2,0,cx+tower/2,D['north_tower_eave']).difference(unary_union(holes))
    stone.prism(masonry,-.29,-.006,STONE,'North stair • tall dressed-stone wall')
    # Slightly recessed mortar lines run between the cut stone blocks. Apertures cut through every joint.
    bed=[]
    for j in range(29):
        z=.18+j*.332
        bed.append(rectangle(cx-tower/2,z-.005,cx+tower/2,z+.005))
        for k in range(-3,4):
            x=cx+k*.74+(j%2)*.37
            if abs(x-cx)<tower/2-.08:
                bed.append(rectangle(x-.004,z,x+.004,z+.332))
    grooves=masonry.intersection(unary_union(bed))
    stone.prism(grooves,-.0056,-.0027,'Stone joints','North stair • staggered masonry joints')
    for hand in (-1,1):
        u=cx+hand*tower/2
        ends=[(u,tower_front),(u,2.21)]
        if hand<0:ends.reverse()
        face=Facade(b,*ends,'North stair returns')
        face.wall(0,D['north_tower_eave'],(),.12,STONE)
        for k in range(21):
            z=.26+k*.332;wide=.18 if k%2==0 else .09
            stone.box(u+hand*wide/2,z,wide,.326,.058,-.006,STONE,'North stair • projecting quoins')
    rear=Facade(b,(cx+tower/2,2.21),(cx-tower/2,2.21),'Back of northern stair head')
    rear.wall(6.90,D['north_tower_eave'],(),.16,STONE)
    ribbed_canopy(b,stone,cx)
