"""West-facing wall of the No. 1 villa, as visible in Gao photographs 02 and 04."""
from pathlib import Path
import json
import math
import numpy as np
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade

STONE = 'Fudefang | pale pink dressed masonry'
CARVED = 'Fudefang | warm carved stone edges'
RECESS = 'Fudefang | recessed carving field'
SLAT = 'Fudefang | dark muted aubergine blind slats'
CORD = 'Fudefang | blind lift cords'
PIPE = 'Fudefang | weathered iron downpipe'
VOID = 'Fudefang | dark window recess'
PALETTE = {
    STONE: dict(color=[.62,.526,.438],roughness=.95),
    CARVED: dict(color=[.727,.620,.520],roughness=.91),
    RECESS: dict(color=[.549,.460,.398],roughness=.94),
    SLAT: dict(color=[.135,.075,.084],metallic=.10,roughness=.72),
    CORD: dict(color=[.119,.088,.082],metallic=.02,roughness=.85),
    PIPE: dict(color=[.19,.14,.123],metallic=.53,roughness=.66),
    VOID: dict(color=[.039,.029,.033],metallic=0,roughness=.92)}
WEST_X = -6.45
WEST_START = .7613
WEST_BREAK = 7.93
WEST_END = 17.9
HIGH_SOFFIT = 11.30
LOW_SOFFIT = 10.52
DATA = Path(__file__).absolute().parents[1]/'measurements/west-wall-photo-controls.json'


def motif(points, width):
    return LineString(points).buffer(width / 2, cap_style=2, join_style=2)


def strip_ring(x,z,w,h,t):
    return box(x-w/2,z,x+w/2,z+h).difference(box(x-w/2+t,z+t,x+w/2-t,z+h-t))


def cubic(a,b,c,d,n=15):
    t=np.linspace(0.,1.,n)[:,None]
    a,b,c,d=map(np.asarray,[a,b,c,d])
    return (1-t)**3*a+3*t*(1-t)**2*b+3*t*t*(1-t)*c+t**3*d


def ornament(face, x, width, z, height, is_panel, lod):
    """Diamond-and-tassel top, inset botanical sprig and two narrow bottom strips."""
    w=width; h=height
    def mappts(points):
        return [(x+u*w,z+v*h) for u,v in points]
    def path(points, thick):return motif(mappts(points),thick)
    def raised(shape,low,high,mat,label):
        if not shape.is_empty:face.prism(shape,low,high,mat,label)
    # Uppermost apron has three diagonal diamonds beneath a row of square teeth.
    ends=[Polygon(mappts([(-.49,.99),(-.40,.99),(-.42,.83),(-.49,.83)])),
          Polygon(mappts([(.40,.99),(.49,.99),(.49,.83),(.42,.83)]))]
    diamonds=[]
    for cx in [-.24,0,.24]:
        diamonds.append(path([(cx-.144,.88),(cx,.772),(cx+.144,.88),(cx,.919),(cx-.144,.88)],.023))
    raised(unary_union(ends+diamonds),.008,.045,CARVED,'folded diamond relief under projecting sill')
    for j in range(9):
        xx=x+(j-4)*w*.084
        face.box(xx,z+.963*h,w*.046,.052,.045,.043,CARVED,'small hanging stone tooth')
    if not is_panel:return
    # These two carved rectangular fields are visible only on the taller portion.
    bottom=z+.19*h; ph=.45*h; fieldw=.71*w
    raised(strip_ring(x,bottom,fieldw,ph,.026),.006,.041,CARVED,'rectangular framed sprig field')
    face.box(x,bottom+ph/2,fieldw-.059,ph-.059,.017,.003,RECESS,'recessed field behind stone sprig')
    def sprig(points,thick):return path([(u*.63,.21+v*.40)for u,v in points],thick)
    strokes=[sprig(cubic([-.48,.23],[-.29,.48],[.08,.41],[.45,.12]),.041),
             sprig(cubic([-.10,.81],[-.04,.50],[.31,.43],[.45,.12]),.035),
             sprig(cubic([-.48,.41],[-.38,.53],[-.25,.50],[-.17,.40]),.027),
             sprig(cubic([-.35,.37],[-.25,.62],[-.16,.58],[-.05,.43]),.028),
             sprig(cubic([.03,.43],[.11,.61],[.18,.53],[.24,.34]),.028),
             sprig(cubic([-.15,.78],[-.22,.88],[-.31,.82],[-.31,.76]),.025)]
    raised(unary_union(strokes),.019,.059,CARVED,'raised branching leaf silhouette')
    if not lod:
        for a in (-1,1):
            leaf=Polygon(mappts([(a*.294,.535),(a*.22,.467),(a*.276,.55),(a*.313,.575)]))
            raised(leaf,.019,.049,CARVED,'detached corner leaf')
    for base in [.027,.094]:
        horizontal=path([(-.45,base),(-.18,base+.015),(0,base-.006),(.18,base+.015),(.45,base)],.024)
        raised(horizontal,.011,.052,CARVED,'undulating pair of narrow head strips')


