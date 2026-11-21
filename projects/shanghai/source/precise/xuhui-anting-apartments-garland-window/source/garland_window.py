"""Construct the southern street window at 43 Anting Road, from its measured sill and apron."""
from math import atan2, cos, pi, sin, sqrt
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

PALETTE = {
    'grey pointing': {'color': [.285,.263,.213], 'roughness': .96},
    'umber facing brick': {'color': [.182,.084,.055], 'roughness': .92},
    'red facing brick': {'color': [.245,.108,.063], 'roughness': .91},
    'violet brown brick': {'color': [.154,.082,.064], 'roughness': .92},
    'pale cast stone': {'color': [.596,.552,.452], 'roughness': .87},
    'worn limestone edge': {'color': [.715,.673,.554], 'roughness': .82},
    'carved floral stone': {'color': [.645,.600,.478], 'roughness': .84},
    'recessed apron field': {'color': [.440,.405,.325], 'roughness': .94},
    'dark window steel': {'color': [.057,.068,.064], 'metallic': .33, 'roughness': .53},
    'smoky daylight glass': {'color': [.151,.188,.174], 'metallic': .19, 'roughness': .28},
    'shaded daylight glass': {'color': [.103,.133,.126], 'metallic': .19, 'roughness': .29},
}
BRICKS = ['umber facing brick','red facing brick','violet brown brick']
STONE='pale cast stone'
EDGE='worn limestone edge'
FLOWER='carved floral stone'
STEEL='dark window steel'
def front(b, outline, nose, back, material, name):
    b.prism(outline,-back,-nose,lambda x,z,d:(x,-d,z),material,name)
def block(b,name,material,left,right,bottom,top,nose,back):
    b.box(((left+right)/2,(nose+back)/2,(bottom+top)/2),(right-left,back-nose,top-bottom),material,label=name)
def bead(b, name, points, radius, material, lod):
    b.tube(points,radius,material,sides=5 if lod else 8,label=name)
def ellipse(x,z,rx,rz,n):
    return Polygon([(x+rx*cos(2*pi*i/n),z+rz*sin(2*pi*i/n))for i in range(n)])
def petal(b,name,x,z,angle,length,width,y,bulge,lod):
    # A lenticular outline and a folded ridge make leaves read in grazing light.
    ax,az=cos(angle),sin(angle)
    def v(a,c,d):return (x+ax*a-az*c,y-d,z+az*a+ax*c)
    vertices=[v(-length/2,0,0),v(-.14*length,width/2,.001),v(.20*length,width*.37,.001),
              v(length/2,0,0),v(.20*length,-width*.37,.001),v(-.14*length,-width/2,.001),v(0,0,bulge)]
    faces=[(6,i,(i+1)%6) for i in range(6)]
    b.add(vertices,[(a,c,d)for a,d,c in faces],FLOWER,name)
    if not lod:
        bead(b,name+' raised midrib',[v(-.28*length,0,bulge*.44),v(0,0,bulge),v(.31*length,0,bulge*.45)],.0035,EDGE,False)
def masonry(b,lod):
    wall=box(-.87,-.118,.87,3.45)
    opening=box(-.604,.901,.604,2.531)
    front(b,wall.difference(opening),0,.247,'grey pointing','Brickwork joint bed and window reveals')
    row=0;z=-.118
    while z<3.45:
        x=-1.23+(.112 if row%2 else 0);col=0
        while x<.87:
            width=.105 if (row+col)%3==0 else .218
            l=max(-.87,x+.004);r=min(.87,x+width-.004);bot=z+.003;top=min(3.45,z+.063)
            if l<r and bot<top:
                panel=box(l,bot,r,top)
                cut=panel.difference(opening)
                if not cut.is_empty and cut.area>.0001:
                    front(b,cut,-.003-(.0014*((row*7+col)%3) if not lod else 0),.001,
                          BRICKS[(col*7+row*5+(col*row)%7)%len(BRICKS)],'Staggered street-facing brick courses')
            x+=width;col+=1
        z+=.066;row+=1
