"""The documented front-wing lightwell and a limited section of the gallery below it."""
import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade, opening
from beijing_front import COURT, ZINC, FRAME, FLOOR, CARVED, STONE, GLAZING, ADDITION, BED, HEIGHT, UPPER_SETBACK
from art_glass import add_skylight

SOFFIT=10.55
HALL='Trust gallery ivory'
HALL_STONE='Trust gallery column stone'
HALL_METAL='Trust lightwell flashing'
HALL_MATERIALS={HALL:{'color':[.81,.807,.768],'roughness':.84},
                HALL_STONE:{'color':[.75,.747,.70],'roughness':.79},
                HALL_METAL:{'color':[.42,.44,.42],'roughness':.63}}

def court_wall(builder,a,b,long_side,lod):
    face=Facade(builder,a,b,'Lightwell')
    holes=[]
    if long_side:
        # Pairs along each side can be seen in the conservation view, while
        # three single windows span the end wall. The opposite side is estimated.
        axes=[(i+.50)*face.length/4-face.length/2+offset for i in range(4)for offset in (-.72,.72)]
    else:
        axes=[f*face.length for f in (-.315,0.,.315)]
    for z0,z1 in ((11.55,14.05),(15.90,18.08),(20.11,22.43)):
        for u in axes:
            width=.83 if long_side else 1.18
            window=opening(u,z0,width,z1-z0)
            holes.append(window)
            face.prism(window.buffer(.018,join_style='mitre'),-.29,-.24,GLAZING,'glass')
            trim=window.buffer(-.017,join_style='mitre')
            pane=trim.buffer(-.051,join_style='mitre')
            cross=box(u-.023,z0,u+.023,z1).union(box(u-width/2,z1-.47,u+width/2,z1-.425))
            if not lod:
                cross=cross.union(box(u-width/2,z0+.59,u+width/2,z0+.625))
            face.prism(trim.difference(pane.difference(cross)),-.18,-.095,FRAME,'steel lightwell frames')
            face.box(u,z0-.068,width+.10,.136,.38,.036,CARVED,'splayed window sill')
    walls=box(-face.length/2,SOFFIT+.28,face.length/2,24.18)
    face.prism(walls.difference(unary_union(holes)),-.34,0,COURT,'open courtyard wall')
    face.box(0,SOFFIT+.31,face.length,.13,.25,-.01,HALL_METAL,'glazing curb flashing')
    face.box(0,24.28,face.length+.032,.20,.36,-.15,CARVED,'courtyard parapet cap')

def point_on_quad(corners,u,v):
    a,b,c,d=np.asarray(corners)
    return (1-v)*((1-u)*a+u*b)+v*((1-u)*d+u*c)

def hall_section(builder,corners,lod):
    poly=Polygon(corners)
    apron=poly.buffer(1.25,join_style='mitre')
    builder.plan_prism(apron,-.04,.10,FLOOR,'Gallery / protected terrazzo floor')
    for edge,(a,b) in enumerate(zip(corners,corners[1:]+corners[:1])):
        face=Facade(builder,b,a,'Gallery')
        inner_border=box(-face.length/2,SOFFIT-.37,face.length/2,SOFFIT+.12)
        face.prism(inner_border,-.55,-.01,HALL,'ceiling surround')
        for high,lo,front in ((SOFFIT-.14,SOFFIT-.20,.05),(SOFFIT-.23,SOFFIT-.30,.09)):
            face.box(0,(high+lo)/2,face.length,high-lo,.25+front,(front-.25)/2,HALL_STONE,'ceiling moulding')
    # Two lines of internal columns follow the photographed long nave. Their
    # precise footprints and the temporary exhibition partitions are unmeasured.
    for side in (-1,1):
        for t in (.09,.36,.65,.91):
            at=point_on_quad(corners, -.072 if side<0 else 1.072,t)
            builder.lathe(at,[(.10,.44),(.22,.44),(.31,.36),(.41,.35),(.48,.30),
                             (SOFFIT-.92,.26),(SOFFIT-.83,.31),(SOFFIT-.77,.32),(SOFFIT-.67,.39)],
                          HALL_STONE,12 if lod else 24,'Gallery / freestanding columns')
            if not lod:
                for j in range(12):
                    p=2*np.pi*j/12;delta=np.array([np.cos(p),np.sin(p)])
                    start=at+delta*.304;end=at+delta*.261
                    builder.tube([(*start,.54),(*end,SOFFIT-.98)],.013,HALL,5,'Gallery / shaft reeds')
            builder.box((*at,SOFFIT-.54),(.88,.84,.27),HALL,label='Gallery / square capitals')
    add_skylight(builder,lod,{'corners':corners,'soffit_z':SOFFIT})

def add_front_wing(builder,plan,lod):
    outer=Polygon(plan['front_wing_xy_m'])
    corners=plan['hall_opening_xy_m']
    court=Polygon(corners)
    # Stop the roof at the seam of the historical front block. The rear wing
    # retains the source city's detail and extent.
    builder.plan_prism(outer.difference(court),23.88,24.06,ZINC,'Front wing / roof around lightwell')
    outside=list(outer.exterior.coords)
    for a,b in zip(outside[1:-1],outside[2:]):
        face=Facade(builder,a,b,'Front wing')
        face.prism(box(-face.length/2,0,face.length/2,24.06),-.29,0,STONE,'perimeter return')
    # Only the street band of the 1990s addition is specified by our sources.
    # At the northern cut the open original lightwell remains visible.
    addition=outer.intersection(box(-8,UPPER_SETBACK,30,6.65))
    builder.plan_prism(addition,HEIGHT-.27,HEIGHT-.13,ZINC,'Addition / street roof')
    for a,b in zip(addition.exterior.coords,list(addition.exterior.coords)[1:]):
        if max(a[1],b[1])<UPPER_SETBACK+.04:continue
        face=Facade(builder,a,b,'Addition')
        face.prism(box(-face.length/2,24.05,face.length/2,HEIGHT-.13),-.15,.15,ADDITION,'limited return')
    for idx in range(4):
        # Reversed edge normal faces into the opening.
        court_wall(builder,corners[(idx+1)%4],corners[idx],idx in (1,3),lod)
    hall_section(builder,corners,lod)
