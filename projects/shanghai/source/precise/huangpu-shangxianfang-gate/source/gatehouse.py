"""Shangxianfang's occupied gatehouse and its covered through-lane, in metres."""
from math import cos, pi, sin
from pathlib import Path

from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade
from sign_lettering import add_facade_lettering

PALETTE = {
    'red-brown brick': {'color':[.48,.224,.13],'roughness':.9},
    'orange brick': {'color':[.57,.287,.164],'roughness':.87},
    'dark fired brick': {'color':[.39,.172,.107],'roughness':.88},
    'fine mortar': {'color':[.395,.286,.219],'roughness':.95},
    'limestone': {'color':[.66,.61,.51],'roughness':.81},
    'ashlar reveal': {'color':[.50,.47,.397],'roughness':.84},
    'weathered tablet': {'color':[.52,.44,.334],'roughness':.82},
    'carved lettering': {'color':[.319,.267,.202],'roughness':.86},
    'brown timber': {'color':[.139,.076,.047],'roughness':.62},
    'window glass': {'color':[.106,.144,.155],'roughness':.25,'metallic':.17},
    'dark iron': {'color':[.073,.077,.073],'roughness':.61,'metallic':.43},
    'passage plaster': {'color':[.48,.454,.392],'roughness':.94},
    'paving': {'color':[.34,.337,.306],'roughness':.87},
    'clay tile': {'color':[.36,.145,.09],'roughness':.85},
    'plain party wall': {'color':[.40,.296,.218],'roughness':.92},
}
WALL = 3.51
DEPTH = 11.70
CLEAR = 2.77
STONE = 'limestone'
FONT = Path(__file__).with_name('fonts')/'ShangxianfangTablet.otf'


def profile(lod):
    # Coordinates were read relative to the base line in the 2022 district frontal photograph.
    half=[(0,12.91),(.24,12.88),(.53,12.79),(.83,12.68),(1.13,12.55),(1.42,12.48),
          (1.71,12.45),(1.88,12.45),(1.88,12.11),(2.07,12.05),(2.24,11.93),
          (2.40,11.78),(2.60,11.67),(2.76,11.63),(2.82,11.40),(3.02,11.21),(3.51,11.15)]
    if lod:
        half=[p for i,p in enumerate(half) if i not in (2,4,10)]
    return [(-u,z) for u,z in half[:0:-1]]+half


def glazing(f,hole,lod,cols,rows,name):
    x0,z0,x1,z1=hole.bounds
    f.prism(hole.buffer(.012,join_style='mitre'),-.40,-.374,'window glass',name+' glazing')
    inner=hole.buffer(-.072,join_style='mitre')
    bars=[box(x-.026,z0,x+.026,z1) for i in range(1,cols) for x in (x0+(x1-x0)*i/cols,)]
    bars.extend(box(x0,z-.023,x1,z+.023) for i in range(1,rows) for z in (z0+(z1-z0)*i/rows,))
    f.prism(hole.difference(inner.difference(unary_union(bars))),-.358,-.272,'brown timber',name+' layered joinery')
    if not lod:
        f.prism(hole.buffer(.034,join_style='mitre').difference(hole),-.01,.046,'dark fired brick',name+' reveal edging')


def masonry(f,mask,lod):
    """The fine horizontal and staggered bed joints are absent from the distant mesh."""
    if lod:
        f.prism(mask,.001,.021,'red-brown brick','red brick facing')
        return
    courses=int(13.0/.096)+1
    brick_groups=[[] for _ in range(3)]
    for r in range(courses):
        z=r*.096
        shift=.104 if r%2 else 0
        for col in range(-18,19):
            x=col*.208+shift
            tile=box(x+.005,z+.004,x+.205,z+.092)
            if not mask.intersects(tile):
                continue
            brick=mask.intersection(tile)
            if brick.area<.00006:
                continue
            tone=(r*7+col*11)%17
            brick_groups[0 if tone<13 else 1 if tone<16 else 2].append(brick)
    for i,mat in enumerate(('red-brown brick','orange brick','dark fired brick')):
        if brick_groups[i]:
            f.prism(unary_union(brick_groups[i]),.004,.027,mat,'original-length brick courses')


