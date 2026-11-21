"""South garden front and western round return of the Libo Garden house."""
from math import ceil, cos, floor, hypot, pi, sin
from shapely.geometry import LineString, Point, Polygon, box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from photo_architecture import Facade

PLASTER = 'warm ivory roughcast'
TIMBER = 'dark red-brown exposed gable timber'
ROOF = 'red barrel clay tiles'
CAP = 'sunlit red clay corrugations'
JOINT = 'shadow under overlapping clay courses'
GLASS = 'recessed grey-green glass'
STEEL = 'dark steel casements'
SHUTTER = 'light grey louvered shutters'
DECK = 'terracotta garden paving'
COPING = 'pale concrete lintel and coping'
GRAVEL = 'gravelled terrace surface'
PALETTE = {m: {'color': co, 'roughness': r} for m,co,r in [
    (PLASTER,[.820,.754,.618],.95),(TIMBER,[.242,.124,.087],.87),
    (ROOF,[.420,.163,.106],.94),(CAP,[.503,.217,.139],.90),
    (JOINT,[.306,.117,.079],.97),(GLASS,[.219,.287,.294],.40),
    (STEEL,[.191,.207,.197],.65),(SHUTTER,[.688,.682,.600],.88),
    (DECK,[.505,.344,.272],.93),(COPING,[.791,.789,.724],.91),
    (GRAVEL,[.440,.457,.395],.98)]}

# The lower terrace and its stepped projecting wings coincide with the
# southern recesses of the source. Positive Y points into the building.
MAIN = box(-8.16,-5.90,11.84,8.39)
SOUTH_WING = box(5.48,-9.64,11.84,-5.68)
TERRACE = box(-5.28,-11.99,5.74,-5.68)
CORE = unary_union([MAIN,SOUTH_WING])
ARC_C = (-10.68,.25)
ARC_R = 2.70
WALK = .26
EAVE = 7.35


def window(face,u,z,w,h,cols,rows,label,glass=GLASS,sill=True):
    opening=box(u-w/2,z,u+w/2,z+h)
    if w<.24:
        face.prism(opening.buffer(.009,join_style=2),-.118,-.105,STEEL,label+' recessed fascia grille')
        for row in range(3):face.box(u,z+.11+row*.12,w-.018,.022,.05,-.075,SHUTTER,label+' grille slat')
        return opening
    face.window(opening,columns=cols,rows=rows,frame=STEEL,glass=glass,trim=False,label=label)
    # The shared casement has a deep stone sill. These painted steel windows
    # have a thin sill almost flush with the wall. The tall doors have none.
    face.builder.parts.pop()
    if sill:face.box(u,z-.035,w+.10,.068,.16,.025,COPING,label+' sill')
    return opening


class HouseWall(Facade):
    """Miter adjacent wall leaves so their end caps stay inside the shell."""
    def __init__(self,builder,a,c,prev,nxt,label):
        super().__init__(builder,a,c,label)
        def turn(p0,p1,p2):
            ax,ay=p1[0]-p0[0],p1[1]-p0[1];bx,by=p2[0]-p1[0],p2[1]-p1[1]
            return (ax*by-ay*bx)/(hypot(ax,ay)*hypot(bx,by))
        self.first_turn=turn(prev,a,c);self.last_turn=turn(a,c,nxt)

    def point(self,u,z,d=0):
        if d<0:
            if abs(u+self.length/2)<.000001: u-=d*self.first_turn
            elif abs(u-self.length/2)<.000001: u+=d*self.last_turn
        return super().point(u,z,d)


