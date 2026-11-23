"""The set-back upper window room seen from Changle Road.

Only the open 2017 right casement is visible in depth. Winter observations
locate the cream return, its neighbouring white window and the dark timber
under the compact tile roof. The back is a plain closure of the surveyed cap.
"""
from math import cos, radians, sin
from shapely.geometry import box
from photo_architecture import Facade
from street_finishes import GREEN, UPPER
from hipped_eaves import BOARD, CAP, DRIP, TILES, WOOD, _beam, _caps, _prism

FACE_Y = 4.43
BACK_Y = 8.11
LEFT = -.28
RIGHT = 5.50
FLOOR = 5.18
WALL_TOP = 9.86
WHITE = 'Changle upper room | pale metal sliding frame'
GLASS = 'Changle upper room | shaded blue grey glass'
LIGHT = 'Changle upper room | light reflected in open pane'
RECESS = 'Changle upper room | interior shadow'
PALETTE = {
    WHITE: {'color': [.698,.693,.646], 'metallic': .14,'roughness': .48},
    GLASS: {'color': [.22,.275,.289], 'roughness': .33,'metallic': .13},
    LIGHT: {'color': [.59,.664,.64], 'roughness': .35,'metallic': .13},
    RECESS: {'color': [.036,.042,.040], 'roughness': .94},
}
GREY_BOUNDS = (.54,8.68,1.72,9.70)
GREEN_BOUNDS = (3.55,7.02,5.13,9.40)
TRANSOM = 8.40

def block(builder,x0,x1,y0,y1,z0,z1,material,name):
    builder.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),material,label='337 high room | '+name)

def window_ring(face,bounds,width,back,front,material,label):
    x0,z0,x1,z1=bounds
    face.prism(box(x0,z0,x1,z1).difference(box(x0+width,z0+width,x1-width,z1-width)),back,front,material,label)

def insert_windows(builder,facade,lod):
    x0,z0,x1,z1 = GREY_BOUNDS
    window_ring(facade,GREY_BOUNDS,.047,-.082,-.018,WHITE,'white sliding frame')
    middle=(x0+x1)/2
    for i,(a,b) in enumerate(((x0+.044,middle+.022),(middle-.013,x1-.044))):
        z=z0+.046
        offset=-.033*i
        window_ring(facade,(a,z,b,z1-.044),.029,-.112+offset,-.069+offset,WHITE,'white double rail')
        facade.prism(box(a+.029,z+.029,b-.029,z1-.073),-.104+offset,-.096+offset,GLASS,'white window glass')
    block(builder,x0-.035,x1+.035,FACE_Y-.065,FACE_Y+.08,z0-.043,z0,WHITE,'shallow white sill')
    x0,z0,x1,z1=GREEN_BOUNDS
    window_ring(facade,GREEN_BOUNDS,.070,-.109,-.031,GREEN,'green opening lining')
    facade.prism(box(x0+.061,TRANSOM-.037,x1-.061,TRANSOM+.037),-.119,-.045,GREEN,'transom rail')
    middle=(x0+x1)/2
    for a,b in ((x0+.07,middle+.017),(middle-.017,x1-.07)):
        window_ring(facade,(a,TRANSOM+.033,b,z1-.065),.042,-.117,-.062,GREEN,'two upper fixed lights')
        facade.prism(box(a+.041,TRANSOM+.075,b-.041,z1-.107),-.115,-.107,GLASS,'transom dark reflection')
    # The 2017 lower opening shows the narrow light edge of a right leaf.
    # Its left half lies behind the street tree. The interior ends in shadow.
    hinge=(x1-.060,FACE_Y+.048)
    leaf_width=(x1-x0-.16)*.5
    angle=radians(106)
    tip=(hinge[0]-leaf_width*cos(angle),hinge[1]-leaf_width*sin(angle))
    leaf=Facade(builder,tip,hinge,'337 high room | green right open casement')
    w=leaf.length
    bounds=(-w/2,z0+.068,w/2,TRANSOM-.042)
    window_ring(leaf,bounds,.045,-.019,.019,GREEN,'open rail')
    leaf.prism(box(-w/2+.045,bounds[1]+.045,w/2-.045,bounds[3]-.045),-.006,.003,LIGHT,'pale edge reflection')
    if not lod:
        leaf.prism(box(-w/2+.042,(bounds[1]+bounds[3])/2-.012,w/2-.042,(bounds[1]+bounds[3])/2+.012),
                   -.015,.015,GREEN,'open sash crossbar')
    block(builder,x0+.040,x1-.040,FACE_Y+.52,FACE_Y+.54,z0+.038,TRANSOM+.012,RECESS,'lower opening rear shadow')
    block(builder,x0,x0+.046,FACE_Y+.15,FACE_Y+.53,z0+.06,TRANSOM-.01,RECESS,'obscured left inner return')
    block(builder,x0-.065,x1+.065,FACE_Y-.095,FACE_Y+.12,z0-.075,z0,WHITE,'painted projecting sill')

