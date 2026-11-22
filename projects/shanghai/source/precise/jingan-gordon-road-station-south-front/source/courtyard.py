"""Photo-derived three-storey portion of the south courtyard elevation, viewed towards the building."""
from math import cos, pi, sin
from shapely.geometry import LineString, Polygon, box as rect
from shapely.ops import unary_union

from photo_architecture import Facade, opening

BRICK='Weathered red brick'
HEADER='Red moulded brick'
LIGHT='Pale lintel stone'
STONE='Warm stone capitals'
TIMBER='Deep red timber'
GLASS='Reflected courtyard glazing'
DARK='Dark door recess'
ROOF='Weathered red tile'
MORTAR='Brick joints'
SOFFIT='Dark eave timber'
MATERIALS={k:{'color':c,'roughness':r} for k,c,r in [
 (BRICK,[.57,.309,.22],.91),(HEADER,[.53,.245,.16],.85),(LIGHT,[.75,.719,.64],.87),
 (STONE,[.62,.56,.44],.86),(TIMBER,[.33,.145,.11],.72),(GLASS,[.255,.30,.29],.38),
 (DARK,[.175,.15,.125],.96),(ROOF,[.41,.286,.21],.88),(MORTAR,[.48,.305,.23],.95),
 (SOFFIT,[.285,.215,.155],.84)]}
# These coordinates refer to the central bay and are estimated from the photographed facade.
# The recovered host footprint determines its placement and the retained building beyond it.
HALF=7.25
PEAK=15.30
EAVES=12.43
LEVEL_1=4.30
LEVEL_2=8.54
GABLE_HALF=2.32
GALLERY_END=7.10
PORCH_Y=.98
BACK_Y=3.10
RETURN_Y=-1.05


def block(face,l,r,b,t,d0,d1,m,n):
    face.box((l+r)/2,(b+t)/2,r-l,t-b,d1-d0,(d1+d0)/2,m,n)


def frame(face,shape,back,distant,cols,rows,label,opaque=False):
    """Set the glass or opaque leaf behind the reveal, then clip real rails to the arch."""
    face.prism(shape.buffer(.008,join_style=2),back-.075,back-.047,DARK if opaque else GLASS,label+' panes')
    x0,z0,x1,z1=shape.bounds
    inner=shape.buffer(-.085,join_style=2)
    bars=[shape.difference(inner)]
    for i in range(1,cols):
        x=x0+(x1-x0)*i/cols
        bars.append(rect(x-.024,z0,x+.024,z1).intersection(inner))
    for t in rows:
        z=z0+(z1-z0)*t
        bars.append(rect(x0,z-.039,x1,z+.039).intersection(inner))
    face.prism(unary_union(bars),back-.017,back+.044,TIMBER,label+' frame')


def brick_courses(face,wall,y,label,distant):
    """Only every fifth brick course is accented in the far mesh."""
    x0,z0,x1,z1=wall.bounds
    step=.225
    mask=[]
    for i in range(1,int((z1-z0)/step)):
        z=z0+i*step
        if not distant or i%5==0:
            mask.append(rect(x0,z-.006,x1,z+.006))
        if not distant and i%3==0:
            for col in range(int((x1-x0)/.54)):
                x=x0+(col+.32+(i%2)*.5)*.54
                mask.append(rect(x-.007,z,x+.007,min(z1,z+step)))
    if mask:
        face.prism(unary_union(mask).intersection(wall),y+.002,y+.010,MORTAR,label)


def gallery_rails(face,l,r,z,label,distant):
    block(face,l,r,z+.04,z+.15,-.10,.02,TIMBER,label+' foot')
    block(face,l,r,z+.91,z+1.04,-.13,.06,TIMBER,label+' handrail')
    count=max(3,round((r-l)/(.22 if distant else .145)))
    for i in range(count):
        u=l+(i+.5)*(r-l)/count
        block(face,u-.019,u+.019,z+.145,z+.913,-.067,-.009,TIMBER,label+' spindles')


