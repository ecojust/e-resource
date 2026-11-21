"""Photo-based courtyard gallery and split-level entrance at 1634 Huaihai Middle Road."""
from math import cos, hypot, pi, sin
from shapely.geometry import box
from photo_architecture import Facade

PLASTER = 'ivory painted stucco'
TRIM = 'lime painted column moulding'
BASE = 'grey plinth'
STONE = 'pink granitic stair'
WOOD = 'brown timber joinery'
GLASS = 'dark blue grey glazing'
IRON = 'black floral cast iron'
TILE = 'burnt red flat tiles'
RIDGE = 'terracotta ridge and rolls'
FASCIA = 'dark eave edge'
BRASS = 'aged metal fittings'
PLAQUE = 'grey metal register plaque'
MATERIALS = {
    PLASTER: ((.88,.86,.80),.88), TRIM: ((.95,.93,.87),.85),
    BASE: ((.47,.46,.44),.92), STONE: ((.66,.55,.49),.83),
    WOOD: ((.32,.20,.132),.68), GLASS: ((.258,.303,.311),.30),
    IRON: ((.115,.12,.12),.55), TILE: ((.58,.26,.157),.91),
    RIDGE: ((.48,.205,.13),.90), FASCIA: ((.265,.205,.16),.80),
    BRASS: ((.6,.49,.28),.46), PLAQUE: ((.58,.59,.58),.63)}
PALETTE = {n:{'color':list(c),'roughness':r} for n,(c,r) in MATERIALS.items()}
# Survey axes. +X is approximately east-northeast and +Y north-northwest.
GALLERY_FLOOR = 1.04
DOOR_FLOOR = 1.86
EAVE = 5.38


def wall(b, a, c, z0, z1, openings, name):
    face = Facade(b, a, c, name)
    holes = []
    for u, sill, width, height, kind in openings:
        cut = box(u-width/2, sill, u+width/2, sill+height)
        holes.append(cut)
        if kind == 'window':
            face.window(cut, columns=2, rows=2, trim=False, glass=GLASS, frame=WOOD, label='timber casement')
            # Use the photographed short painted sill in place of the general stone sill.
            b.parts.pop()
            face.box(u,sill-.052,width+.14,.10,.29,-.055,TRIM,'painted sill')
        else:
            face.prism(cut.buffer(.01,join_style=2),-.27,-.23,WOOD,'recessed timber door')
            inside = cut.buffer(-.10,join_style=2)
            face.prism(cut.difference(inside),-.20,-.10,WOOD,'door casing')
            double = kind == 'double'
            leaves = [u-width/4,u+width/4] if double else [u]
            if double:
                face.box(u,sill+height/2,.025,height-.1,.06,-.19,FASCIA,'meeting stile')
            for mid in leaves:
                leaf = width/len(leaves)-.18
                if double:
                    face.box(mid,sill+height*.68,leaf*.75,height*.32,.025,-.20,GLASS,'upper glazed panel')
                for level in ([.21] if double else [.24,.67]):
                    panel = box(mid-leaf*.37,sill+height*(level-.135),mid+leaf*.37,sill+height*(level+.135))
                    face.prism(panel.difference(panel.buffer(-.025,join_style=2)),-.23,-.19,WOOD,'raised door panel')
                side = 1 if mid<=u else -1
                face.line((mid+side*leaf*.42,sill+.91,-.16),(mid+side*leaf*.42,sill+1.04,-.16),.014,BRASS,8,'handle')
    face.wall(z0,z1,holes,thickness=.30,material=PLASTER)
    return face


