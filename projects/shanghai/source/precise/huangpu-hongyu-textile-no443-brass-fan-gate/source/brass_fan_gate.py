"""The fanlight, projecting stone key and pierced brass ornaments at 443 Middle Jiangxi Road."""
from pathlib import Path
from math import cos,hypot,pi,radians,sin
import json

def finish(rgb,roughness=.78,metallic=0):
    def lin(c):
        a=c/255;return a/12.92 if a<=.04045 else ((a+.055)/1.055)**2.4
    return dict(color=[lin(c)for c in rgb],roughness=roughness,metallic=metallic)
PALETTE={k:finish(v)for k,v in [('scored stucco',(148,143,126)),('ashlar',(158,151,132)),('lit stone',(169,161,143)),('stone joints',(115,113,102)),('door enamel',(40,42,39)),('leaf moulding',(47,49,45)),('fan recess',(33,36,34)),('dark glazing',(55,57,50)),('number enamel',(44,83,62)),('number ivory',(216,210,188))]}
PALETTE['antique brass']=finish((151,114,57),.42,.6);PALETTE['fan iron']=finish((64,65,55),.59,.4)
# Wall-plane homography comes from the four jamb and transom intersections in Antigng's EXIF-corrected image.
H=[[0.009988464102668248, -0.00015765934483120828, -1.7745646740981544], [-0.001196386426296743, -0.00932040397460651, 4.899305439855051], [-0.000461489356715108, 0.00017181901614341926, 1.0]]

def loc(p):
    u,v=p;d=H[2][0]*u+H[2][1]*v+1
    return ((H[0][0]*u+H[0][1]*v+H[0][2])/d,(H[1][0]*u+H[1][1]*v+H[1][2])/d)

def poly(b,shape,front,back,mat,name):
    if sum(a[0]*c[1]-c[0]*a[1]for a,c in zip(shape,shape[1:]+shape[:1]))<0:shape=shape[::-1]
    n=len(shape);v=[(x,y,z)for y in (front,back)for x,z in shape];f=[tuple(range(n)),tuple(reversed(range(n,2*n)))];f.extend(((i+1)%n,i,i+n,(i+1)%n+n)for i in range(n));b.add(v,f,mat,name)

def rect(b,x0,x1,z0,z1,y,d,m,name):poly(b,[(x0,z0),(x1,z0),(x1,z1),(x0,z1)],y,d,m,name)

def strip(b,a,c,half_width,y,d,mat,name):
    dx=c[0]-a[0];dz=c[1]-a[1];le=hypot(dx,dz);nx=-dz*half_width/le;nz=dx*half_width/le
    poly(b,[(a[0]-nx,a[1]-nz),(a[0]+nx,a[1]+nz),(c[0]+nx,c[1]+nz),(c[0]-nx,c[1]-nz)],y,d,mat,name)

INNER=[(70.2,287.5),(71.9,257),(77,229),(85,196),(99,166),(118,144),(137,128),(158,116),(180,110),(201,112),(220,119),(238,132),(252,151),(265,178),(275,207),(282,243),(283.2,282.5)]
OUTER=[(44,287),(46,247),(54,210),(65,178),(81,150),(99,129),(124,110),(148,99),(178,91),(202,92),(226,97),(249,109),(272,131),(292,166),(306,204),(316,245),(319,281)]
RAYS=[11.8,23.5,35.5,46.8,57.5,67.8,98.,107.5,117.8,128.8,138.2,152.8,163.2]

def ellipse(angle,factor):
    a=radians(angle);return (1.102*factor*cos(a),2.085+1.53*factor*sin(a))

def brass(b,lod):
    shapes=json.loads((Path(__file__).parent/'ornament-outlines.json').read_bytes())
    for name,versions in shapes.items():
        mesh=versions['lod' if lod else 'full'];pts=mesh['xz'];n=len(pts);front=.064 if name=='fan centre' else .070;back=front+.020
        v=[(x,y,z)for y in [front,back]for x,z in pts];faces=[tuple(f)for f in mesh['front']]+[tuple(i+n for i in reversed(f))for f in mesh['front']]
        for ring in mesh['rings']:
            for a,c in zip(ring,ring[1:]+ring[:1]):faces.append((c,a,a+n,c+n))
        b.add(v,faces,'antique brass',name+' pierced brass')

