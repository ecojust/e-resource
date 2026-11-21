"""The north end of the west-facing Sichuan North Road elevation, in estimated metres."""
from math import cos, pi, sin
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade, opening

BRICK = 'striated umber face brick'
LIGHT_BRICK = 'rose brown brick headers'
STONE = 'weathered pale mineral render'
DARK = 'dark grey coping'
SILL = 'stone sill and canopy'
GLASS = 'smoky blue window glazing'
SASH = 'charcoal steel sash'
BRASS = 'golden fanlight bars'
SHOP = 'warm shopfront stone'
ROOF = 'grey roof and study return'
SHADE = 'blued grey canopy canvas'
PALETTE = {
    BRICK:dict(color=[.424,.314,.277],roughness=.94), LIGHT_BRICK:dict(color=[.552,.432,.373],roughness=.93),
    STONE:dict(color=[.771,.741,.668],roughness=.90), DARK:dict(color=[.294,.278,.257],roughness=.88),
    SILL:dict(color=[.57,.546,.505],roughness=.88), GLASS:dict(color=[.345,.420,.446],roughness=.29,metallic=.21),
    SASH:dict(color=[.167,.176,.173],roughness=.55), BRASS:dict(color=[.812,.623,.284],roughness=.33,metallic=.53),
    SHOP:dict(color=[.673,.608,.505],roughness=.83), ROOF:dict(color=[.439,.433,.421],roughness=.92),
    SHADE:dict(color=[.341,.33,.303],roughness=.9),
}
LEFT, RIGHT, BACK = -13.0, 13.44, 3.06
BAYS = [-7.8,-3.97,-.14,3.69,7.52,11.35]
END_BAY = -11.45
TOP = 23.42
GOLD_CENTER = -3.18

def slab(b, shape, z, height, mat, part):
    b.prism(shape,z,z+height,lambda x,y,h:(x,y,h),mat,part)

def glazing(f,poly,columns,low,label):
    f.prism(poly.buffer(.008,join_style=2),-.211,-.194,GLASS,label+' panes')
    x,z,x1,z1=poly.bounds
    bars=[poly.difference(poly.buffer(-.043,join_style=2))]
    for k in range(1,columns):
        u=x+(x1-x)*k/columns
        bars.append(poly.intersection(box(u-.021,z,u+.021,z1)))
    if not low:
        v=z+(z1-z)*.7
        bars.append(poly.intersection(box(x,v-.025,x1,v+.025)))
    f.prism(unary_union(bars),-.163,-.123,SASH,label+' sash')
    return poly

def header_courses(f,wall):
    vv=[];ff=[]
    for row in range(33,174):
        z=row*.132
        for n in range(-54,56):
            if (row*53+n*197+row*n*11)%23>6:continue
            x=n*.257+(row%2)*.128
            if not wall.contains(box(x-.104,z-.038,x+.104,z+.038)):continue
            j=len(vv);vv.extend([f.point(x+dx,z+dy,.004)for dx,dy in [(-.104,-.038),(.104,-.038),(.104,.038),(-.104,.038)]])
            ff.append((j,j+1,j+2,j+3))
    if ff:f.builder.add(vv,ff,LIGHT_BRICK,'individual reddish brick headers')

def projecting_balcony(b,f,cx,z,low):
    # The top walkout curves back to each jamb. A real steel railing stands clear of the glazing.
    half=1.36;segments=10 if low else 20
    curve=[(cx-half*cos(i*pi/segments),-.12-.48*sin(i*pi/segments)) for i in range(segments+1)]
    shape=Polygon([(cx-half,.08),*curve,(cx+half,.08)])
    slab(b,shape,z-.145,.145,SILL,'top floor / bowed projecting slab')
    for dz in [.37,.77]:
        b.tube([(x,y,z+dz)for x,y in curve],.032 if dz>.6 else .022,SASH,6,'top floor / independent curved rails')
    for j in range(0,segments+1,2):
        x,y=curve[j];b.tube([(x,y,z),(x,y,z+.77)],.022,SASH,6,'top floor / railing uprights')

def shaft(f,cx,width,low):
    f.box(cx,13.21,width,18.55,.228,.077,STONE,'continuous tall pale pier')
    for z in ([5.,12.92,20.6] if low else [5.,8.90,12.92,16.71,20.60]):
        for side in [-1,1]:
            x=cx+side*width*.335
            f.prism(box(x-.025,z+.12,x+.025,z+.45),.18,.204,SILL,'short recessed-looking vertical pier mark')
        line=Polygon([(cx-.19,z+.23),(cx,z+.11),(cx+.19,z+.23),(cx+.19,z+.265),(cx,z+.151),(cx-.19,z+.265)])
        f.prism(line,.181,.206,SILL,'shallow chevron on pale pier')
    profile=Polygon([(cx-width/2,22.07),(cx+width/2,22.07),(cx+width/2,23.62),(cx+.16,23.86),
                     (cx+.07,24.12),(cx-.07,24.12),(cx-.16,23.86),(cx-width/2,23.62)])
    f.prism(profile,-.09,.20,STONE,'upright crenellated pier cap')
    for k in [0,1,2]:
        z=23.14+.19*k
        chevron=Polygon([(cx-width*.45,z+.14),(cx,z-.11),(cx+width*.45,z+.14),(cx+width*.45,z+.20),(cx,z-.05),(cx-width*.45,z+.20)])
        f.prism(chevron,.198,.227,SILL,'nested crown chevrons')

