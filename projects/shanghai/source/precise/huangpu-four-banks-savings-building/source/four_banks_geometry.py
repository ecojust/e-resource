"""261 Sichuan Middle Road, street wings and the photographically documented corner."""
from math import cos, pi, sin
from shapely.geometry import LineString, Point, Polygon, box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from photo_architecture import Facade, opening

BRICK='dark Taishan face brick'; STONE='warm white marble'; LEDGE='carved limestone'
SASH='dark steel sash'; GLASS='recessed green glass'; BRONZE='dark bronze grille'
ROOF='weathered roof'; BACK='courtyard masonry'; DOOR='shadowed entrance doors'
PALETTE={
 BRICK:{'color':[.255,.152,.112],'roughness':.91},STONE:{'color':[.80,.77,.67],'roughness':.77},
 LEDGE:{'color':[.64,.60,.52],'roughness':.75},SASH:{'color':[.078,.075,.069],'metallic':.35},
 GLASS:{'color':[.12,.195,.194],'metallic':.24,'roughness':.32},BRONZE:{'color':[.238,.179,.105],'metallic':.52},
 ROOF:{'color':[.28,.265,.23],'roughness':.9},BACK:{'color':[.44,.405,.34],'roughness':.90},
 DOOR:{'color':[.16,.116,.08],'metallic':.22}}
# Both WGS84 map traces and the historic corner photograph put the octagonal
# projection on the southeastern splay. Two extra facets are within 0.3 m of the source chord.
SW=(-7.90,-18.77); S=(.25,-18.81); A=(2.70,-18.04); C=(6.45,-15.62); E=(8.54,-13.06)
# The northern party wall is pinned to the retained bank's decoded facade.
# The initial east end extended up to 0.15 m into that source.
NE=(8.22,17.77); NW=(-7.77,17.78)
BASE=Polygon([SW,S,A,C,E,NE,NW])
CORNERS=[S,A,C,E]
TOWER=[S,A,C,E,(7.50,-10.70),(4.98,-9.94),(1.57,-11.79),(-.48,-15.48)]
TOWER_PLAN=Polygon(TOWER)
TOP=41.8

def belt(f,z,h,width,mat=LEDGE):
    f.box(0,z,f.length+.04,h,width+.26,width/2-.12,mat,'continuous stone course')

def centered(f,count):
    return [(i+.5)*f.length/count-f.length/2 for i in range(count)]

def balustrade(f,u,z,w,lod):
    f.box(u,z+.90,w,.14,.27,.14,STONE,'balustrade coping')
    f.box(u,z+.12,w,.18,.32,.11,STONE,'balustrade plinth')
    gaps=max(2,round(w/(.48 if lod else .33)))
    for k in range(gaps):
        x=u-w/2+(k+.5)*w/gaps
        f.box(x,z+.48,.108,.65,.13,.12,STONE,'limestone baluster')
    for x in [u-w/2+.09,u+w/2-.09]:
        f.box(x,z+.48,.2,.80,.22,.12,STONE,'balustrade newel')

def glazed(f,p,lod,cols=2,rows=2):
    f.window(p,columns=cols,rows=rows if not lod else min(2,rows),frame=SASH,trim=False,glass=GLASS,label='inset steel casement')
    u,z,w,_=p.bounds[0],p.bounds[1],p.bounds[2]-p.bounds[0],p.bounds[3]
    f.box(u+w/2,z-.07,w+.19,.14,.35,.065,LEDGE,'drained projecting window sill')

def pierced_story(f,lo,hi,holes,material,lod,cols=2,rows=2):
    f.wall(lo,hi,holes,.4,material)
    for p in holes:glazed(f,p,lod,cols,rows)

