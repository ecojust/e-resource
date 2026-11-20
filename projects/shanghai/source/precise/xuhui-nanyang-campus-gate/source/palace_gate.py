"""The 1935 masonry gate, the open 2010 street entrance and the windowed 2015 campus side."""
from math import cos, sin, pi
from pathlib import Path
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union
from photo_architecture import Facade
from sign_lettering import add_facade_lettering

BRICK='salmon red brick'; JOINT='rose grey mortar'; PLINTH='silvery grey rendered plinth'; POST='vermilion lacquer'
DOOR='oxblood timber'; PAINT='muted turquoise'; BLUE='blue green paint'; GOLD='ochre and gold detail'
ROOF='dark green glazed tile'; TILE='sage green rounded tile cap'; WOOD='shadowed rafters'
STONE='pale carved lion stone'; CARVE='shadowed stone recess'; BLACK='ink black'; WHITE='ivory signboard'; GLASS='old smoky glazing'
COLORS={BRICK:(.63,.246,.174),JOINT:(.66,.375,.306),PLINTH:(.57,.585,.586),POST:(.53,.095,.085),
        DOOR:(.255,.078,.060),PAINT:(.265,.425,.390),BLUE:(.106,.256,.238),GOLD:(.750,.502,.172),
        ROOF:(.156,.272,.174),TILE:(.276,.406,.275),WOOD:(.31,.166,.087),STONE:(.76,.739,.650),
        CARVE:(.334,.327,.285),BLACK:(.085,.074,.065),WHITE:(.855,.827,.728),GLASS:(.211,.270,.253)}
PALETTE={name:dict(color=list(rgb),roughness=.46 if name in (ROOF,TILE,POST,DOOR) else .83) for name,rgb in COLORS.items()}
FONT=Path(__file__).with_name('fonts')/'NanyangGatePlaque.otf'
Y_FRONT,Y_BACK=1.63,10.36
X_WALL=7.33; X_PORTAL=2.92
EAVE_X=8.09; RIDGE_X=4.98; Y_MID=6.02; EAVE_Y=5.70


def cube(builder,xyz,size,material,label):
    builder.box(xyz,size,material,label=label)


def ellipsoid(builder,center,radii,material,label,segments=14,rings=9):
    cx,cy,cz=center;rx,ry,rz=radii;verts=[(cx,cy,cz-rz)];faces=[]
    for r in range(1,rings):
        theta=pi*r/rings-pi/2
        for s in range(segments):
            a=2*pi*s/segments;verts.append((cx+rx*cos(a)*cos(theta),cy+ry*sin(a)*cos(theta),cz+rz*sin(theta)))
    top=len(verts);verts.append((cx,cy,cz+rz))
    for s in range(segments):
        other=(s+1)%segments
        faces.append((0,1+other,1+s))
        for r in range(rings-2):
            k=1+r*segments;faces.append((k+s,k+other,k+segments+other,k+segments+s))
        k=1+(rings-2)*segments;faces.append((k+s,k+other,top))
    builder.add(verts,faces,material,label)


def brickwork(f,extent,height=4.84):
    us=extent.bounds;lines=[]
    for row in range(16):
        z=1.42+row*.214
        if z>height:break
        lines.append(box(us[0],z-.008,us[2],z+.008))
        first=us[0]+(.22 if row%2 else .45)
        while first<us[2]:
            lines.append(box(first-.009,z,first+.009,z+.214));first+=.47
    f.prism(unary_union(lines).intersection(extent),.001,.009,JOINT,'running brick joints')


