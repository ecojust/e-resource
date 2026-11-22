"""The marked five-bay central section of the Gengwu school building, from the base of the shafts upward."""
from math import cos,sin,pi
from pathlib import Path
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union
from photo_architecture import Facade
from brick import uv
STONE='weathered pale stone';WALL='light cement render';BRICK='grey exposed brick';FRAME='painted dark window metal';GLASS='grey purple glazing';BRONZE='dark oculus grille';SHADOW='shadow in recessed stone carving'
PALETTE={
    STONE:{'color':[.72,.714,.67], 'roughness':.91},WALL:{'color':[.778,.76,.69],'roughness':.95},
    BRICK:{'color':[1,1,1], 'roughness':.94,'texture':str(Path(__file__).with_name('grey-brick.png'))},
    FRAME:{'color':[.245,.235,.225],'roughness':.68},GLASS:{'color':[.408,.365,.411],'roughness':.33,'metallic':.09},
    BRONZE:{'color':[.225,.235,.23],'roughness':.77},SHADOW:{'color':[.485,.482,.452],'roughness':.96}
}
BAYS=(-6.48,-3.24,0,3.24,6.48);HALF=9.62;TOP=14.80
WINDOW_ROWS=((.81,2.80),(5.31,6.72),(8.71,10.28))
OCULUS=(0,12.43);OC_RADIUS=.505
def circle(radius,n):
    return Polygon([(OCULUS[0]+radius*cos(2*pi*i/n),OCULUS[1]+radius*sin(2*pi*i/n))for i in range(n)])

def window(face,x,k,low,high,distant):
    width=1.97;shape=box(x-width/2,low,x+width/2,high);group=f'Window {k+1} {BAYS.index(x)+1}'
    face.prism(shape,-.296,-.263,GLASS,group+'/glazing')
    cols=4 if k==2 else 7
    cut=shape.buffer(-.074,join_style=2)
    bars=[box(x-width/2+i*width/cols-.021,low,x-width/2+i*width/cols+.021,high) for i in range(1,cols)]
    at=low+(high-low)*(.56 if k==0 else .39 if k==1 else .49)
    bars.append(box(x-width/2,at-.032,x+width/2,at+.032))
    if k==0 and not distant:
        mid=low+(high-low)*.82;bars.append(box(x-width/2,mid-.019,x+width/2,mid+.019))
    grid=shape.difference(cut.difference(unary_union(bars)))
    face.prism(grid,-.253,-.182,FRAME,group+'/muntins')
    face.box(x,low-.05,width+.12,.10,.39,.048,STONE,group+'/sill')
    if k==2:
        face.box(x,high+.05,width+.13,.1,.22,.01,BRICK,group+'/brick head')

def column(b,x,engaged,distant):
    y=-.235 if not engaged else .10
    name=('Engaged' if engaged else 'Full')+f' column {x:.2f}'
    n=16 if distant else 32
    profile=[(.12,.375),(.19,.385),(.23,.348),(.275,.333),(.314,.358),(.359,.319),(.395,.299),(5.72,.27),(6.10,.26),(6.13,.288),(6.19,.288),(6.22,.263),(6.32,.287),(6.64,.354),(6.76,.411)]
    b.lathe((x,y),profile,STONE,n,name+'/shaft and bell')
    b.box((x,y,6.813),(.87,.77,.107),STONE,label=name+'/abacus')
    leaves=10 if distant else 16
    for i in range(leaves):
        a=2*pi*i/leaves
        if engaged and sin(a)>.35:continue
        outline=[(6.26,.277,0),(6.43,.305,-.065),(6.61,.356,-.067),(6.725,.388,0),(6.56,.348,.070),(6.38,.293,.060)]
        vv=[]
        for z,r,angle in outline:vv.append((x+r*cos(a+angle),y+r*sin(a+angle),z))
        base=len(vv);vv.extend([(x+(r-.026)*cos(a+angle),y+(r-.026)*sin(a+angle),z)for z,r,angle in outline])
        faces=[tuple(range(base)),tuple(reversed(range(base,2*base)))]
        faces.extend((i,(i+1)%base,(i+1)%base+base,i+base)for i in range(base))
        b.add(vv,faces,STONE,name+'/leaf capitals')