def hip_roof(b, rect, base, rise, lod, label):
    x0,y0,x1,y1 = rect
    w, d = x1-x0, y1-y0
    short = min(w,d)/2
    c = [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
    if w>=d:
        r0,r1=(x0+short,(y0+y1)/2),(x1-short,(y0+y1)/2)
        faces = [(0,1,5,4),(1,2,5),(2,3,4,5),(3,0,4)]
    else:
        r0,r1=((x0+x1)/2,y0+short),((x0+x1)/2,y1-short)
        faces = [(0,1,4),(1,2,5,4),(2,3,5),(3,0,4,5)]
    vertices = [(x,y,base) for x,y in c]+[(*r0,base+rise),(*r1,base+rise)]
    b.add(vertices,[*faces,(3,2,1,0)],TILE,label+' hip roof')
    b.plan_prism(box(*rect),base-.17,base-.01,FASCIA,label+' eave edge')
    # Parallel courses follow the actual pitch; each fillet stops at a hip.
    count = max(3,round(short/(.66 if lod else .32)))
    for i in range(1,count):
        run=i*short/count
        v=base+rise*run/short+.009
        corners=[(x0+run,y0+run,v),(x1-run,y0+run,v),(x1-run,y1-run,v),(x0+run,y1-run,v)]
        for a,c1 in zip(corners,corners[1:]+corners[:1]):
            b.tube([a,c1],.022 if lod else .029,RIDGE,4 if lod else 6,label+' tile course')
    for start,end in ((0,4),(1,5 if w>=d else 4),(2,5),(3,4 if w>=d else 5),(4,5)):
        b.tube([vertices[start],vertices[end]],.066,RIDGE,6 if lod else 9,label+' hip or ridge')


def railing(b,a,c,lod):
    dx,dy=c[0]-a[0],c[1]-a[1];length=hypot(dx,dy)
    def pt(u,z):
        return (a[0]+dx*u/length,a[1]+dy*u/length,GALLERY_FLOOR+z)
    for z in (.13,.81,.94):
        b.tube([pt(0,z),pt(length,z)],.023,IRON,6,'gallery horizontal rail')
    bays=max(1,round(length/.49))
    for k in range(bays):
        mid=length*(k+.5)/bays
        b.tube([pt(mid,.11),pt(mid,.91)],.018,IRON,5,'gallery floral stem')
        radius=min(.112,length/bays*.24)
        for sign in (-1,1):
            for center in ([.51] if lod else [.35,.64]):
                path=[]
                for j in range(9 if lod else 15):
                    ang=1.95*pi*j/(8 if lod else 14)
                    path.append(pt(mid+sign*radius*(1-cos(ang)),center+.105*sin(ang)))
                b.tube(path,.014,IRON,4,'gallery paired iron loop')


def column(b,x,y):
    for lo,hi,side,mat,label in [(1.04,1.15,.63,BASE,'base plinth'),(1.15,1.24,.56,TRIM,'column base'),
            (1.24,1.40,.51,TRIM,'moulding'),(1.40,4.91,.425,PLASTER,'square shaft'),
            (4.91,5.00,.48,TRIM,'neck'),(5.0,5.11,.54,TRIM,'capital'),(5.11,EAVE,.62,TRIM,'abacus')]:
        b.box((x,y,(lo+hi)/2),(side,side,hi-lo),mat,label='gallery '+label)


def entrance_stair(b,lod):
    y0,y1=-.06,2.28
    foot,top=9.53,6.49
    n=11
    for k in range(n):
        right=foot-(foot-top)*k/n
        left=foot-(foot-top)*(k+1)/n
        z=DOOR_FLOOR*(k+1)/n
        b.plan_prism(box(left,y0,right,y1),0,z,STONE,'rising granite tread')
        if not lod:
            b.box((right-.02,(y0+y1)/2,z-.024),(.05,y1-y0+.025,.046),STONE,label='rounded tread nosing')
    for y in (y0-.11,y1+.11):
        for k in range(0,n+1,1 if not lod else 2):
            t=k/n; x=foot+(top-foot)*t
            z=DOOR_FLOOR*min(k+1,n)/n
            if k==0:
                b.box((x,y,.49),(.29,.30,.98),STONE,label='square stair newel')
                b.lathe((x,y),[(.96,.098),(1.02,.118),(1.09,.119),(1.16,.085),(1.19,.025)],STONE,14 if not lod else 8,label='ball finial')
            else:
                b.lathe((x,y),[(z,.052),(z+.12,.072),(z+.22,.044),(z+.50,.046),(z+.65,.071),(z+.78,.054)],STONE,10 if not lod else 6,label='turned stone baluster')
        b.tube([(foot,y,.94),(top,y,DOOR_FLOOR+.84)],.085,STONE,12 if not lod else 7,'sloping stone handrail')


def add_building(b,lod):
    # Courtyard-facing portion only. The roof and the walls stop at the section boundary.
    b.plan_prism(box(-4.72,-12.20,9.22,-3.55),0,GALLERY_FLOOR,BASE,'raised south gallery platform')
    b.plan_prism(box(-4.72,-3.55,6.49,6.12),0,DOOR_FLOOR,BASE,'split-level foundation')
    b.plan_prism(box(6.44,2.68,9.22,6.12),0,.16,BASE,'lower service entry footing')
    wall(b,(-4.43,-9.69),(6.87,-9.69),GALLERY_FLOOR,EAVE,[
        (-3.53,1.11,1.06,2.66,'double'),(.14,1.11,1.16,2.66,'double'),(3.82,1.49,1.05,2.44,'window')],'recessed south wall')
    wall(b,(6.87,-9.69),(6.87,-4.78),GALLERY_FLOOR,EAVE,[(-.51,1.53,1.16,2.44,'window')],'porch return')
    wall(b,(6.87,-4.78),(9.21,-4.78),GALLERY_FLOOR,EAVE,[],'window bay return')
    wall(b,(9.21,-4.78),(9.21,-2.48),0,EAVE,[(0,1.55,1.2,2.46,'window')],'projecting casement bay')
    wall(b,(9.21,-2.48),(6.49,-2.48),0,EAVE,[(0,1.62,1.1,2.32,'window')],'door recess south wall')
    wall(b,(6.49,-2.48),(6.49,2.68),DOOR_FLOOR,EAVE,[(.95,DOOR_FLOOR,1.65,2.43,'double')],'landing behind staircase')
    wall(b,(6.49,2.68),(9.22,2.68),0,5.68,[],'north side of landing')
    service=wall(b,(9.22,2.68),(9.22,6.12),0,5.68,[
        (-.77,.10,.88,2.08,'single'),(.92,.68,.62,1.23,'window'),(.36,3.14,.83,1.84,'window')],'lower entrance and bedroom')
    service.box(-1.37,1.81,.38,.24,.035,.025,PLAQUE,'metal register plaque')
    service.beam(2.67,.11,.13,TRIM)
    wall(b,(9.22,6.12),(-4.43,6.12),0,EAVE,[],'northern surveyed section')
    wall(b,(-4.43,6.12),(-4.43,-9.69),0,EAVE,[],'western surveyed section')
    front=[(-4.38,-11.91),(-.01,-11.91),(4.46,-11.91),(8.93,-11.91)]
    side=[front[-1],(8.93,-8.61),(8.93,-5.10)]
    for x,y in front+side[1:]:
        column(b,x,y)
    for points in (front,side):
        for a,c in zip(points,points[1:]):
            length=hypot(c[0]-a[0],c[1]-a[1]);offset=.229/length
            railing(b,tuple(a[i]+(c[i]-a[i])*offset for i in (0,1)),
                    tuple(c[i]+(a[i]-c[i])*offset for i in (0,1)),lod)
    b.box((2.3,-11.91,5.20),(13.94,.42,.36),TRIM,label='southern architrave')
    b.box((8.93,-8.46,5.20),(.42,7.33,.36),TRIM,label='eastern architrave')
    entrance_stair(b,lod)
    hip_roof(b,(-4.87,-12.38,9.46,-3.41),EAVE+.18,1.68,lod,'south gallery')
    hip_roof(b,(-4.87,-3.37,6.79,6.26),EAVE+.18,1.77,lod,'inner wing')
    hip_roof(b,(6.82,2.50,9.49,6.26),5.83,.65,lod,'service projection')
    # The roof over the entrance falls outwards between the two hipped roofs.
    deck=[(6.67,-3.41,6.13),(9.44,-3.41,5.53),(9.44,2.50,5.53),(6.67,2.50,6.13)]
    # Close the triangular return between the pitched connector and the two
    # adjoining eaves. Its narrow cut face is painted plaster in the court.
    lower=[(x,y,z-.13) for x,y,z in deck]
    infill=[(x,y,5.28) for x,y,z in deck]
    b.add(lower+infill,[(0,1,2,3),(7,6,5,4),(4,5,1,0),(5,6,2,1),(6,7,3,2),(7,4,0,3)],
          PLASTER,'filled return where landing and gallery roofs join')
    b.add(deck+lower,[(0,1,2,3),(7,6,5,4),(4,5,1,0),(5,6,2,1),(6,7,3,2),(7,4,0,3)],
          TILE,'sloping red tile roof over landing')
    for k in range(1,6 if not lod else 4):
        f=k/(6 if not lod else 4)
        x=6.67+2.77*f
        z=6.147-.60*f
        b.tube([(x,-3.40,z),(x,2.49,z)],.024,RIDGE,5,'landing roof course')
    b.tube([(9.37,-4.86,5.50),(9.25,-4.86,5.26),(9.25,-4.86,.95),
            (9.31,-4.86,.72),(9.31,-4.86,.22)],.052,FASCIA,8,'courtyard downpipe')
    for x in (-2.2,2.18,6.62):
        b.tube([(x,-10.89,5.33),(x,-10.89,4.93)],.018,IRON,6,'porch pendant drop')
        b.lathe((x,-10.89),[(4.73,.09),(4.80,.19),(4.84,.22),(4.87,.13),(4.94,.051)],
                BRASS,12 if lod else 18,label='porch pendant bowl')
