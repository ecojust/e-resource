"""Visible west bay, its open-sided lower storey and the multi-hipped red tiled roof."""
from pathlib import Path
import json
import math

import numpy as np
from shapely import set_precision
from shapely.geometry import LineString, Polygon, box
from shapely.ops import split, unary_union
from shapely.geometry.polygon import orient
from photo_architecture import Facade, pieces

HERE=Path(__file__).absolute().parent
WALL='Yihe | buff courtyard masonry'
STONE='Yihe | buff stone balcony'
EDGE='Yihe | weathered pale coping'
WOOD='Yihe | west painted wood casements'
GLASS='Yihe | west cool reflected glass'
ROOF='Yihe | fired terracotta tile'
LIP='Yihe | clay tile nose'
FASCIA='Yihe | oxblood eave board'
GABLE='Yihe | pale triangular pediment'
MASS='Yihe | muted rear massing'
PALETTE={MASS:dict(color=[.46,.446,.391],roughness=.96),WALL:dict(color=[.60,.58,.48],roughness=.93),STONE:dict(color=[.59,.55,.44],roughness=.93),
         EDGE:dict(color=[.61,.58,.48],roughness=.92),WOOD:dict(color=[.11,.040,.032],roughness=.72),
         GLASS:dict(color=[.19,.24,.25],roughness=.33,metallic=.14),ROOF:dict(color=[.34,.095,.047],roughness=.85),
         LIP:dict(color=[.39,.123,.062],roughness=.82),FASCIA:dict(color=[.207,.055,.038],roughness=.83),
         GABLE:dict(color=[.66,.62,.52],roughness=.91)}

def window(face,opening,columns,transom,label,lod=False):
    l,z,r,h=opening.bounds
    border=.045;inner=opening.buffer(-border,join_style=2)
    bars=[box(l+(r-l)*i/columns-.018,z,l+(r-l)*i/columns+.018,h)for i in range(1,columns)]
    bars.append(box(l,z+(h-z)*transom-.025,r,z+(h-z)*transom+.025))
    if not lod and columns>=5:
        for i in range(columns):
            mid=l+(i+.5)*(r-l)/columns
            bars.append(box(mid-.013,z+(h-z)*transom,mid+.013,h))
    panes=inner.difference(unary_union(bars))
    face.prism(opening.difference(panes),-.13,-.055,WOOD,label+' red transoms and stiles')
    face.prism(inner,-.155,-.141,GLASS,label+' glazing')
    if not lod:
        rim=opening.buffer(.095,join_style=2).difference(opening)
        face.prism(rim,-.026,.024,EDGE,label+' window reveals')

