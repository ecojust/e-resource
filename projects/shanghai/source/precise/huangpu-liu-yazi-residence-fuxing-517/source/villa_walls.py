"""Walls and openings traced on Wutopia Lab's three occupied-floor plans.

Coordinates below are readings in the 1380-pixel study copies of the drawings.
North and west facade coordinates run against the plan X and Y axes.
"""
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade
from villa_materials import BASE, BRICK, DARK, ROUGH, SILL, STONE
from villa_windows import casement, glazed_opening, round_attic
from villa_roof import HALF_WALL as W, HALF_DEPTH as D, GABLE_WALL_SECTIONS, ROOF_SKIN, roof_z

PLAN_SCALE = .0200067
GALLERY_HALF = 3.48
GALLERY_FRONT = -7.13
PATIO_BACK = -3.42

# A pair stores the two jamb pixels exactly as read on the corresponding facade.
NORTH = (
    [(675,720),(773,821),(948,993)],
    [(328,393),(696,739),(960,1006)],
    [(283,351),(540,583),(696,739),(866,917),(985,1053)],
)
EAST = ([(417,462)], [(417,482)], [(455,506)])
WEST = ([(355,398),(528,573)], [(536,604)], [(509,570)])


def aperture(face, stations, lod, side):
    holes = []
    # A dimensioned plan fixes each width. The photographed lintels/section fix sills and heads.
    heights = ((.66,2.14),(3.98,6.11),(7.51,9.64))
    for level,(jambs,(sill,head)) in enumerate(zip(stations,heights)):
        for index,(a,b) in enumerate(jambs):
            pixels=(a+b)/2
            if side=='north':
                centre=(668-pixels)*PLAN_SCALE
            else:
                centre=(538-pixels)*PLAN_SCALE*(1 if side=='east' else -1)
            width=(b-a)*PLAN_SCALE
            opening=glazed_opening(centre,sill,width,head-sill)
            holes.append(opening)
            closed=(side=='east' and level==2) or (side=='north' and level==2 and index==4)
            leaves=() if level==0 else (-1,1)
            casement(face,opening,lod,f'{side} floor {level+1} bay {index+1}',
                     shutters=leaves,closed=closed)
    return holes


def gable_outline(north):
    west=list(GABLE_WALL_SECTIONS['west'])
    east=list(GABLE_WALL_SECTIONS['east'])
    if north:
        # The centre meets the descending rear roof plane where it intersects the
        # two inner pitches. Only its actual breaks belong in the exterior wall.
        from villa_roof import BACK_PITCH, HIGH, RIDGE_Y, SLOPE, WING, WING_PEAK
        z=HIGH-(D-RIDGE_Y)*BACK_PITCH
        inner=WING-(WING_PEAK-z)/SLOPE
        samples=[*west[:2],(-inner,z-ROOF_SKIN),(inner,z-ROOF_SKIN),*east[1:]]
    else:
        samples=west+east
    top=[(x,z+.015) for x,z in reversed(samples)]
    return Polygon([(-W,0),(W,0),*top])


