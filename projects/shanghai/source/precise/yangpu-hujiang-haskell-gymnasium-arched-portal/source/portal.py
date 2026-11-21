"""Historical Haskell Gymnasium entrance, as recorded in the university archive."""
from math import sqrt
from shapely.geometry import Polygon, box

ASHLAR='warm ashlar'; CUT='pale dressed stone'; RECESS='shadowed stone'; JOINT='stone bedding'; DOOR='dark oak'; RAIL='oak door frame'; GLASS='transom glass'; SILL='worn threshold'
PALETTE={name:dict(color=c,roughness=r) for name,c,r in [
    (ASHLAR,[.49,.434,.344],.94),(CUT,[.69,.631,.515],.88),
    (RECESS,[.323,.274,.215],.94),(JOINT,[.266,.247,.194],.97),
    (DOOR,[.072,.043,.029],.85),(RAIL,[.112,.075,.045],.79),
    (GLASS,[.153,.19,.174],.39),(SILL,[.381,.352,.298],.93)]}

# The opening has nearly vertical springing and two shallow arcs meeting at a point.
# (width, height, depth) are estimates from the photographed opening.
SPRING=2.45
COURSES=[
    (.906,.502,.878,.485,.087,.027,RECESS,'Inner shadow at fanlight'),
    (.963,.563,.906,.502,.023,.132,CUT,'Inner roll'),
    (.994,.585,.963,.563,.065,.136,RECESS,'First hollow'),
    (1.050,.631,.994,.585,-.015,.122,CUT,'Middle roll'),
    (1.084,.654,1.050,.631,.032,.130,RECESS,'Outer hollow'),
    (1.145,.718,1.084,.654,-.065,.122,CUT,'Projecting outer hood')]

def height(t,rise):
    """Two mirrored elliptical segments, with a change of slope at the crown."""
    k=.45
    return SPRING+rise*sqrt(max(0,1-(k+(1-k)*abs(t))**2))/sqrt(1-k*k)

def arch_points(radius,rise,segments):
    return [(radius*i/segments,height(i/segments,rise)) for i in range(-segments,segments+1)]

def opening(radius,rise,segments,bottom):
    return Polygon([(-radius,bottom),(radius,bottom),*reversed(arch_points(radius,rise,segments))])

def face(b,p,front,back,mat,name):
    if not p.is_empty:
        b.prism(p,-back,-front,lambda x,z,t:(x,-t,z),mat,label=name)

def block(b,x0,x1,y0,y1,z0,z1,material,label):
    b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),material,label=label)

def model(b,lod=False):
    segments=16 if lod else 30
    outer=opening(1.145,.718,segments,-.1)
    # Stone face and jambs have a real aperture through their full depth.
    blockheight=.293; wall=box(-1.60,.0,1.60,3.38)
    face(b,wall.difference(outer),.143,.45,JOINT,'Backing with open arched reveal')
    for j in range(12):
        low=j*blockheight
        if low>=3.38:break
        cuts=[-1.60,-1.20,-.60,.03,.62,1.23,1.60] if j%2==0 else [-1.60,-1.43,-.89,-.29,.32,.89,1.43,1.60]
        for left,right in zip(cuts,cuts[1:]):
            slab=box(left+.003,low+.003,right-.003,min(low+blockheight-.003,3.38)).difference(outer)
            for p in getattr(slab,'geoms',[slab]):
                if p.area>.0001:face(b,p,.120,.147,ASHLAR,'Dressed masonry at opening')
    for ro,ho,ri,hi,front,back,mat,name in COURSES:
        face(b,opening(ro,ho,segments,.0).difference(opening(ri,hi,segments,-.1)),front,max(front,back)+.02,mat,name)
    for side in (-1,1):
        x=side*1.377
        block(b,x-.190,x+.190,-.072,.121,.0,.42,ASHLAR,'Jamb plinth')
        block(b,x-.210,x+.210,-.106,.121,.42,.477,CUT,'Jamb plinth cap')
        block(b,x-.142,x+.142,-.032,.122,SPRING-.076,SPRING+.021,CUT,'Stone impost ledge')
    clear=.878
    face(b,opening(clear,.485,segments,.03),.397,.43,RECESS,'Recessed stone backing')
    fan=opening(.868,.477,segments,2.10)
    face(b,fan,.361,.395,GLASS,'Glazed arched transom')
    for i in (-3,-2,-1,0,1,2,3):
        x=i*.217;top=height((abs(x)+.016)/.868,.477)
        block(b,x-.016,x+.016,.312,.372,2.10,top,RAIL,'Vertical transom glazing bars')
    block(b,-clear,clear,.264,.375,2.029,2.103,RAIL,'Transom rail')
    for side in (-1,1):
        x=side*.437
        block(b,x-.432,x+.432,.369,.398,.059,2.03,DOOR,'Recessed paired timber leaves')
        for p in (-.392,.392):
            block(b,x+p-.038,x+p+.038,.321,.371,.064,2.03,RAIL,'Door stiles')
        for lo,hi in [(.069,.187),(1.30,1.392),(1.916,2.03)]:
            block(b,x-.36,x+.36,.327,.371,lo,hi,RAIL,'Door rails')
    block(b,-.915,.915,-.26,.45,.003,.058,SILL,'Stone threshold')
