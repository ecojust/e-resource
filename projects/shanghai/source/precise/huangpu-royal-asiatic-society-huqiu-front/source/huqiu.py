"""The historic Huqiu Road front of the former Royal Asiatic Society museum, Shanghai."""
from math import cos, pi, sin
from pathlib import Path
import sys

from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / 'source/precise/hongkou-general-post-office/source/common'))
from photo_architecture import Facade, opening

BRICK, WARM, PALE = 'buff facing brick', 'ochre facing brick', 'pale brick'
MORTAR = 'buff brick joints'
STONE, EDGE, ROUGH = 'grey ashlar', 'limestone edge', 'grained limestone'
METAL, BRONZE, GLASS = 'dark metal', 'brass window bars', 'blue-grey glass'
DARK, SECTION = 'shadowed doorway', 'cut section'
PALETTE = {key: dict(color=list(rgb), roughness=r, metallic=m) for key,rgb,r,m in [
    (BRICK,(.611,.530,.422),.94,0), (WARM,(.588,.505,.397),.91,0), (PALE,(.639,.556,.449),.92,0), (MORTAR,(.598,.524,.438),.96,0),
    (STONE,(.543,.522,.477),.88,0), (EDGE,(.634,.604,.537),.82,0), (ROUGH,(.474,.431,.358),.92,0),
    (METAL,(.185,.190,.189),.56,.35), (BRONZE,(.516,.396,.251),.54,.48),
    (GLASS,(.289,.348,.373),.32,.13), (DARK,(.128,.125,.118),.97,0), (SECTION,(.475,.434,.373),.94,0)]}

WIDTH = 12.28167895
HALF = WIDTH / 2
SECTION_DEPTH = 2.34
WING_EDGE = 2.69
BASE_TOP = 3.96
WING_TOP = 21.91
CENTER_TOP = 22.87


def stroke(f, coords, width, back, front, material, name):
    poly = LineString(coords).buffer(width / 2, cap_style=2, join_style=2)
    f.prism(poly, back, front, material, name)


def floor_fringe(f, panel, lod):
    if lod:
        return
    xmin,zmin,xmax,zmax = panel.bounds
    for r in range(int((zmax-zmin)/.112)+1):
        z = zmin+r*.112+.004
        joint=LineString([(xmin,z),(xmax,z)]).intersection(panel)
        spans=list(joint.geoms) if hasattr(joint,'geoms') else [joint]
        for span in spans:
            if span.geom_type!='LineString' or span.length<.04:
                continue
            u0,_,u1,_=span.bounds
            v=[f.point(a,b,.004) for a,b in [(u0,z),(u1,z),(u1,z+.007),(u0,z+.007)]]
            f.builder.add(v,[(0,1,2,3)],MORTAR,'horizontal bed joint')
        for c in range(-1,int((xmax-xmin)/.274)+1):
            index = (r*31+c*23+r*c*5)%47
            if index not in (1,3,8,13,17,29):
                continue
            x = xmin+c*.274+(r%2)*.137
            tile = box(x+.004,z,x+.268,z+.105)
            if panel.covers(tile):
                v = [f.point(u,h,.003) for u,h in list(tile.exterior.coords)[:-1]]
                f.builder.add(v,[(0,1,2,3)],PALE if index in (3,17) else WARM,'individual facing brick')


def face(f, panel, holes, lod):
    surface = panel.difference(unary_union(holes)) if holes else panel
    f.prism(surface,-.27,0,BRICK,'brick masonry with through-openings')
    floor_fringe(f,surface,lod)


def glazing(f,x,bottom,top,width,arch,columns,label,lod):
    shell = opening(x,bottom,width,top-bottom,arch,16 if lod else 36)
    f.prism(shell.buffer(.005),-.245,-.230,GLASS,label+' panes')
    frame = [shell.difference(shell.buffer(-.046,join_style=2))]
    for col in range(1,columns):
        xp=x-width/2+width*col/columns
        frame.append(shell.intersection(box(xp-.023,bottom,xp+.023,top)))
    if arch:
        spring=top-arch
        frame.append(shell.intersection(box(x-width/2,spring-.026,x+width/2,spring+.026)))
        for side in (-1,1):
            ray=LineString([(x,spring),(x+side*width*.38,top-.08)]).buffer(.017,cap_style=2)
            frame.append(shell.intersection(ray))
    f.prism(unary_union(frame),-.219,-.166,METAL,label+' sash')
    return shell


