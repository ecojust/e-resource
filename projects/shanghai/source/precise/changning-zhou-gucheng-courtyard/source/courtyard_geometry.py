"""Courtyard elevation from the numbered December 2014 photograph. Local units are metres."""
import math
import numpy as np
from shapely.geometry import Polygon
from photo_architecture import Facade, opening

WALL = 'aged warm white stucco'
STONE = 'cool cut lintel stone'
TILES = 'weathered red barrel tile'
RIDGE = 'curved clay tile rolls'
GLASS = 'smoky blue grey glazing'
WOOD = 'dark red joinery'
IRON = 'forged balcony and grilles'
DARK = 'shaded timber eaves'
PIPE = 'painted rainwater goods'
PLINTH = 'grey entrance flags'
PALETTE = {
    WALL: {'color':[.72,.685,.582], 'roughness':.94},
    STONE: {'color':[.44,.47,.458], 'roughness':.85},
    TILES: {'color':[.31,.115,.068], 'roughness':.87},
    RIDGE: {'color':[.43,.172,.105], 'roughness':.84},
    GLASS: {'color':[.12,.184,.186], 'roughness':.28, 'metallic':.2},
    WOOD: {'color':[.225,.072,.044], 'roughness':.7},
    IRON: {'color':[.114,.101,.083], 'metallic':.44,'roughness':.62},
    DARK: {'color':[.165,.112,.079], 'roughness':.82},
    PIPE: {'color':[.59,.60,.563], 'roughness':.76},
    PLINTH: {'color':[.36,.354,.324], 'roughness':.92},
}


def face(b, x0, x1, y, name):
    return Facade(b,(x0,y),(x1,y),name)


def tiled_slope(b,x0,x1,near,far,eave,rise,lod,name):
    """The photo exposes the projecting tiled apron, its underside and round tile ends."""
    verts=[(x0,near,eave),(x1,near,eave),(x1,far,eave+rise),(x0,far,eave+rise)]
    b.add(verts,[(0,1,2,3)],TILES,name+'/tile pan')
    b.box(((x0+x1)/2,near+.075,eave-.054),(x1-x0,.15,.11),DARK,label=name+'/fascia')
    rolls=max(3,round((x1-x0)/(.44 if lod else .215)))
    for x in np.linspace(x0+.07,x1-.07,rolls):
        b.tube([(x,near-.006,eave+.020),(x,far,eave+rise+.02)],.047 if lod else .062,RIDGE,6 if lod else 10,name+'/round tile rolls')
    for x in np.arange(x0+.16,x1-.10,.57):
        b.tube([(x,near+.035,eave-.112),(x,min(near+.48,far),eave-.015)],.059,DARK,4,name+'/projecting rafter ends')


def strap_window(f,x,z,w,h,lod,grille=False):
    hole=opening(x,z,w,h)
    f.window(hole,2,2 if lod else 3,frame=WOOD,glass=GLASS,trim=False)
    f.box(x,z+h+.067,w+.36,.134,.11,.047,STONE,'stone lintels')
    if grille:
        for u in np.linspace(x-w*.39,x+w*.39,4 if lod else 7):
            f.line((u,z+.04,.087),(u,z+h-.04,.087),.017,IRON,5,'ground window grilles')
        for a in (.33,.72):
            f.line((x-w/2+.02,z+h*a,.087),(x+w/2-.02,z+h*a,.087),.019,IRON,5,'ground window grilles')
    return hole


def grouped(f,x,z,width,height,lod):
    """Three tall casements have pale spiral mullions between separate dark frames."""
    step=width/3
    for k in (-1,0,1):
        p=opening(x+step*k,z,step-.13,height)
        f.window(p,1,1,frame=WOOD,glass=GLASS,trim=False)
    for sign in (-1,1):
        u=x+sign*step/2
        f.line((u,z+.01,.035),(u,z+height-.01,.035),.079,STONE,8,'twisted mullion cores')
        n=22 if lod else 48
        for start in (0,math.pi):
            pts=[]
            for a in np.linspace(0,1,n):
                phi=start+a*math.pi*5.6
                pts.append(f.point(u+.074*math.cos(phi),z+.025+(height-.05)*a,.037+.074*math.sin(phi)))
            f.builder.tube(pts,.018,WALL,5,'Courtyard flanks/helical mouldings')


