"""Clay hipped roof, its eastern return and three photographed shed dormers.

The southwest corner of the lowest gallery bay is the origin. The south eave
runs east along X. Y points into the house and Z is height above the garden.
"""
from math import ceil, cos, dist, floor, hypot, pi, sin, sqrt
from pathlib import Path

TILE = 'Zhu residence | weathered red flat tiles'
RIDGE = 'Zhu residence | earthen ridge caps'
LIP = 'Zhu residence | red tile edge'
BOARD = 'Zhu residence | dark dormer fascia'
APR = 'Zhu residence | charcoal east roof apron'
EAVE = 'Zhu residence | dark garden cornice'
CONSOLE = 'Zhu residence | square eave brackets'
PLASTER = 'Zhu residence | ochre dormer cheeks'
FRAME = 'Zhu residence | painted dormer casement'
GLASS = 'Zhu residence | recessed dormer glass'

def _rgb(r, g, b):
    return [((n / 255 + .055) / 1.055)**2.4 for n in (r, g, b)]

PALETTE = {
    TILE: dict(color=[1., 1., 1.], roughness=.93,
               texture=str(Path(__file__).with_name('zhu-red-flat-tile.png'))),
    RIDGE: dict(color=_rgb(144, 77, 61), roughness=.91),
    LIP: dict(color=_rgb(135, 78, 61), roughness=.91),
    EAVE: dict(color=_rgb(72, 70, 72), roughness=.88),
    CONSOLE: dict(color=_rgb(100, 97, 94), roughness=.88),
    APR: dict(color=_rgb(98, 98, 102), roughness=.90),
    BOARD: dict(color=_rgb(81, 65, 60), roughness=.87),
    PLASTER: dict(color=_rgb(205, 177, 145), roughness=.90),
    FRAME: dict(color=_rgb(121, 107, 96), roughness=.79),
    GLASS: dict(color=_rgb(76, 80, 82), roughness=.31),
}

def make_tile_image():
    """Four staggered flat clay tiles across and three laps per 0.96 × 0.84 m."""
    from PIL import Image
    width, height = 192, 168
    im = Image.new('RGB', (width, height))
    pix = im.load()
    for y in range(height):
        row, lap = divmod(y, 56)
        for x in range(width):
            col, across = divmod((x + 24 * (row % 2)) % width, 48)
            hue = ((col * 7 + row * 3) % 9) - 4
            grain = 1.8 * sin(2*pi*(41*x/width+9*y/height)) + 1.6 * cos(2*pi*37*y/height)
            edge = -18 if across < 2 else 5 if across == 2 else 0
            lip = -21 if lap > 52 else 8 if lap == 51 else 0
            variation = hue + grain + edge + lip + 3*cos(pi*across/48)
            pix[x,y] = tuple(round(base + k*variation) for base,k in ((159,1.),(88,.78),(73,.66)))
    im.save(Path(__file__).with_name('zhu-red-flat-tile.png'), optimize=True)

def _clip(poly, axis, bound, positive):
    result = []
    for a,b in zip(poly, poly[1:]+poly[:1]):
        da,db = a[axis]-bound,b[axis]-bound
        if (da >= 0) == positive or abs(da)<1e-9:
            result.append(a)
        if da*db < -1e-12:
            t=da/(da-db)
            result.append(tuple(a[k]+t*(b[k]-a[k]) for k in range(3)))
    return result

def _area(poly):
    return sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(poly,poly[1:]+poly[:1]))*.5

def _outside(poly, rect):
    """Split a convex face around one actual rectangular dormer penetration."""
    inside=poly
    for axis,cut,keep_high in ((0,rect[0],True),(0,rect[1],False),
                               (1,rect[2],True),(1,rect[3],False)):
        outside=_clip(inside,axis,cut,not keep_high)
        if len(outside)>=3 and abs(_area(outside))>1e-7:
            yield outside
        inside=_clip(inside,axis,cut,keep_high)
        if len(inside)<3 or abs(_area(inside))<1e-7:
            break

