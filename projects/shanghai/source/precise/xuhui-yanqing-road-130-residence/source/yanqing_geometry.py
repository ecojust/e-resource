"""Garden elevation of the 1928 house. The local south edge faces the courtyard."""
from math import cos, sin, pi, sqrt
from shapely.geometry import Polygon, LineString, box
from photo_architecture import Facade, opening

WALL = 'warm ivory render'
STONE = 'pale carved stone'
TRIM = 'limestone stringcourse'
DARK = 'blue grey timber frame'
GLASS = 'shadowed glazed opening'
ROOF = 'weathered French red tile'
RIB = 'fired clay tile joints'
DECK = 'terracotta terrace paving'
HALL = 'deep grey glazed garden hall'
PANEL = 'recessed lime panel'
PALETTE = {name: {'color': rgb, 'roughness': rough} for name,rgb,rough in (
    (WALL,[.80,.79,.69],.92),(STONE,[.82,.80,.70],.87),(TRIM,[.66,.65,.57],.9),
    (HALL,[.074,.115,.111],.32),(DARK,[.20,.26,.25],.70),(GLASS,[.22,.30,.31],.34),(ROOF,[.47,.197,.112],.90),
    (RIB,[.36,.14,.087],.84),(DECK,[.48,.27,.19],.91),(PANEL,[.72,.71,.62],.92))}

GROUND = [(-7.42,1.12),(-6.93,-.48),(-3.82,-.77),(-.12,-1.41),
          (3.55,-1.12),(6.65,-.48),(7.51,.73)]
UPPER = [(-7.42,1.34),(-6.30,.35),(-4.15,.35),(-3.23,1.17),
         (-3.23,2.52),(3.15,2.52),(3.15,1.18),(4.08,.34),
         (6.31,.34),(7.51,1.32)]
BACK = 7.5


def footprint(front):
    return Polygon([*front,(7.96,BACK),(-7.59,BACK)])


def caps(builder, poly, z, depth, mat, name):
    builder.plan_prism(poly,z,z+depth,mat,name)


def cornice(builder,path,z,projection,height,material,name):
    strip=LineString(path).buffer(projection,cap_style='square',join_style='mitre')
    caps(builder,strip,z,height,material,name)


def opening_window(f,z,width,height,columns,lod,arch=0,material=GLASS):
    hole=opening(0,z,width,height,arch,8 if lod else 18)
    f.prism(hole.buffer(.012,join_style='mitre'),-.31,-.285,material,'window glass')
    inside=hole.buffer(-.08,join_style='mitre')
    cuts=[]
    for j in range(1,columns):
        x=width*(j/columns-.5)
        cuts.append(box(x-.037,z,x+.037,z+height+.1))
    transom=z+height*.72
    cuts.append(box(-width/2,transom-.034,width/2,transom+.034))
    from shapely.ops import unary_union
    f.prism(hole.difference(inside.difference(unary_union(cuts))),-.265,-.16,DARK,'painted sashes')
    return hole



def ashlar(f, bottom, top, holes, spacing):
    """Incised horizontal lines stop outside the actual openings and their raised moulding."""
    from shapely.ops import unary_union
    limit=box(-f.length/2+.015,bottom,f.length/2-.015,top)
    if holes:
        limit=limit.difference(unary_union(holes).buffer(.14,join_style='mitre'))
    course=bottom+spacing
    while course<top:
        stroke=limit.intersection(box(-f.length/2,course-.013,f.length/2,course+.013))
        if not stroke.is_empty:
            f.prism(stroke,.008,.021,TRIM,'shallow ashlar course')
        course+=spacing


def upper_window_trim(f, hole):
    """The 2023 close view shows a flat-arched surround below the human-head keystone."""
    outer=hole.buffer(.12,join_style='mitre')
    f.prism(outer.difference(hole.buffer(.015,join_style='mitre')),.015,.086,STONE,'raised window casing')
    left,bottom,right,top=hole.bounds
    f.box((left+right)/2,top+.17,right-left+.52,.105,.20,.055,TRIM,'upper window lintel')

def closed_returns(builder,front,lo,hi):
    """One unfenestrated solid along each unphotographed side and rear stop."""
    core=footprint(front)
    outer=LineString([front[-1],(7.96,BACK),(-7.59,BACK),front[0]])
    wall=outer.buffer(.17,join_style='mitre',cap_style='flat').intersection(core)
    caps(builder,wall,lo,hi-lo,WALL,'plain side and rear closure')


