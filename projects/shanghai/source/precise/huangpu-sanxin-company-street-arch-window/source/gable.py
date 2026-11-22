"""Model a street-level window of the former Sanxin headquarters on Jiangxi Road."""
from math import cos, pi, sin, sqrt
from pathlib import Path
from shapely.geometry import Polygon, box
from profile_tools import BRICK as STONE, cb, slab, bricks_uv

MORTAR='Recessed joints in the street wall'
SILL='Weathered stone sill and courses'
GRILLE='Slender dark metal rods'
SASH='Original window frame'
GLASS='Recessed bluish glazing'
VENT='Shallow opening below the window panel'
PALETTE={}
for key,rgb in [(STONE,(255,255,255)),(MORTAR,(105,100,92)),(SILL,(154,147,133)),
                (GRILLE,(60,61,58)),(SASH,(62,63,59)),(GLASS,(91,105,111)),(VENT,(64,59,53))]:
    PALETTE[key]=dict(color=[(v/255)**2.2 for v in rgb],roughness=.82)
PALETTE[STONE]['texture']=str(Path(__file__).with_name('finish.png'))

HALF=.99
RISE=.82
SPRING=3.22
BOTTOM=.84
OUTER=.30
WIDTH=1.51

def outline(radius,rise,bottom,steps):
    shell=[(-radius,bottom),(radius,bottom)]
    shell.extend((radius*cos(pi*i/steps),SPRING+rise*sin(pi*i/steps)) for i in range(steps+1))
    return Polygon(shell)

def sector(r0,h0,r1,h1,low,high,steps):
    angles=[low+(high-low)*j/steps for j in range(steps+1)]
    upper=[(r1*cos(a),SPRING+h1*sin(a)) for a in angles]
    lower=[(r0*cos(a),SPRING+h0*sin(a)) for a in reversed(angles)]
    return Polygon(upper+lower)

def max_z(x):
    return SPRING+RISE*sqrt(max(0,1-(x/HALF)**2))

def model(b,lod=False):
    steps=24 if lod else 64
    aperture=outline(HALF,RISE,BOTTOM,steps)
    outer=outline(HALF+OUTER,RISE+OUTER,BOTTOM-.03,steps)
    surround=box(-WIDTH,0,WIDTH,4.61).difference(aperture)
    slab(b,surround,.046,.41,MORTAR,'Recessed masonry bed behind joints')
    spandrels=box(-WIDTH,SPRING,WIDTH,4.61).difference(outer)
    slab(b,spandrels,0,.105,STONE,'Plain stone above the arch')
    for side in [-1,1]:
        left,right=(-WIDTH,-HALF) if side<0 else (HALF,WIDTH)
        for i in range(10):
            lo=BOTTOM+(SPRING-BOTTOM)*i/10
            hi=BOTTOM+(SPRING-BOTTOM)*(i+1)/10
            cb(b,left,right,-.016,.11,lo+.008,hi-.008,STONE,'Horizontal rock-faced jamb course')
    # The radial beds turn down into the fronts of the two engaged piers.
    count=11
    for i in range(count):
        low=(i*pi/count)+.006;high=((i+1)*pi/count)-.006
        slab(b,sector(HALF,RISE,HALF+OUTER,RISE+OUTER,low,high,3 if lod else 7),
             -.017,.115,STONE,'Radially jointed stone voussoir')
    slab(b,box(-WIDTH,.22,WIDTH,.81).difference(box(-.52,.225,.52,.279)),0,.135,STONE,'Raised plain window apron')
    cb(b,-.52,.52,.039,.13,.225,.279,VENT,'Recess beneath the window apron')
    for lo,hi,y,span in [(0,.145,-.038,WIDTH),(.145,.205,-.074,WIDTH),(.205,.224,-.041,WIDTH),
                          (.75,.795,-.06,1.070),(.795,.824,-.105,1.095),(.824,.858,-.132,1.11),
                          (4.30,4.38,-.042,WIDTH),(4.38,4.45,-.094,WIDTH),(4.45,4.50,-.14,WIDTH),(4.50,4.59,-.083,WIDTH)]:
        cb(b,-span,span,y,.14,lo,hi,SILL,'Profile of horizontal stone course')
    inner=outline(HALF-.054,RISE-.056,BOTTOM+.06,steps)
    slab(b,aperture.difference(inner),.119,.211,SASH,'Outer frame of recessed sash')
    slab(b,inner,.271,.289,GLASS,'Glazing behind the ironwork')
    cb(b,-.021,.021,.152,.208,BOTTOM+.05,SPRING+RISE-.045,SASH,'Centre mullion behind the grille')
    for level,half in [(1.56,.015),(2.27,.022),(3.24,.027),(3.61,.015)]:
        wid=HALF*sqrt(1-((max(0,level-SPRING))/RISE)**2)-.04
        cb(b,-wid,wid,.145,.196,level-half,level+half,SASH,'Dark window transom')
    rods=range(-8,9) if lod else range(-12,13)
    spacing=.11 if lod else .074
    for j in rods:
        x=j*spacing
        cb(b,x-.009,x+.009,-.067,-.053,BOTTOM+.024,max_z(x)-.033,GRILLE,'Continuous upright of iron grille')
    for z in (1.10,1.73,2.34,2.96,3.53,3.79):
        wid=HALF*sqrt(1-(max(z-SPRING,0)/RISE)**2)-.044
        cb(b,-wid,wid,-.059,-.044,z-.009,z+.009,GRILLE,'Thin cross tie to grille')
    bricks_uv(b)
