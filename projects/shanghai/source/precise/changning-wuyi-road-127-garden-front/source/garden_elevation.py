"""South elevation study. Positive Y is the depth of the architectural section."""
import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade

WALL='cream roughcast plaster'
STONE='carved pale stone'
FRAME='ivory painted mullions'
GLASS='blue grey glazing'
ROOF='charcoal ceramic tile'
RIDGE='grey tile laps'
SHADOW='dark grey exterior sill'
PALETTE={
    WALL:{'color':[.884,.837,.676],'roughness':.93},
    STONE:{'color':[.875,.858,.763],'roughness':.78},
    FRAME:{'color':[.795,.789,.708],'roughness':.67},
    GLASS:{'color':[.219,.280,.294],'roughness':.30,'metallic':.12},
    ROOF:{'color':[.223,.230,.240],'roughness':.81},
    RIDGE:{'color':[.284,.287,.285],'roughness':.79},
    SHADOW:{'color':[.320,.328,.320],'roughness':.88},
}


def window(face,x,base,width,height,columns,rows,label,eyebrow=False):
    hole=box(x-width/2,base,x+width/2,base+height)
    face.window(hole,columns,rows,FRAME,False,GLASS,label)
    if eyebrow:
        face.box(x,base+height+.12,width+.40,.11,.22,.065,STONE,label+' moulded drip')
        face.box(x,base+height+.20,width+.52,.07,.26,.10,STONE,label+' crown')
        for side in (-1,1):
            face.box(x+side*(width*.5-.12),base-.20,.18,.21,.23,.04,STONE,label+' sill console')
    return hole


def terrace(builder,start,end,lod,front_posts):
    """Turned balusters are separate solids, so each intervening space stays open."""
    a=np.array(start);b=np.array(end);delta=b-a
    panels=3 if abs(delta[0])>1e-7 else 1
    for i in range(0 if front_posts else 1,panels+1):
        x,y=a+delta*i/panels
        builder.box((x,y,4.32),(.30,.32,.84),STONE,label='Terrace square piers')
        builder.box((x,y,4.76),(.40,.40,.09),STONE,label='Pier cap slab')
    for height,width,thick in ((3.98,.27,.16),(4.70,.24,.105),(4.78,.27,.07)):
        x,y=(a+b)*.5
        size=(abs(delta[0])+width if delta[0] else width,abs(delta[1])+width if delta[1] else width,thick)
        builder.box((x,y,height),size,STONE,label='Terrace rails')
    for panel in range(panels):
        count=6 if panels==3 else 4
        for i in range(count):
            x,y=a+delta*(panel+(i+.5)/count)/panels
            profile=[(4.052,.074),(4.10,.102),(4.16,.097),(4.26,.056),(4.39,.113),
                     (4.475,.102),(4.55,.052),(4.61,.073),(4.65,.084)]
            builder.lathe((x,y),profile,STONE,12 if lod else 20,'Vase-shaped terrace balusters')


def glazed_gallery(builder,lod):
    front_y=-2.55;width=9.12
    front=Facade(builder,(-width/2,front_y),(width/2,front_y),'Three-bay glass gallery')
    bays=[]
    for i,x in enumerate((-3.04,0.,3.04)):
        bays.append(window(front,x,.18,2.66,3.42,4,5,'Garden glazing '+str(i+1)))
    front.wall(.06,3.82,bays,.25,WALL)
    for side in (-1,1):
        x=side*width/2
        ends=((x,0.),(x,front_y))if side==-1 else ((x,front_y),(x,0.))
        sideface=Facade(builder,*ends,'Glazed gallery return')
        hole=window(sideface,0.,.24,2.22,3.34,4,5,'Return glazing')
        sideface.wall(.06,3.82,[hole],.21,WALL)
        terrace(builder,(x,front_y),(x,-.03),lod,False)
    builder.plan_prism(box(-4.64,front_y-.08,4.64,.09),3.69,3.86,STONE,'Terrace fascia')
    builder.plan_prism(box(-4.72,front_y-.14,4.72,.09),3.84,3.94,STONE,'Terrace cap')
    terrace(builder,(-width/2,front_y),(width/2,front_y),lod,True)
    builder.plan_prism(box(-4.62,front_y-.06,4.62,.04),.0,.11,SHADOW,'Gallery base')