def gate_rooms(b,low):
    for s in [-1,1]:
        lo,hi=sorted((s*X_WALL,s*X_PORTAL));mid=(lo+hi)/2;w=hi-lo
        cube(b,(mid,(Y_FRONT+Y_BACK)/2,.092),(w+.09,Y_BACK-Y_FRONT+.12,.184),PLINTH,'Wings/stone footing')
        cube(b,(mid,(Y_FRONT+Y_BACK)/2,2.55),(w,Y_BACK-Y_FRONT-.38,4.88),BRICK,'Wings/masonry rooms')
        cube(b,(mid,(Y_FRONT+Y_BACK)/2,.72),(w+.02,Y_BACK-Y_FRONT+.01,1.31),PLINTH,'Wings/grey plinth')
        for front in [True,False]:
            y=Y_FRONT if front else Y_BACK
            f=Facade(b,(lo,y),(hi,y),'East red masonry') if front else Facade(b,(hi,y),(lo,y),'Campus windows')
            if front:
                f.box(0,3.10,w,3.48,.25,-.105,BRICK,'red upper wall')
                if not low:brickwork(f,box(-w/2,1.38,w/2,4.82))
            else:
                f.box(0,3.08,w,3.46,.22,-.103,POST,'red timber surround')
                window=box(-w*.412,1.55,w*.412,4.19)
                f.prism(window,.008,.028,GLASS,'smoky panes')
                bars=[window.difference(window.buffer(-.12,join_style='mitre'))]
                for col in range(1,4):
                    u=window.bounds[0]+(window.bounds[2]-window.bounds[0])*col/4
                    bars.append(box(u-.057,1.55,u+.057,4.19))
                bars.append(box(-w/2,3.40,w/2,3.50));f.prism(window.intersection(unary_union(bars)),.042,.121,DOOR,'muntins and transom')
            f.box(0,4.92,w,.188,.29,.012,GOLD,'yellow ochre cornice')
        for x in [lo+.09,hi-.09]:
            for y in [Y_FRONT-.014,Y_BACK+.014]:
                if abs(abs(x)-X_PORTAL)<.15 or y>Y_BACK:
                    b.lathe((x,y),[(.11,.235),(.24,.245),(.30,.205),(4.96,.191),(5.25,.22)],POST,12 if low else 20,'Wings/vermilion columns')
    # A narrow closed panel on either side and the two central leaves swung into the tunnel.
    for s in [-1,1]:
        x=s*2.075
        cube(b,(x,4.79,2.11),(1.61,.125,4.20),DOOR,'Doors/fixed side leaves')
        cube(b,(s*1.237,5.64,2.10),(.14,1.62,4.16),DOOR,'Doors/open central leaves')
        f=Facade(b,(x-.805,4.725),(x+.805,4.725),'Doors/panel and studs')
        for z in [.72,2.32,3.56]:
            edge=box(-.69,z-.43,.69,z+.43);f.prism(edge.difference(edge.buffer(-.029,join_style='mitre')),.002,.019,GOLD,'thin painted border')
        for z in [i*.385+.39 for i in range(10)]:
            for y in [4.99,5.38,5.77,6.16]:
                ellipsoid(b,(s*1.163,y,z),(.040,.052,.052),GOLD,'Doors/open leaf brass bosses',8,5)
    cube(b,(0,(Y_FRONT+Y_BACK)/2,4.94),(2*X_PORTAL,Y_BACK-Y_FRONT,1.03),DOOR,'Passage/ceiling')
    for y in [2.67,4.24,6.01,7.78,9.42]:
        cube(b,(0,y,4.492),(2*X_PORTAL,.13,.14),WOOD,'Passage/exposed transverse beam')
    f=Facade(b,(-X_WALL,Y_FRONT),(X_WALL,Y_FRONT),'East inscription')
    f.box(3.62,2.99,.55,2.58,.079,.06,WHITE,'white vertical plaque')
    for i,ch in enumerate('交通大学'):
        add_facade_lettering(f,ch,3.62,3.86-i*.55,.404,.432,.103,.119,BLACK,label='Vertical plaque '+str(i),font=FONT)
    for x in [-1.73,-.57,.57,1.73]:
        b.tube([(x,2.42,4.95),(x,2.42,4.53)],.022,GOLD,8,'Passage/lantern hanger')
        ellipsoid(b,(x,2.42,4.35),(.30,.29,.23),POST,'Passage/red lantern',12 if low else 20,8)
        cube(b,(x,2.42,4.06),(.034,.035,.18),GOLD,'Passage/lantern tassel')


