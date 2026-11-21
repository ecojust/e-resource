"""Garden veranda, timber clapboards and flared dormers of the 1898 Customs Club."""
from math import cos, hypot, pi, sin

from shapely.geometry import LineString, Polygon, box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

from photo_architecture import Facade, pieces

SIDING = 'weathered pale-grey horizontal boarding'
BOARD_EDGE = 'shadow at the clapboard lap'
TRIM = 'pale painted timber'
POST = 'cream-painted porch columns and brackets'
SASH = 'faded green painted wooden sash'
GLASS = 'recessed grey-green glazing'
PANEL = 'dull green door panel'
FLOOR = 'weathered porch boards'
MASONRY = 'grey stone and brick plinth'
SLATE = 'grey diamond-patterned roof sheets'
JOINT = 'weathered diamond-sheet joints'
HIP = 'oxidised reddish ridge flashing'
FASCIA = 'dark painted eave boards'
CAP = 'dark weatherproof flat roof'
PALETTE = {material:{'color':color,'roughness':roughness} for material,color,roughness in [
    (SIDING,[.705,.686,.647],.94),(BOARD_EDGE,[.532,.523,.499],.92),
    (TRIM,[.783,.769,.722],.88),(POST,[.858,.823,.734],.89),
    (SASH,[.236,.407,.336],.76),(GLASS,[.332,.439,.427],.46),
    (PANEL,[.282,.445,.359],.88),(FLOOR,[.419,.382,.322],.94),
    (MASONRY,[.555,.527,.478],.96),(SLATE,[.229,.241,.253],.95),
    (JOINT,[.174,.188,.200],.95),(HIP,[.386,.253,.199],.90),
    (FASCIA,[.202,.203,.195],.94),(CAP,[.155,.154,.151],.95)]}

VERANDA = .99
EAVE = 4.91
RIDGE = 8.33
RX, RY = 9.61, 8.30
AX, AY = 4.24, 3.24
CORE = box(-8.87,-5.11,8.87,7.59)
FRONT_ROOM = box(-2.03,-7.65,2.03,-5.05)


def roof_z(x,y):
    """Elevation of the four sloping panels at a plan coordinate."""
    rise = min((RX-abs(x))/(RX-AX),(RY-abs(y))/(RY-AY),1.)
    return EAVE + (RIDGE-EAVE)*rise


class TimberWall(Facade):
    """Close both ends of an inset timber wall at their exact adjoining miter."""
    def __init__(self,builder,loop,index,label):
        a,b=loop[index],loop[(index+1)%len(loop)]
        super().__init__(builder,a,b,label)
        def miter(p,q,r):
            ax,ay=q[0]-p[0],q[1]-p[1]
            bx,by=r[0]-q[0],r[1]-q[1]
            return (ax*by-ay*bx)/(hypot(ax,ay)*hypot(bx,by)+ax*bx+ay*by)
        self.first=miter(loop[index-1],a,b)
        self.last=miter(a,b,loop[(index+2)%len(loop)])

    def point(self,u,z,d=0):
        if d<0:
            if abs(u+self.length/2)<1e-7: u-=d*self.first
            elif abs(u-self.length/2)<1e-7: u+=d*self.last
        return super().point(u,z,d)


def opening(frame,u,z,width,height,columns=2,rows=2,door=False):
    aperture = box(u-width/2,z,u+width/2,z+height)
    frame.window(aperture,columns=columns,rows=rows,frame=SASH,glass=GLASS,trim=False,label='timber casement')
    frame.builder.parts.pop()  # Painted sills project a few centimetres.
    frame.box(u,z-.035,width+.11,.07,.14,.018,TRIM,'wood sill')
    if door:
        bottom = box(u-width/2+.085,z+.08,u+width/2-.085,z+height*.42)
        frame.prism(bottom,-.135,-.10,PANEL,'painted lower door panel')
    return aperture


def clad(frame,bottom,top,openings,lod):
    frame.wall(bottom,top,openings,thickness=.14,material=SIDING)
    clear = box(-frame.length/2+.045,bottom,frame.length/2-.045,top).difference(unary_union(openings))
    n = int((top-bottom)/.165)
    for i in range(1,n,2 if lod else 1):
        z = bottom+i*.165
        strip = clear.intersection(box(-frame.length/2,z,frame.length/2,z+.014))
        frame.prism(strip,.005,.020,BOARD_EDGE,'horizontal lap joint')