def central_elevation(b,lod):
    f=Facade(b,(-WALL,0),(WALL,0),'Middle Huaihai Road')
    summit=profile(lod)
    outline=Polygon([(-WALL,0),(WALL,0)]+summit[::-1])
    portal=Polygon([(-CLEAR,-.03),(CLEAR,-.03),(CLEAR,3.07),(2.62,3.12),(2.52,3.31),
                    (-2.52,3.31),(-2.62,3.12),(-CLEAR,3.07)])
    lower=[box(-2.13,4.48,-1.32,6.95),box(-.87,4.48,.87,7.29),box(1.32,4.48,2.13,6.95)]
    upper=[box(-1.64,8.86,-.86,10.27),box(.86,8.86,1.64,10.27)]
    cut=unary_union([portal,*lower,*upper])
    f.prism(outline.difference(cut),-.36,0,'fine mortar','pierced street masonry')
    mask=outline.difference(cut).intersection(box(-WALL,3.98,WALL,13.1))
    masonry(f,mask,lod)
    for i,hole in enumerate(lower+upper):
        glazing(f,hole,lod,4 if i==1 else 2,4 if i<3 else 2,'central sash' if i==1 else 'flanking sash')
        x0,z0,x1,z1=hole.bounds
        f.box((x0+x1)/2,z0-.072,x1-x0+.13,.13,.26,.045,STONE,'window stool')
    for j,x in enumerate((-1.095,1.095)):
        f.box(x,5.92,.42,2.92,.26,.074,STONE,'tall separator between windows')
    # The lower stone frame widens at the corners of the rectangular carriage opening.
    f.prism(box(-WALL,0,WALL,4.03).difference(portal),-.02,.145,'ashlar reveal','ashlar doorcase')
    span=box(-3.01,0,3.01,3.58).difference(portal)
    f.prism(span,.13,.205,STONE,'returned frame with stepped corners')
    for x in (-3.16,3.16):
        for z in (.55,1.10,1.65,2.20,2.75,3.30):
            f.box(x,z,.65,.019,.018,.149,'fine mortar','base masonry coursing')
    f.box(0,4.05,6.60,.14,.30,.10,STONE,'continuous first-floor sill')
    for x in (-1.73,0,1.73):
        width=1.71 if x==0 else .78
        for z in (4.60,5.37):
            f.box(x,z,width,.041,.072,-.025,'dark iron','balconette rails')
        for j in range(7 if x==0 else 4):
            step=6 if x==0 else 3
            px=x-.47*width+j*.94*width/step
            f.box(px,4.99,.023,.78,.045,-.025,'dark iron','iron window guards')
        if not lod:
            for j in range(4 if x==0 else 2):
                cx=x+(j-(1.5 if x==0 else .5))*.35
                for side in (-1,1):
                    pts=[f.point(cx+side*.144*cos(t*pi/12),4.96+.25*sin(t*pi/12),-.015) for t in range(13)]
                    b.tube(pts,.017,'dark iron',6,'Window guards/curved branches')
    for side in (-1,1):
        pilaster(f,side,lod)
    for v,w,d,mat in [(0,.24,.15,'ashlar reveal'),(.085,.12,.23,STONE),(.206,.060,.28,STONE)]:
        pts=[(x,z-v) for x,z in summit]
        band=LineString(pts).buffer(w/2,cap_style='flat',join_style='round',quad_segs=3 if lod else 6)
        f.prism(band,-.02,d,mat,'stepped curvilinear parapet coping')
    f.box(0,12.91,.23,.30,.34,.127,STONE,'crest clasp')
    b.lathe((0,-.07),[(13.03,.115),(13.11,.112),(13.18,.063),(13.23,.03)],STONE,10 if lod else 18,'Gable/diminutive finial')
    tablet(f)
    return portal