def decorated_beams(b,low):
    for front in [True,False]:
        y=Y_FRONT-.067 if front else Y_BACK+.067
        f=Facade(b,(-7.43,y),(7.43,y),'East painted beam') if front else Facade(b,(7.43,y),(-7.43,y),'Campus painted beam')
        f.box(0,5.35,15.07,.72,.40,.055,BLUE,'main beam')
        for z in [5.04,5.68]:
            f.box(0,z,15.12,.055,.425,.066,GOLD,'ochre lining')
        for lo,hi in [(-7.36,-3.02),(-2.84,2.84),(3.02,7.36)]:
            for z in [5.21,5.52]:
                mid=(lo+hi)/2
                main=box(lo+.28,z-.095,hi-.28,z+.095)
                f.prism(main,.254,.272,PAINT,'inset painted panel')
                for x in [lo+.23,hi-.23,mid]:
                    diamond=Polygon([(x-.16,z),(x,z-.14),(x+.16,z),(x,z+.14)])
                    f.prism(diamond,.275,.286,GOLD,'geometric lozenge')
                    if not low:
                        f.prism(diamond.buffer(-.055,join_style='mitre'),.286,.297,POST,'red lozenge centre')
            if not low:
                for x in [lo+.66,hi-.66]:
                    ring=Point(x,5.36).buffer(.148,quad_segs=9)
                    f.prism(ring.difference(ring.buffer(-.042)),.276,.289,WHITE,'painted rosette')
                    for t in range(6):
                        a=t*pi/3
                        f.prism(Point(x+.132*cos(a),5.36+.132*sin(a)).buffer(.027,quad_segs=4),.289,.302,BLACK,'petal dots')
        for x in [-2.51,2.51]:
            extent=Polygon([(x-.4,5.04),(x+.42,5.04),(x+.32,4.81),(x+.1,4.71),(x-.19,4.75),(x-.39,4.86)])
            f.prism(extent,.12,.25,GOLD,'carved bracket below the beam')
        for x in [i*.47 for i in range(-15,16)]:
            f.box(x,5.75,.18,.20,.76,.20,WOOD,'exposed rafter end')
    for s in [-1,1]:
        cube(b,(s*7.12,Y_MID,5.52),(.28,9.10,.50),WOOD,'Returns/longitudinal beam')


def roof_point(side,t,u):
    """Curved hip slopes from lifted eave corners to the straight central ridge."""
    width=EAVE_X+(RIDGE_X-EAVE_X)*t
    half_depth=EAVE_Y*(1-t)
    if side in ('east','west'):
        x=width*u;y=Y_MID+(-1 if side=='east' else 1)*half_depth;corner=abs(u)
    else:
        x=(-1 if side=='south' else 1)*width;y=Y_MID+u*half_depth;corner=abs(u)
    z=5.71+1.31*t+.93*t*t+.42*(1-t)**2*corner**4
    return (x,y,z)


def roof(b,low):
    for side in ('east','west','south','north'):
        long=side in ('east','west');n=64 if long else 40; m=6 if low else 10
        rows=[];faces=[]
        for j in range(m+1):
            t=j/m
            for i in range(n+1):rows.append(roof_point(side,t,2*i/n-1))
        for j in range(m):
            for i in range(n):
                a=j*(n+1)+i;faces.append((a,a+1,a+n+2,a+n+1))
        if side in ('west','south'):faces=[tuple(reversed(f)) for f in faces]
        b.add(rows,faces,ROOF,'Roof/'+side+' glazed slope')
        # Each raised cover tile ends at the physical ridge or hip line.
        count=(49 if low else 79) if long else (27 if low else 45)
        for i in range(count):
            u=2*(i+.5)/count-1
            path=[]
            for j in range(m+1):
                x,y,z=roof_point(side,j/m,u);path.append((x,y,z+.048))
            b.tube(path,.048 if low else .052,TILE,6 if low else 8,'Roof/'+side+' raised tile rows')
        edge=[roof_point(side,0,i/24-1)for i in range(49)]
        b.tube([(x,y,z+.012)for x,y,z in edge],.076,ROOF,8,'Roof/'+side+' eave border')
        if not low:
            for i in range(1,count,2):
                x,y,z=roof_point(side,0,2*(i+.5)/count-1)
                ellipsoid(b,(x,y,z-.058),(.071,.077,.091),TILE,'Roof/'+side+' pendant tile ends',8,5)
    for s in [-1,1]:
        for face in ['east','west']:
            p=[roof_point(face,t/10,s)for t in range(11)]
            b.tube([(x,y,z+.13)for x,y,z in p],.121,ROOF,10,'Roof/rising hip ridges')
            for j in range(5):
                t=.075+j*.056;x,y,z=roof_point(face,t,s)
                ellipsoid(b,(x,y,z+.285),(.08,.093,.125),ROOF,'Roof/five ridge beasts',8,5)
                ellipsoid(b,(x+.052*s,y+(-.055 if face=='east' else .055),z+.405),(.054,.061,.074),TILE,'Roof/upturned beast heads',8,5)
    cube(b,(0,Y_MID,8.015),(RIDGE_X*2+.31,.35,.19),ROOF,'Roof/main glazed ridge')
    for s in [-1,1]:
        x=s*RIDGE_X
        # Curling ceramic ridge terminals seen against the sky in both 2010 and 2017.
        f=Facade(b,(x-1,Y_MID-.105),(x+1,Y_MID-.105),'Roof/dragon ridge terminal')
        pts=[(-.53,8.03),(-.53,8.27),(-.36,8.36),(-.3,8.62),(-.16,8.64),(-.16,8.38),(.08,8.42),
             (.24,8.52),(.14,8.70),(.22,8.86),(.42,8.91),(.58,8.79),(.56,8.52),(.42,8.27),(.41,8.03)]
        head=Polygon([(s*u,z) for u,z in pts]);f.prism(head,-.22,.07,ROOF,'curled silhouette')
        path=[(x+s*u,Y_MID-.183,z)for u,z in [(-.30,8.19),(-.18,8.22),(-.10,8.30),(.01,8.25),(.16,8.21),(.27,8.30),(.31,8.45)]]
        b.tube(path,.031,GOLD,8,'Roof/gilt scroll')


