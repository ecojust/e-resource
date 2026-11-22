"""Central south loggia of the garden residence, 2 Lane 1394, West Beijing Road."""
from pathlib import Path
from math import cos, sin, pi
from shapely.geometry import box
from shapely.ops import unary_union
from photo_architecture import Facade, opening
from sign_lettering import add_facade_lettering

PALETTE = {
    'ivory render': {'color': [.85,.85,.75], 'roughness': .93},
    'pale stucco trim': {'color': [.89,.88,.76], 'roughness': .87},
    'stone step': {'color': [.61,.58,.51], 'roughness': .86},
    'porch paving': {'color': [.71,.66,.58], 'roughness': .89},
    'timber sash': {'color': [.13,.15,.13], 'roughness': .65},
    'shaded glass': {'color': [.18,.23,.24], 'roughness': .27},
    'inner threshold shadow': {'color': [.075,.078,.068], 'roughness': .85},
    'black museum letters': {'color': [.11,.12,.11], 'roughness': .60},
    'dark bronze fitting': {'color': [.37,.31,.21], 'roughness': .54},
    'terrace surface': {'color': [.56,.55,.50], 'roughness': .87},
}
IVORY='ivory render'
TRIM='pale stucco trim'
TIMBER='timber sash'
GLASS='shaded glass'
CENTERS=(-2.16, 0., 2.16)
HALF=3.44
REAR=1.56
LANDING=.54
SPRING=2.89
DECK=5.10

def floor(b,x0,x1,y0,y1,z0,z1,mat,label):
    b.plan_prism(box(x0,y0,x1,y1),z0,z1,mat,label)

def balusters(b,a,c,z0,z1,count,lod,label):
    """The photograph shows turned vase spindles and a continuous top rail."""
    ax,ay=a;bx,by=c
    profile=[(0,.091),(.065,.091),(.114,.062),(.20,.047),(.49,.087),
             (.57,.081),(.66,.056),(.80,.040),(.86,.054),(.91,.075),(1,.075)]
    if lod:profile=[profile[i] for i in (0,1,3,4,6,7,9,10)]
    for i in range(count):
        t=(i+.5)/count
        b.lathe((ax+(bx-ax)*t,ay+(by-ay)*t),
                [(z0+(z1-z0)*h,r) for h,r in profile],TRIM,
                segments=8 if lod else 16,label=label+' spindles')

def round_column(b,x,lod):
    foot=LANDING
    parts=[(foot,.21),(foot+.06,.21),(foot+.09,.185),(foot+.117,.175),
           (foot+.16,.184),(foot+.19,.17),(foot+.22,.151)]
    b.lathe((x,0),parts,TRIM,segments=16 if lod else 40,label='four column moulded bases')
    top=SPRING-.18;seg=24 if lod else 80;verts=[];faces=[]
    for z,r in [(foot+.208,.15),(foot+.33,.149),(top-.10,.139),(top,.141)]:
        for j in range(seg):
            a=2*pi*j/seg
            groove=(.004 if lod else .010)*(.5+.5*cos(10*a))
            verts.append((x+(r-groove)*cos(a),(r-groove)*sin(a),z))
    for row in range(3):
        for j in range(seg):
            n=(j+1)%seg;faces.append((row*seg+j,row*seg+n,(row+1)*seg+n,(row+1)*seg+j))
    faces.extend([tuple(reversed(range(seg))),tuple(3*seg+j for j in range(seg))])
    b.add(verts,faces,TRIM,'four vertical fluted shafts')
    b.lathe((x,0),[(top-.018,.143),(top+.023,.174),(top+.075,.175),
            (top+.11,.21),(top+.15,.218),(SPRING+.010,.216)],
            TRIM,segments=16 if lod else 40,label='four bell capitals')
    b.box((x,0,SPRING+.023),(.419,.419,.072),TRIM,label='square abaci')

def lower_window(f,cx,center,lod):
    w=1.46 if center else 1.56;cw=w/2;spring=2.49;rise=.47;bottom=LANDING if center else .91
    outer=opening(cx,bottom,w,spring+rise-bottom,rise,12 if lod else 28)
    inner=opening(cx,bottom+.05,w-.13,spring+rise-bottom-.135,rise-.052,12 if lod else 28)
    f.prism(outer.difference(inner),-.15,-.016,TIMBER,'arched timber casing')
    f.prism(inner.intersection(box(cx-cw,spring,cx+cw,3.2)),-.17,-.157,GLASS,'arched fanlight')
    f.box(cx,spring,w-.075,.073,.076,-.082,TIMBER,'fanlight transom')
    for angle in (30,60,90,120,150):
        a=angle*pi/180
        f.line((cx,spring+.017,-.108),(cx+(cw-.076)*cos(a),spring+(rise-.077)*sin(a),-.108),.018,TIMBER,6 if lod else 9,'fanlight radial sash')
    if center:
        f.prism(box(cx-cw+.055,bottom+.015,cx+cw-.055,spring-.023),-.433,-.412,'inner threshold shadow','opening behind two folded entrance leaves')
        for side in [-1,1]:
            hinge=cx+side*(cw-.026)
            a=f.point(hinge,0,-.102)[:2];b=f.point(hinge-side*.09,0,-.73)[:2]
            leaf=Facade(f.builder,a if side>0 else b,b if side>0 else a,'folded central glazed door')
            leaf.box(0,(spring+bottom)/2,leaf.length,spring-bottom-.048,.048,0,TIMBER,'timber leaf')
            for z,h in [(1.08,.75),(1.98,.91)]:
                leaf.box(0,z,leaf.length-.10,h,.022,.031,GLASS,'leaf glazing')
            leaf.box(0,1.52,leaf.length-.055,.06,.033,.030,TIMBER,'door rail')
    else:
        f.prism(box(cx-cw+.05,bottom+.035,cx+cw-.05,spring-.027),-.18,-.165,GLASS,'recessed sash glass')
        for delta in (-.25,.25):
            f.box(cx+w*delta,(spring+bottom)/2,.043,spring-bottom-.04,.055,-.101,TIMBER,'side window mullion')
        for z in [1.42,1.94]:
            f.box(cx,z,w-.08,.055,.057,-.098,TIMBER,'side window glazing bar')

