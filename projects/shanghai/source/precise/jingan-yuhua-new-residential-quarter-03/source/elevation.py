"""Brick and stucco entrance elevation from the dated image with the green No. 3 plate."""
import math
import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade,opening

STUCCO='warm ivory render'
SILL='blue grey cast stone'
MORTAR='dark warm brick joints'
BROWN='purple brown facing brick'
RUSSET='burnished russet facing brick'
DUSK='smoke brown facing brick'
GLASS='muted blue window glass'
FRAME='blackened steel window frames'
DOOR='dark weathered gate'
EAVE='dark fascia and roof edge'
SOFFIT='timber soffit lining'
CLAY='weathered clay roof'
GREEN='green ceramic number plaque'
METAL='rainwater pipework'
VINE='small leaf canopy'
TWIG='woody trellis vine'
PALETTE={
 STUCCO:{'color':[.73,.684,.566],'roughness':.90},SILL:{'color':[.43,.454,.445],'roughness':.88},
 MORTAR:{'color':[.255,.174,.147],'roughness':.91},
 BROWN:{'color':[.302,.164,.132],'roughness':.79},RUSSET:{'color':[.405,.220,.159],'roughness':.81},
 DUSK:{'color':[.232,.136,.12],'roughness':.89},GLASS:{'color':[.135,.202,.226],'roughness':.32,'metallic':.21},
 FRAME:{'color':[.067,.065,.065],'roughness':.64,'metallic':.38},DOOR:{'color':[.119,.082,.060],'roughness':.82},
 EAVE:{'color':[.092,.081,.076],'roughness':.82},SOFFIT:{'color':[.375,.30,.23],'roughness':.88},
 CLAY:{'color':[.323,.160,.102],'roughness':.87},GREEN:{'color':[.046,.245,.171],'roughness':.51},
 METAL:{'color':[.325,.305,.287],'roughness':.60,'metallic':.32},
 VINE:{'color':[.122,.216,.138],'roughness':.93},'deep leaf':{'color':[.075,.156,.099],'roughness':.94},TWIG:{'color':[.205,.169,.101],'roughness':.91},
 'faded numeral':{'color':[.776,.792,.73],'roughness':.79},
}


def face(b,a,c,y,name):
    return Facade(b,(a,y),(c,y),name)


def bricks(f,zone,lod,vertical=False,depth=.035):
    """Create brick courses clipped to panel edges and actual window apertures."""
    lo,bot,hi,top=zone.bounds
    f.prism(zone,-.013,.002,MORTAR,'mortar bed')
    height=.24 if lod else .126
    width=.92 if lod else .468
    if vertical:height,width=width,height
    i=0;z=bot
    while z<top-1e-6:
        u=lo-(width*.5 if i%2 else 0.);j=0
        while u<hi-1e-6:
            piece=zone.intersection(box(u+.006,z+.005,u+width-.006,min(z+height-.005,top-.003)))
            if not piece.is_empty and piece.area>.0015:
                choice=(i*11+j*3+i*j*2)%13
                mat=RUSSET if choice in (0,2,7) else DUSK if choice in (3,5,10) else BROWN
                f.prism(piece,.001,depth+(choice%3)*.0016,mat,'individual face bricks')
            u+=width;j+=1
        z+=height;i+=1


def slit(f,u,z,w,h,lod,n=1):
    p=opening(u,z,w,h)
    f.window(p,n,2 if lod else 3,frame=FRAME,glass=GLASS,trim=False)
    return p


def eaves(b,x0,x1,y0,y1,z,pitch,lod,name):
    """Bound the return at the roof edge visible in the near street image."""
    verts=[(x0,y0,z),(x1,y0,z),(x1,y1,z+pitch),(x0,y1,z+pitch)]
    b.add(verts,[(0,1,2,3)],CLAY,name+'/visible shallow tile plane')
    b.box(((x0+x1)/2,y0+.27,z-.055),(x1-x0,.54,.095),SOFFIT,label=name+'/soffit')
    b.box(((x0+x1)/2,y0,z+.018),(x1-x0,.105,.165),EAVE,label=name+'/projecting dark fascia')
    for x in np.arange(x0+.09,x1-.04,.31 if lod else .117):
        b.box((x,y0+.28,z-.111),(.022,.45,.021),EAVE,label=name+'/underside battens')
    for x in np.arange(x0+.085,x1-.02,.45 if lod else .26):
        b.tube([(x,y0+.022,z+.029),(x,y1,z+pitch+.029)],.017,CLAY,5,name+'/tile seams')


