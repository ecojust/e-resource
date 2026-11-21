"""The street-facing eastern porch on the north 4C013 house. All sizes are metres."""
import math
from random import Random
from shapely.geometry import Point, Polygon, box
from photo_architecture import Facade
WALL='Olive-grey roughcast'; GRAIN='Pale grey coarse grains'; STONE='Warm grey cast lintels'
FRAME='Red-brown shutter frames'; WOOD='Red-brown louvres'; DARK='Dark wood door'
GLASS='Recessed shaded glass'; SOFFIT='Sheltered pale plaster'; TILE='Warm grey-red roof tiles'
GUTTER='Painted rainwater metal'; PAVE='Worn porch paving'
MATERIALS={name:dict(color=color,roughness=roughness) for name,color,roughness in [
 (WALL,[.39,.385,.34],.96),(GRAIN,[.48,.472,.41],.96),(STONE,[.65,.612,.477],.89),
 (FRAME,[.32,.157,.112],.82),(WOOD,[.40,.192,.14],.86),(DARK,[.235,.177,.146],.89),
 (GLASS,[.142,.167,.16],.43),(SOFFIT,[.50,.484,.416],.92),(TILE,[.486,.307,.219],.94),
 (GUTTER,[.245,.255,.235],.8),(PAVE,[.47,.46,.421],.94)]}
HALF=1.405
RETURN=2.04
EAVE=8.12
FLAT=4.50
EAST=-3.48
WEST=3.42
BACK=5.12

def roof_height(y):
    return 8.16+(y+.24)*.275

def side_outline(f,z0):
    half=f.length/2
    return Polygon([(-half,z0),(half,z0),(half,roof_height(f.b[1])-.03),
                    (-half,roof_height(f.a[1])-.03)])

def block(builder,label,material,x0,x1,y0,y1,z0,z1):
    builder.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),material,label=label)

def grit(face,surface,seed,lod):
    rng=Random(seed)
    point_count=round(surface.area*(5 if lod else 110))
    x0,z0,x1,z1=surface.bounds
    verts=[];faces=[]
    for _ in range(point_count):
        x=rng.uniform(x0,x1);z=rng.uniform(z0,z1)
        if not surface.contains(Point(x,z)):continue
        a=rng.uniform(.011,.032);b=rng.uniform(.009,.023)
        base=len(verts)
        verts.extend([face.point(x-a,z,.0015),face.point(x+.48*a,z-.88*b,.002),
                      face.point(x+.85*a,z+.82*b,.002),face.point(x-.1*a,z+.21*b,rng.uniform(.005,.014))])
        faces.extend([(base,base+1,base+3),(base+1,base+2,base+3)])
    if verts:face.builder.add(verts,faces,GRAIN,face.label+'/Roughcast aggregate')

def paired_shutters(face,u,z,width,height,lod,label,cut_to_front=False):
    def draw(profile, back, front, material, part):
        if cut_to_front:
            profile=profile.intersection(box(-face.length/2,-1.,face.length/2,12.))
            if profile.is_empty or profile.area<1e-8:
                return
        face.prism(profile,back,front,material,part)
    opening=box(u-width/2,z,u+width/2,z+height)
    draw(opening,-.155,-.12,GLASS,label+' inner sash')
    draw(opening.difference(opening.buffer(-.043,join_style=2)),-.12,.016,FRAME,label+' casing')
    for index in range(2):
        mid=u+(index-.5)*(width-.125)/2
        wide=(width-.125)/2-.018
        area=box(mid-wide/2,z+.046,mid+wide/2,z+height-.046)
        rim=area.difference(area.buffer(-.054,join_style=2))
        draw(area,-.089,-.070,WOOD,label+' back leaves')
        draw(rim,-.067,-.003,FRAME,label+' stile rails')
        n=10 if lod else max(13,int(height/.082))
        for j in range(n):
            zc=z+.10+(height-.20)*(j+.5)/n
            draw(box(mid-wide/2+.059,zc-.018,mid+wide/2-.059,zc+.017),-.068,-.028,WOOD,label+' louvre boards')
        draw(box(mid-wide/2+.044,z+height*.48-.031,mid+wide/2-.044,z+height*.48+.031),-.048,.002,FRAME,label+' meeting rails')
    draw(box(u-width/2-.076,z-.088,u+width/2+.076,z-.009),-.046,.139,STONE,label+' external sill')

