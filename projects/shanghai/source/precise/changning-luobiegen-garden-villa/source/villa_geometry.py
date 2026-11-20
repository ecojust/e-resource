"""Garden villa in metres. Local X follows the garden front, Y points into the house."""
from math import cos, sin, pi
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade, opening, pieces

PALETTE = {
    'lime plaster': {'color': [.84,.81,.71], 'roughness': .85},
    'dark Tudor timber': {'color':[.082,.064,.054], 'roughness':.72},
    'brickwork': {'color':[.51,.296,.211], 'roughness':.88},
    'warm cut stone': {'color':[.70,.64,.52], 'roughness':.84},
    'window leading': {'color':[.12,.128,.124], 'roughness':.52},
    'leaded glazing': {'color':[.21,.29,.29], 'roughness':.25,'metallic':.12},
    'terracotta roofing': {'color':[.43,.17,.091], 'roughness':.91},
    'weathered clay': {'color':[.37,.129,.072], 'roughness':.91},
    'ridge caps': {'color':[.52,.238,.136], 'roughness':.87},
    'stack brick': {'color':[.43,.301,.24], 'roughness':.9},
    'ironwork': {'color':[.115,.108,.09], 'roughness':.57,'metallic':.30},
    'deep shade': {'color':[.092,.087,.079], 'roughness':.95},
}
TIMBER='dark Tudor timber'; STUCCO='lime plaster'; EAVE=6.46


def member(f, p1, p2, width=.15, depth=.11, label='half timber'):
    band=LineString([p1,p2]).buffer(width/2,cap_style='flat')
    f.prism(band,.02,.02+depth,TIMBER,label)


def casement(f, cut, columns, rows, lod, label):
    x0,z0,x1,z1=cut.bounds
    f.prism(cut.buffer(.012,join_style=2),-.265,-.25,'leaded glazing',label+' glass')
    inside=cut.buffer(-.071,join_style=2)
    bars=[]
    for i in range(1,columns):
        x=x0+(x1-x0)*i/columns
        bars.append(box(x-.032,z0,x+.032,z1))
    for i in range(1,rows):
        z=z0+(z1-z0)*i/rows
        bars.append(box(x0,z-.032,x1,z+.032))
    if not lod:
        # Thin leading is visible in the 1998 garden view. Keep the principal sashes at distance.
        for i in range(columns):
            x=x0+(x1-x0)*(i+.5)/columns
            bars.append(box(x-.012,z0,x+.012,z1))
    f.prism(cut.difference(inside.difference(unary_union(bars))),-.226,-.17,'window leading',label+' sashes')
    f.box((x0+x1)/2,z0-.055,x1-x0+.12,.1,.24,-.03,'warm cut stone',label+' sill')


def garden_bay(f, peak, lod):
    w=f.length; half=w/2
    f.prism(Polygon([(-half,0),(half,0),(half,EAVE),(0,peak),(-half,EAVE)]).difference(unary_union([
        opening(0,.48,w*.51,2.18),opening(0,4.15,w*.75,1.54)])),-.34,0,STUCCO,'gable wall with openings')
    lower=opening(0,.48,w*.51,2.18); upper=opening(0,4.15,w*.75,1.54)
    ground=box(-half,0,half,3.30).difference(lower)
    f.prism(ground,.002,.015,'brickwork','exposed brick ground storey')
    casement(f,lower,3,2,lod,'hall casements');casement(f,upper,4,2,lod,'garden casements')
    for x in [-half+.14,half-.14]:f.box(x,4.87,.22,3.28,.21,.075,TIMBER,'corner post')
    for z,width in [(3.34,.23),(4.08,.14),(5.70,.17),(EAVE,.22)]:f.box(0,z,w,width,.20,.07,TIMBER,'horizontal timber')
    for x in [-half*.69,half*.69]:
        member(f,(x,3.42),(x,5.64),.14)
        member(f,(x*.94,5.74),(x*1.25,EAVE-.10),.15)
    for x in [-half*.72,0,half*.72]:
        apex=peak-abs(x)*(peak-EAVE)/half-.10
        if apex>EAVE:member(f,(x,EAVE+.08),(x,apex),.22 if x==0 else .14)
    for sign in [-1,1]:
        member(f,(0,EAVE+.17),(sign*half*.53,peak-(peak-EAVE)*.53-.19),.16)
        member(f,(sign*(half+.09),EAVE-.09),(0,peak+.12),.245,.19,'projecting bargeboard')
    # The photographed panels have a dark foiled pattern against the white stucco.
    for u in [-w*.30,0,w*.30]:
        center=3.69
        points=[(u,center-.26),(u+.09,center-.105),(u+.22,center-.07),
                (u+.16,center+.03),(u+.07,center+.035),(u+.13,center+.16),
                (u,center+.26),(u-.13,center+.16),(u-.07,center+.035),
                (u-.16,center+.03),(u-.22,center-.07),(u-.09,center-.105)]
        f.prism(Polygon(points),.031,.125,TIMBER,'pierced spandrel ornament')
        for side in [-1,1]:
            member(f,(u+side*.26,3.43),(u+side*.39,3.66),.056,.065,'spandrel brace')
    for u in [-.36*w,.36*w]:
        member(f,(u,EAVE+.08),(u,peak-(peak-EAVE)*.72-.13),.19,.145,'gable stud')
    f.builder.tube([f.point(0,peak+.10,.10),f.point(0,peak+.52,.10)],.055,TIMBER,5 if lod else 8,f.label+'/ridge finial')


