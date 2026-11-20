"""Two photographed faces of the protected office at 639/643 Huashan Road."""
from math import ceil, cos, pi, sin
from shapely.geometry import Polygon, box
from photo_architecture import Facade, opening

WALL='warm off-white plaster'
TRIM='pale stone trim'
WOOD='cream painted sash'
GLASS='blue-grey recessed glazing'
FRAME='dark timber entrance'
TILE='weathered red clay roof'
DARK='dark metal flashings'
IRON='slender black iron rail'
FLOOR='terracotta gallery paving'
PALETTE={
    WALL:{'color':[.77,.738,.662],'roughness':.88},
    TRIM:{'color':[.72,.696,.633],'roughness':.84},
    WOOD:{'color':[.784,.764,.692],'roughness':.68},
    GLASS:{'color':[.22,.273,.286],'roughness':.32,'metallic':.22},
    FRAME:{'color':[.224,.176,.120],'roughness':.71},
    TILE:{'color':[.54,.283,.203],'roughness':.85},
    DARK:{'color':[.25,.242,.210],'roughness':.54,'metallic':.37},
    IRON:{'color':[.176,.174,.146],'roughness':.54,'metallic':.56},
    FLOOR:{'color':[.577,.306,.230],'roughness':.82},
}
# +X follows Huashan Road southwest, +Y faces the southeast lawn.
LEFT, RIGHT = -14.55, 14.55
GATE, GARDEN = -6.0, 3.80


def hip(builder, x0, x1, y0, y1, eave, rise, name):
    depth=y1-y0
    inset=min(depth*.45,(x1-x0)*.35)
    mid=(y0+y1)/2
    vertices=[(x0,y0,eave),(x1,y0,eave),(x1,y1,eave),(x0,y1,eave),
              (x0+inset,mid,eave+rise),(x1-inset,mid,eave+rise)]
    builder.add(vertices,[(0,1,5,4),(1,2,5),(2,3,4,5),(3,0,4)],TILE,name+'/hips')
    builder.tube([vertices[4],vertices[5]],.060,TILE,7,name+'/ridge')
    for i,j in [(0,1),(1,2),(2,3),(3,0)]:
        builder.tube([vertices[i],vertices[j]],.055,DARK,6,name+'/gutter')


def glazed(face, centre, sill, width, height, lod, *,door=False):
    hole=box(centre-width/2,sill,centre+width/2,sill+height)
    frame=FRAME if door else WOOD
    face.window(hole,columns=2 if lod else (4 if width>2.6 else 3),
                rows=3 if lod else 5,frame=frame,glass=GLASS,trim=False,label='multi-light sash')
    face.prism(hole.buffer(.085,join_style=2).difference(hole),-.025,.07,WOOD,'plaster window casing')
    return hole


def house_faces(builder,lod):
    road=Facade(builder,(LEFT,GATE),(RIGHT,GATE),'Huashan Road elevation')
    garden=Facade(builder,(RIGHT,GARDEN),(LEFT,GARDEN),'lawn gallery rooms')
    road_holes=[];garden_holes=[]
    for z,h in [(1.00,2.55),(4.65,2.99)]:
        for x in [-11.90,-8.49,-5.16,-1.72,1.72,5.16,8.49,11.90]:
            road_holes.append(glazed(road,x,z,2.12,h,lod))
        for u in [-11.7,-7.2,-2.55,2.40,7.12,11.7]:
            wide=u in [-2.55,7.12]
            garden_holes.append(glazed(garden,u,z if not wide else z-.50,
                                        2.86 if wide else 1.48,h+(.50 if wide else 0),lod,door=wide and z<2))
    for face,holes in [(road,road_holes),(garden,garden_holes)]:
        face.wall(0,8.12,holes,material=WALL)
        face.beam(.26,.38,.24,TRIM)
        face.beam(4.23,.21,.24,TRIM)
        face.beam(8.04,.23,.38,TRIM)
    for a,b in [((LEFT,GARDEN),(LEFT,GATE)),((RIGHT,GATE),(RIGHT,GARDEN))]:
        end=Facade(builder,a,b,'return wall')
        holes=[glazed(end,x,z,1.64,h,lod) for z,h in [(1,2.51),(4.71,2.82)] for x in [-2.60,.02,2.64]]
        end.wall(0,8.10,holes,material=WALL)
        end.beam(4.23,.17,.19,TRIM)
    builder.plan_prism(box(LEFT,GATE,RIGHT,GARDEN),.02,.27,TRIM,'office plinth')


