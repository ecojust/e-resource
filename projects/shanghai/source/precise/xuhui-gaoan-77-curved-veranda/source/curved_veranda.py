"""Southern attic veranda of Gaoan Road 77. Units are metres, +Y into the house."""
from math import atan2, cos, pi, sin, sqrt

import numpy as np
from shapely.geometry import LineString, Polygon, box

PLASTER = 'Gaoan 77 | cream plaster'
SOFFIT = 'Gaoan veranda | plaster soffit'
WOOD = 'Gaoan 77 | exposed dark timber'
IRON = 'Gaoan 77 | wrought iron'
CAP = 'Gaoan veranda | russet coping brick'
TILE = 'Gaoan 77 | red clay roof'
RIDGE = 'Gaoan 77 | tile crests'
TILE_LIGHT = 'Gaoan veranda | sunlit clay rolls'
LINING = 'Gaoan veranda | recessed timber doors'
TILE_DARK = 'Gaoan veranda | shadow under overlapping tile noses'
TILE_WARM = 'Gaoan veranda | weathered russet clay'

def paint(rgb, roughness):
    return {'color': [((n / 255 + .055) / 1.055)**2.4 if n > 10.315 else n / 3294.6 for n in rgb], 'roughness': roughness}

PALETTE = {
    PLASTER: paint((227,217,195), .88), SOFFIT: paint((212,199,168), .89),
    WOOD: paint((63,49,42), .80), IRON: paint((72,66,55), .61),
    CAP: paint((144,89,67), .92), TILE: paint((149,82,59), .93),
    TILE_DARK: paint((80,50,39),.94), TILE_WARM: paint((139,74,53),.92), TILE_LIGHT: paint((171,98,70), .92), RIDGE: paint((153,93,68),.90), LINING: paint((84,63,51), .83),
}
DEFAULT = dict(center_x=0., front_y=0., deck_z=7.0, post_span=3.2,
               balcony_projection_ratio=.163, fascia_projection_ratio=.256,
               ridge_setback_ratio=.396, rear_cut_ratio=.63, ridge_height_ratio=1.454)

def settings(layout):
    result = DEFAULT.copy()
    if layout:
        result.update(layout.get('veranda',layout))
    if result['post_span'] <= 0 or not .045 <= result['balcony_projection_ratio'] <= .34:
        raise ValueError('A positive timber span and a shallow segmental balcony are required.')
    if result['rear_cut_ratio'] < result['ridge_setback_ratio']:
        raise ValueError('Rear cut must be at or behind the visible ridge end.')
    return result

def world(p,x,y,z):
    w=p['post_span']
    return (p['center_x']+x*w,p['front_y']+y*w,p['deck_z']+z*w)

def arc_outline(n):
    return [(.462*cos(i*pi/n), .33953+.392*sin(i*pi/n)) for i in range(n+1)]

def veranda_interface(layout=None):
    p=settings(layout)
    n=32
    opening=[(-.462,-.01),(.462,-.01)]+arc_outline(n)
    ridge=p['ridge_height_ratio']
    shoulder=.809
    low=.416
    edge=1.06133
    back=p['rear_cut_ratio']
    return {'timber_post_span_m':p['post_span'],
            'main_wall_clear_opening_xz':[(world(p,x,0,z)[0],world(p,x,0,z)[2]) for x,z in opening],
            'rear_roof_section':[world(p,x-.024,back,z) for x,z in
                                 [(-edge,.362),(-shoulder,low),(0,ridge),(shoulder,low),(edge,.362)]],
            'ridge_end':world(p,-.024,p['ridge_setback_ratio'],ridge),
            'deck_at_wall':world(p,0,0,0),'wall_top_x_limits':[world(p,x,0,0)[0] for x in [-.775,.775]]}

def solid(b,p,outline,near,far,mat,label):
    b.prism(outline,-far,-near,lambda x,z,o:world(p,x,-o,z),mat,label)