def wall(f, windows, lod, upper=EAVE):
    cuts=[opening(x,z,w,h) for x,z,w,h in windows]
    f.prism(box(-f.length/2,0,f.length/2,upper).difference(unary_union(cuts)),-.34,0,STUCCO,'outer wall')
    base=box(-f.length/2,0,f.length/2,3.30).difference(unary_union(cuts))
    f.prism(base,.002,.014,'brickwork','lower brickwork')
    for i,(cut,(_,_,w,_)) in enumerate(zip(cuts,windows)):
        casement(f,cut,3 if w>2.0 else 2,2,lod,'casement '+str(i+1))
    f.box(0,3.31,f.length,.15,.16,.04,TIMBER,'storey beam')
    for x in [-f.length/2+.09,f.length/2-.09]:f.box(x,(upper+3.36)/2,.17,upper-3.36,.145,.05,TIMBER,'end post')


def balcony(f,lod):
    # Both storeys are recessed behind the two projecting garden gables.
    for x in [-f.length/2+.12,f.length/2-.12]:
        f.box(x,1.67,.26,3.34,.28,0,'brickwork','brick pier')
        f.box(x,4.91,.18,3.12,.19,0,TIMBER,'gallery post')
    f.box(0,3.24,f.length+.16,.22,1.68,-.7,TIMBER,'gallery floor with nosing')
    f.box(0,3.38,f.length+.10,.10,1.63,-.70,'warm cut stone','gallery floor surface')
    for z in [3.55,4.31]:f.box(0,z,f.length-.20,.07,.085,.003,'ironwork','balcony horizontal rail')
    for i in range(1,16 if not lod else 12):
        steps=16 if not lod else 12; x=-f.length/2+f.length*i/steps
        f.box(x,3.94,.038,.72,.043,.005,'ironwork','balcony picket')
        if not lod and i%2==0:
            curve=[f.point(x+.075*sin(t*pi/8),3.96+.17*cos(t*pi/8),.04) for t in range(17)]
            f.builder.tube(curve,.017,'ironwork',5,f.label+'/rail oval')
    f.box(0,EAVE-.12,f.length+.08,.21,.195,.03,TIMBER,'balcony header')


def north_gable(f,lod):
    half=f.length/2;peak=10.48
    upper=Polygon([(-half,EAVE),(half,EAVE),(0,peak)])
    f.prism(upper,-.34,0,STUCCO,'rear gable plaster')
    for s in [-1,1]:
        member(f,(s*half,EAVE),(0,peak+.05),.21,.15,'bargeboard')
        member(f,(0,EAVE+.08),(s*half*.59,peak-(peak-EAVE)*.59-.14),.17)
    member(f,(0,EAVE),(0,peak-.07),.19);f.box(0,EAVE,f.length,.18,.20,.06,TIMBER,'collar tie')


def south_facade(b,lod):
    west=Facade(b,(-7.45,-9.86),(-2.39,-9.86),'Garden/west gable')
    east=Facade(b,(1.68,-9.86),(7.84,-9.86),'Garden/east gable')
    garden_bay(west,10.67,lod);garden_bay(east,11.10,lod)
    center=Facade(b,(-2.39,-8.18),(1.68,-8.18),'Garden/recessed hall')
    wall(center,[(0,.14,2.34,2.70),(0,3.53,2.56,2.32)],lod)
    balcony(Facade(b,(-2.39,-9.78),(1.68,-9.78),'Garden/central balcony'),lod)
    for a,c in [((-2.39,-9.86),(-2.39,-8.18)),((1.68,-8.18),(1.68,-9.86))]:
        wall(Facade(b,a,c,'Garden/porch return'),[],lod)


def oriented_roof(x0,x1,y0,y1,eaves,peak,ridge_along_x):
    if ridge_along_x:
        mid=(y0+y1)/2;k=(peak-eaves)/(mid-y0)
        return [(box(x0,y0,x1,mid),(0,k,peak-k*mid)),(box(x0,mid,x1,y1),(0,-k,peak+k*mid))]
    mid=(x0+x1)/2;k=(peak-eaves)/(mid-x0)
    return [(box(x0,y0,mid,y1),(k,0,peak-k*mid)),(box(mid,y0,x1,y1),(-k,0,peak+k*mid))]


