"""Model the photographed garden facade and stepped flat roofs of the west house."""
from math import cos, sin, pi, ceil, hypot
from shapely.geometry import LineString, Point, Polygon, box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from shapely.affinity import scale
from photo_architecture import Facade

PLASTER = 'pale warm-grey roughcast'
DECK = 'light painted concrete soffit'
STONE = 'grey terrazzo and plinth'
FLAT = 'weathered grey roof finish'
FRAME = 'charcoal steel window frames'
GLASS = 'smoked garden window glass'
BLOCK = 'pale stairwell glazing'
RAIL = 'garden balustrade dark metal'
PALETTE = {name:{'color':rgb,'roughness':rough} for name,rgb,rough in [
    (PLASTER,[.802,.793,.752],.93),(DECK,[.866,.854,.802],.85),
    (STONE,[.473,.476,.453],.88),(FLAT,[.519,.513,.477],.95),
    (FRAME,[.136,.143,.140],.64),(GLASS,[.243,.303,.310],.36),
    (BLOCK,[.397,.482,.474],.40),(RAIL,[.156,.154,.136],.60)]}

# The axial frame is fitted to the western flat roof on three dated imagery
# editions. East/north here denote the house axes, rotated 27.26 degrees.
GROUND = unary_union([box(-11.63,-4.58,7.02,5.05),box(6.82,-3.66,12.24,5.05),
                      box(-11.63,-6.36,-3.12,-4.44),box(-3.02,3.84,3.63,7.53)])
UPPER = unary_union([box(-11.63,-4.58,6.84,5.05),box(6.64,-3.66,12.24,5.05),
                     box(-11.63,-6.36,-5.37,-4.42),box(-3.02,3.84,3.63,7.53)])
BAY_CENTER = (1.00,-4.58)
BAY_RX, BAY_RY = 3.47, 2.18
BALCONY = Polygon([(-5.40,-4.01),(7.02,-4.01),(7.02,-6.82),(3.60,-7.51),
                   *[(-1.65+4.55*cos(-pi/2-i*pi/2/32),-5.0+3.00*sin(-pi/2-i*pi/2/32)) for i in range(33)],
                   (-6.20,-4.04)])
SHADE = unary_union([box(-3.90,-5.50,2.88,-4.00),
                     scale(Point(-.51,-5.55).buffer(1,32),3.39,1.55)])
FLOOR, CEILING, UPPER_CEILING = .69, 4.43, 8.58

def pane(face,x,z,w,h,columns,rows,label,glass=GLASS):
    aperture=box(x-w/2,z,x+w/2,z+h)
    # The repaired windows have a minimal flush sill. Reuse the shared glass
    # and frame, then replace its projecting historic stone sill locally.
    before=len(face.builder.parts)
    face.window(aperture,columns=columns,rows=rows,frame=FRAME,trim=False,glass=glass,label=label)
    sill=face.builder.parts[-1]
    assert len(face.builder.parts)>before and sill['label'].endswith(label+'-sill')
    face.builder.parts.pop()
    face.box(x,z-.035,w+.035,.060,.090,-.012,STONE,label+' flush sill')
    return aperture

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


def shell(b,plan,z0,z1,upper,lod):
    coords=list(orient(plan.simplify(.001)).exterior.coords)
    for i,(a,c) in enumerate(zip(coords,coords[1:])):
        face=HouseWall(b,a,c,coords[(i-1)%(len(coords)-1)],coords[(i+2)%(len(coords)-1)],
                       ('upper' if upper else 'lower')+' wall '+str(i+1))
        holes=[];mx=(a[0]+c[0])/2;my=(a[1]+c[1])/2;horizontal=abs(a[1]-c[1])<.005
        south_garden=horizontal and abs(my+4.58)<.005
        if south_garden and not upper:
            # The photo's curved bay is open to the room. The original front
            # plane stops at the two joints with its projecting glass wall.
            mid=(BAY_CENTER[0]-mx)*face.t[0]
            holes.append(box(mid-BAY_RX+.035,.74,mid+BAY_RX-.035,4.23))
            for x in [-2.75,5.27]:
                if min(a[0],c[0])+.7<x<max(a[0],c[0])-.7:
                    holes.append(pane(face,(x-mx)*face.t[0],.78,1.16,3.22,2,2,'tall glazed garden door'))
        elif south_garden and upper:
            # The recessed wall and its doors remain visible behind the rail.
            for x,w in [(-3.83,1.56),(-.37,1.69),(4.25,1.63)]:
                if min(a[0],c[0])+w/2<x<max(a[0],c[0])-w/2:
                    holes.append(pane(face,(x-mx)*face.t[0],4.69,w,2.67,2,2,'balcony door'))
        elif horizontal and my>7.5:
            holes.append(pane(face,0,z0+.24,4.94,z1-z0-.54,7 if not lod else 5,4 if not lod else 3,
                              'central stair glazing',BLOCK))
        elif face.length>3.1:
            wing=mx>6.7 and (not horizontal or my<0)
            slots=max(1,round(face.length/4.7));step=face.length/slots
            for j in range(slots):
                width=min(step-.60,3.71 if wing else 2.54)
                u=(j+.5)*step-face.length/2
                holes.append(pane(face,u,z0+.97,width,2.09,3 if (width>2.7 and not lod) else 2,2,'steel casement'))
        face.wall(z0,z1,holes,thickness=.24,material=PLASTER)
        if face.length>2.7 and not upper:
            face.beam(.35,.38,.065,STONE,label='low grey water table')


