"""Street elevations of Young Apartments at Huaihai and Yandang Roads."""
import json
import math
from pathlib import Path

from shapely.geometry import Polygon
from photo_architecture import Facade, opening

PARAMETERS = json.loads(Path(__file__).with_name("parameters.json").read_text())
ARC_START, ARC_END = PARAMETERS["arc_angle_range_deg"]
RADIUS = PARAMETERS["reference_radius_m"]
BRICK = "dark russet brick"
STONE = "warm cast stone"
SASH = "blackened steel sash"
WINDOW = "grey blue plate glass"
TILE = "weathered red roof tile"
RAIL = "black iron railing"
FASCIA = "plain bank fascia"
PALETTE = {
    BRICK: {"color":[.31,.129,.084], "roughness":.88},
    STONE: {"color":[.68,.611,.510], "roughness":.83},
    SASH: {"color":[.102,.103,.090], "roughness":.48,"metallic":.2},
    WINDOW: {"color":[.185,.270,.291], "roughness":.29,"metallic":.3},
    TILE: {"color":[.419,.172,.104], "roughness":.85},
    RAIL: {"color":[.07,.091,.085], "roughness":.48,"metallic":.42},
    FASCIA: {"color":[.48,.46,.416], "roughness":.58},
}


def point(degrees, radius=RADIUS, origin=(0., 0.)):
    angle = math.radians(degrees)
    return (origin[0] + radius*math.sin(angle), origin[1] - radius*math.cos(angle))


def angles(start, end, divisions):
    return [start + (end-start)*i/divisions for i in range(divisions+1)]


def rail_on_arc(builder, start, end, radius, floor, lod, name):
    sections = angles(start, end, max(4, round((end-start)/(14 if lod else 5))))
    for height in (.19, .61, 1.00):
        builder.tube([(*point(a, radius), floor+height) for a in sections], .036 if height<1 else .054,
                     RAIL, 6 if lod else 10, name+"/rolled rails")
    for a in angles(start, end, max(2, round((end-start)/(8 if lod else 2.7)))):
        x,y = point(a,radius)
        builder.tube([(x,y,floor+.07),(x,y,floor+1.)], .026 if lod else .023,
                     RAIL, 6, name+"/balusters")
    if not lod:
        # The original photo shows curled ironwork between the rails above the podium.
        for a in angles(start+3, end-3, max(1, round((end-start)/7))):
            loop = [(*point(a+1.25*math.sin(t),radius),floor+.405+.154*math.cos(t))
                    for t in [math.tau*k/12 for k in range(13)]]
            builder.tube(loop,.020,RAIL,6,name+"/ironwork")


def sector(builder, start, end, inner_radius, outer_radius, lo, hi, material, name, lod):
    ticks = angles(start,end,max(3,round((end-start)/(8 if lod else 3))))
    plan = Polygon([point(a,outer_radius) for a in ticks] +
                   [point(a,inner_radius) for a in reversed(ticks)])
    builder.plan_prism(plan,lo,hi,material,name)


def wall_with_windows(facade, lo, hi, material, rows):
    holes = [opening(u,z,w,h) for u,z,w,h,columns,rails in rows]
    facade.wall(lo,hi,holes,thickness=.36,material=material)
    for k,(shape,(_,_,_,_,columns,rails)) in enumerate(zip(holes,rows)):
        facade.window(shape,columns,rails,frame=SASH,glass=WINDOW,trim=False,label=f"window {k+1}")


def return_end(degrees, length, sign):
    angle = math.radians(degrees)
    x,y = point(degrees)
    return (x+sign*length*math.cos(angle), y+sign*length*math.sin(angle))


def street_frontage():
    left = return_end(ARC_START, PARAMETERS["yandang_return_m"], -1)
    right = return_end(ARC_END, PARAMETERS["huaihai_return_m"], 1)
    return [left] + [point(a) for a in angles(ARC_START,ARC_END,40)] + [right]


