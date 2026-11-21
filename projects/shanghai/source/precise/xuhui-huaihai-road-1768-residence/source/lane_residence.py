"""Street-front house beside the south entrance of former Lane 1754."""
import math
import sys
from pathlib import Path

from shapely.affinity import translate
from shapely.geometry import Polygon, box, LineString
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / 'source/precise/hongkou-general-post-office/source/common'))
from photo_architecture import Facade, opening
from sign_lettering import lettering_shapes

WALL, STONE, TRIM, SASH, GLASS, IRON, TILE, RED, IVY, GREEN, IVORY = (
    'warm textured render', 'pink-grey stone base', 'weathered stone moulding',
    'green timber sash', 'muted glazing', 'black rail', 'weathered red roof tile',
    'muted orange panel', 'winter climbing stems', 'green lane plaque', 'ivory lettering')
PALETTE = {k:dict(color=list(color),roughness=r,metallic=metal) for k,color,r,metal in [
    (WALL,(.66,.55,.45),.95,0), (STONE,(.59,.52,.46),.91,0), (TRIM,(.53,.44,.37),.87,0),
    (SASH,(.133,.18,.161),.72,0), (GLASS,(.329,.386,.392),.31,.10),
    (IRON,(.175,.166,.145),.62,.23), (TILE,(.483,.279,.203),.9,0),
    (RED,(.57,.246,.129),.78,0), (IVY,(.262,.223,.184),.92,0),
    (GREEN,(.084,.29,.264),.53,.08), (IVORY,(.89,.88,.75),.78,0)]}
POINTS = [(-4.74473,0),(4.74473,0),(9.29846,13.10968),(-4.58005,13.16529)]
EAVE = 11.17
UPPER = [(4.07,1.85,0), (7.23,1.65,.28)]

def strip(f,u,z,width,height,back,front,mat,label):
    f.box(u,z,width,height,front-back,(back+front)/2,mat,label)

def glazing(f,shape,columns,rows,mat=GLASS):
    x0,z0,x1,z1 = shape.bounds
    inner=shape.buffer(-.057,join_style=2)
    bars=[box(x0+(x1-x0)*i/columns-.019,z0-1,x0+(x1-x0)*i/columns+.019,z1+1)
          for i in range(1,columns)]
    bars.extend(box(x0-1,z0+(z1-z0)*i/rows-.022,x1+1,z0+(z1-z0)*i/rows+.022)
                for i in range(1,rows))
    panes=inner.difference(unary_union(bars)) if bars else inner
    f.prism(panes,-.205,-.177,mat,'inset window surface')
    f.prism(shape.difference(panes),-.188,-.117,SASH,'timber muntins and frames')

def iron_ledge(f,u,z,w,lod):
    strip(f,u,z-.07,w,.105,0,.29,TRIM,'joined window ledge')
    for zz in [z+.07,z+.39]:
        strip(f,u,zz,w,.027,.205,.235,IRON,'horizontal guard')
    n=max(4,round(w/(.245 if lod else .155)))
    for k in range(n+1):
        strip(f,u-w/2+w*k/n,z+.227,.019,.337,.204,.231,IRON,'guard balusters')
    for sign in [-1,1]:
        strip(f,u+sign*w/2,z+.39,.027,.029,.004,.23,IRON,'guard return')

def address(f):
    x=-4.135;z=2.31
    strip(f,x,z,.69,.31,-.01,.037,GREEN,'enamel lane number')
    strip(f,x,z-.43,.69,.50,-.009,.025,STONE,'separate heritage plaque')
    for words,width,height,zz in [('1768弄→',.59,.114,z+.061),('淮海中路',.43,.08,z-.081)]:
        for char,shape in lettering_shapes(words,width,height,font=HERE/'fonts/LanePlaqueSubset.otf'):
            f.prism(translate(shape,xoff=x,yoff=zz),.039,.046,IVORY,'street plaque '+char)