def rooms(builder,lod):
    ground = box(-8.89,-7.80,8.89,7.61)
    builder.plan_prism(ground,0,VERANDA,MASONRY,'one metre masonry plinth')
    builder.plan_prism(ground.buffer(.025,join_style=2),VERANDA,VERANDA+.035,FLOOR,'wood floor of veranda')
    shell = orient(CORE.union(FRONT_ROOM))
    corners=list(shell.exterior.coords)[:-1]
    for index,pt in enumerate(corners):
        f = TimberWall(builder,corners,index,'ground floor wall '+str(index))
        x,y=f.center[:2];holes=[]
        if abs(y+7.65)<.001:
            holes.append(opening(f,-.99,1.31,1.39,2.69,2,3,True))
            holes.append(opening(f,.98,1.56,1.19,2.13,2,2))
        elif abs(y+5.11)<.001:
            for u in (-f.length*.23,f.length*.22):
                holes.append(opening(f,u,1.46,1.23,2.48,2,3,abs(u-f.length*.22)<.001))
        elif abs(x)>8:
            for u in (-f.length*.26,0,f.length*.26):
                holes.append(opening(f,u,1.57,1.40,1.91,2,2))
        elif abs(y-7.59)<.001:
            for u in (-5.46,-.53,5.21): holes.append(opening(f,u,1.59,1.32,1.86))
        clad(f,VERANDA+.035,EAVE-.09,holes,lod)
        builder.box((*pt,(VERANDA+EAVE)/2),(.115,.115,EAVE-VERANDA-.03),TRIM,label='painted corner board')
    # The central stair and two sides of the deep garden veranda are open.
    stair=[(-9.42,0),(-7.80,0),(-7.80,.984)]
    for i in range(5,-1,-1):
        y=-7.80-(6-i)*.27
        stair.append((y,(i+1)*.164))
        if i: stair.append((y,i*.164))
    builder.prism(Polygon(stair),-.96,.96,lambda y,z,x:(x,y,z),MASONRY,'six connected garden steps')
    builder.box((0,-6.51,EAVE-.18),(17.94,3.16,.105),TRIM,label='pale underside of open porch')
    beam_y=-7.72
    builder.box((0,beam_y,4.52),(17.91,.26,.33),FASCIA,label='veranda head beam')
    for ix,x in enumerate([-8.70,-4.34,0,4.34,8.70]):
        builder.box((x,beam_y,2.72),(.31,.33,3.42),POST,label='square south post '+str(ix+1))
        for z,w,h in [(1.12,.40,.16),(4.17,.39,.095),(4.27,.49,.105),(4.37,.60,.10)]:
            builder.box((x,beam_y,z),(w,w,h),POST,label='stepped cap and foot of veranda post')
        # Short curved-looking stepped timber brackets below the head beam.
        for sign in [-1,1]:
            if x*sign>8:continue
            bracket=Polygon([(0,4.08),(.12,4.08),(.23,4.19),(.32,4.26),(.48,4.29),(.55,4.35),(0,4.35)])
            builder.prism(bracket,-.09,.09,lambda u,z,d:(x+u*sign,beam_y-sign*d,z),POST,'stepped bracket below porch beam')
    for x in (-8.70,8.70):
        builder.box((x,-6.45,4.52),(.25,2.68,.33),FASCIA,label='side return of veranda beam')