def upper_corner(builder,lod):
    # Three glazing bays across the stone central projection. The broad central
    # bay spans the intersection without an extra stone mullion down its centre.
    spans = [ARC_START,-42,-16,16,42,ARC_END]
    for i,(start,end) in enumerate(zip(spans,spans[1:])):
        f = Facade(builder,point(start),point(end),f"rounded intersection/bay {i+1}")
        outer = i in (0,len(spans)-2)
        wide = not outer
        for lo,hi,material,width,columns in [
            (0,3.98,STONE,.74 if wide else .62,2),
            (3.98,7.45,STONE,.72,2),
            (7.45,17.98,BRICK if outer else STONE,.82 if wide else .60,2),
            (17.98,21.86,BRICK,.74,2)]:
            heights = [lo] if lo!=7.45 else PARAMETERS["repeated_balcony_heights_m"]
            rows=[]
            for z in heights:
                sill = .12 if z==0 else (.23 if lo==7.45 else .51)
                height = 3.22 if z==0 else (2.91 if lo==7.45 else 2.71)
                rows.append((0,z+sill,f.length*width,height,3 if start==-16 else columns,2 if lod else 3))
            wall_with_windows(f,lo,hi,material,rows)
    # The lower balcony is continuous; higher ironwork sits within three bays.
    for floor in PARAMETERS["repeated_balcony_heights_m"]:
        arcs = [(-46,46)] if floor==7.45 else [(-42,-16),(-15,15),(16,42)]
        for start,end in arcs:
            name=f"bank arc/balcony at {floor:g} m"
            outer = RADIUS+(.65 if floor==7.45 else .24)
            sector(builder,start,end,RADIUS-.37,outer,floor-.21,floor,STONE,name+"/projecting floor",lod)
            rail_on_arc(builder,start,end,outer-.075,floor,lod,name)
    for degree in (-46,-16,16,46):
        mid=point(degree,RADIUS)
        if abs(degree)==46:
            builder.lathe(mid,[(7.38,.27),(7.55,.31),(7.72,.22),(17.58,.22),
                               (17.71,.28),(17.89,.30)],STONE,10 if lod else 18,"bank arc/tall jamb")
        else:
            for floor in PARAMETERS["repeated_balcony_heights_m"]:
                builder.lathe(mid,[(floor,.29),(floor+.13,.31),(floor+.28,.24),(floor+2.93,.24),
                                   (floor+3.00,.28),(floor+3.14,.33)],STONE,10 if lod else 18,"bank arc/stone pier")
    for lo,hi,outer,mat,name in [(3.13,4.11,.25,FASCIA,"blank sign frieze"),(3.06,3.15,.29,STONE,"shop string"),
        (4.08,4.18,.31,STONE,"shop cornice"),(17.61,17.97,.20,STONE,"wide cornice"),
        (17.97,18.12,.27,STONE,"cornice cap"),(21.31,21.48,.24,STONE,"upper string"),
        (21.54,21.81,.52,STONE,"main eaves"),(21.81,21.89,.57,STONE,"drip")]:
        sector(builder,ARC_START,ARC_END,RADIUS-.30,RADIUS+outer,lo,hi,mat,"bank arc/"+name,lod)
    if not lod:
        for a in angles(ARC_START+3,ARC_END-3,26):
            builder.box((*point(a,RADIUS+.05),21.35),(.18,.47,.28),STONE,label="bank arc/eaves modillions")


