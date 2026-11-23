"""South flank and roof of the three-gabled street building. Dimensions are in the shared authoring frame."""
import json
from pathlib import Path

from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from placement import Facade
from loggia_materials import ROUGHCAST, LIME, CEMENT, TILE, SHADE
from wing_openings import sash, awning

LAYOUT = json.loads(Path(__file__).with_name('wing_layout.json').read_text())['wings']
REAR = 22.38
# Ratios are taken from the two-year station fit in side-and-roof-observations.json.
SCALE = .683
FRONT = LAYOUT['right']['y']
RIGHT = LAYOUT['right']['x1']
EAVE = LAYOUT['right']['inner_eave']
PALETTE = {}


def plate(b, vertices, depth, material, label):
    """Closed triangular or quadrilateral sheet, counter-clockwise in plan."""
    count = len(vertices)
    bottom = [(x, y, z-depth) for x, y, z in vertices]
    faces = [(0, j, j+1) for j in range(1, count-1)]
    faces += [(count, count+j+1, count+j) for j in range(1, count-1)]
    for j in range(count):
        k = (j+1)%count
        faces.extend([(j, count+j, count+k), (j, count+k, k)])
    b.add(vertices+bottom, faces, material, label)


def part_profiles():
    """Use the actual four wing merlons and central gable profile as the front roof edges."""
    result = []
    for key in ['left', 'left connector', 'centre', 'right connector', 'right']:
        if key == 'centre':
            result.append((key, 0., [(-4.58,11.49), (.38,13.49), (4.98,10.76)]))
            continue
        wing = LAYOUT[key]
        points = [(wing['x0'],wing['outer_eave']), (wing['x1'],wing['inner_eave'])]
        if 'ridge' in wing:
            points.insert(1,tuple(wing['ridge']))
        if 'verge_start' in wing:
            points.insert(1,tuple(wing['verge_start']))
        result.append((key, wing['y'],points))
    return result


def roof_surface(x, y, front_z):
    """The three front-facing gables intersect the long NE–SW roof. Rear pitch is approximate."""
    left = LAYOUT['left']['x0']
    gable = front_z if y <= 8.0 else front_z + (EAVE-front_z)*min(1.,(y-8.)/(REAR-8.))
    transverse = min(8.85+.45*y, EAVE+.36*(REAR-y), EAVE+.43*(x-left), EAVE+.43*(RIGHT-x))
    return max(gable, transverse)+.025


def roof(b):
    profiles = part_profiles()
    for name, front, line in profiles:
        # Dense enough to resolve the genuine crease where the front and transverse pitches meet.
        for (a, za),(c, zc) in zip(line,line[1:]):
            count = max(1,round((c-a)/.85))
            xs = [a+(c-a)*i/count for i in range(count+1)]
            ys = sorted({front,8., REAR, *[j*.5 for j in range(1,45) if front < j*.5 < REAR]})
            vertices = [(x,y,roof_surface(x,y,za+(zc-za)*(x-a)/(c-a))) for y in ys for x in xs]
            nx = len(xs)
            p = len(vertices)
            faces = []
            for j in range(len(ys)-1):
                for i in range(nx-1):
                    u=j*nx+i
                    faces.extend([(u,u+1,u+nx+1),(u,u+nx+1,u+nx)])
            faces.extend([tuple(p+k for k in reversed(t)) for t in list(faces)])
            boundary = [*range(nx),*[j*nx+nx-1 for j in range(1,len(ys))],
                        *[(len(ys)-1)*nx+i for i in range(nx-2,-1,-1)],
                        *[j*nx for j in range(len(ys)-2,0,-1)]]
            for i,u in enumerate(boundary):
                v=boundary[(i+1)%len(boundary)]
                faces.extend([(u,p+u,p+v),(u,p+v,v)])
            b.add(vertices+[(x,y,z-.13) for x,y,z in vertices],faces,TILE,name+' | red tile roof')
    # Vertical cheeks where the high gables meet the lower connector slopes.
    for (_,fa,aa),(_,fb,bb) in zip(profiles,profiles[1:]):
        x = aa[-1][0]
        y0=max(fa,fb)
        yvals=sorted({y0, REAR,*[j*.5 for j in range(1,45) if y0<j*.5<REAR]})
        side=Facade(b,(x,0),(0,1),'Roof | gable return')
        for a,c in zip(yvals,yvals[1:]):
            left=[roof_surface(x,y,aa[-1][1]) for y in (a,c)]
            right=[roof_surface(x,y,bb[0][1]) for y in (a,c)]
            low=[min(a,b)-.12 for a,b in zip(left,right)]
            high=[max(a,b)-.01 for a,b in zip(left,right)]
            outline=Polygon([(a,low[0]),(c,low[1]),(c,high[1]),(a,high[0])])
            side.solid(outline,-.05,.0,ROUGHCAST,'gable and connector seam')