def shaft(face,u,z0,z1,label,distant):
    """Square brick pier terminating in a clustered stone capital and short shaft."""
    block(face,u-.19,u+.19,z0,z1-1.40,-.30,.15,BRICK,label+' brick pier')
    for half,za,zb in ((.29,z1-1.44,z1-1.21),(.235,z1-1.21,z1-1.04),(.175,z1-1.04,z1-.37),(.225,z1-.37,z1-.22),(.285,z1-.22,z1-.08)):
        block(face,u-half,u+half,za,zb,-.23,half-.045,STONE,label+' stepped capital')


def arch_stones(face,u,bottom,width,height,rise,distant,label):
    count=21 if not distant else 11
    upper=label=='Upper'
    span=.55 if upper else .38
    crown=.68 if upper else .52
    spring=bottom+height-rise
    for n in range(count):
        lo=n*pi/count+.01;hi=(n+1)*pi/count-.01;ts=(lo,(lo+hi)/2,hi)
        def curve(t,outer):
            return u+cos(t)*(width/2+(span if outer else 0)),spring+sin(t)*(rise+(crown if outer else 0))
        p=Polygon([curve(t,False)for t in ts]+[curve(t,True)for t in reversed(ts)])
        face.prism(p,.012,.105,HEADER,label+' brick arch')
    face.prism(Polygon([(u-.12,spring+rise-.04),(u+.12,spring+rise-.04),(u+.19,spring+rise+crown+.07),(u-.19,spring+rise+crown+.07)]),.02,.20,STONE,label+' keystone')


def portal(face,hole):
    half=1.38
    inside=.99
    for sign in (-1,1):
        l,r=sorted((sign*inside,sign*half))
        jamb=Polygon([(sign*.97,0),(sign*1.49,0),(sign*1.34,2.64),(sign*.97,2.64)])
        face.prism(jamb,.01,.18,LIGHT,'Splayed door jamb')
        block(face,l-.04,r+.04,.04,.21,.16,.23,STONE,'Door base')
    # A shallow swept lintel is wider than the opening. Both returns terminate over the piers.
    points=[(-1.94,2.54),(-1.55,2.56),(-1.19,2.75),(-.72,2.94),(0,3.04),(.72,2.94),(1.19,2.75),(1.55,2.56),(1.94,2.54)]
    upper=[(u,z+.27)for u,z in points]
    face.prism(Polygon(points+upper[::-1]),.00,.27,LIGHT,'Arcuated entrance lintel')
    for off,size in ((.027,.055),(.242,.071)):
        face.prism(LineString([(u,z+off)for u,z in points]).buffer(size/2,cap_style=2,join_style=2),.25,.326,STONE,'Lintel edge moulding')
    # The photographed stone reveals narrow towards the two dark leaves.
    # Use the same arch sampling for each edge of the sloping reveal.
    inside=opening(0,.03,1.36,2.30,.20,16)
    outside=opening(0,.03,1.94,2.58,.27,16)
    near=list(outside.exterior.coords)[:-1]
    far=list(inside.exterior.coords)[:-1]
    vertices=[face.point(x,z,depth)for edge,depth in ((near,.10),(far,-.84)) for x,z in edge]
    count=len(near)
    faces=[]
    for i in range(1,count):
        j=(i+1)%count
        faces.extend([(i,j,j+count),(i,j+count,i+count)])
    face.builder.add(vertices,faces,STONE,'Splayed stone entrance reveals')
    face.prism(hole.buffer(.009),-.965,-.946,DARK,'Dark entrance return')
    frame(face,inside,-.89,False,2,[.79],'Central doorway',True)


def plate_wall(face,w,t,distant,y,label,holes):
    wall=rect(-w/2,0,w/2,t).difference(unary_union(holes)) if holes else rect(-w/2,0,w/2,t)
    face.prism(wall,y-.34,y,BRICK,label)
    brick_courses(face,wall,y,label+' joints',distant)


