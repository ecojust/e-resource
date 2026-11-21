"""The projecting stone entrance on Anfu Road, from the two documented elevations."""
from math import cos, sin, pi, sqrt
from shapely.geometry import Polygon, LineString, Point, box
from photo_architecture import Facade

STONE = 'Grey washed aggregate'
TRIM = 'Raised cement mouldings'
SHADOW = 'Dark mineral incisions'
PALE = 'Weathered capstone'
IRON = 'Dark metal door and fanlight'
GLASS = 'Grey-green fanlight glazing'
LOW_GLASS = 'Dark door glazing'
GREEN = 'Green house number'
WHITE = 'Pale house number'
FLOOR = 'Grey threshold slab'
PALETTE = {key:dict(color=c,roughness=r) for key,c,r in [
    (STONE,[.53,.51,.475],.92),(TRIM,[.615,.59,.527],.86),
    (SHADOW,[.370,.361,.331],.93),(PALE,[.653,.632,.581],.85),
    (IRON,[.093,.095,.087],.60),(GLASS,[.211,.256,.239],.35),
    (LOW_GLASS,[.140,.156,.153],.40),(GREEN,[.086,.332,.222],.75),
    (WHITE,[.905,.886,.757],.80),(FLOOR,[.504,.495,.465],.91)]}
WIDTH = 4.38
DEPTH = 1.11
# The two dated street stations give 3.007 m between capital centres.
METRES_PER_STUDY_UNIT = .860
SPRING = 2.10
RADIUS = 1.18
RISE = 1.025
EAVE = 4.10
DECK = 4.47
RAIL_HEAD = 5.22

def halfdisc(radius, spring, segments):
    return [(radius*cos(pi*i/segments), spring+radius*RISE/RADIUS*sin(pi*i/segments))
            for i in range(segments+1)]

def block(b,label,m,x0,x1,y0,y1,z0,z1):
    b.box(((x1+x0)*.5,(y1+y0)*.5,(z1+z0)*.5),
          (x1-x0,y1-y0,z1-z0),m,label=label)

def line(f,coords,width,back,front,mat,name):
    f.prism(LineString(coords).buffer(width/2,cap_style='round',join_style='round',
                                      quad_segs=4),back,front,mat,name)

def opening(f,n):
    arch=Polygon([(-RADIUS,.054),(RADIUS,.054),*halfdisc(RADIUS,SPRING,n)])
    f.wall(0,EAVE,holes=[arch],thickness=.37,material=STONE)
    f.prism(arch.buffer(.008),-.405,-.385,IRON,'Doorway dark lining behind frame')
    f.prism(arch.buffer(-.047),-.322,-.301,LOW_GLASS,'Dark glazing below transom')
    fan=Polygon(halfdisc(RADIUS-.049,SPRING,n))
    f.prism(fan,-.301,-.284,GLASS,'Set-back half round fanlight')
    f.prism(arch.difference(arch.buffer(-.059)), -.328,-.238,IRON,'Continuous jamb and fanlight rim')
    leaf_width=(2*RADIUS-.10)/2
    for x in (-leaf_width/2,leaf_width/2):
        leaf=box(x-leaf_width/2+.008,.082,x+leaf_width/2-.008,SPRING-.028)
        f.prism(leaf.difference(leaf.buffer(-.042,join_style=2)), -.29,-.244,IRON,'Door perimeter')
        for h in (.682,1.17):
            f.box(x,h,leaf_width-.050,.032,.042,-.265,IRON,'Door transverse rail')
    f.box(0,SPRING-.010,2*RADIUS-.04,.069,.101,-.244,IRON,'Door transom')
    # A semicircle inside the fanlight extends out into five radial divisions.
    inner=RADIUS*.54
    line(f,halfdisc(inner,SPRING,n),.027,-.284,-.233,IRON,'Concentric fanlight ring')
    for i in range(1,6):
        ang=i*pi/6
        line(f,[(inner*cos(ang),SPRING+inner*RISE/RADIUS*sin(ang)),((RADIUS-.045)*cos(ang),SPRING+(RADIUS-.045)*RISE/RADIUS*sin(ang))],
             .026,-.284,-.236,IRON,'Radial steel glazing bar')
    line(f,[(0,SPRING),(0,SPRING+inner*RISE/RADIUS)],.027,-.284,-.238,IRON,'Central fanlight division')
    return arch

