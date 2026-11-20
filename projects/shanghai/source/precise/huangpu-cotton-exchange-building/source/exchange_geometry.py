"""Photo-led elevations of the old Cotton Exchange, with its museum-period entrance and roof lantern."""
from math import pi,cos,sin
from pathlib import Path

from shapely.geometry import box,Polygon,Point,LineString
from shapely.ops import unary_union
from photo_architecture import Facade,opening
from sign_lettering import add_facade_lettering

STONE='warm grey cast stone'
BASE='rusticated grey granite'
LIGHT='pale carved stone'
SEAM='dark mortar joints'
FRAME='bottle-green steel casement'
GLASS='green grey glazing'
IRON='forged museum gate'
GOLD='aged gold inscription'
DARK='entrance shadow'
ROOF='dark pavilion roof'
METAL='weathered sheet metal'
PALETTE={
    STONE:dict(color=[.565,.541,.481],roughness=.89),BASE:dict(color=[.382,.376,.340],roughness=.93),
    LIGHT:dict(color=[.674,.652,.586],roughness=.81),SEAM:dict(color=[.272,.269,.242],roughness=.96),
    FRAME:dict(color=[.176,.221,.185],roughness=.61,metallic=.28),GLASS:dict(color=[.157,.221,.195],roughness=.30,metallic=.18),
    IRON:dict(color=[.274,.262,.203],roughness=.65,metallic=.52),GOLD:dict(color=[.734,.572,.312],roughness=.53,metallic=.53),
    DARK:dict(color=[.087,.089,.080],roughness=.88),ROOF:dict(color=[.264,.267,.244],roughness=.91),
    METAL:dict(color=[.390,.397,.350],roughness=.61,metallic=.28)}
AXIS=3.18
CROWN=19.46
CX,CY=-20.05,4.50
RADIUS=4.38
FONT=Path(__file__).with_name('fonts')/'NaturalHistorySign.otf'
CURVE=[(CX+RADIUS*cos((180+t*90/12)*pi/180),CY+RADIUS*sin((180+t*90/12)*pi/180))for t in range(13)]
PLAN=Polygon([(-20.05,.12),(20.06,.12),(47.09,54.54),(19.69,71.18),(-24.42,5.00),*CURVE[:-1]])
# The two lower rectangles are visible in all three satellite releases. Their heights are approximate.
COURT=Polygon([(2.7,19.3),(12.8,14.5),(22.7,35.4),(12.8,40.0)])
REAR=Polygon([(14.9,52.8),(32.6,44.1),(35.4,50.2),(17.9,58.8)])


def lathe(b,center,rings,sides,material,label):
    verts=[];faces=[]
    for radius,z in rings:
        for i in range(sides):
            a=2*pi*i/sides;verts.append((center[0]+radius*cos(a),center[1]+radius*sin(a),z))
    for row in range(len(rings)-1):
        for i in range(sides):
            j=(i+1)%sides;a=row*sides;faces.append((a+i,a+j,a+sides+j,a+sides+i))
    faces.extend([tuple(range(sides-1,-1,-1)),tuple(range((len(rings)-1)*sides,len(rings)*sides))])
    b.add(verts,faces,material,label)


def casements(f,windows,depth,low,label='windows'):
    panels=[];sashes=[]
    for op,cols,rows in windows:
        l,b,r,t=op.bounds
        panels.append(op.buffer(.013,join_style='mitre'))
        bars=[op.difference(op.buffer(-.060,join_style='mitre'))]
        for i in range(1,cols):
            x=l+(r-l)*i/cols;bars.append(box(x-.035,b,x+.035,t))
        for i in range(1,rows):
            h=b+(t-b)*i/rows;bars.append(box(l,h-.031,r,h+.031))
        if not low and cols>1:
            for i in range(cols):
                x=l+(r-l)*(i+.5)/cols;bars.append(box(x-.015,b,x+.015,t))
        sashes.append(op.intersection(unary_union(bars)))
    if panels:
        f.prism(unary_union(panels),-depth-.04,-depth,GLASS,label+' panes')
        f.prism(unary_union(sashes),-depth+.018,-depth+.068,FRAME,label+' mullions')


