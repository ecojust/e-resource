"""Measured house envelope, wall openings and intersecting pitched roofs at 315 Xinhua Road."""
import math
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade as FlatFacade, opening, pieces

COLOURS = {
    'red garden brick':(.434,.210,.159), 'brick course':(.62,.42,.32),
    'bonded face brick':(.56,.29,.206), 'rough lime render':(.87,.841,.76),
    'dark oak framing':(.135,.115,.096), 'painted steel':(.172,.173,.153),
    'old casement glass':(.202,.253,.239), 'garden door glass':(.228,.301,.273),
    'recess shadow':(.145,.155,.144), 'weathered sandstone':(.616,.56,.478),
    'terracotta roof':(.485,.262,.166), 'tile edges':(.420,.205,.122),
    'old clay ridge':(.497,.251,.149), 'rainwater zinc':(.306,.304,.279),
    'chimney brick':(.63,.36,.243), 'balcony iron':(.225,.234,.218),
}
PALETTE={k:{'color':list(v),'roughness':.30 if 'glass' in k else .82} for k,v in COLOURS.items()}
WEST,EAST=-14.97,14.95
FRONT_GABLE=(-6.57,.25)
NORTH_GABLE=(-.77,5.60)
NORTH_WING=(-12.50,-4.90)
EAVE=7.80
MID_STOREY=3.84
MAIN_NORTH=12.03
WING_END=19.64


class Facade(FlatFacade):
    def prism(self,poly,back,front,material='limestone',label='wall'):
        if label!='continuous-open-wall':
            return super().prism(poly,back,front,material,label)
        # At a return, the back edge of the main-wall cap lies a little inside the
        # perpendicular exterior skin. This small bevel removes overlapping end planes.
        def point(u,z,d):
            if d<0 and abs(abs(u)-self.length/2)<1e-6:
                u-=math.copysign(min(-d,.235)*.09,u)
            return self.point(u,z,d)
        self.builder.prism(poly,back,front,point,material,self.label+'/'+label)


def sash(f, hole, cols, rows, lod, steel=False):
    x0,z0,x1,z1=hole.bounds
    f.prism(hole.buffer(.008,join_style='mitre'),-.286,-.266,
            'garden door glass' if steel else 'old casement glass','recessed glazing')
    inner=hole.buffer(-.068,join_style='mitre')
    bars=[box(x0+(x1-x0)*i/cols-.025,z0,x0+(x1-x0)*i/cols+.025,z1) for i in range(1,cols)]
    bars.extend(box(x0,z0+(z1-z0)*i/rows-.022,x1,z0+(z1-z0)*i/rows+.022) for i in range(1,rows))
    frame=hole.difference(inner.difference(unary_union(bars)))
    f.prism(frame,-.220,-.145,'painted steel' if steel else 'dark oak framing','casement frames and muntins')
    if not lod and z0>.25:
        f.box((x0+x1)/2,z0-.048,x1-x0+.145,.096,.213,.038,'weathered sandstone','window sills')


def front_edge(b,x0,x1,y,label):
    return Facade(b,(x0,y),(x1,y),label)


def north_edge(b,x0,x1,y,label):
    return Facade(b,(x1,y),(x0,y),label)


def wall(f,bottom,top,glazing,lod,material,extra=()):
    holes=[opening(u,z,w,h) for u,z,w,h,*_ in glazing]
    solid=f.wall(bottom,top,holes+list(extra),.235,material)
    for data,hole in zip(glazing,holes):
        sash(f,hole,data[4],data[5],lod,len(data)>6 and data[6])
    if material=='red garden brick' and not lod:
        # Narrow bed joints give the brick base a scale reference. Windows remain actual holes.
        bands=[]
        for i in range(math.ceil(bottom/.143), math.ceil(top/.143)):
            if i%2==0:
                z=i*.143
                bands.append(box(-f.length/2+.025,z,f.length/2-.025,z+.008))
        if bands:
            f.prism(solid.intersection(unary_union(bands)),.001,.005,'brick course','brick bedding')


def balcony(b,x0,x1,front,back,z,label,lod):
    b.box(((x0+x1)/2,(front+back)/2,z-.075),(x1-x0,back-front,.15),'weathered sandstone',label=label+'/projecting slab')
    lines=[((x0,back),(x0,front)),((x0,front),(x1,front)),((x1,front),(x1,back))]
    for a,c in lines:
        n=max(1,math.ceil(math.dist(a,c)/(.31 if lod else .19)))
        for i in range(n):
            u=i/n
            x,y=[s+(t-s)*u for s,t in zip(a,c)]
            b.box((x,y,z+.51),(.027,.032,1.01),'balcony iron',label=label+'/vertical pickets')
        for dz in [1.03,.15]:
            b.tube([(*a,z+dz),(*c,z+dz)],.032 if dz>.5 else .023,'balcony iron',6,label+'/continuous rails')