def steps_and_door(b,f,u,lod):
    for k in range(3):
        h=.135*(k+1)
        f.box(u,h/2,2.44-.15*k,h,1.20-.25*k,.62-.125*k,PLINTH,'three entrance steps')
    f.prism(opening(u,.405,1.54,2.57),-.485,-.45,WOOD,'recessed double timber door')
    for s in (-1,1):
        v=u+s*.375
        f.box(v,1.10,.58,1.01,.080,-.413,WOOD,'lower door panels')
        p=opening(v,1.77,.45,.91)
        f.prism(p,-.407,-.377,GLASS,'door lights')
        for v2 in (v-.235,v+.235):f.box(v2,2.22,.047,.99,.052,-.358,WOOD,'door glazing bars')
        for z in (1.75,2.69):f.box(v,z,.52,.065,.052,-.358,WOOD,'door glazing bars')
        f.box(u+s*.105,1.42,.028,.188,.058,-.317,IRON,'door pulls')
    for s in (-1,1):
        f.box(u+s*.866,1.74,.153,2.76,.28,-.055,DARK,'dark entrance surrounds')
    # Only the photographed lean-to extends beyond the courtyard wall.
    x=f.point(u,0)[0];y=f.point(0,0)[1]
    tiled_slope(b,x-1.66,x+1.66,y-1.22,y+.10,3.11,.34,lod,'Entrance canopy')
    for sx in (u-1.32,u+1.32):
        f.line((sx,2.76,.07),(sx,3.04,.82),.068,DARK,4,'canopy knee braces')
    f.box(u,3.07,3.3,.126,.126,1.125,DARK,'outer canopy beam')


def balcony(b,f,lod):
    """The guard follows a shallow bowed plan in front of the long central opening."""
    r=1.45; points=[(-r,.04),(-r,.51),(-1.31,.72),(-.86,.92),(0,1.02),(.86,.92),(1.31,.72),(r,.51),(r,.04)]
    deck=Polygon([(u,-d+f.center[1])for u,d in points])
    from shapely.affinity import translate
    b.plan_prism(translate(deck,xoff=f.center[0]),2.98,3.18,STONE,'Balcony/bowed stone slab')
    for z in (3.28,3.84,4.05):
        b.tube([f.point(u,z,d)for u,d in points],.018 if z<4 else .037,IRON,6 if lod else 10,'Balcony/continuous bowed rails')
    for a,c in zip(points,points[1:]):
        length=math.dist(a,c);n=max(1,round(length/(.33 if lod else .165)))
        for i in range(n):
            t=i/n;u=a[0]+(c[0]-a[0])*t;d=a[1]+(c[1]-a[1])*t
            f.line((u,3.18,d),(u,4.05,d),.023,IRON,5 if lod else 8,'forged vertical pickets')
    for s in (-1,1):
        f.box(s*.92,2.90,.22,.20,.38,.33,STONE,'slab supports')


