"""Front and side eaves of the tiled canopy on the Shanghai branch of Juxingcheng Bank."""
from pathlib import Path
from math import pi,sin
import numpy as np
from shapely.geometry import Polygon
from profile_tools import BRICK as FACE,cb,slab,bricks_uv
TILE='Ochre glazed rolls';CAP='Round tile ends';HIP='Raised hip tiles';RIM='Gilded clay ridge';WOOD='Brown bracket arms';DARK='Bracket bearing blocks';FASCIA='Recessed fascia';SOFFIT='Shadowed soffit'
PALETTE={}
for key,rgb in [(FACE,(255,255,255)),(TILE,(158,134,97)),(CAP,(169,143,105)),(HIP,(151,125,87)),(RIM,(180,151,108)),(WOOD,(112,96,70)),(DARK,(86,76,59)),(FASCIA,(145,130,109)),(SOFFIT,(115,104,83))]:
    PALETTE[key]=dict(color=[(v/255)**2.2 for v in rgb],roughness=.82)
PALETTE[FACE]['texture']=str(Path(__file__).with_name('finish.png'))
EAVE=3.4; RIDGE=2.47; Y0=-1.09; Y1=.34; REAR=1.07; LOW=1.33; HIGH=2.12
ROLLS=np.linspace(-.967,.967,33);BRACKETS=[-2.61,-1.57,-.53,.53,1.57,2.61]
def point(face,u,s):
    span=EAVE+(RIDGE-EAVE)*s
    if face=='front':x=u*span;y=Y0+(Y1-Y0)*s;corner=abs(u)**6
    elif face=='back':x=-u*span;y=REAR+(Y1-REAR)*s;corner=abs(u)**6
    else:
        x=(1 if face=='right' else -1)*span
        frac=(1+u)/2 if face=='right' else (1-u)/2
        y=(Y0+(REAR-Y0)*frac)*(1-s)+Y1*s;corner=1
    z=LOW+(HIGH-LOW)*s-.095*sin(pi*s)+.092*corner*(1-s)
    return np.array([x,y,z])
def roof_surface(b,face,ns,nu):
    vertices=[point(face,u,s) for s in np.linspace(0,1,ns+1) for u in np.linspace(-1,1,nu+1)]
    ind=lambda k,j:k*(nu+1)+j
    faces=[]
    for k in range(ns):
        for j in range(nu):faces.append([ind(k,j),ind(k,j+1),ind(k+1,j+1),ind(k+1,j)])
    b.add(vertices,faces,FACE,'Bowed tile bed '+face)
def bracket(b,x):
    cb(b,x-.12,x+.12,-.31,.19,.10,.39,DARK,'Lower square bearing')
    cb(b,x-.20,x+.20,-.39,.17,.36,.47,WOOD,'First bracket bearing block')
    # Outward arms turn up at the ends and carry the square bearing blocks.
    for z,width,y in [(.465,.283,-.46),(.71,.39,-.61)]:
        contour=[(-width,0),(-width+.035,0),(-width+.058,-.05),(-.12,-.095),(.12,-.095),(width-.058,-.05),(width-.035,0),(width,0),(width,.12),(.21,.12),(.145,.074),(-.145,.074),(-.21,.12),(-width,.12)]
        slab(b,Polygon([(x+dx,z+dz)for dx,dz in contour]),y,-.025,WOOD,'Upturned transverse bracket arm')
        for side in [-1,1]:
            cx=x+side*(width-.073)
            cb(b,cx-.069,cx+.069,y-.015,-.05,z+.119,z+.21,DARK,'Square bearing at tip of bracket arm')
    cb(b,x-.082,x+.082,-.67,.18,.54,.72,WOOD,'Forward projecting interlock')
    cb(b,x-.099,x+.099,-.71,.11,.90,1.069,WOOD,'Upper forward arm')
def model(b,lod=False):
    ns=3 if lod else 8;nu=8 if lod else 20;sides=5 if lod else 10
    cb(b,-3.16,3.16,-.036,.70,.0,.98,FASCIA,'Shadowed back of bracket band')
    for x in BRACKETS:bracket(b,x)
    cb(b,-3.23,3.23,-.76,.72,1.035,1.13,DARK,'Continuous bracket head beam')
    cb(b,-3.31,3.31,-.89,.82,1.13,1.205,WOOD,'Upper eave fascia')
    cb(b,-3.39,3.39,Y0+.005,REAR-.005,1.205,1.335,SOFFIT,'Overhanging soffit')
    for face in ('front','right','back','left'):
        roof_surface(b,face,ns,nu)
        for u in ROLLS if face in ('front','back') else np.linspace(-.89,.89,9):
            upper=.978 if face in ('front','back') else .83
            pts=[point(face,u,s)+[0,0,.027]for s in np.linspace(0,upper,ns+1)]
            b.tube(pts,.056,TILE,sides,'Half-round cover tile '+face)
            if face=='front':
                center=point(face,u,0)+[0,-.025,.012]
                b.tube([center,center+[0,.064,0]],.069,CAP,sides,'Round-ended drip tile')
            if face in ('front','back') and not lod:
                for s in [.26,.52,.77]:
                    p=point(face,u,s)+[0,0,.030];q=point(face,u,s+.015)+[0,0,.030]
                    b.tube([p,q],.061,TILE,8,'Overlap of cover tiles')
    for face in ['front','back']:
        for u in [-1.,1.]:
            p=[point(face,u,s)+[0,0,.061]for s in np.linspace(0,1,ns+1)]
            b.tube(p,.093,HIP,6 if lod else 12,'Rounded descending hip')
    cb(b,-RIDGE-.07,RIDGE+.07,Y1-.094,Y1+.101,HIGH-.009,HIGH+.122,HIP,'Long horizontal roof ridge')
    cb(b,-RIDGE-.075,RIDGE+.075,Y1-.114,Y1+.115,HIGH+.11,HIGH+.17,RIM,'Light-coloured ridge crest')
    bricks_uv(b)
