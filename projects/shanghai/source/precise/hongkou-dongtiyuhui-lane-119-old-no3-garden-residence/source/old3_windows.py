"""Garden-house window frames, radial transoms and twisted window columns from dated exterior photographs."""
from math import ceil, cos, pi, sin
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union


def finish(rgb, roughness, metal=0.):
    channels = [v/255. for v in rgb]
    return dict(color=[c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in channels],
                roughness=roughness, metallic=metal)


CASE='Old No 3 | deep umber outer frame'
WOOD='Old No 3 | reddish brown casement'
PANEL='Old No 3 | plum brown door panel'
SKY='Old No 3 | cool reflected glass'
TREE='Old No 3 | leaf shaded glass'
DARK='Old No 3 | shaded radial head'
IRON='Old No 3 | reddish iron grille'
BRASS='Old No 3 | dull brass handle'
STONE='Old No 3 | grey white spiral'
EDGE='Old No 3 | weathered shaft moulding'
PALETTE={CASE:finish((69,54,50),.68), WOOD:finish((100,71,66),.57),
         PANEL:finish((82,61,56),.63), SKY:finish((146,156,157),.27,.09),
         TREE:finish((82,106,91),.34,.09), DARK:finish((70,78,70),.47,.08),
         IRON:finish((122,83,76),.58,.36), BRASS:finish((145,129,91),.43,.46),
         STONE:finish((202,201,189),.84), EDGE:finish((182,182,172),.85)}


def _front(face):
    return face in ('front','garden','courtyard')


def _point(face,t,d,z,layout):
    if _front(face):
        return (t,d,z)
    if face in ('side','lane','left'):
        return (d,t,z)
    if face in ('rear','back'):
        return (t,float(layout['depth'])-d,z)
    raise ValueError(f'Photographic coordinates unavailable for {face!r}')


def _solid(b,face,l,poly,d1,d2,mat,label):
    sign=-1. if _front(face) else 1.
    bounds=sorted((sign*d1,sign*d2))
    b.prism(poly,*bounds,lambda t,z,v:_point(face,t,sign*v,z,l),mat,label)


def _head(c,r,sill,spring,top,n):
    p=[(c-r,sill),(c+r,sill)]
    p.extend((c+r*cos(pi*i/n),spring+(top-spring)*sin(pi*i/n)) for i in range(n+1))
    return Polygon(p)


def _strip(points,width):
    return LineString(points).buffer(width/2,cap_style=2,join_style=2)


def _ornamental_grille(b,face,l,c,w,lo,hi,d,tag,lod):
    """Two stacked registers of opposed C scrolls, with through openings."""
    x0=c-w/2; x1=c+w/2
    thick=.012*w; n=6
    rails=[.05,.11,.46,.51,.55,.88,.94]
    parts=[box(x0,lo+(hi-lo)*v-thick/2,x1,lo+(hi-lo)*v+thick/2)for v in rails]
    pitch=w/n
    for i in range(n+1):
        x=x0+i*pitch
        parts.append(box(x-thick*.55,lo,x+thick*.55,hi))
    _solid(b,face,l,unary_union(parts),d,d+.018,IRON,tag+' iron uprights and rails')
    # Opposed open scrolls terminate against the upper and lower horizontal rails.
    curls=[]
    for i in range(n):
        x=x0+(i+.5)*pitch
        for v0,v1 in ((.11,.46),(.55,.88)):
            z0=lo+v0*(hi-lo);z1=lo+v1*(hi-lo)
            for mirror in (-1.,1.):
                a=pitch*.31; rad=pitch*.115
                curve=[(x+mirror*a,z0+1.1*rad),(x+mirror*a,z1-1.1*rad)]
                for j in range(1,8 if lod else 13):
                    angle=pi*1.58*j/(7 if lod else 12)
                    curve.append((x+mirror*(a-rad+rad*cos(angle)),z1-1.1*rad+rad*sin(angle)))
                lower=[(u,z0+z1-v)for u,v in curve[1:]]
                curls.append(_strip([*lower[::-1],*curve[1:]],thick*.69))
    _solid(b,face,l,unary_union(curls),d+.002,d+.015,IRON,tag+' paired grille scrolls')