def spandrel(f,x,z0,z1,width,center,lod):
    panel=box(x-width/2,z0,x+width/2,z1)
    f.prism(panel,-.20,-.145,METAL,'dark metal spandrel')
    count=(8 if lod else 22) if center else (3 if lod else 8)
    for i in range(count):
        pos=x-width/2+width*(i+.5)/count
        if center and abs(x-pos)<.104:continue
        f.box(pos,(z0+z1)/2,.017,z1-z0-.045,.034,-.132,METAL,'vertical fluting')
    if center:
        for i in range(8 if not lod else 4):
            n=8 if not lod else 4
            h=z0+(i+.5)*(z1-z0)/n
            xy=[(x-.067,h-.075),(x+.045,h-.047),(x+.063,h+.018),(x-.045,h+.055),(x-.058,h+.094)]
            stroke(f,xy,.023,-.147,-.103,ROUGH,'central cast scroll')


def octagon(x,z,r):
    return Polygon([(x+r*cos(pi/8+k*pi/4),z+r*sin(pi/8+k*pi/4))for k in range(8)])


def bagua(f,x,z,lod):
    """Clockwise from top. Each triple is outer, middle, inner as seen in the 2011 detail."""
    r=.501; wheel=octagon(x,z,r)
    f.prism(wheel,-.222,-.209,DARK,'octagonal recess glazing')
    f.prism(wheel.difference(wheel.buffer(-.025,join_style=2)),-.197,-.136,BRONZE,'octagonal outer frame')
    t=.227;ring=Point(x,z).buffer(t,quad_segs=12 if lod else 22)
    f.prism(ring.difference(ring.buffer(-.012)),-.169,-.129,BRONZE,'central circular band')
    # One continuous brass S separates the two lobes. The photograph shows no applied dots.
    curve=[]
    for upper in [False,True]:
        cy=z+(.5 if upper else -.5)*t
        for i in range(1 if upper else 0,13 if lod else 25):
            n=12 if lod else 24
            a=-pi/2+i*pi/n
            curve.append((x+(1 if upper else -1)*t/2*cos(a),cy+t/2*sin(a)))
    stroke(f,curve,.013,-.164,-.120,BRONZE,'curved yin-yang divider')
    tri=['111','011','101','001','000','100','010','110']
    for i,pattern in enumerate(tri):
        a=pi/2-i*pi/4
        def xy(u,v):return (x+u*sin(a)+v*cos(a),z-u*cos(a)+v*sin(a))
        stroke(f,[xy(-.085,.218),xy(-.187,.440)],.011,-.174,-.129,BRONZE,'radial divider')
        for side in (-1,1):
            stroke(f,[xy(side*.055,.223),xy(side*.108,.440)],.009,-.181,-.157,BRONZE,'trigram strut')
        for j,digit in enumerate(pattern):
            radial=.391-j*.047
            length=.130-j*.015
            intervals=[(-length,length)] if digit=='1' else [(-length,-.019),(.019,length)]
            for lo,hi in intervals:
                stroke(f,[xy(lo,radial),xy(hi,radial)],.019,-.151,-.112,BRONZE,'trigram line '+str(i))


def gate(f,x,lod):
    w=1.52; h=3.17;entry=opening(x,.225,w,h-.225,.70,16 if lod else 36)
    f.prism(entry,-1.154,-1.132,DARK,'shadow inside historical entrance')
    # Three graded stone treads visible in the 2010 photograph.
    for j in range(3):
        f.box(x,.044*(j+1),1.54,.088*(j+1),.23,.48-.19*j,STONE,'entrance tread')
    count=9 if lod else 16
    for j in range(count):
        dx=(j/(count-1)-.5)*(w-.12)
        top=1.46+.37*(2*dx/w)**2
        f.box(x+dx,(.23+top)/2,.020,top-.23,.038,-.230,METAL,'curving gate picket')
    for z in [.37,1.42]:
        points=[(x+(j/12-.5)*(w-.10),z+(.36*(2*j/12-1)**2 if z>1 else 0))for j in range(13)]
        stroke(f,points,.028,-.255,-.206,METAL,'gate horizontal rail')


def upper_lights(f,lod):
    holes=[];rows=[(9.09,11.91),(13.57,15.91),(17.74,19.75)]
    for x,w,n in [(-2.03,.53,1),(0,1.52,3),(2.03,.53,1)]:
        roof=19.75 if x==0 else 19.17;arch=.70 if x==0 else 0
        holes.append(opening(x,9.0,w,roof-9.0,arch,16 if lod else 36))
        for lo,hi in rows:
            glazing(f,x,lo,min(roof,hi),w,arch if lo>17 else 0,n,'high window',lod)
        for lo,hi in [(11.91,13.57),(15.91,17.74)]:
            spandrel(f,x,lo,hi,w,x==0,lod)
        low=opening(x,4.46,w,3.50)
        holes.append(low)
        glazing(f,x,4.46,7.96,w,0,n,'balcony door and lights',lod)
    return holes