def timber(f,lines,holes=()):
    wood=unary_union([LineString([a,c]).buffer(w/2,cap_style='flat',join_style='mitre') for a,c,w in lines])
    if holes: wood=wood.difference(unary_union(holes))
    f.prism(wood,.003,.072,'dark oak framing','exposed timber framing')


def gable(f,lod,kind,peak):
    half=f.length/2
    if kind=='garden':
        lower=[(-1.64,.74,.92,2.07,2,3),(0,.74,1.09,2.07,2,3),(1.66,.74,.92,2.07,2,3)]
        upper=[(0,5.03,4.45,1.89,5,2),(0,9.87,1.58,1.74,3,2)]
        beams=[((x,MID_STOREY),(x,peak-abs(x)*(peak-EAVE)/half-.12),.225)
               for x in [-half+.10,-1.20,1.20,half-.10]]
        for z in [MID_STOREY+.11,5.0,7.02,8.17,9.73]:
            xmax=half if z<=EAVE else half*(peak-z)/(peak-EAVE)
            beams.append(((-xmax,z),(xmax,z),.17))
        for sign in [-1,1]:
            beams.append(((sign*(half-.07),EAVE),(0,peak-.13),.215))
    else:
        lower=[(-1.76,.08,.95,2.14,1,3)] if kind=='stair' else []
        upper=[(0,4.03,1.26,2.76,2,3),(0,9.18,1.16,1.36,2,2)]
        beams=[((x,MID_STOREY+.06),(x,peak-abs(x)*(peak-EAVE)/half-.14),.178)
               for x in [-half+.10,-.79,.79,half-.10]]
        for z in [MID_STOREY+.08,7.0,8.38]:
            xmax=half if z<=EAVE else half*(peak-z)/(peak-EAVE)
            beams.append(((-xmax,z),(xmax,z),.164))
        beams.extend([((s*(half-.06),EAVE),(0,peak-.10),.208) for s in (-1,1)])
    wall(f,0,MID_STOREY,lower,lod,'red garden brick')
    holes=[opening(u,z,w,h)for u,z,w,h,*_ in upper]
    outline=Polygon([(-half,MID_STOREY),(half,MID_STOREY),(half,EAVE),(0,peak),(-half,EAVE)])
    f.wall(MID_STOREY,peak,holes,.235,'rough lime render',outline=outline)
    for d,q in zip(upper,holes):sash(f,q,d[4],d[5],lod)
    timber(f,beams,holes)
    if kind=='garden':
        for s in (-1,1): f.line((0,peak+.015,.14),(s*(half+.24),EAVE-.13,.14),.103,'dark oak framing',6,'raking bargeboard')


def sidewall(b,x,y0,y1,top,label,lod,northwards=True,windows=(),timbers=False,base=MID_STOREY):
    a,c=(x,y0),(x,y1)
    f=Facade(b,a if northwards else c,c if northwards else a,label)
    lower=[s for s in windows if s[1]<base]
    upper=[s for s in windows if s[1]>=base]
    wall(f,0,base,lower,lod,'red garden brick')
    wall(f,base,top,upper,lod,'rough lime render')
    if timbers:
        timber(f,[((u,base),(u,top),.17) for u in [-f.length*.44,0,f.length*.44]]+
               [((-f.length/2,z),(f.length/2,z),.18) for z in [base+.10,top-.20]],
               [opening(*s[:4])for s in upper])
    return f