def stones(f,lod):
    segments=13
    for j in range(1,segments):
        angle=pi*j/segments
        first=RADIUS+.018
        outer=1.595
        line(f,[(first*cos(angle),SPRING+first*RISE/RADIUS*sin(angle)),(outer*cos(angle),SPRING+outer*RISE/RADIUS*sin(angle))],
             .009 if not lod else .012,.001,.004,SHADOW,'Radiating voussoir joint')
    # The shallow dark cuts correspond to the joints between stone-faced blocks.
    for s in (-1,1):
        for h in (.69,1.39,2.10):
            line(f,[(s*(RADIUS+.022),h),(s*2.16,h)],.007,.001,.0035,SHADOW,'Facing bed joint')

def key_scroll(f,lod):
    center=SPRING+RISE
    key=Polygon([(-.148,center+.017),(.148,center+.017),(.225,center+.622),
                 (.177,center+.710),(-.188,center+.710),(-.220,center+.629)])
    f.prism(key,.001,.17,TRIM,'Volute keystone base')
    # Flutes flare upwards and the bottom makes a forward curl under them.
    for i in (-1.5,-.5,.5,1.5):
        run=[(i*.055,center+.065),(i*.061,center+.165),(i*.071,center+.538),(i*.088,center+.632)]
        line(f,run,.034,.168,.202,PALE,'Raised keystone ribs')
    b=f.builder
    profile=[(.018,.040),(.063,.082),(.135,.068),(.184,.039),(.176,-.020),(.112,-.044),(.067,-.025),(.060,.013)]
    shape=Polygon([(d,center+.090+z)for d,z in profile])
    b.prism(shape,-.147,.147,lambda d,z,x:(-x,-.113-d,z),TRIM,'Keystone rolled lower tip')
    for s in (-1,1):
        pts=[(.050+cos(i*.19)*(.042-.00086*i),center+.096+sin(i*.19)*(.042-.00086*i))for i in range(26)]
        seam=LineString(pts).buffer(.004,quad_segs=3)
        # d along the lateral axis is negative-X for the (depth,height) coordinates.
        at=s*.149
        b.prism(seam,at-.002,at+.002,lambda d,z,x:(-x,-.113-d,z),SHADOW,'Keystone volute scroll on end')

def pilaster(f,x,lod):
    # A scalloped plan forms six recessed vertical channels. Shadows move with the view.
    b=f.builder; half=.195; front=-.213;back=.006
    verts=[(x-half,back),(x-half,front)]
    for i in range(6):
        px=x-half+.027+(i+.5)*(.336/6); r=.022
        verts.extend([(px+r*cos(a*pi/(3 if lod else 8)),front+r*sin(a*pi/(3 if lod else 8)))
                      for a in range(3 if lod else 8,-1,-1)])
    verts.extend([(x+half,front),(x+half,back)])
    b.prism(Polygon(verts),.398,2.97,lambda u,y,z:(u,y,z),TRIM,'Six-channel pilaster shaft')
    for lo,hi,wide,projection,mat,name in [
        (.004,.131,.55,.353,STONE,'Square pedestal'),(.131,.304,.499,.294,TRIM,'Raised pedestal'),
        (.304,.372,.538,.333,PALE,'Base collar'),(.372,.413,.449,.240,TRIM,'Base top bed'),
        (2.961,3.023,.453,.256,TRIM,'Upper neck'),(3.023,3.087,.519,.293,PALE,'Lower capital bead'),
        (3.087,3.237,.447,.239,STONE,'Capital recessed neck'),(3.237,3.282,.538,.312,PALE,'Lower projecting ledge'),
        (3.282,3.327,.569,.333,TRIM,'Upper projecting ledge'),(3.327,3.374,.492,.257,STONE,'Capital joint'),
        (3.374,3.814,.444,.241,TRIM,'Medallion panel'),(3.814,3.861,.502,.283,PALE,'Panel cap'),
        (3.861,3.912,.554,.327,TRIM,'Capital top'),(3.912,3.940,.590,.347,PALE,'Thin abacus')]:
        block(b,'Pilaster/'+name,mat,x-wide/2,x+wide/2,-projection,.013,lo,hi)
    disk=Point(x,3.585).buffer(.141,quad_segs=8 if lod else 16)
    f.prism(disk,.240,.261,TRIM,'Circular medallion base')
    f.prism(disk.difference(disk.buffer(-.024)),.259,.276,PALE,'Ring around central boss')
    f.prism(Point(x,3.585).buffer(.043,quad_segs=6 if lod else 12),.259,.299,TRIM,'Medallion button')