def ball(builder,centre,radii,material,label,lod):
    nx,ny=(8,5)if lod else(16,9)
    x,y,z=centre;rx,ry,rz=radii
    v=[(x,y,z-rz)]
    for j in range(1,ny):
        h=pi*j/ny-pi/2
        for i in range(nx):
            a=2*pi*i/nx
            v.append((x+rx*cos(h)*cos(a),y+ry*cos(h)*sin(a),z+rz*sin(h)))
    top=len(v);v.append((x,y,z+rz))
    fs=[(0,1+(i+1)%nx,1+i)for i in range(nx)]
    for j in range(ny-2):
        a=1+j*nx
        fs +=[(a+i,a+(i+1)%nx,a+nx+(i+1)%nx,a+nx+i)for i in range(nx)]
    fs +=[(top,top-nx+i,top-nx+(i+1)%nx)for i in range(nx)]
    builder.add(v,fs,material,label)


def planter(builder,x,y,z,lod):
    profile=[(z,.19),(z+.06,.23),(z+.12,.16),(z+.20,.12),
             (z+.27,.21),(z+.40,.40),(z+.47,.46),(z+.51,.46)]
    builder.lathe((x,y),profile,STONE,12 if lod else 24,'shallow stone urn')
    builder.lathe((x,y),[(z+.51,.39),(z+.519,.39)],PANEL,12 if lod else 24,'urn rim inset')


def baluster(builder,x,y,z,lod):
    levels=[(.0,.105),(.10,.115),(.24,.066),(.37,.113),(.45,.105),(.56,.062),(.66,.11),(.71,.11)]
    builder.lathe((x,y),[(z+h,r)for h,r in levels],STONE,8 if lod else 14,'balustrade turned spindle')


def garden_railing(builder,front,lod):
    for i,(a,b) in enumerate(zip(front,front[1:])):
        wall=Facade(builder,a,b,'terrace outer parapet')
        w=wall.length
        wall.box(0,5.01,w,.80,.28,-.05,WALL,'low solid parapet')
        if w>2.5:
            outer=box(-w*.36,4.8,w*.36,5.20)
            wall.prism(outer,-.005,.105,TRIM,'recessed rectangular border')
            wall.prism(outer.buffer(-.07,join_style='mitre'),.105,.117,PANEL,'inset field')
            if not lod:
                pts=[wall.point(-w*.27,5.11,.139),wall.point(-w*.13,5.00,.139),wall.point(0,4.99,.139),
                     wall.point(w*.12,5.04,.139),wall.point(w*.25,5.12,.139)]
                builder.tube(pts,.026,STONE,7,'shallow garland')
    cornice(builder,front,5.40,.18,.105,STONE,'parapet coping')
    for x,y in front[1:-1]:
        builder.box((x,y,5.02),(.44,.43,.95),STONE,label='square urn pedestal')
        builder.box((x,y,5.52),(.55,.52,.13),STONE,label='projecting pedestal top')
    for i in (1,2,4,5):
        x,y=front[i];planter(builder,x,y,5.585,lod)


def face_key(builder,x,y,z,lod):
    f=Facade(builder,(x-.58,y),(x+.58,y),'architrave central stone')
    f.prism(Polygon([(-.32,z-.36),(.32,z-.36),(.46,z+.32),(-.46,z+.32)]),0,.16,STONE,'tapering keystone')
    ball(builder,(x,y-.18,z),(.165,.070,.210),TRIM,'key portrait silhouette',lod)
    if not lod:
        for h,r in ((.088,.048),(-.032,.035)):
            ball(builder,(x,y-.24,z+h),(r,.028,r),STONE,'forehead and nose',False)
        for side in (-1,1):
            ball(builder,(x+side*.071,y-.237,z+.055),(.06,.019,.022),STONE,'carved brow',False)
        ball(builder,(x,y-.215,z-.124),(.075,.038,.043),STONE,'carved chin',False)