def walls(b,lod):
    coords=list(orient(CORE).exterior.coords)
    for i,(a,c) in enumerate(zip(coords,coords[1:])):
        f=HouseWall(b,a,c,coords[(i-1)%(len(coords)-1)],coords[(i+2)%(len(coords)-1)],'house exterior '+str(i));holes=[]
        x=(a[0]+c[0])/2;y=(a[1]+c[1])/2
        if abs(y+9.64)<.001:
            for z in (1.32,5.18):
                holes.append(window(f,0,z,4.36,1.52,4,2,'projecting southeast ribbon window'))
        elif abs(y+5.90)<.001:
            # The reopened upper doors sit behind the roof terrace.
            for xx,w in [(-2.95,2.28),(.40,1.83),(3.45,1.03)]:
                if min(a[0],c[0])+w/2<xx<max(a[0],c[0])-w/2:
                    h=2.02 if w>1.5 else .84;z=4.34 if h>1 else 5.32
                    holes.append(window(f,(xx-x)*f.t[0],z,w,h,2,2,'balcony opening'))
        elif abs(x+8.16)<.001:
            for yy in (-4.14,5.54):
                for z in (1.08,4.86):
                    holes.append(window(f,(yy-y)*f.t[1],z,1.65,1.67,2,2,'western casement'))
        elif f.length>3.0:
            count=max(1,round(f.length/4.05))
            for j in range(count):
                u=(j+.5)*f.length/count-f.length/2
                for z in (1.23,4.80):
                    holes.append(window(f,u,z,min(2.12,.62*f.length/count),1.56,2,2,'side or rear casement'))
        f.wall(WALK,EAVE,holes,thickness=.23,material=PLASTER)
    b.plan_prism(CORE,0,WALK,PLASTER,'grounded core plinth')


def terrace(b):
    coords=list(orient(TERRACE).exterior.coords)
    for i,(a,c) in enumerate(zip(coords,coords[1:])):
        f=HouseWall(b,a,c,coords[(i-1)%(len(coords)-1)],coords[(i+2)%(len(coords)-1)],'garden terrace');x,y=f.center[:2];holes=[]
        if abs(y+11.99)<.01:
            for j in range(5):holes.append(window(f,-4.31+2.05*j,.33,1.42,2.85,1,1,'tall glazed garden opening',sill=False))
            for j in range(6):
                u=-4.78+1.87*j
                holes.append(window(f,u,3.64,.16,.48,1,1,'narrow fascia slot',sill=False))
        elif x<0:
            for j in range(3):holes.append(window(f,-1.91+j*1.92,.36,.92,2.77,1,1,'western terrace opening',sill=False))
        f.wall(.26,4.27,holes,material=PLASTER,thickness=.20)
    b.plan_prism(TERRACE,0,.26,COPING,'terrace slab below tall glazing')
    b.plan_prism(TERRACE,3.95,4.04,GRAVEL,'accessible flat terrace above garden doors')
    b.plan_prism(TERRACE.buffer(.044,join_style=2).difference(TERRACE.buffer(-.17,join_style=2)),
                 4.25,4.36,COPING,'slim southern terrace parapet cap')
    for i in range(2):
        b.plan_prism(box(-5.40,-13.15+i*.38,11.89,-9.65),i*.12,(i+1)*.12,DECK,'low terrace and brick approach')


def plaster_gable(b,xmid,y,half,zbase,top,opening):
    face=Facade(b,(xmid-half,y),(xmid+half,y),'south-facing gable')
    outline=Polygon([(-half,zbase),(half,zbase),(0,top)])
    holes=[]
    if opening:
        holes=[window(face,0,zbase+.48,2.78,1.20,4,2,'central four-light attic window')]
    face.wall(zbase,top,holes,outline=outline,material=PLASTER,thickness=.22)
    # Thin three-dimensional timber strips stop at the sloping verge and at
    # the recessed window. The source shows a framed central four-light bay.
    bars=[]
    step=.72 if opening else .70
    for i in range(-ceil(half/step),ceil(half/step)+1):
        x=step*i;bars.append(box(x-.062,zbase,x+.062,top))
    bars.append(box(-half,zbase,half,zbase+.14))
    if opening:
        bars.extend([box(-1.51,zbase+.34,1.51,zbase+.48),box(-1.51,zbase+1.69,1.51,zbase+1.81)])
    bar_area=unary_union(bars).intersection(outline)
    if holes:bar_area=bar_area.difference(unary_union(holes).buffer(.01))
    face.prism(bar_area,-.014,.072,TIMBER,'exposed vertical timbers and rails')
    for end in (-half,half):
        face.line((end,zbase,.09),(0,top,.09),.095,TIMBER,7,'dark sloping bargeboard')