def elevations(b,lod):
    a,c=FRONT_GABLE
    gable(front_edge(b,a,c,-1.52,'south / projecting garden gable'),lod,'garden',14.25)
    west=front_edge(b,WEST,a,.90,'south / western bays')
    wall(west,0,MID_STOREY,[(-1.90,.65,1.27,1.98,2,3),(.06,.65,1.27,1.98,2,3),(1.98,.65,1.27,1.98,2,3)],lod,'red garden brick')
    upper=[(-2.38,4.53,1.16,1.95,2,2),(0,4.53,1.17,1.95,2,2),(2.4,4.53,1.16,1.95,2,2)]
    wall(west,MID_STOREY,EAVE,upper,lod,'rough lime render')
    timber(west,[((x,MID_STOREY),(x,EAVE),.17)for x in [-3.75,-1.23,1.23,3.75]]+
           [((-west.length/2,z),(west.length/2,z),.18) for z in [3.99,6.76,7.63]],
           [opening(*s[:4])for s in upper])
    for x,rev,depth in [(a,False,.90),(c,True,1.35)]:
        sidewall(b,x,-1.52,depth,EAVE,'garden gable / returns',lod,rev)
    east=front_edge(b,c,8.95,1.35,'south / garden room')
    wall(east,0,MID_STOREY,[(.07,.05,5.84,3.02,5,2,True)],lod,'red garden brick')
    series=[(-3.18,4.97,1.17,1.41,2,2),(-.99,3.90,.84,2.47,1,3),
            (1.05,3.90,.84,2.47,1,3),(3.30,4.97,1.20,1.41,2,2)]
    wall(east,MID_STOREY,EAVE,series,lod,'rough lime render')
    balcony(b,2.51,6.94,.30,1.45,MID_STOREY,'sitting room / balcony',lod)
    b.box((4.82,1.07,3.19),(6.15,.65,.15),'weathered sandstone',label='sitting room / garden door lintel')
    porch=front_edge(b,8.95,EAST,.21,'south / garden veranda arcade')
    bay=opening(.0,.0,4.92,2.84,.52,32)
    wall(porch,0,MID_STOREY,[],lod,'red garden brick',[bay])
    porch.prism(bay.buffer(.17,join_style='mitre').difference(bay).intersection(box(-3,0,3,3.39)),.005,.057,
                'bonded face brick','broad brick segmental arch')
    for i in range(1,16 if not lod else 8):
        n=16 if not lod else 8;t=i*math.pi/n
        x=2.46*math.cos(t);z=2.32+.52*math.sin(t)
        porch.line((x,z,.064),(x+.149*math.cos(t),z+.14*math.sin(t),.064),.007,'brick course',4,'arch joints')
    rear=front_edge(b,8.95,EAST,3.09,'south / recessed terrace wall')
    wall(rear,0,MID_STOREY,[(.18,.1,2.44,2.58,3,2,True)],lod,'red garden brick')
    wall(rear,MID_STOREY,EAVE,[(0,3.92,3.09,2.65,4,3)],lod,'rough lime render')
    balcony(b,8.97,EAST,.18,3.18,MID_STOREY,'eastern veranda / gallery',lod)
    for x in [8.99,EAST-.04]:
        b.box((x,.27,5.80),(.17,.18,3.85),'dark oak framing',label='eastern veranda / gallery posts')
    for x,ya,yb,rev,top in [(8.95,.21,3.09,False,MID_STOREY),(EAST,.21,3.09,True,MID_STOREY)]:
        f=Facade(b,(x,ya)if rev else(x,yb),(x,yb)if rev else(x,ya),'veranda / flanking brick')
        wall(f,0,top,[],lod,'red garden brick')
    sidewall(b,WEST,.90,MAIN_NORTH,EAVE,'west end / main range',lod,False,[(1.57,.76,.96,1.68,2,2),(-.64,4.75,1.08,1.68,2,2)],True)
    sidewall(b,EAST,3.09,MAIN_NORTH,EAVE,'east end / main range',lod,True,[(-1.56,.78,1.02,1.6,2,2),(.83,4.77,1.15,1.64,2,2)],True)
    # The north court photograph and the plan both distinguish two separate projecting gables.
    wa,wc=NORTH_WING;na,nc=NORTH_GABLE
    for lo,hi in [(WEST,wa),(wc,na),(nc,EAST)]:
        f=north_edge(b,lo,hi,MAIN_NORTH,'north street / recessed wall')
        count=3 if hi-lo>7 else 1
        centers=[(i-(count-1)*.5)*2.38 for i in range(count)]
        lower=[(u,.77,.96,1.63,2,2) for u in centers]
        upper=[(u,4.72,1.12,1.87,2,2) for u in centers]
        wall(f,0,MID_STOREY,lower,lod,'red garden brick')
        wall(f,MID_STOREY,EAVE,upper,lod,'rough lime render')
        timber(f,[((s*(f.length/2-.08),MID_STOREY),(s*(f.length/2-.08),EAVE),.15)for s in [-1,1]]+
               [((-f.length/2,z),(f.length/2,z),.18)for z in [3.94,6.92]], [opening(*d[:4])for d in upper])
    for lo,hi,face,peak,kind in [(wa,wc,WING_END,13.56,'western north wing'),(na,nc,13.64,12.16,'stair')]:
        gable(north_edge(b,lo,hi,face,'north / '+kind+' gable'),lod,kind,peak)
        for x,rev in [(lo,False),(hi,True)]:
            wins=[(-2.02,4.65,1.08,1.74,2,2),(.80,4.65,1.05,1.74,2,2)] if face-MAIN_NORTH>5 else []
            sidewall(b,x,MAIN_NORTH,face,EAVE,'north / '+kind+' returns',lod,rev,wins,True)
    floor=unary_union([box(WEST,.90,8.95,MAIN_NORTH),box(a,-1.52,c,3),
                       box(8.95,.21,EAST,MAIN_NORTH),box(wa,11.9,wc,WING_END),box(na,11.9,nc,13.64)])
    b.plan_prism(floor,.015,.083,'weathered sandstone','house / ground floor')