def parapet(f,x0,x1,h,lod):
    f.box((x0+x1)/2,h-.49,x1-x0,.83,.205,.043,EDGE,'parapet relief panel')
    f.box((x0+x1)/2,h-.93,x1-x0,.090,.24,.057,ROUGH,'parapet shadow edge')
    f.box((x0+x1)/2,h+.02,x1-x0,.085,.23,.052,EDGE,'coping')
    # A raised rectangular cartouche with mirrored spiral leaves and a centre disk.
    c=(x0+x1)/2;z=h-.45
    rim=box(c-.91,z-.21,c+.91,z+.21)
    f.prism(rim.difference(rim.buffer(-.022,join_style=2)),.145,.171,ROUGH,'relief cartouche border')
    f.prism(Point(c,z).buffer(.091,quad_segs=8),.145,.179,EDGE,'central stone boss')
    for sign in (-1,1):
        for radius,offset,flip in [(.18,.58,1),(.11,.31,-1)]:
            turns=8 if lod else 17
            path=[]
            for j in range(turns+1):
                t=j/turns;angle=-.18*pi+1.87*pi*t
                path.append((c+sign*(offset+radius*(1-.80*t)*cos(angle)),z+flip*radius*(1-.80*t)*sin(angle)))
            stroke(f,path,.024,.15,.182,ROUGH,'mirrored carved scroll')
        stroke(f,[(c+sign*.10,z-.025),(c+sign*.27,z-.08),(c+sign*.44,z+.11),(c+sign*.64,z+.13)],.030,.151,.179,EDGE,'scroll stem')
        if not lod:
            for j in range(4):
                xx=c+sign*(.29+j*.13)
                stroke(f,[(xx,z+.09),(xx+sign*.056,z+.151)],.024,.15,.181,ROUGH,'short foliate stroke')


def crown_initials(f,lod):
    # The 2010 museum photograph resolves the initials R A S on the upper slab.
    paths=[
      [[(-.20,-.20),(-.20,.20),(.095,.20),(.18,.15),(.18,.046),(.105,.005),(-.19,.005)],[(.015,.004),(.21,-.20)]],
      [[(-.21,-.20),(0,.20),(.21,-.20)],[(-.118,-.045),(.118,-.045)]],
      [[(.19,.20),(-.14,.20),(-.19,.14),(-.19,.03),(-.14,-.005),(.126,-.005),(.19,-.06),(.19,-.15),(.13,-.20),(-.19,-.20)]]]
    for j,strokes in enumerate(paths):
        x=(j-1)*.775
        for coords in strokes:
            stroke(f,[(x+u,22.95+v)for u,v in coords],.022,.209,.235,ROUGH,'roof initials R A S')
        if j<2:f.box(x+.32,22.77,.031,.031,.023,.222,ROUGH,'period between roof initials')


def stone_label(f,lod):
    f.box(0,8.50,5.17,1.18,.27,.064,EDGE,'four-character historic name slab')
    # Outline strokes drawn separately, right-to-left 亞 洲 文 會, in the photographed seal-script layout.
    parts=[
      [[(-.41,.21),(0,.53),(.41,.21)],[(-.31,.19),(.31,.19)],[(-.28,.12),(-.28,-.10),(.28,-.10),(.28,.12),(-.28,.12)],[(-.10,.10),(-.10,-.10)],[(.10,.10),(.10,-.10)],[(-.24,-.19),(.24,-.19),(.24,-.43),(-.24,-.43),(-.24,-.19)],[(-.21,-.30),(.21,-.30)]],
      [[(-.36,.19),(-.22,.36),(.10,.43),(.29,.30),(.32,.16)],[(-.11,.27),(-.04,.10),(-.12,-.08),(-.14,-.40)],[(.09,.24),(.16,.08),(.11,-.13),(.11,-.42)]],
      [[(-.41,.28),(-.25,.18)],[(-.42,.04),(-.27,-.03)],[(-.40,-.32),(-.22,-.12)],[(-.14,.34),(-.04,.16),(-.10,-.02),(-.19,-.32)],[(.05,.38),(.14,.17),(.09,-.02),(.05,-.33)],[(.25,.34),(.35,.13),(.29,-.08),(.30,-.34)]],
      [[(-.40,.37),(.40,.37)],[(-.33,-.35),(.40,-.35)],[(-.19,.34),(-.19,.10),(-.39,.10),(-.39,-.11),(-.18,-.11),(-.18,-.33)],[(.20,.35),(.20,.10),(.38,.10),(.38,-.11),(.19,-.11),(.19,-.33)]]]
    for j,paths in enumerate(parts):
        c=(j-1.5)*1.03
        for path in paths:stroke(f,[(c+u*.64,8.51+z*.65) for u,z in path],.029,.199,.216,ROUGH,'seal-script name relief')
    for x in [-1.50,1.50]:
        f.box(x,7.83,.16,.27,.27,.04,ROUGH,'slab bracket')


