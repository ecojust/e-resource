"""The two inner columns and curved balcony of the Tang Residence's south porch."""
from math import cos, sin, pi, tau
from shapely.geometry import Polygon

STONE = 'pale warm column stone'
MOLDING = 'weathered stone edge'
IRON = 'dark balcony iron'
WOOD = 'aged red joinery'
GLASS = 'shaded window glass'
REVEAL = 'recessed red brown surround'
PALETTE = {k: dict(color=v, roughness=r) for k,v,r in [
    (STONE,[.72,.68,.60],.86),(MOLDING,[.57,.52,.44],.92),
    (IRON,[.045,.034,.025],.73),(WOOD,[.26,.088,.054],.82),
    (GLASS,[.068,.052,.048],.35),(REVEAL,[.215,.115,.082],.91)]}
HALF_BAY = 1.12
COLUMN_Y = -.43
BALCONY_WIDTH = 1.72
DECK = 3.43

def balcony_front(x):
    return -.24-.60*(1-(x/BALCONY_WIDTH)**2)

def rectangle(b, center, size, material, group):
    b.box(center,size,material,label=group)

def leaf(b,x,angle,stagger,radius,height):
    # Fold the acanthus leaf along its centre ridge and curl the tip outwards.
    z0=6.015+stagger
    vx,vy=cos(angle),sin(angle)
    def point(tangent,rad,z):
        return (x+vx*rad-vy*tangent,COLUMN_Y+vy*rad+vx*tangent,z)
    verts=[]
    for h,w,rad in [(0,.014,radius),(.28,.056,radius+.01),
                    (.55,.077,radius+.045),(.74,.060,radius+.063),
                    (.90,.070,radius+.102),(1,.014,radius+.127)]:
        verts.extend([point(-w,rad,z0+h*height),
                      point(0,rad+.022,z0+h*height),point(w,rad,z0+h*height)])
    faces=[]
    for start in range(0,len(verts)-3,3):
        for j in (0,1):
            i=start+j;faces.extend([(i,i+1,i+4),(i,i+4,i+3)])
    b.add(verts,faces,STONE,'Acanthus courses')

def capital(b,x,lod):
    count=8 if lod else 12
    for i in range(count):
        a=tau*i/count
        leaf(b,x,a,0,.224,.275)
        if not lod: leaf(b,x,a+pi/count,.135,.222,.265)
    # Each face carries two opposed spirals immediately beneath the abacus.
    for j in range(4):
        a=j*pi/2;nx,ny=cos(a),sin(a)
        for s in (-1,1):
            coords=[]
            for k in range(9 if lod else 19):
                t=k/(8 if lod else 18);phi=-pi*.78+t*pi*2.12
                tangent=s*(.143+cos(phi)*(.118-.082*t))
                height=6.356+sin(phi)*(.116-.08*t)
                coords.append((x+.26*nx-tangent*ny,COLUMN_Y+.26*ny+tangent*nx,height))
            b.tube(coords,.025,STONE,5 if lod else 7,'Capital volutes')

def column(b,x,lod):
    ring=16 if lod else 36
    rectangle(b,(x,COLUMN_Y,.13),(.84,.85,.26),MOLDING,'Square column footing')
    prof=[(.235,.395),(.275,.40),(.294,.378),(.314,.35),(.338,.339),
          (.354,.36),(.375,.375),(.401,.352),(.417,.320),(.438,.302),
          (.462,.307),(.481,.307),(.498,.280),(.54,.265),(1.45,.26),
          (3.65,.248),(5.91,.222),(5.97,.222),(5.992,.244),(6.029,.246),
          (6.055,.227),(6.11,.236),(6.279,.267),(6.39,.298),(6.432,.295)]
    b.lathe((x,COLUMN_Y),prof,STONE,ring,'Base shaft and capital bell')
    capital(b,x,lod)
    for z,w,h,mat in [(6.438,.677,.076,STONE),(6.491,.712,.050,MOLDING),(6.534,.732,.048,STONE)]:
        rectangle(b,(x,COLUMN_Y,z),(w,w,h),mat,'Square abacus')