def beam(b,p,points,width,near,far,label):
    shape=LineString(points).buffer(width/2,cap_style=2,join_style=2)
    solid(b,p,shape,near,far,WOOD,label)

def shell(b,p,upper,lower,mat,label):
    # Vertices are ordered around each contour in the same direction.
    vertices=np.array([world(p,*v) for v in list(lower)+list(upper)])
    n=len(upper)
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces.extend((i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n))
    volume=sum(np.dot(vertices[f[0]],np.cross(vertices[f[j]],vertices[f[j+1]]))/6
               for f in faces for j in range(1,len(f)-1))
    if volume<0:
        faces=[tuple(reversed(f)) for f in faces]
    b.add(vertices,faces,mat,label)

def profile_sweep(b,p,stations,mat,label):
    # Each station is a rectangular transverse section, ordered lower-front to upper-front.
    vs=[world(p,*v) for section in stations for v in section]
    fs=[(3,2,1,0)]
    for j in range(len(stations)-1):
        i=4*j
        for k in range(4):
            m=(k+1)%4
            fs.append((i+k,i+m,i+4+m,i+4+k))
    i=len(vs)-4
    fs.append((i,i+1,i+2,i+3))
    v=np.asarray(vs)
    volume=sum(np.dot(v[f[0]],np.cross(v[f[j]],v[f[j+1]]))/6 for f in fs for j in range(1,len(f)-1))
    if volume<0: fs=[tuple(reversed(f)) for f in fs]
    b.add(vs,fs,mat,label)

def veranda_body(b,p,lod):
    n=17 if lod else 34
    opening=Polygon([(-.462,-.035),(.462,-.035)]+arc_outline(n))
    hip_fraction=p['fascia_projection_ratio']/(p['fascia_projection_ratio']+p['ridge_setback_ratio'])
    crest=p['ridge_height_ratio']
    knee=.496*(1-hip_fraction)
    def roof_bottom(x):
        return .416+(crest-.416)*(1-abs(x+.024)/.809)-.037
    gable=Polygon([(-.775,-.021),(.775,-.021),(.775,roof_bottom(.775)),(knee,roof_bottom(knee)),(-knee,roof_bottom(knee)),(-.775,roof_bottom(.775))])
    solid(b,p,gable.difference(opening),.008,.23,PLASTER,'veranda gable and jamb returns')
    # A second arch is visible from the south-east. The rear portion is a dark,
    # recessed door reveal whose threshold lies above the second storey.
    back_outline=box(-.51,-.015,.51,.764)
    doors=[(-.425,-.153,.605),(-.065,.234,.603)]
    for left,right,top in doors:
        back_outline=back_outline.difference(box(left,.012,right,top))
    solid(b,p,back_outline,.233,.269,PLASTER,'veranda recessed plaster lunette')
    for i,(left,right,top) in enumerate(doors,1):
        solid(b,p,box(left-.004,.01,right+.004,top+.003),.281,.296,LINING,f'veranda recessed door leaf {i}')
    # The recess floor and side cheeks terminate at the documented rear door plane.
    floor=box(-.474,-.025,.474,.013)
    solid(b,p,floor,-.005,.282,SOFFIT,'veranda recessed floor')
    for i,x in enumerate([-.472,.46],1):
        solid(b,p,box(x,-.012,x+.012,.54),.016,.277,PLASTER,f'veranda jamb cheek {i}')
    arch_outer=[(.505*cos(i*pi/n),.33953+.426*sin(i*pi/n)) for i in range(n+1)]
    ring=Polygon(arch_outer+list(reversed(arc_outline(n))))
    for j,y in enumerate([-.026,.223],1):
        solid(b,p,ring,y,y+.028,WOOD,f'veranda arched timber {j}')
    for side in [-1,1]:
        tag='left' if side<0 else 'right'
        x=.5*side
        beam(b,p,[(x,-.017),(x,.660)],.044,-.032,.021,f'{tag} main timber post')
        beam(b,p,[(side*.758,-.012),(side*.758,.390)],.03,-.03,.021,f'{tag} outer timber post')
        beam(b,p,[(side*.381,0),(side*.772,0)],.043,-.031,.021,f'{tag} sill timber')
        beam(b,p,[(side*.381,.340),(side*.772,.341)],.038,-.029,.02,f'{tag} cross timber')
        beam(b,p,[(side*.746,.330),(side*.512,.012)],.031,-.030,.01,f'{tag} outer diagonal')
        beam(b,p,[(side*.381,.011),(side*.484,.328)],.026,-.033,.012,f'{tag} X timber ascending')
        beam(b,p,[(side*.486,.008),(side*.381,.328)],.026,-.030,.014,f'{tag} X timber descending')
        bracket=Polygon([(x-.028,-.012),(x+.028,-.012),(x+.022,-.105),(x-.017,-.105)])
        solid(b,p,bracket,-.046,.017,PLASTER,f'{tag} rendered sill corbel')