def roof_plate(builder,points,material,label):
    lower=[(x,y,z-.11)for x,y,z in points]
    roof_faces=[(0,1,2),(0,2,3),(4,6,5),(4,7,6)]
    for i in range(4):
        j=(i+1)%4
        roof_faces.extend([(i,j,j+4),(i,j+4,i+4)])
    builder.add(points+lower,roof_faces,material,label)


def pitched_patch(builder,x0,x1,y0,y1,z0,z1,material,label):
    points=[(x0,y0,z0),(x1,y0,z0),(x1,y1,z1),(x0,y1,z1)]
    roof_plate(builder,points,material,label)


def add_building(b,distant=False):
    f=Facade(b,(-HALF,0),(HALF,0),'Courtyard')
    door=opening(0,.03,2.0,2.58,.27,16)
    mid=opening(0,5.01,2.22,2.45,.37,16)
    top=opening(0,9.63,2.33,2.03,.88,20)
    polygon=Polygon([(-GABLE_HALF,0),(GABLE_HALF,0),(GABLE_HALF,EAVES),(0,PEAK),(-GABLE_HALF,EAVES)])
    wall=polygon.difference(unary_union([door,mid,top]))
    f.prism(wall,-.39,0,BRICK,'Central gable and reveals')
    brick_courses(f,wall,0,'Central brick bond',distant)
    portal(f,door)
    for g,columns,rs,name in [(mid,4,[.68],'Segmented middle window'),(top,4,[.35,.67],'Round upper window')]:
        frame(f,g,-.26,distant,columns,rs,name)
        block(f,g.bounds[0]-.13,g.bounds[2]+.13,g.bounds[1]-.11,g.bounds[1]-.025,0,.15,HEADER,name+' sill')
    arch_stones(f,0,9.63,2.33,2.03,.88,distant,'Upper')
    arch_stones(f,0,5.01,2.22,2.45,.37,distant,'Middle')
    for z,w,d in ((3.47,1.82,.14),(7.80,1.52,.13),(8.30,1.52,.16),(9.06,1.55,.13),(9.32,1.31,.14)):
        block(f,-w,w,z-.055,z+.045,-.015,d,STONE if z in (3.47,8.30,9.32) else HEADER,'Window apron and portal courses')
    for sign in (-1,1):
        u=sign*(GABLE_HALF-.17)
        block(f,u-.13,u+.13,.19,EAVES-.32,-.018,.16,HEADER,'Brick edge pilasters')
        block(f,u-.21,u+.21,EAVES-.57,EAVES-.05,.08,.23,STONE,'Stone corbel')
        for k in (-1,0,1):
            block(f,u+k*.105-.022,u+k*.105+.022,EAVES-.54,EAVES-.12,.22,.27,LIGHT,'Corbel flutes')
    for z,w in ((4.18,GABLE_HALF+.09),(8.20,GABLE_HALF+.06),(12.47,GABLE_HALF-.08),(13.34,1.51),(14.42,.64)):
        block(f,-w,w,z-.056,z+.054,0,.095,STONE if z>=12 or z==4.18 else HEADER,'Gable horizontal dressings')
    f.prism(LineString([(-GABLE_HALF-.05,EAVES),(0,PEAK),(GABLE_HALF+.05,EAVES)]).buffer(.087,cap_style=2,join_style=2),-.14,.12,STONE,'Sloping stone coping')
    for i in (-1,1):
        a,bx=sorted((i*GABLE_HALF,i*GALLERY_END));center=(a+bx)/2
        # Gallery return is a real courtyard wall seen obliquely behind the face.
        for ux,inner in ((i*GABLE_HALF,0),(i*GALLERY_END,RETURN_Y)):
            end=Facade(b,(ux,inner),(ux,BACK_Y), 'Courtyard returns') if ((ux>0)==(abs(ux)==GABLE_HALF)) else Facade(b,(ux,BACK_Y),(ux,inner),'Courtyard returns')
            end.prism(rect(-end.length/2,0,end.length/2,EAVES-.14),-.14,.015,BRICK,'Side wall')
        g=Facade(b,(a,PORCH_Y),(bx,PORCH_Y),'Gallery')
        ground=[]
        for d in (-1,1):
            u=d*(bx-a)*.24
            hole=opening(u,.54,1.26,2.41,.59,18);ground.append(hole)
            frame(g,hole,-.25,distant,2,[.52,.82],'Ground arched window')
        low=rect(-(bx-a)/2,0,(bx-a)/2,LEVEL_1).difference(unary_union(ground))
        g.prism(low,-.33,0,BRICK,'Ground arcade wall')
        brick_courses(g,low,0,'Ground brickwork',distant)
        for z in (LEVEL_1,LEVEL_2):
            slabfront=PORCH_Y-.13
            b.box([center,(slabfront+BACK_Y)/2,z-.1],[bx-a,BACK_Y-slabfront,.20],HEADER,label='Gallery floor')
            gallery_rails(g,-g.length/2+.07,-.20,z,'Gallery',distant)
            gallery_rails(g,.20,g.length/2-.07,z,'Gallery',distant)
        # The red masonry pier continues through the middle gallery to the stone capital at the top.
        block(g,-.21,.21,LEVEL_1,LEVEL_2+.04,-.29,.17,BRICK,'Continuous brick pier')
        shaft(g,0,LEVEL_2,EAVES,'Upper',distant)
        for side in (-1,1):
            u=side*(g.length/2-.15)
            shaft(g,u,LEVEL_2,EAVES,'Respond',distant)
        pillars=[-g.length/2+.12,0,g.length/2-.12]
        openings=[]
        for n in range(2):
            l=pillars[n]+.20;r=pillars[n+1]-.20
            op=opening((l+r)/2,LEVEL_1,r-l,LEVEL_2-LEVEL_1-.54,.23,14)
            openings.append(op)
        spandrel=rect(-g.length/2,LEVEL_2-1.05,g.length/2,LEVEL_2-.025).difference(unary_union(openings))
        g.prism(spandrel,-.31,.12,BRICK,'Middle gallery arch soffits')
        rear=Facade(b,(a,BACK_Y),(bx,BACK_Y),'Recessed gallery')
        holes=[]
        for z in (LEVEL_1,LEVEL_2):
            for j in (-1,1):
                u=j*(bx-a)*.22
                shape=opening(u,z+.29,1.28,2.40,.11,12);holes.append(shape)
                frame(rear,shape,-.22,distant,2,[.62],'Inner wood window')
        plate_wall(rear,bx-a,EAVES,distant,0,'Shaded gallery rear',holes)
        for z in (LEVEL_2,EAVES):
            block(g,-g.length/2,g.length/2,z-.16,z+.06,-.14,.16,SOFFIT,'Dark eave band')
        # The two forward piers bound the portion in view; the adjoining bays belong to the retained building.
        line=i*GALLERY_END
        b.box([line,RETURN_Y+.095,EAVES/2],[.24,.24,EAVES],BRICK,label='Cut edge of adjacent bay')
        pitched_patch(b,a,bx,PORCH_Y-.18,BACK_Y+.28,EAVES+.05,EAVES+.95,ROOF,'Gallery roof')
        x0,x1=sorted((i*GALLERY_END,i*HALF))
        pitched_patch(b,x0,x1,RETURN_Y-.19,BACK_Y+.28,EAVES+.05,EAVES+1.15,ROOF,'Near edge of wing roof')
    for i in (-1,1):
        xl,xr=sorted((0,i*(GABLE_HALF+.09)))
        def roof_z(x):return PEAK+.06-abs(x)/GABLE_HALF*(PEAK-EAVES)
        roof_plate(b,[(xl,-.15,roof_z(xl)),(xr,-.15,roof_z(xr)),(xr,BACK_Y+.28,roof_z(xr)),(xl,BACK_Y+.28,roof_z(xl))],ROOF,'Gable roof')