def _solid(b, poly, delta, mat, name, uv=None):
    """Extrude a planar face. Distinct edge UVs retain positive areas."""
    a,c,d=poly[:3];v=[c[i]-a[i] for i in range(3)];w=[d[i]-a[i] for i in range(3)]
    normal=(v[1]*w[2]-v[2]*w[1],v[2]*w[0]-v[0]*w[2],v[0]*w[1]-v[1]*w[0])
    if sum(n*t for n,t in zip(normal,delta))>0:poly=list(reversed(poly))
    lo=[tuple(p[k]+delta[k] for k in range(3)) for p in poly]
    sides=[[poly[(i+1)%len(poly)],p,lo[i],lo[(i+1)%len(poly)]] for i,p in enumerate(poly)]
    vertices,faces,coords=[],[],[]
    for i,ring in enumerate([poly,list(reversed(lo)),*sides]):
        k=len(vertices);vertices.extend(ring);faces.append(tuple(range(k,k+len(ring))))
        if uv and i<2:coords.extend([uv(p) for p in ring])
        elif uv:
            length,t=dist(ring[0],ring[1])/.96,dist(ring[1],ring[2])/.84
            coords.extend([(0.,0.),(length,0.),(length,t),(0.,t)])
    b.add(vertices,faces,mat,name)
    if coords and not b.parts[-1].get('texcoords'):
        b.parts[-1]['texcoords']=coords

def _hip_cap(b,p,q,width,lod,label):
    dx,dy=q[0]-p[0],q[1]-p[1];length=hypot(dx,dy)
    cross=(-dy/length,dx/length);steps=ceil(length/(.90 if lod else .42))
    for i in range(steps):
        t=i/steps;t1=min(1.,(i+1)/steps+.010/length)
        faces=[];verts=[]
        for u in (t,t1):
            center=[a+(c-a)*u for a,c in zip(p,q)]
            for k in range(7):
                angle=pi*k/6
                off=width*cos(angle);h=.015+width*.57*sin(angle)
                verts.append((center[0]+cross[0]*off,center[1]+cross[1]*off,center[2]+h))
        faces.extend([list(range(7)),list(reversed(range(7,14)))])
        for k in range(7):faces.append((k,7+k,7+(k+1)%7,(k+1)%7))
        # The cap profiles run from the left edge to the right through the crown.
        b.add(verts,[tuple(reversed(face)) for face in faces],RIDGE,label)

def roof_features(layout):
    east=layout['east_x'];north=layout['rear_y'];z=layout['south_eave_z']
    xscale=east/18.8;yscale=north/11.3;y0=layout.get('roof_south_y',-.23)
    rise=layout.get('roof_rise',4.52)
    def pt(x,y,h=0):return (-.20+x*xscale,y0+y*yscale,z+h)
    sw,se,nw,ne=pt(0,0),pt(19.09,0),pt(.32,10.55),pt(19.23,10.14)
    west,east_node=pt(2.08,4.75,rise),pt(15.30,4.65,rise)
    es,ens=pt(19.12,1.65),pt(19.20,8.37)
    outer_s,outer_n=pt(21.92,1.92),pt(21.75,8.05)
    end_ridge=pt(19.73,5.18,rise*.68)
    faces=[('south',[sw,se,east_node,west],1),('north',[nw,west,east_node,ne],1),
           ('west',[sw,west,nw],0),('east south hip',[se,es,east_node],0),
           ('return south',[es,outer_s,end_ridge,east_node],1),
           ('east end',[outer_s,outer_n,end_ridge],0),
           ('return north',[outer_n,ens,east_node,end_ridge],1),
           ('east north hip',[ens,ne,east_node],0)]
    caps=[('principal ridge',west,east_node),('west south hip',sw,west),
          ('west north hip',nw,west),('east south fold',se,east_node),
          ('east north fold',ne,east_node),('lower eastern ridge',east_node,end_ridge),
          ('small east south hip',outer_s,end_ridge),('small east north hip',outer_n,end_ridge)]
    # Each dormer has its own face width, height and projection. The eastern
    # casement is visibly divided; the south panes are largely hidden by their lips.
    defaults=[('west south shed','south',6.80,1.142,2.534,2.68,1),
              ('east south shed','south',12.183,1.142,2.416,2.64,2),
              ('side shed','east',11.391,17.90,1.66,1.55,2)]
    dormers=[]
    for tag,side,u,d,width,height,lights in defaults:
        override=layout.get('roof_dormers',{}).get(tag,{})
        u,d=override.get('u',u),override.get('d',d)
        width,height=override.get('width',width),override.get('height',height)
        if side=='south':
            x,y,_=pt(u,d);w=width*xscale
            def loc(a,into,h,x=x,y=y):return (x+a,y+into,h)
            base=z+rise*d/4.7+.035
        else:
            x,y,_=pt(d,u);w=width*yscale
            def loc(a,into,h,x=x,y=y):return (x-into,y+a,h)
            base=z+1.18
        dormers.append(dict(label=tag,side=side,loc=loc,width=w,height=height,base=base,
                            run=override.get('run',3.62 if side=='south' else 1.08),
                            lights=lights))
    return faces,caps,dormers