def add_building(b,lod):
    count=14 if lod else 32
    front=Facade(b,(-HALF,0),(HALF,0),'garden loggia')
    back=Facade(b,(-HALF,REAR),(HALF,REAR),'rear window wall')
    floor(b,-HALF,HALF,-.19,REAR+.18,.012,LANDING,'porch paving','raised open porch')
    for n,z in enumerate((.135,.27,.405)):
        floor(b,-1.02,1.02,-1.11+n*.31,-.16,.006,z,'stone step','three central stone treads')
    for side in (-1,1):
        floor(b,side*1.12-.10,side*1.12+.10,-1.10,-.17,.008,.18,'stone step','outer tread cheek')
    openings=[opening(x,SPRING-.011,1.92,1.00,.962,count)for x in CENTERS]
    wholes=unary_union(openings)
    front.prism(box(-HALF,SPRING,HALF,DECK-.11).difference(wholes),-.29,.018,IVORY,'three arch spandrels')
    for x,hole in zip(CENTERS,openings):
        band=hole.buffer(.075,join_style=2).difference(hole).intersection(box(x-1.063,SPRING+.019,x+1.063,4.04))
        front.prism(band,-.012,.083,TRIM,'moulded archivolts')
        front.prism(box(x-.065,3.807,x+.065,3.984),.067,.112,TRIM,'three projecting keystones')
    for x in [-3.24,-1.08,1.08,3.24]:round_column(b,x,lod)
    floor(b,-HALF-.042,HALF+.042,-.18,REAR+.19,DECK-.17,DECK-.065,TRIM,'terrace lower lip')
    floor(b,-HALF,HALF,-.109,REAR+.18,DECK-.066,DECK,'terrace surface','terrace slab')
    lower_shapes=[opening(x,LANDING if x==0 else .91,1.46 if x==0 else 1.56,
                          2.96-(LANDING if x==0 else .91),.47,count) for x in CENTERS]
    upperholes=[box(x-.57,5.18,x+.57,6.94)for x in CENTERS]
    back.prism(box(-HALF,LANDING,HALF,7.18).difference(unary_union(lower_shapes+upperholes)),
               -.19,.012,IVORY,'loggia and first floor backdrop')
    for x in CENTERS:
        lower_window(back,x,x==0,lod)
        back.box(x,6.06,1.13,1.749,.048,-.149,GLASS,'three upper dark windows')
        outline=box(x-.60,5.165,x+.60,6.965).difference(box(x-.535,5.216,x+.535,6.899))
        back.prism(outline,-.162,-.016,TIMBER,'upper French window frames')
        back.box(x,6.06,.046,1.71,.052,-.084,TIMBER,'upper mullions')
        for z in [5.75,6.48]:
            back.box(x,z,1.096,.044,.055,-.083,TIMBER,'upper transoms')
        back.box(x,6.999,1.35,.073,.117,.024,TRIM,'upper lintel hood')
    for sx in [-1,1]:
        a,bx=sorted([sx*1.29,sx*3.14])
        floor(b,a,bx,-.103,.116,LANDING,LANDING+.16,TRIM,'lower flank plinth')
        floor(b,a-.017,bx+.017,-.13,.134,1.206,1.296,TRIM,'lower flank handrail')
        balusters(b,(a,0),(bx,0),LANDING+.16,1.206,7,lod,'lower flank')
    for a,bx in [(-3.27,-1.11),(-1.04,1.04),(1.11,3.27)]:
        balusters(b,(a,-.029),(bx,-.029),DECK+.092,DECK+.782,9,lod,'upper balcony')
    for sx in [-1,1]:
        xx=sx*(HALF-.13)
        balusters(b,(xx,.10),(xx,REAR-.07),DECK+.092,DECK+.782,5,lod,'terrace return')
        floor(b,xx-.105,xx+.105,0,REAR+.03,DECK,DECK+.11,TRIM,'side rail plinth')
        floor(b,xx-.12,xx+.12,-.1,REAR+.03,DECK+.777,DECK+.872,TRIM,'side rail cap')
        front.box(xx,DECK+.45,.21,.90,.235,.025,TRIM,'terrace end posts')
    front.box(0,DECK+.055,HALF*2,.11,.217,.025,TRIM,'front rail plinth')
    front.box(0,DECK+.825,HALF*2+.046,.10,.250,.027,TRIM,'front rail cap')
    for x in [-1.08,1.08]:
        front.box(x,DECK+.441,.105,.78,.17,.024,TRIM,'intermediate end blocks')
    for text,z,width,ht in [('毕加索艺术中心',4.696,2.43,.21),('PICASSO ART CENTER',4.397,2.81,.20)]:
        add_facade_lettering(front,text,0,z,width,ht,.026,.050,'black museum letters',label='2025 museum sign',font=Path(__file__).parent/'fonts/GardenLoggiaSign.otf')
