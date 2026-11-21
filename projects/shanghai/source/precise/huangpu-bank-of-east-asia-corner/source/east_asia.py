"""Four-column portico, five bands of corner windows, two setbacks and the photographed crown."""
import json
from math import asin, cos, sin
from pathlib import Path
from shapely.affinity import translate
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade
from aggregate import texture_uv
from portal import PORTAL_MATERIALS, add_portal, bank_glyph, portal_opening

SOURCE=Path(__file__).resolve().parent
REG=json.loads((SOURCE/'frontage-registration.json').read_bytes())
EDGES=REG['visible_edges_local_m']
RADIUS=REG['arc_radius_m']
HALF=REG['arc_half_chord_m']
STONE='grey aggregate stone'
EDGE='smooth grey stringcourse'
DARK='blackened window metal'
GLASS='muted street glass'
LIGHT='upper storey glass'
BRONZE='raised bronze characters'
ZINC='weathered zinc'
PALETTE={
    STONE:{'color':[1,1,1],'roughness':.9,'texture':str(SOURCE/'aggregate.png')},
    EDGE:{'color':[.59,.565,.53],'roughness':.77},
    DARK:{'color':[.18,.17,.165],'roughness':.48,'metallic':.30},
    GLASS:{'color':[.24,.31,.35],'roughness':.30,'metallic':.21},
    LIGHT:{'color':[.32,.39,.42],'roughness':.34,'metallic':.16},
    BRONZE:{'color':[.29,.17,.13],'roughness':.55,'metallic':.47},
    ZINC:{'color':[.34,.32,.30],'roughness':.62,'metallic':.22},
    **PORTAL_MATERIALS,
}
# Window-storey heights and offsets were estimated using the entrance image and the 2013 street photo.
BANDS=[(7.05,10.06),(10.98,13.64),(14.69,17.36),(18.35,20.97),(21.94,24.47)]
def point_on_curve(angle,retreat=0):
    r=RADIUS-retreat
    return [r*sin(angle),RADIUS-r*cos(angle)]
def angles(half,retreat,count):
    limit=asin(half/(RADIUS-retreat))
    return [-limit+2*limit*i/count for i in range(count+1)]
def arc_parts(half,retreat,count):
    return [point_on_curve(a,retreat) for a in angles(half,retreat,count)]
def strip(builder,path,projection,back,lo,hi,material,name):
    line=LineString(path)
    front=line.offset_curve(-projection,join_style='mitre')
    rear=line.offset_curve(back,join_style='mitre')
    p=Polygon([*front.coords,*reversed(rear.coords)])
    assert p.is_valid and p.area>.0001
    builder.plan_prism(p,lo,hi,material,name)
def glass(face,hole,label,glass=GLASS,split=True,grille=False):
    lo,b,hi,t=hole.bounds
    face.prism(hole.buffer(.009,join_style=2),-.328,-.308,glass,label+' pane')
    inner=hole.buffer(-.065,join_style=2)
    cross=b+(t-b)*.67
    bars=[box(lo,cross-.029,hi,cross+.029)]
    if split:
        mid=(lo+hi)/2
        bars.append(box(mid-.028,b,mid+.028,cross))
    if grille:
        bars.extend(box(lo+(hi-lo)*i/5-.015,b,lo+(hi-lo)*i/5+.015,cross)for i in range(1,5))
        bars.append(box(lo,b+(cross-b)*.53,hi,b+(cross-b)*.53+.038))
    face.prism(hole.buffer(-.013,join_style=2).difference(inner.difference(unary_union(bars))),-.244,-.15,DARK,label+' sash')
def clipped(center,bottom,width,top,cut):
    l,r=center-width/2,center+width/2
    return Polygon([(l,bottom),(r,bottom),(r,top-cut),(r-cut*.65,top),(l+cut*.65,top),(l,top-cut)])