def side_wing(builder, start, end, street, lod):
    f=Facade(builder,start,end,street)
    # Windows in the brick bay nearest the arc are narrow. The next group has
    # a shallow balcony, clear in the 2006 façade image and the museum plate.
    width=f.length
    at=[-.255*width,.255*width]
    bank=[(u,.14,.345*width,3.13,3,2) for u in at]
    wall_with_windows(f,0,4.13,STONE,bank)
    for floor,top in [(4.13,7.45),(7.45,10.96),(10.96,14.44),(14.44,17.98),(17.98,21.86)]:
        heights=[(u,floor+.47,.305*width,top-floor-1.,3,2 if lod else 3) for u in at]
        wall_with_windows(f,floor,top,BRICK,heights)
        if floor in PARAMETERS["repeated_balcony_heights_m"]:
            u=at[0] if street=="Yandang Road" else at[1]
            w=width*.35
            f.box(u,floor-.08,w+.20,.16,.86,.25,STONE,"balcony slab")
            for z in (.19,.94):
                f.line((u-w/2,floor+z,.57),(u+w/2,floor+z,.57),.034,RAIL,6,"balcony rails")
                for edge in (u-w/2,u+w/2):
                    f.line((edge,floor+z,.02),(edge,floor+z,.57),.034,RAIL,6,"balcony returns")
            n=6 if lod else 13
            for k in range(n+1):
                v=u-w/2+w*k/n
                f.line((v,floor+.03,.57),(v,floor+.95,.57),.023,RAIL,6,"balcony irons")
    for z,h,proj,mat in [(3.62,.84,.18,FASCIA),(4.13,.13,.27,STONE),(17.98,.14,.13,STONE),
                         (21.48,.15,.24,STONE),(21.74,.26,.53,STONE)]:
        f.beam(z,h,proj,mat,label="street stringcourse")
    if not lod:
        for v in [(-width*.43)+width*.86*k/16 for k in range(17)]:
            f.box(v,21.48,.13,.24,.38,.12,STONE,"cornice modillions")


def roof_pavilion(builder, lod):
    centre = (0.,-.30)
    radius=PARAMETERS["sunroom_radius_m"]
    points=angles(-180,180,14 if lod else 18)
    for i,(a,b) in enumerate(zip(points,points[1:])):
        face=Facade(builder,point(a,radius,centre),point(b,radius,centre),f"sunroom/bay {i+1}")
        wall_with_windows(face,21.88,25.2,BRICK,[(0,22.16,.79*face.length,2.53,2,2 if lod else 3)])
    segments=32 if lod else 72
    builder.lathe(centre,[(21.78,4.79),(21.90,4.88),(22.02,4.75),(22.07,4.61)],STONE,segments,"sunroom/lower skirt")
    builder.lathe(centre,[(25.00,4.67),(25.10,4.88),(25.25,5.04),(25.38,5.04)],STONE,segments,"sunroom/circular cornice")
    builder.lathe(centre,[(25.38,5.11),(25.50,4.93),(26.82,1.55),(26.89,1.42)],TILE,segments,"sunroom/pitched tile roof")
    builder.lathe(centre,[(26.83,1.47),(26.96,1.53),(27.10,1.34),(27.51,1.34),
                          (27.56,1.49),(27.66,1.54)],STONE,segments,"sunroom/raised centre drum")
    builder.lathe(centre,[(27.66,1.58),(27.75,1.53),(28.08,.12)],TILE,segments,"sunroom/upper cap")
    if not lod:
        for a in angles(-180,180,88)[:-1]:
            builder.tube([(*point(a,r,centre),z) for r,z in [(4.98,25.48),(3.08,26.24),(1.56,26.86)]],
                         .035,TILE,6,"sunroom/rolled tile ridges")


def add_young_corner(builder,lod):
    frontage=street_frontage()
    footprint=Polygon(frontage)
    builder.plan_prism(footprint,.015,.14,STONE,"street corner/plinth slab")
    builder.plan_prism(footprint,21.65,21.88,"roof zinc","street corner/flat terrace")
    upper_corner(builder,lod)
    side_wing(builder,frontage[0],frontage[1],"Yandang Road",lod)
    side_wing(builder,frontage[-2],frontage[-1],"Huaihai Road",lod)
    rear=Facade(builder,frontage[-1],frontage[0],"cut to unmodelled street block")
    rear.wall(.14,21.69,material="dark stone",thickness=.18)
    roof_pavilion(builder,lod)
