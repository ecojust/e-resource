"""Flaring tiled roof and the photographed two-light shed dormer at Old No. 3.

X follows the courtyard frontage, Y runs into the house and Z is above the sill.
The canonical survey width is 8.40 m. The eave and wall-depth values can be
supplied independently for the host model. No photographic pixels are used.
"""
from bisect import bisect_right
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
TILE = 'Old No 3 | scalloped red clay tiles'
RIDGE = 'Old No 3 | ridge terracotta'
TIP = 'Old No 3 | rolled tile noses'
LAP = 'Old No 3 | weathered clay laps'
BOARD = 'Old No 3 | dark fascia'
SOFFIT = 'Old No 3 | warm eave soffit'
CHEEK = 'Old No 3 | pale dormer panels'
TIMBER = 'Old No 3 | casement timber'
L_GLASS = 'Old No 3 | shaded glass'
R_GLASS = 'Old No 3 | light glass'
METAL = 'Old No 3 | shed cover'
TAU = 2.0 * math.pi


def _color(rgb):
    return [((v / 255.0 + .055) / 1.055) ** 2.4 for v in rgb]


PALETTE = {
    key: {'color': _color(rgb), 'roughness': rough}
    for key, rgb, rough in (
        (RIDGE, (147, 87, 66), .91), (TIP, (151, 85, 63), .93), (LAP, (119, 72, 56), .95),
        (BOARD, (70, 49, 42), .82), (SOFFIT, (161, 145, 134), .9),
        (CHEEK, (179, 177, 166), .92), (TIMBER, (94, 59, 48), .76),
        (L_GLASS, (66, 65, 60), .32), (R_GLASS, (130, 143, 139), .34),
        (METAL, (123, 103, 91), .75),
    )
}
PALETTE[TILE] = dict(color=[1., 1., 1.], roughness=.92,
                     texture=str(HERE / 'old3-clay-tiles.png'))

# Inset by successive horizontal roof rings. Height is relative to the eave
# masonry, not the outside lip. The fractions and heights come from the
# calibrated left hip outline in the published courtyard view.
PROFILE = [(0., .33), (.079, .46), (.158, .59), (.295, .83), (.385, 1.),
           (.48, 1.25), (.55, 1.50), (.633, 1.77), (.72, 2.10),
           (.806, 2.44), (.888, 2.77), (1., 3.27)]


def make_texture():
    """A 0.72 × 0.72 m original repeat of four formed tiles and three laps."""
    from PIL import Image
    size = 192
    image = Image.new('RGB', (size, size))
    pix = image.load()
    for y in range(size):
        row = y // 64
        for x in range(size):
            col = x // 48
            t = (x % 48 + .5) / 48
            wave = .5 - .5 * math.cos(t * TAU)
            phase = (y % 64 + 4.0 * wave) % 64
            noise = 2.6 * math.sin(x * TAU / size * 53 + row) * math.cos(y * TAU / size * 23)
            patina = 4.7 * math.sin((x + y) * TAU / size * 5) + (col * 13 + row * 7) % 11 - 5
            seam = -12 * math.exp(-((t - .10) / .06) ** 2)
            nose = -31 if phase > 57 else (15 if 53 < phase < 57 else 0)
            grain = 9 * math.cos((t - .32) * TAU) + seam + noise + patina + nose
            pix[x, y] = tuple(round(v + grain * k) for v, k in [(163, 1.), (100, .82), (77, .75)])
    image.save(HERE / 'old3-clay-tiles.png', optimize=True)


def _cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def _vector(a, b):
    return tuple(x-y for x,y in zip(a,b))


def _surface(b, points, delta, material, name, uv=None):
    """Closed convex prism. Separate texture seams only, outward winding."""
    poly = list(points)
    nx = _cross(_vector(poly[1],poly[0]), _vector(poly[2],poly[0]))
    if sum(v*d for v,d in zip(nx,delta)) > 0:
        poly.reverse()
    bottom = [tuple(x+dx for x,dx in zip(p,delta)) for p in poly]
    count = len(poly)
    if uv is None:
        vertices = poly + bottom
        faces = [tuple(range(count)),tuple(reversed(range(count,2*count)))]
        faces.extend(((i+1)%count,i,count+i,count+(i+1)%count) for i in range(count))
        b.add(vertices,faces,material,name)
        return
    vertices,faces,tex = [],[],[]
    rings = [poly,list(reversed(bottom))]
    rings.extend([poly[(i+1)%count],poly[i],bottom[i],bottom[(i+1)%count]] for i in range(count))
    for j,ring in enumerate(rings):
        k = len(vertices)
        vertices.extend(ring)
        faces.append(tuple(range(k,k+len(ring))))
        if j < 2:
            tex.extend(uv(p) for p in ring)
        else:
            length = math.dist(ring[0],ring[1])/.72
            thick = math.dist(ring[1],ring[2])/.72
            tex.extend([(0.,0.),(length,0.),(length,thick),(0.,thick)])
    b.add(vertices,faces,material,name)
    # Old3Builder projects the physical 0.72 m repeat on its own split vertices.
    part=b.parts[-1]
    if not part.get('texcoords'):
        part['texcoords'] = tex


