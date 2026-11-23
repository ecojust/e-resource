"""Tiled cross roof, the west eave return and the plain rear closure of the recorded volume."""
import numpy as np
from shapely.geometry import Polygon,box
from east_roof_light import CUT as EAST_LIGHT_CUT,add_east_roof_light
from east_return import EAST_EAVE_PROFILE,EAST_WALL_U
from curved_veranda import veranda_interface
from house_layout import U,D,Z,LAYOUT,POST_SPAN
from hipped_tiles import tile
from materials import BASE,DARK,PLASTER,RIDGE,ROOF,STONE
from south_verandah import END,slab
from west_dormer import CUT,add_west_dormer
from west_wing import ORIGIN,SEAT,SOFFIT,WEST_CAL

REAR=(ORIGIN+4.05)*WEST_CAL
WEST_EAVE=SOFFIT*WEST_CAL
SOUTH_EAVE=D(-.0277)
SOUTH_RIDGE=D(1.074)
FRONT_HEIGHT=Z(.069)
RIDGE_HEIGHT=Z(.887)
WING_RIGHT=U(2.743)
HIP_START=U(1.82)

def panels(shape):
    if shape.is_empty:return
    if shape.geom_type=='Polygon':
        if shape.area>.00001:yield shape
    elif hasattr(shape,'geoms'):
        for part in shape.geoms:yield from panels(part)

def roof_face(f,facet,height,axis,lod,name,exclude=None):
    """Cut the pan rows into convex panels at openings before creating the closed folded tile strips."""
    xmin,dmin,xmax,dmax=facet.bounds
    pieces=[facet]
    if exclude is not None and facet.intersects(exclude):
        x0,d0,x1,d1=exclude.bounds
        masks=[box(-90,-90,x0,90),box(x1,-90,90,90),box(x0,-90,x1,d0),box(x0,d1,x1,90)]
        pieces=[q for mask in masks for q in panels(facet.intersection(mask))]
    a,b=(xmin,xmax) if axis==0 else (dmin,dmax)
    n=max(1,round((b-a)/(.34 if lod else .195)))
    for pc in pieces:
        f.b.prism(pc,-.095,-.029,lambda x,d,t:f.point(x,d,height(x,d)+t),DARK,name+' | eaves and underside')
        for i in range(n):
            lo=a+i*(b-a)/n;hi=a+(i+1)*(b-a)/n
            mask=box(lo,-90,hi,90) if axis==0 else box(-90,lo,90,hi)
            for section in panels(pc.intersection(mask)):
                tile(f,section,axis,lo,hi,height,lod,RIDGE if i%11==6 else ROOF,name+' | raised clay tile pans')
        low,high=(dmin,dmax) if axis==0 else (xmin,xmax)
        rows=max(1,round((high-low)/(.42 if lod else .335)))
        for i in range(1,rows):
            at=low+(high-low)*i/rows
            mask=box(-90,at,90,at+.024) if axis==0 else box(at,-90,at+.024,90)
            for band in panels(pc.intersection(mask)):
                f.b.prism(band,.006,.029,lambda x,d,t:f.point(x,d,height(x,d)+t),RIDGE,name+' | tile course joints')

def western_roof(f,lod):
    section=veranda_interface(LAYOUT)['rear_roof_section']
    start=section[0][1];bend=(ORIGIN+.51)*WEST_CAL;end=REAR+.17
    # Match the photographed flared edge at the front. At the west side the plane must bear on the six timber heads.
    rear_section=[(x,bend,max(0.,WEST_EAVE+.11-section[0][2])*(1-abs(i-2)/2*.15)+z) for i,(x,d,z) in enumerate(section)]
    rear_hip=[(x,end,z-(1.32 if i==2 else .42 if i in (1,3) else .08)) for i,(x,d,z) in enumerate(rear_section)]
    for q,r,tag in [(section,rear_section,'west wing'),(rear_section,rear_hip,'west rear slope')]:
        for i in range(4):
            x0,d0,z0=q[i];x1,_,z1=q[i+1];_,d1,h0=r[i];_,_,h1=r[i+1]
            def height(x,d):
                across=(x-x0)/(x1-x0);along=(d-d0)/(d1-d0)
                return (1-along)*(z0+(z1-z0)*across)+along*(h0+(h1-h0)*across)
            roof_face(f,box(x0,d0,x1,d1),height,1,lod,tag+' | '+['west flare','west main pitch','east main pitch','east flare'][i],CUT if i==1 else None)
        a=q[2];b=r[2];f.rail([(a[0],a[1],a[2]+.037),(b[0],b[1],b[2]+.037)],.048,RIDGE,tag+' | ridge coping',6 if lod else 10)
    # At X=0 the flared roof sits above the projecting bracket heads; the plaster rises only behind them.
    def wall_top(vertices):
        (xa,_,za),(xb,_,zb)=vertices[1:3]
        return za+(zb-za)*(0-xa)/(xb-xa)-.075
    face=f.face(0,bend,0,-1)
    face.solid(Polygon([(0,WEST_EAVE-.025),(bend,WEST_EAVE-.025),(bend,wall_top(section)),
                        (bend-start,wall_top(section)),(0,wall_top(rear_section))]),-.135,0,PLASTER,'west wing | plaster above timber heads')
    return rear_hip