def pilaster(f,side,lod):
    x=side*3.265
    f.box(x,6.89,.40,6.87,.32,.088,STONE,'quoined flanking pilaster')
    f.box(x,3.74,.52,1.05,.39,.149,STONE,'pilaster drop')
    for j in range(7):
        f.box(x,3.40+j*.07,.32,.027,.035,.36,'ashlar reveal','fluted pilaster foot')
    for j in range(10):
        f.box(x,4.47+j*.566,.394,.014,.015,.250,'ashlar reveal','pilaster ashlar joints')
    for z,w,h,d in [(10.32,.46,.13,.22),(10.45,.56,.17,.25),(10.59,.69,.12,.28)]:
        f.box(x,z,w,h,d+.2,d/2,STONE,'moulded capital')
    cap=Polygon([(x-.44,10.63),(x+.44,10.63),(x+.28,10.88),(x+.19,11.19),(x-.19,11.19),(x-.28,10.88)])
    f.prism(cap,-.05,.27,STONE,'sloping capital hood')
    obelisk=Polygon([(x-.16,11.16),(x+.16,11.16),(x+.092,12.02),(x-.092,12.02)])
    f.prism(obelisk,-.06,.19,STONE,'square-taper end obelisk')
    cx=side*2.61;cz=11.29
    f.prism(Point(cx,cz).buffer(.28,quad_segs=5 if lod else 11),.01,.13,STONE,'circular springing boss')
    if not lod:
        pts=[f.point(cx+side*(.025+.014*t)*cos(t),cz+(.025+.014*t)*sin(t),.149) for t in [i*.25 for i in range(50)]]
        f.builder.tube(pts,.018,'ashlar reveal',7,'Capital/spiral volute')


def tablet(f):
    f.box(0,9.59,1.55,3.02,.26,.13,STONE,'stone tablet outer block')
    f.box(0,9.63,1.08,2.59,.09,.296,'weathered tablet','inset inscription field')
    f.box(0,11.13,1.73,.15,.44,.19,STONE,'tablet head cornice')
    f.box(0,8.03,1.49,.13,.39,.16,STONE,'tablet bevelled foot')
    for side in (-1,1):
        x=side*.845
        f.box(x,10.58,.33,.16,.17,.16,STONE,'tablet ears')
        f.box(x-side*.065,10.42,.20,.22,.17,.16,STONE,'tablet stepped returns')
    for i,ch in enumerate('尚賢坊'):
        add_facade_lettering(f,ch,0,10.43-i*.82,.728,.729,.343,.367,'carved lettering',
                             label='Inscribed tablet',font=FONT)


def iron_screen(b,lod):
    f=Facade(b,(-3.30,.78),(3.30,.78),'Recessed street screen')
    for side in (-1,1):
        left,right=sorted((side*.74,side*(CLEAR-.03)))
        length=right-left;mid=(left+right)/2
        f.box(mid,2.89,length,.081,.12,0,'dark iron','upper transom')
        f.box(mid,2.35,length,.068,.10,0,'dark iron','cross rail')
        f.box(mid,.775,length,.067,.10,0,'dark iron','lower cross rail')
        for x in (left,right):
            f.box(x,1.49,.074,2.91,.13,0,'dark iron','screen end post')
        n=9 if lod else 15
        for i in range(1,n):
            x=left+i*length/n
            f.box(x,1.46,.026,2.85,.052,0,'dark iron','slender bars')
        if not lod:
            for band in (.69,2.57):
                for i in range(7):
                    x=left+.095+i*(length-.19)/6
                    f.prism(Point(x,band).buffer(.095,quad_segs=6).boundary.buffer(.012),.028,.055,
                            'dark iron','small roundels')
    f.box(0,2.94,CLEAR*2,.09,.12,0,'dark iron','header above central opening')
    for i in range(-10,11):
        f.box(i*.256,3.096,.025,.258,.047,0,'dark iron','transom balusters')


