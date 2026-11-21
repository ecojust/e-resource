"""Seven-storey Brookside Apartments. Ground coordinates follow the registered garden and street wings."""
from math import atan2, tan
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade, opening

PLASTER = 'cream mineral render'
STONE = 'pale limestone moulding'
FRAME = 'dark painted steel window'
GLASS = 'desaturated blue grey glass'
IRON = 'dark iron balcony rail'
DOOR = 'brown garden entrance door'
ROOF = 'weathered dark flat roof'
COPING = 'aged red-brown roof tiles'
VENT = 'cement chimney cap'
PALETTE = {name:{'color':color,'roughness':roughness} for name,color,roughness in (
    (PLASTER,[.80,.76,.64],.91),(STONE,[.68,.66,.56],.86),(FRAME,[.18,.22,.22],.65),
    (GLASS,[.24,.31,.31],.34),(IRON,[.19,.20,.18],.64),(DOOR,[.30,.18,.14],.82),
    (ROOF,[.27,.275,.265],.89),(COPING,[.39,.295,.23],.91),(VENT,[.63,.60,.54],.90))}
RING = [(35.4983,-1.3336),(29.7244,-6.8492),(19.3102,3.3944),(-1.8277,3.3944),
        (-26.1672,-23.6404),(-33.4306,-16.6970),(-6.7892,12.2216),(23.7176,12.6518),(33.5164,3.7137)]
LEVELS = [1.38,4.71,8.04,11.37,14.70,18.03,21.36]
ROOF_SURFACE = 24.84


def joined(face, bottom, top, holes, left=0, right=0, outline=None):
    start=len(face.builder.parts)
    face.wall(bottom,top,holes,thickness=.32,material=PLASTER,outline=outline)
    for part in face.builder.parts[start:]:
        vertices=[]
        for vertex in part['vertices']:
            offset=vertex-face.center
            u,depth=offset@face.t,offset@face.n
            shift = 0.0
            if abs(u+face.length/2)<1e-6:
                shift = -depth*left
            elif abs(u-face.length/2)<1e-6:
                shift = depth*right
            vertices.append(tuple(vertex+shift*face.t))
        part['vertices']=vertices


def sash(face, u, bottom, width, height, lod, columns=2, material=GLASS, arch=0):
    shape=opening(u,bottom,width,height,arch,10 if lod else 20)
    grid_columns = min(columns, 1 if width<=1.65 else 2) if lod else columns
    face.window(shape, columns=grid_columns, rows=1 if lod else 3, frame=FRAME, glass=material, trim=False)
    # The shared default projects 0.40 m. The photographed mineral sill is almost flush.
    default_sill = face.builder.parts[-1]
    assert default_sill['label'].endswith('window-sill')
    face.builder.parts.pop()
    if not lod or width>1.65:
        face.box(u,bottom-.045,width+.08,.09,.14,.015,STONE,'mineral sill')
    return shape


def iron_rail(face,u,bottom,width,lod):
    for z in (.18,.86):
        face.box(u,bottom+z,width,.048,.058,.23,IRON,'balcony handrail')
    for j in range(5 if lod else 11):
        n=5 if lod else 11
        face.box(u+((j+.5)/n-.5)*width,bottom+.52,.034,.65,.04,.23,IRON,'balcony bars')


def diamond_openings(u, z, columns, spacing=.25):
    cutouts=[]
    for row in range(2):
        count=columns-row
        for col in range(count):
            x=u+(col-(count-1)/2)*spacing
            h=z-row*.145
            cutouts.append(Polygon([(x-.057,h),(x,h-.081),(x+.057,h),(x,h+.081)]))
    return cutouts


def pierced_balustrade(face, u, z, width):
    frame=box(u-width/2,z-.29,u+width/2,z+.29)
    holes=diamond_openings(u,z+.085,10)
    face.prism(frame.difference(unary_union(holes)),.32,.445,STONE,'garden pierced balcony')
    face.box(u,z-.32,width+.11,.11,.57,.145,STONE,'balcony slab')


