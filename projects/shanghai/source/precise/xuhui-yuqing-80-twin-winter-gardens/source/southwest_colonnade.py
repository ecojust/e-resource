"""Open southwest ground-floor porch of the Yuqing Road garden elevation."""
from math import cos, pi, sin
from pathlib import Path
import json
import sys

import numpy as np
from shapely.geometry import Polygon, box

MEASUREMENTS = Path(__file__).resolve().parents[1] / 'measurements'
sys.path.insert(0, str(MEASUREMENTS))
from register_garden import Camera

WALL = 'Garden | cream roughcast'
WHITE = 'Garden | warm white column'
TERRACE = 'Garden | weathered terrace'
COPING = 'Garden | pale edged concrete'
WOOD = 'Garden | walnut door joinery'
PANEL = 'Garden | inset hardwood panels'
RECESS = 'Garden | shaded doorway interior'
HANDLE = 'Garden | patinated door hardware'
STONE = 'Garden | dark porch threshold'
PALETTE = {
    WALL: dict(color=[.82, .79, .70], roughness=.96),
    WHITE: dict(color=[.87, .85, .76], roughness=.87),
    COPING: dict(color=[.84,.83,.75], roughness=.88),
    TERRACE: dict(color=[.61, .59, .53], roughness=.90),
    WOOD: dict(color=[.113, .059, .031], roughness=.75),
    PANEL: dict(color=[.159, .089, .045], roughness=.77),
    RECESS: dict(color=[.011,.010,.009], roughness=1.),
    HANDLE: dict(color=[.108, .095, .073], roughness=.51, metallic=.44),
    STONE: dict(color=[.148, .142, .12], roughness=.88),
}


def curved_opening(front, back, spring, rise, base, count):
    middle = (front+back)*.5
    radius = (back-front)*.5
    perimeter = [(front,base),(back,base)]
    perimeter.extend((middle+radius*cos(angle), spring+rise*sin(angle))
                     for angle in np.linspace(0,pi,count+1))
    return Polygon(perimeter)


def add_wooden_door(builder, left, right, back_y, head, lod):
    """Recessed frame and separately hinged two-leaf panel door shown in Gao 6."""
    label = 'SW porch | timber double door'
    def front_panel(poly,y0,y1,material,name):
        builder.prism(poly,-y1,-y0,lambda x,z,d:(x,-d,z),material,label+' | '+name)

    # The partially open leaf shows a dark interior in 6. These short dark returns
    # close the observed recess at the clearance of one leaf; they do not define a room.
    depth = .91
    width = right-left
    back = back_y+depth+.018
    builder.box(((left+right)*.5,back,head*.5),(width,.036,head),RECESS,
                label=label+' | shadow behind open leaf')
    for jamb,x in [('west',left+.012),('east',right-.012)]:
        builder.box((x,back_y+(depth+.18)*.5,head*.5),(.024,depth-.18,head),RECESS,
                    label=label+' | short '+jamb+' dark reveal')
    builder.box(((left+right)*.5,back_y+(depth+.18)*.5,head-.012),(width,depth-.18,.024),RECESS,
                label=label+' | inner soffit')
    frame = .070
    inner = box(left+frame,.025,right-frame,head-frame)
    shell = box(left,0,right,head).difference(box(left+frame,-.10,right-frame,head-frame))
    front_panel(shell,back_y+.026,back_y+.162,WOOD,'recessed square head and jambs')
    front_panel(box(left,.002,right,.025),back_y-.075,back_y+.26,STONE,'dark threshold')
    leaf_w = (inner.bounds[2]-inner.bounds[0])*.5-.008
    leaf_h = head-frame-.029
    for side,hinge_x,hand,angle in [('left',left+frame+.002,1,0),
                                    ('right',right-frame-.002,-1,37*pi/180)]:
        ux,uy = hand*cos(angle),sin(angle)
        # Handed local axes leave the outer face toward the garden on both leaves.
        normal = np.array([sin(angle)*hand,-cos(angle)])
        hinge_y = back_y+.136
        def leaf(poly,inner_depth,outer_depth,mat,name):
            def mapper(u,v,d):
                return (hinge_x+u*ux+normal[0]*d,hinge_y+u*uy+normal[1]*d,.029+v)
            if hand == 1:
                builder.prism(poly,inner_depth,outer_depth,mapper,mat,label+' | '+side+' | '+name)
            else:
                builder.prism(poly,-outer_depth,-inner_depth,
                              lambda u,v,d:mapper(u,v,-d),mat,label+' | '+side+' | '+name)
        leaf(box(0,0,leaf_w,leaf_h),-.041,-.014,WOOD,'leaf')
        # Two narrow panels on each of three rows and a single broad kick panel.
        openings=[]
        openings.append(box(.075,.105,leaf_w-.075,.238*leaf_h))
        for row in range(3):
            lo = (.274 + .223*row)*leaf_h
            hi = (.464 + .223*row)*leaf_h
            for a,c in ((.075,leaf_w*.5-.027),(leaf_w*.5+.027,leaf_w-.075)):
                openings.append(box(a,lo,c,hi))
        skin = box(0,0,leaf_w,leaf_h)
        for opening in openings:
            skin=skin.difference(opening)
        leaf(skin,-.015,.014,WOOD,'stiles and rails')
        for n,opening in enumerate(openings,1):
            leaf(opening.buffer(-.004,join_style=2),-.013,-.007,PANEL,f'recessed panel {n}')
            if not lod:
                rebate=opening.difference(opening.buffer(-.017,join_style=2))
                leaf(rebate,-.012,.004,WOOD,f'panel bevel {n}')
        handle_u=leaf_w-.06
        handle_point=np.array([hinge_x+handle_u*ux,hinge_y+handle_u*uy])+.036*normal
        builder.tube([(*handle_point,.99),(*handle_point,1.094)],.014,HANDLE,
                    7 if lod else 12,label+' | '+side+' pull')


