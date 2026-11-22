"""Sichuan Middle Road elevation. X runs toward the south end, Y into the building."""
from math import cos, sin, pi
from shapely.geometry import Polygon, box
from photo_architecture import Facade, opening

STONE = 'warm grey ashlar'
TRIM = 'carved pale stone'
BASE = 'grey granite plinth'
GLASS = 'smoky blue glass'
FRAME = 'dark metal window sash'
BRONZE = 'aged door metal'
DARK = 'deep green door panels'
ROOF = 'grey roof flashing'
JOINT = 'shadowed stone joint'
PALETTE = {
    STONE: dict(color=[.643,.625,.571],roughness=.89),
    TRIM: dict(color=[.737,.704,.639],roughness=.80),
    BASE: dict(color=[.485,.477,.449],roughness=.87),
    GLASS: dict(color=[.301,.331,.329],metallic=.23,roughness=.32),
    FRAME: dict(color=[.200,.209,.198],metallic=.25,roughness=.53),
    BRONZE: dict(color=[.434,.365,.219],metallic=.53,roughness=.49),
    DARK: dict(color=[.220,.271,.235],metallic=.18,roughness=.56),
    ROOF: dict(color=[.396,.393,.382],roughness=.83),
    JOINT: dict(color=[.432,.420,.383],roughness=.90),
}
END = 20.36
SHOULDER = 14.26
DEPTH = 4.42
CENTERS = (-11.34,-5.67,0,5.67,11.34)
WINDOW_BASES = (8.75,12.02,15.29,18.56)
ATTIC = 21.85


def front(b,left,right,y,name):
    return Facade(b,(left,y),(right,y),name)


def head_course(f,z,scale=1):
    for ds,ht,proj in [(-.15,.15,.32),(.02,.12,.39),(.13,.11,.46)]:
        f.box(0,z+ds*scale,f.length+.05,ht*scale,proj*scale,.09*scale,TRIM,'moulded belt')


def divided_window(f,x,z,w,h,lod,small=False):
    hole=box(x-w/2,z,x+w/2,z+h)
    f.prism(hole.buffer(.012,join_style=2),-.31,-.29,GLASS,'recessed panes')
    outer=hole.buffer(-.018,join_style=2)
    lights=[box(x-w/2+.058,z+.067,x+w/2-.058,z+h*(.735 if not small else .63)),
            box(x-w/2+.058,z+h*(.735 if not small else .63)+.058,x+w/2-.058,z+h-.064)]
    from shapely.ops import unary_union
    f.prism(outer.difference(unary_union(lights)),-.244,-.16,FRAME,'sash and high transoms')
    f.box(x,z-.055,w+.145,.11,.34,-.035,TRIM,'stone sills')
    if not lod and small:
        f.box(x,z+h*.45,.025,h*.75,.033,-.194,FRAME,'small sash bar')
    return hole


def pier(b,f,x,low,high,width,pitch,name):
    first=low
    while first<high-.01:
        last=min(first+pitch,high)
        f.box(x,(first+last)/2,width,last-first-.020,.18,.076,STONE,name)
        first=last


def bracket(b,x,ybase,z,lod,label):
    # Swept underside is deep at the wall, shallow at the leading edge.
    side=Polygon([(0,0),(.17,.02),(.32,.15),(.40,.38),(.52,.58),(.74,.72),(.75,.86),(0,.86)])
    f=Facade(b,(x+.10,ybase),(x+.10,ybase+.2),label)
    # A side polygon in depth and height, extruded along the bay width.
    b.prism(side,-.12,.12,lambda u,v,d:(x-d,ybase-u,z+v),TRIM,label+'/curved consoles')
    if not lod:
        for step in range(5):
            b.box((x,ybase-.065,z+.078+step*.128),(.272,.10,.043),STONE,label=label+'/console flutes')