def west_bay(b,lod):
    section=json.loads((HERE.parent/'measurements/balustrade-sections.json').read_bytes())['upper west bay']
    plan=np.asarray(section['plan']);z0=section['z0'];x=plan[1,0];ystop=plan[2,1]
    # 05 frames the short return; 04 shows the long run of casements, solid panels and square supports.
    # The west wall is limited to the measured openwork bay; the farther curved entrance is separately identifiable.
    wall=Facade(b,(x,ystop+.04),(x,0.),'West return | main wall')
    center=(ystop+.04)/2
    high=[(2.48,3.90),(4.62,5.91),(6.85,7.97)]
    holes=[box(center-bb,11.57,center-aa,14.70)for aa,bb in high]
    lower=box(center-7.73,.28,center-2.72,4.20)
    wall.wall(0,15.10,[lower,*holes],.23,WALL)
    for i,hole in enumerate(holes):
        window(wall,hole,2,.75,'upper casement '+str(i+1),lod)
    window(wall,lower,8,.75,'shaded ground-floor window',lod)
    floor=5.02;soffit=4.79
    planpoly=Polygon(plan)
    b.plan_prism(planpoly.buffer(.042,join_style=2),soffit,floor,EDGE,'West bay | square cantilever floor')
    for idx in (0,3):
        corner=plan[idx].copy()
        corner[0]+=.16;corner[1]+=.14 if idx==0 else -.14
        b.box((*corner,(.085+soffit)/2),(.38,.40,soffit-.085),STONE,label='West bay | square post under glazed bay')
    for a,c,title in ((0,1,'south facing short return'),(3,0,'broad west-facing sash'),(2,3,'back cheek')):
        side=Facade(b,plan[a],plan[c],'West bay | '+title)
        length=side.length
        if a==0:
            aperture=box(-length/2+.222,7.17,-length/2+1.548,9.86)
            openings=[aperture]
        elif a==3:
            aperture=box(-length/2+.31,6.67,length/2-.30,10.04)
            openings=[aperture]
        else:
            openings=[]
        side.wall(floor,z0,openings,.19,WALL)
        for aperture in openings:window(side,aperture,2 if a==0 else 8,.73,title,lod)
        side.prism(box(-length/2,floor+.02,length/2,floor+.27),-.19,.036,STONE,'carved frieze')
        if a!=2 and not lod:
            repeats=max(2,round(length/.27))
            strokes=[]
            for i in range(repeats):
                u=-length/2+(i+.5)*length/repeats
                strokes.append(LineString([(u-.106,floor+.235),(u,floor+.073),(u+.106,floor+.235)]).buffer(.014,cap_style=2,join_style=2))
            side.prism(unary_union(strokes),.034,.051,EDGE,'incised chevrons below bay windows')
    return section

def plane_poly(poly,coords,height):
    z=np.array([height(x,y) for x,y in coords])
    return poly,np.linalg.solve(np.c_[coords,np.ones(len(coords))],z)

def hip(x0,y0,x1,y1,eave,pitch):
    """Four planar roof slopes meeting on the longer axis of a rectangle."""
    midx=(x0+x1)/2;midy=(y0+y1)/2
    run=min(x1-x0,y1-y0)/2;sw=(x0,y0);se=(x1,y0);ne=(x1,y1);nw=(x0,y1)
    if x1-x0>=y1-y0:
        a=(x0+run,midy);c=(x1-run,midy)
        facets=[[sw,se,c,a],[se,ne,c],[ne,nw,a,c],[nw,sw,a]]
    else:
        a=(midx,y0+run);c=(midx,y1-run)
        facets=[[sw,se,a],[se,ne,c,a],[ne,nw,c],[nw,sw,a,c]]
    def height(x,y):return eave+pitch*min(x-x0,x1-x,y-y0,y1-y)
    return [plane_poly(Polygon(f),np.array(f[:3]),height)for f in facets]

def upper_surfaces(facets):
    # Clip each facet wherever another wing's roof rises above it. Coincident planes
    # retain a single outside skin. Roof troughs and hips consequently share vertices.
    for i,(shape,plane) in enumerate(facets):
        area=shape
        for j,(other,p)in enumerate(facets):
            if i==j or not area.intersects(other):continue
            overlap=area.intersection(other)
            if overlap.area<1e-7:continue
            delta=p-plane;dx,dy,c=delta;mag=np.hypot(dx,dy)
            if mag<1e-7:
                if c>1e-6 or(abs(c)<1e-6 and j<i):area=area.difference(other)
                continue
            anchor=-c*delta[:2]/mag**2;along=np.array([-dy,dx])*100/mag
            line=LineString([anchor-along,anchor+along])
            for piece in split(overlap,line).geoms:
                if piece.area<1e-7:continue
                center=piece.representative_point()
                if dx*center.x+dy*center.y+c>0:area=area.difference(piece)
        for fragment in pieces(set_precision(area,1.e-6)):
            if fragment.area>.003:yield fragment,plane

