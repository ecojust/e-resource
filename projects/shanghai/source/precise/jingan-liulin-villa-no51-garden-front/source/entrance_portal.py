"""柳林别墅51号柱后门罩、双扇门、两侧格窗及院内三级踏步。

以高参88的两张花园立面原照校正至门墙Y2.280m。坐标请参阅
measurements/no51-house-cameras.json。各玻璃格、门框、滴边和门饰均为几何。
"""
from pathlib import Path
import numpy as np
from math import cos, radians, sin
from shapely.geometry import LineString, Polygon, box as polygon_box
from shapely.ops import unary_union

PLASTER = 'Entrance | warm pale render'
EDGE = 'Entrance | projecting moulded cream edges'
WOOD = 'Entrance | recessed walnut joinery'
RAIL = 'Entrance | polished wood beads'
GLASS = 'Entrance | dark reflective glazing'
IRON = 'Entrance | aged paired door pulls'
SHADOW = 'Entrance | shaded space beyond opening'
TREAD = 'Entrance | worn grey-brown treads'
RISER = 'Entrance | darker stone risers'

def finish(rgb, roughness, metallic=0.):
    def linear(n):
        s = n / 255.
        return s / 12.92 if s <= .04045 else ((s + .055) / 1.055) ** 2.4
    return dict(color=[linear(n) for n in rgb], roughness=roughness, metallic=metallic)

PALETTE = {
    PLASTER: finish((187,177,155),.84), EDGE: finish((202,192,168),.78),
    WOOD: finish((78,51,38),.65), RAIL: finish((91,61,46),.52),
    GLASS: dict(finish((37,46,45),.26,.14),alpha=.83),
    IRON: finish((67,61,47),.43,.48), SHADOW: finish((22,20,18),.97),
    TREAD: finish((139,130,117),.69), RISER: finish((98,91,81),.81),
}

# Swatches are deterministic procedural grains, with no street photograph pixels.
for key,file,factor in ((WOOD,'entrance-dark-timber.jpg',1.),
                        (TREAD,'entrance-step-stone.jpg',1.),(RISER,'entrance-step-stone.jpg',.49)):
    PALETTE[key].update(texture=str(Path(__file__).with_name(file)),color=[factor]*3)

def material_faces(part):
    """Lay out each actual face including returns. Keep all UVs inside the portable clamped swatch."""
    material=part['material']
    if not PALETTE.get(material,{}).get('texture'):
        return
    vertices=np.array(part['vertices'])
    new_vertices=[];uv=[];faces=[]
    bounds=np.ptp(vertices,axis=0)
    for tri in part['triangles']:
        pts=vertices[list(tri)]
        normal=np.cross(pts[1]-pts[0],pts[2]-pts[0])
        axis=int(np.argmax(np.abs(normal)))
        if axis==2:
            u_axis,v_axis=0,1
        elif axis==0:
            u_axis,v_axis=1,2
        else:
            u_axis,v_axis=0,2
        if material==WOOD and bounds[2]<max(bounds[0],bounds[1]):
            u_axis,v_axis=v_axis,u_axis
        low=vertices[:,[u_axis,v_axis]].min(axis=0)
        scale=np.maximum(np.ptp(vertices[:,[u_axis,v_axis]],axis=0),.08)
        coords=(pts[:,[u_axis,v_axis]]-low)/scale
        index=len(new_vertices);new_vertices.extend(map(tuple,pts))
        uv.extend((float(.01+a*.98),float(.99-b*.98)) for a,b in coords)
        faces.append((index,index+1,index+2))
    part.update(vertices=new_vertices,triangles=faces,texcoords=uv)

def combined_wall_cut():
    """(left, right, bottom, top) in metres; union includes the side panels."""
    return (-2.62, 2.20, .48, 3.39)

def rect_x(u):
    return u / 160. - 3.30

def rect_z(v):
    return 4.65 - v / 160.