def covered_lane(b):
    for side in (-1,1):
        left,right=sorted((side*CLEAR,side*WALL))
        b.plan_prism(box(left,.34,right,DEPTH),0,3.43,'passage plaster','Covered lane/plain side walls')
        b.plan_prism(box(left,.34,right,DEPTH),3.43,9.37,'plain party wall','Common wall/upper return')
        b.box((side*(CLEAR+.048),DEPTH*.5,.21),(.10,DEPTH-.04,.42),'ashlar reveal',label='Covered lane/stone skirting')
    b.plan_prism(box(-WALL,.33,WALL,DEPTH-.22),3.34,3.53,'passage plaster','Covered lane/continuous ceiling')
    b.plan_prism(box(-WALL,.12,WALL,DEPTH+.015),.002,.041,'paving','Covered lane/pavement')
    for y in (.36,3.58,7.08,DEPTH-.33):
        b.box((0,y,3.315),(WALL*2,.145,.072),'ashlar reveal',label='Covered lane/transverse lintels')
    back=Facade(b,(WALL,DEPTH),(-WALL,DEPTH),'Back edge of first row')
    rear_opening=box(-CLEAR,-.1,CLEAR,3.25)
    back.prism(box(-WALL,0,WALL,9.34).difference(rear_opening),-.32,0,'plain party wall','passage exit under plain rear wall')
    back.box(0,3.34,2*CLEAR+.28,.18,.26,-.036,'ashlar reveal','rear opening head')


def roof(b,lod):
    # Aerials show the red-tiled first row. The faces of this bounded bay stop at adjoining shops.
    ridge=DEPTH*.50
    def height(y):
        # The front attic windows require an eave above their heads.
        if y<=ridge:
            return 10.48+(11.48-10.48)*y/ridge
        return 11.48-(11.48-9.34)*(y-ridge)/(DEPTH-ridge)
    side=Facade(b,(WALL,0),(WALL,DEPTH),'East shared roof edge')
    west=Facade(b,(-WALL,DEPTH),(-WALL,0),'West shared roof edge')
    for f,near,far in ((side,height(0),height(DEPTH)),(west,height(DEPTH),height(0))):
        f.prism(Polygon([(-DEPTH/2,9.30),(DEPTH/2,9.30),(DEPTH/2,far),(0,height(ridge)),(-DEPTH/2,near)]),-.21,0,
                'plain party wall','bounded roof cheek')
    for y0,y1 in ((.36,ridge),(ridge,DEPTH+.03)):
        a=.011
        verts=[(-WALL,y0,height(y0)),(WALL,y0,height(y0)),(WALL,y1,height(y1)),(-WALL,y1,height(y1))]
        b.add(verts+[(x,y,z-.13) for x,y,z in verts],[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),
              (2,6,7,3),(3,7,4,0)],'clay tile','Roof/pitched tile plane')
        n=11 if lod else 22
        for i in range(n+1):
            x=-WALL+(WALL*2)*i/n
            b.tube([(x,y0,height(y0)+a),(x,y1,height(y1)+a)],.035 if lod else .028,
                   'clay tile',5 if lod else 7,'Roof/tile rolls')
        if not lod:
            for i in range(1,17):
                y=y0+(y1-y0)*i/17
                b.tube([(-WALL,y,height(y)+.017),(WALL,y,height(y)+.017)],.017,'dark fired brick',5,'Roof/tile course lips')
    b.tube([(-WALL-.03,ridge,height(ridge)+.045),(WALL+.03,ridge,height(ridge)+.045)],.085,
           'clay tile',7 if lod else 12,'Roof/ridge capping')
    # A small return closes the rear of the tall street parapet above the sloping roof.
    for x in (-WALL+.12,WALL-.12):
        b.box((x,.44,10.10),(.24,.30,1.56),'red-brown brick',label='Parapet/ends')


def make_gatehouse(builder,lod):
    central_elevation(builder,lod)
    covered_lane(builder)
    iron_screen(builder,lod)
    roof(builder,lod)