def sloped_band(face,ring,z_low,z_peak,wide):
    face.prism(Polygon([(-HALF,z_low),(0,z_peak),(HALF,z_low),(HALF,z_low+wide),(0,z_peak+wide),(-HALF,z_low+wide)]),-.43,ring,STONE,'pediment/raking courses')

def add_building(b,distant):
    face=Facade(b,(-HALF,0),(HALF,0),'Gengwu central front')
    windows=[[box(x-.985,z0,x+.985,z1)for x in BAYS]for z0,z1 in WINDOW_ROWS]
    lower=box(-HALF,0,HALF,8.24).difference(unary_union(windows[0]+windows[1]))
    face.prism(lower,-.56,0,WALL,'wall/two main storeys')
    n=36 if distant else 76
    upper=Polygon([(-HALF,8.24),(HALF,8.24),(HALF,11.25),(0,TOP),(-HALF,11.25)])
    face.prism(upper.difference(unary_union(windows[2]+[circle(OC_RADIUS,n)])),-.56,0,BRICK,'upper brick with pierced oculus')
    for k,(lo,hi) in enumerate(WINDOW_ROWS):
        for x in BAYS:window(face,x,k,lo,hi,distant)
    for x in (-8.10,-4.86,-1.62,1.62,4.86,8.10):column(b,x,abs(x)>8,distant)
    for x in (-8.86,8.86):
        face.box(x,3.45,1.11,6.77,.655,.06,STONE,'outer ashlar piers')
        for z in (.15,3.04,5.50,6.72):
            face.box(x,z,1.12,.03,.674,.056,SHADOW,'outer horizontal masonry joint')
        for z,h,w,d in ((.065,.13,1.34,.85),(6.97,.26,1.29,.76),(7.17,.15,1.43,.81)):
            face.box(x,z,w,h,d,.10,STONE,'pier bases and capitals')
    for x in BAYS:
        for j in (-.47,.47):
            u=x+j;z=4.06;ww=.34;hh=.84
            face.prism(box(u-.413,z-.949,u+.413,z+.949),.002,.033,STONE,'spandrel/ten recessed panels')
            pattern=Polygon([(u-ww,z),(u,z+hh),(u+ww,z),(u,z-hh)])
            ring=pattern.difference(pattern.buffer(-.02,join_style=2))
            face.prism(ring,.033,.043,SHADOW,'spandrel/ten diamond reliefs')
    for z,height,projection in ((.06,.12,.30),(6.91,.105,.17),(7.10,.14,.23),(7.39,.43,.13),(7.67,.11,.24),(7.82,.11,.30),(7.99,.20,.37),(8.17,.12,.42),(8.40,.13,.14),(10.87,.21,.20),(11.11,.15,.32)):
        face.box(0,z,HALF*2+.06,height,.56+projection,(projection-.56)/2,STONE,'continuous stone belts')
    for z,height,proj in ((11.04,.17,.25),(11.21,.165,.36),(11.39,.105,.40)):
        sloped_band(face,proj,z,z+(TOP-11.50),height)
    face.prism(circle(.714,n).difference(circle(OC_RADIUS,n)),-.15,.19,STONE,'oculus/dressed surround')
    face.prism(circle(.752,n).difference(circle(.71,n)),.055,.137,STONE,'oculus/outer bead')
    for i in range(4):
        a=i*pi/2;c=cos(a);s=sin(a)
        points=[(.535,-.078),(.535,.078),(.84,.14),(.84,-.14)]
        poly=Polygon([(x*c-y*s,x*s+y*c+OCULUS[1])for x,y in points])
        face.prism(poly,.178,.31,STONE,'oculus/four raised keys')
    face.prism(circle(OC_RADIUS,n),-.395,-.37,BRONZE,'oculus/dark recessed screen')
    for j in range(-7,8):
        z=OCULUS[1]+j*.062;strip=circle(OC_RADIUS,n).intersection(box(-.53,z-.012,.53,z+.012))
        if not strip.is_empty:face.prism(strip,-.317,-.29,FRAME,'oculus/slats')
    for part in b.parts:
        if part['material']==BRICK:part['texcoords']=[uv(*v) for v in part['vertices']]