def block(b,x0,x1,y0,y1,z0,z1,mat,name):
    b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),mat,label=name)

def registered_xz(x,z,y):
    # Invert the sightline from the gao06 native camera to the rectified wall plane.
    fraction=(y+20.82112089157552)/(2.28+20.82112089157552)
    return (9.792830942010045+fraction*(x-9.792830942010045),
            1.7359989153098836+fraction*(z-1.7359989153098836))

def rect(b,u0,u1,v0,v1,y,depth,mat,name):
    x0,z0=registered_xz(rect_x(u0),rect_z(v1),y)
    x1,z1=registered_xz(rect_x(u1),rect_z(v0),y)
    block(b,x0,x1,y,y+depth,z0,z1,mat,name)

def frame(b,u0,u1,v0,v1,width,y,depth,mat,name):
    rect(b,u0,u1,v0,v0+width,y,depth,mat,name)
    rect(b,u0,u1,v1-width,v1,y,depth,mat,name)
    rect(b,u0,u0+width,v0+width,v1-width,y,depth,mat,name)
    rect(b,u1-width,u1,v0+width,v1-width,y,depth,mat,name)

def screen(b,offset,side):
    name = 'Portal '+side+' | '
    rect(b,136+offset,146+offset,239,529,2.22,.12,WOOD,name+'sash jambs')
    rect(b,288+offset,298+offset,239,529,2.22,.12,WOOD,name+'sash jambs')
    rect(b,146+offset,288+offset,239,258,2.22,.12,WOOD,name+'sash head')
    rect(b,146+offset,288+offset,502,529,2.22,.12,WOOD,name+'sash bottom rail')
    for start,end,bar in ((146,218,188),(220,288,255)):
        u0,u1=start+offset,end+offset
        left,right=((165,210) if start==146 else (234,278))
        left,right,bar=left+offset,right+offset,bar+offset
        rect(b,u0,left,257,503,2.249,.077,WOOD,name+'paired casement frames')
        rect(b,right,u1,257,503,2.249,.077,WOOD,name+'paired casement frames')
        rect(b,left,right,257,264,2.249,.077,WOOD,name+'paired casement frames')
        rect(b,left,right,498,503,2.249,.077,WOOD,name+'paired casement frames')
        rect(b,bar-2,bar+2,264,498,2.254,.041,RAIL,name+'glazing bars')
        for v in (319,379,441):
            rect(b,left,right,v-2.1,v+2.1,2.252,.046,RAIL,name+'glazing bars')
        for a,c in [(left,bar-2),(bar+2,right)]:
            for top,base in [(264,316.9),(321.1,376.9),(381.1,438.9),(443.1,498)]:
                rect(b,a,c,top,base,2.291,.008,GLASS,name+'sixteen separate glass panes')
    rect(b,214+offset,220+offset,257,503,2.23,.105,WOOD,name+'meeting stile')
    rect(b,97+offset,328+offset,525,546,1.988,.368,EDGE,name+'stone sill')
    rect(b,104+offset,323+offset,546,553,2.055,.26,PLASTER,name+'sill underside')
    rect(b,110+offset,325+offset,552,666,2.235,.15,PLASTER,name+'low blank panel')
    frame(b,132+offset,298+offset,611,649,3,2.207,.029,EDGE,name+'panel inset bead')

