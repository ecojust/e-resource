"""Street wing roof, front gable and the two stepped chimney stacks, viewed in 2015 and 2020."""
import numpy as np
from shapely.geometry import Polygon, box
from central_stair import WALL, BASE, CREAM, finish
from residence_finishes import TILE
from stair_surface import PLAN, Camera
from street_bays import bay_layout
from street_frontage import block, shell

FASCIA = 'Yanqing 2 | dark rafter fascia'
RIDGE = 'Yanqing 2 | terracotta ridge caps'
GABLE = 'Yanqing 2 | shaded gable panels'
STACK = 'Yanqing 2 | pale chimney roughcast'
CAP = 'Yanqing 2 | weathered chimney coping'
PIPE = 'Yanqing 2 | light painted downpipe'
PALETTE = {FASCIA:finish((88,56,46),.89),RIDGE:finish((143,75,54),.89),
           GABLE:finish((118,137,123),.91),STACK:finish((183,191,180),.93),
           CAP:finish((115,112,102),.90),PIPE:finish((192,193,177),.76)}

def skin(b,points,drop,material,name):
    ring=[]
    for point in points:
        if not ring or np.linalg.norm(np.array(point)-ring[-1])>.00001:
            ring.append(point)
    if len(ring)>1 and np.linalg.norm(np.array(ring[0])-ring[-1])<.00001:
        ring.pop()
    if len(ring)<3:
        return
    points = np.asarray(ring,dtype=float)
    if np.cross(points[1]-points[0],points[2]-points[0])[2] < 0:
        points = points[::-1]
    n=len(points)
    faces = [(0,i,i+1) for i in range(1,n-1)]
    faces += [(n,n+i+1,n+i) for i in range(1,n-1)]
    faces += [(i,n+i,n+(i+1)%n,(i+1)%n) for i in range(n)]
    b.add(np.vstack((points,points-[0,0,drop])),faces,material,'Roof | '+name)

def front_eave():
    bays=bay_layout()
    shoulder=bays['east shoulder']['plan']; west=bays['west']['plan']; middle=bays['three-window bay']['plan']
    # Each edge follows the measured face below. The eaves extend over the curved stair
    # and over the two projecting balconies, as seen in the winter station.
    line=[(-12.99,1.38),(-12.82,1.40),*[(x,y-.37) for x,y in west],(-7.95,1.40),
          *[(x,y-.37) for x,y in middle],*[(x,y-.32) for x,y in PLAN],
          (2.55,1.15),(4.39,1.15),*[(x,y-.32) for x,y in shoulder],(7.7,2.06),(8.43,2.07)]
    return sorted(line)

def eave_height(x):
    return float(np.interp(x,[-13.,-7.,0.,4.,8.5],[10.29,10.28,10.06,10.08,10.00]))

def ridge_height(x):
    return float(np.interp(x,[-12.99,-12.27,5.89,8.43],[eave_height(-12.99),11.95,11.95,eave_height(8.43)]))

def main_roof(b):
    eave=front_eave()
    for x in (-12.27,5.89):
        y=float(np.interp(x,*np.array(eave).T))
        eave.append((x,y));eave.sort()
    ridge_y=6.18; back_y=12.05
    for i,((x,y),(xx,yy)) in enumerate(zip(eave,eave[1:])):
        if xx-x<.00005:continue
        z,zz=eave_height(x),eave_height(xx);h,hh=ridge_height(x),ridge_height(xx)
        # Intersect the end slope with the front and back slopes. At a hipped
        # end their intersections meet the two eave corners, then converge
        # to the ridge. This third face closes the surface under both hip caps.
        lo,hi = np.interp([x,xx],[-12.99,-12.27,5.89,8.43],[1,0,0,1])
        yl=ridge_y+(y-ridge_y)*lo
        yr=ridge_y+(yy-ridge_y)*hi
        bl=ridge_y+(back_y-ridge_y)*lo
        br=ridge_y+(back_y-ridge_y)*hi
        front=[(x,y,z),(xx,yy,zz),(xx,yr,hh),(x,yl,h)]
        rear=[(x,bl,h),(xx,br,hh),(xx,back_y,zz),(x,back_y,z)]
        if lo>0 or hi>0:
            skin(b,[(x,yl,h),(xx,yr,hh),(xx,br,hh),(x,bl,h)],.132,TILE,'hip surface between the two corner ridges')
        skin(b,front,.122,TILE,'street-facing tile plane')
        skin(b,rear,.122,TILE,'rear tile plane within the street wing')
        skin(b,[(x,y,z-.089),(xx,yy,zz-.089),(xx,yy+.19,zz-.089),(x,y+.19,z-.089)],.105,FASCIA,'outer eave board')
    b.tube([(-12.27,ridge_y,11.95),(5.89,ridge_y,11.95)],.075,RIDGE,sides=10,label='Roof | long capped ridge')
    for x in (-12.99,8.43):
        xx=-12.27 if x<0 else 5.89
        y=float(np.interp(x,*np.array(eave).T));h=eave_height(x)
        for end in [(x,y,h),(x,back_y,h)]:
            b.tube([end,(xx,ridge_y,11.95)],.061,RIDGE,sides=8,label='Roof | short hip cap')
    # The end and rear are the surveyed extent of the short street wing. Other houses
    # continue behind it in the heritage group. Individual rear openings lack attribution.
    block(b,-12.73,8.15,11.66,11.87,.52,10.21,WALL,'rear closure of street wing')
    block(b,-12.73,8.15,11.65,11.87,0,.54,BASE,'rear closure plinth')
    for x,yfront in [(-12.73,1.75),(8.15,2.40)]:
        block(b,x-.08,x+.08,yfront,11.87,0,.55,BASE,'end wall plinth')
        block(b,x-.08,x+.08,yfront,11.87,.55,eave_height(x)-.09,WALL,'end wall')
    skin(b,[(-12.73,1.76,.018),(8.15,2.42,.018),(8.15,11.8,.018),(-12.73,11.8,.018)],.05,BASE,'under footprint')