def window_wall(b, x, y0, y1, z0, z1, windows, name, lod):
    f=Facade(b,(x,0),(0,1),name)
    bounds = [r[0] for r in windows]
    f.solid(box(y0,z0,y1,z1).difference(unary_union([box(*v) for v in bounds])),
            -.19,0,ROUGHCAST,'roughcast with window reveals')
    for i,(v,columns,rows,hood) in enumerate(windows):
        label=name+' | window '+str(i+1)
        sash(f,v,label,columns=columns,rows=rows,lod=lod)
        if hood:
            awning(f,v,label,lod=lod,detail_scale=.83)


def low_bay(b, x, y0, y1, windows, name, lod):
    top=7.27
    window_wall(b,x,y0,y1,.0,top,windows,name,lod)
    for y in (y0,y1):
        b.box(((RIGHT+x)*.5,y,top*.5),(x-RIGHT,.15,top),ROUGHCAST,label=name+' | return')
    # Nearly level terrace cover bounded by a continuous shallow plaster edge.
    plate(b,[(RIGHT,y0-.10,top+.13),(x+.15,y0-.10,top+.06),
             (x+.15,y1+.10,top+.06),(RIGHT,y1+.10,top+.13)],.15,LIME,name+' | cap')
    b.box((x+.04,(y0+y1)*.5,top-.14),(.19,y1-y0+.17,.13),CEMENT,label=name+' | drip')


def chimney(b):
    f=Facade(b,(RIGHT-.09,0),(0,1),'South roof | chimney')
    near,far=16.04,18.83
    top=14.01
    middle=(near+far)*.5
    holes=[]
    for y,z in [(middle-.52,13.01),(middle+.52,13.01),(middle,13.56)]:
        a=.14
        holes.append(Polygon([(y-a,z),(y,z-a),(y+a,z),(y,z+a)]))
    f.solid(box(near,11.73,far,top).difference(unary_union(holes)),-.99,0,ROUGHCAST,'three diamond openings')
    for h in holes:
        f.solid(h,-.74,-.72,SHADE,'recess behind diamond')
    b.box((RIGHT-.59,middle,top+.025),(1.14,far-near+.12,.08),LIME,label='South roof | chimney coping')


def add_side_roofs(b,lod=False):
    roof(b)
    high = [
        ((6.38,7.98,8.45,10.75),4,4,True),
        ((10.44,7.97,12.75,10.42),4,4,True),
    ]
    window_wall(b,RIGHT,FRONT,REAR,0.,EAVE,high,'South high wall',lod)
    for y in (FRONT+.13,REAR-.17):
        b.tube([(RIGHT+.06,y,.06),(RIGHT+.06,y,EAVE-.12)],.057,LIME,sides=8,label='South wall | rainwater pipe')
    b.box((RIGHT+.035,(FRONT+REAR)*.5,EAVE-.08),(.28,REAR-FRONT+.17,.17),LIME,label='South wall | high continuous eave')
    first=RIGHT+3.05/SCALE
    second=RIGHT+3.77/SCALE
    low_bay(b,first,6.04,9.04,[
        ((6.57,3.56,8.70,5.57),4,4,True),((6.64,.04,8.58,1.0),4,2,False)],
        'South first shallow bay',lod)
    # The deeper plane starts at the return of the broad forward bay. The back limit is obscured.
    low_bay(b,second,9.05,21.75,[
        ((9.66,3.54,12.20,5.62),5,4,True),((13.16,3.61,14.22,5.60),2,4,True),
        ((17.37,3.58,19.28,5.57),4,4,True),((9.68,.04,12.18,1.07),4,2,False)],
        'South second projecting bay',lod)
    chimney(b)
    # The hidden north end and the southeast eave are drawn only as plain limits of the roof.
    left=LAYOUT['left']['x0']
    b.box((left+.10,(FRONT+REAR)*.5,EAVE*.5),(.20,REAR-FRONT,EAVE),ROUGHCAST,label='North flank | plain closure')
    b.box(((left+RIGHT)*.5,REAR-.10,EAVE*.5),(RIGHT-left,.20,EAVE),ROUGHCAST,label='Rear | plain eave closure')