def roof(builder,lod):
    """Two photographed roof pitches, bounded at their ridge. Dormers pierce the lower one."""
    half=8.60
    lower=Polygon([(-half,7.07),(half,7.07),(7.72,9.32),(-7.72,9.32)])
    dormers=[(-4.84,2.56,False),(0.,3.21,True),(4.84,2.56,False)]
    def y_at(z):
        return -.24+(z-7.07)*.425
    def project(x,z,d):
        return (x,y_at(z)-d,z)
    for x,width,centre in dormers:
        opening=box(x-width*.5,7.91,x+width*.5,9.04)
        lower=lower.difference(opening)
        y=-.082
        face=Facade(builder,(x-width/2,y),(x+width/2,y),'Pediment dormer' if centre else 'Shed dormer')
        pane=window(face,0.,8.03,width-.52,.90,4,3,'Attic sash')
        face.wall(7.88,9.09,[pane],.14,STONE)
        for edge in (x-width/2,x+width/2):
            vs=[(edge,y,7.88),(edge,y_at(7.88)+.03,7.88),(edge,y_at(9.09)+.04,9.09),(edge,y,9.09)]
            builder.add(vs,[(0,1,2,3)],STONE,'Dormer cheek')
        if centre:
            pediment=Polygon([(-width/2-.08,9.05),(width/2+.08,9.05),(0,9.56)])
            face.prism(pediment,-.21,.035,STONE,'Triangular pediment')
            for end in (-1,1):
                edge=x+end*(width/2+.13)
                builder.add([(x,y-.11,9.62),(edge,y-.11,9.10),(edge,1.02,9.34),(x,1.02,9.68)],[(0,1,2,3)],ROOF,'Pediment roof tiles')
                builder.tube([(x,y-.13,9.59),(edge,y-.13,9.075)],.046,STONE,6 if lod else 10,'Pediment raking mould')
        else:
            builder.add([(x-width/2-.12,y-.10,9.12),(x+width/2+.12,y-.10,9.12),
                         (x+width/2+.12,.87,9.35),(x-width/2-.12,.87,9.35)],[(0,1,2,3)],ROOF,'Shed dormer top')
            face.box(0,9.06,width+.23,.12,.24,.02,STONE,'Dormer head')
    builder.prism(lower,-.065,0,project,ROOF,'Lower tiled mansard')
    # Each tile course terminates at the actual dormer cut, avoiding hidden strip intersections.
    for z in np.linspace(7.14,9.27,10 if lod else 21):
        intersections=lower.intersection(box(-9,z-.009,9,z+.009))
        if not intersections.is_empty:builder.prism(intersections,.005,.029,project,RIDGE,'Mansard tile courses')
    rear_y=3.10;ridge_z=10.30
    builder.add([(-7.72,y_at(9.32),9.32),(7.72,y_at(9.32),9.32),(5.91,rear_y,ridge_z),(-5.91,rear_y,ridge_z)],[(0,1,2,3)],ROOF,'Upper roof pitch')
    for sign in (-1,1):
        vertices=[(sign*half,y_at(7.07),7.07),(sign*7.72,y_at(9.32),9.32),(sign*5.91,rear_y,ridge_z),(sign*half,rear_y,7.07)]
        facets=[(0,1,2),(0,2,3)] if sign<0 else [(2,1,0),(3,2,0)]
        builder.add(vertices,facets,ROOF,'End hip')
        builder.tube(vertices[:3],.048,RIDGE,7 if lod else 10,'Hip tile ridges')
    for t in np.linspace(.08,.94,5 if lod else 11):
        x=7.72+(5.91-7.72)*t;y=y_at(9.32)+(rear_y-y_at(9.32))*t;z=9.32+(ridge_z-9.32)*t
        builder.tube([(-x,y,z+.01),(x,y,z+.01)],.018,RIDGE,5 if lod else 7,'Upper tile laps')
    builder.add([(-half,rear_y,7.07),(half,rear_y,7.07),(5.91,rear_y,ridge_z),(-5.91,rear_y,ridge_z)],[(0,3,2,1)],ROOF,'Closed model section at ridge')
    builder.tube([(-5.91,rear_y,ridge_z),(5.91,rear_y,ridge_z)],.072,RIDGE,8,'Ridge cap')
    for x in (-5.69,5.65):
        builder.box((x,2.69,10.18),(.48,.49,1.22),WALL,label='Two pale chimney stacks')
        builder.box((x,2.69,10.81),(.55,.57,.11),STONE,label='Chimney coping')


def facade(builder,lod):
    south=Facade(builder,(-8.42,0),(8.42,0),'South garden elevation')
    openings=[]
    for i,x in enumerate((-6.49,-2.09,2.09,6.49)):
        openings.append(window(south,x,5.06,1.49,1.54,4,4,'Upper paired casements '+str(i+1)))
    for x in (-6.40,6.40):
        openings.append(window(south,x,.73,2.04,2.50,3,5,'Lower end window',True))
    south.wall(.05,7.12,openings,.32,WALL)
    south.beam(6.94,.19,.29,STONE,label='Bracketed eaves')
    for x in np.linspace(-8.12,8.12,35):
        builder.box((x,-.17,6.73),(.145,.28,.27),STONE,label='Small projecting eaves brackets')
    for x in (-8.15,8.15):
        builder.tube([(x,-.055,.17),(x,-.055,6.48),(x,-.15,6.80)],.052,SHADOW,7 if lod else 11,'Eaves downpipes')
    glazed_gallery(builder,lod)
    roof(builder,lod)