def wall_shell(builder,lod,entry_cut):
    south=Facade(builder,(-W,-D),(W,-D),'garden double gable')
    north=Facade(builder,(W,D),(-W,D),'Fuxing Road double gable')
    east=Facade(builder,(W,-D),(W,D),'east entrance elevation')
    west=Facade(builder,(-W,D),(-W,-D),'west elevation')
    north_holes=aperture(north,NORTH,lod,'north')
    east_holes=aperture(east,EAST,lod,'east')+[entry_cut]
    west_holes=aperture(west,WEST,lod,'west')
    south_holes=[box(-GALLERY_HALF,-.1,GALLERY_HALF,14.0)]
    for face,holes in ((south,south_holes),(north,north_holes)):
        for x in (-6.13,6.13):
            holes.append(round_attic(face,x,11.57,lod,'attic round vent'))
    for x in (-6.12,6.12):
        for level,sill,height,arch in ((2,3.80,2.09,.31),(3,7.61,1.95,0)):
            shape=glazed_opening(x,sill,2.12,height,arch,lod)
            south_holes.append(shape)
            casement(south,shape,lod,'garden wing floor '+str(level),
                     cols=3,shutters=(-1,1) if level==3 else (),closed=(x<0 and level==3))
    for a,b in ((900,943),(1006,1048)):
        shape=glazed_opening(((a+b)/2-668)*PLAN_SCALE,.54,(b-a)*PLAN_SCALE,1.53)
        south_holes.append(shape)
        casement(south,shape,lod,'east wing ground window')
    # This wing wall is inside the projecting ground-floor study.
    south_holes.append(box(-7.82,0,-GALLERY_HALF,2.86))
    for face,holes in ((south,south_holes),(north,north_holes)):
        face.wall(0,14,holes,.26,ROUGH,gable_outline(face is north))
    z=roof_z(W,0)-ROOF_SKIN+.012
    for face,holes in ((east,east_holes),(west,west_holes)):
        face.wall(0,z,holes,.24,ROUGH)
        for low,high,depth,mat in [(2.50,2.59,.10,BRICK),(2.61,2.67,.13,BRICK)]:
            line=box(-D,low,D,high).difference(unary_union(holes))
            face.prism(line,-.025,depth,mat,'brick belt at first floor')
    # The entrance crosses the second-floor datum. Leave its internal stairwell genuinely clear.
    for z in (.03,3.01,6.92):
        floor=box(-W+.10,-D+.10,W-.10,D-.10)
        floor=floor.difference(box(-GALLERY_HALF-.01,-D-.1,GALLERY_HALF+.01,PATIO_BACK)) if z<.1 else floor
        if z==3.01:floor=floor.difference(box(5.08,3.43,W+.1,4.95))
        builder.prism(floor,z-.10,z,lambda x,y,h:(x,y,h),SILL,'villa floor slabs')
    return south,east,north


