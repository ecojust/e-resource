"""Rendered wall, exposed brick courses and the three separately documented plaques west of the gate."""
from math import cos,pi,sin
from shapely.geometry import box,Polygon
from shapely.ops import unary_union
from photo_architecture import Facade
from details import (STONE,PANEL,BRICK,BURNT,FADED,MORTAR,WOOD,WHITE,INK,BRONZE,HIGHLIGHT,GREEN,ALLOY,
                     oval,strip,letters)

WEST=-4.43
EAST=-2.18
BOTTOM_BELT=1.55
TOP=2.31

def masonry(face,lod):
    centre=(WEST+EAST)/2;width=EAST-WEST
    face.box(centre,TOP/2,width,TOP,.305,-.15,MORTAR,'western cut masonry backing')
    face.box(centre,.075,width,.150,.33,-.145,STONE,'grey plinth')
    # The street view shows staggered red faces and pale recessed mortar.
    for row in range(19):
        low=.15+row*(BOTTOM_BELT-.15)/19;high=.15+(row+1)*(BOTTOM_BELT-.15)/19
        start=WEST-(.111 if row%2 else 0.)
        for col in range(12):
            left=max(WEST,start+col*.225+.006);right=min(EAST,start+(col+1)*.225-.006)
            if right-left<.012:continue
            mat=(BRICK,BRICK,FADED,BRICK,BURNT,BRICK,FADED)[(row*13+col*5)%7]
            face.prism(box(left,low+.004,right,high-.004),.001,.010 if lod else .012,mat,'brick courses '+str(row//4+1))
    face.box(centre,1.59,width+.010,.072,.344,-.141,STONE,'plaque bed lower sill')
    face.box(centre,1.939,width,.635,.315,-.145,PANEL,'rendered wall above sill')
    face.box(centre,2.281,width+.026,.083,.353,-.140,STONE,'wall coping')
    for x in (WEST+.094,-2.85):
        face.box(x,1.945,.074,.636,.329,-.140,STONE,'panel framing strips')

def rosette(face,x,z,r,d,lod,label):
    face.prism(oval(x,z,r,r,lod),d,d+.017,BRONZE,label+'/rose backing')
    coil=[]
    for i in range(17 if lod else 31):
        n=(16 if lod else 30)
        t=i/n;phi=t*2.63*pi
        coil.append((x+r*(.87-.68*t)*cos(phi),z+r*(.87-.68*t)*sin(phi)))
    strip(face,coil,max(.005,r*.13),d+.014,d+.025,HIGHLIGHT,label+'/curling petals')

def memorial(face,lod):
    cx=-2.595; z=1.982
    # Tapered cream inset with notched shoulders below a circular medallion.
    inner=Polygon([(cx-.152,z-.187),(cx-.138,z-.202),(cx+.138,z-.202),(cx+.154,z-.187),
                   (cx+.154,z+.100),(cx+.114,z+.118),(cx+.089,z+.157),
                   (cx+.053,z+.183),(cx-.048,z+.183),(cx-.089,z+.157),(cx-.113,z+.120),(cx-.154,z+.102)])
    surround=inner.buffer(.032,join_style='round',quad_segs=4 if lod else 7)
    face.prism(surround,.029,.061,BRONZE,'memorial / cast rounded surround')
    face.prism(inner,.059,.068,WHITE,'memorial / ceramic inset')
    face.prism(surround.difference(inner),.059,.084,HIGHLIGHT,'memorial / raised moulding')
    for sign in (-1,1):
        x=cx+sign*.181
        face.box(x,z-.015,.036,.357,.028,.082,BRONZE,'memorial / paired fluted pilasters')
        for offset in (-.010,.008):
            face.box(x+offset,z-.014,.004,.31,.012,.099,HIGHLIGHT,'memorial / flutes')
        for off,w,h in ((.123,.057,.020),(.15,.067,.018),(.165,.079,.012)):
            face.box(x,z+off,w,h,.034,.085,HIGHLIGHT,'memorial / pilaster capital')
        for j in range(3):
            ax=x+sign*(.010+.013*j);az=z+.053-.013*j
            leaf=Polygon([(ax,az-.027),(ax+sign*.028,az-.007),(ax+sign*.039,az+.026),(ax+sign*.009,az+.013)])
            face.prism(leaf,.078,.091,HIGHLIGHT,'memorial / laurel leaves')
    med=oval(cx,z+.179,.053,.056,lod);face.prism(med,.068,.086,BRONZE,'memorial / circular medallion')
    face.prism(med.difference(med.buffer(-.006)),.086,.094,HIGHLIGHT,'memorial / beaded medallion')
    # The cast wreath is a continuous peaked mount behind the embossed roses.
    # Its two sloping shoulders spring from the pilaster capitals.
    shoulders=Polygon([(cx-.215,z+.15),(cx-.197,z+.191),(cx-.111,z+.221),
                       (cx-.066,z+.272),(cx,z+.305),(cx+.066,z+.272),
                       (cx+.111,z+.221),(cx+.197,z+.191),(cx+.215,z+.15),
                       (cx+.143,z+.155),(cx+.078,z+.187),(cx,z+.226),
                       (cx-.078,z+.187),(cx-.143,z+.155)])
    apron=Polygon([(cx-.146,z-.193),(cx-.111,z-.242),(cx-.044,z-.277),(cx,z-.288),
                   (cx+.044,z-.277),(cx+.111,z-.242),(cx+.146,z-.193),
                   (cx+.087,z-.200),(cx,z-.225),(cx-.087,z-.200)])
    face.prism(shoulders,.041,.075,BRONZE,'memorial / continuous peaked bronze mount')
    face.prism(apron,.052,.075,BRONZE,'memorial / tapered foot mount')
    for dz,span,r in ((.276,.084,.039),(.223,.135,.027),(-.253,.077,.035),(-.219,.134,.029)):
        for i in (-1,0,1):
            rosette(face,cx+i*span,z+dz+(.011 if i==0 else 0),r,.067,lod,'memorial / floral crest')
    letters(face,'阮玲玉故居',cx,z+.074,.182,.032,.068,.071,INK,'memorial / plaque title',lod)
    if not lod:
        # The relief reproduces line layout only. The smaller bilingual wording
        # is outside the resolution established for the complete gate.
        for line,width in enumerate((.218,.238,.224,.236,.207,.234,.192,.196,.211)):
            h=z+.033-.017*line-(.013 if line>4 else 0)
            face.box(cx,h,width,.0023,.002,.070,INK,'memorial / inscription line layout')

def plates(face,lod):
    hx=-3.943
    face.box(hx,1.922,.553,.424,.026,.036,ALLOY,'heritage plate / metal field')
    letters(face,'优秀历史建筑',hx,2.052,.392,.041,.049,.054,INK,'heritage plate / heading',lod)
    if not lod:
        for n,width in enumerate((.41,.37,.43,.38,.415,.31)):
            face.box(hx,1.966-n*.025,width,.0028,.003,.052,INK,'heritage plate / inscription line layout')
    ax=-3.316
    num=box(ax-.302,1.895,ax+.302,2.089)
    face.prism(num,.019,.034,GREEN,'green enamel / street number')
    for sign in (-1,1):
        for level in (1.908,2.073):
            face.prism(oval(ax+sign*.29,level,.0038,.0038,lod),.034,.039,ALLOY,'green enamel / fixing screws')
    letters(face,'1124',ax-.164,2.017,.225,.089,.034,.039,WHITE,'green enamel / lane number',lod)
    letters(face,'弄1–59号',ax+.12,2.010,.286,.052,.034,.039,WHITE,'green enamel / house range',lod)
    letters(face,'新闸路',ax,1.936,.32,.045,.034,.039,WHITE,'green enamel / street name',lod)
    memorial(face,lod)

def wall(builder,lod):
    # The front of the plaque wall is approximately level with the western pier face.
    face=Facade(builder,(-5,-.006),(5,-.006),'west plaque wall')
    masonry(face,lod);plates(face,lod)
