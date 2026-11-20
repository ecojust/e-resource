"""Street-facing roof and lower north return of the house in Lane 955."""
from math import ceil, floor
from shapely.geometry import Polygon, box, Point
from shapely.ops import unary_union
from photo_architecture import Facade

STUCCO = 'pale yellow roughcast'
WOOD = 'weathered brown joinery'
GLASS = 'grey casement glass'
TILE = 'weathered brown-red roof tiles'
TILE_EDGE = 'shadow under tile courses'
RIDGE = 'red-brown ridge caps'
STONE = 'pebbled grey base'
METAL = 'dark rainwater pipe'
PALETTE = {name: {'color': color, 'roughness': roughness} for name, color, roughness in [
    (STUCCO,[.735,.696,.576],.93), (WOOD,[.21,.169,.144],.86),
    (GLASS,[.240,.288,.307],.41),(TILE,[.435,.235,.177],.94),
    (TILE_EDGE,[.330,.188,.145],.96),(RIDGE,[.497,.286,.209],.90),
    (STONE,[.462,.446,.393],.92),(METAL,[.186,.180,.151],.71)]}

# Origin is the centroid of the base-map source. Positive Y faces the road.
BODY = box(-9.38,-4.50,9.42,8.70)
RETURN = box(5.15,6.74,11.08,14.55)
WALL_PLAN = unary_union([BODY,RETURN])
DORMERS = [(1.90,8.07),(7.14,7.56)]
EAVE = 7.55


def pane(face,u,z,w,h,lod,columns=2):
    aperture=box(u-w/2,z,u+w/2,z+h)
    face.window(aperture,columns=columns,rows=2 if lod else 3,frame=WOOD,glass=GLASS,trim=False,
                label='inset casement')
    return aperture


def walls(builder,lod):
    points=list(WALL_PLAN.exterior.coords)
    if not WALL_PLAN.exterior.is_ccw:points.reverse()
    for i,(a,b) in enumerate(zip(points,points[1:])):
        f=Facade(builder,a,b,f'outer wall {i+1}')
        low=BODY.boundary.distance(Point((a[0]+b[0])/2,(a[1]+b[1])/2))>.01
        height=5.94 if low else EAVE
        holes=[]
        if f.length>3.5:
            if low:
                # The north return presents a plain plaster front and
                # smaller paired side casements in the dated road views.
                if abs(a[0]-b[0])<.05 and f.length>4:
                    for u in (-1.15,1.15):
                        holes.append(pane(f,u,3.52,1.65,1.35,lod))
                else:
                    holes.append(pane(f,0,1.02,1.23,1.53,lod))
            else:
                slots=max(1,int(f.length/3.7))
                us=[(k+.5)*f.length/slots-f.length/2 for k in range(slots)]
                for k,u in enumerate(us):
                    if k==slots//2 and abs(a[1]-b[1])<.05 and a[1]>8:
                        holes.append(pane(f,u,.18,1.35,2.50,lod,2))
                    else: holes.append(pane(f,u,.93,1.04,1.65,lod))
                    holes.append(pane(f,u,4.30,1.30,1.64,lod))
        f.wall(.15,height,holes,material=STUCCO,thickness=.24)
        f.beam(.39,.42,.07,STONE,label='grey water table')
        f.beam(height-.10,.15,.11,WOOD,label='dark fascia under eaves')
    # The footprint merges the return into the house at ground height. Above
    # its lower roof the main house still has two short exposed wall planes.
    for a,b in [((9.42,8.70),(5.15,8.70)),((9.42,6.74),(9.42,8.70))]:
        face=Facade(builder,a,b,'upper wall above the return')
        face.wall(5.76,EAVE,[],material=STUCCO,thickness=.24)
        face.beam(EAVE-.10,.15,.11,WOOD,label='upper return fascia')
    builder.plan_prism(WALL_PLAN,0,.24,STONE,'foundation within wall outline')