def add_southwest_colonnade(builder,lod=False):
    """Build the porch up to the registered middle-floor underside. Deck level is zero."""
    for key,value in PALETTE.items():
        builder.palette.setdefault(key,value)
    source=json.loads((MEASUREMENTS/'southwest-court-sections.json').read_bytes())
    camera=Camera(6)
    anchors=camera.data['shared_colonnade_xyz']
    roof=camera.data['middle_slab_underside_z']
    base=0.
    # The rounded part ends at Y=0. In 6 its ceiling remains unbroken as it
    # reaches the rectangular rear wall. The central bridge only covers X>=cx.
    cx=camera.data['centres_m']['SW']
    rear=source['back_y']+.19
    radius=camera.data['midfloor_radii_m']['SW']
    closure=box(cx-radius,-.006,cx,rear)
    builder.prism(closure,roof,roof+.15,lambda x,y,z:(x,y,z),COPING,
                  'SW porch | flat soffit return from semicircle to back wall')
    for key,name in [('west_capital','west end'),('inner_capital','inner end')]:
        x,y=anchors[key][:2]
        builder.tube([(x,y,base),(x,y,roof+.006)],source['radii'][key],WHITE,
                    18 if lod else 48,'SW porch | plain white round post | '+name)

    arch_x=source['arch_x']
    back_y=source['back_y']
    xmin=source['back_wall_left_x']
    front_y=source['arch_wall_front_y']
    controls=json.loads((MEASUREMENTS/'southwest-court-photo-controls.json').read_bytes())
    corners=np.array([camera.wall(p,back_y) for p in controls['controls_raw_pixels']['6']['wood_frame']])
    left,right=corners[[0,3],0].mean(),corners[[1,2],0].mean()
    head=corners[:2,2].mean()
    blank=box(xmin,base,camera.data['centres_m']['SW']+camera.data['outer_radii_m']['SW']-.10,roof)
    aperture=box(left,-.10,right,head)
    builder.prism(blank.difference(aperture),-back_y-.19,-back_y,lambda x,z,d:(x,-d,z),
                  WALL,'SW porch | back wall with timber door opening')
    add_wooden_door(builder,left,right,back_y,head,lod)
    front,back = source['arch_jamb_y']
    spring=source['arch_spring_z']
    rise=anchors['arch_crown'][2]-spring
    n=20 if lod else 46
    opening=curved_opening(front,back,spring,rise,-.08,n)
    trim=source['arch_band']
    outer=curved_opening(front-trim,back+trim,spring,rise+trim,-.08,n)
    field=box(front_y,base,back_y,roof)
    # Wall, raised architrave and reveal are distinct closed members; the aperture stays open.
    yz=lambda y,z,x:(x,y,z)
    thickness=source['arch_wall_thickness']
    builder.prism(field.difference(outer),arch_x,arch_x+thickness,yz,WALL,
                  'SW porch | return with full-depth arched passage')
    builder.prism(outer.difference(opening).intersection(field),arch_x-.012,
                  arch_x+thickness+.012,yz,WHITE,'SW porch | radiused white arch and jambs')

    # The square-edged landing and two lower treads descend toward the garden.
    x0,x1 = source['platform_x']
    nose=source['platform_front_y']
    terrace=box(x0,nose,x1,back_y+.18)
    builder.prism(terrace,-.42,0.,lambda x,y,z:(x,y,z),TERRACE,'SW porch | raised landing')
    for step in (1,2):
        back_edge=nose-(step-1)*source['tread_run']
        rectangle=box(x0,back_edge-source['tread_run'],x1,back_edge)
        builder.prism(rectangle,-.42,-.14*step,lambda x,y,z:(x,y,z),TERRACE,
                      f'SW porch | garden stair tread {step}')
