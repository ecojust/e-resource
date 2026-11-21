"""Palladian balcony on the 1925 garden house at 630 Yongjia Road.

All dimensions refer to the selected historical fragment. X goes right in
the near-frontal 2013 photograph, Y recedes from the rail into the facade.
"""
from math import cos,pi,sin
from shapely.affinity import translate
from shapely.geometry import LineString,Polygon,Point,box
from shapely.ops import unary_union

PALETTE={
    'grey aggregate stone':{'color':[.31,.303,.272],'roughness':.90},
    'recessed grey plaster':{'color':[.265,.254,.215],'roughness':.90},
    'projecting pale stone':{'color':[.445,.424,.376],'roughness':.85},
    'faded ivory joinery':{'color':[.79,.746,.60],'roughness':.76},
    'ivory pierced balustrade':{'color':[.845,.804,.666],'roughness':.83},
    'shaded leaded glass':{'color':[.070,.12,.126],'metallic':.18,'roughness':.23},
    'reflected grey glass':{'color':[.113,.154,.156],'metallic':.18,'roughness':.28},
    'moulded weathered sill':{'color':[.348,.336,.301],'roughness':.88},
}
STONE='grey aggregate stone'
LIGHT='projecting pale stone'
IVORY='ivory pierced balustrade'

def front(b,profile,outer,back,material,name):
    b.prism(profile,-back,-outer,lambda x,z,d:(x,-d,z),material,name)
def block(b,name,material,x,y,z,w,d,h):
    b.box((x,y,z),(w,d,h),material,label=name)
def rail_pattern(lod):
    n=14 if lod else 32
    bars=[]
    for x in (-.365,.365):
        outer=Point(x,1.33).buffer(.397,quad_segs=n)
        bars.append(outer.difference(Point(x,1.33).buffer(.293,quad_segs=n)))
        for sign in (-1,1):
            line=LineString([(x-sign*.30,.915),(x+sign*.30,1.75)])
            bars.append(line.buffer(.036,cap_style=2).intersection(outer))
    # The white end motifs are diamonds with four flared, concave arms.
    outer=Polygon([(0,.48),(.083,.48),(.127,.25),(.196,.128),(.336,.107),(.336,-.05),(.223,-.077),(.132,-.213),(.077,-.47),(-.079,-.47),(-.138,-.209),(-.217,-.071),(-.338,-.047),(-.338,.105),(-.189,.130),(-.121,.257),(-.076,.48)])
    hole=Polygon([(0,.273),(.085,.117),(.181,.032),(.09,-.058),(0,-.268),(-.089,-.065),(-.174,.027),(-.074,.118)])
    shape=outer.difference(hole)
    for x in (-1.005,1.005):
        bars.append(translate(shape,xoff=x,yoff=1.32))
    bars.append(box(-1.36,1.29,-1.15,1.37));bars.append(box(1.15,1.29,1.36,1.37))
    return unary_union(bars)
def window(b,lod,x,width,bottom,top,panes,rows,label):
    opening=box(x-width/2,bottom,x+width/2,top)
    inner=opening.buffer(-.069,join_style=2)
    front(b,opening.difference(inner),.875,.985,'faded ivory joinery',label+' frame')
    a,z0,c,z1=inner.bounds
    for i in range(panes):
        for j in range(rows):
            xl=a+(c-a)*i/panes;xr=a+(c-a)*(i+1)/panes;zb=z0+(z1-z0)*j/rows;zt=z0+(z1-z0)*(j+1)/rows
            left=xl+(.017 if i else 0);right=xr-(.017 if i+1<panes else 0);lo=zb+(.016 if j else 0);hi=zt-(.016 if j+1<rows else 0)
            tint='reflected grey glass' if (i+j)%4==1 else 'shaded leaded glass'
            block(b,label+' panes',tint,(left+right)/2,.991,(lo+hi)/2,right-left,.018,hi-lo)
    for i in range(1,panes):
        block(b,label+' vertical stiles','faded ivory joinery',a+(c-a)*i/panes,.921,(z0+z1)/2,.034,.099,z1-z0)
    for j in range(1,rows):
        z=z0+(z1-z0)*j/rows
        for i in range(panes):
            left=a+(c-a)*i/panes+(.017 if i else 0);right=a+(c-a)*(i+1)/panes-(.017 if i+1<panes else 0)
            block(b,label+' rails','faded ivory joinery',(left+right)/2,.936,z,right-left,.076,.032)
