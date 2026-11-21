"""Photo-based fragment of the entrance to House One in Dingxiang Garden.

Local X runs from the curved wing to the canted bay when viewed from the court.
Only the short returns visible in the two studied views are included.
"""
import math

from shapely.geometry import LineString, Polygon, box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

from photo_architecture import Facade, opening

CREAM = 'warm roughcast'
STONE = 'grey moulded stone'
DARK = 'dark corbel stone'
TIMBER = 'oxblood timber'
EDGE = 'weathered bargeboard'
GLASS = 'lead grey glass'
SHADE = 'inner door glazing'
TILE = 'earthen roof tiles'
LIP = 'clay tile laps'
GOLD = 'brass address plate'
BLACK = 'enamel numeral'
PAVING = 'grey stone tread'
PALETTE = {key:dict(color=color, roughness=roughness, metallic=metallic)
           for key,color,roughness,metallic in [
               (CREAM,[.78,.72,.565],.94,0), (STONE,[.315,.304,.262],.84,0),
               (DARK,[.18,.181,.168],.85,0), (TIMBER,[.26,.077,.049],.64,0),
               (EDGE,[.183,.059,.039],.74,0), (GLASS,[.155,.229,.265],.27,.18),
               (SHADE,[.082,.099,.102],.39,.07), (TILE,[.405,.161,.096],.86,0),
               (LIP,[.493,.215,.139],.86,0), (GOLD,[.59,.426,.136],.54,.48),
               (BLACK,[.068,.059,.041],.61,.09), (PAVING,[.423,.414,.375],.88,0)]}


def casement(face, shape, columns=2, lights=2, back=-.235, label='casement', glass=GLASS, transom=None):
    """Cut the wood grid from a single frame; glazing sits behind its jambs."""
    left,bottom,right,top=shape.bounds
    inner=shape.buffer(-.075,join_style=2)
    bars=[]
    for i in range(1,columns):
        x=left+(right-left)*i/columns
        bars.append(box(x-.031,bottom,x+.031,top))
    for i in range(1,lights):
        z=bottom+(top-bottom)*(transom if transom is not None else i/lights)
        bars.append(box(left,z-.028,right,z+.028))
    face.prism(shape.difference(inner.difference(unary_union(bars))),back,back+.080,TIMBER,label+' joinery')
    face.prism(shape.buffer(.008,join_style=2),back-.05,back-.025,glass,label+' panes')


def portal(b,lod):
    center=1.14
    half=1.56
    depth=2.43
    surfaces=[Facade(b,(center-half,-depth),(center+half,-depth),'entrance arch'),
              Facade(b,(center-half,0),(center-half,-depth),'left porch arch'),
              Facade(b,(center+half,-depth),(center+half,0),'right porch arch')]
    for index,face in enumerate(surfaces):
        width=face.length
        radius=width*.305
        arch=opening(0,-.05,2*radius,2.4+radius+.05,radius,12 if lod else 36)
        vents=[opening(u,3.46,.28,.38,.14,8 if lod else 18) for u in (-.47,0,.47)]
        # At the two front corners the return abuts the back skin of the
        # street face. A second cap flush with the front creates a dark seam.
        left=-width/2+(.235 if index==2 else 0)
        right=width/2-(.235 if index==1 else 0)
        outline=box(left,.31,right,4.28)
        face.wall(.31,4.28,[arch,*vents],thickness=.235,material=CREAM,outline=outline)
        for z,height,projection in ((3.99,.068,.075),(4.07,.115,.125),(4.20,.092,.18)):
            face.beam(z,height,projection,STONE,label='stepped cornice')
        for sign in (-1,1):
            x=sign*(radius+.074)
            for z,height,w,d in ((2.075,.15,.18,.16),(2.205,.12,.23,.21),
                                 (2.325,.12,.31,.265),(2.43,.09,.40,.32)):
                face.box(x,z,w,height,d,.045,DARK,'four ledges of spring corbel')
            face.box(sign*(width/2-.14),.61,.26,.55,.27,-.075,STONE,'pier plinth')
    roof=box(center-half,-depth,center+half,0)
    b.plan_prism(roof,.285,.35,PAVING,'porch/landing')
    b.plan_prism(roof,3.93,4.00,CREAM,'porch/soffit')
    b.plan_prism(roof,4.22,4.29,STONE,'porch/top coping')
    for i in range(3):
        b.box((center,-depth-.67+.22*i,(i+1)*.052),(2.64,.23,(i+1)*.104),PAVING,label='porch/three stone treads')
    front=surfaces[0]
    front.box(1.23,3.01,.235,.355,.031,.024,GOLD,'number plate')
    one=Polygon([(1.172,3.075),(1.226,3.136),(1.262,3.136),(1.262,2.905),
                 (1.291,2.905),(1.291,2.88),(1.183,2.88),(1.183,2.905),
                 (1.217,2.905),(1.217,3.075),(1.188,3.050)])
    front.prism(one,.041,.048,BLACK,'numeral one')