def fan(f,cx,z,rad,low):
    # A glazed semicircle in a later shopfront with an open fan-shaped frame.
    n=12 if low else 26;coords=[(cx+rad*cos(pi*i/n),z+rad*sin(pi*i/n))for i in range(n+1)]
    shape=Polygon(coords)
    f.prism(shape,.074,.092,GLASS,'semicircular shop fan glazing')
    f.prism(shape.difference(shape.buffer(-.065,join_style=2)),.096,.148,BRASS,'semicircular brass frame')
    for i in range(1,6):
        theta=i*pi/6
        f.builder.tube([f.point(cx,z+.025,.128),f.point(cx+(rad-.055)*cos(theta),z+(rad-.055)*sin(theta),.128)],.024,BRASS,7,'shop fanlight spokes')

def shopfront(f,low):
    columns=[-12.95,-10.32,-6.92,-3.72,-.55,2.8,5.98,9.78,13.44];holes=[]
    for a,b in zip(columns,columns[1:]):
        hi=3.28
        holes.append(glazing(f,box(a+.21,.20,b-.20,hi),2 if low else 3,low,'shop doors and display'))
    panel=box(LEFT,0,RIGHT,4.66).difference(unary_union(holes))
    f.prism(panel,-.29,0,SHOP,'shop piers and fascia')
    f.box(-3.25,4.13,19.30,.62,.40,.22,SHOP,'shallow frontage fascia below fan')
    f.box(-3.25,4.55,19.34,.108,.49,.255,DARK,'horizontal moulding over shopfront')
    f=Facade(f.builder,(-13.5,-.64),(13.5,-.64),'later shop gable')
    center=GOLD_CENTER;side=3.05;h=7.82
    pediment=Polygon([(center-side,4.57),(center+side,4.57),(center+side,h-1.32),(center,h),(center-side,h-1.32)])
    radius=1.28
    aperture=Polygon([(center+radius*cos(i*pi/30),4.58+radius*sin(i*pi/30))for i in range(31)])
    f.prism(pediment.difference(aperture),-.48,.111,SHOP,'later triangular shop pediment')
    for j in [0,1]:
        y=h+.057+j*.098;r=side+.13+j*.087
        p=Polygon([(center-r,y-1.35),(center,y),(center+r,y-1.35),(center+r,y-1.22),(center,y+.13),(center-r,y-1.22)])
        f.prism(p,.099,.285+j*.070,DARK,'sloping pediment crown')
    for x,r in [(center,1.28),(center-3.51,.77),(center+3.51,.77)]:
        if x!=center:
            outer=opening(x,4.44,2*r+.24,r+.23,r+.11)
            f.prism(outer,-.42,.084,SHOP,'side fan arch backing')
        fan(f,x,4.58,r,low)

def make_front(b,low):
    f=Facade(b,(-13.5,0),(13.5,0),'street elevation')
    holes=[]
    for i in range(6):
        z=4.64+i*3.00+.36
        for c in [END_BAY,*BAYS]:
            plain=c==END_BAY;width=1.08 if plain else 2.50
            if i==5 and not plain:
                window=opening(c,z,width,2.61,.45,12 if low else 25);projecting_balcony(b,f,c,z+.03,low)
            else:window=box(c-width/2,z,c+width/2,z+(1.91 if plain else 1.97))
            holes.append(glazing(f,window,2 if low or plain else 4,low,'narrow end window' if plain else 'window between tall piers'))
            if plain:continue
            if i<5:
                # Individually projecting short shades have a pitched rather than vertical leading face.
                slab(b,box(c-1.31,-.45,c+1.31,.06),z-.11,.115,SILL,'individual small window sill')
                head=z+2.08
                verts=[(c+dx,y,head+dz)for dx in [-1.32,1.32]for y,dz in [(.01,0),(-.51,-.21),(-.51,-.273),(.01,-.061)]]
                b.add(verts,[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],SHADE,'separate sloping window hood')
    outer=box(LEFT,4.66,RIGHT,TOP)
    wall=outer.difference(unary_union(holes))
    f.prism(wall,-.25,0,BRICK,'brick spandrels and window surrounds')
    if not low:header_courses(f,wall)
    for c in [LEFT+.22,-9.72,-5.885,-2.055,1.775,5.605,9.435,RIGHT-.23]:
        shaft(f,c,.63 if c not in [LEFT+.22,RIGHT-.23] else .44,low)
    for c in BAYS:
        crest=Polygon([(c-1.50,TOP-.22),(c+1.50,TOP-.22),(c+1.50,TOP+.07),
                       (c+.69,TOP+.19),(c,TOP+.095),(c-.69,TOP+.19),(c-1.5,TOP+.07)])
        f.prism(crest,-.21,.068,STONE,'individual parapet between pier caps')
    shopfront(f,low)
    plan=box(LEFT,0,RIGHT,BACK)
    slab(b,plan,TOP-.24,.11,ROOF,'flat study roof behind parapet')
    slab(b,plan,.02,.11,SHOP,'shop floors')
    for a,c in [((RIGHT,0),(RIGHT,BACK)),((RIGHT,BACK),(LEFT,BACK)),((LEFT,BACK),(LEFT,0))]:
        Facade(b,a,c,'documented crop / plain end').wall(0,TOP-.14,thickness=.105,material=ROOF)