def southern_roof(f,lod):
    x0=U(.58);xf=WING_RIGHT;xc=HIP_START;d0=SOUTH_EAVE;dc=SOUTH_RIDGE
    z0=FRONT_HEIGHT;zc=RIDGE_HEIGHT;xe=U(EAST_WALL_U)+.24
    front=lambda x,d:z0+(zc-z0)*(d-d0)/(dc-d0)
    hole=box(U(1.065)-.06,D(.33)-.055,U(1.646)+.06,D(.33)+1.01)
    roof_face(f,Polygon([(U(.755),d0),(xf,d0),(xc,dc),(x0,dc)]),front,0,lod,'south portico | principal tiled pitch',hole)
    def tri(a,b,c,name,axis,opening=None):
        points=np.array([a,b,c]);mat=np.column_stack((points[:,:2],np.ones(3)))
        dx,dy,z=np.linalg.solve(mat,points[:,2]);height=lambda x,d:z+dx*x+dy*d
        roof_face(f,Polygon(points[:,:2]),height,axis,lod,name,opening)
    # Eastern verge observed in photo 38; the sharp drop after station 2.48 is visible against the sky.
    edges=[(xf,d0,z0)]+[(xe,D(d),Z(z)) for d,z in EAST_EAVE_PROFILE]
    crest=[(xc,dc,zc),(xc,D(2.48),Z(.42)),(xc,D(3.27)+.06,Z(-.47))]
    tri(edges[0],edges[1],crest[0],'south portico | front hip',1)
    tri(edges[1],edges[2],crest[0],'east roof | garden hip',1)
    for i,(r1,r2) in enumerate(zip(crest,crest[1:])):
        a,b=edges[i+2:i+4];name='east roof | '+('long side pitch' if i==0 else 'rear folded pitch')
        tri(a,b,r1,name,1,EAST_LIGHT_CUT);tri(r1,b,r2,name,1,EAST_LIGHT_CUT)
        def height(x,d):return r1[2]+(r2[2]-r1[2])*(d-r1[1])/(r2[1]-r1[1])
        roof_face(f,box(x0,r1[1],xc,r2[1]),height,0,lod,'rear roof | '+('upper' if i==0 else 'lower')+' return')
    def capped(points,name,radius,mat):
        f.rail([(u,d,z+.02) for u,d,z in points],radius,mat,name,6 if lod else 10)
    capped([edges[0],crest[0]],'portico roof | front hip cap',.050,RIDGE)
    capped([(x0,dc,zc),crest[0]],'portico roof | cross ridge',.055,RIDGE)
    capped(crest,'east roof | return ridge',.046,RIDGE)
    capped(edges,'east roof | verge and gutter',.070,DARK)
    # Join the column capitals to the roof: horizontal soffit, fascia and drip bed are visible in photo 35.
    slab(f,box(U(.69),d0+.02,xf,D(.56)),Z(-.065)-.10,z0-.16,PLASTER,'south portico | cornice and soffit')
    slab(f,box(U(.69)-.02,d0-.014,xf+.012,D(.56)+.02),z0-.233,z0-.025,DARK,'south portico | eave fascia')
    slab(f,box(U(.69),d0+.013,xf-.015,D(.56)),z0-.303,z0-.227,DARK,'south portico | lower recessed eave moulding')
    rear_z=edges[-1][2];ridge_z=crest[-1][2];return x0,xc,xe,rear_z,ridge_z

def add_roof_and_returns(f,lod):
    add_west_dormer(f,lod)
    add_east_roof_light(f,lod)
    west=western_roof(f,lod);x0,xc,xe,eave_z,ridge_z=southern_roof(f,lod)
    # No view of the north windows is available. The rear cut follows the stepped visible mass without invented openings.
    rear=f.face(0,REAR,-1,0)
    gable=[(-x,z-.10) for x,d,z in west if 0<x<x0]
    gable.sort(reverse=True)
    west_z=west[2][2]; shape=Polygon([(0,0),(-x0,0),(-x0,west_z-.65),*reversed(gable),(0,west[1][2]-.10)])
    rear.solid(shape,-.135,0,PLASTER,'west | plain north return')
    end=D(3.27)
    rear=f.face(0,end,-1,0);shape=Polygon([(-x0,0),(-U(END),0),(-U(END),eave_z+.06),(-xc,ridge_z-.05),(-x0,ridge_z-.05)])
    rear.solid(shape,-.14,0,PLASTER,'east wing | plain north return')
    side=f.face(x0,end,0,-1)
    side.solid(Polygon([(0,0),(end-REAR,0),(end-REAR,Z(.42)-.10),(0,ridge_z-.06)]),-.14,0,PLASTER,'east wing | plain inset return')
    slab(f,Polygon([(0,0),(U(END),0),(U(END),end),(x0,end),(x0,REAR),(0,REAR)]),-.12,.002,BASE,'building | underside')