def upper_half_plane(a,b,c):
    length=(a*a+b*b)**.5
    if length<1e-8:return box(-100,-100,100,100) if c>0 else Polygon()
    nx,ny=a/length,b/length;tx,ty=-ny,nx;d=-c/length
    return Polygon([(nx*d+tx*t+nx*n,ny*d+ty*t+ny*n) for t,n in [(-150,0),(150,0),(150,300),(-150,300)]])


def roof(b,lod):
    sections=[(-7.74,8.12,-9.55,5.10,EAVE,10.60,True),
              (-7.74,-2.18,-10.12,.12,EAVE,10.82,False),
              (1.45,8.07,-10.13,.48,EAVE,11.25,False),
              (-5.58,6.76,2.68,9.91,EAVE,10.63,False),
              (7.62,13.13,-5.60,5.03,EAVE,8.52,True)]
    # The three photographed outer gables already have solid decorated walls.
    # Close the other roof ends where one pitch rises above the adjoining pitch.
    # Below their intersection the roof conceals the plain attic partition.
    ends=[(True,True),(False,True),(False,True),(True,False),(True,True)]
    for index,(section,closed) in enumerate(zip(sections,ends)):
        x0,x1,y0,y1,eave,peak,along_x=section
        span=y1-y0 if along_x else x1-x0
        face=Polygon([(-span/2,eave-.04),(span/2,eave-.04),(0,peak-.075)])
        for end,needed in enumerate(closed):
            if not needed:continue
            if along_x:
                x=x1-.25 if end else x0+.25
                line=((x,y0),(x,y1)) if end else ((x,y1),(x,y0))
            else:
                y=y1-.13 if end else y0+.13
                line=((x1,y),(x0,y)) if end else ((x0,y),(x1,y))
            wall=Facade(b,*line,f'Roof/gable end {index+1}.{end+1}')
            wall.prism(face,-.16,0,STUCCO,'attic infill')
    planes=[p for spec in sections for p in oriented_roof(*spec)]
    for i,(domain,plane) in enumerate(planes):
        a,c,d=plane;exposed=domain
        for j,(other,second) in enumerate(planes):
            if i==j or not domain.intersects(other):continue
            oa,oc,od=second;block=other.intersection(upper_half_plane(oa-a,oc-c,od-d))
            exposed=exposed.difference(block)
        if exposed.is_empty:continue
        mapper=lambda x,y,h:(x,y,a*x+c*y+d+h)
        b.prism(exposed,-.11,0,mapper,'terracotta roofing','Roof/intersecting pitch '+str(i+1))
        for poly in pieces(exposed):
            # Eave and valley edges follow their actual plane intersections.
            vertices=list(poly.exterior.coords)
            for p,q in zip(vertices,vertices[1:]):
                if abs(p[0]-q[0])+abs(p[1]-q[1])<.3:continue
                z0=a*p[0]+c*p[1]+d;z1=a*q[0]+c*q[1]+d
                if abs(z1-z0)<.012 and min(z0,z1)>8.1:
                    b.tube([mapper(*p,.018),mapper(*q,.018)],.085,'ridge caps',5 if lod else 9,'Roof/half-round ridge caps')
        if lod:continue
        step=.255 if a else .29
        for n in range(-48,58):
            v=n*step
            band=box(v,-22,v+.031,22) if a else box(-24,v,24,v+.029)
            strip=exposed.intersection(band)
            if strip.area>.012:b.prism(strip,.003,.016,mapper,'weathered clay','Roof/overlapping tile courses '+str(i+1))


def chimney(b,x,y,base,height,radius,lod,label):
    for z0,z1,r,material in [(base,height-.35,radius,'stack brick'),(height-.64,height-.53,radius+.045,'warm cut stone'),(height-.34,height-.12,radius+.085,'stack brick'),(height-.12,height,radius+.115,'stack brick')]:
        outer=Polygon([(x+r*cos(2*pi*i/8+pi/8),y+r*sin(2*pi*i/8+pi/8)) for i in range(8)])
        inner=Point(x,y).buffer(radius*.48,quad_segs=2)
        b.plan_prism(outer.difference(inner),z0,z1,material,label+'/masonry')
    b.plan_prism(Point(x,y).buffer(radius*.53,quad_segs=2),height-.39,height-.37,'deep shade',label+'/flue')
    if not lod:
        for i in range(max(0,int((height-1-base)/.33))):
            z=base+.33*i
            ring=Polygon([(x+(radius+.008)*cos(2*pi*j/8+pi/8),y+(radius+.008)*sin(2*pi*j/8+pi/8)) for j in range(8)])
            b.plan_prism(ring.difference(Point(x,y).buffer(radius*.85,quad_segs=2)),z,z+.017,'warm cut stone',label+'/brick courses')