def balcony(b,p,lod):
    n=15 if lod else 32
    a=.378
    sag=p['balcony_projection_ratio']
    radius=(a*a+sag*sag)/(2*sag)
    def line(x): return radius-sag-sqrt(max(0,radius*radius-x*x))-.008
    def band(x0,x1,low,high,thick,mat,label,offset=0):
        stations=[]
        for x in np.linspace(x0,x1,max(4,round(n*(x1-x0)/(2*a)))+1):
            y=line(x)+offset
            stations.append([(x,y,low),(x,y+thick,low),(x,y+thick,high),(x,y,high)])
        profile_sweep(b,p,stations,mat,label)
    deck=[]
    for x in np.linspace(-a,a,n+1):
        y=line(x)
        # Back-wall intersection of the tapered soffit, observed independently in views 35 and 37.
        bottom_wall=-.016-.111*(1-(x/a)**2)
        deck.append([(x,y,-.014),(x,.054,bottom_wall),(x,.054,.080),(x,y,.080)])
    profile_sweep(b,p,deck,SOFFIT,'veranda curved deck and tapered soffit')
    band(-a,a,.016,.139,.047,PLASTER,'veranda circular front sill')
    band(-a,a,-.004,.020,.040,PLASTER,'veranda lower drip lip',-.006)
    for tag,x0,x1 in [('west',-a,-.233),('east',.233,a)]:
        band(x0,x1,.121,.306,.045,PLASTER,tag+' raised curved parapet')
        band(x0,x1,.306,.345,.051,CAP,tag+' tile coping',-.004)
    def rail(points,r,mat,label):
        b.tube([world(p,*q) for q in points],r*p['post_span'],mat,5 if lod else 8,label)
    xs=np.linspace(-.237,.237,n+1)
    for i,z in enumerate([.144,.260,.320]):
        rail([(x,line(x)+.010,z)for x in xs],.0055,IRON,f'veranda curved rail {i+1}')
    # The straight uprights and circular scrolls can be counted in the 690-pixel frontal image.
    for i,x in enumerate(np.linspace(-.231,.231,10)):
        rail([(x,line(x)+.011,.142),(x,line(x)+.011,.323)],.0046,IRON,f'veranda grille upright {i+1}')
    for i,x in enumerate(np.linspace(-.231+.462/18,.231-.462/18,9)):
        pts=[]
        for t in np.linspace(0,1,13 if lod else 24):
            angle=2*pi*1.19*t
            r=.0203*(1-.73*t)
            xx=x+r*cos(angle)
            pts.append((xx,line(xx)+.009,.289+r*sin(angle)))
        rail(pts,.0031,IRON,f'veranda grille scroll {i+1}')
    for i,x in enumerate(np.linspace(-.231,.231,10)[1:-1],1):
        for sign in [-1,1]:
            xx=x+sign*.009
            rail([(x,line(x)+.009,.294),(xx,line(xx)+.009,.314)],.0025,IRON,
                 f'veranda short iron fork {i} {sign:+d}')
    for j,z in enumerate([-.001,.014],1):
        rail([(x,line(x)-.005,z) for x in np.linspace(-a,a,n+1)],.0044,SOFFIT,
             f'veranda double drip moulding {j}')
    for sign in [-1,1]:
        for i,x in enumerate(np.linspace(.239,a-.005,9),1):
            xx=sign*x
            band(xx-.0009,xx+.0009,.309,.344,.0017,LINING,f'veranda coping joint {sign:+d} {i}',-.0053)