def garden_gallery(builder,lod):
    h=GALLERY_HALF
    front=Facade(builder,(-h,GALLERY_FRONT),(h,GALLERY_FRONT),'garden projecting glazed gallery')
    holes=[box(-h+.27,-.1,-.34,2.64),box(.34,-.1,h-.27,2.64)]
    for lev,sill,head in ((2,3.69,6.17),(3,7.51,9.75)):
        for x in (-1.72,1.72):
            shape=glazed_opening(x,sill,2.66,head-sill)
            holes.append(shape)
            casement(front,shape,lod,'garden gallery floor '+str(lev),cols=8,stone_sill=False)
    front.wall(0,10.30,holes,.27,ROUGH)
    for side in (-1,1):
        x=side*h
        a,b=((x,GALLERY_FRONT),(x,-D)) if side==1 else ((x,-D),(x,GALLERY_FRONT))
        ret=Facade(builder,a,b,'gallery side return')
        voids=[box(-ret.length/2+.20,-.1,ret.length/2-.11,2.60)]
        if side==-1:
            entrance=glazed_opening(0,3.01,.92,2.30)
            voids.append(entrance)
            casement(ret,entrance,lod,'entrance from garden stair',stone_sill=False)
        ret.wall(0,10.30,voids,.22,ROUGH)
    # The ground-floor photo looks through the two front bays to the sheltered bookshop.
    recessed=Facade(builder,(-h,PATIO_BACK),(h,PATIO_BACK),'recessed flower porch')
    patio=[]
    for x in (-2.06,0,2.06):
        sh=glazed_opening(x,.12,1.46,2.30)
        patio.append(sh);casement(recessed,sh,lod,'porch recessed glazed doors',cols=3,stone_sill=False)
    recessed.wall(0,3.01,patio,.22,ROUGH)
    for x in (-h,h):
        builder.box((x,(PATIO_BACK-D)/2,1.44),(.22,PATIO_BACK+D,2.88),ROUGH,label='flower porch deep returns')
    # Light-grey exterior flags extend to the set-back ground-floor doors.
    # Only the covered porch receives this surface; the estate grounds are separate.
    width=2*h-.14
    depth=PATIO_BACK-GALLERY_FRONT
    builder.box((0,(PATIO_BACK+GALLERY_FRONT)/2,.014),(width,depth,.073),BASE,label='flower porch stone bedding')
    cols,rows=(5,3) if lod else (10,6)
    for i in range(cols):
        for j in range(rows):
            x=-width/2+(i+.5)*width/cols
            y=GALLERY_FRONT+(j+.5)*depth/rows
            mat=STONE if (i+2*j)%5==1 else SILL
            builder.box((x,y,.055),(width/cols-.011,depth/rows-.009,.020),mat,label='flower porch garden paving')
    front.box(0,.084,2*h,.128,.36,-.045,SILL,'garden porch threshold')
    for z,height,depth,mat in [(2.77,.18,.20,STONE),(2.92,.09,.27,SILL),(6.46,.12,.13,SILL),
                               (6.56,.16,.22,STONE),(6.67,.07,.28,SILL),
                               (10.06,.13,.15,STONE),(10.18,.14,.23,STONE),(10.29,.09,.31,SILL)]:
        front.box(0,z,2*h+.33,height,depth+.15,.025,mat,'gallery cornice profile')
        for side in (-1,1):
            builder.box((side*(h+.03),(GALLERY_FRONT-D)/2,z),
                        (depth+.15,-D-GALLERY_FRONT+.16,height),mat,label='gallery cornice returns')
    for i in range(13):
        front.box(-3.20+i*6.40/12,9.96,.092,.13,.22,.066,STONE,'upper cornice corbels')
    for z in (2.99,6.90):
        builder.box((0,(GALLERY_FRONT-D)/2,z-.08),(2*h,-D-GALLERY_FRONT+.12,.16),SILL,label='gallery storey slabs')


def west_study(builder,lod):
    # On plan 44 the study door opens into the flower porch. Its garden wall
    # follows the stair stringer. Plan 45 shows the flight rises east to the gallery.
    left,right,front=-8.51,-GALLERY_HALF,-7.14
    depth=-D-front
    length=right-left
    f=Facade(builder,(left,front),(right,front),'garden stair and study')
    tread=length/17
    plate=[(-length/2,0),(length/2,0)]
    for i in reversed(range(17)):
        z=(i+1)*3.01/17
        plate.extend([(-length/2+(i+1)*tread,z),(-length/2+i*tread,z)])
    f.prism(Polygon(plate),-.18,0,ROUGH,'stepped study wall under stringer')
    for i in range(17):
        z=(i+1)*3.01/17
        x=left+(i+.5)*tread
        builder.box((x,front+depth/2,z-.052),(tread+.025,depth+.05,.104),SILL,label='south outdoor straight stair')
        if i:
            builder.box((x-tread/2,front+depth/2,z-.112),(.075,depth,.148),SILL,label='garden stair risers')
    y=front+.092
    builder.tube([(left+.11,y,1.04),(right-.15,y,3.88)],.028,'Blackened iron',6 if lod else 10,'south stair handrail')
    for i in range(0,17,2):
        x=left+(i+.5)*tread;z=(i+1)*3.01/17
        builder.tube([(x,y,z),(x,y,z+.86)],.019,'Blackened iron',6,'south stair iron uprights')
    # A genuine doorway below the landing connects the low study and the flower porch.
    side=Facade(builder,(right,front),(right,-D),'study entrance from porch')
    sh=glazed_opening(0,.10,.85,2.16)
    side.wall(0,2.79,[sh],.16,ROUGH)
    casement(side,sh,lod,'study door',stone_sill=False)