def add_huqiu(builder,lod=False):
    front=Facade(builder,(-HALF,0),(HALF,0),'Huqiu Road')
    def plane(y):return Facade(builder,(-HALF,y),(HALF,y),'recessed central bay')
    center=plane(.62)
    holes=[opening(x,.225,1.52,3.17-.225,.70,16 if lod else 36) for x in (-2.04,0,2.04)]
    holes += [octagon(x,2.23,.501) for x in (-4.45,4.45)]
    plinth=box(-HALF,.016,HALF,BASE_TOP).difference(unary_union(holes))
    front.prism(plinth,-.56,0,STONE,'street ashlar and arched reveals')
    for x in (-2.04,0,2.04):gate(front,x,lod)
    for x in (-4.45,4.45):
        bagua(front,x,2.23,lod)
        front.box(x,1.27,1.27,.42,.045,.028,METAL,'museum nameplate')
    for left,right in [(-HALF,-WING_EDGE),(WING_EDGE,HALF)]:
        x=(left+right)/2
        light=box(x-.27,17.59,x+.27,19.56)
        face(front,box(left,BASE_TOP,right,WING_TOP),[light],lod)
        glazing(front,x,17.59,19.56,.54,0,1,'outer high light',lod)
        front.box(x,17.42,.59,.20,.15,.034,EDGE,'high light sill')
        front.box(x,11.31,.038,12.01,.095,.035,PALE,'vertical brick detail')
        parapet(front,left,right,WING_TOP,lod)
    for side in [-1,1]:
        x=side*WING_EDGE
        builder.box((x,.334,(BASE_TOP+WING_TOP)/2),(.04,.67,WING_TOP-BASE_TOP),BRICK,label='return joining the recessed brick plane')
    hi_openings=upper_lights(center,lod)
    face(center,box(-WING_EDGE,BASE_TOP,WING_EDGE,CENTER_TOP),hi_openings,lod)
    stone_label(center,lod)
    center.box(0,22.93,2.99,.66,.33,.039,EDGE,'stepped crown')
    center.box(0,23.31,3.26,.11,.42,.082,EDGE,'crown upper shelf')
    center.box(0,22.54,3.62,.12,.39,.067,ROUGH,'crown lower shelf')
    crown_initials(center,lod)
    for x in [-2.25,2.25]:
        for k in range(3):
            center.box(x,22.83+.098*k,.34-.055*k,.075,.23-.031*k,.06,ROUGH,'corner crest')
    front.box(0,3.90,7.72,.23,1.24,.31,EDGE,'projecting balcony slab')
    for i in [-3,-1,1,3]:
        x=i*1.18
        builder.box((x,-.76,4.61),(.36,.35,1.26),STONE,label='balcony pier')
        builder.box((x,-.76,5.27),(.43,.40,.14),ROUGH,label='balcony cap')
        curve=[(-.90,3.90),(-.90,3.83)]
        for j in range(1,9):
            t=pi*j/16
            curve.append((-.30-.60*cos(t),3.83-.34*sin(t)))
        curve += [(.01,3.49),(.01,3.90)]
        # Side profile sweeps back from the balcony nose into the ashlar wall.
        builder.prism(Polygon(curve),-.135,.135,lambda y,z,r:(x+r,y,z),STONE,'curved under-balcony corbel')
    for z in [4.28,4.77]:
        front.box(0,z,7.15,.158,.185,.77,EDGE,'open stone balcony rail')
    for x in (-3.55,3.55):
        builder.box((x,-.045,4.77),(.17,1.19,.158),EDGE,label='balcony rail return')
    # Plain section surfaces terminate the short, measured frontage fragment.
    for side in (-1,1):
        builder.box((side*(HALF-.026),SECTION_DEPTH/2,WING_TOP/2),(.052,SECTION_DEPTH,WING_TOP),SECTION,label='plain side section')
    for left,right,h in [(-HALF,-WING_EDGE,WING_TOP),(-WING_EDGE,WING_EDGE,CENTER_TOP),(WING_EDGE,HALF,WING_TOP)]:
        y=.62 if left==-WING_EDGE else 0
        builder.box(((left+right)/2,(y+SECTION_DEPTH)/2,h-.02),(right-left,SECTION_DEPTH-y,.04),SECTION,label='plain top section')
    builder.box((0,SECTION_DEPTH-.026,9.60),(WIDTH,.052,19.20),SECTION,label='rear section at unmodified city shell')