def railing(b,lod):
    front=-.18; back=DEPTH; ex=2.06
    # The front comprises two matching runs divided by a square pier.
    for p in [(x,front)for x in (-ex,0,ex)]+[(-ex,back-.18),(ex,back-.18)]:
        x,y=p
        for bottom,top,w,mat in [(DECK,DECK+.064,.42,PALE),(DECK+.064,RAIL_HEAD-.092,.340,STONE),
                                 (RAIL_HEAD-.092,RAIL_HEAD-.049,.383,TRIM),(RAIL_HEAD-.049,RAIL_HEAD+.015,.437,PALE)]:
            block(b,'Terrace square pier',mat,x-w/2,x+w/2,y-w/2,y+w/2,bottom,top)
    for direction in (-1,1):
        x=direction*ex
        points=[(direction*(.26+i*(ex-.52)/6),front)for i in range(7)]
        points.extend((x,front+.30+i*(back-front-.74)/3)for i in range(4))
        for cx,cy in points:
            profile=[(.053,.087),(.089,.096),(.119,.061),(.176,.054),(.251,.103),
                     (.334,.111),(.401,.082),(.477,.044),(.559,.035),(.594,.061),(.620,.085),(.654,.085)]
            if lod:profile=[profile[k]for k in (0,1,3,5,7,8,10,11)]
            b.lathe((cx,cy),[(DECK+z,rr)for z,rr in profile],TRIM,segments=7 if lod else 14,label='Terrace turned balusters')
        # The cap and supporting sill return to the rear brick facade on each side.
        for lo,hi,w in [(DECK+.010,DECK+.070,.235),(RAIL_HEAD-.107,RAIL_HEAD-.052,.214),(RAIL_HEAD-.052,RAIL_HEAD,.256)]:
            block(b,'Side balustrade horizontal rail',TRIM,x-w/2,x+w/2,front,back,lo,hi)
        cx=direction*ex
        finial=[(-.002,.115),(.033,.122),(.061,.074),(.105,.058),(.156,.089),(.228,.104),(.283,.084),(.323,.053),(.338,.001)]
        b.lathe((cx,front),[(RAIL_HEAD+.012+z,r)for z,r in finial],PALE,segments=10 if lod else 24,label='Corner finial')
    for lo,hi,w in [(DECK+.01,DECK+.070,.236),(RAIL_HEAD-.107,RAIL_HEAD-.052,.214),(RAIL_HEAD-.052,RAIL_HEAD,.256)]:
        block(b,'Front balustrade horizontal rail',TRIM,-ex,ex,front-w/2,front+w/2,lo,hi)