def crown(builder,x,lod):
    y=.24;f=Facade(builder,(x-1.83,y),(x+1.83,y),'arched upper garden window')
    z=10.14
    hole=opening_window(f,z+.65,2.63,1.37,3,lod,.27)
    f.wall(10.1,12.52,[hole],thickness=.36,material=WALL)
    for sx in (-1,1):
        f.box(sx*1.54,11.23,.34,1.88,.45,.04,STONE,'short pediment pier')
        f.box(sx*1.54,12.14,.55,.15,.52,.07,TRIM,'pier capital')
    w=1.86
    def arc(u):return 12.16+1.03*(1-(u/w)**2)
    n=16 if lod else 32
    xs=[-w+2*w*j/n for j in range(n+1)]
    shell=Polygon([(-w,12.15),(w,12.15),*[(u,arc(u))for u in xs[-2:0:-1]]])
    f.prism(shell,-.29,.135,WALL,'segmental tympanum')
    for lift,r,mat in ((.0,.108,STONE),(.14,.07,TRIM)):
        builder.tube([f.point(u,arc(u)+lift,.20)for u in xs],r,mat,8 if lod else 12,'double curved moulding')
    for sx in (-1,1):
        if not lod:
            for du,h,scale_factor in ((.55,12.66,1.0),(.86,12.58,.73)):
                leaf=Polygon([(sx*(du-.11*scale_factor),h-.095),(sx*(du+.07*scale_factor),h-.02),
                              (sx*(du+.16*scale_factor),h+.15),(sx*(du-.05*scale_factor),h+.093)])
                f.prism(leaf,.139,.182,STONE,'shallow tympanum leaf')
        pts=[f.point(sx*pt,h,.164)for pt,h in ((.14,12.47),(.36,12.49),(.50,12.65),(.73,12.72),(1.02,12.57),(1.25,12.39))]
        builder.tube(pts,.045 if lod else .058,STONE,8,'paired pediment scroll')
    f.prism(Polygon([(-.15,12.38),(.15,12.38),(.21,12.95),(-.21,12.95)]),.141,.23,STONE,'pediment keystone')
    rail=[(x-1.78,.54),(x-1.49,-.19),(x+1.48,-.19),(x+1.80,.54)]
    shelf=Polygon([*rail,(x+1.70,1.10),(x-1.70,1.10)])
    caps(builder,shelf,9.37,.18,TRIM,'crowned bay balcony base')
    cornice(builder,rail,9.52,.105,.12,STONE,'pierced balcony footing')
    cornice(builder,rail,10.34,.14,.145,STONE,'balcony handrail')
    for i,(a,b) in enumerate(zip(rail,rail[1:])):
        count=8 if i==1 else 2
        for j in range(count):
            t=(j+.5)/count;baluster(builder,a[0]*(1-t)+b[0]*t,a[1]*(1-t)+b[1]*t,9.63,lod)
    for a,b in (rail[0],rail[-1]):
        builder.box((a,b,9.98),(.32,.32,.91),STONE,label='balcony end pier')