def add_window(b,face,opening,layout,lod=False):
    """Insert a photographed sash or eight-panel door in one measured wall opening."""
    c,w,lo,top=[float(opening[k])for k in ('center','width','sill','head')]
    kind=opening['kind'];tag=f'{face.title()} {c:.2f} {kind} '
    left,right=c-w/2,c+w/2
    dep=float(opening.get('sash_depth',.16 if kind in ('arch','door') else .12))
    def make(poly,d0,d1,mat,name):
        _solid(b,face,layout,poly,d0,d1,mat,tag+name)
    rounded=kind in ('arch','door')
    spring=float(opening.get('spring',top-w/2))
    outside=_head(c,w/2,lo,spring,top,16 if lod else 36) if rounded else box(left,lo,right,top)
    rim=(.043 if rounded else .049)*w
    inside=outside.buffer(-rim,join_style=2)
    make(outside.difference(inside),dep,dep+.085,CASE,'fixed casing')
    if rounded:
        inner_lo,inner_hi=lo+rim,spring
        if kind=='door':
            make(box(left+rim,inner_lo,right-rim,inner_hi),dep+.023,dep+.078,PANEL,'single timber leaf')
            rails=[]
            margin=w*.075
            panel_width=(w-2*rim-3*margin)/2
            panel_height=(inner_hi-inner_lo-5*margin)/4
            for r in range(4):
                for i in range(2):
                    x=left+rim+margin+(panel_width+margin)*i
                    z=inner_lo+margin+(panel_height+margin)*r
                    edge=box(x,z,x+panel_width,z+panel_height)
                    rails.append(edge.difference(edge.buffer(-.023*w,join_style=2)))
            make(unary_union(rails),dep+.004,dep+.022,WOOD,'eight panel borders')
            stem=c-.365*w;handlez=inner_lo+.47*(inner_hi-inner_lo)
            b.tube([_point(face,stem,dep+.025,handlez-.07,layout),
                    _point(face,stem,dep-.03,handlez,layout),
                    _point(face,stem+.08*w,dep-.03,handlez+.005,layout)],
                   .012*w,BRASS,6 if lod else 9,tag+' handle')
        else:
            lower=box(left+rim,inner_lo,right-rim,inner_hi)
            make(lower,dep+.080,dep+.095,TREE,'glass behind iron')
            make(box(c-.022*w,inner_lo,c+.022*w,inner_hi),dep+.038,dep+.072,WOOD,'vertical meeting rail')
            _ornamental_grille(b,face,layout,c,w-2*rim,inner_lo,inner_hi,dep-.051,tag,lod)
        head=inside.intersection(box(left,spring,right,top))
        make(head,dep+.08,dep+.095,DARK,'fanlight glass')
        rx=w/2-rim; rz=top-spring-rim; k=.40
        lines=[box(left+rim,spring-.021*w,right-rim,spring+.021*w)]
        inner=[(c+k*rx*cos(j*pi/24),spring+k*rz*sin(j*pi/24)) for j in range(25)]
        lines.append(_strip(inner,.030*w))
        for angle in (pi/4,pi/2,3*pi/4):
            lines.append(_strip([(c+k*rx*cos(angle),spring+k*rz*sin(angle)),
                                 (c+rx*cos(angle),spring+rz*sin(angle))],.026*w))
        make(unary_union(lines).intersection(inside),dep+.012,dep+.068,WOOD,'semiring and three radii')
        return
    x0,z0,x1,z1=inside.bounds
    lower_rail=z0+(.32*(z1-z0) if kind=='balcony' else 0.)
    bars=[]
    # The courtyard windows show two glazing bars. Ivy conceals the upper
    # division on the lane, where one bar can be identified on the clearest sash.
    lights_per_leaf=int(opening.get('lights_per_leaf',3))
    for i in range(2):
        ac=(x0 if i==0 else c);bc=(c if i==0 else x1)
        ax,bx=ac+.041*w,bc-.041*w
        sash=box(ac,z0,bc,z1)
        if kind=='balcony':
            make(box(ax,z0+.045*w,bx,lower_rail-.018*w),dep+.067,dep+.081,PANEL,'lower timber field '+str(i+1))
        bottom=lower_rail+.044*w
        holes=[]
        for j in range(lights_per_leaf):
            p0=bottom+(z1-.044*w-bottom)*j/lights_per_leaf
            p1=bottom+(z1-.044*w-bottom)*(j+1)/lights_per_leaf
            glass=box(ax,p0+(.009*w if j else 0),bx,p1-(.009*w if j+1<lights_per_leaf else 0))
            holes.append(glass)
            mat=SKY if kind=='balcony' else TREE
            make(glass,dep+.072,dep+.083,mat,'glass '+str(i+1)+'-'+str(j+1))
        if kind=='balcony':
            holes.append(box(ax,z0+.045*w,bx,lower_rail-.018*w))
        bars.append(sash.difference(unary_union(holes)))
    make(unary_union(bars),dep+.020,dep+.071,WOOD,'two fitted wood casements')