def gable(b):
    # The bay carries a triangular timbered gable facing the street, in front of the main ridge.
    left,peak,right=-6.62,-4.39,-1.89
    y=.70; foot,top=10.13,11.82; depth=4.88
    face=Polygon([(left,foot),(right,foot),(peak,top)])
    shell(b,face,y,GABLE,'front gable infill',.16)
    for t in np.linspace(left+.38,right-.37,9):
        point=face.intersection(box(t-.035,foot,t+.035,top))
        shell(b,point,y-.046,CREAM,'upright on front gable',.052)
    for a,z1,c,z2 in [(left-.19,foot-.07,peak,top+.09),(peak,top+.09,right+.17,foot-.07)]:
        skin(b,[(a,y-.27,z1),(c,y-.27,z2),(c,depth,z2),(a,depth,z1)],.102,TILE,'gable tile slope')
        skin(b,[(a,y-.28,z1-.048),(c,y-.28,z2-.048),(c,y-.13,z2-.048),(a,y-.13,z1-.048)],.165,FASCIA,'front gable bargeboard')
    b.tube([(peak,y-.27,top+.093),(peak,depth,top+.093)],.065,RIDGE,sides=10,label='Roof | short gable ridge')
    block(b,left,right,y-.16,y+.10,foot-.06,foot+.003,FASCIA,'gable foot board')

def chimney(b,pixels,depth,thickness,label):
    c=Camera();left,top,right,step,outer=pixels
    x0,_,z=c.wall(left,depth);x1=c.wall(right,depth)[0];x2=c.wall(outer,depth)[0]
    h=c.wall(top,depth)[2];low=c.wall(step,depth)[2]; bottom=10.82
    for a,e,hgt,word in [(x0,x1,h,'higher shaft'),(x1,x2,low,'lower shaft')]:
        block(b,a,e,depth,depth+thickness,bottom,hgt-.083,STACK,label+' '+word)
        block(b,a-.036,e+.036,depth-.045,depth+thickness+.039,hgt-.139,hgt-.068,CAP,label+' cornice return')
        block(b,a-.058,e+.058,depth-.062,depth+thickness+.057,hgt-.073,hgt,CAP,label+' coping')

def add_roof(b,lod=False):
    main_roof(b);gable(b)
    chimney(b,[(1037,128),(1061,119),(1115,130),(1138,225),(1162,235)],3.35,.62,'tall stepped chimney')
    chimney(b,[(1262,201),(1282,197),(1322,203),(1351,215),(1388,215)],4.45,.57,'lower stepped chimney')
    # Only the building-mounted rain leaders distinguishable from the utility poles are included.
    for i,(x,y) in enumerate([(-12.53,1.72),(-7.99,1.66),(-2.20,1.33),(6.29,2.42)]):
        top=eave_height(x)-.17
        b.tube([(x,y-.10,.08),(x,y-.10,top-.31),(x,y-.22,top-.15),(x,y-.22,top)],.054,PIPE,sides=8 if lod else 12,label='Street | pale downpipe '+str(i+1))
