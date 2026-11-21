"""Black-tile street gate roofs at 133 Shangwen Road, in metres, Z up.

X runs east along the front wall at Y=0. The 2017 oblique view constrains
the rear silhouette. The present-day street photographs resolve the front
tile heads, staggered eaves and exposed square timber ends. The far side
uses the estimated gate depth and has no conjectural ridge ornament.
"""
from dataclasses import dataclass
from math import cos, pi, sin, sqrt


PAN = 'Longmen weathered pan tiles'
ROLL = 'Longmen charcoal cover tiles'
HEAD = 'Longmen grey fired tile ends'
BED = 'Longmen dark eave underside'
WOOD = 'Longmen dark timber'
END = 'Longmen weathered timber ends'
RIDGE = 'Longmen grey ridge mortar'
ROOF_MATERIALS = {
    PAN: {'color': [.137, .144, .143], 'roughness': .92},
    ROLL: {'color': [.186, .196, .194], 'roughness': .87},
    HEAD: {'color': [.35, .36, .34], 'roughness': .90},
    BED: {'color': [.088, .087, .079], 'roughness': .93},
    WOOD: {'color': [.145, .133, .109], 'roughness': .88},
    END: {'color': [.28, .265, .224], 'roughness': .9},
    RIDGE: {'color': [.235, .244, .232], 'roughness': .94},
}

FRONT = -1.06
BACK = 4.59
MID = 2.045

# Street tips are wider than the estimated rear eave in the elevated view.
STREET_EXTENTS = {'upper': (-2.77,2.77), 'west': (-3.73,-1.585), 'east': (1.585,3.73)}
STREET_CORNER_RISE = .18


@dataclass(frozen=True)
class Tier:
    name: str
    left: float
    right: float
    eave: float
    ridge: float
    lift: float
    tip: float
    cap_height: float
    left_hip: bool
    right_hip: bool
    rolls: int

    def roof(self, u, t, rear=False):
        """Follow a tile row from the street or rear eave to the ridge."""
        inset = .52 if self.name == 'upper' else .47
        eave_left,eave_right = (self.left,self.right) if rear else STREET_EXTENTS[self.name]
        left = (1.-t)*eave_left + t*(self.left+self.left_hip*inset)
        right = (1.-t)*eave_right + t*(self.right-self.right_hip*inset)
        edge = float(rear) * (BACK - FRONT) + FRONT
        flare = (self.left_hip * max(0., 1.-2.*u)**4
                 + self.right_hip * max(0., 2.*u-1.)**4)
        height = self.eave + (self.ridge-self.eave)*(.68*t+.32*t*t)
        eave_lift = self.lift if rear else self.lift+STREET_CORNER_RISE
        height += ((1.-t)*eave_lift + t*self.tip)*flare
        return (left+(right-left)*u, edge+(MID-edge)*t, height)

    def hip(self, s, t, right):
        """Exposed triangular end with eave tips rising at front and rear."""
        u = float(right)
        x, y, z = self.roof(u,t)
        back_x,back_y,_ = self.roof(u,t,True)
        front_lift = self.lift+STREET_CORNER_RISE
        side_lift = front_lift*max(0.,1.-2.*s)**4 + self.lift*max(0.,2.*s-1.)**4
        return (x+(back_x-x)*s, y+(back_y-y)*s, z+(1.-t)*(side_lift-front_lift))


TIERS = (
    Tier('upper', -2.32, 2.32, 12.86, 14.83, .61, .22, .30, True, True, 19),
    Tier('west', -3.43, -1.585, 11.49, 12.93, .54, .16, .26, True, False, 8),
    Tier('east', 1.585, 3.43, 11.49, 12.93, .54, .16, .26, False, True, 8),
)


def _add(a,b): return tuple(x+y for x,y in zip(a,b))
def _sub(a,b): return tuple(x-y for x,y in zip(a,b))
def _scale(a,s): return tuple(x*s for x in a)
def _dot(a,b): return sum(x*y for x,y in zip(a,b))
def _cross(a,b): return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def _unit(v): return _scale(v,1./sqrt(_dot(v,v)))
def _higher(p,d): return (p[0],p[1],p[2]+d)