def add_building(b,lod=False):
    inner=list(map(loc,INNER));outer=list(map(loc,OUTER));top=loc((193,39))[1]
    # Joints meet the photographed arch on its two impost faces and radiate toward the projecting central key.
    for i in range(len(inner)-1):
        a,c=inner[i:i+2];d,e=outer[i:i+2];poly(b,[a,c,e,d],-.055,.16,'stone joints',f'arch mortar {i+1}')
        def lerp(a,b,t):return (a[0]*(1-t)+b[0]*t,a[1]*(1-t)+b[1]*t)
        gaps=(.012,.988)if i%2==0 else (.002,.977)
        poly(b,[lerp(a,c,gaps[0]),lerp(a,c,gaps[1]),lerp(d,e,gaps[1]),lerp(d,e,gaps[0])],-.067,.15,'ashlar',f'arch reveal {i+1}')
        poly(b,[d,e,(e[0],top),(d[0],top)],.005,.24,'scored stucco',f'upper spandrel {i+1}')
    for side,idx,edge in [('left',0,-1.58),('right',-1,1.65)]:
        corner=outer[idx];sill=inner[idx];a,c=sorted((corner[0],edge));rect(b,a,c,.43,top,.005,.24,'scored stucco',side+' plaster margin')
        a,c=sorted((edge,sill[0]));rect(b,a,c,.43,sill[1],.005,.24,'scored stucco',side+' jamb')
        a,c=sorted((corner[0],sill[0]));rect(b,a,c,.43,sill[1],-.060,.16,'ashlar',side+' jamb reveal')
    key=list(map(loc,[(193,47),(228,51),(222,114),(194,115)]));poly(b,key,-.135,.10,'lit stone','projecting tapered key')
    # Solid leaf panels sit further back than their vertical stiles and the through-pierced metal work.
    rect(b,-1.10,-.011,.43,2.087,.120,.168,'door enamel','left leaf upper field');rect(b,.011,1.10,.43,2.087,.120,.168,'door enamel','right leaf upper field')
    for i,x in enumerate([-1.073,-.021,.021,1.073]):rect(b,x-.016,x+.016,.43,2.09,.084,.154,'leaf moulding',f'leaf stile {i+1}')
    for j,z in enumerate([1.74,1.80,2.07]):rect(b,-1.10,1.10,z-.017,z+.017,.085,.16,'leaf moulding',f'cross moulding {j+1}')
    for i in range(len(inner)-1):poly(b,[(0,2.086),inner[i],inner[i+1]],.160,.219,'fan recess',f'fan background {i+1}')
    for j,a in enumerate(RAYS):strip(b,ellipse(a,.25),ellipse(a,.90),.009,.082,.119,'fan iron',f'photographed fan spoke {j+1}')
    for rad,name in [(.25,'central fan ring'),(.90,'outer fan ring')]:
        for j in range(24 if lod else 40):
            steps=24 if lod else 40;strip(b,ellipse(j*180/steps,rad),ellipse((j+1)*180/steps,rad),.014,.078,.121,'fan iron',name+' '+str(j+1))
    brass(b,lod)
    # The photographed 443 number plate is to the right of the arch at springing height.
    plate=[(318.4,195.5),(340.0,194.0),(340.2,219.0),(319.4,220.1)];poly(b,list(map(loc,plate)),-.022,.028,'number enamel','443 enamel street plate')
    digits=[[(.75,0),(.18,.62),(.98,.62)],[(.74,.03),(.74,1)]]
    for i in range(3):
        paths=digits if i<2 else [[(.08,.17),(.46,.04),(.82,.13),(.90,.31),(.49,.48),(.83,.62),(.90,.83),(.65,.98),(.28,.98),(.10,.85)]]
        for n,line in enumerate(paths):
            points=[loc((321.2+i*5.35+x*3.55,200.2+y*9.30))for x,y in line]
            for k,(a,c)in enumerate(zip(points,points[1:])):strip(b,a,c,.0039,-.026,-.018,'number ivory',f'number {i+1} stroke {n+1} part {k+1}')
