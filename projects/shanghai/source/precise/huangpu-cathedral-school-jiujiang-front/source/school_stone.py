"""Extruded wall sections, steel windows and hand-drawn carved tracery on the school."""
from math import cos, sin, pi
from shapely.geometry import Polygon, box as rect, LineString
from shapely.ops import unary_union
from taishan_brick import MATERIAL as BRICK

STONE='School sand-coloured cast stone'
LIP='School stone moulding edge'
DARK='School shadowed carving'
IRON='School blackened iron'
GLASS='School recessed steel-window glazing'
SKY='School cool transom glazing'
BASE='School brown-grey basement stone'
CAP='School capstone and sill'
LEAD='School roof flashing'
DOOR='School dark service door timber'

def srgb(rgb):
    def linear(v):
        v=v/255.
        return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
    return [linear(v) for v in rgb]

PALETTE={k:{'color':srgb(c),'metallic':m,'roughness':r} for k,c,m,r in [
    (BRICK,(103,76,77),0,.90),(STONE,(174,153,128),0,.87),
    (LIP,(191,171,144),0,.84),(DARK,(123,101,84),0,.90),
    (IRON,(64,60,54),.30,.55),(GLASS,(85,103,108),.19,.31),
    (SKY,(105,119,123),.16,.35),(BASE,(146,125,107),0,.91),(CAP,(160,143,125),0,.89),
    (LEAD,(97,87,78),.25,.67),(DOOR,(58,52,45),0,.75)]}

class Front:
    def __init__(self,builder):
        self.builder=builder

    def box(self,name,material,x0,x1,y0,y1,z0,z1):
        assert x1>x0 and y1>y0 and z1>z0,name
        self.builder.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),
                         (x1-x0,y1-y0,z1-z0),material,label=name)

    def profile(self,name,material,polygon,y0,y1):
        if not polygon.is_empty:
            self.builder.prism(polygon,-y1,-y0,lambda x,z,d:(x,-d,z),material,name)

    def carved_line(self,name,mat,points,y,thickness,reach):
        polygon=LineString(points).buffer(thickness*.5,quad_segs=2,cap_style='round',join_style='round')
        self.profile(name,mat,polygon,y,y+reach)

def panes(front,name,opening,face,detail,recess=.235):
    face=face+.235-recess
    a,b,c,d=opening.bounds
    front.box(name+' glass',GLASS,a,c,face-.260,face-.235,b,d)
    front.profile(name+' steel frame',IRON,opening.difference(rect(a+.05,b+.05,c-.05,d-.05)),face-.236,face-.16)
    if detail:
        # Original steel casements have small operable lights and a shallow transom.
        front.box(name+' cold transom',SKY,a+.05,c-.05,face-.235,face-.2315,d-.29*(d-b),d-.05)
        w=.028
        lines=[rect((a+c-w)/2,b,(a+c+w)/2,d)]
        for h in (.32,.68):
            z=b+(d-b)*h
            lines.append(rect(a,z-w/2,c,z+w/2))
        front.profile(name+' glazing bars',IRON,unary_union(lines),face-.231,face-.193)

def stone_rib(front,name,x,half,face,z0,z1,detail):
    """Faceted slender cast-stone mullions carry through the spandrels."""
    reach=.171 if detail else .15
    vertices=[(x-half,face+.080),(x+half,face+.080),(x+half*.88,face+.135),
              (x+half*.43,face+reach),(x-half*.43,face+reach),(x-half*.88,face+.135)]
    front.builder.plan_prism(Polygon(vertices),z0,z1,STONE,name+' mullion')
    if detail:
        front.box(name+' fine arris',LIP,x-.018,x+.018,face+reach-.002,face+reach+.012,z0+.035,z1-.035)

def petal_points(x,z,width,height):
    # A lance-shaped leaf with a shallow centre ridge.
    return [(x,z-height*.5),(x+width*.42,z-height*.14),(x+width*.5,z+height*.12),
            (x,z+height*.5),(x-width*.5,z+height*.12),(x-width*.42,z-height*.14)]

def quatrefoil(x,z,r):
    # Four overlapping lobes yield a four-petal motif with concave notches.
    lobes=[]
    for k in range(4):
        a=k*pi/2
        from shapely.geometry import Point
        lobes.append(Point(x+cos(a)*r*.43,z+sin(a)*r*.43).buffer(r*.46,quad_segs=4))
    return unary_union(lobes)

def carved_spandrel(front,name,x,z,w,h,y,detailed):
    diamond=Polygon([(x,z+h/2),(x+w/2,z),(x,z-h/2),(x-w/2,z)])
    r=min(w,h)
    if detailed:
        front.profile(name+' diamond border',LIP,diamond.difference(diamond.buffer(-.043,join_style='mitre')),y,y+.038)
        clover=quatrefoil(x,z,r*.255)
        front.profile(name+' four lobes',DARK,clover,y+.002,y+.018)
        front.profile(name+' quatrefoil edge',STONE,clover.boundary.buffer(.019,quad_segs=2),y+.018,y+.049)
    else:
        front.profile(name+' carved panel',CAP,diamond.difference(diamond.buffer(-.065,join_style='mitre')),y,y+.052)

def shield(front,name,x,z,scale,y,detailed):
    pts=[(-.39,.49),(.39,.49),(.37,-.08),(.23,-.30),(0,-.49),(-.23,-.30),(-.37,-.08)]
    outer=Polygon([(x+a*scale,z+b*scale) for a,b in pts])
    front.profile(name+' shield',CAP,outer,y,y+.050)
    if detailed:
        front.profile(name+' rim',LIP,outer.difference(outer.buffer(-.038,join_style='mitre')),y+.046,y+.074)
        # The uncovered escutcheon shown in the restoration record bears a cross.
        cross=unary_union([rect(x-.055*scale,z-.20*scale,x+.055*scale,z+.28*scale),
                          rect(x-.20*scale,z+.03*scale,x+.20*scale,z+.14*scale)])
        front.profile(name+' raised cross',LIP,cross,y+.050,y+.078)

def vine(front,name,x,z,w,h,y,detailed):
    """Interpret the grape-and-vine relief documented at both gables."""
    field=Polygon([(x-w*.50,z),(x+w*.50,z),(x+w*.47,z+h*.67),(x,z+h),(x-w*.47,z+h*.67)])
    front.profile(name+' carved stone field',STONE,field,y,y+.055)
    if not detailed:
        front.profile(name+' inner field',CAP,field.buffer(-.10,join_style='mitre'),y+.055,y+.081)
        return
    from shapely.geometry import Point
    for side in (-1,1):
        path=[(x,z+h*.18),(x+side*w*.11,z+h*.40),(x+side*w*.30,z+h*.47),(x+side*w*.36,z+h*.64)]
        front.carved_line(name+' vine',DARK,path,y+.056,.043,.035)
        leaves=[Polygon(petal_points(x+side*w*.24,z+h*.51,w*.10,h*.22)),
                Polygon(petal_points(x+side*w*.38,z+h*.57,w*.08,h*.16))]
        front.profile(name+' leaves',LIP,unary_union(leaves),y+.057,y+.095)
        grapes=[]
        for row,cols in enumerate([3,2,1]):
            for col in range(cols):
                grapes.append(Point(x+side*w*.22+(col-(cols-1)/2)*.084,z+h*.37-row*.079).buffer(.047,quad_segs=4))
        front.profile(name+' grapes',CAP,unary_union(grapes),y+.057,y+.110)