def slab(b,lod):
    count=18 if lod else 40
    for bottom,top,out,material,group in [
        (3.22,3.273,.008,MOLDING,'Curved soffit edge'),(3.27,3.329,.065,STONE,'Curved lower roll'),
        (3.325,3.369,.012,MOLDING,'Curved fascia recess'),(3.366,DECK,.080,STONE,'Curved balcony lip')]:
        points=[(-BALCONY_WIDTH,.63)]
        for i in range(count+1):
            x=BALCONY_WIDTH*(2*i/count-1);points.append((x,balcony_front(x)-out))
        points.append((BALCONY_WIDTH,.63))
        b.plan_prism(Polygon(points),bottom,top,material,group)

def grille(b,lod):
    def wire(coords,radius,label):
        b.tube([(x,balcony_front(x)-.004,z) for x,z in coords],radius,IRON,5 if lod else 7,label)
    lo,hi=-1.67,1.67
    for z,r in [(3.475,.024),(3.555,.014),(3.997,.019),(4.051,.030)]:
        count=14 if lod else 32
        wire([(lo+(hi-lo)*i/count,z) for i in range(count+1)],r,'Curved gallery rails')
    panels=12
    for i in range(panels+1):
        x=lo+(hi-lo)*i/panels
        wire([(x,3.47),(x,4.05)],.012,'Balcony pickets')
    for i in range(panels):
        center=lo+(hi-lo)*(i+.5)/panels
        for s in (-1,1):
            points=[]
            count=6 if lod else 14
            for k in range(count+1):
                t=k/count;angle=pi+.85*pi*2*t
                points.append((center+s*(.063+.052*cos(angle)),3.767+.188*sin(angle)))
            wire(points,.010,'Paired railing scrolls')

def glazed_wall(b):
    # The paired photographed openings have a reddish wall pier between their jambs.
    # They are two shallow exterior bays. No rooms or continuation of the porch are inferred.
    rectangle(b,(0,.855,3.36),(3.38,.12,6.17),REVEAL,'Rear porch wall panel')
    for cx in (-.825,.825):
        width=1.415
        for z0,z1,rows in [(.31,3.15,2),(3.50,6.31,4)]:
            y=.745
            rectangle(b,(cx,y+.043,(z0+z1)/2),(width,.072,z1-z0),GLASS,'Recessed glass panes')
            for side in (-1,1):
                rectangle(b,(cx+side*width/2,.716,(z0+z1)/2),(.092,.109,z1-z0),WOOD,'Timber outer jambs')
            rectangle(b,(cx,.708,(z0+z1)/2),(.061,.072,z1-z0),WOOD,'Timber meeting stile')
            for j in range(rows+1):
                z=z0+(z1-z0)*j/rows
                rectangle(b,(cx,.723,z),(width+.06,.070,.084 if j in (0,rows) else .045),WOOD,'Window and door rails')
            if z0<1:
                for side in (-1,1):
                    xp=cx+side*width/4
                    rectangle(b,(xp,.731,.65),(width/2-.058,.055,.66),WOOD,'Lower timber door panels')
                    rectangle(b,(xp,.697,.65),(width/2-.148,.040,.48),WOOD,'Recessed panel field')
            else:
                for side in (-1,1):
                    rectangle(b,(cx+side*.362,.732,5.967),(.028,.054,.681),WOOD,'Upper transom mullions')


def model(b,lod=False):
    for x in (-HALF_BAY,HALF_BAY):column(b,x,lod)
    slab(b,lod);grille(b,lod);glazed_wall(b)
    for y,z,dy,ht,mat,name in [
        (-.33,6.6,.8,.108,STONE,'Architrave lower band'),
        (-.32,6.71,.76,.135,STONE,'Architrave face'),
        (-.34,6.803,.88,.065,MOLDING,'Entablature shadow step'),
        (-.34,6.867,.93,.073,STONE,'Crowning stone edge')]:
        rectangle(b,(0,y,z),(3.58,dy,ht),mat,name)
    for z,w,front in [(.037,3.55,-1.00),(.107,3.46,-.83),(.181,3.39,-.65)]:
        rectangle(b,(0,(front+.8)/2,z),(w,.8-front,.074),MOLDING,'Central porch tread')
