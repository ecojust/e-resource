"""Measured Ningbo Road roof pavilion. Local X follows the long ridge east, −Y faces Ningbo Road."""
from math import cos, pi, sin
import numpy as np

CERAMIC = 'weathered green glazed pans'
CAP = 'blue-green glazed roll caps'
CREAM = 'warm grey ridge relief'
TIMBER = 'deep red timber'
FRAME = 'brown red sash'
GLASS = 'recessed blue grey glazing'
SHADE = 'dark rafters and soffit'
PALETTE = {name: {'color': rgb, 'roughness': roughness} for name,rgb,roughness in (
    (CERAMIC,[.26,.40,.35],.68),(CAP,[.35,.53,.46],.48),(CREAM,[.69,.65,.50],.84),
    (TIMBER,[.42,.19,.16],.82),(FRAME,[.29,.16,.15],.81),(GLASS,[.33,.40,.45],.42),
    (SHADE,[.21,.17,.15],.92))}
LOWER=(8.55,4.53,1.30,2.85,.74)
UPPER=(6.98,3.52,4.42,6.53,.66)

def profile(t, dimensions):
    """Tangential corner lift, paired eaves and the shorter upper hip under its gable."""
    a,b,z0,z1,rise=dimensions
    if dimensions==LOWER:
        return a-2.77*t,b-2.17*t,z0+(z1-z0)*(.37*t+.63*t*t),rise*(1-t)**1.90
    if t<=.55:half=a-(a-4.72)*(t/.55)
    else:half=4.72
    return half,b*(1-t),z0+(z1-z0)*(.33*t+.67*t*t),rise*(1-t)**2.15

def linepoint(s,t,side,d):
    a,b,z,lift=profile(t,d)
    # Each hip corner is shared by two independently editable roof slopes.
    if side==0:x,y=a*s,-b
    elif side==1:x,y=a,b*s
    elif side==2:x,y=-a*s,b
    else:x,y=-a,-b*s
    if side in (1,3) and d==UPPER and t>.55:
        z=profile(.55,d)[2]+lift*abs(s)**4
    else:z+=lift*abs(s)**4
    return np.array([x,y,z])

def shell(b,d,far):
    name='Upper' if d==UPPER else 'Lower'
    stages=np.array([0,.22,.55,.78,1.]) if far else np.array([0,.10,.22,.38,.55,.69,.84,1.])
    strips=12 if far else 28
    for side in range(4):
        if d==UPPER and side in (1,3):
            levels=stages[stages<=.55]
        else:levels=stages
        grid=[[linepoint(s,t,side,d) for s in np.linspace(-1,1,strips+1)] for t in levels]
        width=strips+1;vertices=[p for row in grid for p in row];faces=[]
        for row in range(len(grid)-1):
            for col in range(strips):
                a=row*width+col;faces.append((a,a+1,a+1+width,a+width))
        b.add(vertices,faces,CERAMIC,name+' tiled roof face '+str(side+1))
        # The visible fascia has depth and an independent underside. All hip junctions meet.
        eave=np.array(grid[0]);top=eave.copy();bottom=eave-[0,0,.16]
        faces=[(i,i+1,i+1+width,i+width) for i in range(strips)]
        b.add([*bottom,*top],faces,TIMBER,name+' red fascia')
        inset=[p*np.array([.86,.86,1.])-[0,0,.09] for p in bottom]
        b.add([*inset,*bottom],faces,SHADE,name+' projecting soffit')
        b.tube(top+[0,0,.012],.077,CAP,sides=6 if far else 9,label=name+' rounded eave edge')
        # Curved rows terminate against the hip transition. End faces have no rows inside the vertical gable.
        rows=(13 if side%2==0 else 7) if far else (55 if side%2==0 else 29)
        for s in np.linspace(-1,1,rows):
            points=[linepoint(s,t,side,d)+[0,0,.036] for t in levels]
            if np.linalg.norm(points[-1]-points[-2])>.001:
                b.tube(points,.044 if not far else .051,CAP,sides=4 if far else 6,label=name+' rows of tile caps')
            if side in (0,3) and not far:
                outward=np.array([(0,-1),(1,0),(0,1),(-1,0)][side]+(0,))
                end=points[0]+.067*outward
                b.tube([points[0]-.04*outward,end],.071,CAP,sides=9,label=name+' round glazed ends')
                b.tube([end,end+.016*outward],.048,CERAMIC,sides=8,label=name+' inset tile end face')
        # The two visible eave levels terminate in raised, tapered arrises.
        corner = linepoint(1, 0, side, d)
        direction = np.array([np.sign(corner[0]), np.sign(corner[1]), 0.0])
        direction /= np.linalg.norm(direction)
        cross = np.array([-direction[1], direction[0], 0.0])
        outline = [(-.36,.11,.05),(-.09,.17,.07),(.09,.29,.045),(.24,.52,.018),(.30,.65,.007)]
        vertices = []
        for distance, height, width in outline:
            point = corner + distance*direction + [0,0,height]
            vertices.extend([point+width*cross, point+[0,0,width], point-width*cross, point-[0,0,width]])
        panels = [(4*i+j,4*i+(j+1)%4,4*(i+1)+(j+1)%4,4*(i+1)+j) for i in range(len(outline)-1) for j in range(4)]
        b.add(vertices,[(3,2,1,0),*panels,(16,17,18,19)],CAP,name+' tapered corner tip')
        hip_end=.55 if d==UPPER else 1.
        b.tube([linepoint(1,t,side,d)+[0,0,.073] for t in stages if t<=hip_end],.105,CREAM,sides=6 if far else 10,label=name+' corner hip ridge')
    if d==UPPER:
        # Xieshan upper roof terminates in two gables. The shorter hip laps the base of each gable.
        a,bw,z,unused=profile(.55,d)
        for side in [-1,1]:
            x=side*a;polygon=[(x,-bw,z),(x,bw,z),(x,0,profile(1,d)[2])]
            b.add(polygon,[(0,1,2) if side==1 else(2,1,0)],TIMBER,'End gable timber infill')
            for sy in [-1,1]:
                pts=[(side*profile(t,d)[0],sy*profile(t,d)[1],profile(t,d)[2]+.06)for t in stages if t>=.55]
                b.tube(pts,.073,SHADE,sides=5 if far else 8,label='Gable verge')
    return name

