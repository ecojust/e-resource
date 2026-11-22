"""Model the two-storey south iron gallery of the Qiuxin Shipyard office.

The surveyed south edge supplies the width. The envelope follows the implemented
pitched-roof option. Curls and leaf detail are original simplified castings.
"""
from math import cos, sin, pi
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade

HALF = 10.4955
BACK = 17.90
WALL = 2.38
DECK = 4.52
EAVE = 8.85
RIDGE = 11.14
STATIONS = tuple(-10.24 + 20.48 * i / 5 for i in range(6))
BRICK = 'orange red wall brick'
IRON = 'graphite cast iron'
TRIM = 'oxblood eave timber'
FRAME = 'deep red sash'
GLASS = 'recessed smoky glass'
BOARD = 'warm gallery boards'
STONE = 'weathered grey stone'
SOFFIT = 'pale gallery ceiling'
ROOF = 'brown clay roof'
FLASH = 'weathered ridge flashing'
SIDE = 'weathered side brick'
CLAY = ['warm vermilion brick', 'muted cinnamon brick', 'weathered russet brick']
PALETTE = {
    BRICK: {'color':[.40,.177,.104], 'roughness':.89},
    SIDE: {'color':[.36,.308,.267], 'roughness':.90},
    CLAY[0]: {'color':[.44,.187,.103], 'roughness':.9},
    CLAY[1]: {'color':[.385,.158,.094], 'roughness':.88},
    CLAY[2]: {'color':[.43,.202,.133], 'roughness':.89},
    IRON: {'color':[.09,.091,.085], 'roughness':.52, 'metallic':.58},
    TRIM: {'color':[.39,.116,.093], 'roughness':.7},
    FRAME: {'color':[.25,.078,.058], 'roughness':.62},
    GLASS: {'color':[.15,.209,.217], 'metallic':.12,'roughness':.28},
    BOARD: {'color':[.41,.221,.145], 'roughness':.75},
    STONE: {'color':[.42,.411,.369], 'roughness':.84},
    SOFFIT: {'color':[.71,.682,.619], 'roughness':.77},
    ROOF: {'color':[.353,.245,.189], 'roughness':.9},
    FLASH: {'color':[.23,.214,.198], 'roughness':.76},
}


def solid(builder, front, back, material, group):
    n=len(front)
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces.extend((i,(i+1)%n,(i+1)%n+n,i+n)for i in range(n))
    builder.add(front+back,faces,material,group)


def roof_and_shell(b,lod):
    # Cross-section ordering supplies exterior single-sided normals on both gables.
    yz=[(WALL,8.51),(BACK,8.51),(BACK,8.81),(9.05,RIDGE),(WALL,9.39)]
    left=[(-HALF,y,z)for y,z in yz]
    right=[(HALF,y,z)for y,z in yz]
    solid(b,left,right,BRICK,'Gable end envelope')
    edge=[(-.12,EAVE),(9.05,RIDGE),(BACK+.10,8.81)]
    for i,((y0,z0),(y1,z1)) in enumerate(zip(edge,edge[1:])):
        low=[(-HALF-.07,y0,z0-.15),(HALF+.07,y0,z0-.15),
             (HALF+.07,y1,z1-.15),(-HALF-.07,y1,z1-.15)]
        solid(b,low,[(x,y,z+.15)for x,y,z in low],ROOF,'South roof pitch' if i==0 else 'North roof pitch')
    b.box((0,9.05,RIDGE+.025),(2*HALF+.20,.15,.08),FLASH,label='Roof ridge cap')
    for i,x in enumerate([-4.92,3.67]):
        for a,sz,z in [(ROOF,(.77,.65,1.33),10.83),(BRICK,(.89,.78,.11),11.54),
                       (STONE,(.98,.85,.10),11.645)]:
            b.box((x,5.20,z),sz,a,label=f'Chimney {i+1} masonry')
    # Rear plaster and side returns close the volume. Historic openings are added
    # only along the photographed south face and eastern end of that face.
    b.box((0,BACK-.13,4.31),(2*HALF,.26,8.62),BRICK,label='Rear envelope')
    b.box((-HALF+.13,(WALL+BACK)/2,4.31),(.26,BACK-WALL,8.62),BRICK,label='West return envelope')
    east=Facade(b,(HALF,WALL),(HALF,BACK),'East return')
    returns=[(-6.5,1.02,1.10,2.04),(-4.13,1.03,1.07,1.99),(-1.78,1.05,1.01,1.98)]
    openings=[box(x-w/2,z,x+w/2,z+h)for x,z,w,h in returns]
    upper=[box(x-w/2,5.18,x+w/2,7.37)for x,z,w,h in returns]
    east.wall(0,8.63,openings+upper,thickness=.24,material=SIDE)
    for shape in openings+upper:
        sash(east,shape,lod)
    for x,z,w,h in returns:
        for head in (z+h,7.37):
            curve=[(x+(w*.5+.11)*cos(pi*k/12),head+.088+.115*sin(pi*k/12))for k in range(13)]
            outer=[(x+(w*.5+.22)*cos(pi*k/12),head+.083+.228*sin(pi*k/12))for k in reversed(range(13))]
            east.prism(Polygon(curve+outer),-.014,.068,BRICK,'Segmental brick side hood')
    for z in (1.15,4.35,5.38,8.24):
        east.box(0,z,BACK-WALL-.06,.105,.103,.018,BRICK,'Side brick stringcourse')
    b.box((0,BACK/2,.095),(2*HALF,BACK,.19),STONE,label='Ground plinth')


