"""Faceted curved bay, sheltered pointed door and wrought iron on the street-facing balcony."""
from math import atan2,cos,hypot,pi,sin
from shapely.geometry import Polygon,LineString,box
from shapely.ops import unary_union
from wuyi_fabric import DOOR,DARK,FRAME,GLASS,IRON,STONE,WALL,face,glazing,metric,slab,wall

DECK=2.84

def xat(u):return metric(u,616)[0]

def perimeter():
    # Ordered east to west as seen from the garden path, positive Y inward.
    # The east portion is straight, followed by a convex three-window bow.
    anchors=[(132,-.08),(132,-.98),(226,-.98),(244,-1.23),(269,-1.47),
             (298,-1.55),(328,-1.55),(355,-1.44),(381,-1.16),(381,-.06)]
    return [(3.70+(u-244.5769231)*(8.80+y)/392.6153846,y) for u,y in anchors]

def entrance(b,lod):
    xl,xr=xat(156),xat(224);left,right=xl+.14,xr-.14;centre=(xl+xr)/2
    opening=Polygon([(left,0),(right,0),(right,1.57),(right-.045,1.67),
                     (right-.15,1.77),(centre,1.89),(left+.15,1.77),(left+.045,1.67),(left,1.57)])
    outline=box(xl,-.015,xr,2.54)
    face(b,outline.difference(opening),-.89,-.62,STONE,'pointed stone entrance and jambs')
    lip=opening.buffer(.072,join_style='round').difference(opening).intersection(outline)
    face(b,lip,-.918,-.871,STONE,'pointed entrance moulded lip')
    face(b,opening,.24,.28,DARK,'open entrance inner shadow')
    # A swept stone bracket carries the straight east end of the balcony.
    edge=perimeter()[1][0];support=Polygon([(edge,DECK-.255),(xl+.07,DECK-.255),(xl+.07,1.57),
                                    (xl-.008,1.75),(xl-.095,1.98),(xl-.20,2.21),
                                    (edge+.16,2.49),(edge,2.57)])
    face(b,support,-.91,-.09,STONE,'curved left portal bearing')
    ring=opening.buffer(.119,join_style='round').difference(opening.buffer(.080,join_style='round')).intersection(outline)
    face(b,ring,-.925,-.884,STONE,'pointed entrance outer recessed bead')
    # The inner timber leaf is ajar on the east hinge in the 2025 view.
    hinge=(left+.019,-.60);end=(left+.33,.21);width=hypot(end[0]-hinge[0],end[1]-hinge[1]);
    wall(b,box(0,.025,width,1.66),hinge,end,0,.06,DOOR,'open timber door leaf')
    for j in range(4):
        for i in range(2):
            a=.055+i*width*.47;z=.11+j*.355;shape=box(a,z,a+width*.36,z+.27)
            wall(b,shape.difference(shape.buffer(-.021,join_style='mitre')),hinge,end,-.018,.005,FRAME,'door inset panel moulding')
    for i in range(2):
        slab(b,box(xl-.11,-1.41+i*.14,xr+.055,-.72),-.12+i*.06,-.060+i*.06,STONE,'entrance stone step')