def add_building(builder,lod):
    f=Facade(builder,(-WIDTH/2,0),(WIDTH/2,0),'Anfu Road porch')
    opening(f,24 if lod else 56);stones(f,lod);key_scroll(f,lod)
    for side in (-1,1):
        pilaster(f,side*1.74,lod)
        if side<0:
            block(builder,'East side wall',STONE,side*WIDTH/2-.07,side*WIDTH/2+.07,.0,DEPTH,0,EAVE)
        else:
            flank=Facade(builder,(WIDTH/2+.07,0),(WIDTH/2+.07,DEPTH),'West return to main house')
            radius=.147
            narrow=Polygon([(-radius,.686),(radius,.686),*((radius*cos(i*pi/24),2.397+radius*sin(i*pi/24)) for i in range(25))])
            flank.wall(0,EAVE,holes=[narrow],thickness=.148,material=STONE)
            flank.prism(narrow.buffer(.009),-.162,-.150,IRON,'Return arch dark reveal')
            inset=narrow.buffer(-.035)
            flank.prism(inset,-.143,-.124,LOW_GLASS,'Narrow arched side window')
            flank.box(0,1.570,.016,1.75,.032,-.108,IRON,'Side sash meeting stile')
            for height in (1.23,1.84,2.367):
                flank.box(0,height,2*radius-.047,.024,.04,-.106,IRON,'Side sash rail')
    block(builder,'Door threshold',FLOOR,-1.18,1.18,-.40,.387,.001,.054)
    for bottom,top,extended,mat in [(3.940,4.040,.095,STONE),(4.040,4.087,.169,TRIM),(4.087,4.155,.201,SHADOW),
                                   (4.155,4.254,.292,TRIM),(4.254,4.321,.399,PALE),(4.321,4.388,.375,TRIM),
                                   (4.388,DECK,.398,PALE)]:
        block(builder,'Entablature fascia and returns',mat,-WIDTH/2-extended,WIDTH/2+extended,-extended-.07,DEPTH,bottom,top)
    for i in range(48 if not lod else 32):
        x=-WIDTH/2+.08+(WIDTH-.16)*i/(47 if not lod else 31)
        block(builder,'Small entablature dentils',TRIM,x-.020,x+.020,-.166,-.082,3.948,4.008)
    railing(builder,lod)
    # Number plate and rendered digits are lifted from the photographed left jamb.
    p=box(-1.561,2.04,-1.255,2.231)
    f.prism(p,.015,.032,GREEN,'Green 233 enamel number plate')
    f.prism(p.difference(p.buffer(-.009,join_style=2)),.031,.036,WHITE,'Light number plate border')
    glyphs={'2':[(0,.76),(.20,.96),(.76,1),(.98,.78),(.93,.61),(.04,.05),(.99,.05)],
            '3':[(.035,.87),(.23,1),(.79,.98),(.98,.76),(.74,.55),(.39,.52),(.81,.48),(.99,.29),(.86,.07),(.28,0),(0,.14)]}
    for j,c in enumerate('233'):
        seq=[(-1.544+.091*j+.066*u,2.077+.121*v)for u,v in glyphs[c]]
        line(f,seq,.013,.034,.041,WHITE,'Number plate digit '+c)
    # Planar UVs follow each face normal so that the jambs and capital sides
    # retain the same mineral grain as the frontal surfaces.
    from pathlib import Path
    import numpy as np
    builder.palette[STONE]['texture']=str(Path(__file__).with_name('mineral-aggregate.png'))
    for part in builder.parts:
        if part['material']!=STONE:continue
        original=np.array(part['vertices'])
        vertices=[];faces=[];uv=[]
        for triangle in part['triangles']:
            pts=original[list(triangle)]
            a,b,c=pts
            n=np.abs(np.cross(b-a,c-a))
            direction=int(np.argmax(n))
            for x,y,z in pts:
                if direction==0:u,v=(y+.55)/(DEPTH+.76),1.-z/5.9
                elif direction==1:u,v=(x+2.85)/5.7,1.-z/5.9
                else:u,v=(x+2.85)/5.7,(y+.55)/(DEPTH+.76)
                uv.append([u,v])
            faces.append([len(vertices),len(vertices)+1,len(vertices)+2]);vertices.extend(pts.tolist())
        part.update(vertices=vertices,triangles=faces,texcoords=uv)

    for part in builder.parts:
        part['vertices']=[[v*METRES_PER_STUDY_UNIT for v in xyz] for xyz in part['vertices']]