def _clip(points, x, keep_left):
    result=[]
    for a,c in zip(points,points[1:]+points[:1]):
        before = a[0] <= x if keep_left else a[0] >= x
        after = c[0] <= x if keep_left else c[0] >= x
        if before:
            result.append(a)
        if before != after:
            t=(x-a[0])/(c[0]-a[0])
            result.append(tuple(a[i]+t*(c[i]-a[i]) for i in range(3)))
    return result


def _box(b, x0,x1,y0,y1,z0,z1,mat,name):
    b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),
          (x1-x0,y1-y0,z1-z0),mat,label=name)


def _rolled_cap(b, start,end,radius,mat,name,detail):
    dx,dy,_ = _vector(end,start)
    length=math.hypot(dx,dy)
    if length < 1e-7:
        return
    normal=(-dy/length,dx/length)
    # The ridge cap is the upper part of a fired tube bedded on mortar.
    steps=7 if detail else 4
    rings=[]
    for i,t in enumerate((0.,.13,1.)):
        a=[start[k]+(end[k]-start[k])*t for k in range(3)]
        r=radius*(1.09 if i==0 else 1.)
        rings.append([(a[0]+normal[0]*r*math.cos(theta),a[1]+normal[1]*r*math.cos(theta),
                       a[2]+r*math.sin(theta)) for theta in [math.pi*k/steps for k in range(steps+1)]])
    verts=sum(rings,[]);n=steps+1
    faces=[tuple(reversed(range(n))),tuple(range(2*n,3*n))]
    for i in range(2):
        for j in range(n):
            k=(j+1)%n
            faces.append((i*n+j,i*n+k,(i+1)*n+k,(i+1)*n+j))
    b.add(verts,faces,mat,name)