def roadside_porch(builder,lod):
    half=3.08;outer=-9.05
    ring=[(-half,outer),(half,outer),(half,GATE),(-half,GATE)]
    for i in [0,1,3]:
        a,b=ring[i],ring[(i+1)%4]
        f=Facade(builder,a,b,'street entrance porch')
        width=2.88 if i==0 else 1.97
        portal=opening(0,.06,width,3.54,.90,9 if lod else 17)
        f.wall(.06,5.86,[portal],thickness=.42,material=WALL)
        coping=portal.buffer(.14,join_style=2).difference(portal).intersection(box(-half,.06,half,5.86))
        f.prism(coping,-.025,.09,TRIM,'arched portal coping')
        f.beam(4.65,.13,.21,TRIM)
        f.beam(5.82,.22,.33,TRIM)
        if i==0:
            for x in [-.52,.52]:
                f.prism(box(x-.34,5.01,x+.34,5.46),.005,.015,DARK,'attic vent')
    back=Facade(builder,(-half,GATE-.15),(half,GATE-.15),'inset office door')
    door=box(-1.09,.28,1.09,3.37)
    back.prism(door,0,.09,FRAME,'recessed double door')
    back.prism(box(-.82,1.51,.82,3.03),.10,.11,GLASS,'door glazing')
    back.box(0,2.28,.10,1.59,.07,.12,FRAME,'middle stile')
    builder.plan_prism(Polygon(ring),.02,.23,FLOOR,'porch paving')
    hip(builder,-3.35,3.35,outer-.28,GATE+.34,5.98,1.74,'porch red roof')


def gallery_rail(builder,a,b,z,lod):
    dx,dy=b[0]-a[0],b[1]-a[1];length=(dx*dx+dy*dy)**.5
    for h in [.13,.98]:
        builder.tube([(a[0],a[1],z+h),(b[0],b[1],z+h)],.044,IRON,6,'gallery horizontal rails')
    repeat=max(2,ceil(length/(.62 if lod else .33)))
    for j in range(repeat):
        for sign in [-1,1]:
            count=4 if lod else 8
            curve=[]
            for i in range(count+1):
                t=i/count;u=(j+.5+.41*sign*sin(pi*t))/repeat
                curve.append((a[0]+u*dx,a[1]+u*dy,z+.14+.83*t))
            builder.tube(curve,.019,IRON,5,'bent balcony baluster')


def garden_veranda(builder,lod):
    # The straight double-height loggia turns around the east (left) end.
    arc=[(-9.70-5.0*cos(t*pi/2/10),3.35+4.05*sin(t*pi/2/10)) for t in range(11)]
    outline=[*arc,(13.78,7.40),(13.78,3.62),(-14.70,3.35)]
    floor=Polygon(outline)
    for z,t,mat in [(.09,.22,FLOOR),(4.03,.27,TRIM),(8.00,.30,TRIM)]:
        builder.plan_prism(floor,z,z+t,mat,'double-level lawn veranda')
    for x,y in [arc[0],arc[5],arc[-1],(-4.70,7.17),(.10,7.17),(4.90,7.17),(9.68,7.17),(13.44,7.17)]:
        builder.box((x,y,4.17),(.51,.54,7.97),WALL,label='full-height square gallery pillar')
        builder.box((x,y,8.00),(.65,.67,.23),TRIM,label='square pillar cap')
    outer=[*arc,(13.59,7.40)]
    for a,b in zip(outer,outer[1:]):
        gallery_rail(builder,a,b,4.30,lod)
    for a,b in zip(arc,arc[1:]):
        gallery_rail(builder,a,b,8.30,lod)


def attic(builder,lod):
    hip(builder,LEFT-.32,RIGHT+.32,GATE-.32,6.65,8.21,3.71,'main clay-tile roof')
    # The street face has a long glazed dormer. Three unequal hipped
    # projections look across the lawn in the current and archival images.
    for x,y,w,d,garden in [(0,-4.41,18.70,3.45,False),(-8.20,4.74,4.32,3.28,True),
                             (-.55,4.71,8.15,3.16,True),(8.21,4.71,4.31,3.25,True)]:
        z=8.72;h=1.91
        a,b=((x+w/2,y),(x-w/2,y)) if garden else ((x-w/2,y),(x+w/2,y))
        f=Facade(builder,a,b,'hipped attic sash')
        count=5 if w>12 else (2 if w>6 else 1)
        band=w/count
        holes=[glazed(f,band*(i-(count-1)/2),z+.18,min(band*.71,2.65),1.38,lod) for i in range(count)]
        f.wall(z,z+h,holes,thickness=.21,material=WALL)
        inner=y-d if garden else y+d
        for edge in [a,b]:
            xs=edge[0]
            builder.box((xs,(y+inner)/2,z+h/2),(.22,d,h),WALL,label='attic return')
        hip(builder,x-w/2-.19,x+w/2+.19,min(y,inner)-.22,max(y,inner)+.22,z+h,1.10,'attic caps')


def add_building(builder,lod):
    house_faces(builder,lod)
    roadside_porch(builder,lod)
    garden_veranda(builder,lod)
    attic(builder,lod)