def porch_front(b,lod):
    f=Facade(b,(-HALF,0),(HALF,0),'Projecting east bay')
    area=box(-.74,5.76,.74,7.47)
    surface=f.wall(FLAT,EAVE,[area],.19,WALL)
    grit(f,surface.buffer(-.05),204,lod)
    paired_shutters(f,0,5.76,1.48,1.71,lod,'Upper paired shutters')
    block(b,'Door canopy roof',STONE,-1.52,1.52,-.19,RETURN+.05,4.35,4.54)
    block(b,'Porch soffit',SOFFIT,-1.39,1.39,-.08,RETURN-.025,4.31,4.35)
    # The thin lip, pale cap and darker undersurface are separately visible.
    f.prism(box(-1.525,4.49,1.525,4.555),.052,.203,STONE,'Shallow projecting drip')
    for sx in (-1,1):
        mid=sx*1.294
        block(b,'Porch '+('east' if sx<0 else 'west')+' support',SOFFIT,mid-.112,mid+.112,-.005,.22,.10,4.31)
        block(b,'Support foot',STONE,mid-.136,mid+.136,-.033,.242,.065,.255)
        block(b,'Support neck',STONE,mid-.135,mid+.135,-.031,.243,4.21,4.32)
    block(b,'Entrance slab',PAVE,-1.45,1.45,-.19,RETURN,.026,.097)
    block(b,'Paving front nosing',STONE,-1.46,1.46,-.24,-.10,.023,.087)
    back=Facade(b,(-HALF,RETURN),(HALF,RETURN),'Recessed entrance')
    hole=box(-.98,.098,.98,3.35)
    back.wall(.04,4.34,[hole],.21,SOFFIT)
    back.prism(hole,-.25,-.215,DARK,'Door reveal in shade')
    for ux in (-.45,.45):
        back.prism(box(ux-.439,.10,ux+.439,2.64),-.218,-.157,DARK,'Double leaf')
        lights=box(ux-.361,1.26,ux+.361,2.52)
        back.prism(lights,-.157,-.138,GLASS,'Dark upper lights')
        back.prism(lights.difference(lights.buffer(-.042,join_style=2)),-.138,-.102,DARK,'Timber light frames')
        back.prism(box(ux-.398,.25,ux+.398,1.12),-.155,-.118,DARK,'Lower door panels')
    back.prism(box(-.92,2.70,.92,3.29),-.19,-.155,GLASS,'Transom in shadow')
    back.prism(box(-.94,2.62,.94,2.72),-.18,-.075,DARK,'Door head')
    back.prism(box(-.027,2.70,.027,3.30),-.15,-.092,DARK,'Transom centre')
    back.prism(hole.difference(hole.buffer(-.064,join_style=2)),-.18,-.06,DARK,'Rebated door jamb')

