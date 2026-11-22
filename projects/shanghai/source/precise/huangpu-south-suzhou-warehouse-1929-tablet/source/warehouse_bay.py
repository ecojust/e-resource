"""The 1929 date tablet, steel factory window and facing brickwork at 955 South Suzhou Road."""
from math import cos, sin, hypot, pi

def material(rgb, metal=0, roughness=.85):
    linear = [(v/255/12.92 if v/255 < .04045 else ((v/255+.055)/1.055)**2.4) for v in rgb]
    return dict(color=linear, roughness=roughness, metallic=metal)

PALETTE = {key:material(value) for key,value in {
    'pointing':(108,101,87), 'kiln brown':(102,85,69), 'sooted blue grey':(83,79,75),
    'fired buff':(139,115,83),'pale date stone':(197,190,170),'lintel grey':(139,132,120),
    'sill stone':(186,173,146),'light brick':(123,105,86),'plain iron':(62,65,65),
    'recess':(59,58,55)}.items()}
PALETTE.update({'date characters':material((48,45,39),.14),'window glass':material((74,83,85),.28,.35)})

def box(b,name,x0,x1,y0,y1,z0,z1,mat):
    vertices=[(x0,y0,z0),(x1,y0,z0),(x1,y0,z1),(x0,y0,z1),
              (x0,y1,z0),(x1,y1,z0),(x1,y1,z1),(x0,y1,z1)]
    b.add(vertices,[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],mat,name)

def strips(b,name,points,widths):
    # The dark numerals use outlined strokes, including the open counter in each 9.
    contour=[]
    for i,((x,z),width) in enumerate(zip(points,widths)):
        left=points[max(i-1,0)];right=points[min(i+1,len(points)-1)]
        dx=right[0]-left[0];dz=right[1]-left[1];length=hypot(dx,dz)
        nx=-dz/length*width/2;nz=dx/length*width/2
        contour.append(((x+nx,z+nz),(x-nx,z-nz)))
    vertices=[(x,y,z) for pair in contour for y in (-.103,-.083) for x,z in pair]
    faces=[(0,1,3,2)]
    for i in range(len(points)-1):
        a=4*i;c=a+4
        faces.extend([(a,a+1,c+1,c),(a+3,a+2,c+2,c+3),(a+2,a,c,c+2),(a+1,a+3,c+3,c+1)])
    a=len(vertices)-4;faces.append((a+2,a+3,a+1,a))
    b.add(vertices,faces,'date characters',name)

def digit(b,index,n,x,low_detail):
    def line(suffix,pts,widths):
        strips(b,f'date {index} {n} {suffix}',[(x+px,2.28+pz) for px,pz in pts],widths)
    if n==1:
        line('main stroke',[(-.085,.298),(-.022,.349),(.007,.358),(.007,.019)],[.024,.039,.060,.057])
        line('foot',[(-.065,.014),(.008,.014),(.077,.014)],[.018,.028,.017])
    if n==9:
        count=14 if low_detail else 36
        pts=[(.004+.094*cos(t*2*pi/count),.252+.097*sin(t*2*pi/count)) for t in range(count+1)]
        line('counter',pts,[.041+.017*abs(cos(t*2*pi/count))for t in range(count+1)])
        line('curved tail',[(.095,.244),(.095,.201),(.089,.154),(.074,.106),(.048,.063),(.006,.030),(-.050,.016),(-.080,.020)],[.055,.061,.061,.056,.050,.041,.026,.016])
    if n==2:
        line('arched head and descending stroke',[(-.100,.263),(-.085,.304),(-.048,.338),(.003,.351),(.056,.339),(.088,.311),(.098,.270),(.088,.222),(.058,.177),(.012,.127),(-.050,.065),(-.102,.013)],[.024,.035,.046,.049,.052,.056,.058,.057,.051,.045,.034,.023])
        line('lower serif',[(-.105,.015),(-.025,.022),(.093,.024),(.104,.061)],[.026,.046,.048,.020])

def add_building(b,lod=False):
    # Render the brick reveals as well as the front faces; no masonry crosses the glass.
    for name,x0,x1,z0,z1 in [('left',-2,-1.48,.0,3.62),('right',1.48,2,.0,3.62),
                             ('top',-1.48,1.48,1.63,3.62),('bottom',-1.48,1.48,0,.23)]:
        box(b,'reveal and brick bed '+name,x0,x1,.027,.29,z0,z1,'pointing')
    brick_mats=['kiln brown','sooted blue grey','light brick','fired buff']
    for row in range(29):
        z0=row*.126;z1=min(z0+.12,3.62)
        if z0>=z1:continue
        for col in range(-1,13):
            x0=-2+col*.351+(row%2)*.1755;x1=x0+.343
            if x1<=-2 or x0>=2:continue
            x0=max(x0,-2);x1=min(x1,2)
            for xa,xb,za,zb in ((x0,min(-1.48,x1),z0,z1),(max(1.48,x0),x1,z0,z1),
                                 (max(-1.48,x0),min(1.48,x1),max(z0,1.63),z1),
                                 (max(-1.48,x0),min(1.48,x1),z0,min(z1,.23))):
                if xb-xa<.009 or zb-za<.006:continue
                noise=(row*29+col*47+row*col*7)%23
                mat=brick_mats[2 if noise in (1,4,17) else 3 if noise==7 else int(noise%3==0)]
                name='brickwork '+mat
                if lod:
                    # One front plane per brick preserves the bond; the common masonry bed carries the returns.
                    b.add([(xa,0,za),(xb,0,za),(xb,0,zb),(xa,0,zb)],[(0,1,2,3)],mat,name)
                else:box(b,name,xa,xb,-.001*(noise%3),.036,za,zb,mat)
    box(b,'window head',-1.56,1.56,-.066,.24,1.582,1.823,'lintel grey')
    box(b,'pale projecting stone sill',-1.56,1.56,-.128,.245,.18,.285,'sill stone')
    box(b,'glass behind the muntins',-1.48,1.48,.177,.19,.275,1.59,'window glass')
    for i,x in enumerate([-1.444,-.48,.48,1.444]):
        box(b,f'primary vertical steel frame {i}',x-.023,x+.023,.116,.179,.281,1.586,'plain iron')
    for i,x in enumerate([-.96,0,.96]):
        box(b,f'slender sash bar {i}',x-.009,x+.009,.142,.179,.281,1.586,'plain iron')
    for i,z in enumerate([.298,.935,1.55]):
        box(b,f'horizontal steel frame {i}',-1.475,1.475,.12,.179,z-.020,z+.020,'plain iron')
    # Width changes and the short step between the lower feet are discernible in the 2015 image.
    for name,x0,x1,z0,z1 in [('wide top',-.950,.950,2.57,3.23),('date face',-.765,.765,2.151,2.573),
                             ('left foot',-.765,-.420,2.079,2.151),('right foot',.420,.765,2.079,2.151)]:
        box(b,name,x0,x1,-.085,.03,z0,z1,'pale date stone')
    box(b,'short coping over tablet',-.979,.979,-.099,.027,3.227,3.259,'sill stone')
    for i,(n,x) in enumerate(zip((1,9,2,9),(-.545,-.19,.18,.55))): digit(b,i,n,x,lod)