def sash(wall,shape,lod):
    x0,z0,x1,z1=shape.bounds
    wall.prism(shape.buffer(.012,join_style=2),-.21,-.19,GLASS,'Recessed glass')
    inside=shape.buffer(-.075,join_style=2)
    x=(x0+x1)/2
    bars=[box(x-.030,z0,x+.030,z1),box(x0,z1-.59,x1,z1-.53)]
    panes=inside.difference(unary_union(bars))
    wall.prism(shape.buffer(-.013,join_style=2).difference(panes),-.145,-.072,FRAME,'Transomed sash')
    if not lod:
        wall.box(x,z1+.046,x1-x0+.10,.086,.135,.036,FRAME,'Sash head')
    wall.box(x,z0-.04,x1-x0+.13,.075,.16,.033,STONE,'Stone sill')


def gallery_wall(b,lod):
    wall=Facade(b,(-HALF,WALL),(HALF,WALL),'South wall')
    # Window centres are approximate where branches cover adjacent sashes in the
    # 2015 front view. These are tall rectangular transomed joinery inside the porch.
    xs=(-8.66,-6.25,-3.83,-1.45,.96,3.38,5.84,8.58)
    holes=[]
    for i,x in enumerate(xs):
        for base,head in [(0.42 if i in (1,6) else .84,3.48),(4.78,7.71)]:
            w=1.25 if i in (1,6) else 1.15
            holes.append(box(x-w/2,base,x+w/2,head))
    wall.wall(.19,8.63,holes,thickness=.26,material=BRICK)
    for hole in holes:
        sash(wall,hole,lod)
    if lod:return
    # Each tile is a visible, outward-facing south skin over the intact structural
    # wall. Rows clear all cut openings so grazing views show the deep reveals.
    frames=[f.bounds for f in holes]
    groups=[([],[])for _ in CLAY]
    h=.099; length=.324
    for row in range(84):
        z0=.24+h*row;z1=z0+h-.012
        for col in range(-35,35):
            x0=max(-HALF+.015,col*length + (row%2)*length/2)
            x1=min(HALF-.015,(col+1)*length + (row%2)*length/2-.012)
            if x1-x0<.035:continue
            if any(x0<e+.02 and x1>a-.02 and z0<f+.02 and z1>c-.02 for a,c,e,f in frames):continue
            vs,fs=groups[(col*31+row*13+row*col)%3];start=len(vs)
            vs.extend([(x0,WALL-.005,z0),(x1,WALL-.005,z0),(x1,WALL-.005,z1),(x0,WALL-.005,z1)])
            fs.append((start,start+1,start+2,start+3))
    for i,(vs,fs) in enumerate(groups):
        b.add(vs,fs,CLAY[i],'South running bond '+str(i+1))


def support(b,x,y,base,top,lod):
    high=top-base
    profile=[(base,.15),(base+.08,.15),(base+.141,.116),(base+.21,.094),
             (base+high*.19,.088),(top-.46,.062),(top-.40,.102),(top-.36,.087),
             (top-.24,.109),(top-.13,.152),(top-.091,.154),(top-.06,.13)]
    b.lathe((x,y),profile,IRON,8 if lod else 14,'Cast column shafts')
    b.box((x,y,top-.035),(.31,.28,.07),IRON,label='Capital abacus')
    if lod:return
    for k in range(6):
        t=pi*k/3;near=(x+.09*cos(t),y+.09*sin(t),top-.37)
        lower=(x+.125*cos(t),y+.125*sin(t),top-.27)
        outer=(x+.147*cos(t),y+.147*sin(t),top-.16)
        b.tube([near,lower,outer],.022,IRON,5,'Capitals folded leaves')


def filigree(b,left,right,z,lod):
    span=right-left
    # A stem descends at each capital. The open area between stems and leaf loops
    # remains transparent in the two GLBs.
    for hand,anchor in [(1,left),(-1,right)]:
        def pt(t,drop=0):
            u=t*span*.49
            return (anchor+hand*u,.075,z-(.56*(1-t)**2+.12+drop))
        b.tube([pt(t/n)for n in [5 if lod else 9]for t in range(n+1)],.032,IRON,5,'Branched iron spandrels')
        if lod:continue
        for k in range(7):
            u=.008+.13*k
            b.tube([pt(u,-.005),pt(u+.045,.07),pt(u+.10,.085),pt(u+.13,.025),pt(u+.095,-.028)],
                   .018,IRON,4,'Open leaf casting')
            b.tube([pt(u+.07,.01),pt(u+.125,-.07),pt(u+.18,-.10)],.016,IRON,4,'Small leaf stems')
            # Closed, tapered lobes fill the spandrel under the fascia while
            # retaining open sky between the original mesh strands.
            arc=[pt(u+.066+.051*cos(2*pi*j/9),-.09+.054*sin(2*pi*j/9))for j in range(10)]
            b.tube(arc,.014,IRON,5,'Open acanthus lobes')
        second=[(anchor+hand*span*.49*j/8,.08,z-.13-.16*(1-j/8)**2)for j in range(9)]
        b.tube(second,.021,IRON,5,'Upper iron scroll stem')
    b.box(((left+right)/2,.075,z-.057),(span,.087,.105),IRON,label='Cast head beam')


