"""The roof and gable above the hedges in the publisher's attributed pen drawing."""
import numpy as np
from shapely.geometry import Polygon, box
from photo_architecture import Facade

WALL='pale gable plaster'
ROOF='grey roof in pen drawing'
RIDGE='raised grey roof courses'
EDGE='dark bargeboards'
FRAME='weathered sash frames'
GLASS='tonal grey window lights'
STONE='pale chimney stone'
PALETTE={
    WALL:{'color':[.80,.79,.76],'roughness':.92},
    ROOF:{'color':[.343,.351,.349],'roughness':.85},
    RIDGE:{'color':[.40,.405,.396],'roughness':.83},
    EDGE:{'color':[.26,.255,.238],'roughness':.79},
    FRAME:{'color':[.301,.297,.264],'roughness':.79},
    GLASS:{'color':[.287,.315,.315],'roughness':.32,'metallic':.10},
    STONE:{'color':[.690,.681,.637],'roughness':.86},
    'carved pale stone':{'color':[.70,.69,.65],'roughness':.83},
}
HALF_GABLE=3.18
RIDGE_HEIGHT=5.18
EAVE=.74
MAIN_RIDGE=3.46
MAIN_DEPTH=3.5
FRONT_Y=-.92


def gable_height(x):
    return RIDGE_HEIGHT-(RIDGE_HEIGHT-EAVE)*abs(x)/HALF_GABLE


def main_height(y):
    return EAVE+(MAIN_RIDGE-EAVE)*y/MAIN_DEPTH


def roof(builder,lod):
    """Stop both receding surfaces where the drawing stops. Join at the true valleys."""
    cross_at_ridge=HALF_GABLE*(RIDGE_HEIGHT-MAIN_RIDGE)/(RIDGE_HEIGHT-EAVE)
    for side,extent in ((-1,8.05),(1,8.55)):
        sx=side*HALF_GABLE
        topx=side*cross_at_ridge
        wing=[(sx,0,EAVE),(side*extent,0,EAVE),(side*extent,MAIN_DEPTH,MAIN_RIDGE),(topx,MAIN_DEPTH,MAIN_RIDGE)]
        wing_faces=[(0,1,2),(0,2,3)] if side>0 else [(2,1,0),(3,2,0)]
        builder.add(wing,wing_faces,ROOF,'Long wings of main pitched roof')
        cross=[(0,FRONT_Y,RIDGE_HEIGHT),(sx,FRONT_Y,EAVE),(sx,0,EAVE),(topx,MAIN_DEPTH,MAIN_RIDGE),(0,MAIN_DEPTH,RIDGE_HEIGHT)]
        cross_faces=[(0,1,2),(0,2,3),(0,3,4)]
        if side<0:cross_faces=[tuple(reversed(t))for t in cross_faces]
        builder.add(cross,cross_faces,ROOF,'Sides of projecting cross-gable')
        builder.tube([(sx,0,EAVE+.014),(topx,MAIN_DEPTH,MAIN_RIDGE+.014)],.032,EDGE,6,'Valley seam')
        builder.tube([(0,FRONT_Y-.075,RIDGE_HEIGHT+.018),(sx,FRONT_Y-.075,EAVE+.018)],.071,EDGE,7 if lod else 12,'Projecting gable verge')
        for t in np.linspace(.035,.968,10 if lod else 19):
            y=t*MAIN_DEPTH;start=side*(HALF_GABLE+(cross_at_ridge-HALF_GABLE)*t)
            builder.tube([(start,y,main_height(y)+.009),(side*extent,y,main_height(y)+.009)],.017,RIDGE,4 if lod else 7,'Main slope tile laps')
        for t in np.linspace(.055,.966,9 if lod else 16):
            x=side*HALF_GABLE*t
            end_y=min(MAIN_DEPTH,(gable_height(x)-EAVE)*MAIN_DEPTH/(MAIN_RIDGE-EAVE))
            builder.tube([(x,FRONT_Y,gable_height(x)+.007),(x,end_y,gable_height(x)+.007)],.015,RIDGE,4 if lod else 7,'Gable roof tile laps')
        rear=[(0,MAIN_DEPTH,EAVE),(side*extent,MAIN_DEPTH,EAVE),(side*extent,MAIN_DEPTH,MAIN_RIDGE),(topx,MAIN_DEPTH,MAIN_RIDGE),(0,MAIN_DEPTH,RIDGE_HEIGHT)]
        builder.add(rear,[(0,2,1),(0,3,2),(0,4,3)] if side>0 else [(0,1,2),(0,2,3),(0,3,4)],ROOF,'Back of roof section')
        end=[(side*extent,0,EAVE),(side*extent,MAIN_DEPTH,EAVE),(side*extent,MAIN_DEPTH,MAIN_RIDGE)]
        builder.add(end,[(0,1,2)] if side>0 else [(2,1,0)],ROOF,'Closed outer roof section')
    builder.tube([(0,FRONT_Y-.06,RIDGE_HEIGHT+.012),(0,MAIN_DEPTH,RIDGE_HEIGHT+.012)],.058,RIDGE,8,'Gable ridge capping')


def facade(builder,lod):
    width=2*HALF_GABLE
    front=Facade(builder,(-HALF_GABLE,FRONT_Y),(HALF_GABLE,FRONT_Y),'Central pale gable')
    wall=Polygon([(-HALF_GABLE,0),(HALF_GABLE,0),(HALF_GABLE,EAVE-.025),(0,RIDGE_HEIGHT-.025),(-HALF_GABLE,EAVE-.025)])
    casement=box(-.845,1.04,.845,2.04)
    front.wall(0,RIDGE_HEIGHT,[casement],.27,WALL,wall)
    front.window(casement,4,3,FRAME,False,GLASS,'Gable grouped sash')
    front.box(0,2.10,1.99,.075,.21,.07,EDGE,'Dark projecting window lintel')
    for side in (-1,1):
        x,extent=side*HALF_GABLE,(-8.05 if side<0 else 8.55)
        builder.box(((x+extent)/2,.07,.48),(abs(extent-x),.14,.68),WALL,label='Visible eaves wall strip')
        builder.box(((x+extent)/2,-.05,EAVE),(abs(extent-x)+.08,.25,.115),EDGE,label='Dark lines below long eaves')
    roof(builder,lod)
    # The drawing shows the shafts only above the overlapping roof pitches.
    for x,y,top in ((-2.68,1.42,4.36),(1.66,2.17,4.87)):
        z=max(main_height(y),gable_height(x))-.11
        builder.box((x,y,(z+top)/2),(.42,.46,top-z),STONE,label='Chimney shafts')
        builder.box((x,y,top-.12),(.46,.50,.11),RIDGE,label='Chimney upper bands')
        builder.box((x,y,top+.04),(.60,.57,.13),STONE,label='Broad chimney caps')
        if not lod:
            for edge in (-.12,.12):builder.box((x+edge,y-.29,top+.03),(.031,.018,.075),EDGE,label='Small cap joints')