def add_garland_window(b,lod=False):
    masonry(b,lod)
    # The 2018 photograph shows two casements, each divided into two by four lights.
    window=box(-.604,.901,.604,2.531);open_area=box(-.551,.958,.551,2.479)
    front(b,window.difference(open_area),.063,.182,STEEL,'Outer rolled-steel window frame')
    for col,(lo,hi) in enumerate([(-.551,-.026),(.026,.551)]):
        light=box(lo,.958,hi,2.479);inner=light.buffer(-.024,join_style=2)
        front(b,light.difference(inner),.072,.158,STEEL,'Left or right leaf perimeter')
        lx,bz,rx,tz=inner.bounds;mx=(lx+rx)/2
        block(b,'Casement vertical glazing bar',STEEL,mx-.010,mx+.010,bz,tz,.103,.151)
        for row in range(4):
            bottom=bz+(tz-bz)*row/4;upper=bz+(tz-bz)*(row+1)/4
            for cell,(left,right) in enumerate([(lx,mx-.010),(mx+.010,rx)]):
                block(b,'Divided window glass',['smoky daylight glass','shaded daylight glass'][(col+cell+row//2)%2],
                      left,right,bottom+(.012 if row else 0),upper-(.012 if row<3 else 0),.156,.162)
            if row<3:block(b,'Horizontal glazing bar',STEEL,lx,rx,upper-.012,upper+.012,.100,.150)
    block(b,'Meeting stiles',STEEL,-.026,.026,.952,2.486,.073,.167)
    block(b,'Projecting square sill',STONE,-.740,.740,.766,.893,-.108,.210)
    block(b,'Sill weathered lip',EDGE,-.744,.744,.875,.910,-.128,.090)
    # The apron is a separate stone set into the brick, with concentric rectangular mouldings.
    widths=[(1.222,.555,0,-.044),(1.179,.514,.0205,-.065),(1.140,.474,.0405,-.043),(1.087,.426,.0645,-.070)]
    for i,(width,height,z,depth) in enumerate(widths):
        shape=box(-width/2,z,width/2,z+height)
        if i<len(widths)-1:
            w,h,sz,_=widths[i+1]
            front(b,shape.difference(box(-w/2,sz,w/2,sz+h)),depth,.005,EDGE if i%2 else STONE,'Apron concentric bead '+str(i+1))
        else:
            front(b,shape,depth,.004,'recessed apron field','Recessed apron tablet')
    # Festoon, tied at both ends with two hanging ends, and a central floral boss above.
    n=16 if lod else 28
    def swag(x):return .155+.218*(x/.455)**2
    bead(b,'Continuous festoon cord',[(.455*i/n,-.094,swag(.455*i/n)) for i in range(-n,n+1)],.019,FLOWER,lod)
    for i in range(-8,9):
        x=i*.047;z=swag(x)
        sl=atan2(2*.218*x,.455**2)
        for side in [-1,1]:
            petal(b,'Folded garland leaves',x,z+side*.019,sl+side*.54,.107,.048,-.099,.014,lod)
    for side in [-1,1]:
        x=side*.455
        for dx in [-.022,.025]:
            bead(b,'Hanging knot ends',[(x,-.095,.374),(x+dx*.48,-.111,.312),(x+dx,-.097,.245)],.011,FLOWER,lod)
            petal(b,'Pendant tassel tips',x+dx,.228,-pi/2,.063,.028,-.106,.011,lod)
        for a in [.2*pi,.72*pi]:
            petal(b,'Festoon bow loops',x,.385,a,.094,.044,-.105,.015,lod)
    for i in range(8):
        a=2*pi*i/8;petal(b,'Apron central rosette petals',.035*cos(a),.374+.046*sin(a),a,.075,.047,-.090,.018,lod)
    front(b,ellipse(0,.374,.022,.026,12 if lod else 20),-.125,-.087,EDGE,'Apron rosette button')
    # Two short consoles return down either side of the opening; the brick piers remain visible.
    for s in [-1,1]:
        x=s*.671
        block(b,'Square stone head blocks',STONE,x-.077,x+.077,2.337,2.734,-.045,.092)
    block(b,'Pale lintel',STONE,-.736,.736,2.525,2.758,-.049,.095)
    block(b,'Projecting pediment bed',EDGE,-.763,.763,2.750,2.812,-.106,.070)
    rise=.497;rad=.700;spring=2.807
    n=24 if lod else 48
    def arc(xr,zr):return [(xr*cos(i*pi/n),spring+zr*sin(i*pi/n)) for i in range(n+1)]
    arch=Polygon(arc(rad,rise));inner=Polygon(arc(.591,.390))
    front(b,arch.difference(inner),-.065,.055,STONE,'Segmental arched pediment')
    front(b,inner,-.036,.014,'recessed apron field','Recessed pediment tympanum')
    for xr,zr,name,depth in [(rad,rise,'Outer arched bead',-.081),(.596,.395,'Inner arched bead',-.066)]:
        bead(b,name,[(x,depth,z) for x,z in arc(xr,zr)],.009,EDGE,lod)
    # Fine scrolls follow the paired S-curves flanking the lyre-like centre in the donor image.
    for s in [-1,1]:
        path=[(.035,.005),(.063,.092),(.083,.216),(.138,.266),(.162,.233),(.141,.192),(.119,.199),(.121,.226)]
        path2=[(.160,.014),(.219,.040),(.286,.149),(.326,.147),(.342,.113),(.319,.086),(.295,.099)]
        for j,curve in enumerate([path,path2]):
            bead(b,'Paired pediment volute '+str(j+1),[(s*x,-.051,spring+.020+z)for x,z in curve],.011,STONE,lod)
        bead(b,'Outer small foliage scroll',[(s*x,-.050,spring+z)for x,z in [(.337,.018),(.409,.044),(.449,.090),(.421,.099)]],.010,STONE,lod)
    for z,w in [(2.850,.182),(2.872,.150),(2.966,.138)]:
        block(b,'Tympanum central basket bands',EDGE,-w/2,w/2,z,z+.016,-.060,-.040)
    for x in [-.055,-.019,.019,.055]:
        bead(b,'Tympanum narrow basket uprights',[(x*.77,-.052,2.879),(x,-.052,2.966)],.007,STONE,lod)
