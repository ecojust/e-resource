"""Square roof pavilion at the top of the National Industrial Bank's rounded corner."""
from pathlib import Path
from math import cos, sin, pi
import numpy as np
from shapely.geometry import Point,Polygon,box
from profile_tools import BRICK as WALL,cb,slab,bricks_uv

CAP='Weathered pale cornice'; COLUMN='Round sandstone column'; LINE='Recessed stone reveal'
SHADOW='Recess inside the upper pavilion';LEAF='Crescent frieze';TOP='Uppermost roof curb';IRON='Top railing'
PALETTE={}
for title,rgb in [(WALL,(255,255,255)),(CAP,(189,176,151)),(COLUMN,(175,162,136)),(LINE,(111,100,86)),(SHADOW,(55,51,48)),(LEAF,(202,186,157)),(TOP,(163,150,129)),(IRON,(77,78,72))]:
    PALETTE[title]=dict(color=[(v/255)**2.2 for v in rgb],roughness=.86)
PALETTE[WALL]['texture']=str(Path(__file__).with_name('finish.png'))
PILLARS=(-1.36,1.36)
CRESCENTS=(-1.86,-1.20,0.,1.20,1.86)
def roundpart(b,xc,r,lo,hi,n,material,name):
    polygon=Polygon([(xc+r*cos(2*pi*i/n),.18+r*sin(2*pi*i/n)) for i in range(n)])
    b.prism(polygon,lo,hi,lambda x,y,z:(x,y,z),material,label=name)
def model(b,lod=False):
    sides=12 if lod else 36
    for x in [-2.04,2.04]:
        cb(b,x-.285,x+.285,-.020,.57,.12,1.71,WALL,'Outer square stone pier')
        for z,width,y0 in [(1.70,.63,-.055),(1.77,.70,-.090),(1.83,.73,-.113)]:
            cb(b,x-width/2,x+width/2,y0,.59,z,z+.065,CAP,'Stepped cap of each square pier')
    for xc in PILLARS:
        for r,lo,hi,mat,name in [(.207,.12,.18,CAP,'Round shaft foot'),(.174,.18,1.53,COLUMN,'Round shaft'),(.196,1.53,1.59,CAP,'Neck roll'),(.172,1.59,1.66,COLUMN,'Neck under the capital'),(.215,1.66,1.74,CAP,'Echinus'),(.238,1.74,1.80,CAP,'Capital edge')]:
            roundpart(b,xc,r,lo,hi,sides,mat,name)
        cb(b,xc-.27,xc+.27,-.115,.46,1.80,1.88,CAP,'Square abacus above the round capital')
    cb(b,-2.23,2.23,.85,1.00,.10,2.10,SHADOW,'Dark inner face behind the columns')
    cb(b,-.95,.95,.32,.75,.095,.19,CAP,'Low recessed sill')
    cb(b,-.78,.78,.42,.75,.19,.245,CAP,'Second inset sill course')
    # The shallow front curb is above the separate dated stone panel.
    cb(b,-2.40,2.40,-.145,.87,.00,.12,CAP,'Stone lip above the dated lower roof')
    for lo,hi,x,front,mat,label in [(1.88,1.94,2.36,-.11,CAP,'Lower architrave'),(1.94,1.978,2.30,-.054,LINE,'Narrow shaded joint'),(1.978,2.045,2.39,-.151,CAP,'Raised lintel lip'),(2.045,2.25,2.30,-.045,WALL,'Frieze with five shallow ornaments'),(2.25,2.31,2.34,-.072,CAP,'Upper frieze rim'),(2.31,2.39,2.40,-.104,LINE,'Shaded roof soffit'),(2.39,2.60,2.56,-.25,TOP,'Projecting crown slab')]:
        cb(b,-x,x,front,1.01,lo,hi,mat,label)
    for x in CRESCENTS:
        seg=6 if lod else 18
        outer=Point(x,2.208).buffer(.136,quad_segs=seg);inner=Point(x,2.249).buffer(.13,quad_segs=seg)
        curve=outer.difference(inner).intersection(box(x-.137,2.052,x+.137,2.20))
        slab(b,curve,-.076,-.045,LEAF,'Paired rising ends on frieze relief')
    # A small set-back roof railing is visible against the sky, with rounded ends.
    # The silhouette rises through quarter-rounds at the two ends of the railing.
    steps=5 if lod else 12
    rail=[(-.91,.39,2.60),(-.91,.39,2.748)]
    for theta in np.linspace(pi,pi/2,steps+1):
        rail.append((-.799+.111*cos(theta),.39,2.748+.111*sin(theta)))
    rail.append((.799,.39,2.859))
    for theta in np.linspace(pi/2,0,steps+1):
        rail.append((.799+.111*cos(theta),.39,2.748+.111*sin(theta)))
    rail.append((.91,.39,2.60))
    cleaned=[rail[0]]
    for xyz in rail[1:]:
        if np.linalg.norm(np.subtract(xyz,cleaned[-1]))>1.e-7:cleaned.append(xyz)
    b.tube(cleaned,.011,IRON,6 if lod else 12,'Continuous top rail with two curved corners')
    for x in np.linspace(-.732,.732,8):
        cb(b,x-.009,x+.009,.380,.400,2.60,2.858,IRON,'Slender front rail upright')
    bricks_uv(b)
