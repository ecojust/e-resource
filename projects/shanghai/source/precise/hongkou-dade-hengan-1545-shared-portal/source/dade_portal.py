"""Double lane nameboard at the 1545 North Sichuan Road passage, Shanghai."""
from pathlib import Path
from math import cos, sin, pi
import json
from shapely.geometry import Polygon, box, shape

WALL = 'warm grey cement'
PANEL = 'weathered grey name panel'
STONE = 'pale moulded stone'
JOINT = 'recessed grey joint'
INK = 'charcoal lane inscription'
GREEN = 'deep green address enamel'
WHITE = 'ivory enamel lettering'
IRON = 'weathered iron'
PALETTE = {name:dict(color=color,roughness=roughness) for name,color,roughness in (
    (WALL,[.38,.361,.303],.95), (PANEL,[.266,.262,.249],.94),
    (STONE,[.52,.495,.453],.92),(JOINT,[.236,.225,.20],.97),
    (INK,[.020,.021,.022],.81),(GREEN,[.020,.135,.094],.58),
    (WHITE,[.85,.85,.74],.76),(IRON,[.066,.068,.062],.82))}
HALF = 1.32
EXTENT = 1.87

def face(builder,profile,front,back,material,group):
    if not profile.is_empty:
        builder.prism(profile,-back,-front,lambda x,z,d:(x,-d,z),material,group)

def rect(b,left,bottom,right,top,front,back,material,name):
    face(b,box(left,bottom,right,top),front,back,material,name)

def shoulder(b,side,lod):
    # The deep straight top of the opening dies into a stepped and hollowed console at each end.
    divisions=5 if lod else 14
    points=[(HALF,2.19),(HALF-.052,2.19),(HALF-.052,2.225),
            (HALF-.092,2.225),(HALF-.092,2.26)]
    for i in range(divisions+1):
        theta=pi*i/(2*divisions)
        points.append((HALF-.092-.124*sin(theta),2.26+.144*(1-cos(theta))))
    points.extend([(HALF-.216,2.424),(HALF-.262,2.424),(HALF-.262,2.456),
                   (HALF-.315,2.456),(HALF-.315,2.50),(HALF,2.50)])
    silhouette=Polygon([(side*x,z)for x,z in points])
    face(b,silhouette,-.056,.38,STONE,'Coved return '+str(side))
    for z,w,front in [(2.204,.063,-.073),(2.434,.257,-.074),(2.476,.318,-.080)]:
        low,high=sorted((side*HALF,side*(HALF-w)))
        rect(b,low,z-.008,high,z+.008,front,.33,STONE,'Stepped edge '+str(side))

def leaf(b):
    # One partly open street grille is visible on the left. The right-hand portion is a through passage.
    left=-1.265
    right=-.236
    def depth(x):return .11+(x-left)*.17
    def line(x0,z0,x1,z1,r,label):
        b.tube([(x0,depth(x0),z0),(x1,depth(x1),z1)],r,IRON,8,label)
    for x in (left,right):
        line(x,.04,x,2.19,.026,'Gate outside uprights')
    for z in (.12,.83,1.22,1.70,1.96,2.145):
        line(left,z,right,z,.022 if z in (.12,2.145)else .012,'Gate rails')
    for i in range(1,8):
        x=left+i*(right-left)/8
        line(x,.12,x,2.19,.012,'Grille pickets')
        # An open oval sits between the two head rails.
        pts=[(x+.044*cos(i*pi/8),depth(x),2.053+.079*sin(i*pi/8))for i in range(17)]
        b.tube(pts,.008,IRON,6,'Open head loops')
    for z in (.34,1.80):
        line(left-.045,z,left+.04,z,.03,'Gate hinge straps')

def model(b,lod=False):
    for side in (-1,1):
        left,right=sorted((side*HALF,side*EXTENT))
        rect(b,left+.011,0,right-.011,3.21,.007,.477,JOINT,'Joint beds '+str(side))
        # Visible horizontal courses continue across the adjoining shop piers.
        levels=(0,.58,1.18,1.78,2.37,2.89,3.21)
        for index,(bottom,top) in enumerate(zip(levels,levels[1:])):
            rect(b,left,bottom+.006,right,top-.005,-.003,.47,WALL,'Pier course '+str(side)+' '+str(index+1))
        inner_left,inner_right=sorted((side*HALF,side*(HALF+.071)))
        rect(b,inner_left,0,inner_right,2.29,-.025,.48,STONE,'Narrow return '+str(side))
        shoulder(b,side,lod)
        # Both green plates sit on the flanking piers at the top of the visible leaf.
        cx=side*1.589
        rect(b,cx-.229,1.973,cx+.229,2.146,-.032,-.006,GREEN,'1545 enamel plate '+str(side))
        for xx in (cx-.219,cx+.219):
            for zz in (1.984,2.135):
                rect(b,xx-.006,zz-.006,xx+.006,zz+.006,-.040,-.031,IRON,'Plate fasteners')
    rect(b,-HALF,2.50,HALF,3.210,.012,.50,STONE,'Lintel to passage soffit')
    field=box(-HALF+.060,2.703,HALF-.060,3.158)
    frame=box(-HALF,2.679,HALF,3.182).difference(field)
    face(b,frame,-.046,.045,STONE,'Stone border around inset panel')
    rect(b,-HALF+.060,2.703,HALF-.060,3.158,-.026,.035,PANEL,'Inset nameboard field')
    for bottom,top,front in [(2.50,2.526,-.087),(2.526,2.570,-.071),(2.570,2.679,-.038),
                             (2.679,2.705,-.018),(3.158,3.182,-.034),(3.182,3.210,-.058)]:
        rect(b,-HALF,bottom,HALF,top,front,.11,STONE,'Nameboard ledge '+str(bottom))
    for item in json.loads(Path(__file__).with_name('letter-contours.json').read_bytes()):
        g=shape(item['geometry'])
        if item['material']==INK:
            g=g.buffer(.0028,quad_segs=2,join_style='round')
        if lod:g=g.simplify(.0011,preserve_topology=True)
        for part in getattr(g,'geoms',[g]):
            if isinstance(part,Polygon):
                face(b,part,item['front'],item['front']+.007,item['material'],item['group'])
    leaf(b)