def add_geometry(b,lod):
    east=face(b,-10.15,-3.12,.02,'East wing')
    entrance=face(b,-3.12,.78,.53,'Entry bay')
    central=face(b,.78,5.47,-.10,'Balcony bay')
    west=face(b,5.47,10.13,.64,'West wing')
    # Openings are cut through the wall before fitting the recessed glass and grilles.
    g=[opening(1.12*k,4.10,.99,1.48)for k in (-1,0,1)]
    lows=[opening(x,.72,1.27,1.72)for x in (-1.82,1.72)]
    east.wall(.0,6.62,g+lows,thickness=.28,material=WALL)
    grouped(east,0,4.10,3.36,1.48,lod)
    for q in lows:
        x=(q.bounds[0]+q.bounds[2])/2;strap_window(east,x,.72,1.27,1.72,lod,True)
    east.beam(.23,.46,.03,STONE,label='stone plinth')
    # A narrow tiled hood and an incised arch above the middle casement
    # identify this wing even when the lower windows are hidden by shrubs.
    east.box(-.22,3.30,6.76,.142,.43,.17,DARK,'dark bracketed belt above ground windows')
    for u in np.linspace(-3.30,2.93,8):
        east.line((u,3.10,.025),(u,3.25,.30),.055,DARK,4,'short belt brackets')
    arc=[east.point(.50*math.cos(t),5.59+.39*math.sin(t),.023)for t in np.linspace(0,math.pi,12 if lod else 28)]
    b.tube(arc,.023,STONE,6,'East wing/semicircular incised overlight')
    for u,z in [(1.13,5.91),(1.13,6.20),(1.57,6.03)]:
        east.line((u,z,.008),(u,z,.060),.068,STONE,8 if lod else 16,'small roundel bosses')
    for q in lows:
        x=(q.bounds[0]+q.bounds[2])/2
        for sign in (-1,1):
            east.box(x+sign*.741,1.22,.209,.293,.089,.044,STONE,'intermittent jamb stones')
        east.box(x,2.489,.256,.236,.111,.068,STONE,'keystones')

    roof_lights=[opening(0,4.02,1.36,1.55)]
    entrance.wall(.0,6.96,roof_lights+[opening(0,.39,1.61,2.68)],thickness=.32,material=WALL)
    strap_window(entrance,0,4.02,1.36,1.55,lod)
    steps_and_door(b,entrance,0,lod)
    # The high, street-visible centre panel has a rectangular vertical attic vent in the 2014 view.
    x=central.length/2
    crown=Polygon([(-x,0),(x,0),(x,6.65),(.35,7.49),(-x,7.47)])
    long=opening(0,3.16,1.75,2.72);vent=opening(-.32,6.58,.26,.61)
    central.wall(0,7.5,[long,vent],thickness=.34,material=WALL,outline=crown)
    central.window(long,3,5 if not lod else 4,frame=WOOD,glass=GLASS,trim=False)
    central.box(0,5.97,2.29,.19,.145,.029,STONE,'long opening lintel')
    central.prism(vent,-.32,-.305,DARK,'recessed attic vent')
    for z in np.linspace(6.64,7.10,4 if lod else 6):
        central.box(-.32,z,.227,.031,.061,-.095,DARK,'vent slats')
    balcony(b,central,lod)
    # Bottom left of the photograph shows a shallow service panel beneath the balcony.
    central.box(.18,1.02,1.94,1.20,.074,.049,PLINTH,'lower service panel')
    central.box(.18,2.11,.87,.38,.048,.038,DARK,'small unlettered wall plaque')
    central.box(.19,.22,2.60,.42,.38,.10,STONE,'curved bay base')
    r=[opening(.83*k,4.11,.70,1.24)for k in (-1,0,1)]
    west.wall(3.17,6.12,r,thickness=.28,material=WALL)
    grouped(west,0,4.11,2.49,1.24,lod)
    # The lower western wall is obscured by a separate low structure; the visible model ends at its abutment.
    for x0,x1,y,eave,rise in [(-10.28,-3.02,.02,6.62,.55),(-3.20,.85,.53,6.98,.46),(5.39,10.27,.64,6.12,.52)]:
        tiled_slope(b,x0,x1,y-.48,y+1.38,eave,rise,lod,'Main eaves '+str(x0))
    # Return only enough of the gable roof to describe the photographed courtyard edge.
    xs=[.72,3.48,5.54];zs=[7.49,7.52,6.67]
    for xa,xb,za,zb in zip(xs,xs[1:],zs,zs[1:]):
        b.add([(xa,-.20,za),(xb,-.20,zb),(xb,1.89,zb+.28),(xa,1.89,za+.28)],[(0,1,2,3)],TILES,'Balcony bay/trimmed tile edge')
        for u in np.linspace(xa+.05,xb-.05,max(3,round((xb-xa)/(.44 if lod else .215)))):
            z=za+(zb-za)*(u-xa)/(xb-xa)
            b.tube([(u,-.21,z+.03),(u,1.88,z+.306)],.043,RIDGE,6 if lod else 8,'Balcony bay/tile rolls')
    # Shallow returns explain the three changes in wall plane visible in the photograph.
    for x,ya,yb,h in [(-10.15,.02,.98,6.62),(-3.12,.02,.53,6.6),(.78,-.10,.53,6.93),(5.47,-.10,.64,6.1),(10.13,.64,1.4,6.12)]:
        low=3.17 if x>9 else 0
        Facade(b,(x,ya),(x,yb),'Side returns').wall(low,h,thickness=.18,material=WALL)
    for x,y,h in [(.71,-.22,7.04),(5.56,.18,5.98)]:
        b.tube([(x,y,h),(x,y,h-.44),(x+.06,y-.15,h-.60),(x+.06,y-.15,2.12),(x+.27,y-.19,1.83),(x+.27,y-.19,.16)],.059,PIPE,7 if lod else 12,'Rainwater/downspouts and swan necks')