def tiled_plane(builder,vertices,edge,top,material,label,lod,holes=()):
    a,b,c=vertices[:3]
    def surface(x,y):
        det=(b[0]-a[0])*(c[1]-a[1])-(c[0]-a[0])*(b[1]-a[1])
        dx=((b[2]-a[2])*(c[1]-a[1])-(c[2]-a[2])*(b[1]-a[1]))/det
        dy=((b[0]-a[0])*(c[2]-a[2])-(c[0]-a[0])*(b[2]-a[2]))/det
        return a[2]+dx*(x-a[0])+dy*(y-a[1])
    area=Polygon([(v[0],v[1])for v in vertices])
    if holes:area=area.difference(unary_union(holes))
    builder.prism(area,-.115,0,lambda x,y,d:(x,y,surface(x,y)+d),material,label)
    if lod:return
    # Closed clay courses on each pitched face. The cuts for the dormer
    # cheeks continue through the overlapping courses as well as the deck.
    ds=(b[0]-a[0],b[1]-a[1])
    horizontal=abs(ds[0])>=abs(ds[1])
    v0=(a[1] if horizontal else a[0]);v1=(top[1] if horizontal else top[0])
    count=max(2,ceil(abs(v1-v0)/.34))
    vertices=[];triangles=[]
    # Joints between individual pantiles terminate at each overlapping course.
    # Their shallow crests follow the roof pitch and stop short of openings.
    xmin,ymin,xmax,ymax=area.bounds
    umin,umax=(xmin,xmax) if horizontal else (ymin,ymax)
    for i in range(count):
        along0=v0+(v1-v0)*(i+.09)/count
        along1=v0+(v1-v0)*(i+.94)/count
        center=umin+(i%2)*.10
        while center<umax:
            vertices2=[(center-.012,along0),(center+.012,along0),(center+.012,along1),(center-.012,along1)]
            if not horizontal:vertices2=[(y,x)for x,y in vertices2]
            if area.covers(Polygon(vertices2)):
                if not Polygon(vertices2).exterior.is_ccw:vertices2.reverse()
                start=len(vertices)
                for x,y in vertices2:vertices.append((x,y,surface(x,y)+.013))
                triangles.extend([(start,start+1,start+2),(start,start+2,start+3)])
            center+=.31
    if vertices:builder.add(vertices,triangles,TILE_EDGE,label+' staggered tile joints')
    for i in range(1,count):
        u=v0+(v1-v0)*i/count
        band=box(-40,u-.026,40,u+.027) if horizontal else box(u-.026,-40,u+.027,40)
        strip=area.intersection(band)
        if strip.area>.018:
            builder.prism(strip,0.004,.029,lambda x,y,d:(x,y,surface(x,y)+d),TILE_EDGE,label+' tile courses')


def hip(builder,rect,ridge,z_eave,z_ridge,title,lod,voids=()):
    x0,y0,x1,y1=rect;left,right=ridge
    ll=(x0,y0,z_eave);lr=(x1,y0,z_eave);ur=(x1,y1,z_eave);ul=(x0,y1,z_eave)
    p=(*left,z_ridge);q=(*right,z_ridge)
    faces=[([ll,lr,q,p],p,()),([lr,ur,q],q,()),([ur,ul,p,q],p,voids),([ul,ll,p],p,())]
    for i,(vs,top,cut) in enumerate(faces):
        tiled_plane(builder,vs,vs[0],top,TILE,f'{title} pitch {i+1}',lod,cut)
    for a,b in [(ll,p),(ul,p),(lr,q),(ur,q),(p,q)]:
        builder.tube([a,b],.072 if lod else .096,RIDGE,6 if lod else 9,title+' rolled hips and ridge')


def dormer(builder,x,y,lod):
    hbase=8.25;shoulder=10.78;apex=11.95;half=1.03
    # The window is recessed in the gable wall under two small roof pitches.
    face=Facade(builder,(x+half,y),(x-half,y),'north-facing dormer')
    light=pane(face,0,8.66,1.30,1.73,lod)
    front=Polygon([(-half,hbase),(half,hbase),(half,shoulder),(0,apex),(-half,shoulder)])
    face.prism(front.difference(light),-.38,0,STUCCO,'gable pierced for sash')
    back=y-2.73;end=y+.22
    for sign in (-1,1):
        side_x=x+sign*half
        verts=[(side_x,y,hbase),(side_x,y,shoulder),(side_x,back,shoulder),
               (side_x,back,9.98)]
        if sign<0:verts.reverse()
        builder.add(verts,[(0,1,2,3)],WOOD,'dormer side cheek')
        roof=[(x+sign*(half+.18),end,shoulder+.07),(x+sign*(half+.18),back,shoulder+.07),
              (x,back,apex+.075),(x,end,apex+.075)]
        tiled_plane(builder,roof,roof[0],roof[2],TILE,'dormer gable slope',lod)
    builder.tube([(x,back,apex+.10),(x,end+.02,apex+.10)],.071,RIDGE,6,'dormer ridge cap')


def add_building(builder,lod=False):
    walls(builder,lod)
    # Raised part of each dormer occupies an actual opening in the roof.
    roof_holes=[box(x-.99,y-2.40,x+.99,y-.035)for x,y in DORMERS]
    hip(builder,(-9.85,-4.97,10.66,9.13),((-7.09,1.77),(7.29,1.77)),
        EAVE+.10,14.04,'main clay roof',lod,roof_holes)
    hip(builder,(4.83,6.62,11.42,15.02),((7.48,11.99),(9.63,11.99)),
        6.15,8.08,'lower north return',lod)
    for x,y in DORMERS:dormer(builder,x,y,lod)
    # Street frames in 2020 and 2021 show two offset pipe runs wrapping the
    # corner under the low roof. Their exact terminals disappear behind trees.
    for z,low,x0 in [(5.38,3.12,6.22),(4.94,2.68,6.90)]:
        path=[(x0,14.60,low),(x0,14.60,z-.18),(x0+.14,14.60,z),
              (10.98,14.60,z),(11.12,14.46,z-.10),(11.12,12.80,z-.10),
              (11.12,12.60,z-.25),(11.12,12.60,z-.96)]
        builder.tube(path,.036,METAL,5 if lod else 8,'exposed pipe and elbow on north return')
    for x in (5.18,11.02):
        builder.tube([(x,14.60,5.98),(x,14.60,.42),(x,14.42,.30)],.056,METAL,6 if lod else 9,'north return downpipe')