def base_wall(f,count,lod,kind):
    w=f.length/count
    if kind=='portal':
        # The site photograph resolves two distinct arches, a recessed barrel with
        # coffers below and an almost semicircular radial fanlight over the lintel.
        width=f.length*.82;door=opening(0,.46,width,7.34,arch=width/2)
        fan=opening(0,8.14,width,2.37,arch=width*.43)
        f.wall(0,13,[door,fan],.7,STONE)
        f.prism(door.buffer(.012),-1.10,-1.02,DOOR,'recessed bank door plane')
        for k in range(1,10 if not lod else 6):
            n=10 if not lod else 6;x=width*(k/n-.5)
            rail=LineString([(x,.5),(x,8.1)]).buffer(.023,cap_style=2).intersection(door)
            f.prism(rail,-.63,-.58,BRONZE,'entrance grille bars')
        f.prism(fan.buffer(.012),-.42,-.39,GLASS,'dark fanlight')
        for i in range(1,12 if not lod else 8):
            a=pi*i/(12 if not lod else 8)
            rib=LineString([(0,8.15),(.55*width*cos(a),8.15+2.5*sin(a))]).buffer(.043,cap_style=2).intersection(fan)
            f.prism(rib,-.18,-.13,BRONZE,'sunburst fanlight')
        for o in [door,fan]:
            f.prism(o.buffer(.20,join_style=2).difference(o),-.04,.15,LEDGE,'entrance archivolt')
        f.box(0,7.99,width+.35,.25,.32,.06,STONE,'entrance letter fascia')
        for u in [-f.length/2+.1,f.length/2-.1]:
            f.box(u,6.23,.26,12.0,.32,.04,STONE,'portal jamb')
    else:
        holes=[]
        for u in centered(f,count):
            if kind=='flank':
                holes.extend([opening(u,1.12,w*.54,3.25),Point(u,6.55).buffer(w*.215,resolution=12 if not lod else 7),opening(u,9.10,w*.50,2.55)])
            else:
                holes.extend([opening(u,.55,w*.58,1.1),opening(u,2.55,w*.64,6.88),opening(u,10.32,w*.58,1.32)])
        pierced_story(f,0,13,holes,STONE,lod,2,3)
        if kind=='street':
            for i in range(count+1):
                u=(i-count/2)*w
                f.box(u,6.8,w*.18,11.8,.32,.10,STONE,'fluted marble pilaster')
                if not lod:
                    for d in [-.15,0,.15]:f.box(u+d,6.50,.026,10.45,.05,.27,LEDGE,'pilaster flute')
    for z,h,d in [(1.82,.17,.11),(12.48,.18,.26),(12.93,.28,.40)]:belt(f,z,h,d)

def street_face(b,a,c,num,lod,kind):
    f=Facade(b,a,c,kind);base_wall(f,num,lod,kind)
    if kind in ['portal','flank']:balustrade(f,0,12.99,f.length,lod)
    w=f.length/num
    for level in range(4):
        lo=13.13+4.48*level;hi=lo+4.48
        apertures=[opening(u,lo+.73,min(w*.62,3.15),2.92)for u in centered(f,num)]
        pierced_story(f,lo,hi,apertures,BRICK,lod,2,2)
        if kind=='portal'and level==2:balustrade(f,0,lo-.04,min(2.55,w*.80),lod)
    for z,h,d in [(30.94,.17,.22),(31.14,.23,.38)]:belt(f,z,h,d)
    apertures=[opening(u,31.72,min(w*.50,2.36),3.18,arch=min(.88,w*.24))for u in centered(f,num)]
    if kind in ['portal','flank']:
        apertures=[opening(0,31.71,w*.52,3.17)]
    pierced_story(f,31.05,35.66,apertures,STONE,lod,2,3)
    if kind in ['portal','flank']:
        upper=opening(0,36.22,w*.55,4.06,arch=w*.23)
        pierced_story(f,35.66,TOP,[upper],STONE,lod,2,3)
        if not lod:f.prism(upper.buffer(.14).difference(upper),.007,.18,LEDGE,'upper tower arch surround')
    else:
        belt(f,35.65,.21,.30)
        balustrade(f,0,35.75,f.length,lod)
    return f