def add_villa(b,lod):
    south_facade(b,lod)
    # Clockwise views from the garden. The later connecting strip to the west is outside the residence.
    outline=[(-7.45,-9.86),(-2.39,-9.86),(-2.39,-8.18),(1.68,-8.18),(1.68,-9.86),(7.84,-9.86),
             (7.84,-5.27),(12.85,-5.27),(12.85,4.70),(6.52,4.70),(6.52,9.62),(-5.36,9.62),(-5.36,4.72),(-7.45,4.72)]
    walls=[
        (5,[(-.28,.67,1.45,1.61),(.12,3.85,1.68,1.66)]),
        (6,[(0,.69,2.35,1.63),(0,3.64,3.89,2.15)]),
        (7,[(-2.43,.66,1.64,1.71),(.15,.65,1.66,1.71),(2.83,.65,1.65,1.71),(-2.32,3.73,1.88,1.95),(.04,3.73,1.83,1.95),(2.53,3.73,1.90,1.95)]),
        (8,[(-.66,.38,1.72,2.29),(-.65,3.72,1.97,1.96)]),
        (9,[(0,.64,1.64,1.68),(0,3.72,1.80,1.97)]),
        (10,[(-3.92,.67,1.53,1.65),(.0,.09,1.43,2.48),(3.76,.67,1.68,1.68),(-3.86,3.74,1.56,2.01),(0,3.50,2.36,2.42),(3.77,3.74,1.71,2.00)]),
        (11,[(.27,.66,1.47,1.67),(.27,3.71,1.69,1.91)]),
        (12,[]),
        (13,[(-4.86,.72,1.38,1.60),(-1.70,.73,1.72,1.57),(3.89,.65,1.70,1.76),(-4.76,3.78,1.62,1.72),(-1.82,3.78,1.73,1.78),(3.77,3.78,1.83,1.82)]),
    ]
    for index,windows in walls:
        f=Facade(b,outline[index],outline[(index+1)%len(outline)],'Residence/side '+str(index))
        wall(f,windows,lod)
        if index==10:north_gable(f,lod)
        if index in (7,13):
            for u in [-f.length*.25,.15*f.length]:member(f,(u,3.45),(u,6.36),.12)
    # Garden-facing oriel of the lower eastern wing, documented in the 1998 district photo.
    east=Facade(b,(7.84,-5.27),(12.85,-5.27),'Garden/eastern light room')
    for u in [-1.9,-.65,.65,1.9]:east.box(u,4.77,.16,2.36,.24,.095,'warm cut stone','oriel mullion')
    for z in [3.59,5.99]:east.box(0,z,4.49,.20,.32,.105,'warm cut stone','oriel frame')
    # A small north entrance porch, with the blocked door set back from its opening.
    rear=Facade(b,(2.45,10.45),(-1.85,10.45),'Rear/entrance')
    tip=4.68
    face=Polygon([(-2.15,0),(2.15,0),(2.15,2.82),(0,tip),(-2.15,2.82)])
    mouth=opening(0,.03,1.8,2.93,.91,10 if lod else 24)
    rear.prism(face.difference(mouth),-.36,0,STUCCO,'pointed entrance surround')
    rear.prism(mouth.buffer(.085).difference(mouth),.005,.06,'warm cut stone','arched stone trim')
    for s in [-1,1]:member(rear,(s*2.19,2.81),(0,tip+.08),.16,.10,'porch verge')
    for s in [-1,1]:b.box((.3+2.02*s,10.06,1.42),(.26,.86,2.84),STUCCO,label='Rear/porch return')
    for dom,(a,c,d) in oriented_roof(-1.98,2.58,9.48,10.62,2.85,4.83,False):
        b.prism(dom,-.095,0,lambda x,y,h:(x,y,a*x+c*y+d+h),'terracotta roofing','Rear/porch roof')
    b.plan_prism(Polygon(outline),0,.105,'warm cut stone','Residence/ground floor')
    b.plan_prism(Polygon(outline).buffer(-.21,join_style=2),3.11,3.22,'deep shade','Residence/first floor')
    roof(b,lod)
    chimney(b,11.92,.74,5.86,11.18,.50,lod,'Roof/east shaft')
    chimney(b,-2.93,2.98,7.28,11.42,.415,lod,'Roof/inner shaft')
    # The coarse owner also contains a long western connector. Set the native origin
    # at the main house itself so its camera and map anchor use the delivered span.
    for part in b.parts:
        part['vertices']=[(x-2.7,y,z) for x,y,z in part['vertices']]