def window_storeys(b,lod):
    for zone,l,r,y,top,axes in [
        ('north end',-END,-SHOULDER,-.18,25.83,[(-END-SHOULDER)/2]),
        ('central range',-SHOULDER,SHOULDER,.10,25.27,CENTERS),
        ('south end',SHOULDER,END,-.18,25.83,[(END+SHOULDER)/2])]:
        f=front(b,l,r,y,zone);local=lambda x:x-(l+r)/2;middle=zone=='central range';holes=[]
        for x in axes:
            c=local(x)
            for z in WINDOW_BASES:
                offsets=(-1.18,0,1.18) if middle else (-.60,.60)
                for dx in offsets:holes.append(divided_window(f,c+dx,z,1.05,2.08,lod))
            offsets=(-.88,.88) if middle else (-.58,.58)
            for dx in offsets:holes.append(divided_window(f,c+dx,ATTIC+.18*(not middle),1.10,1.26,lod,True))
        f.wall(8.30,top,holes,.26,STONE)
        if middle:
            for x in [-8.505,-2.835,2.835,8.505]:
                for side in (-1,1):
                    f.box(x+side*.34,14.81,.20,12.63,.17,.055,TRIM,'paired shallow piers')
                f.box(x,20.82,1.00,.24,.29,.080,TRIM,'flat pier caps')
        else:
            for x in (-2.29,2.29):pier(b,f,x,8.35,21.60,1.16,.61,'rusticated end pilasters')
        head_course(f,8.34,1.13);head_course(f,21.19,.72)
        f.box(0,top-.85,f.length+.24,.24,1.05,.26,TRIM,'projecting cornice soffit')
        f.box(0,top-.62,f.length+.25,.21,1.15,.32,TRIM,'dentil rail')
        count=max(1,round(f.length/.36))
        for n in range(count):
            f.box(f.length*((n+.5)/count-.5),top-.45,.18,.17,.36,.74,TRIM,'stone dentils')
        f.box(0,top-.254,f.length+.30,.20,1.28,.31,TRIM,'cornice lip')
        f.box(0,top-.10,f.length+.20,.12,.92,.20,STONE,'parapet coping')
        centers=[l+.52,r-.52] if not middle else [-8.50,-2.835,2.835,8.50]
        for x in centers:
            for dx in (-.23,.23):bracket(b,x+dx,y-.09,top-1.83,lod,zone)
        b.plan_prism(box(l,y-.1,r,DEPTH),top-.19,top-.12,ROOF,zone+'/roof strip')
        b.box(((l+r)/2,DEPTH-.10,(top+8.30)/2),(r-l,.20,top-8.30),STONE,label=zone+'/rear section')


def cast_column(b,x,z0,z1,lod,zone):
    h=z1-z0
    b.box((x,-.12,z0+.12),(.86,.83,.24),BASE,label=zone+'/square pedestals')
    curve=[(.21,.411),(.27,.425),(.35,.438),(.41,.427),(.46,.358),(.54,.38),
           (.62,.339),(h*.5,.328),(h-.52,.296),(h-.45,.330),(h-.40,.304),
           (h-.32,.350),(h-.23,.399),(h-.17,.420)]
    b.lathe((x,-.12),[(z0+z,r)for z,r in curve],TRIM,14 if lod else 24,zone+'/tapered stone shafts')
    b.box((x,-.12,z1-.105),(.91,.87,.21),TRIM,label=zone+'/capital slabs')
    for dx in (-.28,.28):
        b.lathe((x+dx,-.33),[(z1-.37,.065),(z1-.32,.098),(z1-.25,.10),(z1-.19,.064)],
                TRIM,6 if lod else 10,zone+'/capital lobes')


def ornamental_windows(b,lod,side):
    zone='north colonnade'if side<0 else 'south colonnade';a,c=sorted((side*2.72,side*SHOULDER));mid=(a+c)/2
    f=front(b,a,c,.65,zone+'/recess');holes=[]
    for dx in (-2.69,2.69):
        hole=box(dx-2.20,1.04,dx+2.20,7.67);holes.append(hole)
        f.prism(hole.buffer(.008,join_style=2),-.217,-.204,GLASS,'bank windows')
        f.prism(hole.difference(hole.buffer(-.093,join_style=2)),-.17,-.12,FRAME,'recess frames')
        for z in (4.67,5.34):f.box(dx,z,4.44,.145,.17,-.045,FRAME,'transom beams')
        for j in range(1,6):
            x=dx-2.20+4.40*j/6
            f.box(x,4.39,.051,6.51,.06,-.117,FRAME,'window mullions')
        for j in range(-2,3):
            xc=dx+j*.73
            for i in range(2 if lod else 5):
                z=1.22+(i+.5)*((4.43-1.22)/(2 if lod else 5))
                # Geometric approximation of the photographed metal grille, not a cast pattern survey.
                pts=[f.point(xc+.31*cos(t*pi/8),z+.24*sin(t*pi/8),-.042)for t in range(17)]
                b.tube(pts,.027,BRONZE,4 if lod else 6,zone+'/circular grille')
        for i in range(7):
            t=(i+.5)/7;f.box(dx+4.39*(t-.5),6.56,.038,2.25,.045,-.119,FRAME,'upper narrow lights')
        if not lod:
            for edge in (-1,1):
                f.line((dx,5.34,-.035),(dx+edge*1.58,5.02,-.035),.052,FRAME,6,'shallow pediment')
    f.wall(.05,8.32,holes,.26,STONE)
    for x in (a+.22,mid-.47,mid+.47,c-.22):cast_column(b,x,.78,8.07,lod,zone)
    face=front(b,a,c,.12,zone)
    face.box(0,.22,face.length,.44,.72,.055,BASE,'plinth')
    for dx in (-2.69,2.69):
        for i in range(9):
            x=mid+dx+(i-4)*.46
            b.lathe((x,.035),[(.39,.115),(.47,.106),(.55,.062),(.65,.090),(.70,.070),(.80,.095)],TRIM,6 if lod else 10,zone+'/low balusters')
        face.box(dx,.87,4.36,.13,.37,.11,TRIM,'balustrade coping')
    face.box(0,8.12,face.length+.05,.30,.86,0,TRIM,'column head beam')
    b.plan_prism(box(a,.04,c,DEPTH),8.10,8.30,STONE,zone+'/soffit')