def overlapping_courses(b,p,poly,z_at,tag,front,lod):
    """Watertight corrugated pans and dark cut noses along each true course."""
    sign=1 if poly.centroid.x>0 else -1
    def map_plan(u,v):
        return (u,v) if front else (-sign*v,u)
    uv=Polygon([(x,y) if front else (y,-sign*x) for x,y in list(poly.exterior.coords)[:-1]])
    ulo,vlo,uhi,vhi=uv.bounds
    if front:
        stops=[0,.151,.256,.355,.457,.565,.67,.778,.878,.957,1]
    elif 'flared' in tag:
        stops=np.linspace(0,1,4)
    else:
        stops=np.linspace(0,1,14)
    pitch=.029
    # A lug is higher at its exposed lower edge. The small variation in each
    # row's horizontal phase follows the stagger visible on the 4912-pixel negative.
    fills=[TILE,TILE_LIGHT,TILE,TILE_WARM,TILE_LIGHT]
    for row,(ta,tb) in enumerate(zip(stops,stops[1:]),1):
        lower=vlo+(vhi-vlo)*ta
        upper=vlo+(vhi-vlo)*tb
        phase=pitch*(.13*((row%3)-1))
        def piece(vlow,vhigh,nose):
            outline=uv.intersection(box(ulo-.001,vlow,uhi+.001,vhigh))
            if outline.geom_type!='Polygon' or outline.area<1e-8:return
            ustart,_,uend,_=outline.bounds
            if lod:
                samples_per_pan=(.85 if front else .30) if nose else (2.4 if front else .95)
            else:
                samples_per_pan=(2.6 if front else 1.4) if nose else (4.4 if front else 3.1)
            cells=max(2,round((uend-ustart)/pitch*samples_per_pan))
            splits=np.linspace(ustart,uend,cells+1)
            verts=[]; ix={}; tris=[]
            def idx(u,v):
                key=(round(u,8),round(v,8))
                if key not in ix:
                    ix[key]=len(verts);verts.append(key)
                return ix[key]
            for left,right in zip(splits,splits[1:]):
                section=outline.intersection(box(left,vlow-.001,right,vhigh+.001))
                if section.geom_type!='Polygon' or section.area<1e-10:continue
                indices=[idx(u,v)for u,v in list(section.exterior.coords)[:-1]]
                for j in range(1,len(indices)-1):
                    a,c,d=indices[0],indices[j],indices[j+1]
                    if len({a,c,d})==3:
                        cross=(verts[c][0]-verts[a][0])*(verts[d][1]-verts[a][1])-(verts[c][1]-verts[a][1])*(verts[d][0]-verts[a][0])
                        if abs(cross)>1e-13:tris.append((a,c,d) if cross>0 else (a,d,c))
            if not tris:return
            top=[];bottom=[]
            for u,v in verts:
                x,y=map_plan(u,v)
                crown=.5+.5*cos(2*pi*(u+phase)/pitch)
                t=min(1,max(0,(v-lower)/(upper-lower)))
                lift=.019*(1-t)+.0025*t+.009*crown
                if nose:
                    hi=z_at(x,y)+.016+.009*crown
                    lo=z_at(x,y)+.0006+.006*crown
                else:
                    hi=z_at(x,y)+lift
                    lo=hi-.007
                top.append(world(p,x,y,hi));bottom.append(world(p,x,y,lo))
            count=len(verts);faces=tris+[tuple(k+count for k in reversed(f))for f in tris]
            boundary=set()
            for tri in tris:
                for a,c in zip(tri,tri[1:]+tri[:1]):
                    if (c,a) in boundary:boundary.remove((c,a))
                    else:boundary.add((a,c))
            faces.extend((c,a,a+count,c+count)for a,c in boundary)
            # map_plan has determinant +1 for the front and one wing, -1 on the other.
            if not front and sign<0:faces=[tuple(reversed(f)) for f in faces]
            mat=TILE_DARK if nose else fills[(row+(0 if front else 2))%len(fills)]
            b.add(top+bottom,faces,mat,f'{tag} course {row:02d} '+('undercut' if nose else 'rolled clay'))
        piece(lower,upper+.001,False)
        piece(lower-.0014,lower+.0025,True)