def paired_windows(f,lod):
    for z,h in ((3.75,1.57),(6.60,1.24)):
        holes=[opening(u,z,.61,h)for u in (-1.14,1.14)]
        band=box(-1.65,z-.035,1.63,z+h+.034)
        bricks(f,band.difference(unary_union(holes)),lod)
        for u in (-1.14,1.14):slit(f,u,z,.61,h,lod)
        f.box(0,z-.11,3.47,.13,.24,.08,SILL,'continuous narrow sills')


def numbered_gate(b,lod):
    gate=face(b,.18,3.67,-1.28,'Lane entrance')
    high=2.49
    door=opening(0,.06,1.29,2.19)
    outline=Polygon([(-1.745,.02),(1.745,.02),(1.745,1.59),(.99,1.59),(.99,high),(-1.06,high),(-1.06,1.61),(-1.745,1.61)])
    gate.wall(.02,high,[door],thickness=.19,material=MORTAR,outline=outline)
    returns=box(-1.745,.05,1.745,1.60)
    bricks(gate,returns.difference(door),lod)
    for u in (-.750,.750):
        gate.box(u,1.29,.19,2.54,.28,.047,SILL,'tall stone gateposts')
    gate.box(0,2.41,2.07,.24,.38,.09,SILL,'lintel under vine canopy')
    gate.prism(door,-.245,-.215,DOOR,'shaded gate leaf')
    for u in np.linspace(-.52,.52,5 if lod else 11):
        gate.box(u,1.16,.019,2.08,.018,-.198,EAVE,'vertical gate boards')
    gate.box(-.81,1.94,.28,.28,.052,.208,GREEN,'green No 3 plate')
    # Stroke outline of the photographed single digit; this is original geometry.
    coords=[(-.072,.084),(-.026,.111),(.047,.104),(.081,.075),(.076,.033),(.043,.004),(-.003,-.001),(.049,-.015),(.084,-.051),(.079,-.089),(.034,-.114),(-.027,-.108),(-.072,-.086)]
    pts=[gate.point(-.81+u*.75,1.94+z*.75,.238)for u,z in coords]
    b.tube(pts,.009,'faded numeral',6,'Lane entrance/No 3 numeral')
    for s in (-1,1):
        x=gate.center[0]+s*1.62
        b.box((x,-.91,1.56),(.12,.74,.12),DOOR,label='Lane entrance/pergola side rails')
    b.box((1.925,-1.31,2.55),(3.59,.14,.115),DOOR,label='Lane entrance/trellis front rail')
    for x in np.linspace(.31,3.53,7 if lod else 12):
        b.box((x,-.99,2.55),(.063,.73,.066),DOOR,label='Lane entrance/trellis slats')
    # Several branching sprays form the leafy edge of the gate canopy in the photo.
    # Keep each leaf a separate curved plane so the doorway remains visible through it.
    branches=8 if lod else 21
    for j in range(branches):
        x0=.14+3.78*j/(branches-1)
        y0=-1.10+.10*math.cos(j*.7)
        length=.24+.28*((j*5)%11)/10
        points=[]
        for k in range(7):
            t=k/6
            points.append((x0+.18*math.sin(j*1.3+4*t),y0-length*t,2.62+.16*math.sin(t*math.pi+j*.3)-.15*t))
        b.tube(points,.011,TWIG,5,'Lane entrance/branching foliage stems')
        for k,(x,y,z)in enumerate(points[1:]):
            for sign in (-1,1):
                u=.042+.019*((j+k)%3)
                tip=(x+sign*u*1.85,y-.035,z+.018)
                b.add([(x,y,z),(x+sign*u*.83,y-.068,z+.033),tip,(x+sign*u*.72,y+.009,z-.014)],
                      [(0,1,2),(0,2,3)],'deep leaf' if (j+k)%3 else VINE,'Lane entrance/leaf canopy')
    # Keep the woody runners visible below the new growth.
    for j in range(5 if lod else 9):
        x0=.29+j*(3.23/(4 if lod else 8));pts=[]
        for k in range(9):
            u=k/8;pts.append((x0+.125*math.sin(4*u+j),-1.04-.49*u+.10*math.cos(6*u+j),2.66+.13*math.sin(3.5*u+j)-.17*u))
        b.tube(pts,.014,TWIG,5,'Lane entrance/trellis vines')
        for k,pt in enumerate(pts[1::2]if lod else pts[1:]):
            x,y,z=pt;scale=.066+.017*((j+k)%3)
            b.add([(x,y,z),(x+scale*.64,y-.044,z+.028),(x+scale*1.72,y-.064,z+.007),(x+scale*.69,y-.013,z-.018)],[(0,1,2),(0,2,3)],VINE,'Lane entrance/leaflets')


