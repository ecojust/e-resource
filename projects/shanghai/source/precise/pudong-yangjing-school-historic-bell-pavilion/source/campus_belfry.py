"""The freestanding clock pavilion and suspended historic bronze bell in front of Yangjing's 1947 building."""
from math import cos,sin,pi,sqrt

COLORS={'aged post':(.107,.057,.046),'post highlight':(.145,.074,.056),
        'beam end':(.126,.064,.045),'beam underside':(.076,.047,.040),
        'dark fascia':(.102,.095,.080),'roof boards':(.247,.237,.199),
        'weathered roof boards':(.297,.284,.251),'ridge':(.365,.348,.301),
        'bronze':(.275,.197,.106),'bronze lip':(.370,.280,.145),
        'dark bronze':(.159,.111,.061),'clapper':(.094,.080,.061),
        'hardware':(.087,.083,.074),'iron shoes':(.081,.084,.077)}
PALETTE={k:{'color':list(v),'roughness':.53 if k in ('bronze','bronze lip','clapper')else .74}for k,v in COLORS.items()}
CUBE=[(0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),(1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)]

def tapered(b,label,bottom,top,base,head,mat):
    verts=[]
    for c,r in [(bottom,base),(top,head)]:
        x,y,z=c;a,d=r
        verts.extend([(x-a,y-d,z),(x+a,y-d,z),(x+a,y+d,z),(x-a,y+d,z)])
    b.add(verts,CUBE,mat,label)

def box(b,label,a,c,y0,y1,lo,hi,mat):
    tapered(b,label,((a+c)/2,(y0+y1)/2,lo),((a+c)/2,(y0+y1)/2,hi),((c-a)/2,(y1-y0)/2),((c-a)/2,(y1-y0)/2),mat)

def panel(b,label,pts,mat):
    # Each trapezoidal roof board forms an independent shallow closed solid.
    vs=pts+[(x,y,z-.021)for x,y,z in pts]
    b.add(vs,[(0,1,2),(0,2,3),(4,6,5),(4,7,6),(0,5,1),(0,4,5),
              (1,6,2),(1,5,6),(2,7,3),(2,6,7),(3,4,0),(3,7,4)],mat,label)

def spin(b,label,profile,mat,sides):
    v=[(radius*cos(2*pi*i/sides),radius*sin(2*pi*i/sides),z)for radius,z in profile for i in range(sides)]
    f=[]
    for j in range(len(profile)):
        after=(j+1)%len(profile)
        for k in range(sides):
            k1=(k+1)%sides;a=j*sides+k;c=j*sides+k1;d=after*sides+k;e=after*sides+k1
            f.extend([(a,c,e),(a,e,d)])
    b.add(v,f,mat,label)

def bell(b,lod):
    n=28 if lod else 64
    outer=[(.218,1.923),(.227,1.935),(.222,1.949),(.203,1.963),(.192,1.979),(.174,2.009),(.157,2.055),(.144,2.118),(.136,2.174),(.125,2.210),(.108,2.230),(.083,2.242),(.046,2.248)]
    inner=[(.046,2.231),(.076,2.228),(.099,2.215),(.117,2.181),(.129,2.121),(.145,2.053),(.164,2.005),(.184,1.965),(.203,1.932),(.205,1.923)]
    spin(b,'hollow historic bronze bell',outer+inner,'bronze',n)
    for idx,(rad,z) in enumerate([(.222,1.941),(.202,1.965),(.158,2.052),(.121,2.215)]):
        spin(b,f'cast circumferential ring {idx+1}',[(rad-.003,z-.004),(rad+.005,z-.003),(rad+.005,z+.003),(rad-.003,z+.004)],'bronze lip',n)
    spin(b,'crown below suspension',[(.004,2.235),(.046,2.235),(.049,2.245),(.035,2.259),(.004,2.265)],'dark bronze',n)
    spin(b,'interior clapper stem',[(.004,1.945),(.011,1.945),(.011,2.232),(.004,2.232)],'hardware',16)
    spin(b,'bell clapper with striking head',[(.002,1.853),(.019,1.858),(.034,1.877),(.040,1.899),(.034,1.918),(.014,1.929),(.010,1.951),(.002,1.951)],'clapper',18 if lod else 32)
    box(b,'short dark clapper tail',-.004,.004,-.005,.005,1.804,1.867,'clapper')
    for x in [-.018,.018]:
        box(b,'suspension strap left'if x<0 else'suspension strap right',x-.005,x+.005,-.008,.008,2.25,2.325,'hardware')

def add_building(b,lod):
    for sx in (-1,1):
        for sy in (-1,1):
            name=('left'if sx==-1 else'right')+(' back'if sy==1 else' front')
            top=(.309*sx,.292*sy,2.45);foot=(.470*sx,.405*sy,0)
            tapered(b,name+' splayed timber',foot,top,(.055,.050),(.056,.054),'aged post'if sx<0 else'post highlight')
            tapered(b,name+' foot ferrule',(foot[0],foot[1],.004),(foot[0],foot[1],.040),(.058,.053),(.058,.053),'iron shoes')
    for y in [-.292,.292]:
        box(b,'front carrying beam'if y<0 else'rear carrying beam',-.382,.382,y-.05,y+.05,2.337,2.439,'beam end')
    for x in [-.309,.309]:
        box(b,'left tie'if x<0 else'right tie',x-.050,x+.050,-.354,.354,2.285,2.367,'beam underside')
    box(b,'central bell yoke',-.335,.335,-.043,.043,2.314,2.387,'beam underside')
    tapered(b,'square soffit at eaves',(0,0,2.430),(0,0,2.469),(.526,.490),(.563,.529),'dark fascia')
    ring=[(-.582,-.548),(.582,-.548),(.582,.548),(-.582,.548)]
    for face in range(4):
        a=ring[face];c=ring[(face+1)%4]
        def point(p,t,z):return(p[0]*t,p[1]*t,z)
        for j in range(8):
            za=2.466+j*.026;zb=za+.028
            s0=1-j*.116;s1=1-(j+1)*.116
            vs=[point(a,s0,za),point(c,s0,za),point(c,s1,zb),point(a,s1,zb)]
            panel(b,f'hip {face+1} overlapping course {j+1}',vs,'roof boards'if j%3 else'weathered roof boards')
    tapered(b,'small cap over four roof hips',(0,0,2.665),(0,0,2.689),(.055,.051),(.011,.010),'ridge')
    bell(b,lod)