def add_balcony(b,lod=False):
    n=13 if lod else 32
    # Photographs 4, 11 and 18 show the two corner consoles and dark projecting floor.
    for x in (-1.54,1.54):
        console=Polygon([(-.10,.45),(.66,.45),(.82,-.29),(.63,-.29),(.48,-.21),(.42,-.04),(.26,.02),(.22,.18),(-.10,.27)])
        b.prism(console,x-.135,x+.135,lambda y,z,d:(d,y,z),STONE,'Stepped supporting console')
    block(b,'Projecting balcony floor',STONE,0,.427,.463,3.78,1.24,.162)
    block(b,'Lower moulded drip','moulded weathered sill',0,.413,.555,3.88,1.29,.09)
    face=box(-1.80,.596,1.80,2.12);aperture=box(-1.35,.868,1.35,1.87)
    front(b,face.difference(aperture),-.145,.11,STONE,'Pierced balcony frame')
    front(b,rail_pattern(lod).intersection(aperture),-.093,-.018,IVORY,'Paired circles, crosses and cusped diamonds')
    block(b,'Continuous front coping',LIGHT,0,-.025,2.15,3.72,.35,.083)
    for x in (-1.70,1.70):
        outline=box(.08,.60,1.04,2.12);slot=box(.155,.867,.93,1.87)
        b.prism(outline.difference(slot),x-.10,x+.10,lambda y,z,d:(d,y,z),STONE,'Side of historic balcony')
        # One further raised diamond is visible on the return in the oblique image.
        diamond=Polygon([(.54,1.82),(.68,1.52),(.91,1.35),(.68,1.16),(.54,.90),(.42,1.16),(.18,1.35),(.42,1.52)])
        b.prism(diamond.difference(diamond.buffer(-.065,join_style=2)),x-.035,x+.035,lambda y,z,d:(d,y,z),IVORY,'Open diamond on side return')
        block(b,'Side coping',LIGHT,x,.566,2.15,.26,.973,.083)
    for x in (-1.5,1.5):
        block(b,'Pier foot',LIGHT,x,.075,2.24,.48,.50,.105)
        b.lathe((x,.085),[(2.28,.219),(2.34,.212),(2.385,.16),(2.42,.145),(2.48,.148),(2.54,.132),(3.76,.125),(3.79,.148),(3.85,.154),(3.89,.144)],LIGHT,segments=12 if lod else 28,label='Round column shaft and annulets')
        for z,w,d,h in [(3.92,.35,.38,.075),(4,.408,.42,.082),(4.08,.453,.477,.082),(4.15,.50,.52,.064)]:
            block(b,'Stepped column capital',STONE,x,.072,z,w,d,h)
    sp=4.52;rr=1.47;cx=0
    hemi=Point(cx,sp).buffer(rr,quad_segs=n).intersection(box(-2,sp,2,6.4))
    outer=Point(cx,sp).buffer(rr+.187,quad_segs=n).intersection(box(-2,sp,2,6.4))
    front(b,outer.difference(hemi),-.14,.829,STONE,'Barrel and projecting arch ring')
    bead=Point(cx,sp).buffer(rr+.192,quad_segs=n).difference(Point(cx,sp).buffer(rr+.145,quad_segs=n)).intersection(box(-2,sp,2,6.45))
    front(b,bead,-.175,-.135,LIGHT,'Fine raised archive moulding')
    front(b,hemi,.821,1.005,'recessed grey plaster','Recessed lunette')
    shield=Polygon([(-.205,4.94),(-.20,5.22),(0,5.295),(.205,5.22),(.202,4.94),(0,4.81)])
    front(b,shield,.75,.825,LIGHT,'Shield in lunette')
    for z,w,fr,back,h in [(4.19,3.47,-.155,1.,.10),(4.295,3.58,-.185,1.,.095),(4.396,3.62,-.21,1.,.099),(4.48,3.61,-.22,.99,.072)]:
        block(b,'Horizontal archivolt bed',STONE,0,(fr+back)/2,z,w,back-fr,h)
    # The window behind the balcony is drawn as three pairs of divided casements.
    window(b,lod,0,2.16,.65,4.12,6,8,'Middle French casements')
    for side in (-1,1):
        x=side*2.10;opening=box(x-.31,1.875,x+.31,4.17);frame=opening.buffer(.146,join_style=2)
        front(b,frame.difference(opening),.71,1.01,STONE,'Side window surround')
        window(b,lod,x,.622,1.875,4.17,2,4,'Lateral white window')
        block(b,'Side window sill',LIGHT,x,.81,1.786,.91,.36,.101)
        for z,w,h in [(4.35,.91,.15),(4.46,.95,.067),(4.535,.99,.07)]:
            block(b,'Side cornice returns',STONE,x,.799,z,w,.41,h)