def ground(builder,lod):
    half=3.12;flat_y=.26
    front=Facade(builder,[-half,flat_y],[half,flat_y],'entrance')
    l,r,b,t=portal_opening(0,width=6.15,height=5.55)
    front.wall(0,6.22,[box(l,b,r,t)],.54,STONE)
    add_portal(front,0,lod,width=6.15,height=5.55)
    for sign,edge in ((-1,EDGES[1]),(1,EDGES[2])):
        ends=([sign*half,flat_y],edge)
        if sign<0:ends=ends[::-1]
        face=Facade(builder,*ends,'portico shoulder')
        face.wall(0,6.22,[],.49,STONE)
        for i in range(1,7):
            u=face.length*(i/7-.5)
            face.box(u,5.26,.042,1.34,.046,.016,EDGE,'shallow frieze fluting')
        for u in (-face.length*.34,face.length*.34):
            face.box(u,2.39,.062,4.40,.065,.019,EDGE,'dressed shoulder edge')
        face.box(0,.175,face.length,.35,.16,.045,STONE,'low shoulder plinth')
    # A shallow fluted panel is visible over the stone pediment.
    for i in range(-19,20):
        u=i*.151
        crest=5.55-max(0,abs(u)-.19)*.31
        bottom=crest+.028
        height=6.11-bottom
        front.box(u,bottom+height/2,.048,height,.055,.02,EDGE,'fluted overdoor')
    for side,(a,b) in enumerate(((EDGES[0],EDGES[1]),(EDGES[2],EDGES[3]))):
        f=Facade(builder,a,b,'Sichuan street' if side==0 else 'Jiujiang street')
        sign=1 if side==0 else -1
        narrow=sign*1.18;wide=-sign*.86
        holes=[clipped(narrow,.72,1.00,5.65,.33),
               box(wide-.85,.72,wide+.85,5.65)]
        f.wall(0,6.22,holes,.48,STONE)
        for j,shape in enumerate(holes):
            glass(f,shape,'street front',split=j==1,grille=True)
            lo,z,hi,top=shape.bounds
            f.box((lo+hi)/2,3.11,hi-lo,.18,.33,-.105,STONE,'ground floor stone transom')
            f.box((lo+hi)/2,.65,hi-lo+.10,.13,.30,.043,EDGE,'low window sill')
        for u in [-2.12,.12,2.12]:
            f.box(u,3.12,.14,5.68,.12,.035,EDGE,'vertical dressed strip')
def upper_centre(builder,lod):
    # Each curved ribbon contains four glazed panels separated by narrow stone mullions.
    ang=angles(HALF,0,4)
    for i,(a,b) in enumerate(zip(ang,ang[1:])):
        face=Facade(builder,point_on_curve(a),point_on_curve(b),'curved office front')
        hs=[]
        for j,(lo,hi)in enumerate(BANDS):
            margin=.125 if i in (1,2) else .145
            hs.append(box(-face.length/2+margin,lo,face.length/2-margin,hi))
        face.wall(6.22,24.95,hs,.47,STONE)
        for j,hole in enumerate(hs):
            glass(face,hole,'four-part ribbon',GLASS if j%2==0 else LIGHT)
            face.box(0,hole.bounds[1]-.053,face.length-.02,.102,.18,.028,EDGE,'curved window sill')
def wing(builder,side):
    a,b=(EDGES[0],EDGES[1])if side==0 else(EDGES[2],EDGES[3])
    face=Facade(builder,a,b,'Sichuan return' if side==0 else 'Jiujiang return')
    sign=1 if side==0 else -1
    holes=[]
    for lo,hi in BANDS:
        holes.extend([box(sign*1.29-.49,lo,sign*1.29+.49,hi),
                      box(-sign*.88-.92,lo,-sign*.88+.92,hi)])
    face.wall(6.22,24.95,holes,.49,STONE)
    for i,hole in enumerate(holes):
        glass(face,hole,'single flank light' if i%2==0 else 'paired street light',split=i%2==1)
        l,b,r,_=hole.bounds
        face.box((l+r)/2,b-.048,r-l+.16,.09,.21,.029,EDGE,'flank sill')
    # Continuous vertical piers appear between the narrow flank light and the street wing.
    for u in (sign*2.17,sign*.43):
        face.box(u,15.70,.16,17.42,.14,.044,EDGE,'vertical stone fillet')