def floor_bands(f,length,low):
    for z,h,projection in [(6.68,.24,.30),(6.95,.18,.50),(14.68,.15,.19),(15.03,.21,.41),(18.97,.19,.33),(19.33,.25,.42)]:
        f.box(0,z,length+.02,h,projection,.055,LIGHT,'horizontal stone cornice')
    if not low:
        teeth=[box(-length/2+.21+i*.41,14.81,-length/2+.34+i*.41,14.94)for i in range(int((length-.30)/.41))]
        if teeth:f.prism(unary_union(teeth),.090,.27,LIGHT,'dentil course')


def bays(f,positions,upper_only=False,low=False,roof=CROWN):
    length=f.length;windows=[];sills=[]
    for x in positions:
        tiers=[(7.53,2.58),(11.54,2.30),(15.59,2.56)]
        if not upper_only:tiers=[(.39,1.84),(3.28,2.40),*tiers]
        for z,height in tiers:
            w=1.93 if z>=7 else 1.80
            o=box(x-w/2,z,x+w/2,z+height);windows.append((o,2,3 if z>3 else 2));sills.append(box(x-w/2-.10,z-.12,x+w/2+.10,z-.04))
    holes=unary_union([o for o,_,_ in windows]);main=box(-length/2,0,length/2,roof)
    f.prism(main.intersection(box(-length,0,length,6.78)).difference(holes),-.30,0,BASE,'rusticated lower storeys')
    f.prism(main.intersection(box(-length,6.78,length,roof)).difference(holes),-.31,0,STONE,'upper stone face')
    casements(f,windows,.326,low)
    if sills:f.prism(unary_union(sills),.006,.145,LIGHT,'stone window sills')
    if not low:
        seams=unary_union([box(-length/2,q*.61-.027,length/2,q*.61+.019)for q in range(1,12)]);f.prism(seams.difference(holes),.002,.012,SEAM,'lower coursing')
    for a,b in zip(positions,positions[1:]):
        x=(a+b)/2
        f.box(x,10.84,.54,7.55,.27,.084,STONE,'upper engaged pier')
        f.box(x,14.49,.76,.25,.35,.108,LIGHT,'pier capital')
        f.box(x,15.66,.41,1.12,.15,.065,STONE,'attic pilaster base')
    floor_bands(f,length,low)


def arch_face(f,low):
    length=f.length;h=length/2
    op=opening(0,15.42,5.2,2.50,2.05,24);portal=box(-1.64,.10,1.64,4.38)
    bay=box(-2.35,7.26,2.35,14.43);small=[]
    for x in [-3.47,3.47]:
        for z in [7.88,11.79]:small.append((box(x-.51,z,x+.51,z+1.76),1,3))
    cuts=unary_union([op,portal,bay,*[o for o,_,_ in small]])
    f.prism(box(-h,0,h,CROWN).difference(cuts),-.30,0,STONE,'projecting main entrance bay')
    casements(f,[(op,5,2),*small],.337,low,'arched top and narrow sidelights')
    f.prism(op.buffer(.17,join_style='round').difference(op).intersection(box(-3.0,15.44,3,18.5)),.008,.152,LIGHT,'semicircular window archivolt')
    for x in [-3.40,3.40]:
        for z in [7.1,10.8,14.31]:f.box(x,z,1.42,.15,.26,.09,LIGHT,'sill block')
    floor_bands(f,length,low)
    # The shallow canted oriel below the semicircle is visible directly above the museum entrance.
    base_y=f.center[1];outline=[(AXIS-2.35,base_y),(AXIS-1.82,base_y-.55),(AXIS+1.82,base_y-.55),(AXIS+2.35,base_y)]
    for a,b in zip(outline,outline[1:]):
        side=Facade(f.builder,a,b,'Entrance oriel');W=side.length
        holes=[] if W<1 else [(box(-1.46,z,1.46,z+1.86),3,2)for z in [7.86,11.73]]
        side.prism(box(-W/2,7.26,W/2,14.43).difference(unary_union([o for o,_,_ in holes])),-.19,0,LIGHT,'canted frame')
        casements(side,holes,.248,low,'oriel')
    for z in [7.22,10.58,14.41]:f.builder.plan_prism(Polygon(outline),z,z+.13,LIGHT,'Oriel/canted stringcourse')
    tri=Polygon([(-h-.18,19.34),(0,21.49),(h+.18,19.34)])
    f.prism(tri,-.33,.19,STONE,'triangular pediment')
    for a,b in [((-h-.22,19.38),(0,21.58)),((0,21.58),(h+.22,19.38))]:
        f.prism(LineString([a,b]).buffer(.10,cap_style='square'),.055,.32,LIGHT,'pediment raking cornice')
    f.prism(tri.buffer(-.35).boundary.buffer(.035),.19,.225,LIGHT,'tympanum moulding')
    museum_gate(f,low)