def lower_bay(b):
    points=perimeter(); arc=[(xat(229),-.025),(xat(229),-.92),(xat(257),-1.23),(xat(285),-1.38),
                               (xat(313),-1.42),(xat(342),-1.32),(xat(372),-1.09),(xat(372),-.025)]
    for i,(a,c)in enumerate(zip(arc,arc[1:])):
        length=hypot(c[0]-a[0],c[1]-a[1]);skin=box(0,.025,length,DECK-.16)
        if i in (2,3,4):
            light=box(.063,.56,length-.063,1.94);surround=light.buffer(.096,join_style='mitre').intersection(skin)
            skin=skin.difference(surround);wall(b,surround.difference(light),a,c,-.046,.158,STONE,'lower bay stone window surround')
            glazing(b,light,a,c,.106,'lower bay light '+str(i-1),1,1)
            wall(b,box(0,.477,length,.55),a,c,-.105,.038,STONE,'lower bay sill')
        wall(b,skin,a,c,.005,.152,WALL,'lower curved bay face '+str(i+1))
    for a,c in zip(arc[1:-2],arc[2:-1]):
        length=hypot(c[0]-a[0],c[1]-a[1]);
        for x in (.22*length,.77*length):
            wall(b,box(x-.045,2.38,x+.045,2.61),a,c,-.076,.035,STONE,'small north balcony corbel')
    slab(b,Polygon(points),DECK-.25,DECK-.03,STONE,'north balcony faceted bearing slab')
    slab(b,Polygon(points).buffer(.044,join_style='mitre'),DECK-.09,DECK,STONE,'north balcony projecting nosing')

def iron_panel(b,a,c,i,lod):
    length=hypot(c[0]-a[0],c[1]-a[1]); z0=DECK+.085;z1=DECK+.92
    def put(shape,label):wall(b,shape,a,c,-.021,.017,IRON,'north balcony '+label)
    for z,h in [(z0,.048),(z1,.057),(z1-.142,.025)]:put(box(0,z,length,z+h),'rails')
    count=3 if i==1 else max(1,round(length/.76));span=length/count
    def line(points,width=.014):
        return LineString(points).buffer(width,cap_style='round',join_style='round',quad_segs=2)
    def curl(x,z,rx,rz,sx,sz):
        pts=[];steps=13 if lod else 25
        for k in range(steps):
            t=k/(steps-1);ang=1.76*pi*t
            pts.append((x+sx*rx*(.62+.62*(1-.75*t)*(-cos(ang))),
                        z+sz*rz*(.92*t+.66*(1-.76*t)*sin(ang))))
        return line(pts,.011)
    for j in range(count):
        l=j*span;r=(j+1)*span;mid=(l+r)/2;centre=(z0+z1-.142)*.5
        put(box(l,z0,l+.031,z1),'balusters')
        # A continuous row of paired, downward curls fills the narrow top frieze.
        for k in range(2):
            u=l+(k+.5)*span/2
            put(unary_union([curl(u,z1-.045,span*.16,.074,sign,-1) for sign in (-1,1)]),'top scrolls')
        scroll=(j==1 if i==1 else i in (0,2,3,6,8))
        if scroll:
            motifs=[curl(mid,centre,span*.33,.34,sx,sz)for sx in (-1,1)for sz in (-1,1)]
            motifs.extend([curl(mid,centre,span*.23,.18,sx,sz)for sx in (-1,1)for sz in (-1,1)])
            put(unary_union(motifs),'eight opposed C scrolls')
        else:
            left=l+.055;right=r-.045;bottom=z0+.067;top=z1-.17
            outer=box(left,bottom,right,top)
            ornaments=[outer.difference(outer.buffer(-.019,join_style=2))]
            for k in range(4):
                x=left+(right-left)*(k+.5)/4;spacing=(right-left)/4
                ornaments.append(box(x-.011,bottom+.060,x+.011,top-.070))
                for z in (bottom+.13,top-.13):
                    ornaments.append(Polygon([(x,z-.060),(x+.022,z-.020),(x+.027,z),(x+.015,z+.028),(x,z+.053),
                                              (x-.015,z+.028),(x-.027,z),(x-.022,z-.020)]))
                for z,sz in ((bottom+.114,-1),(top-.115,1)):
                    for sx in (-1,1):ornaments.append(curl(x,z,spacing*.36,.087,sx,sz))
            put(unary_union(ornaments),'four collared spindles and filigree')
    put(box(length-.035,z0,length,z1),'end balusters')

def add_north_balcony(b,lod):
    entrance(b,lod);lower_bay(b);points=perimeter()
    for i,(a,c)in enumerate(zip(points,points[1:])):iron_panel(b,a,c,i,lod)