def add_twisted_column(b,face,opening,layout,lod=False):
    """Closed helical relief with separate square end blocks and rounded mouldings."""
    c,w,z0,z1=[float(opening[k])for k in ('center','width','sill','head')]
    d=float(opening.get('shaft_axis_depth',.06));pitch=float(opening.get('pitch',(z1-z0)/float(opening.get('courses',25 if z0>2.5 else 17))))
    tag=f'{face.title()} {c:.2f} spiral ';radius=w*.49
    baseh=w*.35; caph=w*.26;lo=z0+baseh;hi=z1-caph
    step=24 if lod else 40;rows=max(20,ceil((hi-lo)/pitch*(4 if lod else 7)))
    amp=w*(.047 if z0>2.5 else .066);starts=int(opening.get('starts',4))
    vertices=[];faces=[]
    for k in range(rows+1):
        z=lo+(hi-lo)*k/rows
        end_fade=min(1,(z-lo)/(.25*pitch),(hi-z)/(.25*pitch))
        for i in range(step):
            theta=2*pi*i/step
            angle=2*pi*(z-lo)/pitch-starts*theta
            relief=(.5+.5*cos(angle))**2.0
            r=radius-amp*end_fade*relief
            vertices.append(_point(face,c+r*sin(theta),d-r*cos(theta),z,layout))
    for k in range(rows):
        for i in range(step):
            a=k*step+i;j=k*step+(i+1)%step;faces.append((a,j,j+step,a+step))
    bottom=len(vertices);vertices.extend([_point(face,c,d,lo,layout),_point(face,c,d,hi,layout)])
    for i in range(step):
        j=(i+1)%step
        faces.extend([(bottom,j,i),(bottom+1,rows*step+i,rows*step+j)])
    if not _front(face):faces=[tuple(reversed(f))for f in faces]
    b.add(vertices,faces,STONE,tag+' twisted shaft')
    # Flat square plinth, two circular moulds, neck, square capital and thin crowning shelf.
    def ring(zlo,zhi,rad,rad2,name):
        vs=[];fs=[]
        for z,r in [(zlo,rad),(zhi,rad2)]:
            for i in range(step):
                theta=2*pi*i/step;vs.append(_point(face,c+r*sin(theta),d-r*cos(theta),z,layout))
        vs.extend([_point(face,c,d,zlo,layout),_point(face,c,d,zhi,layout)])
        for i in range(step):
            j=(i+1)%step;fs.extend([(i,j,j+step,i+step),(2*step,j,i),(2*step+1,i+step,j+step)])
        if not _front(face):fs=[tuple(reversed(f))for f in fs]
        b.add(vs,fs,EDGE,tag+name)
    def square(a,bb,f,name):
        _solid(b,face,layout,box(c-w*f/2,a,c+w*f/2,bb),d-w*f/2,d+w*f/2,EDGE,tag+name)
    square(z0,z0+.14*w,1.16,'square plinth')
    ring(z0+.14*w,z0+.22*w,w*.58,w*.52,'lower bevel')
    ring(z0+.22*w,lo,w*.53,radius,'base mould')
    ring(hi,hi+.065*w,radius,w*.545,'shaft neck')
    square(hi+.065*w,z1-.075*w,1.10,'capital block')
    square(z1-.075*w,z1,1.25,'capital shelf')
