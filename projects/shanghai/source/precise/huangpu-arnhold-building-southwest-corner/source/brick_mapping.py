"""Metre-based masonry coordinates along the two straight walls and their radiused junction."""
from math import atan2,cos,hypot,pi,sin,tan
BRICK='Arnhold exposed red brick'
WEST_NORTH=(-4.903539,23.679043)
WEST_CHORD=(-3.643346,2.101508)
T=(.058299,-.998299)
CORNER_RADIUS=3.65
TURN=atan2(-T[1],T[0])
VIRTUAL=(WEST_CHORD[0]-WEST_CHORD[1]*T[0]/T[1],0.)
TANGENT_DISTANCE=CORNER_RADIUS*tan(TURN/2)
WEST_TANGENT=(VIRTUAL[0]-T[0]*TANGENT_DISTANCE,-T[1]*TANGENT_DISTANCE)
SOUTH_TANGENT=(VIRTUAL[0]+TANGENT_DISTANCE,0.)
ARC_CENTER=(SOUTH_TANGENT[0],CORNER_RADIUS)
ARC_FIRST=-pi/2-TURN
ARC_LENGTH=CORNER_RADIUS*TURN
WEST_LIMIT=(WEST_TANGENT[0]-T[0]*12.5,WEST_TANGENT[1]-T[1]*12.5)
SOUTH_LIMIT=(18.75,0.)
EDGES={'Sichuan':(WEST_LIMIT,WEST_TANGENT),'Jiujiang':(SOUTH_TANGENT,SOUTH_LIMIT)}

def lengths_at(label,x,y):
    side=label.split('/')[0]
    if side=='Corner':
        angle=atan2(y-ARC_CENTER[1],x-ARC_CENTER[0])
        if angle>0:angle-=2*pi
        return 12.5+CORNER_RADIUS*(angle-ARC_FIRST)
    a,b=EDGES[side];dx,dy=b[0]-a[0],b[1]-a[1]
    origin=0. if side=='Sichuan' else 12.5+ARC_LENGTH
    return origin+((x-a[0])*dx+(y-a[1])*dy)/hypot(dx,dy)

def brick_uv(label,vertex):
    # The atlas spans 32 m. On Jiujiang the origin moves by 16 m (64 bricks),
    # preserving the running bond across the radiused junction.
    along=lengths_at(label,*vertex[:2])
    if label.startswith('Jiujiang/'):along-=16.
    return ((along+.66)/32.,(vertex[2]+.25)/32.)