def roof_regions():
    """Return each roof face after cutting the valleys at equal elevations."""
    slopes=[]
    def gable(rect,axis,eave,apex,ridge):
        x0,y0,x1,y1=rect
        for lo,hi in [(True,False),(False,True)]:
            if axis=='x':
                side=x0 if lo else x1;m=(apex-eave)/(ridge-side);poly=box(x0 if lo else ridge,y0,ridge if lo else x1,y1)
                abc=(m,0.,eave-m*side)
            else:
                side=y0 if lo else y1;m=(apex-eave)/(ridge-side);poly=box(x0,y0 if lo else ridge,x1,ridge if lo else y1)
                abc=(0.,m,eave-m*side)
            slopes.append((poly,abc))
    gable((-8.60,-6.19,10.19,8.74),'x',7.35,11.32,.83)
    gable((5.22,-9.99,12.15,.86),'x',7.34,9.08,8.71)
    gable((.90,-2.64,12.15,8.74),'y',7.35,9.70,3.07)
    for i,(domain,abc) in enumerate(slopes):
        geom=domain
        for j,(other,high) in enumerate(slopes):
            if i==j:continue
            dx,dy,offset=(high[k]-abc[k] for k in range(3));length=hypot(dx,dy)
            if length<1e-7:
                if offset>0:geom=geom.difference(other)
                continue
            x=-offset*dx/(length*length);y=-offset*dy/(length*length);nx,ny=dx/length,dy/length;tx,ty=-ny,nx
            half=Polygon([(x+u*tx+v*nx,y+u*ty+v*ny)for u,v in [(-80,0),(80,0),(80,90),(-80,90)]])
            geom=geom.difference(other.intersection(half))
        yield geom,abc


def roof(b,lod):
    for i,(plan,abc) in enumerate(roof_regions()):
        if plan.area<.01:continue
        a,c,k=abc
        z=lambda x,y,d: (x,y,a*x+c*y+k+d)
        b.prism(plan,-.12,0,z,ROOF,'red roof plane '+str(i))
        if lod:continue
        # Convex crests of pan tiles run from ridge to eaves. Short dark
        # course joints stop between adjacent ribs and alternate each course.
        xmin,ymin,xmax,ymax=plan.bounds
        transverse=abs(a)>abs(c)
        lo,hi=(ymin,ymax)if transverse else(xmin,xmax)
        for j in range(floor(lo/.315),ceil(hi/.315)):
            at=j*.315
            ln=LineString([(-36,at),(36,at)])if transverse else LineString([(at,-36),(at,36)])
            part=plan.intersection(ln)
            for seg in [part] if part.geom_type=='LineString' else [v for v in getattr(part,'geoms',[]) if v.geom_type=='LineString']:
                if seg.length<.11:continue
                b.tube([z(x,y,.014) for x,y in (seg.coords[0],seg.coords[-1])],.038,CAP,6,'rounded barrel tile rib')
        lo,hi=(xmin,xmax)if transverse else(ymin,ymax)
        for j in range(floor(lo/.42),ceil(hi/.42)):
            at=j*.42
            stripe=(box(at-.010,-36,at+.010,36)if transverse else box(-36,at-.010,36,at+.010)).intersection(plan)
            if stripe.area>.01:b.prism(stripe,.001,.008,z,JOINT,'overlapping horizontal tile courses')
    for x,y0,y1,z in [(0.83,-6.19,8.74,11.32),(8.71,-9.99,-.85,9.08)]:
        b.tube([(x,y0,z+.012),(x,y1,z+.012)],.083,CAP,6 if lod else 10,'rounded ridge caps')
    plaster_gable(b,.83,-5.91,9.01,7.34,11.27,True)
    plaster_gable(b,8.71,-9.65,3.16,7.30,9.03,False)
    # The east end of the rear transverse roof has its own short gable.
    f=Facade(b,(11.835,-2.51),(11.835,8.32),'east transverse gable')
    f.prism(Polygon([(-f.length/2,7.33),(f.length/2,7.33),(.17,9.67)]),-.18,0,PLASTER,'transverse roof end')