def gable(b,lod):
    left,right=-3.93,3.93
    eaves,peak=8.43,11.31
    front=Facade(b,(left,0),(right,0),'main gable')
    profile=Polygon([(left,.25),(right,.25),(right,eaves),(0,peak),(left,eaves)])
    door=opening(1.14,.349,1.40,2.49,.12,12)
    small=[opening(x,4.72,.72,1.72,.075,12) for x in (-2.15,-1.11)]
    narrow=box(1.92,4.48,2.49,6.72)
    oriel=box(-2.51,7.74,-.56,9.14)
    front.wall(0,peak,[door,*small,narrow,oriel],thickness=.27,material=CREAM,outline=profile)
    for window in [*small,narrow]:
        casement(front,window,1,2)
    casement(front,door,2,3,-.23,'entrance door',glass=SHADE)
    panel=box(.457,.36,1.823,1.09)
    front.prism(panel,-.145,-.126,TIMBER,'lower door panels')
    for x in (.77,1.51):
        inset=box(x-.23,.50,x+.23,.96)
        front.prism(inset.difference(inset.buffer(-.041,join_style=2)),-.119,-.095,EDGE,'door panel rim')
    front.prism(box(left,3.98,right,4.12),.005,.107,STONE,'lower string course')
    field=profile.intersection(box(left,6.68,right,peak))
    bars=[box(left,6.68,right,6.815),box(left,8.12,right,8.238)]
    for x in (-3.73,-3.04,-2.46,-1.72,-.97,-.31,.43,1.16,1.94,2.66,3.42,3.82):
        bars.append(box(x-.054,6.68,x+.054,peak))
    frame=unary_union(bars).intersection(field).difference(oriel)
    front.prism(frame,.002,.112,TIMBER,'exposed wall studs and rails')
    for a,v in [((left,eaves),(0,peak)),((0,peak),(right,eaves))]:
        line=LineString([a,v])
        front.prism(line.buffer(.115,cap_style=2),.04,.28,EDGE,'sloping bargeboards')
    # The four-leaf projecting timber window has glazed returns and visible corbels.
    x0,x1=oriel.bounds[0]-.04,oriel.bounds[2]+.04
    short=.44
    for face in [Facade(b,(x0,-short),(x1,-short),'oriel front'),
                 Facade(b,(x0,0),(x0,-short),'oriel west return'),
                 Facade(b,(x1,-short),(x1,0),'oriel east return')]:
        half=face.length/2
        casement(face,box(-half,7.72,half,9.17),4 if half>.55 else 1,2,0,'projecting sash',transom=.736)
        for z,height in ((7.65,.16),(7.80,.084),(9.23,.15),(9.32,.075)):
            face.box(0,z,face.length+.11,height,.15,.025,TIMBER,'projecting sill and head')
    b.box(((x0+x1)/2,-short/2,7.64),(x1-x0+.13,short+.17,.14),EDGE,label='oriel/soffit')
    b.box(((x0+x1)/2,-short/2,9.27),(x1-x0+.16,short+.16,.12),TIMBER,label='oriel/lintel cover')
    for x in (x0+.08,x0+.49,x1-.49,x1-.08):
        side=Facade(b,(x,-.49),(x,.01),'oriel carved timber brackets')
        side.prism(Polygon([(-.23,7.57),(.22,7.57),(.22,7.20),(.10,7.27),(.035,7.42),(-.17,7.47)]),
                   -.049,.049,EDGE,'stepped curved bracket')
    # Short roof return only. The photographed crest continues behind this fragment.
    for side in (-1,1):
        x0,x1=sorted([0,side*4.23])
        def mapper(x,y,z):
            return (x,y,peak+.17-side*x*.732+z)
        b.prism(box(x0,-.32,x1,3.84),-.15,0,mapper,TILE,'main roof/slopes')
        spacing=.31 if lod else .243
        rows=math.ceil(4.23/spacing)
        for i in range(1,rows):
            x=side*i*spacing
            b.tube([mapper(x,-.31,.01),mapper(x,3.83,.01)],.022,LIP,5 if lod else 8,'main roof/horizontal tile laps')
        if not lod:
            for i in range(rows):
                xa,xb=sorted([side*(i*spacing+.020),side*min(4.21,(i+1)*spacing-.018)])
                if xb-xa <.04: continue
                for j in range(16):
                    y=-.3+(j+.5*(i%2))*.281
                    if y>=3.82:continue
                    b.prism(box(xa,y,xb,y+.012),.002,.013,mapper,EDGE,'main roof/staggered tile ends')
    b.tube([(0,-.34,peak+.20),(0,3.87,peak+.20)],.070,TILE,8 if lod else 14,'roof/ridge tile')
    for x in (left,right):
        side=Facade(b,(x,3.8),(x,.27),'gable left return') if x<0 else Facade(b,(x,.27),(x,3.8),'gable right return')
        side.wall(.28,eaves,thickness=.22,material=CREAM)
    for x,y,base,top,width in ((-2.11,2.44,9.74,12.45,.93),(2.95,3.30,8.92,11.15,.68)):
        b.box((x,y,(top+base)/2),(width,.60,top-base),CREAM,label='stacks/rendered shafts')
        for z,h,w in ((top-.13,.09,.08),(top,.13,.15)):
            b.box((x,y,z),(width+w,.60+w,h),STONE,label='stacks/stone caps')
        for edge in (-1,1):
            b.box((x+edge*(width/2-.10),y-.325,top-(top-base)*.32),
                  (.08,.065,(top-base)*.52),CREAM,label='stacks/vertical plaster ribs')