def _dormer(b,d):
    name=d['label'];p=d['loc'];half=d['width']/2;h=d['height'];low=d['base'];run=d['run'];top=low+h
    east = d['side']=='east'
    lintel = .50 if not east else .59
    pier = .31 if east else .135
    yz=p(0,0,0);forward=tuple(p(0,.038,0)[i]-yz[i] for i in range(3))
    side=tuple(p(.085,0,0)[i]-yz[i] for i in range(3))
    def front(a,c,v,w,depth,material,label,thickness=None):
        if thickness is None:
            thickness=.16 if material==PLASTER else .09 if material==FRAME else .04
        _solid(b,[p(a,depth,v),p(c,depth,v),p(c,depth,w),p(a,depth,w)],
               tuple(t*thickness/.038 for t in forward),material,name+' '+label)
    for i in (0,1):
        u=(-half if i==0 else half-.085)
        _solid(b,[p(u,0,low-.10),p(u,run,low-.10),p(u,run,top+.36),p(u,0,top)],
               side,PLASTER,name+' side cheeks')
    front(-half,half,low-.09,low+.14,0,PLASTER,'sill and breast')
    front(-half,half,top-lintel,top,0,PLASTER,'head')
    for a,c in [(-half,-half+pier),(half-pier,half)]:
        front(a,c,low+.14,top-lintel,0,PLASTER,'jambs')
    a,c=-half+pier,half-pier;bottom,head=low+.14,top-lintel
    for x0,x1,z0,z1 in [(a,a+.052,bottom,head),(c-.052,c,bottom,head),
                          (a+.052,c-.052,bottom,bottom+.052),(a+.052,c-.052,head-.052,head)]:
        front(x0,x1,z0,z1,.05,FRAME,'casement')
    middle=d['lights']==2
    if middle:front(-.023,.023,bottom+.052,head-.052,.05,FRAME,'central muntin')
    lights = [(a+.052,-.023),(.023,c-.052)] if middle else [(a+.052,c-.052)]
    for x0,x1 in lights:
        if east:
            # Two casements, each with the same shallow transom seen in Gao 10.
            cross = low + .62
            front(x0,x1,cross-.024,cross+.024,.05,FRAME,'meeting rail')
            panes = [(bottom+.052,cross-.024),(cross+.024,head-.052)]
        else:
            panes = [(bottom+.052,head-.052)]
        for z0,z1 in panes:
            front(x0,x1,z0,z1,.108,GLASS,'window panes',.025)
    cap=[p(-half-.14,-.20,top+.055),p(half+.14,-.20,top+.055),
         p(half+.14,run+.03,top+.42),p(-half-.14,run+.03,top+.42)]
    _solid(b,cap,(0,0,-.066),TILE,name+' tiled cap',lambda t:(t[0]/.96,t[1]/.84))
    front(-half-.14,half+.14,top-.085,top+.045,-.20,BOARD,'front fascia')
    front(-half-.16,half+.16,top+.045,top+.08,-.21,LIP,'projecting tile lip')