def rail(b,x0,x1,y,base,lod,return_x=None):
    span=x1-x0
    def point(u,z):
        return (u,y,z) if return_x is None else (return_x,u,z)
    def rod(vertices,radius,material,sides,label):
        b.tube([point(v[0],v[2])for v in vertices],radius,material,sides,label)

    for z,r,m in [(base+.1,.024,IRON),(base+.91,.038,TRIM)]:
        rod([(x0,y,z),(x1,y,z)],r,m,6,'Gallery rail')
    cells=8 if return_x is None else 5
    for i in range(cells+1):
        x=x0+span*i/cells
        rod([(x,y,base+.10),(x,y,base+.90)],.020,IRON,5,'Vertical rail bars')
        if i==cells:break
        center=x+span/cells/2
        if lod:
            rod([(center-.12,y,base+.24),(center+.09,y,base+.48),(center-.11,y,base+.73)],.017,IRON,4,'Gallery baluster scrolls')
        else:
            for sign in [-1,1]:
                s=.10*sign
                pts=[(center-s*.9,y,base+.17),(center-s*1.7,y,base+.26),(center-s*1.6,y,base+.38),
                     (center-s*.6,y,base+.44),(center+s*.45,y,base+.53),(center+s*.8,y,base+.64),
                     (center+s*.22,y,base+.72),(center-s*.36,y,base+.66)]
                rounded=[pts[0]]
                for v0,v1 in zip(pts,pts[1:]):
                    rounded.extend([tuple(.76*a+.24*b for a,b in zip(v0,v1)),tuple(.24*a+.76*b for a,b in zip(v0,v1))])
                rounded.append(pts[-1])
                rod(rounded,.016,IRON,5,'Gallery baluster scrolls')


def floor_edges(b,lod):
    b.box((0,WALL/2,DECK-.12),(2*HALF+.08,WALL+.11,.24),SOFFIT,label='Balcony slab and soffit')
    b.box((0,WALL/2,DECK+.012),(2*HALF+.05,WALL+.06,.024),BOARD,label='Balcony wood deck')
    b.box((0,WALL/2,EAVE-.20),(2*HALF+.08,WALL+.10,.13),SOFFIT,label='Upper porch soffit')
    for z in [DECK-.16,EAVE-.12]:
        b.box((0,-.017,z),(2*HALF+.20,.20,.25),TRIM,label='Red gallery fascia')
        b.box((0,-.086,z+.114),(2*HALF+.23,.175,.052),TRIM,label='Fascia upper bead')
        if not lod:
            n=117
            for i in range(n):
                x=-HALF+(i+.5)*2*HALF/n
                if z<EAVE-1:
                    p=Polygon([(x-.078,z-.102),(x,z-.203),(x+.078,z-.102)])
                    b.prism(p,-.012,.04,lambda u,v,q:(u,-.111-q,v),TRIM,'Sawtooth balcony valance')
                else:
                    b.box((x,-.107,z-.015),(.092,.096,.087),TRIM,label='Upper cornice dentils')
    if not lod:
        for i in range(1,15):
            b.box((0,WALL*i/15,DECK+.026),(2*HALF-.08,.009,.007),TRIM,label='Wood deck joints')


def add_veranda(builder,lod):
    roof_and_shell(builder,lod)
    gallery_wall(builder,lod)
    floor_edges(builder,lod)
    for base,top in [(.19,DECK-.26),(DECK+.026,EAVE-.26)]:
        for i,station in enumerate(STATIONS):
            posts=[station] if i in (0,len(STATIONS)-1) else [station-.172,station+.172]
            for x in posts:
                support(builder,x,.074,base,top,lod)
        for i,(left,right)in enumerate(zip(STATIONS,STATIONS[1:])):
            a=left+(.05 if i==0 else .21);bb=right-(.05 if i==4 else .21)
            filigree(builder,a,bb,top,lod)
            if base>1 or i in (3,4):rail(builder,a,bb,.079,base,lod)
        if base>1:
            for x in (STATIONS[0],STATIONS[-1]):
                rail(builder,.14,WALL-.09,.079,base,lod,return_x=x)
                builder.box((x,WALL/2,EAVE-.32),(.10,WALL-.1,.16),IRON,label='Gallery return head')