def guardian(b,s,low):
    """A seated stone lion with paired paws, spiral mane, open jaw and carved pedestal."""
    x=4.97*s;y=-1.12;name='Northern guardian' if s>0 else 'Southern guardian'
    def stone(center,size,material,part):
        cx,cy,cz=center;ellipsoid(b,(x+cx,y+cy,cz),size,material,name+'/'+part,12 if low else 18,7 if low else 11)
    for z,w,h,d in [(.075,1.23,.15,1.41),(.45,1.13,.63,1.29),(.82,1.23,.14,1.38),(.94,1.19,.10,1.34)]:
        cube(b,(x,y,z),(w,d,h),STONE,name+'/stepped pedestal')
    f=Facade(b,(x-.55,y-.65),(x+.55,y-.65),name+'/carved apron')
    apron=Polygon([(-.46,.70),(.46,.70),(0,.28)])
    f.prism(apron,.009,.047,STONE,'triangular shield')
    f.prism(apron.buffer(-.078).difference(apron.buffer(-.101)),.050,.061,CARVE,'carved border')
    stone((0,.12,1.37),(.47,.54,.43),STONE,'seated haunches');stone((0,.02,1.65),(.40,.41,.52),STONE,'body')
    stone((0,-.16,1.91),(.39,.38,.49),STONE,'chest')
    for a in [-1,1]:
        stone((a*.28,-.29,1.48),(.13,.15,.47),STONE,'straight forelegs')
        stone((a*.27,-.40,1.10),(.171,.196,.12),STONE,'forward paws')
        for j in [-1,0,1]:stone((a*.27+j*.06,-.55,1.084),(.042,.070,.051),STONE,'claws')
        stone((a*.36,.24,1.32),(.21,.31,.25),STONE,'coiled rear legs')
    stone((-.26*s,-.47,1.124),(.184,.18,.151),STONE,'carved foot ornament')
    stone((.23*s,.37,1.54),(.158,.166,.24),STONE,'raised tail')
    stone((0,-.19,2.34),(.39,.34,.38),STONE,'head')
    for k in range(12 if low else 18):
        a=2*pi*k/(12 if low else 18);cx=.344*cos(a);cz=2.34+.32*sin(a)
        stone((cx,-.205,cz),(.121,.132,.127),STONE,'ringed mane curls')
        if not low:
            cx2=.306*cos(a);cz2=2.34+.293*sin(a)
            stone((cx2,-.319,cz2),(.056,.046,.055),STONE,'carved curl centres')
    for a in [-1,1]:
        stone((a*.20,-.456,2.405),(.134,.093,.096),STONE,'brows')
        stone((a*.185,-.519,2.38),(.069,.032,.042),CARVE,'eyes')
        stone((a*.16,-.467,2.18),(.136,.14,.109),STONE,'muzzle')
        stone((a*.107,-.528,2.115),(.041,.043,.064),STONE,'fangs')
    stone((0,-.450,2.065),(.176,.146,.069),CARVE,'open mouth')
    stone((0,-.436,1.99),(.184,.135,.079),STONE,'lower jaw')
    stone((0,-.528,2.238),(.124,.081,.07),STONE,'nose')
    stone((0,-.502,1.81),(.10,.055,.13),STONE,'chest bell')


def make_gate(builder,low=False):
    gate_rooms(builder,low);decorated_beams(builder,low);roof(builder,low)
    for side in [-1,1]:guardian(builder,side,low)