def museum_gate(f,low):
    # A split bronze disc and two wreath-shaped medallions are visible on the surviving two-leaf grille.
    f.prism(box(-1.68,.09,1.68,4.43),-.98,-.94,DARK,'dark lobby behind gate')
    edge=box(-1.63,.10,1.63,4.38);bars=[edge.difference(edge.buffer(-.087,join_style='mitre')),box(-.038,.12,.038,4.36)]
    for x in [-1.38,-1.1,-.84,-.56,-.28,.28,.56,.84,1.1,1.38]:bars.append(box(x-.018,.14,x+.018,4.34))
    for h in [.44,3.75,4.06]:bars.append(box(-1.60,h-.021,1.60,h+.021))
    for s in [-1,1]:
        for z in [.78,3.36,3.97]:
            for j in range(3 if not low else 2):
                x=s*(.34+.39*j)
                path=[(x+.15*cos(t*pi/13)*(1-t/35),z+.11*sin(t*pi/13)*(1-t/35))for t in range(30)]
                bars.append(LineString(path).buffer(.016,cap_style='round'))
        rings=[]
        for scale in [1,.77]:
            pts=[(s*.89+.34*scale*cos(2*pi*t/32),2.19+.44*scale*sin(2*pi*t/32))for t in range(33)]
            rings.append(LineString(pts).buffer(.021))
        for j in range(8):
            a=(j+.65)*pi/9
            for flank in [-1,1]:
                x=s*.89+flank*.35*sin(a);z=2.19-.45*cos(a)
                rings.append(Polygon([(x-.034,z),(x+flank*.106,z+.079),(x+.038,z+.071)]))
        f.prism(unary_union(rings),-.81,-.755,GOLD,'paired laurel gate ornaments')
    f.prism(unary_union(bars),-.88,-.817,IRON,'closed iron double gate')
    disk=Point(0,1.45).buffer(.416,quad_segs=18).difference(box(-.025,.8,.025,2.1))
    f.prism(disk,-.827,-.728,GOLD,'split round gate plate')
    for x in [-1.66,1.66]:f.box(x,2.28,.09,4.55,.99,-.42,BASE,'lobby side reveal')
    f.box(0,4.42,3.34,.09,1.0,-.42,LIGHT,'door soffit')
    f.box(0,.05,3.39,.10,1.39,-.30,BASE,'door threshold')
    f.prism(box(-1.97,4.73,1.97,5.81),.02,.18,LIGHT,'museum stone nameplate')
    for i,c in enumerate('上海自然博物馆'):
        add_facade_lettering(f,c,(i-3)*.48,5.28,.36,.43,.188,.235,GOLD,label=f'Museum name {i+1}',font=FONT)
    for s in [-1,1]:
        x=AXIS+s*2.53;y=f.center[1]-.30
        lathe(f.builder,(x,y+.008),[(.397,.06),(.397,.19),(.327,.25),(.280,.39),(.269,5.73),(.301,5.81),(.34,5.89)],18 if low else 30,LIGHT,'Portal/Ionic shaft')
        for dx in [-.26,.26]:
            spiral=[(x+dx+(.128-.0023*t)*cos(t*pi/14),y-.335,6.028+(.128-.0023*t)*sin(t*pi/14))for t in range(43)]
            f.builder.tube(spiral,.042,LIGHT,sides=6 if low else 10,label='Portal/paired Ionic volutes')
        f.builder.box((x,y,6.23),(.86,.77,.20),LIGHT,label='Portal/Ionic abacus')
    f.box(0,6.46,6.6,.30,.63,.24,LIGHT,'portico lintel')