def roof(b,p,lod):
    p=dict(p,center_x=p['center_x']-.024*p['post_span'])
    fy=-p['fascia_projection_ratio']; depth=p['ridge_setback_ratio']; back=p['rear_cut_ratio']
    height=p['ridge_height_ratio']; side=.809; edge=1.06133133
    low=.416; toe=.362
    fork=.496
    clip_z=low+(height-low)*(side-fork)/side
    triangle=[(-fork,fy,clip_z),(fork,fy,clip_z),(0,depth,height)]
    patches=[('cropped front hip',triangle,True)]
    for side_sign,tag in [(-1,'left'),(1,'right')]:
        def vertex(x,y,z): return (x*side_sign,y,z)
        patches.append((tag+' main pitch',[vertex(fork,fy,clip_z),vertex(side,fy,low),vertex(side,back,low),vertex(0,back,height),vertex(0,depth,height)],False))
        patches.append((tag+' flared pitch',[vertex(side,fy,low),vertex(edge,fy,toe),vertex(edge,back,toe),vertex(side,back,low)],False))
    for tag,vs,front in patches:
        plane=np.linalg.lstsq(np.array([[x,y,1] for x,y,z in vs]),np.array([z for x,y,z in vs]),rcond=None)[0]
        poly=Polygon([(x,y)for x,y,z in vs])
        def z_at(x,y): return plane[0]*x+plane[1]*y+plane[2]
        shell(b,p,[(x,y,z-.010)for x,y,z in vs],[(x,y,z-.036)for x,y,z in vs],SOFFIT,tag+' soffit')
        shell(b,p,vs,[(x,y,z-.012)for x,y,z in vs],TILE,tag+' tile field')
        front_edge=vs[:2]
        if tag.endswith('main pitch') or tag.endswith('flared pitch') or front:
            (x1,y1,z1),(x2,y2,z2)=front_edge
            profile_sweep(b,p,[[(x,fy-.004,z-.054),(x,fy+.017,z-.054),(x,fy+.017,z-.009),(x,fy-.004,z-.009)]for x,z in [(x1,z1),(x2,z2)]],WOOD,tag+' dark fascia')
        overlapping_courses(b,p,poly,z_at,tag,front,lod)
    for sign,name in [(-1,'left'),(1,'right')]:
        b.tube([world(p,sign*fork,fy,clip_z+.008),world(p,0,depth,height+.01)],.015*p['post_span'],RIDGE,6 if lod else 10,name+' front hip tile')
    if back>depth+.001:
        b.tube([world(p,0,depth,height+.01),world(p,0,back,height+.01)],.016*p['post_span'],RIDGE,6 if lod else 10,'veranda ridge tile')

def add_veranda(b,lod=False,layout=None):
    """Build all visible elements, including the front clipped roof to its registered rear section."""
    p=settings(layout)
    for k,v in PALETTE.items(): b.palette.setdefault(k,v)
    veranda_body(b,p,lod)
    balcony(b,p,lod)
    roof(b,p,lod)