def upper_tower(b,lod):
    for i,a in enumerate(TOWER):
        c=TOWER[(i+1)%len(TOWER)];f=Facade(b,a,c,'octagonal crown');w=f.length
        if i>=3:
            openings=[opening(0,36.2,min(1.3,w*.55),4,arch=.57)]
            pierced_story(f,35.55,TOP,openings,STONE,lod)
        r=min(.64,w*.22);z=44.05
        clover=unary_union([Point(x,zz).buffer(r,resolution=6 if lod else 12)for x,zz in [(0,z+.37),(0,z-.37),(-r*.60,z),(r*.60,z)]])
        f.wall(TOP,46.64,[clover],.34,STONE)
        f.prism(clover.buffer(.012),-.35,-.32,BRONZE,'quatrefoil dark backing')
        f.prism(clover.buffer(.11).difference(clover),.01,.12,LEDGE,'quatrefoil tracery')
        for u in [-w/2+.18,w/2-.18]:f.box(u,44.04,.24,3.53,.29,.06,LEDGE,'crown pilaster')
        for h,height,d in [(41.85,.35,.45),(42.20,.18,.26),(46.58,.23,.35)]:belt(f,h,height,d)
        f.wall(46.70,46.96,(),.27,STONE)
        finial=unary_union([box(-w*.26,46.92,w*.26,47.48),Point(0,47.42).buffer(min(w*.26,.98),resolution=8 if lod else 16).intersection(box(-w,47.41,w,48.65))])
        f.prism(finial,-.30,.02,STONE,'scalloped crown parapet')
    b.plan_prism(TOWER_PLAN,46.49,46.63,ROOF,'octagonal tower roof')
    center=TOWER_PLAN.centroid;b.plan_prism(center.buffer(.26,resolution=8),46.62,47.72,BRONZE,'flag standard foot')
    b.tube([[center.x,center.y,47.71],[center.x,center.y,49.99]],.035,BRONZE,8,'flag mast')

def add_building(b,lod):
    street_face(b,SW,S,2,lod,'street')
    for (a,c),role in zip(zip(CORNERS,CORNERS[1:]),['flank','portal','flank']):street_face(b,a,c,1,lod,role)
    street_face(b,E,NE,6,lod,'street')
    for a,c in [(NE,NW),(NW,SW)]:
        side=Facade(b,a,c,'shared party wall');side.wall(0,35.76,(),.28,BACK)
    # The strip of glazing sets back behind the first pale-storey balustrade.
    # Construct all returns from one closed footprint to match both roof slabs.
    attic=orient(BASE.buffer(-1.22,join_style=2).difference(TOWER_PLAN),sign=1.0)
    south=LineString([SW,S]);east=LineString([E,NE])
    for a,c in zip(list(attic.exterior.coords)[:-1],list(attic.exterior.coords)[1:]):
        f=Facade(b,a,c,'roof terrace setback')
        wall_mid=Point((a[0]+c[0])/2,(a[1]+c[1])/2)
        is_street=min(south.distance(wall_mid),east.distance(wall_mid))<1.24
        if is_street and f.length>2:
            num=max(1,round(f.length/3.5))
            holes=[opening(u,36.24,min(f.length/num*.83,2.99),2.98)for u in centered(f,num)]
            pierced_story(f,35.64,40.28,holes,STONE,lod,2,2);belt(f,40.21,.23,.26)
        else:f.wall(35.64,40.28,(),.28,BACK)
    b.plan_prism(BASE,0,.12,LEDGE,'ground floor')
    b.plan_prism(BASE.difference(TOWER_PLAN),35.55,35.73,ROOF,'terrace around corner tower')
    b.plan_prism(attic,40.09,40.28,ROOF,'upper roof behind parapet')
    upper_tower(b,lod)