def corner_rotunda(builder,low):
    center=(CX,CY);sides=40 if low else 64
    # Short annular bands leave the eight openings in the lantern clear.
    def collar(r0,r1,z0,z1,material,label):
        shape=Point(center).buffer(r1,quad_segs=sides//4).difference(Point(center).buffer(r0,quad_segs=sides//4))
        builder.plan_prism(shape,z0,z1,material,'Lantern/'+label)
    collar(2.25,3.03,19.32,19.79,STONE,'circular porch sill')
    collar(2.26,2.93,19.79,20.13,LIGHT,'lower stringcourse')
    for j in range(8):
        a=(j+.5)*pi/4
        x=CX+2.62*cos(a);y=CY+2.62*sin(a)
        lathe(builder,(x,y),[(.33,20.07),(.33,20.27),(.253,20.36),(.228,24.00),(.305,24.08),(.352,24.27)],12 if low else 24,LIGHT,'Lantern/open colonnade')
    collar(2.05,2.95,24.15,24.37,LIGHT,'column head')
    collar(1.95,3.05,24.36,24.72,STONE,'ring beam')
    collar(1.96,3.09,24.71,24.84,LIGHT,'ring coping')
    corners=[(CX+2.81*cos((j+.5)*pi/4),CY+2.81*sin((j+.5)*pi/4))for j in range(8)]
    for i,(a,b) in enumerate(zip(corners,corners[1:]+corners[:1])):
        f=Facade(builder,a,b,'Lantern oculi');hw=f.length/2
        eye=Point(0,25.97).buffer(.49,quad_segs=10 if low else 15)
        end=Polygon([(-hw,24.83),(hw,24.83),(hw,26.46),(.74,26.68),(.40,26.99),(0,27.12),(-.40,26.99),(-.74,26.68),(-hw,26.46)])
        f.prism(end.difference(eye),-.23,0,STONE,'oculus wall')
        f.prism(eye.buffer(.134).difference(eye),-.015,.104,LIGHT,'round aperture surround')
        # Observed dark backing behind the circular opening. The colonnade below remains open.
        f.prism(eye.buffer(.018),-.40,-.375,DARK,'oculus backing')
    # Stepped top and a domed cap with a flagstaff are visible in both street periods.
    rings=[(2.65,26.45),(2.67,26.57)]
    for j in range(1,13):
        a=j*pi/25
        rings.append((max(.08,2.67*cos(a)),26.52+2.04*sin(a)))
    rings.append((.075,28.57))
    lathe(builder,center,rings,sides,METAL,'Lantern/rounded dome')
    lathe(builder,center,[(.185,28.50),(.185,28.70),(.068,28.79),(.040,31.69)],12 if low else 18,METAL,'Lantern/flagstaff')


def curved_return(builder,low):
    # The long side alley is visible from the foot of the rounded southwest corner.
    # Use separate cylindrical belts so the cornice stays continuous above the windows.
    for j,(a,b) in enumerate(zip(CURVE,CURVE[1:])):
        f=Facade(builder,a,b,'Curved street corner');w=f.length
        holes=[];glass=[]
        for (bottom,top) in [(.65,2.31),(3.41,5.53),(7.58,10.0),(11.60,13.78),(15.64,18.10)]:
            if j in (0,4,8,11):continue
            op=box(-w/2-.001,bottom,w/2+.001,top);holes.append(op);glass.append((op,1,2))
        base=box(-w/2,0,w/2,CROWN)
        notch=unary_union(holes).intersection(base)
        f.prism(base.intersection(box(-5,0,5,6.78)).difference(notch),-.29,0,BASE,'rounded lower masonry')
        f.prism(base.intersection(box(-5,6.78,5,CROWN)).difference(notch),-.30,0,STONE,'rounded upper masonry')
        casements(f,glass,.299,low,'curved green windows')
        for z,h,dep in [(6.88,.29,.39),(10.56,.14,.18),(14.91,.23,.32),(19.15,.20,.34),(19.40,.10,.43)]:
            f.box(0,z,w+.026,h,dep,.062,LIGHT,'circular mouldings')


def office_return(builder,a,b,count,low,label):
    f=Facade(builder,a,b,label);length=f.length
    positions=[(i+.5-count/2)*length/count for i in range(count)]
    bays(f,positions,low=low)
    return f


def make_exchange(builder,low=False):
    x0,x1=AXIS-4.13,AXIS+4.13
    for a,b,n,label in [(-20.05,x0,4,'West south front'),(x1,20.06,3,'East south front')]:
        f=Facade(builder,(a,.12),(b,.12),label)
        bays(f,[(i+.5-n/2)*f.length/n for i in range(n)],low=low)
    front_y=-.38
    f=Facade(builder,(x0,front_y),(x1,front_y),'South main bay');arch_face(f,low)
    for a,b in [((x0,.12),(x0,front_y)),((x1,front_y),(x1,.12))]:
        f=Facade(builder,a,b,'Projecting entrance return');f.wall(0,CROWN,thickness=.19,material=STONE)
    curved_return(builder,low)
    west=(-24.42,5.00);back_w=(19.69,71.18);back_e=(47.09,54.54);front_e=(20.06,.12)
    office_return(builder,front_e,back_e,10,low,'East garden facade')
    office_return(builder,back_e,back_w,5,low,'Northern rear')
    office_return(builder,back_w,west,12,low,'West office alley')
    if abs(west[1]-CURVE[0][1])>.1:
        Facade(builder,west,CURVE[0],'Corner junction').wall(0,CROWN,thickness=.25,material=STONE)
    # Raised trading hall floor under the later museum occupied these roof wells. Hidden interiors
    # are represented by the lower roof only, preserving the uninterrupted ground-level floor.
    builder.plan_prism(PLAN,0,.088,BASE,'Envelope/lower slab')
    builder.plan_prism(PLAN.difference(COURT.union(REAR)),18.97,19.12,ROOF,'Roof/upper terrace')
    for shape,bottom,label in [(COURT,13.10,'trading hall'),(REAR,14.55,'rear court')]:
        builder.plan_prism(shape,bottom-.13,bottom,ROOF,'Roof/'+label+' lower surface')
        ring=list(shape.exterior.coords)
        for a,b in zip(ring,ring[1:]):
            f=Facade(builder,b,a,'Inner '+label);w=f.length
            opens=[]
            if w>8:
                count=3 if w>18 else 2
                for i in range(count):
                    x=(i+.5-count/2)*w/count;opens.append((box(x-.54,16.0,x+.54,17.65),1,2))
            f.prism(box(-w/2,bottom,w/2,19.12).difference(unary_union([o for o,_,_ in opens])),-.18,0,STONE,'inner courtyard face')
            casements(f,opens,.24,low,'court glass')
    builder.plan_prism(box(x0,-.39,x1,.14),18.99,19.12,ROOF,'Roof/entrance projection')
    # The rounded corner fronts a larger rectangular deck, with a clear viewing gallery below its dome.
    builder.plan_prism(Point((CX,CY)).buffer(2.98,quad_segs=16),19.10,19.33,LIGHT,'Lantern/plinth')
    corner_rotunda(builder,low)