def _east_lip(b,layout):
    """The dark cornice below the roof window, across the straight upper door bay."""
    sx=layout['east_x']/18.8;sy=layout['rear_y']/11.3
    dz=layout['south_eave_z']-8.86;lo,hi=8.86*sy,12.89*sy
    def profile(y0,y1,section,material,label):
        _solid(b,[(x*sx,y0,z+dz) for x,z in section],(0,y1-y0,0),material,label)
    profile(lo,hi,[(18.80,8.78),(18.93,8.86),(19.125,8.852),(19.125,8.842),
                    (19.148,8.82),(19.148,8.52),(19.142,8.48),
                    (19.142,8.25),(19.095,8.25),(19.095,8.65)],
            APR,'East door bay dark roof cornice')
    for i in range(8):
        y=lo+(hi-lo)*(i+.5)/8
        profile(y-.055,y+.055,[(19.14,8.51),(19.18,8.51),(19.18,8.47),
                (19.16,8.40),(19.14,8.39)],EAVE,'East eave dark bracket ends')


def _western_tile_return(b,layout):
    """The short lip and exposed apron left of the two identifiable south casements."""
    sx=layout['east_x']/18.8
    sy=layout['rear_y']/11.3
    z=layout['south_eave_z']
    def pt(x,y,h):return (x*sx,y*sy,z+h)
    def uv(p):return (p[0]/.96,p[1]/.84)
    # Gao 05 shows the short horizontal red edge above two rows of tiles. The
    # body below its lip is hidden; only visible clay and fascia are included.
    upper=[pt(2.65,1.80,3.30),pt(4.89,1.80,3.32),
           pt(4.89,3.63,3.47),pt(2.65,3.63,3.45)]
    _solid(b,upper,(0,0,-.09),TILE,'West garden short tile return',uv)
    apron=[pt(2.34,1.60,2.72),pt(4.96,1.60,2.74),
           pt(4.96,1.85,3.08),pt(2.34,1.85,3.06)]
    _solid(b,apron,(0,0,-.055),TILE,'West garden short tile apron',uv)
    band=[pt(2.67,1.82,3.32),pt(4.89,1.82,3.34),
          pt(4.89,1.82,3.15),pt(2.67,1.82,3.13)]
    _solid(b,band,(0,.12,0),LIP,'West garden short red lip')


def garden_eave_lines(layout):
    xscale=layout['east_x']/18.8
    edges=layout['bay_edges']
    left, first, second, right=(-.10*xscale, edges[1]-.54*xscale,
                                  edges[2]+.15*xscale, edges[3]+.22*xscale)
    side, middle=layout['front_y'][0]-.98,layout['front_y'][1]-.94
    return [(left,side),(first,side),(first,middle),(second,middle),
            (second,side),(right,side)]


