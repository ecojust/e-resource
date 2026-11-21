"""Two adjoining faces of the fifth-storey corner of the Kakuta Apartments."""
from math import cos, sin, pi, radians
from shapely.geometry import box, Polygon
from shapely.ops import unary_union

WALL='buff mineral render'
TRIM='projecting render'
SILL='sandstone sill'
JOIN='render fillet'
METAL='dark window frame'
CLEAR='blue reflected glazing'
TOP='shadowed transom glass'
HOOD='maroon canopy edge'
UNDER='canopy underside'
BRACKET='painted steel brackets'
PALETTE={name:dict(color=colour,roughness=rough) for name,colour,rough in [
    (WALL,[.52,.451,.32],.89),(TRIM,[.56,.487,.355],.86),(SILL,[.60,.51,.343],.84),
    (JOIN,[.445,.373,.265],.88),(METAL,[.048,.052,.053],.42),(CLEAR,[.117,.173,.231],.19),
    (TOP,[.048,.074,.088],.23),(HOOD,[.154,.067,.071],.69),(UNDER,[.107,.089,.084],.80),(BRACKET,[.098,.077,.070],.74)]}
HALF_TURN=radians(49.4811166425/2)
FACET_LENGTH=3.35
WINDOWS=(1.24,2.36)
R=.444
RISE=.303
SPRING=1.585
BASE=.762
HEIGHT=2.77

def point(side,u,y,z):
    """Map horizontal distance from the shared arris, depth and height to local metres."""
    return (side*(u*cos(HALF_TURN)-y*sin(HALF_TURN)),
            u*sin(HALF_TURN)+y*cos(HALF_TURN), z)

def face(builder,side,polygon,front,back,material,label):
    if polygon.is_empty:return
    # Builder requires a right-handed (u,z,extrusion) basis on either face.
    if side==1:
        builder.prism(polygon,-back,-front,lambda u,z,d:point(side,u,-d,z),material,label)
    else:
        builder.prism(polygon,front,back,lambda u,z,d:point(side,u,d,z),material,label)

def rect(builder,side,u0,u1,z0,z1,front,back,material,label):
    face(builder,side,box(u0,z0,u1,z1),front,back,material,label)

def sash(cx,rx,rise,spring,bottom,segments):
    return Polygon([(cx-rx,bottom),(cx+rx,bottom)]+[
        (cx+rx*cos(pi*i/segments),spring+rise*sin(pi*i/segments)) for i in range(segments+1)])

def model(builder,lod=False):
    n=14 if lod else 40
    arris=Polygon([(0,-.091/cos(HALF_TURN)),point(1,0,-.091,0)[:2],(0,.02),point(-1,0,-.091,0)[:2]])
    builder.plan_prism(arris,0,HEIGHT,TRIM,'Fold in central cast pier')

    for side,side_name in [(-1,'Left'),(1,'Right')]:
        wall=box(0,0,FACET_LENGTH,HEIGHT).difference(unary_union([sash(u,R,RISE,SPRING,BASE,n) for u in WINDOWS]))
        face(builder,side,wall,0,.245,WALL,side_name+' splayed window wall')
        # The photographed arris has a broad raised central band and a small edge fillet.
        rect(builder,side,0,.151,0,HEIGHT,-.091,.022,TRIM,side_name+' raised central pier')
        rect(builder,side,.151,.207,0,HEIGHT,-.047,.012,TRIM,side_name+' pier shoulder')
        rect(builder,side,.208,.225,0,HEIGHT,-.012,.012,JOIN,side_name+' narrow trailing arris')
        for index,u in enumerate(WINDOWS):
            name=side_name+' '+('inner' if index==0 else 'outer')
            clear=sash(u,R-.058,RISE-.051,SPRING-.007,BASE+.056,n)
            ring=sash(u,R,RISE,SPRING,BASE,n).difference(clear)
            face(builder,side,ring,.114,.176,METAL,name+' recessed arch frame')
            face(builder,side,clear.intersection(box(u-R,BASE,u+R,1.374)),.172,.194,CLEAR,name+' two lower casements')
            face(builder,side,clear.intersection(box(u-R,1.374,u+R,2.0)),.172,.194,TOP,name+' curved transom glass')
            rect(builder,side,u-R+.043,u+R-.043,1.348,1.385,.105,.178,METAL,name+' transom rail')
            rect(builder,side,u-.019,u+.019,BASE+.036,1.369,.117,.178,METAL,name+' lower centre stile')
            rect(builder,side,u-R-.044,u+R+.044,BASE-.077,BASE-.012,-.102,.176,SILL,name+' sill shelf')
            rect(builder,side,u-R-.025,u+R+.025,BASE-.092,BASE-.077,-.052,.17,TRIM,name+' sill drip')
            # Individual metal covers meet above each pair, with dark edges and inset undersides.
            left=u-.552;right=u+.552
            rect(builder,side,left,right,2.121,2.168,-.408,.007,UNDER,name+' canopy soffit')
            rect(builder,side,left,right,2.168,2.194,-.420,.012,HOOD,name+' canopy top')
            rect(builder,side,left,right,2.103,2.174,-.422,-.393,HOOD,name+' canopy front rim')
            for k in (left,right-.023):
                rect(builder,side,k,k+.023,2.112,2.174,-.416,.014,HOOD,name+' canopy side return')

            for fastener in [-.365,.365]:
                section=Polygon([(-.294,2.131),(.013,2.131),(.013,1.962),(-.040,1.962)])
                builder.prism(section,-.023,.023,lambda y,z,t:point(side,u+fastener+side*t,y,z),
                              BRACKET,name+' folded triangular supporting bracket')