def cap_roof(builder,lod):
    import numpy as np
    corners=np.array([[-.916,3.829,9.971],[6.008,3.829,9.971],[6.008,8.731,9.971],[-.916,8.731,9.971]])
    left=np.array([1.396,5.999,11.877]);right=np.array([4.500,5.999,11.877])
    # Both ridge ends share one Y so the lapped tile courses and their timber deck are coplanar.
    slopes=[(corners[0],corners[1],left,right),(corners[1],corners[2],right,right),
            (corners[2],corners[3],right,left),(corners[3],corners[0],left,left)]
    for i,(a,b,ta,tb) in enumerate(slopes):
        end_is_point=np.array_equal(ta,tb)
        outline=[a,b,tb] if end_is_point else [a,b,tb,ta]
        _prism(builder,outline,[0,0,-.125],BOARD,'337 upper roof | timber deck')
        rows=6 if lod else 12
        for n in range(rows):
            s0=n/rows;s1=min(1,(n+1)/rows+.006)
            p0=a+(ta-a)*s0;p1=b+(tb-b)*s0
            p2=b+(tb-b)*s1;p3=a+(ta-a)*s1
            surface=[p0,p1,p2] if end_is_point and s1==1 else [p0,p1,p2,p3]
            # The small tilt at each lap makes the tile courses legible from the east.
            pts=[p+np.array([0,0,.014 if j<2 else .003]) for j,p in enumerate(surface)]
            _prism(builder,pts,[0,0,-.020],TILES[(i+n//3)%3],'337 upper roof | lapped clay course')
        _beam(builder,a,b,.042,.13,DRIP,'337 upper roof | thin dark edge')
        inside=(ta+tb-a-b)*.5;inside[2]=0;inside/=np.linalg.norm(inside)
        edge=a+np.array([0,0,-.115]);end=b+np.array([0,0,-.115])
        _beam(builder,edge+.06*inside,end+.06*inside,.042,.15,WOOD,'337 upper roof | red fascia')
        if i!=2:
            count=round(np.linalg.norm(end-edge)/(.83 if lod else .47))
            for j in range(count):
                p=edge+(end-edge)*(j+.50)/count
                _beam(builder,p+.09*inside,p+.57*inside,.049,.125,WOOD,'337 upper roof | exposed dark rafter end')
    for a,b in ((corners[0],left),(corners[1],right),(corners[2],right),(corners[3],left),(left,right)):
        _caps(builder,a,b,lod,'337 upper roof | ridge tile')

def add_upper_storey(builder,lod=False):
    for mat,props in PALETTE.items():
        builder.palette.setdefault(mat,props)
    face=Facade(builder,(-1,FACE_Y),(1,FACE_Y),'337 high room')
    skin=box(LEFT,FLOOR,RIGHT,WALL_TOP)
    for bounds in (GREY_BOUNDS,GREEN_BOUNDS):
        skin=skin.difference(box(*bounds))
    face.prism(skin,-.20,0,UPPER,'warm roughcast with both openings')
    block(builder,LEFT,LEFT+.16,FACE_Y+.20,BACK_Y,FLOOR,WALL_TOP,UPPER,'plain eastern return')
    block(builder,RIGHT-.16,RIGHT,FACE_Y+.20,BACK_Y,FLOOR,WALL_TOP,UPPER,'plain western return')
    block(builder,LEFT+.16,RIGHT-.16,BACK_Y-.16,BACK_Y,FLOOR,WALL_TOP,UPPER,'rear extent closure')
    block(builder,LEFT+.16,RIGHT-.16,FACE_Y+.20,BACK_Y-.16,FLOOR,FLOOR+.10,RECESS,'room base')
    block(builder,LEFT,RIGHT,FACE_Y,BACK_Y,WALL_TOP-.012,WALL_TOP+.04,BOARD,'ceiling above both window heads')
    insert_windows(builder,face,lod)
    cap_roof(builder,lod)