def bay(b,lod):
    steps=12 if lod else 20
    pts=[(BAY_CENTER[0]+BAY_RX*cos(pi+i*pi/steps),BAY_CENTER[1]+BAY_RY*sin(pi+i*pi/steps))for i in range(steps+1)]
    rings=Polygon(pts)
    b.plan_prism(rings,.66,1.13,PLASTER,'curved sill and lower parapet')
    b.plan_prism(rings,3.63,4.42,PLASTER,'curved head between glass and balcony')
    verts=[];faces=[]
    for a,c in zip(pts,pts[1:]):
        start=len(verts);verts.extend([(*a,1.12),(*c,1.12),(*c,3.64),(*a,3.64)])
        faces.append((start,start+1,start+2,start+3))
    b.add(verts,faces,GLASS,'curved garden bay glazed in narrow segments')
    for z in (1.12,3.06,3.63):
        b.tube([(*p,z)for p in pts],.052 if z==3.06 else .071,FRAME,6 if lod else 9,'curved steel head transom or sill')
    for j in range(0,steps+1,2):
        x,y=pts[j];b.tube([(x,y,1.10),(x,y,3.65)],.048,FRAME,6 if lod else 9,'vertical steel bay mullion')


def balcony(b,lod):
    b.plan_prism(BALCONY,4.30,4.66,DECK,'curved balcony deck and projecting soffit')
    outer=orient(BALCONY).exterior
    parapet=BALCONY.difference(BALCONY.buffer(-.19,join_style=2)).difference(UPPER.buffer(.06))
    b.plan_prism(parapet,4.65,5.45,PLASTER,'solid L-shaped parapet above the curved windows')
    boundary=outer.difference(UPPER.buffer(.14));parts=[boundary]if boundary.geom_type=='LineString'else list(boundary.geoms)
    for section in parts:
        if section.length<.24:continue
        path=list(section.coords);b.tube([(*u,5.87)for u in path],.036,RAIL,6 if lod else 9,'metal top rail')
        posts=max(1,ceil(section.length/1.58))
        for j in range(posts+1):
            p=section.interpolate(j/posts,normalized=True);b.tube([(p.x,p.y,5.44),(p.x,p.y,5.88)],.028,RAIL,5 if lod else 8,'rail upright')
        if not lod and section.length>5:
            for j in range(1,posts):
                p=section.interpolate((j-.5)/posts,normalized=True);v=section.interpolate((j-.5)/posts+.001,normalized=True)
                dx,dy=v.x-p.x,v.y-p.y;d=(dx*dx+dy*dy)**.5
                if d<.00001:continue
                for sign in (-1,1):
                    path=[(p.x+sign*dx/d*(.17+.14*cos(t*pi/7)),p.y+sign*dy/d*(.17+.14*cos(t*pi/7)),5.67+.13*sin(t*pi/7))for t in range(11)]
                    b.tube(path,.014,RAIL,5,'paired ornamental rail curves')
    b.plan_prism(SHADE,7.73,7.92,DECK,'thin tongue-shaped upper shelter')
    for x,y in [(-2.68,-5.71),(2.24,-5.67)]:
        b.tube([(x,y,4.62),(x,y,7.75)],.068,FRAME,8 if lod else 14,'slender supports to tongue canopy')
    for x,y in [(-4.75,-6.15),(6.29,-6.02)]:
        b.tube([(x,y,.53),(x,y,4.32)],.092,FRAME,8 if lod else 14,'garden loggia columns')
    if not lod:
        # Shallow square details read on the soffit in the repair photograph.
        for x in [-2.66,-1.88,-1.10,-.32,.46,1.24,2.02]:
            for y in [-6.19,-5.73]:
                if SHADE.covers(box(x-.09,y-.09,x+.09,y+.09)):
                    b.box((x,y,7.722),(.12,.12,.019),STONE,label='small canopy soffit inset')


def add_building(b,lod=False):
    approach=unary_union([GROUND,box(-5.4,-7.88,7.32,-4.32),scale(Point(-1.85,-6.47).buffer(1,24),4.12,2.08)])
    for i in range(3):
        shellplan=approach.buffer(.47-i*.20,join_style=1)
        b.plan_prism(shellplan,i*.18,(i+1)*.18,STONE,'garden terrace step '+str(i+1))
    b.plan_prism(GROUND,.52,FLOOR,PLASTER,'continuous low base')
    shell(b,GROUND,FLOOR,CEILING,False,lod);shell(b,UPPER,CEILING,UPPER_CEILING,True,lod)
    b.plan_prism(GROUND.buffer(.035),4.37,4.51,DECK,'slab between storeys');bay(b,lod);balcony(b,lod)
    b.plan_prism(UPPER,8.58,8.66,FLAT,'flat main roof');rim=UPPER.difference(UPPER.buffer(-.19,join_style=2))
    b.plan_prism(rim,8.66,9.03,PLASTER,'roof parapet on stepped perimeter')
    b.plan_prism(rim.buffer(.025),9.03,9.085,DECK,'cap of the roof parapet')
    stair=box(-2.88,3.70,3.48,7.40);b.plan_prism(stair,8.53,9.28,PLASTER,'raised stair bay seen in roof imagery')
    b.plan_prism(stair.buffer(.045),9.27,9.34,FLAT,'stair bay flat cap')
    # The two sides of the corner light read as one band under a shallow brow.
    for x,y in [(12.30,-2.92),(-11.66,3.80)]:
        b.tube([(x,y,8.92),(x,y,1.0),(x,y+.17,.81)],.055,FRAME,6 if lod else 9,'rainwater downpipe at return')