def _garden_cornice(b,layout):
    """Projecting soffit, its return corners and the visible square brackets in Gao 05."""
    top=layout['south_eave_z']+.20
    line=garden_eave_lines(layout)
    for j in (0,2,4):
        a,y=line[j];c=line[j+1][0];rear=.20
        _solid(b,[(a,y,top-.051),(c,y,top-.051),(c,rear,top-.051),
                  (a,rear,top-.051)],(0,0,-.17),EAVE,'Garden deep eave soffits')
    for i,((x,y),(u,v)) in enumerate(zip(line,line[1:])):
        length=hypot(u-x,v-y);dx,dy=(u-x)/length,(v-y)/length
        # The chain progresses east; its left-hand normal points inside the roof.
        def point(t,inside,h):return (x+t*dx-dy*inside,y+t*dy+dx*inside,top+h)
        def trim(t0,t1,profile,material,name):
            poly=[point(t0,d,h) for d,h in profile]
            _solid(b,poly,((t1-t0)*dx,(t1-t0)*dy,0.),material,name)
        trim(-.032,length+.032,[(-.032,0),(.10,0),(.10,-.105),(.00,-.105),
                                  (.00,-.075),(-.032,-.065)],EAVE,'Garden cornice projecting top bead')
        trim(0,length,[(.075,-.115),(.16,-.115),(.16,-.255),(.095,-.255),
                       (.075,-.236)],EAVE,'Garden cornice lower bead')
        count=max(1,round(length/.58))
        for k in range(count):
            mid=(k+.5)*length/count
            trim(mid-.075,mid+.075,[(.23,-.20),(.70,-.20),(.70,-.375),
                (.42,-.375),(.38,-.33),(.29,-.32),(.23,-.265)],
                CONSOLE,'Garden eave square brackets')


def east_apron_z(base, into):
    """Height of the short dark roof strip at the signed distance behind the sash."""
    return base + .10 + 1.16 * into


def add_roof(b,lod=False,layout=None):
    if layout is None:layout=dict(east_x=18.8,rear_y=11.3,south_eave_z=8.9,
                                   bay_edges=[0,5.97,12.8,18.8],front_y=[0,-.84,0])
    for k,v in PALETTE.items():b.palette.setdefault(k,v)
    faces,caps,dormers=roof_features(layout)
    # This short charcoal return appears directly below the eastern casement in
    # Gao 10. Its far edge marks the measured section of the northern addition.
    east_dormer = dormers[-1]
    p=east_dormer['loc'];base=east_dormer['base']
    def apron(a,into):
        return p(a,into,east_apron_z(base,into))
    faces.append(('east dormer apron',[apron(-1.50,-1.10),apron(1.66,-1.10),
                                      apron(1.66,1.22),apron(-1.50,1.22)],0))
    for label,poly,axis in faces:
        # The east return is visibly lower than the main ridge. Break its two
        # slightly twisted panels into planes before clipping for accurate Z.
        pieces=[poly] if len(poly)==3 else [[poly[0],poly[1],poly[2]],[poly[0],poly[2],poly[3]]]
        for dormer in dormers:
            if (dormer['side']=='south' and label!='south') or (dormer['side']=='east' and label!='east dormer apron'):continue
            p=dormer['loc'];a=dormer['width']/2-.066
            corners=[p(-a,.015,0),p(a,dormer['run']-.04,0)]
            xs,ys=zip(*[q[:2] for q in corners])
            rect=(min(xs),max(xs),min(ys),max(ys))
            pieces=[part for face in pieces for part in _outside(face,rect)]
        for tri in pieces:
            if abs(_area(tri))<1e-7:continue
            low=min(q[axis] for q in tri);high=max(q[axis] for q in tri)
            step=1.12 if lod else .28
            for j in range(floor(low/step),ceil(high/step)):
                slab=_clip(_clip(tri,axis,j*step,True),axis,(j+1)*step,False)
                if len(slab)<3 or abs(_area(slab))<1e-7:continue
                uphill= label in ('south','return south','west')
                slab=[(q[0],q[1],q[2]+.013*((j+1)-q[axis]/step if uphill else q[axis]/step-j)) for q in slab]
                scale=sqrt(1+.73**2)
                def uv(q,axis=axis,scale=scale):return (q[1-axis]/.96,q[axis]*scale/.84)
                material = APR if label=='east dormer apron' else TILE
                _solid(b,slab,(0,0,-.082),material,'Zhu '+label+' tiled roof',uv if material==TILE else None)
    for label,p,q in caps:_hip_cap(b,p,q,.095 if 'ridge' in label else .071,lod,'Zhu '+label)
    for dormer in dormers:_dormer(b,dormer)
    _garden_cornice(b,layout)
    _western_tile_return(b,layout)
    _east_lip(b,layout)