def portal(b,lod,name,left,right,width,arch_height,entry):
    f=front(b,left,right,-.16,name);zbase=.23;opening_shape=opening(0,zbase,width,arch_height,1.31 if entry else .91,12 if lod else 24)
    f.wall(.045,8.32,[opening_shape],.63,STONE)
    # Thin, discontinuous rustication strips do not cross the real door opening.
    from shapely.geometry import box as rect
    for i in range(1,14):
        h=.54+i*.61
        joint=rect(-f.length/2,h-.015,f.length/2,h+.015).difference(opening_shape.buffer(.03))
        f.prism(joint,.003,.013,JOINT,'horizontal stone joints')
    spring=zbase+arch_height-(1.31 if entry else .91)
    for i in range(1,10):
        t=pi*i/10;x=cos(t)*width*.5;z=spring+sin(t)*(1.31 if entry else .91)
        f.line((x,z,.023),(x+cos(t)*.71,z+sin(t)*.56,.023),.024,JOINT,4,'radiating arch joints')
    back=front(b,left,right,.425,name+'/recessed doorway');back.prism(opening_shape,-.07,.00,BASE,'door reveal back')
    door_h=3.46 if entry else 2.86
    door_w=width-.29
    for side in (-1,1):
        back.box(side*door_w*.247,.29+door_h*.5,door_w*.48,door_h,.12,.063,DARK,'paired door leaves')
        rect=box(side*door_w*.247-door_w*.158,.66,side*door_w*.247+door_w*.158,door_h-.02)
        back.prism(rect.difference(rect.buffer(-.055,join_style=2)),.12,.153,BRONZE,'door panel trim')
        if entry:
            center=side*door_w*.247
            for ring_radius in (.24,.31):
                ring=[back.point(center+ring_radius*cos(t*pi/12),2.56+ring_radius*sin(t*pi/12),.169) for t in range(25)]
                b.tube(ring,.025,BRONZE,5 if lod else 8,name+'/circular leaf emblems')
            for dx in (-.35,-.18,0,.18,.35):
                z0=.69 if abs(dx)>.31 else .74
                z1=door_h-.11
                back.box(center+dx,(z0+z1)/2,.024,z1-z0,.045,.145,BRONZE,'slender upright door rods')
    fan=opening(0,door_h+.70,width-.24,arch_height-door_h-.60,1.12 if entry else .65,18)
    back.prism(fan,-.015,.043,GLASS,'arched transom glass')
    for fctr in (-.25,0,.25):
        strip=box(width*fctr-.037,door_h+.64,width*fctr+.037,zbase+arch_height).intersection(fan)
        back.prism(strip,.05,.09,FRAME,'fanlight mullions')
    for offset,size,height in [(.41,.20,.12),(.61,.29,.15)]:
        back.box(0,door_h+offset,width+.035,height,size,.12,TRIM,'overdoor lintel')
    b.plan_prism(box(left,-.16,right,DEPTH),8.10,8.30,STONE,name+'/head slab')
    b.plan_prism(box((left+right-width)/2-.10,-.43,(left+right+width)/2+.10,.60),0,.105,BASE,name+'/street threshold')


def make_front(b,lod):
    window_storeys(b,lod)
    ornamental_windows(b,lod,-1);ornamental_windows(b,lod,1)
    portal(b,lod,'central smaller portal',-2.72,2.72,2.13,5.52,False)
    portal(b,lod,'south arched portal',SHOULDER,END,3.49,6.87,True)
    # The 2015 camera does not show the projecting north end at pavement level.
    # Its existing city source is retained there, including its original street-level collision.
    b.box(((END-SHOULDER)/2,DEPTH-.13,4.13),(SHOULDER+END,.26,8.26),STONE,label='ground/section closure')
    for x,bottom,top in [(-END,8.30,25.83),(END,.05,25.83)]:
        b.box((x,.5*DEPTH,(bottom+top)/2),(.18,DEPTH,top-bottom),STONE,label='end/section returns')
