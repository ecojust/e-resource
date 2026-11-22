"""Small pitched courtyard wall and its left-hand six-light casements, Jiaozhou Road Lane 125."""
from math import cos, pi
from random import Random


def finish(rgb,rough=.84):
    linear=[c/3294.6 if c<=10 else ((c/255+.055)/1.055)**2.4 for c in rgb]
    return dict(color=linear,roughness=rough,metallic=0)

PALETTE={name:finish(rgb) for name,rgb in {
    'pink render':(213,172,163),'sand grains':(190,150,138),'pale grains':(226,190,176),
    'grey plinth':(104,111,113),'weathered plinth':(144,146,141),'verge cement':(143,141,132),
    'tile burnt umber':(144,87,66),'tile dried earth':(161,104,82),'tile dark red':(126,78,62),
    'roof shadow':(81,64,54),'window trim':(219,217,204),'wood':(111,51,43),
    'wood edge':(124,64,53),'window glass':(72,72,67),'gate iron':(64,62,61),
    'dark behind gate':(51,48,44),'casement hinge':(98,92,80)}.items()}
XLEFT=-.82
XPEAK=0.
XRIGHT=.82
EAVE=2.46
RIDGE=3.30
ROOF_DEPTH=1.12
WIN=(-2.55,-1.82,.86,2.02)


def box(b,x0,x1,y0,y1,z0,z1,mat,name):
    b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),mat,label=name)


def roof_height(x):
    return RIDGE-(RIDGE-EAVE)*abs(x)/XRIGHT


def prism(b,points,y0,y1,mat,name):
    n=len(points);v=[(x,y,z) for y in (y0,y1) for x,z in points]
    faces=[(0,i,i+1)for i in range(1,n-1)]
    faces.extend((n,i+n+1,i+n)for i in range(1,n-1))
    faces.extend((i,i+n,(i+1)%n+n,(i+1)%n)for i in range(n))
    b.add(v,faces,mat,name)


def pink_wall(b):
    # Openings in the lane elevation are built out of separate masonry strips.
    x0,x1,zb,zt=WIN
    for i,(a,c,l,h) in enumerate([(-2.90,x0,0,2.40),(x1,-1.62,0,2.40),(x0,x1,0,zb),(x0,x1,zt,2.40)]):
        box(b,a,c,.035,.24,l,h,'pink render','left wing masonry '+str(i))
    for a,c in [(-2.90,-1.62),(XLEFT,XRIGHT)]:
        box(b,a,c,-.018,.24,0,.32,'grey plinth','grey render plinth '+str(a))
    box(b,XLEFT,XRIGHT,0,.25,.32,EAVE,'pink render','gable wall lower part')
    prism(b,[(XLEFT,EAVE),(XRIGHT,EAVE),(0,RIDGE)],0,.25,'pink render','gable field')
    for side in (-1,1):
        a,c=sorted((side*.846,0.))
        za,zc=roof_height(a),roof_height(c)
        prism(b,[(a,za-.027),(c,zc-.027),(c,zc+.036),(a,za+.036)],-.029,.080,
              'verge cement','bevelled street verge '+str(side))


def windows(b):
    a,c,base,head=WIN
    box(b,a-.055,c+.055,-.095,.22,base-.058,base+.025,'window trim','projecting white sill')
    box(b,a-.044,c+.044,-.068,.20,head-.015,head+.026,'window trim','white drip lip')
    prism(b,[(a-.035,head+.026),(c+.035,head+.026),(c+.014,head+.059),(a-.014,head+.059)],-.048,.18,'window trim','white sloped drip crown')
    width=(c-a)/2
    for i in range(2):
        left=a+i*width;right=left+width
        for x in (left+.016,right-.016):
            box(b,x-.016,x+.016,.050,.105,base+.031,head-.020,'wood','separate casement stile '+str((i,x)))
        for z in (base+.055,head-.045):
            box(b,left+.022,right-.022,.050,.105,z-.019,z+.019,'wood','casement top bottom rail '+str((i,z)))
        for j in (1,2):
            z=base+.065+j*((head-base)-.13)/3
            box(b,left+.026,right-.026,.063,.089,z-.009,z+.009,'wood edge','glazing horizontal '+str((i,j)))
        mid=(left+right)/2
        box(b,mid-.0065,mid+.0065,.067,.088,base+.065,head-.062,'wood edge','thin upright glazing bar '+str(i))
        box(b,left+.020,right-.020,.113,.120,base+.045,head-.040,'window glass','inset glass '+str(i))