def side_walls(b,lod):
    for sign,word in [(-1,'east'),(1,'west')]:
        start,stop=((sign*HALF,RETURN),(sign*HALF,0)) if sign<0 else ((sign*HALF,0),(sign*HALF,RETURN))
        f=Facade(b,start,stop,word.capitalize()+' porch cheek')
        holes=[];center=-.02
        if sign>0:
            # The dark round opening is seen independently from two positions west of the bay.
            main=Point(center,6.67).buffer(.365,quad_segs=12 if lod else 28)
            holes=[main]
        surface=f.wall(FLAT,roof_height(RETURN),holes,.175,WALL,outline=side_outline(f,FLAT))
        grit(f,surface.buffer(-.055),107+sign,lod)
        if sign>0:
            lip=main.buffer(.053,quad_segs=12 if lod else 28).difference(main)
            f.prism(lip,-.02,.041,STONE,'Oculus rim')
            f.prism(main,-.213,-.188,GLASS,'Oculus dark glazing')
            inside=main.difference(main.buffer(-.026,quad_segs=12))
            f.prism(inside,-.184,-.13,GUTTER,'Oculus inner frame')
    wings=[(EAST,-HALF,'East wing'),(HALF,WEST,'West wing')]
    for i,(x0,x1,label) in enumerate(wings):
        f=Facade(b,(x0,RETURN),(x1,RETURN),label)
        if i==0:
            # A broad paired window sits below the projecting bay's sill.
            # Its left margin extends beyond this short facade study.
            dx=-2.96-(x0+x1)/2
            windows=[(dx,3.90,1.93,2.02,'Wide east flank window')]
        else:
            windows=[(.08,1.13,.79,2.,'Street window'),(.08,5.72,.79,1.71,'Upper window')]
        span=box(-f.length/2,.03,f.length/2,roof_height(RETURN)-.03)
        cuts=[box(dx-width/2,z,dx+width/2,z+ht).intersection(span)
              for dx,z,width,ht,part in windows]
        surface=f.wall(.03,roof_height(RETURN)-.03,cuts,.20,WALL)
        grit(f,surface.buffer(-.05),401+i,lod)
        f.prism(box(-f.length/2,.04,f.length/2,.27),.002,.038,STONE,'Base course')
        for dx,z,width,ht,part in windows:
            paired_shutters(f,dx,z,width,ht,lod,part,cut_to_front=i==0)
        x=x0 if i==0 else x1
        start,end=((x,BACK),(x,RETURN)) if i==0 else ((x,RETURN),(x,BACK))
        endwall=Facade(b,start,end,label+' cut return')
        endwall.wall(.03,roof_height(BACK),(),.13,WALL,outline=side_outline(endwall,.03))
    # A continuous ceiling is seen between the outer posts and the deeply set inner door.
    for x in (-HALF,HALF):
        block(b,'Canopy side lip',STONE,x-.042,x+.042,-.02,RETURN+.045,4.46,4.549)

def roof(b,lod):
    # Only the roof on this short cut is included. The dormers are farther
    # along the frontage and the existing roof continues beyond the cut.
    def strip(x0,x1,y0,y1,label):
        polygon=[(x0,y0,roof_height(y0)),(x1,y0,roof_height(y0)),(x1,y1,roof_height(y1)),(x0,y1,roof_height(y1))]
        b.add(polygon,[(0,1,2),(0,2,3)],TILE,label+' roof plane')
        ny=max(1,round((y1-y0)/(.47 if lod else .28)))
        nx=max(1,round((x1-x0)/(.54 if lod else .22)))
        for j in range(ny):
            ya=y0+(y1-y0)*j/ny;yb=y0+(y1-y0)*(j+1)/ny
            b.tube([(x0,ya,roof_height(ya)+.015),(x1,ya,roof_height(ya)+.015)],.018,TILE,4 if lod else 7,label+' tile course')
            for k in range(nx):
                x=x0+(x1-x0)*(k+.5*(j%2))/nx
                b.tube([(x,ya,roof_height(ya)+.02),(x,yb,roof_height(yb)+.014)],.015,TILE,4 if lod else 5,label+' tile ribs')
        b.tube([(x0,y0-.005,roof_height(y0)-.045),(x1,y0-.005,roof_height(y0)-.045)],.048,GUTTER,7 if lod else 12,label+' eaves gutter')
        block(b,label+' eaves underside',DARK,x0,x1,y0,y0+.17,roof_height(y0)-.125,roof_height(y0)-.010)
    strip(EAST,-HALF-.13,RETURN-.18,BACK,'East roof')
    strip(-HALF-.13,HALF+.13,-.23,BACK,'Porch roof')
    strip(HALF+.13,WEST,RETURN-.18,BACK,'West roof')

def add_building(builder,lod=False):
    porch_front(builder,lod)
    side_walls(builder,lod)
    roof(builder,lod)