def add_geometry(b,lod):
    left=face(b,-3.98,.10,.19,'Tall left-hand wing')
    grouped=[opening(u,z,.61,h)for z,h in ((3.75,1.57),(6.60,1.24))for u in (-1.14,1.14)]
    low=[opening(u,.66,.77,1.51)for u in (-1.24,.94)]
    left.wall(0,8.49,[*grouped,*low],thickness=.27,material=STUCCO)
    paired_windows(left,lod)
    bricks(left,box(-2.03,.055,2.035,2.80).difference(unary_union(low)),lod)
    for u in (-1.24,.94):slit(left,u,.66,.77,1.51,lod)
    left.box(0,2.9,4.08,.14,.21,.06,SILL,'ground-floor band')
    eaves(b,-4.16,.16,-.39,1.36,8.49,.45,lod,'Tall left wing roof')
    # The blade projects above the large eave, with narrow mottled brick tiles on its visible edge.
    blade=face(b,-.11,.39,-.27,'Brick vertical blade')
    tip=Polygon([(-.25,0),(.25,0),(.25,9.42),(-.25,9.21)])
    blade.wall(0,9.42,thickness=.47,material=MORTAR,outline=tip)
    bricks(blade,tip,lod,depth=.052)
    side=Facade(b,(.39,-.27),(.39,.96),'Blade/deep pale return')
    side.wall(0,9.42,thickness=.12,material=STUCCO,outline=Polygon([(-side.length/2,0),(side.length/2,0),(side.length/2,8.72),(-side.length/2,9.42)]))
    right=face(b,.39,3.68,-.05,'Brick balcony bay')
    big=opening(0,3.98,1.72,1.62)
    right.wall(.0,6.36,[big],thickness=.285,material=STUCCO)
    bricks(right,box(-right.length/2,3.83,right.length/2,5.86).difference(big),lod)
    # The left-hand third is open and dark in the numbered image. The right
    # two-thirds are glazed behind the balcony guard; keep their depth distinct.
    infill=opening(.303,3.98,1.115,1.62)
    right.window(infill,2,2 if lod else 3,frame=FRAME,glass=GLASS,trim=False)
    right.prism(opening(-.563,3.98,.60,1.62),-.816,-.788,EAVE,'dark recessed left balcony back')
    right.prism(box(-.86,3.98,-.824,5.60),-.79,-.035,STUCCO,'recessed side reveal')
    right.prism(box(-.86,5.555,-.25,5.60),-.79,-.035,SOFFIT,'balcony recess soffit')
    bricks(right,box(-.86,5.61,.86,5.84),lod,vertical=True)
    right.box(0,3.78,right.length+.08,.14,.22,.105,SILL,'balcony sill course')
    for z in (4.13,4.49):
        right.line((-.86,z,.13),(.86,z,.13),.02,FRAME,5,'horizontal dark guards')
    eaves(b,.30,3.91,-.59,1.04,6.38,.31,lod,'Lower right wing roof')
    attic=face(b,.41,2.77,.94,'Setback attic wall')
    arch=opening(.07,6.45,.66,.82,.33,9 if lod else 18)
    attic.wall(6.30,7.66,[arch],thickness=.22,material=STUCCO)
    attic.window(arch,1,2,frame=FRAME,glass=GLASS,trim=False)
    eaves(b,.34,2.86,.56,1.56,7.68,.29,lod,'Setback attic eaves')
    # Photo gives the right wall return, not the detached neighbor or the rear unit.
    for x,y0,y1,z in [(-3.98,.19,.93,8.49),(3.68,-.05,.83,6.37)]:
        Facade(b,(x,y0),(x,y1),'Limited side reveal').wall(0,z,thickness=.14,material=STUCCO)
    b.tube([(.40,-.32,7.14),(.40,-.32,3.45),(.47,-.30,3.32),(.47,-.30,.15)],.044,METAL,7 if lod else 11,'Facade/rainwater downpipe')
    numbered_gate(b,lod)