def round_return(b,lod):
    """Western stair and entrance return with its own radial tile roof."""
    cx,cy=ARC_C;r=ARC_R;count=12 if lod else 24
    arc=[(cx+r*cos(pi/2+pi*j/count),cy+r*sin(pi/2+pi*j/count)) for j in range(count+1)]
    plan=Polygon([*arc,(-7.88,cy-r),(-7.88,cy+r)])
    lower_r=2.14
    inner=[(cx+.19+lower_r*cos(pi/2+pi*j/count),cy+lower_r*sin(pi/2+pi*j/count))for j in range(count+1)]
    lower=Polygon([*inner,(-7.88,cy-lower_r),(-7.88,cy+lower_r)])
    b.plan_prism(lower,0,3.60,PLASTER,'inset round stair core and open entrance recess')
    b.plan_prism(plan,3.60,3.70,COPING,'overhanging soffit of the round window')
    b.plan_prism(plan,3.70,4.6,PLASTER,'curved white sill below stair glazing')
    b.plan_prism(plan,6.43,7.06,PLASTER,'semicircular stair head below roof')
    for index,(a,c) in enumerate(zip(arc,arc[1:])):
        face=Facade(b,a,c,'round western stair')
        face.prism(box(-face.length/2,4.60,face.length/2,6.43),-.09,-.065,GLASS,'curved stair glass')
        if index%max(1,count//6)==0:face.box(-face.length/2,5.51,.065,1.82,.075,0,SHUTTER,'light stair mullion')
    for z in (4.96,5.39,5.83,6.27):
        b.tube([(*point,z)for point in arc],.024,SHUTTER,5 if lod else 8,'light horizontal louvres across round stair windows')
    # Shutters partly enclose the end lights in the west elevation. The
    # central glass and the ribs of the radial roof remain visible.
    for j in [0,1,len(arc)-3,len(arc)-2]:
        a,c=arc[j],arc[j+1]
        for z in [4.79+i*.14 for i in range(11)]:
            b.tube([(*a,z),(*c,z)],.025,SHUTTER,5 if lod else 7,'fine end shutter louvres')
    for y,k in [(cy+r,1),(cy-r,-1)]:
        f=Facade(b,(-7.90,y),(cx,y),'side of round return')if k==1 else Facade(b,(cx,y),(-7.90,y),'side of round return')
        op=window(f,0,4.62,1.83,1.72,2,2,'glazed return',sill=False)
        f.wall(4.60,6.43,[op],material=PLASTER,thickness=.17)
    cap_arc=[(cx+(r+.29)*cos(pi/2+pi*j/count),cy+(r+.29)*sin(pi/2+pi*j/count),7.12)for j in range(count+1)]
    ctr=(cx,cy,8.85)
    b.add([ctr,*cap_arc],[(0,i+1,i+2)for i in range(count)],ROOF,'fan-shaped tiled roof on the round return')
    for i,p in enumerate(cap_arc):
        if not lod or i%2==0:b.tube([ctr,p],.041,CAP,6,'radial barrel tile')
    for sign in [-1,1]:
        edge=cy+sign*(r+.29);points=[(cx,cy,8.85),(-7.52,cy,8.85),(-7.52,edge,7.12),(cx,edge,7.12)]
        if sign==-1:points.reverse()
        b.add(points,[(0,1,2,3)],ROOF,'roof return toward main house')
    b.plan_prism(plan.buffer(.11,join_style=1),6.98,7.07,TIMBER,'dark fascia below rounded eave')
    b.lathe((cx-.18,cy-2.20),[(0,.33),(.19,.38),(.22,.32),(3.59,.27),(3.70,.35)],COPING,16,'western entrance support')


def chimney(b,x,y,z):
    # Two deep apertures cut through the pale square chimney crown, as in
    # the overhead west elevation. A single tall prism would conceal them.
    w,d=(1.17,.91)if x<0 else(.84,.68)
    b.box((x,y,(z+7.35)/2),(w,d,z-7.35),PLASTER,label='roughcast chimney')
    for dx in [-w*.40,0,w*.40]:b.box((x+dx,y,z+.19),(w*.20,d,.38),PLASTER,label='chimney vent piers')
    b.box((x,y,z+.43),(w+.04,d+.05,.10),COPING,label='chimney vent cap')


def add_building(b,lod=False):
    walls(b,lod);terrace(b);roof(b,lod);round_return(b,lod)
    chimney(b,-6.45,.75,10.07)
    chimney(b,3.71,5.11,11.00)