def add_building(builder,lod=False):
    closed_returns(builder,GROUND,.05,4.42)
    ground_poly=footprint(GROUND)
    caps(builder,ground_poly,.035,.18,TRIM,'ground footprint')
    for i,(a,b)in enumerate(zip(GROUND,GROUND[1:])):
        outer=Facade(builder,a,b,'bowed lower hall')
        recess=.90 if i in (2,3) else .26 if i==4 else 0.
        ax,ay=outer.point(-outer.length/2,0,-recess)[:2]
        bx,by=outer.point(outer.length/2,0,-recess)[:2]
        f=Facade(builder,(ax,ay),(bx,by),'recessed garden glazing')
        holes=[]
        if f.length>2.85:
            h=opening_window(f,.52,min(2.81,f.length-.49),3.42,3 if i not in (1,4) else 2,lod,material=HALL)
            holes.append(h)
            f.wall(.15,4.42,holes,thickness=.38,material=WALL)
            if i==1:
                f.box(0,.91,2.40,.72,.09,-.18,DARK,'garden double door lower panel')
                f.box(0,1.17,2.32,.07,.11,-.115,TRIM,'door lower rail')
        else:f.wall(.15,4.42,thickness=.36,material=WALL)
        ashlar(f,.22,4.10,holes,.43 if not lod else .86)
        if recess>0.:
            outer.box(0,4.16,outer.length+.09,.25,.51,-.14,STONE,'projecting terrace architrave')
    # The pair of full-height round columns stands in front of the dark glazed hall.
    # A square rusticated end pilaster carries each outer bay.
    for x,y in GROUND[2:5]:
        builder.lathe((x,y-.14),[(.13,.30),(.22,.31),(.32,.35),(.41,.30),(.49,.24),
                              (3.76,.22),(3.85,.26),(3.91,.24),(4.00,.31),(4.08,.35),(4.19,.38)],
                      STONE,16 if lod else 28,'freestanding courtyard column')
        builder.box((x,y-.13,4.19),(.81,.71,.15),TRIM,label='column square abacus')
    entry=Facade(builder,GROUND[1],GROUND[2],'garden steps')
    for i in range(4):
        depth=1.39-i*.29
        pts=[entry.point(u,0,d)[:2]for u,d in [
            (-1.41,-.05),(-1.54,depth*.43),(-1.47,depth*.70),(-1.25,depth*.88),(-.82,depth*.98),
            (0,depth),(.82,depth*.98),(1.25,depth*.88),(1.47,depth*.70),(1.54,depth*.43),(1.41,-.05)]]
        caps(builder,Polygon(pts),i*.126+.012,.129,STONE,'rounded entry step')
    caps(builder,ground_poly.buffer(.14,join_style='mitre'),4.28,.23,TRIM,'hall terrace rim')
    caps(builder,ground_poly,4.51,.07,DECK,'terrace tile surface')
    garden_railing(builder,GROUND,lod)
    for i,(a,b)in enumerate(zip(UPPER,UPPER[1:])):
        f=Facade(builder,a,b,'receding garden rooms')
        holes=[]
        if i in (1,7):
            hole=opening_window(f,5.45,1.72,2.73,2,lod);f.wall(4.58,9.44,[hole],thickness=.36,material=WALL)
            holes.append(hole);upper_window_trim(f,hole)
            face_key(builder,(a[0]+b[0])/2,(a[1]+b[1])/2-.02,8.58,lod)
        elif i==4:
            holes=[]
            for x in (-1.85,0,1.85):
                h=opening(x,5.45,1.4,2.52,0);f.prism(h,-.30,-.27,GLASS,'recessed central opening')
                f.box(x,6.69,.06,2.46,.07,-.22,DARK,'central window mullion');holes.append(h)
            f.wall(4.58,9.44,holes,thickness=.34,material=WALL);face_key(builder,0,a[1]-.02,8.55,lod)
        else:f.wall(4.58,9.44,thickness=.32,material=WALL)
        ashlar(f,4.61,9.25,holes,.45 if not lod else .90)
    closed_returns(builder,UPPER,4.58,9.49)
    cornice(builder,UPPER,9.29,.16,.16,TRIM,'bow and return cornice')
    upper=footprint(UPPER);caps(builder,upper,9.43,.17,DECK,'upper garden setback')
    for x in (-5.25,5.17):crown(builder,x,lod)
    # The two end pediments and an open terrace stand in front of a single shed dormer.
    dormer=Facade(builder,(-3.45,2.75),(3.45,2.75),'central shed dormer')
    hs=[]
    for u in (-2.18,-.74,.74,2.18):
        h=opening(u,10.46,1.22,1.24,.10,10);hs.append(h);dormer.prism(h,-.25,-.22,GLASS,'dormer glazing')
        dormer.box(u,11.0,.05,1.20,.05,-.19,DARK,'dormer sash')
    dormer.wall(9.60,11.92,hs,thickness=.32,material=WALL)
    dormer.box(0,11.99,7.22,.14,1.43,-.38,ROOF,'shed dormer eave')
    middle=[(-3.31,1.41),(-1.65,1.18),(1.65,1.18),(3.23,1.40)]
    cornice(builder,middle,9.66,.12,.72,WALL,'upper terrace central solid wall')
    cornice(builder,middle,10.38,.15,.12,STONE,'upper terrace cap')
    for x in (-2.85,2.85):planter(builder,x,1.35,10.51,lod)
    # South mansard half terminates at the surveyed rear seam. Farther roof surfaces retain the original city mesh.
    def height(y):return 10.64+(y-1.86)*.98 if y<4.0 else 12.737+(y-4.0)*.39
    x0,x1=-7.49,7.78
    for xa,xb,start_y in [(x0,-3.50,1.86),(-3.50,3.50,4.22),(3.50,x1,1.86)]:
        segments=[(start_y,4.0),(4.0,BACK)] if start_y<4 else [(start_y,BACK)]
        for left,right in segments:
            z0,z1=height(left),height(right)
            profile=Polygon([(left,z0-.18),(right,z1-.18),(right,z1),(left,z0)])
            builder.prism(profile,xa,xb,lambda y,z,x:(x,y,z),ROOF,'red tiled mansard slope')
            count=5 if lod else 9
            for j in range(1,count):
                y=left+(right-left)*j/count
                builder.tube([(xa,y,height(y)+.018),(xb,y,height(y)+.018)],.017,RIB,5,'horizontal tile courses')
                if not lod:
                    for k in range(22):
                        xx=xa+.25+(k+(j%2)*.47)*.72;yy=y+(right-left)*.87/count
                        if xx<xb:builder.tube([(xx,y,height(y)+.020),(xx,yy,height(yy)+.020)],.013,ROOF,5,'staggered tile ends')
    shed=Polygon([(2.44,11.87),(4.24,height(4.24)-.13),(4.24,height(4.24)),(2.44,12.00)])
    builder.prism(shed,-3.53,3.53,lambda y,z,x:(x,y,z),ROOF,'dormer fall to window head')
    for x in (x0,x1):
        gable=Polygon([(1.86,9.54),(BACK,9.54),(BACK,height(BACK)-.18),(4,height(4)-.18),(1.86,height(1.86)-.18)])
        builder.prism(gable,x-.02,x+.02,lambda y,z,v:(v,y,z),WALL,'plain capped roof return')
