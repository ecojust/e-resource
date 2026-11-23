"""Short visible return gable, separate slim light and outward-tilted awning sash."""
from math import cos, radians, sin
from shapely.geometry import box, Polygon, LineString
import numpy as np
from street314 import RED, GABLE, STONE, CAP, TIMBER, DEEP, GLASS, IRON

PROFILE=[(0,9.60),(.14,9.60),(1.00,10.43),(1.19,10.51),(2.91,10.36),(2.88,10.03),
         (3.53,10.16),(3.62,10.05),(3.56,9.90),(4.21,9.23),(4.43,9.18),(4.43,8.58)]
INNER=[(0,8.91),(.45,9.05),(1.46,9.76),(1.59,9.99),(2.53,9.91),(2.60,9.45),
       (3.05,9.49),(3.11,9.32),(4.03,8.79),(4.43,8.74)]
def add_return(b,lod):
    def face(poly,left,right,mat,name):
        b.prism(poly,left,right,lambda y,z,x:(x,y,z),mat,'314 northwest return '+name)
    def rectangle(a,z,q,h,left,right,mat,name):
        face(box(a,z,q,h),left,right,mat,name)
    shell=Polygon(PROFILE+[(4.43,0),(0,0)])
    large=box(1.44,6.75,3.06,8.53)
    narrow=box(.88,8.12,1.14,8.84)
    lower=box(1.26,1.65,2.94,3.79)
    shell=shell.difference(large).difference(narrow).difference(lower)
    face(shell,.0,.31,RED,'masonry')
    face(Polygon(PROFILE+list(reversed(INNER))).buffer(0).intersection(shell),-.061,.015,STONE,'stepped perimeter')
    line=LineString(PROFILE).buffer(.048,cap_style=2,join_style=2)
    face(line,-.128,.33,CAP,'dark gable-edge coping')
    for z,h in [(2.95,.36),(5.57,.52),(7.79,.34)]:
        face(shell.intersection(box(0,z,4.43,z+h)),-.023,.002,STONE,'horizontal render')
    # Behind the narrow street portal the 2015 photograph shows a tall dark
    # timber-framed lower opening and an angled pale masonry apron below it.
    rectangle(1.16,1.55,3.06,3.92,.47,.52,DEEP,'lower window dark inner wall')
    face(lower.difference(lower.buffer(-.096,join_style=2)),.12,.20,TIMBER,'lower recessed surround')
    rectangle(1.31,3.06,2.89,3.13,.135,.20,TIMBER,'lower transom')
    rectangle(2.09,3.11,2.14,3.72,.14,.19,TIMBER,'lower light mullion')
    for left,right in [(1.37,2.08),(2.15,2.83)]:
        rectangle(left,3.14,right,3.68,.204,.23,GLASS,'upper lights of lower window')
    rectangle(1.15,1.57,3.06,1.67,-.12,.20,STONE,'lower weathered sill')
    rectangle(1.12,.90,3.09,1.52,-.026,.018,STONE,'lower pale apron')
    rectangle(.77,6.52,3.69,8.71,.50,.53,DEEP,'deep recess')
    rectangle(.88,8.12,1.14,8.84,.092,.119,GLASS,'narrow daylight pane')
    face(narrow.difference(narrow.buffer(-.026,join_style=2)),.048,.10,TIMBER,'narrow frame')
    rectangle(.89,8.44,1.13,8.475,.048,.09,TIMBER,'narrow divider')
    rectangle(1.35,8.55,3.13,8.66,-.19,.025,STONE,'projecting window head')
    rectangle(1.31,8.66,3.16,8.76,-.24,.03,CAP,'lintel coping')
    for y in [1.46,3.04]:
        rectangle(y-.025,6.76,y+.025,8.53,.048,.109,TIMBER,'main frame')
    for z in [6.78,7.81,8.49]:
        rectangle(1.47,z-.025,3.03,z+.025,.043,.11,TIMBER,'main frame rail')
    # The upper sash tips out from a horizontal hinge. It is visible above the
    # gate parapet opposite, whereas much of the fixed lower part is hidden.
    a=radians(36)
    along=np.array([0.,1.,0.])
    down=np.array([-sin(a),0.,-cos(a)])
    normal=np.cross(along,down)
    hinge=np.array([.06,1.48,8.46])
    def piece(u,v,w,h,thick,mat,name):
        b.box(hinge+u*along+v*down,(w,h,thick),mat,[along,down,normal],'314 northwest return '+name)
    piece(.77,.395,1.52,.78,.024,GLASS,'top-hung glass')
    for u in [.025,1.505]:piece(u,.395,.05,.79,.057,TIMBER,'top-hung stile')
    for v in [.025,.765]:piece(.765,v,1.53,.05,.058,TIMBER,'top-hung rail')
    if not lod:
        for y in [1.51,2.97]:
            b.tube([(.048,y,7.86),(-.355,y,7.91)],.013,IRON,7,'314 northwest sash stay')