def roof(b,lod):
    rng=Random(125)
    for side in (-1,1):
        x0,x1=sorted((side*.865,0.))
        prism(b,[(x0,roof_height(x0)-.049),(x1,roof_height(x1)-.049),
                 (x1,roof_height(x1)),(x0,roof_height(x0))],.065,ROOF_DEPTH,'roof shadow','roof bed '+str(side))
        # The photograph shows four transverse course ends on the near slope;
        # clay laps are highest at the free edge and cover the lower course.
        for row in range(4):
            start=row*.21;end=(row+1)*.21+.029
            for col in range(7):
                y0=.090+col*.147
                samples=4 if lod else 8
                verts=[];faces=[]
                for k in range(samples+1):
                    s=k/samples;y=y0+.146*s;wave=.018*(1-cos(2*pi*s))
                    for distance,dz in [(start,.005),(end,.026),(end,.008),(start,-.004)]:
                        x=side*distance;verts.append((x,y,roof_height(x)+dz+wave))
                for k in range(samples):
                    for v in range(4):
                        faces.append((k*4+v,(k+1)*4+v,(k+1)*4+(v+1)%4,k*4+(v+1)%4))
                faces.extend([(3,2,1,0),tuple(range(samples*4,samples*4+4))])
                b.add(verts,faces,rng.choice(['tile dried earth','tile burnt umber','tile dark red']),'lapped rolled tile '+str((side,row,col)))
    # The surviving cement ridge runs away from the street into the court.
    prism(b,[(-.067,RIDGE-.014),(.067,RIDGE-.014),(.046,RIDGE+.053),(0,RIDGE+.072),(-.046,RIDGE+.053)],
          .07,ROOF_DEPTH+.020,'verge cement','rendered ridge coping')


def stipple(b,lod):
    rng=Random(156);batches={n:([],[]) for n in ('sand grains','pale grains','weathered plinth')}
    for i in range(1900 if lod else 5900):
        x=rng.uniform(-2.9,.82);z=rng.uniform(.008,RIDGE)
        if -1.62<x<XLEFT:continue
        if x<=-1.62:
            if z>2.39 or WIN[0]-.06<x<WIN[1]+.06 and WIN[2]-.075<z<WIN[3]+.072:continue
            front=.035
        else:
            if z>roof_height(x)-.028:continue
            front=0.
        if z<=.32:
            if i%3:continue
            mat='weathered plinth';front=-.018
        else:mat=rng.choice(('sand grains','pale grains'))
        vs,fs=batches[mat];off=len(vs);w=rng.uniform(.0025,.0075)*(1.4 if lod else 1)
        vs.extend([(x-w,front-.0011,z),(x,front-.0011,z-w*.9),(x+w,front-.0011,z),(x,front-.0011,z+w*.82),(x+w*.15,front-.0052,z)])
        fs.extend((off+4,off+j,off+(j+1)%4)for j in range(4))
    for mat,(vs,fs) in batches.items():b.add(vs,fs,mat,'render grain '+mat)


def add_building(b,lod=False):
    pink_wall(b);windows(b);roof(b,lod);stipple(b,lod)
    for side,(x0,x1) in enumerate([(-1.62,XLEFT),(XRIGHT,1.68)]):
        box(b,x0+.014,x1-.014,.080,.115,.032,1.90,'gate iron','lane gate visible plain sheet '+str(side))
        for x in (x0+.017,x1-.017):box(b,x-.012,x+.012,.110,.156,.03,1.905,'gate iron','gate edge '+str((side,x)))