def setback(builder,z0,top,half,retreat,name,lod):
    pts=arc_parts(half,retreat,4)
    for a,b in zip(pts,pts[1:]):
        face=Facade(builder,a,b,name)
        h=box(-face.length/2+.115,z0+.34,face.length/2-.115,top-.31)
        face.wall(z0,top,[h],.36,STONE)
        glass(face,h,name,GLASS,split=False)
    strip(builder,arc_parts(half,retreat,8 if lod else 16),.17,.58,top-.16,top+.02,EDGE,name+' cap')
    return pts
def crown(builder,lod):
    # The frontal stone top can be read in the 2013 photo. Depths are bounded estimates.
    for half,y,b,t,name in [(1.60,1.67,29.73,30.18,'crown plinth'),(1.09,1.86,30.18,30.58,'crown shoulders')]:
        builder.box([0,y+.34,(b+t)/2],[half*2,.68,t-b],STONE,label=name)
    face=Facade(builder,[-.79,1.95],[.79,1.95],'crown')
    holes=[box(x-.16,30.84,x+.16,31.60)for x in (-.39,0,.39)]
    face.wall(30.58,31.98,holes,.59,STONE)
    for h in holes:
        face.prism(h.buffer(.012),-.24,-.22,DARK,'dark lantern slit')
    face.box(0,31.99,1.65,.14,.72,-.24,EDGE,'lantern cap')
    # Over the flat capital rises a low stepped, hipped roof and a short dark finial.
    for z,w,d,h in [(32.07,1.34,.65,.17),(32.24,1.02,.54,.17),(32.41,.72,.44,.15)]:
        builder.box([0,2.24,z+h/2],[w,d,h],STONE,label='stepped crown roof')
    builder.lathe([0,2.24],[(32.56,.33),(32.82,.18),(32.92,.12),(33.15,.055),(33.28,.038)],ZINC,8 if lod else 16,'small crown finial')
def add_building(builder,lod):
    ground(builder,lod);upper_centre(builder,lod)
    wing(builder,0);wing(builder,1)
    full=[EDGES[0],*arc_parts(HALF,0,12 if lod else 24),EDGES[3]]
    for lo,hi,out,back,mat,label in [
            (5.62,5.77,.23,.42,EDGE,'sign bottom lip'),(5.77,6.67,.17,.46,STONE,'continuous sign fascia'),
            (6.67,6.82,.29,.44,EDGE,'sign upper lip'),(6.82,6.94,.20,.46,STONE,'fascia coping'),
            (24.71,25.02,.31,.62,EDGE,'top window cornice'),(25.02,25.22,.52,.69,STONE,'projecting top cornice'),
            (25.22,25.36,.48,1.38,EDGE,'first setback ledge')]:
        strip(builder,full,out,back,lo,hi,mat,label)
    for i,char in enumerate('東亞銀行'):
        theta=asin(((i-1.5)*1.05)/RADIUS)
        f=Facade(builder,point_on_curve(theta-.02),point_on_curve(theta+.02),'curved fascia')
        shape=translate(bank_glyph(char,.70,.73,lod),yoff=6.23)
        f.prism(shape,.174,.223,BRONZE,'bank name '+char)
    setback(builder,25.30,27.08,3.83,.62,'first setback',lod)
    strip(builder,arc_parts(3.83,.62,10 if lod else 18),.24,1.20,27.07,27.28,EDGE,'second setback ledge')
    setback(builder,27.23,29.77,2.82,1.31,'second setback',lod)
    strip(builder,arc_parts(2.82,1.31,10),.07,1.13,29.74,29.86,EDGE,'crown base roof')
    # The straight metal rails stop at the corner drum. Keep the rails inside the evidenced street bays.
    for a,b in ((EDGES[0],EDGES[1]),(EDGES[2],EDGES[3])):
        f=Facade(builder,a,b,'street roof rail')
        for z in (25.72,26.18,26.68):
            f.box(0,z,f.length,.058,.067,-.36,ZINC,'horizontal rooftop rail')
        for u in (-.43*f.length,0,.43*f.length):
            f.box(u,26.04,.092,1.47,.105,-.36,EDGE,'roof rail stanchion')
    crown(builder,lod)
    for part in builder.parts:
        if part['material']==STONE:
            part['texcoords']=[(u,1-v)for u,v in (texture_uv(*v)for v in part['vertices'])]