def roof_mesh(b,lod):
    survey=json.loads((HERE.parent/'measurements/roof-and-wing-evidence.json').read_bytes())
    eave=survey['eave_top_m'];pitch=survey['pitch_rise_over_run']
    footprints=survey['hip_rectangle_bounds_m']
    planes=[item for rect in footprints for item in hip(*rect,eave,pitch)]
    for i,(shape,p) in enumerate(upper_surfaces(planes)):
        a,c,z=p
        def surface(x,y,d):return (x,y,a*x+c*y+z+d)
        b.prism(shape,-.137,0.,surface,ROOF,'Main roof | red hipped slope '+str(i+1))
        if not lod:
            # Coarse tiles cast narrow shadows at the noses of photographed clay courses.
            norm=np.hypot(a,c);slope=np.array([a,c])/norm;across=np.array([-slope[1],slope[0]])
            verts=np.asarray(shape.exterior.coords);dist=verts@slope
            for t in np.arange(np.ceil(min(dist)/.35)*.35,max(dist),.35):
                center=t*slope;line=LineString([center-across*60,center+across*60])
                strip=shape.intersection(line.buffer(.012,cap_style=2))
                for bit in pieces(set_precision(strip,1.e-6)):
                    if bit.area>.001:b.prism(bit,-.002,.014,surface,LIP,'Main roof | clay tile courses '+str(i+1))
    outline=unary_union([box(*rect)for rect in footprints])
    fascia=outline.difference(outline.buffer(-.31,join_style=2))
    b.plan_prism(fascia,eave-.23,eave-.126,FASCIA,'Main roof | dark red eave fascia')
    # Continuous horizontal soffit physically bears on the front and upper west wall;
    # its perimeter follows the independent roof ridges and the adjusted west return.
    b.plan_prism(outline,eave-.32,eave-.23,EDGE,'Main roof | continuous pale soffit')
    shell=orient(outline.buffer(-.32,join_style=2),sign=1.)
    west_end=json.loads((HERE.parent/'measurements/balustrade-sections.json').read_bytes())['upper west bay']['plan'][2][1]
    boundary=list(shell.exterior.coords)
    for (a,c),(d,e) in zip(boundary,boundary[1:]):
        if abs(c-e)<.00001 and max(c,e)<.2:
            continue
        if abs(d-a)<.00001 and abs(a+10.43)<.15:
            if max(c,e)<=west_end+.045:
                continue
            c=max(c,west_end+.030);e=max(e,west_end+.030)
        if np.hypot(d-a,e-c)>.02:
            rear=Facade(b,(a,c),(d,e),'Indicative block | courtyard roof footprint')
            rear.wall(-.012,15.13,(),.24,MASS)
    g=survey['pediment'];l,r,y,base,apex=g['x0'],g['x1'],g['y'],g['shoulder_z'],g['apex_z'];x=g['apex_x']
    face=Facade(b,(l,y),(r,y),'Main roof | observed triangular pediment')
    half=(r-l)/2;u=x-(l+r)/2
    face.prism(Polygon([(-half,base-.47),(half,base-.47),(half,base),(u,apex),(-half,base)]),-.16,.012,GABLE,'triangular pale infill')
    back=g['return_m']
    # Each folded terracotta verge returns to the pitched body. The return depth is a modelling estimate.
    for a,h,bb,hh in ((l,base,x,apex),(x,apex,r,base)):
        slope=(hh-h)/(bb-a)
        b.prism(box(a,y-.081,bb,y+back),-.090,0,
                lambda xx,yy,d:(xx,yy,h+(xx-a)*slope+d),ROOF,'Main roof | gable tile return')
        left=a-(l+r)/2;right=bb-(l+r)/2
        panel=Polygon([(left,h),(right,hh),(right,hh-.140),(left,h-.140)])
        face.prism(panel,-.11,.060,FASCIA,'raised red verge')
    return survey

def add_west_wing_and_roof(builder,lod=False):
    for name,value in PALETTE.items():builder.palette.setdefault(name,value)
    west_bay(builder,lod)
    return roof_mesh(builder,lod)