def add_roof(b, lod=False, layout=None):
    """Assemble the measured roof around the host's width, depth and eaves."""
    cfg=layout or {}
    width,depth,eaves=(float(cfg.get('width',8.40)),float(cfg.get('depth',11.08)),
                       float(cfg.get('eaves',7.57)))
    scale=width/8.4
    def xyz(x,y,z):
        return (scale*x,scale*y,eaves+scale*z)
    back=depth/scale
    def box(x0,x1,y0,y1,z0,z1,mat,label):
        p,q=xyz(x0,y0,z0),xyz(x1,y1,z1)
        _box(b,p[0],q[0],p[1],q[1],p[2],q[2],mat,'Old3 '+label)
    def ring(t):
        i=max(0,min(len(PROFILE)-2,bisect_right([a for a,_ in PROFILE],t)-1))
        a,h=PROFILE[i];c,g=PROFILE[i+1]
        z=h+(g-h)*(t-a)/(c-a)
        left=-.64+2.49*t;right=8.4+.64-2.49*t;front=-.53+2.65*t;rear=back+.48-2.65*t
        return [xyz(left,front,z),xyz(right,front,z),xyz(right,rear,z),xyz(left,rear,z)]

    left,right=3.20,5.12
    face=.28
    end=1.88
    eave=-.53
    t_front=(face-.055-eave)/2.65
    t_end=(end-eave)/2.65
    breakpoints=sorted(set([t for t,_ in PROFILE]+[t_front,t_end]))
    for i,(first,last) in enumerate(zip(breakpoints,breakpoints[1:])):
        near,far=ring(first),ring(last)
        for side in range(4):
            j=(side+1)%4
            points=[near[side],near[j],far[j],far[side]]
            pieces=[points]
            if side==0 and first>=t_front-1e-7 and last<=t_end+1e-7:
                pieces=[_clip(points,left*scale,True),_clip(points,right*scale,False)]
            idx=0 if side%2==0 else 1
            def uv(p):
                across=p[idx]/scale/.72
                line=((p[1]/scale+.53) if side==0 else ((8.4+.64-p[0]/scale) if side==1 else
                      (back+.48-p[1]/scale) if side==2 else (p[0]/scale+.64)))
                return across, -(line+(.20 if side==2 else 0))/.72
            for k,piece in enumerate(pieces):
                if len(piece)>=3:
                    _surface(b,piece,(0.,0.,-.078*scale),TILE,
                             f'Old3 slope {side+1} band {i+1} piece {k+1}',uv)

    # The upper, steeper surface has distinct downturned tile ends. Courses
    # follow true developed slope length so the lower flare does not stretch
    # the tile spacing. The northern terrace image resolves about 15–17 laps.
    progress=[0.]
    for (t0,h0),(t1,h1) in zip(PROFILE,PROFILE[1:]):
        progress.append(progress[-1]+math.hypot(2.65*(t1-t0),h1-h0))
    def arclength_fraction(distance):
        i=max(0,min(len(progress)-2,bisect_right(progress,distance)-1))
        t0,t1=PROFILE[i][0],PROFILE[i+1][0]
        return t0+(t1-t0)*(distance-progress[i])/(progress[i+1]-progress[i])
    courses=round(progress[-1]/.25)
    for row in range(1,courses):
        if lod and row%2: continue
        t=arclength_fraction(progress[-1]*row/courses)
        tail=arclength_fraction(min(progress[-1],progress[-1]*row/courses+.076))
        lo,hi=ring(t),ring(tail)
        for side in range(4):
            j=(side+1)%4
            intervals=[(0.,1.)]
            if side==0 and t<t_end and tail>=t_front:
                u0=(scale*left-lo[0][0])/(lo[1][0]-lo[0][0])
                u1=(scale*right-lo[0][0])/(lo[1][0]-lo[0][0])
                intervals=[(0.,max(0.,u0)),(min(1.,u1),1.)]
            for piece,(start,finish) in enumerate(intervals):
                if finish-start<1.e-5:continue
                verts=[];faces=[]
                length=math.dist(lo[side],lo[j])/scale
                cells=max(1,round(length*(finish-start)/.18))
                ns=cells*(2 if lod else 4)
                for k in range(ns+1):
                    u=start+(finish-start)*k/ns
                    a=[x+(y-x)*u for x,y in zip(lo[side],lo[j])]
                    c=[x+(y-x)*u for x,y in zip(hi[side],hi[j])]
                    # The repeating edge sags slightly between side rolls.
                    bulge=(1+math.cos((u*length/.18+.12*(row%2))*TAU))/2
                    for deep,up in [(0.,.028+.019*bulge),(1.,.010),(.99,.002),(.02,.003)]:
                        pt=[x+(y-x)*deep for x,y in zip(a,c)]
                        pt[2]+=up*scale
                        verts.append(pt)
                faces.append((3,2,1,0))
                for k in range(ns):
                    for m in range(4):
                        q=(m+1)%4
                        faces.append((k*4+m,k*4+q,(k+1)*4+q,(k+1)*4+m))
                faces.append(tuple(ns*4+m for m in range(4)))
                b.add(verts,[tuple(reversed(f)) for f in faces],LAP,
                      f'Old3 roof {side+1} scalloped course {row}-{piece+1}')
    # A shallow closed upper cap represents the roof area hidden beyond the
    # documented break in pitch. It carries no inferred chimneys or roof lights.
    top=ring(1.)
    _surface(b,top,(0,0,-.09*scale),TILE,'Old3 upper roof cover',
             lambda p:(p[0]/scale/.72,p[1]/scale/.72))

    # Each visible roll is a closed tile with its lower lapped mouth enlarged.
    corners=[ring(t) for t,h in PROFILE]
    for side in range(4):
        for i,(r0,r1) in enumerate(zip(corners,corners[1:])):
            a,c=r0[side],r1[side]
            _rolled_cap(b,a,c,.072*scale,RIDGE,f'Old3 hip {side+1} cap {i+1}',not lod)
        a,c=top[side],top[(side+1)%4]
        n=max(1,round(math.dist(a,c)/(.35*scale)))
        for i in range(n if not lod else 1):
            pieces=n if not lod else 1
            start=tuple(x+(y-x)*i/pieces for x,y in zip(a,c))
            stop=tuple(x+(y-x)*(i+1)/pieces for x,y in zip(a,c))
            _rolled_cap(b,start,stop,.064*scale,RIDGE,f'Old3 crown {side+1} cap {i+1}',not lod)

    for side in range(4):
        r=ring(0.);a,c=r[side],r[(side+1)%4]
        # The outer face is darker than the masonry, and the underside returns
        # to the wall. The side-on photograph separates both bands clearly.
        inset=[(0,.49),(-.61,0),(0,-.45),(.61,0)][side]
        rear=lambda p,dd:(p[0]+inset[0]*scale*dd,p[1]+inset[1]*scale*dd,p[2]-.23*scale)
        pts=[a,c,rear(c,.15),rear(a,.15)]
        _surface(b,pts,(inset[0]*.10*scale,inset[1]*.10*scale,0),BOARD,f'Old3 edge {side+1} dark fascia')
        _surface(b,[rear(a,.12),rear(c,.12),rear(c,1.05),rear(a,1.05)],
                 (0,0,-.09*scale),SOFFIT,f'Old3 edge {side+1} soffit')
        # Physical scallops at the bottom course, where the profile reads
        # against the gutter. Each cell is a closed section of the same mesh.
        along=_vector(c,a);length=math.dist(a,c);n=round(length/(.18*scale))
        count=n*(5 if not lod else 3)
        vertices=[];faces=[]
        inward=[(0.,1.),(-1.,0.),(0.,-1.),(1.,0.)][side]
        for k in range(count+1):
            t=k/count;wave=(1+math.cos(t*n*TAU))*.5
            ex=a[0]+along[0]*t;ey=a[1]+along[1]*t;ez=a[2]+(.003+.023*wave)*scale
            for d,h in [(-.021,0.),(.125,.079),(.125,.056),(-.021,-.020)]:
                vertices.append((ex+inward[0]*d*scale,ey+inward[1]*d*scale,ez+h*scale))
        faces.append((3,2,1,0))
        for k in range(count):
            for m in range(4):
                q=(m+1)%4
                faces.append((k*4+m,k*4+q,(k+1)*4+q,(k+1)*4+m))
        faces.append(tuple(count*4+k for k in range(4)))
        b.add(vertices,[tuple(reversed(f)) for f in faces],TIP,f'Old3 edge {side+1} formed tile mouths')

    sill,head=1.13,2.23
    box(left-.035,right+.035,face-.097,face+.16,sill-.12,sill,TIMBER,'dormer projecting sill')
    box(left+.012,right-.012,face+.02,face+.10,sill-.146,sill-.12,BOARD,'dormer sill flashing')
    apron=[xyz(left,-.10,.687),xyz(right,-.10,.687),xyz(right,face-.04,sill-.145),xyz(left,face-.04,sill-.145)]
    _surface(b,apron,(0,0,-.035*scale),TILE,'Old3 dormer tiled apron',
             lambda p:(p[0]/scale/.72,p[1]/scale/.72))
    for x0,x1,name in [(left,3.62,'left'),(4.73,right,'right')]:
        box(x0,x1,face,face+.13,sill,head,CHEEK,'dormer '+name+' painted panel')
    # The clear courtyard image shows one glass area on either side of the
    # central meeting rail. The shadow across the left light is not a muntin.
    x0,x1=3.62,4.73;middle=4.155
    for x,name in [(x0,'west stile'),(x1,'east stile'),(middle,'meeting stile')]:
        box(x-.037,x+.037,face+.023,face+.112,sill,head,TIMBER,'dormer '+name)
    for z,name in [(sill+.036,'bottom rail'),(head-.042,'top rail')]:
        box(x0+.037,x1-.037,face+.024,face+.110,z-.036,z+.036,TIMBER,'dormer '+name)
    for low,high,material,name in [(x0+.037,middle-.037,L_GLASS,'left'),(middle+.037,x1-.037,R_GLASS,'right')]:
        box(low,high,face+.087,face+.11,sill+.073,head-.078,material,'dormer '+name+' glazing')
    # The cap is visibly deeper than the light. It dies into the steep upper
    # pitch, while the side is closed by the exposed triangular cheek.
    for x,sign,name in [(left,1.,'left'),(right,-1.,'right')]:
        outline=[xyz(x,face,sill),xyz(x,face,head+.12),xyz(x,end,2.85),xyz(x,end,2.80),
                 xyz(x,1.56,2.47),xyz(x,.75,1.25)]
        _surface(b,outline,(sign*.11*scale,0,0),CHEEK,'Old3 dormer '+name+' return')
    frontlip=-.10
    cover=[xyz(2.93,frontlip,2.40),xyz(5.37,frontlip,2.40),xyz(5.37,end,2.83),xyz(2.93,end,2.83)]
    _surface(b,cover,(0,0,-.052*scale),METAL,'Old3 dormer weathered cap')
    _surface(b,[(x,y,z-.052*scale) for x,y,z in cover],(0,0,-.074*scale),BOARD,'Old3 dormer cap edge')
    _surface(b,[(x,y,z-.126*scale) for x,y,z in cover],(0,0,-.044*scale),SOFFIT,'Old3 dormer underside')
    box(left-.018,right+.018,face+.012,face+.14,head,head+.105,SOFFIT,'dormer head lining')


if __name__=='__main__':
    make_texture()