def door_leaf(b,open_leaf):
    name='Door '+('open right' if open_leaf else 'closed left')+' | '
    start=len(b.parts)
    x0,x1=352.,498.
    rect(b,x0,x0+20,238,662,2.131,.105,WOOD,name+'hinge stile')
    rect(b,x1-19,x1,238,662,2.131,.105,WOOD,name+'meeting stile')
    rect(b,x0+20,x1-19,238,287,2.131,.105,WOOD,name+'top rail')
    for a,c in [(372,402),(462,479)]:
        rect(b,a,c,287,476,2.143,.09,WOOD,name+'upper glazing surround')
    rect(b,402,462,287,292,2.143,.09,WOOD,name+'upper glazing surround')
    rect(b,402,462,469,476,2.143,.09,WOOD,name+'upper glazing surround')
    frame(b,397,467,284,475,4,2.121,.043,RAIL,name+'beaded glass rebate')
    rect(b,428,436,292,469,2.149,.041,WOOD,name+'upper vertical glazing bar')
    for v in (349,411):
        rect(b,402,462,v-3.2,v+3.2,2.143,.047,WOOD,name+'two horizontal glazing bars')
    for left,right in [(402,428),(436,462)]:
        for top,base in [(292,345.8),(352.2,407.8),(414.2,469)]:
            rect(b,left,right,top,base,2.19,.008,GLASS,name+'six individual upper panes')
    rect(b,372,479,476,662,2.155,.077,WOOD,name+'lower panel field')
    rect(b,372,479,477,509,2.13,.103,WOOD,name+'lock rail')
    frame(b,380,475,507,638,6.5,2.126,.043,RAIL,name+'lower field outer bead')
    frame(b,389,466,517,628,3.2,2.134,.034,RAIL,name+'inner raised panel bead')
    rect(b,372,479,640,662,2.13,.103,WOOD,name+'lower solid rail')
    if not open_leaf:
        anchor=registered_xz(rect_x(352),0,2.15)[0]
        for part in b.parts[start:]:
            part['vertices']=[(anchor+.958*(x-anchor),y,z) for x,y,z in part['vertices']]
    if open_leaf:
        u=360.
        for v in (482,526):
            rect(b,u-2,u+2,v-2,v+2,2.085,.053,IRON,name+'handle mounts')
        rect(b,u-1.7,u+1.7,481,528,2.075,.017,IRON,name+'long iron pull')
        theta=radians(92)
        for part in b.parts[start:]:
            part['vertices']=[(.66+(x-registered_xz(rect_x(x1),0,2.15)[0])*cos(theta)-(y-2.15)*sin(theta),
                               2.22+(x-registered_xz(rect_x(x1),0,2.15)[0])*sin(theta)+(y-2.15)*cos(theta),z)
                              for x,y,z in part['vertices']]

def ornaments(b,centre,far,side):
    name='Portal '+side+' | '
    rect(b,centre-21,centre+21,233,662,2.125,.213,PLASTER,name+'plaster pilaster')
    frame(b,centre-18,centre+18,244,448,1.35,2.113,.024,EDGE,name+'carved field border')
    lines=[]
    def trace(coords,width):
        lines.append(LineString([registered_xz(rect_x(centre+x),rect_z(y),2.087) for x,y in coords]).buffer(
            width/320,quad_segs=1 if far else 3,cap_style='round',join_style='round'))
    for sign in (-1,1):
        trace([(sign*7,302),(sign*9,294),(sign*8,273),(sign*7,248)],2.6)
        for v in (255,268,282,295):
            trace([(sign*7,v+4),(sign*11,v),(sign*10,v-4)],2.4)
        trace([(0,315),(sign*7,309),(sign*14,308),(sign*17,314),(sign*13,318),(sign*6,317),(0,314)],3.3)
        trace([(0,317),(sign*5,321),(sign*11,324),(sign*14,323)],2.4)
        for v in (342,379,416):
            trace([(0,v-12),(sign*6,v-10),(sign*9,v-4),(sign*7,v+4)],2.5)
            trace([(0,v+10),(sign*5,v+14),(sign*13,v+13),(sign*15,v+7),(sign*12,v+8)],3.)
            trace([(0,v+15),(sign*4,v+18),(sign*2,v+21)],2.5)
    trace([(0,317),(0,333)],2.)
    for v in (345,382,419):
        trace([(-3,v+8),(0,v+4),(3,v+8),(0,v+11),(-3,v+8)],2.8)
    b.prism(unary_union(lines),-2.135,-2.087,lambda x,z,d:(x,-d,z),EDGE,name+'paired ribbons and pendant leaves')