def upper_half_plane(a,b,c):
    """Return the part of the local site where a*x+b*y+c is positive."""
    square=[(-80,-80),(80,-80),(80,80),(-80,80)]
    points=[]
    for prev,curr in zip(square[-1:]+square,square):
        pv=a*prev[0]+b*prev[1]+c;cv=a*curr[0]+b*curr[1]+c
        if (pv>0)!=(cv>0):
            k=pv/(pv-cv)
            points.append((prev[0]+k*(curr[0]-prev[0]),prev[1]+k*(curr[1]-prev[1])))
        if cv>0:points.append(curr)
    return Polygon(points) if len(points)>=3 else Polygon()


def patch(name, vertices):
    (x0,y0,z0),(x1,y1,z1),(x2,y2,z2)=vertices[:3]
    dx,dy=x1-x0,y1-y0;qx,qy=x2-x0,y2-y0;det=dx*qy-dy*qx
    a=((z1-z0)*qy-dy*(z2-z0))/det;b=(dx*(z2-z0)-(z1-z0)*qx)/det
    return name,Polygon([(x,y) for x,y,_ in vertices]),(a,b,z0-a*x0-b*y0)


def roofing(b,lod):
    x0,x1,y0,y1=WEST-.46,EAST+.46,.0,12.53
    ry=6.11;ridge=12.36;eave=7.89
    sw,se,nw,ne=(x0,y0,eave),(x1,y0,eave),(x0,y1,eave),(x1,y1,eave)
    rw,re=(x0+3.12,ry,ridge),(x1-3.29,ry,ridge)
    patches=[patch('main southern roof',[sw,se,re,rw]),patch('main northern roof',[ne,nw,rw,re]),
             patch('west hip',[nw,sw,rw]),patch('east hip',[se,ne,re])]
    def crossroof(name,xleft,xright,tip,far,high):
        xl=xleft-.277;xr=xright+.277;xm=(xl+xr)/2
        for xedge in [xl,xr]:
            v=[(xedge,tip,eave-.04),(xm,tip,high+.18),(xm,far,ridge-.15),(xedge,far,eave-.04)]
            patches.extend([patch(name,v[:3]),patch(name,[v[0],v[2],v[3]])])
    crossroof('south timber gable',*FRONT_GABLE,-1.92,ry,14.25)
    crossroof('northwest wing gable',*NORTH_WING,WING_END+.39,ry,13.56)
    crossroof('north stair gable',*NORTH_GABLE,14.02,ry,12.16)
    # Subtract only the part above each plane. Roof courses stop at their real valley.
    for i,(name,extent,(a,sl,c)) in enumerate(patches):
        geom=extent
        for j,(_,other,(da,db,dc)) in enumerate(patches):
            if i==j or not extent.intersects(other):continue
            higher=upper_half_plane(da-a,db-sl,dc-c-1e-8)
            if not higher.is_empty:geom=geom.difference(higher.intersection(other))
        solid=unary_union([poly for poly in pieces(geom) if poly.area>.00001])
        if solid.is_empty:continue
        def mapper(x,y,d):return x,y,a*x+sl*y+c+d
        b.prism(solid,-.115,.0,mapper,'terracotta roof','roofs/'+name+' clay slope')
        grad=math.hypot(a,sl);gx,gy=a/grad,sl/grad;tx,ty=gy,-gx
        step=.34 if not lod else .59
        projected=[x*gx+y*gy for poly in pieces(solid)for x,y in poly.exterior.coords]
        for k in range(math.floor(min(projected)/step),math.ceil(max(projected)/step)+1):
            d=k*step
            xy=lambda t,n:(t*tx+n*gx,t*ty+n*gy)
            strip=Polygon([xy(-50,d),xy(50,d),xy(50,d+.024),xy(-50,d+.024)]).intersection(solid)
            for seg in pieces(strip):
                if seg.area>.0002:b.prism(seg,.002,.015,mapper,'tile edges','roofs/'+name+' tile courses')
            if not lod:
                transverse=[x*tx+y*ty for poly in pieces(solid) for x,y in poly.exterior.coords]
                for n in range(math.floor(min(transverse)/.32),math.ceil(max(transverse)/.32)+1):
                    # Alternating head joints separate the successive flat clay tiles.
                    t=(n+(k%2)*.5)*.32
                    face=Polygon([xy(t,d+.034),xy(t+.014,d+.034),xy(t+.014,d+step-.009),xy(t,d+step-.009)]).intersection(solid)
                    if face.area>.0007:
                        for poly in pieces(face):
                            from shapely.geometry.polygon import orient
                            from shapely import constrained_delaunay_triangles
                            verts=[];faces=[]
                            for tri in constrained_delaunay_triangles(poly).geoms:
                                base=len(verts);verts.extend(mapper(x,y,.0045) for x,y in list(orient(tri,1).exterior.coords)[:3])
                                faces.append((base,base+1,base+2))
                            b.add(verts,faces,'tile edges','roofs/'+name+' staggered head joints')
    for loc in [(rw,re)]:b.tube(loc,.105,'old clay ridge',8,'roofs/main ridge')
    for name,span,tip,high in [('garden',FRONT_GABLE,-1.92,14.25),('northwest',NORTH_WING,WING_END+.39,13.56),('stair',NORTH_GABLE,14.02,12.16)]:
        x=sum(span)/2
        b.tube([(x,tip,high+.19),(x,ry,ridge-.145)],.093,'old clay ridge',8,'roofs/'+name+' gable ridge')
    # Three shed dormers on the garden slope. Plane intersections set the cheek depth.
    def dormer(x,width,y,z,south,n):
        front=y;back=y+(2.00 if south else -2.00)
        edge=front_edge(b,x-width/2,x+width/2,y,'garden / shed dormer') if south else north_edge(b,x-width/2,x+width/2,y,'street / shed dormer')
        h=1.18
        hole=opening(0,z+.11,width-.38,.92)
        edge.wall(z-.14,z+h,[hole],.15,'dark oak framing')
        sash(edge,hole,n,2,lod)
        backz=z+1.60
        for side in [-1,1]:
            xx=x+side*width/2
            b.add([(xx,front,z-.16),(xx,front,z+h),(xx,back,backz),(xx,back,z+.23)],[(0,1,2,3)],'dark oak framing','dormers / timber cheeks')
        fy=front+(-.23 if south else .23);by=back+(.08 if south else -.08)
        roofplane=patch('shed roof',[(x-width/2-.20,fy,z+h+.10),(x+width/2+.20,fy,z+h+.10),
                                     (x+width/2+.20,by,backz+.09),(x-width/2-.20,by,backz+.09)])
        _,poly,(pa,pb,pc)=roofplane
        b.prism(poly,-.122,0,lambda u,v,d:(u,v,pa*u+pb*v+pc+d),'terracotta roof','dormers / projecting tiled shed caps')
    dormer(-11.27,2.51,1.74,9.12,True,3)
    dormer(4.54,5.56,1.77,9.14,True,6)
    dormer(11.67,1.30,1.51,9.01,True,2)
    dormer(7.49,3.66,10.88,8.88,False,4)