def _grid(builder, rows, mat, name, exterior):
    size = len(rows[0])
    faces = []
    vertices = [p for row in rows for p in row]
    for j in range(len(rows)-1):
        for i in range(size-1):
            a = size*j+i
            face = [a,a+1,a+size+1,a+size]
            first,second,third = [vertices[k] for k in face[:3]]
            normal = exterior(j,i) if callable(exterior) else exterior
            if _dot(_cross(_sub(second,first),_sub(third,first)),normal) < 0:
                face.reverse()
            faces.append(face)
    builder.add(vertices,faces,mat,name)


def _sheet(builder, point, nx, ny, name):
    rows = [[point(i/nx,j/ny) for i in range(nx+1)] for j in range(ny+1)]
    lower = [[_higher(p,-.11) for p in row] for row in rows]
    _grid(builder,rows,PAN,name+' pans',(0,0,1))
    _grid(builder,lower,BED,name+' soffit',(0,0,-1))
    # On the roof edge the cut face shows a dark, shallow fascia.
    edge = rows[0]
    middle = point(.5,.5)
    outer = _sub(point(.5,0.),middle)
    _grid(builder,[edge,lower[0]],BED,name+' fascia',(outer[0],outer[1],0))


def _roll(builder, point, u, intervals, arc_count, label, radius, lapped):
    """Half-round cover tile over the continuous pan, with real lap shoulders."""
    rows = []
    profile_normals = []
    ts = []
    if lapped:
        # Two sections at every joint make the downhill tile lap stand proud.
        for k in range(intervals):
            t = .984*k/intervals
            ts.extend([(t,.012),(.984*(k+1)/intervals-.002,0.)])
    else:
        ts = [(.984*k/intervals,0.) for k in range(intervals+1)]
    for t,lip in ts:
        p = point(u,t)
        along = _unit(_sub(point(u,min(.999,t+.001)),p))
        side = _unit(_sub(point(u+.0005,t),point(u-.0005,t)))
        normal = _unit(_cross(side,along))
        if normal[2]<0:normal=_scale(normal,-1.)
        # Orthogonal to the tile axis, including the curve near the roof hips.
        side = _unit(_cross(along,normal))
        r = radius*(1.-.10*t)+lip
        row = []
        for a in range(arc_count+1):
            phi = pi*a/arc_count
            row.append(_add(p,_add(_scale(side,r*cos(phi)),_scale(normal,r*sin(phi)+.006))))
        rows.append(row)
        profile_normals.append([_add(_scale(side,cos(pi*(i+.5)/arc_count)),
                                     _scale(normal,sin(pi*(i+.5)/arc_count))) for i in range(arc_count)])
    _grid(builder,rows,ROLL,label,lambda j,i:profile_normals[j][i])


def _head(builder, point, inward, radius, lod, label):
    """A short round terminal normal to the last course, with a visible face."""
    direction = _unit(inward)
    side = _unit(_cross(direction,(0,0,1)))
    up = _unit(_cross(side,direction))
    center = _add(point,_add(_scale(direction,-.027),_scale(up,.020)))
    n = 8 if lod else 12
    vertices = []
    for depth,r in [(0.,radius),(.045,radius*1.04)]:
        for k in range(n):
            angle = 2*pi*k/n
            vertices.append(_add(center,_add(_scale(direction,depth),
                                             _add(_scale(side,r*cos(angle)),_scale(up,r*sin(angle))))))
    faces = [(i,(i+1)%n,n+(i+1)%n,n+i) for i in range(n)]
    faces += [tuple(reversed(range(n))),tuple(range(n,2*n))]
    # side x up points out of the eave. Its first polygon therefore faces out.
    faces = [tuple(reversed(f)) for f in faces]
    builder.add(vertices,faces,HEAD,label)


def _timber(builder, start, end, width, height, label, end_face=False):
    axis = _unit(_sub(end,start))
    side = _unit(_cross((0.,0.,1.),axis))
    up = _unit(_cross(axis,side))
    size = sqrt(_dot(_sub(end,start),_sub(end,start)))
    builder.box(_scale(_add(start,end),.5),(size,width,height),WOOD,
                basis=(axis,side,up),label=label)
    if end_face:
        builder.box(_add(end,_scale(axis,.004)),(.009,width*.95,height*.95),END,
                    basis=(axis,side,up),label=label+' tips')