def detail_wall(f,lod,front=False,garden=False):
    count=10 if lod else 24
    centers=[-.305*f.length,-.160*f.length,.142*f.length,.285*f.length] if front else (
        [-.326*f.length,-.13*f.length] if not garden else [.09*f.length,.33*f.length])
    holes=[]
    for bottom,h,arch in ([] if garden else UPPER):
        for x in centers:
            o=opening(x,bottom,.76,h,arch,count);holes.append(o)
            glazing(f,o,2 if not lod else 1,3)
            f.prism(o.buffer(.068,join_style=2).difference(o),-.012,.062,TRIM,'window reveal')
        for a,b in zip(centers[::2],centers[1::2]):iron_ledge(f,(a+b)/2,bottom,b-a+1.07,lod)
    if front:
        for x,panel in [(-2.05,GLASS),(2.12,RED)]:
            s=opening(x,.12,2.30,2.65,.26,count);holes.append(s)
            # The photograph records an obscured ground-level panel at right.
            f.prism(s,-.185,-.155,panel,'broad ground opening')
            f.prism(s.buffer(.105,join_style=2).difference(s),-.014,.084,STONE,'segmental stone surround')
            strip(f,x,2.53,2.23,.052,-.147,-.109,SASH,'upper transom')
    elif garden:
        for x in centers:
            s=opening(x,.58,1.12,1.84,.045,count);holes.append(s);glazing(f,s,2,2)
    f.wall(.045,EAVE,holes,.26,WALL)

def branch(f,lod):
    # Visible dormant main branches are drawn from the winter reference. The finer
    # canopy and individual leaves cannot be recovered from the street image.
    curves=[ [(-4.32,.65),(-4.27,2.91),(-3.88,3.58),(-1.74,3.89),(.09,4.18),(1.65,5.78)],
             [(-3.88,3.58),(-3.64,5.88),(-2.70,6.49),(-.28,7.11),(1.40,8.59)],
             [(-4.27,2.91),(-4.20,5.70),(-3.97,7.66),(-2.62,8.70),(-.39,9.78)],
             [(4.37,.9),(4.18,3.15),(3.69,4.38),(3.58,6.36),(2.61,7.14),(.67,8.70)],
             [(3.58,6.36),(2.30,6.61),(1.0,6.87),(-1.44,7.09)] ]
    for line in curves[:3 if lod else 5]:
        curve=[line[0]]
        for (a,b),(x,z) in zip(line,line[1:]):
            curve.extend([(.76*a+.24*x,.76*b+.24*z),(.24*a+.76*x,.24*b+.76*z)])
        curve.append(line[-1])
        f.builder.tube([f.point(u,z,.085)for u,z in curve],.010 if lod else .014,IVY,5,'dormant façade vine')
        if not lod:
            for i in range(1,len(line)-1):
                x,z=line[i];f.builder.tube([f.point(x,z,.084),f.point(x+.30,z+.16,.082),f.point(x+.62,z+.51,.078)],.008,IVY,4,'dormant vine branches')

def add_residence(builder,lod):
    p=Polygon(POINTS)
    builder.plan_prism(p,0,.15,STONE,'house footprint and plinth')
    sides=[Facade(builder,a,b,name) for a,b,name in zip(POINTS,POINTS[1:]+POINTS[:1],
        ['street front','northeast return','undocumented rear','southwest lane return'])]
    for j,f in enumerate(sides):
        if j==2:f.wall(.045,EAVE,[],.24,WALL)
        else:detail_wall(f,lod,front=j==0,garden=j==3)
        for z,h,d in [(3.17,.12,.10),(3.30,.10,.16),(9.62,.11,.085),(10.58,.095,.09),(10.82,.12,.16),(11.03,.15,.265)]:
            strip(f,0,z,f.length,h,-.03,d,TRIM,'continuous shallow cornice and bands')
    address(sides[0]);branch(sides[0],lod)
    a,b,c,d=POINTS;ridge=[(1.03,4.58,12.81),(2.24,8.58,12.81)]
    verts=[(x,y,EAVE)for x,y in POINTS]+ridge
    builder.add(verts,[(0,1,4),(1,2,5,4),(2,3,5),(3,0,4,5),(3,2,1,0)],TILE,'mapped hipped roof volume')
    for i,j in [(0,4),(1,4),(2,5),(3,5),(4,5)]:
        builder.tube([verts[i],verts[j]],.062,TILE,6,'hip and ridge caps')
    for f in sides:
        for z,h,d in [(11.13,.075,.33),(11.18,.065,.245)]:
            strip(f,0,z,f.length,h,-.005,d,TILE,'terracotta eave edge')

        if not lod:
            count=round(f.length/.236)
            for i in range(count):
                u=f.length*((i+.5)/count-.5)
                builder.tube([f.point(u,11.227,-.01),f.point(u,11.168,.328)],.035,TILE,6,'profiled roof edge tiles')
