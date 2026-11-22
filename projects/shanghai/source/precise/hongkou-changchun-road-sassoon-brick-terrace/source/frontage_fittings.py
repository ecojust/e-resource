"""Plate 319, paired condensers and the metal cage at the end of the photographed run."""
import json
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon
from frontage_coordinates import facade_point
from terrace_wall import section,block,finish,IRON,WOOD

ENAMEL='North wall fittings | weathered cream enamel'
MESH='North wall fittings | condenser grille'
SIGN='North wall fittings | green number plate'
LETTER='North wall fittings | white lettering'
RAIL='North wall fittings | weathered metal'
PALETTE={ENAMEL:finish([182,179,164],.72,.13),MESH:finish([87,93,88],.68,.13),SIGN:finish([42,101,75],.71,.14),
         LETTER:finish([211,209,181],.82),RAIL:finish([84,91,79],.76,.18)}
DATA=Path(__file__).resolve().parents[1]/'measurements'
def path_on(b,pts,y,r,m,label,lod):
    b.tube([facade_point(u,v,y) for u,v in pts],r,m,7 if lod else 12,label)
def rect_on(b,l,r,t,bottom,y,k,mat,label):
    pts=[facade_point(u,v,y)[::2]for u,v in [(l,t),(r,t),(r,bottom),(l,bottom)]]
    section(b,Polygon(pts),y,k,mat,label)
def unit(b,u,v,width,height,wall,lod,n):
    front=wall-.43
    l=facade_point(u-width/2,v,front)[0];r=facade_point(u+width/2,v,front)[0]
    z=facade_point(u,v,front)[2];hi=facade_point(u,v-height/2,front)[2];lo=2*z-hi
    title='North wall fittings | '+n
    block(b,l,r,front,wall-.035,lo,hi,ENAMEL,title+' casing')
    cx=l+(r-l)*.43;rz=(hi-lo)*.385;rx=min((r-l)*.35,rz)
    curve=[(cx+rx*np.cos(a),z+rz*np.sin(a))for a in np.linspace(0,2*np.pi,23 if lod else 37)[:-1]]
    section(b,Polygon(curve),front-.008,front+.003,MESH,title+' fan recess')
    for frac in ([-.57,-.17,.25,.65] if lod else np.linspace(-.8,.8,9)):
        dz=rz*frac;dx=rx*(1-frac*frac)**.5
        block(b,cx-dx,cx+dx,front-.016,front-.004,z+dz-.008,z+dz+.008,ENAMEL,title+' grille slats')
    for x in [l+.12*(r-l),r-.12*(r-l)]:
        b.tube([(x,wall-.014,lo-.16),(x,front+.06,lo-.016),(x,wall-.04,lo-.016)],.016,RAIL,7,title+' wall brackets')
def add_fittings(b,lod=False):
    pipes=json.loads((DATA/'north-frontage-drainpipes.json').read_bytes())
    for k,rows in pipes.items():
        y=-.105
        mid=[facade_point(*r[:2],y)for r in rows]
        # Extend only as far as the photographed parapet and the canopy over the lower door.
        x1,_,z1=mid[0];xe,_,ze=mid[-1];slope=(x1-xe)/(z1-ze)
        def axis(z):return(x1+(z-z1)*slope,y,z)
        base=facade_point(rows[-1][0],416,y)[2];top=facade_point(rows[0][0],154,y)[2]
        b.tube([axis(base),*reversed(mid),axis(top-.19),(axis(top)[0],-.22,top-.02)],.045,IRON,10 if lod else 16,'North face | '+k+' drainpipe')
        for z in np.arange(base+.36,top-.26,1.58):
            b.tube([axis(z),axis(z+.037)],.055,IRON,8 if lod else 14,'North face | '+k+' pipe socket')
    # The enamel plate labels the doorway of the building behind the free-standing gate.
    rect_on(b,185.1,197.4,412.0,420.2,-.092,-.065,SIGN,'North face | enamel plate 319')
    digits={'3':[[(0,0),(.7,0),(1,.2),(.6,.48),(.25,.5),(.72,.54),(1,.76),(.82,1),(.05,1)]],
            '1':[[ (.12,.22),(.56,0),(.56,1)],[(.10,1),(.95,1)]],
            '9':[[(.98,.48),(.18,.48),(0,.24),(.15,.02),(.82,0),(1,.23),(.94,.72),(.53,1),(.15,1)]]}
    for i,ch in enumerate('319'):
        for stroke in digits[ch]:
            path_on(b,[(186.3+i*3.45+2.4*x,413.4+5.3*h)for x,h in stroke],-.096,.0068,LETTER,'North face | door number '+ch,lod)
    for u,v,width,height,wall,n in [(768.5,123,29,18,-.91,'attic inner'),(817.5,130,28,18,-.91,'attic outer'),
            (743,237,30,18,-.03,'third floor'),(779,383,32,18,-.36,'second floor left'),(825,382,30,19,-.36,'second floor right')]:
        unit(b,u,v,width,height,wall,lod,n)
    # The oblique struts are evident above the glazed metal enclosure on the last window.
    front=-.71
    for ux,vy,ex,ey in [(757,257,820,294),(790,255,854,296)]:
        b.tube([facade_point(ux,vy,-.04),facade_point(ex,ey,front)],.027,RAIL,8 if lod else 12,'West window | high diagonal bracket')
    for u in [760,772,828,850]:
        path_on(b,[(u,309),(u+7,366)],front,.021,RAIL,'West window | enclosure standards',lod)
    for v in [307,312,365,368]:
        path_on(b,[(756,v),(851,v+.5)],front,.022,RAIL,'West window | enclosure rails',lod)
    for u in [761,849]:
        b.tube([facade_point(u,309,front),facade_point(u-3,312,-.04)],.019,RAIL,9,'West window | returning enclosure rails')