def chimney(b,lod):
    x,y=8.08,5.67;z0,z1=10.38,13.76
    mat='chimney brick';name='garden chimney/'
    b.box((x,y,(z0+z1)/2),(.79,.80,z1-z0),mat,label=name+'tall brick shaft')
    for i in range(3):
        z=z1-.15+i*.098
        b.box((x,y,z),(.85+(i%2)*.09,.86+(i%2)*.09,.09),mat,label=name+'corbelled courses')
    b.box((x,y,z1+.093),(.75,.71,.08),'recess shadow',label=name+'top flue')
    for xoff,yoff,w,d in [(0,-.355,.91,.10),(0,.355,.91,.10),(-.405,0,.10,.62),(.405,0,.10,.62)]:
        b.box((x+xoff,y+yoff,z1+.16),(w,d,.14),mat,label=name+'flue rim')
    for s in [-1,1]:
        b.box((x+s*.224,y-.413,z1-1.10),(.078,.074,1.86),mat,label=name+'brick ribs')
    if not lod:
        for i in range(1,24):
            b.box((x,y-.403,z0+i*.133),(.78,.010,.009),'brick course',label=name+'shaft joints')


def house(builder,lod):
    elevations(builder,lod)
    roofing(builder,lod)
    chimney(builder,lod)
