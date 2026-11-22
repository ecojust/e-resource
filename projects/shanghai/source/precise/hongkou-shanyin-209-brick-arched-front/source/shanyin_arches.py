"""The three upper red-brick segmental arches and pale fanlights in Fayhoo's 2015 photograph."""
from math import asin, cos, pi, sin, sqrt

from shapely import set_precision
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

LIGHT = 'Shanyin sash | pale painted timber'
STILE = 'Shanyin sash | meeting rails'
GLASS = 'Shanyin sash | slightly blue glass'
LOW = 'Shanyin sash | grey lower glass'
MORTAR = 'Shanyin arch | warm pointing'
BRICKS = ['Shanyin arch | red facing','Shanyin arch | amber red','Shanyin arch | dark red']
LEDGE = 'Shanyin arch | moulded springing'

def finish(rgb,roughness,metallic=0):
    def channel(c):
        c=c/255
        return c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4
    return dict(color=[channel(c)for c in rgb],roughness=roughness,metallic=metallic)

PALETTE={LIGHT:finish((202,200,182),.73),STILE:finish((187,185,170),.71),
         GLASS:finish((105,123,122),.31,.14),LOW:finish((89,106,107),.36,.15),
         MORTAR:finish((196,136,101),.91),
         BRICKS[0]:finish((163,77,45),.90),BRICKS[1]:finish((172,86,53),.91),
         BRICKS[2]:finish((153,68,36),.89),LEDGE:finish((163,79,53),.85)}

def dimensions(row):
    x0,x1,sill,spring,top=(row[k] for k in ('x0','x1','z_sill','z_spring','z_crown'))
    width=x1-x0
    rise=top-spring
    if not (width>0 and sill<spring<top and rise<=.5*width):
        raise ValueError('Expected a two-jamb segmental arch with a sill below its spring')
    radius=(width*width/4+rise*rise)/(2*rise)
    return width,(x0+x1)/2,top-radius,radius

def samples(cx,cy,r,start,stop,steps):
    return [(cx+r*cos(start+(stop-start)*i/steps),cy+r*sin(start+(stop-start)*i/steps))for i in range(steps+1)]

def opening_polygon(row):
    """Outer joinery line used as the matching through-cut in its masonry wall."""
    w,c,z,r=dimensions(row)
    right=asin((row['z_spring']-z)/r)
    return Polygon([(row['x0'],row['z_sill']),(row['x1'],row['z_sill']),
                    *samples(c,z,r,right,pi-right,56)])

def sector(cx,cy,r0,r1,a,b,steps):
    return Polygon(samples(cx,cy,r1,a,b,steps)+samples(cx,cy,r0,b,a,steps))

def panels(b,shape,front,back,mat,label):
    if shape.is_empty:return
    if back<=front:raise ValueError('A solid must have positive depth')
    # Remove coincident sub-micron vertices left where an arc meets a spoke.
    shape=set_precision(shape,1e-7).simplify(2e-7,preserve_topology=True)
    b.prism(shape,-back,-front,lambda x,z,y:(x,-y,z),mat,label)

def batch(b,solids,mat,label):
    """Keep editable brick courses compact while preserving each complete brick shell."""
    if not solids:return
    original=len(b.parts)
    for shape,front,back in solids:
        panels(b,shape,front,back,mat,label)
    pieces=b.parts[original:]
    if not pieces:return
    del b.parts[original:]
    vertices=[];triangles=[]
    for piece in pieces:
        start=len(vertices);vertices.extend(piece['vertices'])
        triangles.extend(tuple(start+i for i in face)for face in piece['triangles'])
    b.add(vertices,triangles,mat,label)

def brick_head(b,far,row,index,left_cut,right_cut):
    width,c,cy,r=dimensions(row)
    y=row.get('face_y',0)
    spring=row['z_spring']
    title=f'Upper arch {index}'
    # Four concentric courses are present. The two outer bands are noticeably shorter headers.
    limit=box(left_cut,spring,right_cut,row['z_crown']+.30*width)
    outer=row.get('brick_ring',(.197,.208,.197)[index-1]*width)
    # The rings continue laterally down to the spring, rather than stopping along a radial edge.
    angle=asin((spring-cy)/(r+outer))
    face=Polygon(samples(c,cy,r+outer,angle,pi-angle,84)).intersection(limit)
    hole=opening_polygon(row)
    panels(b,face.difference(hole),y-.014*width,y+.001*width,MORTAR,title+' | mortar bed')
    radii=[r+outer*f for f in (0,.39,.70,.85,1)]
    for course,(inner,out) in enumerate(zip(radii,radii[1:])):
        tones=[[],[],[]]
        if far and course>=2:
            ring=sector(c,cy,inner+.0018*width,out-.0018*width,angle,pi-angle,44)
            panels(b,ring.intersection(limit),y-.024*width,y-.015*width,
                   BRICKS[(0,1,0,2)[course]],title+f' | course {course+1}')
            continue
        count=((22,23,24,25) if far else (44,45,49,51))[course]
        pitch=(pi-2*angle)/count
        tick=angle-pitch*(.35 if course in (1,3) else 0)
        serial=0
        while tick<pi-angle:
            a=max(angle,tick)+.0023*width/inner
            end=min(pi-angle,tick+pitch)-.0023*width/inner
            if end>a:
                shape=sector(c,cy,inner+.0014*width,out-.0014*width,a,end,2 if far else 3).intersection(limit)
                colour=(serial*7+course*3)%19
                tone=1 if colour<5 else (2 if colour>15 else 0)
                tones[tone].append((shape,y-(.022+.0006*(serial%4))*width,y-.014*width))
            serial+=1;tick+=pitch
        for tone,bricks in enumerate(tones):
            batch(b,bricks,BRICKS[tone],title+f' | course {course+1} brick {tone+1}')
    for side in ('left','right'):
        x0,x1=(left_cut,row['x0'])if side=='left' else (row['x1'],right_cut)
        span=min(x1-x0,.175*width)
        if side=='left':x0=x1-span
        else:x1=x0+span
        for n,(lo,hi,inset,projection) in enumerate([(-.128,-.071,.014,.032),(-.071,-.035,.004,.047),(-.035,0,0,.059)]):
            shape=box(x0+inset*width,spring+lo*width,x1-inset*width,spring+hi*width)
            panels(b,shape,y-projection*width,y-.002*width,LEDGE,title+f' | {side} impost {n+1}')