def steps(b,far):
    # The paving disappears behind the left planter. The exact buried end is approximate.
    def course(x0,x1,front,back,z0,z1,radius,material,name):
        radius=min(radius,(back-front)*.88)
        if far: count=3
        else: count=7
        points=[(x0,back),(x1,back),(x1,front+radius)]
        for i in range(1,count+1):
            angle=radians(-90*i/count)
            points.append((x1-radius+radius*cos(angle),front+radius+radius*sin(angle)))
        points.append((x0+radius,front))
        for i in range(1,count+1):
            angle=radians(-90-90*i/count)
            points.append((x0+radius+radius*cos(angle),front+radius+radius*sin(angle)))
        b.prism(Polygon(points),z0,z1,lambda x,y,z:(x,y,z),material,name)
    for i,(left,right,front,top) in enumerate([(-2.84,2.94,-.979,.177),(-2.77,2.72,-.615,.348),(-2.71,2.49,-.433,.523)]):
        base=(0,.177,.348)[i]
        name='Stair '+str(i+1)+' | '
        course(left+.025,right-.025,front+.032,-.29,base,top-.042,.18,RISER,name+'rounded riser')
        course(left,right,front,-.29,top-.042,top,.19,TREAD,name+'projecting stone nosing')

def add_entrance(b,lod=False):
    """Add the surveyed garden entrance and its three stair courses to a house builder."""
    b.palette.update(PALETTE)
    first_part=len(b.parts)
    # The front trims overlap a common casing behind. Real apertures stay open.
    x0,x1,z0,z1=combined_wall_cut()
    body=polygon_box(x0-.008,z0-.009,x1+.008,z1+.008)
    for left,right,top,bottom in ((146,288,257,503),(353,644,238,663),(703,845,257,503)):
        body=body.difference(polygon_box(rect_x(left),rect_z(bottom),rect_x(right),rect_z(top)))
    b.prism(body,-2.463,-2.337,lambda x,z,d:(x,-d,z),PLASTER,'Portal | wall casing with three real openings')
    rect(b,106,882,211,239,2.145,.195,PLASTER,'Portal | continuous head casing')
    for u0,u1 in ((106,137),(848,882)):
        rect(b,u0,u1,237,666,2.163,.189,PLASTER,'Portal | outer wall jambs')
    # The far right side screen is partly hidden by two porch columns in both photographs.
    for shift,side in ((0,'left'),(553,'right')):
        screen(b,shift,side)
    for centre,side in [(323,'left'),(665,'right')]:
        ornaments(b,centre,lod,side)
    rect(b,344,353,237,662,2.151,.195,WOOD,'Portal | left door jamb')
    rect(b,634,645,237,662,2.151,.195,WOOD,'Portal | right door jamb')
    rect(b,353,634,234,242,2.151,.195,WOOD,'Portal | door lintel rebate')
    # Opaque dark stop behind the opening records the photographed shadow only.
    rect(b,353,634,238,663,2.566,.013,SHADOW,'Portal | shadow behind partly open door')
    door_leaf(b,False)
    door_leaf(b,True)
    for u0,u1,v0,v1,y in [(51,937,148,158,1.86),(62,926,158,169,1.90),(74,914,169,177,1.95),
                             (82,906,177,184,1.99),(89,899,184,202,2.065),(95,893,202,212,2.029)]:
        rect(b,u0,u1,v0,v1,y,2.355-y,EDGE if v0 in (148,169,202) else PLASTER,'Portal | six stepped hood courses')
    for u in [92.5+i*13.59 for i in range(60)]:
        rect(b,u,u+8,184,195,2.009,.064,EDGE,'Portal | separate dentil blocks')
    steps(b,lod)
    for part in b.parts[first_part:]:
        material_faces(part)