class Dormer:
    """One roof window, measured in its own front-facing frame."""
    def __init__(self,name,x,y,turn,width,depth,cap,apex,chamfer=0.,tower=False):
        self.name,self.x,self.y,self.cap,self.apex,self.tower=name,x,y,cap,apex,tower
        self.c,self.s=cos(turn),sin(turn)
        w,h=width/2,depth/2
        self.local=[(-w,h),(-w,-h+chamfer),(-w+chamfer,-h),(w-chamfer,-h),(w,-h+chamfer),(w,h)] if chamfer else [(-w,h),(-w,-h),(w,-h),(w,h)]
        self.plan=orient(Polygon([self.xy(u,v)for u,v in self.local]))
        self.front_y=-h

    def xy(self,u,v):
        return self.x+u*self.c-v*self.s,self.y+u*self.s+v*self.c

    def add(self,b,lod):
        local=self.local; plan=[self.xy(*p) for p in local]; roof_base=self.cap
        for i,(a,c) in enumerate(zip(plan,plan[1:]+plan[:1])):
            f=TimberWall(b,plan,i,self.name);bottom_start=roof_z(*a)-.06;bottom_end=roof_z(*c)-.06
            if self.tower: bottom_start=bottom_end=3.21
            wall=Polygon([(-f.length/2,min(bottom_start,roof_base-.055)),(f.length/2,min(bottom_end,roof_base-.055)),(f.length/2,roof_base),(-f.length/2,roof_base)])
            u,v=local[i];u2,v2=local[(i+1)%len(local)]
            front=abs(v-self.front_y)<.001 and abs(v2-self.front_y)<.001
            diagonal=len(local)>4 and abs(u-u2)>.02 and abs(v-v2)>.02
            bottom=max(bottom_start,bottom_end)+.055
            holes=[]
            if (front or diagonal or self.tower) and roof_base-bottom>.40 and f.length>.62:
                width=f.length*(.79 if front else .70); z=max(bottom,roof_base-(1.03 if self.tower else 1.21));height=roof_base-z-.095
                holes.append(opening(f,0,z,width,height,3 if front and f.length>1.8 else 2,2))
            f.prism(wall.difference(unary_union(holes)),-.095,0,SIDING,'roof-window cheek and front')
            height=roof_base-bottom_start
            if height>.12:
                b.box((*a,bottom_start+height/2),(.066,.066,height),TRIM,label=self.name+' corner trim')
        # Each little roof bends up at the corners. Sample the edge and bend
        # the roof surface towards its peak, continuing the historic hip caps.
        scale=1.17 if not self.tower else 1.15
        edge=[];corners=[];steps=5 if not lod else 3
        for i,(a,c) in enumerate(zip(local,local[1:]+local[:1])):
            for j in range(steps):
                f=j/steps;u=(a[0]*(1-f)+c[0]*f)*scale;v=(a[1]*(1-f)+c[1]*f)*scale
                x,y=self.xy(u,v);z=self.cap+.04+.20*abs(2*f-1)**1.7
                if j==0:corners.append(len(edge))
                edge.append((x,y,z))
        rings=[];n=5 if not lod else 3
        for j in range(n):
            t=j/n;r=[]
            for x,y,z in edge:
                r.append((x*(1-t)+self.x*t,y*(1-t)+self.y*t,z*(1-t)+self.apex*t-.18*sin(pi*t)))
            rings.append(r)
        size=len(edge);vertices=[v for ring in rings for v in ring];vertices.append((self.x,self.y,self.apex));faces=[]
        for j in range(n-1):
            for i in range(size):faces.append((j*size+i,j*size+(i+1)%size,(j+1)*size+(i+1)%size,(j+1)*size+i))
        for i in range(size):faces.append(((n-1)*size+i,(n-1)*size+(i+1)%size,len(vertices)-1))
        b.add(vertices,faces,SLATE,self.name+' upturned hipped cover')
        b.tube(edge+[edge[0]],.032,FASCIA,5,self.name+' eaves')
        for i in corners:b.tube([*(ring[i]for ring in rings),(self.x,self.y,self.apex)],.036,HIP,5,self.name+' flared hip flashing')


def openings():
    return [Dormer('south faceted dormer',0,-5.40,0,3.89,2.28,7.72,8.69,.58),
            Dormer('southeast slope window',6.83,-2.49,pi/2,2.38,1.76,7.60,8.10),
            Dormer('northeast slope window',6.83,2.50,pi/2,2.38,1.76,7.60,8.10),
            Dormer('western roof window',-6.79,.48,-pi/2,2.44,1.80,7.68,8.18),
            Dormer('northwest square turret',-7.67,5.68,-pi/2,2.17,2.03,7.44,8.95,tower=True)]


def roof(b,lod,dormers):
    outer=[(-RX,-RY),(RX,-RY),(RX,RY),(-RX,RY)]
    inner=[(-AX,-AY),(AX,-AY),(AX,AY),(-AX,AY)]
    holes=unary_union([d.plan for d in dormers]);flat=box(-AX,-AY,AX,AY)
    b.plan_prism(flat,RIDGE-.11,RIDGE,CAP,'flat central cap to truncated roof')
    for i in range(4):
        j=(i+1)%4;xy=[outer[i],outer[j],inner[j],inner[i]];panel=Polygon(xy).difference(holes)
        mapper=lambda x,y,z:(x,y,roof_z(x,y)+z)
        b.prism(panel,-.10,0,mapper,SLATE,'sloped sheet roof panel '+str(i))
        # Actual sheets read as overlapping diamonds, aligned with the eave.
        lines=[];spacing=.53 if not lod else .98
        for sign in [-1,1]:
            for line in range(-36,37):
                intercept=line*spacing
                seg=panel.intersection(LineString([(-18,sign*(-18)+intercept),(18,sign*18+intercept)]))
                for geom in getattr(seg,'geoms',[seg]):
                    if geom.geom_type=='LineString' and geom.length>.08:
                        lines.append(geom.buffer(.008 if not lod else .010,cap_style='flat'))
        if lines:
            # Intersecting roof joints are one surface, eliminating coplanar overlaps.
            joint=unary_union(lines).intersection(panel.buffer(-.020,join_style='mitre'))
            b.prism(joint,.002,.007,mapper,JOINT,'diamond sheet joints '+str(i))
        b.tube([(x,y,roof_z(x,y)+.018)for x,y in [outer[i],inner[i]]],.044,HIP,6,'hip flashing')
        b.tube([(*outer[i],EAVE-.070),(*outer[j],EAVE-.070)],.057,FASCIA,6,'continuous main eave')
    for d in dormers:d.add(b,lod)


def add_building(builder,lod=False):
    rooms(builder,lod)
    roof(builder,lod,openings())