def sash(b,far,row,index):
    w,c,cz,r=dimensions(row);spring=row['z_spring'];sill=row['z_sill'];top=row['z_crown']
    face=row.get('face_y',0);recess=row.get('recess',.063*w);y=face+recess
    name=f'White fanlight {index}'
    outer=opening_polygon(row)
    fixed=outer.buffer(-.018*w,join_style='round',quad_segs=3)
    panels(b,outer.difference(fixed),y,y+.052*w,LIGHT,name+' | outer casing')
    # The central little arc spans roughly one quarter of the parent fanlight.
    # Its spring coincides with the broad rail; the three straight spokes connect both arcs.
    ws=.232*w;hs=.087*w; rr=(ws*ws/4+hs*hs)/(2*hs);zz=spring+hs-rr
    aa=asin((spring-zz)/rr)
    mini=LineString(samples(c,zz,rr,aa,pi-aa,23 if far else 46))
    rails=[mini.buffer(.006*w,cap_style='flat'),
           box(row['x0'],spring-.018*w,row['x1'],spring+.020*w)]
    def outward(dx):
        vx, vz=dx, sqrt(max(0.,1-dx*dx))
        # The diagonal spokes share a virtual origin on the rail.
        A=spring-cz
        t=-A*vz+sqrt(A*A*vz*vz+r*r-A*A)
        small=spring-zz
        start=-small*vz+sqrt(small*small*vz*vz+rr*rr-small*small)
        return LineString([(c+vx*start,spring+vz*start),(c+vx*t,spring+vz*t)])
    for u in (-.702,0,.698):
        rails.append(outward(u).buffer(.006*w,cap_style='flat'))
    below=box(row['x0'],sill,row['x1'],spring)
    dividers=(.257,.524,.754)if index==1 else ((.242,.458,.766)if index==2 else (.245,.492,.746))
    for i,f in enumerate(dividers):
        x=row['x0']+w*f
        half=w*(.017 if i!=1 else .011)
        rails.append(box(x-half,sill,x+half,spring))
    lattice=unary_union(rails).intersection(fixed)
    panels(b,lattice,y+.005*w,y+.041*w,STILE,name+' | radial and lower rails')
    panes=fixed.difference(lattice)
    upper=unary_union([p for p in panes.geoms if p.representative_point().y>spring]);lower=unary_union([p for p in panes.geoms if p.representative_point().y<spring])
    if far:
        upper=fixed.difference(below);lower=fixed.intersection(below)
    for shape,material,subtitle in [(upper,GLASS,'arched glass'),(lower,LOW,'lower glass')]:
        bits=list(getattr(shape,'geoms',[shape]))
        # Each clear painted lower light can be separately selected in the editable model.
        # The slim stop around the glass is behind the broad stiles and transom.
        for serial,pane in enumerate(sorted(bits,key=lambda p:p.centroid.x),1):
            if pane.area<=1e-9:continue
            if material==LOW and not far:
                clear=pane.buffer(-.0042*w,join_style='mitre')
                panels(b,pane.difference(clear),y+.025*w,y+.043*w,LIGHT,
                       name+f' | lower glazing stop {serial}')
            panels(b,pane,y+.048*w,y+.054*w,material,name+f' | {subtitle} {serial}')

def add_shanyin_arches(b,lod,openings):
    """Place three corresponding brick rings, stepped imposts and glazed fanlights."""
    if len(openings)!=3:raise ValueError('The façade study has three adjacent upper arches')
    far=lod is True or lod=='lod'
    for i,row in enumerate(openings):
        width,*_=dimensions(row)
        left=(openings[i-1]['x1']+row['x0'])/2 if i else row['x0']-.222*width
        right=(openings[i+1]['x0']+row['x1'])/2 if i+1<len(openings) else row['x1']+.222*width
        brick_head(b,far,row,i+1,left,right)
        sash(b,far,row,i+1)