def wings(b,lod):
    # Left cylindrical return, tangent glazed bays follow the arc itself.
    center=(-4.38,1.56)
    radius=1.40
    a0,a1=math.radians(177),math.radians(290)
    count=3
    edges=[a0+(a1-a0)*i/count for i in range(count+1)]
    def xy(angle,r=radius):
        return (center[0]+r*math.cos(angle),center[1]+r*math.sin(angle))
    for i,(a,z) in enumerate(zip(edges,edges[1:])):
        angles=[a+(z-a)*j/4 for j in range(5)]
        # The middle of each curved sector contains a straight recessed timber sash.
        breaks=[angles[0],a+.12*(z-a),a+.88*(z-a),angles[-1]]
        for j,(u,v) in enumerate(zip(breaks,breaks[1:])):
            face=Facade(b,xy(u),xy(v),'rounded wing')
            cuts=[]
            if j==1 and i in (0,2):
                width=face.length*.85
                cuts=[opening(0,h,width,1.82,.11,10) for h in (1.02,4.88)]
            face.wall(.26,7.38,cuts,thickness=.21,material=CREAM)
            for window in cuts:casement(face,window,1,2)
    ring=[xy(a0+(a1-a0)*i/(16 if lod else 34)) for i in range((16 if lod else 34)+1)]
    inner=[xy(a0+(a1-a0)*i/(16 if lod else 34),radius-.20) for i in reversed(range((16 if lod else 34)+1))]
    arc=Polygon(ring+inner)
    for z,h,w in ((.35,.19,.045),(3.94,.16,.09),(7.30,.14,.10),(7.52,.12,.115)):
        b.plan_prism(arc.buffer(w,join_style=2),z,z+h,STONE,'round wing/curved stone bands')
    b.plan_prism(Polygon([center,*ring]).buffer(.04),7.4,7.52,CREAM,'round wing/parapet cover')
    pts=[(3.93,.68),(4.81,-.16),(6.11,.02),(6.86,1.10),(6.68,2.56)]
    for i,(a,z) in enumerate(zip(pts,pts[1:])):
        face=Facade(b,a,z,'canted bay')
        holes=[opening(0,h,min(.70,face.length*.63),1.59,.11,10) for h in (1.02,4.87)]
        face.wall(.26,7.64,holes,thickness=.22,material=CREAM)
        for hole in holes:
            casement(face,hole,2,2)
            u,h,v,_=hole.bounds
            face.box(0,h-.075,v-u+.17,.11,.29,.025,STONE,'cut stone sill')
        # Two nested rectangular panels appear below the upper sills in the
        # 2013 street-facing bay. Retain the recessed field behind each rim.
        if i < 3:
            half=min(.47,face.length/2-.07)
            panel=box(-half,4.19,half,4.71)
            face.prism(panel.difference(panel.buffer(-.063,join_style=2)),.008,.067,
                       CREAM,'upper window apron rim')
            face.prism(panel.buffer(-.082,join_style=2).difference(panel.buffer(-.111,join_style=2)),
                       .008,.046,STONE,'upper apron inner moulding')
        for h in (.45,4.02,6.85,7.58):
            timber=h>6
            face.beam(h,.12,.095,TIMBER if timber else STONE,label='horizontal half timber' if timber else 'string')
        face.box(-face.length/2+.074,7.19,.102,.66,.115,.03,TIMBER,'short upright')
    footprint=Polygon([*pts,(4.08,2.79)])
    eave=orient(footprint.buffer(.19,join_style=2),sign=1)
    apex=(5.06,1.38,8.57)
    for a,z in zip(eave.exterior.coords,list(eave.exterior.coords)[1:]):
        b.add([(*a,7.72),(*z,7.72),apex,(*a,7.63),(*z,7.63),(apex[0],apex[1],apex[2]-.09)],
              [(0,1,2),(5,4,3),(0,3,4,1),(1,4,5,2),(2,5,3,0)],TILE,'bay/hipped roof')
        steps=3 if lod else 7
        for k in range(1,steps):
            t=k/steps
            tips=[(x+(apex[0]-x)*t,y+(apex[1]-y)*t,7.73+(apex[2]-7.72)*t)
                  for x,y in (a,z)]
            b.tube(tips,.014,LIP,4 if lod else 7,'bay/hip tile courses')


def add_house(builder,lod=False):
    gable(builder,lod)
    wings(builder,lod)
    portal(builder,lod)