def sash_wall(b,far):
    for sign in [-1,1]:
        # Roof supports on the rear are visually closed. Its window arrangement is undocumented.
        b.box((0,sign*2.40,3.41),(12.0,.18,2.44),TIMBER,label='Red timber wall and frame')
    for sign in [-1,1]:
        b.box((sign*5.96,0,3.41),(.17,4.82,2.44),TIMBER,label='End wall below the upper roof')
    for x in (-5.57,-2.79,0,2.79,5.57):
        b.box((x,-2.55,3.42),(.18,.23,2.48),TIMBER,label='Street side structural posts')
        b.box((x,-2.67,4.51),(.36,.40,.14),TIMBER,label='Post head below eaves')
    for centre in (-4.18,-1.39,1.39,4.18):
        for s in [-1,1]:
            x=centre+s*.60
            b.box((x,-2.517,3.55),(1.075,.050,1.65),GLASS,label='Glazed paired red sash')
            for xx in (x-.54,x+.54):
                b.box((xx,-2.553,3.55),(.064,.075,1.75),FRAME,label='Fixed sash frame')
            for zz in ([2.705,3.46,4.385] if far else [2.705,3.16,3.61,4.035,4.385]):
                b.box((x,-2.56,zz),(1.11,.075,.055),FRAME,label='Sash horizontal glazing bar')
            if not far:
                b.box((x,-2.561,3.55),(.035,.076,1.63),FRAME,label='Thin mullion')
    # Dark brackets and rafter ends are plainly visible under the forward overhang in the labelled close-up.
    for x in np.linspace(-5.63,5.63,9 if far else 21):
        b.tube([(x,-2.55,4.28),(x,-3.20,4.30),(x,-3.39,4.38)],.067,SHADE,sides=4,label='Visible rafter ends')

def crest(b,far):
    # Photograph shows two separate open rectangles divided by a wider pale central relief.
    z=6.53
    b.box((0,0,z+.13),(9.5,.26,.25),CREAM,label='Main ridge bed')
    for s in [-1,1]:
        b.box((s*3.62,0,z+.34),(1.94,.24,.36),CREAM,label='Main ridge outer panels')
        b.box((s*2.03,0,z+.52),(1.32,.15,.105),CREAM,label='Opening beneath upper ridge rail')
        for xx in np.linspace(1.46,2.56,3 if far else 5):
            b.tube([(s*xx,-.02,z+.24),(s*(xx+.12),-.02,z+.46)],.028,SHADE,sides=4,label='Open ridge lattice')
        # Two worn terminal silhouettes are shown by profile, without invented figurative anatomy.
        b.tube([(s*4.33,0,z+.27),(s*4.47,0,z+.53),(s*4.54,0,z+.93),(s*4.46,0,z+1.15)],.093,CREAM,sides=6,label='Turned end to the ridge crest')
        for height, reach in [(.48,.24),(.65,.19),(.80,.12)]:
            b.tube([(s*4.48,0,z+height),(s*(4.48+reach*.62),-.005,z+height+.06),(s*(4.48+reach),-.015,z+height+.13)],.035,CREAM,sides=4 if far else 6,label='Short branches of the ridge silhouette')
    b.box((0,0,z+.36),(2.77,.26,.43),CREAM,label='Pale central decorated ridge panel')
    if not far:
        for x in [-.89,-.29,.29,.89]:
            pts=[(x+.23*cos(t),-.15,z+.355+.072*sin(2*t))for t in np.linspace(0,2*pi,16)]
            b.tube(pts,.019,CREAM,sides=4,label='Shallow ridge relief')
    b.lathe((0,0),[(z+.545+h,r) for h,r in [(0,.14),(.10,.10),(.17,.055),(.38,.011)]],CAP,segments=8,label='Central ridge finial')

def add_building(b,far):
    b.box((0,0,.64),(14.20,6.10,1.28),SHADE,label='Recessed roof-level support')
    sash_wall(b,far)
    shell(b,LOWER,far)
    shell(b,UPPER,far)
    crest(b,far)
