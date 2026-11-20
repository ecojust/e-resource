"""The continuous slated roof and the differently shaped dormers of the restored school."""
import math
import numpy as np
from shapely.geometry import Polygon, box
from window_bays import BRICK,STONE,DARK,GLASS,ROOF,SEAM,BASE,arched,panel

EAVE=14.95
BREAK=17.97
RIDGE=22.30
HALF=34.05
DEPTH=24.07
SECTIONS=[(-HALF,-22.72,0,DEPTH),(-22.72,-7.25,1.34,21.88),
          (-7.25,7.25,-.055,DEPTH), (7.25,22.72,1.34,21.88),(22.72,HALF,0,DEPTH)]

def roof(b,lod):
    mid=DEPTH/2
    def face(vertices,label):
        b.add(vertices,[(0,n,n+1)for n in range(1,len(vertices)-1)],ROOF,label)
    def station(x,a,c,end):
        # Hips at the east and west ends, with a distinct change of fall at the lower ring.
        return [(x,a-.26,EAVE),(x+end*1.75,a+1.60,BREAK),
                (x+end*5.25,mid,RIDGE),(x+end*1.75,c-1.60,BREAK),(x,c+.26,EAVE)]
    for i,(x0,x1,a,c)in enumerate(SECTIONS):
        left=station(x0,a,c,1 if i==0 else 0);right=station(x1,a,c,-1 if i==4 else 0)
        for j in range(4):
            face([left[j],right[j],right[j+1],left[j+1]],'Roof / double slope')
        if i in (0,4):
            q=left if i==0 else right
            lower=[q[0],q[4],q[3],q[1]];upper=[q[1],q[3],q[2]]
            face(lower[::-1] if i==0 else lower,'Roof / end lower hips')
            face(upper[::-1] if i==0 else upper,'Roof / end upper hips')
        if i:
            for j in (0,1,2,3):
                # Close raised roof shoulders over the masonry steps in the two side wings.
                face([prev[j],left[j],left[j+1],prev[j+1]],'Roof / stepped junctions')
        prev=right
        for a1,a2 in [(left[1],right[1]),(left[3],right[3])]:
            b.tube([a1,a2],.053,SEAM,7 if lod else 9,'Roof / breaks in pitch')
        if not lod:
            for j in [0,1,2,3]:
                A,B,C,D=map(np.asarray,[left[j],right[j],left[j+1],right[j+1]])
                # Selected horizontal slate courses retain the scale and direction of the tiled surfaces.
                for tt in np.linspace(.14,.88,6):
                    b.tube([(1-tt)*A+tt*C,(1-tt)*B+tt*D],.015,SEAM,5,'Roof / slate courses')
    b.tube([(-HALF+5.25,mid,RIDGE),(HALF-5.25,mid,RIDGE)],.075,SEAM,8,'Roof / ridge flashing')

def dormer(f,x,z,w,h,kind,front,lod):
    # A closed rear wedge meets the sloping roof. The window opening cuts the complete front skin.
    points=[(x-w/2,z),(x+w/2,z),(x+w/2,z+h)]
    if kind=='round':
        for a in np.linspace(0,math.pi,13)[1:]:
            points.append((x+w/2*math.cos(a),z+h+w*.31*math.sin(a)))
    else:points.extend([(x,z+h+w*.31),(x-w/2,z+h)])
    contour=Polygon(points)
    cut=arched(x,z+.085,w*.59,h*.85,min(.22,w*.11))
    f.prism(contour.difference(cut),front-.36,front,STONE,'dormer cheeks')
    f.prism(cut,front-.25,front-.22,GLASS,'dormer glazing')
    panel(f,x,z+h*.43,.047,h*.70,front-.225,front-.114,DARK,'dormer frames')
    stroke=contour.exterior.intersection(box(x-w,z+h-.018,x+w,z+h+w))
    f.prism(stroke.buffer(.047,cap_style=2,join_style=2),front-.40,front+.080,SEAM,'dormer hood')
    # Dark slate cheeks and cap close the front to the roof behind it.
    p0=[f.point(xx,zz,front-.35)for xx,zz in points];p1=[f.point(xx,z+.04,front-2.3)for xx,zz in points]
    for i in range(1,len(p0)-1):
        f.builder.add([p0[i],p0[i+1],p1[i+1],p1[i]],[(0,1,2),(0,2,3)],ROOF,f.label+'/dormer backs')

def ornamental_gable(f,x,w,main,lod):
    z=14.81;h=3.12 if main else 2.36
    # Brick outline rises from wide shoulders into the central arched pediment.
    xs=np.array([-1,-.82,-.67,-.54,-.45,-.40,.40,.45,.54,.67,.82,1])*w/2
    zs=z+np.array([.18,.20,.39,.78,1.17,h,h,1.17,.78,.39,.20,.18])
    q=Polygon([(x-w/2,z)]+[(x+u,v)for u,v in zip(xs,zs)]+[(x+w/2,z)])
    win=arched(x,z+.29,1.35 if main else 1.25,h-.4,.17)
    f.prism(q.difference(win),-.34,.17,BRICK,'roof window gables')
    f.prism(win,-.30,-.28,GLASS,'gable opening')
    for dx in (-.34,0,.34):panel(f,x+dx,z+h*.48,.044,h-.67,-.28,-.17,DARK,'gable mullions')
    rim=q.exterior.intersection(box(x-w,z+.14,x+w,z+h+.10))
    f.prism(rim.buffer(.065,cap_style=2,join_style=2),.17,.26,STONE,'gable edge')
    if main:
        # The 2023 closeup shows a broken crest with curved returns and a separate centre stone.
        for side in (-1,1):
            pts=[f.point(x+side*t,z+h+zz,.255)for t,zz in [(1.20,-.04),(1.09,.13),(.76,.32),(.38,.24),(.32,.12)]]
            f.builder.tube(pts,.10,STONE,8,'Gable / broken pediment')
        panel(f,x,z+h+.32,.38,.24,.02,.23,STONE,'gable key')
    else:
        v=[f.point(x+t,z+h+.31*math.sqrt(max(0,1-(t/1.13)**2)),.223)for t in np.linspace(-1.13,1.13,17)]
        f.builder.tube(v,.087,STONE,8,'Gable / curved end hood')