def bay_face(face,u,lod):
    """Garden oriel with a flat middle, two splayed cheeks and a projecting base."""
    span,half_span,depth=1.27,.81,.68
    local=[(u-span,0),(u-half_span,depth),(u+half_span,depth),(u+span,0)]
    world=[tuple(face.point(x,0,d)[:2])for x,d in local]
    solid=Polygon([*world,tuple(face.point(u+span,0,-.16)[:2]),tuple(face.point(u-span,0,-.16)[:2])])
    low,high=10.90,20.72
    # Upper and lower balconies are expressed in the window treatment; the seven-storey core is continuous behind.
    for a,b in zip(world,world[1:]):
        wall=Facade(face.builder,a,b,'garden splayed bay')
        holes=[]
        for z in LEVELS[3:6]:
            holes.append(sash(wall,0,z+.45,wall.length-.17,1.85,lod,columns=2 if wall.length>1 else 1))
        joined(wall,low,high,holes)
    face.builder.plan_prism(solid,low-.16,low+.02,STONE,'oriel corbel slab')
    face.builder.plan_prism(solid,high-.03,high+.16,STONE,'oriel weather cap')
    return box(u-span+.02,low+.02,u+span-.02,high-.02)


def garden_core(face,lod,left,right):
    holes=[]
    for i,z in enumerate(LEVELS):
        if i==0:
            holes.append(sash(face,0,.84,1.36,2.35,lod,columns=2,material=DOOR,arch=.21))
        else:
            holes.append(sash(face,0,z+.44,1.12,1.91 if i<5 else 1.57,lod))
        for sign in (-1,1):
            # A broad group on each side of the narrow entrance axis; some apartments have exterior rails.
            u=sign*4.55
            for dx in (-1.00,0.,1.00):
                holes.append(sash(face,u+dx,z+.42,.81,1.84,lod,columns=1 if lod else 2))
            if i in (4,6):
                pierced_balustrade(face,u,z-.07,3.12)
            outer=sign*8.12
            if i not in (3,4,5):
                holes.append(sash(face,outer,z+.43,1.54,1.79,lod))
    for u in (-8.12,8.12):holes.append(bay_face(face,u,lod))
    joined(face,.08,ROOF_SURFACE+.08,holes,left,right)
    for z,w,h in ((3.48,1.97,.13),(3.62,1.77,.08)):
        face.box(0,z,w,h,.35,.075,STONE,'garden entrance lintel')
    for i in range(5):
        projection=1.50-i*.25
        face.box(0,.085+i*.143,2.10,.16,projection,-.02+projection/2,STONE,'garden entrance step')
    # A pediment over the taller middle arch, three open arches to either side and lower arcades beyond.
    line=[(-face.length/2,ROOF_SURFACE),(-face.length/2,26.30),(-6.00,26.30),(-6.00,27.30),
          (-1.52,27.30),(-1.52,28.40),(0,28.90),(1.52,28.40),(1.52,27.30),(6.00,27.30),(6.00,26.30),
          (face.length/2,26.30),(face.length/2,ROOF_SURFACE)]
    cap=Polygon(line);portals=[]
    for u in (-9.81,-8.53,-7.25,7.25,8.53,9.81):
        portals.append(opening(u,ROOF_SURFACE+.17,1.06,.99,.30,9 if lod else 20))
    for u in (-5.16,-3.67,-2.18,2.18,3.67,5.16):
        portals.append(opening(u,ROOF_SURFACE+.69,1.22,1.54,.58,9 if lod else 22))
    portals.append(opening(0,ROOF_SURFACE+.68,1.48,1.67,.66,10 if lod else 22))
    for u in (-3.75,0.,3.75):
        portals.extend(diamond_openings(u,25.29,7))
    face.prism(cap.difference(unary_union(portals)),-.36,0,PLASTER,'garden open roof arcade')
    # Four small geometric marks are visible on the raised centre of the 2023 crest.
    for u,z,w,h in ((0.,28.47,.075,.31),(0.,28.04,.075,.22),(-.17,28.24,.20,.060),(.17,28.24,.20,.060)):
        face.box(u,z,w,h,.072,.043,STONE,'central crest relief')
    for u,z,w in ((-8.28,26.29,4.53),(8.28,26.29,4.53),(-3.76,27.29,4.50),(3.76,27.29,4.50)):
        face.box(u,z,w,.11,.47,.015,COPING,'arcade coping')
    face.box(0,24.88,face.length+.12,.14,.47,.01,STONE,'garden cornice')