def blinds(face, center, left, right, low, high, pitch, lod):
    """Angled horizontal blades span one recess, with three visible vertical lift cords."""
    frame_width=right-left; zcenter=.5*(low+high)
    face.box(center,zcenter,frame_width-.008,high-low-.008,.028,-.127,VOID,'back of dark blind recess')
    count=max(9,round((high-low)/pitch))
    if lod:count=max(8,(count+1)//2)
    step=(high-low)/count
    x0=center-frame_width/2+.011;x1=center+frame_width/2-.011
    vertices=[];faces=[]
    # Tilted slats overlap in elevation whilst remaining separate closed elements.
    for j in range(count):
        z=low+(j+.5)*step
        for x in (x0,x1):
            for zz,dd in [(z+step*.46,-.099),(z-step*.48,-.062),
                          (z-step*.55,-.066),(z+step*.39,-.103)]:
                vertices.append(face.point(x,zz,dd))
        k=8*j
        facets=[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
        # End cap winding is checked when the local mesh is emitted.
        faces.extend(tuple(k+i for i in f) for f in facets)
    vs=np.asarray(vertices)
    sig=sum(np.dot(vs[f[0]],np.cross(vs[f[1]],vs[f[2]]))+np.dot(vs[f[0]],np.cross(vs[f[2]],vs[f[3]])) for f in faces)
    face.builder.add(vs,[f if sig>0 else tuple(reversed(f)) for f in faces],SLAT,'west blinds / sloping slats in a recessed side window')
    for fraction in [-.34,0,.34]:
        face.box(center+fraction*frame_width,zcenter,.010,high-low-.024,.011,-.052,CORD,'vertical blind lift cord')


def downpipe(b,y,high,low,lod):
    """The rectangular hoppers, shaft and wide fixing collars are resolved in photo 04."""
    x=WEST_X-.060
    points=[(x,y,low),(x,y,high-.09),(x+.015,y,high)]
    b.tube(points,.070,PIPE,8 if lod else 16,'west / vertical iron downpipe')
    for z in np.arange(high-.11,low,-1.42):
        b.tube([(x,y,z-.029),(x,y,z+.029)],.095,PIPE,8 if lod else 16,'west / pipe collar')
        b.box([x+.055,y,z],[.13,.23,.025],PIPE,label='west / fixing bracket')
    profile=[(high+dz,r) for dz,r in [(-.08,.071),(-.025,.078),(.038,.144),(.18,.165),(.226,.153),(.246,.125)]]
    b.lathe([x,y],profile,PIPE,8 if lod else 12,'west / hopper under eaves')


def add_west(b,lod=False):
    rows=json.loads(DATA.read_bytes())['windows']
    face=Facade(b,(WEST_X,WEST_END),(WEST_X,WEST_START),'west long elevation')
    middle=(WEST_END+WEST_START)/2
    to_u=lambda y:middle-y
    openings={}
    for name,s in rows.items():
        ylo,yhi=s['outer_wall_y_interval_m'];lo,hi=s['outer_wall_z_interval_m']
        # Left jamb return is distinctly visible from the garden, most strongly in the tall nearest window.
        yhi+=.16 if name=='rear-north-upper' else .11 if name.startswith('rear') else .15
        openings[name]=(to_u(yhi),to_u(ylo),lo,hi)
    for ya,yb,soffit,tag in [(WEST_START,WEST_BREAK,HIGH_SOFFIT,'tall'),(WEST_BREAK,WEST_END,LOW_SOFFIT,'lower')]:
        a,c=to_u(yb),to_u(ya);cornice=box(a,0,c,soffit)
        cuts=[]
        for nm,(l,r,lo,hi) in openings.items():
            if a<.5*(l+r)<c:cuts.append(box(l,lo,r,hi))
        face.prism(cornice.difference(unary_union(cuts)),-.28,0,STONE,tag+' west wall with measured openings')
        # On the far tower end the roof outline continues, but the photograph does not resolve each last corbel.
        face.box((a+c)/2,soffit-.15,c-a,.30,.072,.026,CARVED,tag+' cornice frieze')
        face.box((a+c)/2,soffit+.025,c-a,.11,.41,.145,STONE,tag+' soffit course')
        face.box((a+c)/2,soffit+.111,c-a,.081,.56,.212,CARVED,tag+' stepped leading edge')
        face.box((a+c)/2,soffit+.168,c-a,.052,.59,.224,STONE,tag+' flat upper rim')
        stop=min(yb,13.4);spacing=.264 if tag=='tall' else .176
        for yy in np.arange(ya+.12,stop-.05,spacing):
            face.box(to_u(yy),soffit+.0008,.073 if tag=='tall' else .055,.112,.19,.116,RECESS,tag+' tooth below projection')
        if tag=='tall':
            xx=np.arange(a+.035,c-.022,.025 if not lod else .061)
            yy=soffit-.177+.036*np.sin((xx-a)*2*np.pi/.23)
            line=motif(np.column_stack((xx,yy)),.021)
            face.prism(line,.056,.073,CARVED,'continuous low wave on high west frieze')
    for nm,(l,r,lo,hi) in openings.items():
        center=(l+r)/2;wid=r-l
        face.prism(strip_ring(center,lo-.046,wid+.13,hi-lo+.092,.053),-.012,.035,CARVED,'stone channel around '+nm)
        face.box(center,lo-.065,wid+.20,.074,.15,.054,CARVED,'projecting sill '+nm)
        face.box(center,lo-.111,wid+.145,.042,.116,.041,STONE,'sill bed '+nm)
        pitch=rows[nm]['median_horizontal_step_m'] or .038
        blinds(face,center,l,r,lo,hi,pitch,lod)
        upper=nm.endswith('upper')
        if upper and not nm.startswith('rear'):
            mid_high=openings[nm.replace('upper','middle')][3]
            ornament(face,center,wid+.11,mid_high+.036,lo-.14-mid_high,True,lod)
        else:
            ornament(face,center,wid+.08,lo-.41,.265,False,lod)
    downpipe(b,.633,HIGH_SOFFIT-.61,3.6,lod)
    downpipe(b,7.775,LOW_SOFFIT+.033,4.67,lod)