def _eave_frame(builder, tier, rear, lod):
    end = BACK if rear else FRONT
    inside = -1. if rear else 1.
    edge = lambda u: tier.roof(u,0.,rear)
    name = tier.name+(' rear' if rear else ' street')
    samples = 8 if lod else 14
    purlins=[(.105,.19,.105,.10),(.32,.31,.105,.115)]
    if not rear:
        purlins.append((.72,.41,.135,.15))
    for y_offset,drop,width,height in purlins:
        points = [(edge(i/samples)[0],end+inside*y_offset,edge(i/samples)[2]-drop) for i in range(samples+1)]
        for p,q in zip(points,points[1:]):
            _timber(builder,p,q,width,height,name+' eave purlins')
    if tier.name=='upper':positions=(.255,.418,.582,.745)
    elif tier.left_hip:positions=(.56,.92)
    else:positions=(.08,.44)
    # Four prominent square ends above the central front, and two on each wing.
    # The back carries simpler framing, estimated from the high oblique image.
    for u in positions:
        x,_,z = edge(u)
        start=(x,end+.76*inside if rear else .27,z-.55)
        tip=(x,end-inside*.014,z-.22)
        _timber(builder,start,tip,.116,.13,name+' projecting squares',end_face=not rear)
    if not lod:
        for k in range(1,tier.rolls):
            u=k/tier.rolls
            x,_,z=edge(u)
            _timber(builder,(x,end+inside*(.38 if rear else .95),z-.20),(x,end+inside*.015,z-.15),
                    .058,.070,name+' close rafters')
    for right,exposed in [(False,tier.left_hip),(True,tier.right_hip)]:
        if not exposed:continue
        u=float(right);x,_,z=edge(u);d=1 if right else -1
        _timber(builder,(x-d*.54,end+inside*(.59 if rear else 1.18),z-.78),
                (x-d*.055,end+inside*.075,z-.22),.142,.16,name+' hip timbers',not rear)


def _ridge(builder,tier,lod):
    n=10 if lod else 20
    pts=[tier.roof(i/n,1.) for i in range(n+1)]
    for outer,lower,upper,material,label in [
        (.155,-.04,tier.cap_height*.78,RIDGE,'ridge bed'),
        (.174,tier.cap_height*.77,tier.cap_height,RIDGE,'ridge crest')]:
        front=[(x,y-outer/2,z+lower) for x,y,z in pts]
        rear=[(x,y+outer/2,z+lower) for x,y,z in pts]
        top_front=[(x,y-outer/2,z+upper) for x,y,z in pts]
        top_rear=[(x,y+outer/2,z+upper) for x,y,z in pts]
        _grid(builder,[front,top_front],material,tier.name+' '+label,(0,-1,0))
        _grid(builder,[rear,top_rear],material,tier.name+' '+label,(0,1,0))
        _grid(builder,[top_front,top_rear],material,tier.name+' '+label,(0,0,1))
        _grid(builder,[front,rear],material,tier.name+' '+label,(0,0,-1))
        for k,side in [(0,-1),(-1,1)]:
            _grid(builder,[[front[k],rear[k]],[top_front[k],top_rear[k]]],material,tier.name+' '+label,(side,0,0))


def add_roof(builder,lod=False):
    """Add the central raised roof, two lower roofs and exposed eave structure."""
    for tier in TIERS:
        for rear in (False,True):
            side = ' rear' if rear else ' street'
            name=tier.name+side
            point=lambda u,t: tier.roof(u,t,rear)
            _sheet(builder,point,12 if lod else 22,4 if lod else 7,name)
            for k in range(tier.rolls):
                u=(k+.5)/tier.rolls
                _roll(builder,point,u,4 if lod else 7,3 if lod else 5,name+' cover tiles',.069,not lod)
                p=point(u,0.)
                _head(builder,p,_sub(point(u,.015),p),.078,lod,name+' round tile heads')
            _eave_frame(builder,tier,rear,lod)
        for right,exposed in [(False,tier.left_hip),(True,tier.right_hip)]:
            if not exposed:continue
            name=tier.name+(' east hip' if right else ' west hip')
            point=lambda s,t: tier.hip(s,t,right)
            _sheet(builder,point,10 if lod else 18,4 if lod else 7,name)
            for j in range(15):
                u=(j+.5)/15
                _roll(builder,point,u,3 if lod else 5,2 if lod else 4,name+' cover tiles',.054,False)
            for rear in (False,True):
                steps=5 if lod else 11
                pts=[_higher(tier.roof(float(right),k/steps,rear),.067) for k in range(steps+1)]
                builder.tube(pts,.083,RIDGE,sides=6 if lod else 9,label=name+' raised arris')
        _ridge(builder,tier,lod)