def garden_wing(face,lod,left,right,bays):
    holes=[]
    for i,z in enumerate(LEVELS):
        for j in range(bays):
            u=face.length*((j+.5)/bays-.5)
            width=(1.25,1.53,1.12,1.74,1.48)[j%5]
            h=sash(face,u,z+.46,width,1.82,lod,columns=2 if width<1.6 or lod else 3)
            holes.append(h)
            if i in (2,4,5) and j%4==1:
                face.box(u,z+.30,width+.18,.14,.43,.12,STONE,'shallow balcony ledge')
                iron_rail(face,u,z+.37,width+.12,lod)
    joined(face,.08,ROOF_SURFACE+.47,holes,left,right)
    face.box(0,ROOF_SURFACE+.42,face.length,.11,.41,.015,STONE,'wing parapet coping')


def road_wall(face,lod,left,right,bays):
    holes=[]
    for j in range(bays):
        u=face.length*((j+.5)/bays-.5)
        for i,z in enumerate(LEVELS):
            w=(1.02,1.32,1.48,1.11)[j%4]
            holes.append(sash(face,u,z+.55,w,1.68,lod,columns=2))
    joined(face,.08,ROOF_SURFACE+.53,holes,left,right)
    face.box(0,ROOF_SURFACE+.51,face.length,.11,.40,.015,STONE,'street parapet coping')


def turn(prev,here,nxt):
    ax,ay=here[0]-prev[0],here[1]-prev[1]
    bx,by=nxt[0]-here[0],nxt[1]-here[1]
    return tan(atan2(ax*by-ay*bx,ax*bx+ay*by)/2)


def add_building(builder,lod=False):
    builder.plan_prism(Polygon(RING).buffer(-.035),.035,.20,PLASTER,'continuous apartment plinth')
    builder.plan_prism(Polygon(RING),24.49,ROOF_SURFACE,ROOF,'dark flat roof')
    # Native polygon order is clockwise; exterior openings face out along its reversed walk.
    for j in range(9):
        k=(j-1)%9
        a,b=RING[j],RING[k]
        left=turn(RING[(j+1)%9],a,b);right=turn(a,b,RING[(k-1)%9])
        wall=Facade(builder,a,b,'garden middle' if j==3 else f'exterior {j}')
        if j==3:garden_core(wall,lod,left,right)
        elif j in (4,2):garden_wing(wall,lod,left,right,12 if j==4 else 5)
        else:road_wall(wall,lod,left,right,max(2,round(wall.length/3.03)))
    for edge,fractions in ((4,[.10,.32,.55,.83]),(3,[.16,.69]),(2,[.46]),(0,[.40])):
        f=Facade(builder,RING[edge],RING[(edge-1)%9],'roof service')
        for j,t in enumerate(fractions):
            u=f.length*(t-.5);x,y=f.point(u,0,-3.68)[:2];z=26.05+(j%2)*.22
            builder.box((x,y,(z+ROOF_SURFACE)/2),(.80,.68,z-ROOF_SURFACE),PLASTER,label='roof chimney')
            builder.box((x,y,z+.07),(.92,.80,.16),VENT,label='chimney cap')
    # The 2019 image shows a compact set of flat-roofed service spaces behind the central upper arcade.
    for x,y,w,d,h in ((2.75,9.40,4.55,2.65,1.43),(10.18,10.32,2.52,2.23,2.04),(17.46,9.87,4.28,2.44,1.23)):
        builder.box((x,y,ROOF_SURFACE+h/2),(w,d,h),PLASTER,label='setback roof room')
        builder.box((x,y,ROOF_SURFACE+h+.075),(w+.22,d+.21,.15),COPING,label='roof room cap')
