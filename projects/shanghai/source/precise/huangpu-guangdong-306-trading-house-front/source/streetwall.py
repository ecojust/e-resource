"""Guangdong Road elevation, measured in proportion from the December 2014 facade photograph."""
from pathlib import Path
from shapely.geometry import box, LineString, Polygon
from shapely.ops import unary_union
from brick import wall_uv
from repeat import repeat_only_texture

HERE=Path(__file__).parent
PLASTER='warm ivory render'
TILE='red glazed tile bands'
STONE='pale carved relief'
METAL='oxidized railing'
SASH='dark bronze sash'
GLASS='recessed grey green glass'
DOOR='deep brown entrance leaves'
LINING='shaded balcony soffit'
GROOVE='grey cut stone grooves'
PALETTE={
    GROOVE:{'color':[.47,.49,.48],'roughness':.94},
    PLASTER:{'color':[.78,.773,.732],'roughness':.87},
    TILE:{'color':[1.,1.,1.],'texture':str(HERE/'brick.png'),'roughness':.80},
    STONE:{'color':[.82,.801,.735],'roughness':.82},
    METAL:{'color':[.34,.34,.302],'metallic':.54,'roughness':.45},
    SASH:{'color':[.135,.14,.122],'metallic':.28,'roughness':.55},
    GLASS:{'color':[.209,.275,.262],'metallic':.17,'roughness':.32},
    DOOR:{'color':[.12,.107,.089],'roughness':.67},
    LINING:{'color':[.63,.619,.573],'roughness':.9}}
HALF=7.7443
CENTRAL=(-4.80,-2.90,-1.00,.90,2.80,4.70)
ENDS=(-6.80,6.80)
WINDOWS=((4.46,5.91),(6.96,8.95),(10.42,11.91),(13.52,14.61))

def point(x,z,depth):
    return x,-depth,z

def slab(b,x0,x1,z0,z1,back,front,mat,label):
    b.prism(box(x0,z0,x1,z1),back,front,point,mat,label)

def mesh(b,polygon,back,front,mat,label):
    if not polygon.is_empty:b.prism(polygon,back,front,point,mat,label)

def bead(b,points,width,back,front,mat,group):
    path=LineString(points)
    shape=path.buffer(width/2,cap_style='flat',join_style='mitre')
    channel=path.buffer(width*.94,cap_style='flat',join_style='mitre').difference(shape)
    mesh(b,channel,back+.0004,back+.006,GROOVE,group+' channel')
    mesh(b,shape,back,front,mat,group)

def pane(b,shape,depth,lod,door=False):
    x0,z0,x1,z1=shape.bounds
    front=-depth
    name='Lower entrance' if door else 'Upper sash'
    mesh(b,shape,front-.045,front,DOOR if door else GLASS,name+' rear plane')
    pieces=[shape.difference(shape.buffer(-.050,join_style='mitre'))]
    if door:
        for x in [x0+.25*(x1-x0),x0+.75*(x1-x0)]:
            slab(b,x-.15*(x1-x0),x+.15*(x1-x0),z0+.59,z1-.34,front,front+.020,GLASS,'Entrance glass panels')
    bars=[.76] if lod else [.71,.80]
    for frac in bars:
        z=z0+(z1-z0)*frac;pieces.append(box(x0,z-.017,x1,z+.017))
    x=(x0+x1)/2;pieces.append(box(x-.022,z0,x+.022,z1))
    mesh(b,unary_union(pieces),front+.025,front+.07,SASH,name+' rails and stiles')

def chevrons(b,left,right,z,amplitude,n,back,front,label,two=True):
    step=(right-left)/n
    for rise in ([0,.15] if two else [0]):
        line=[(left+i*step/2,z+rise+(amplitude if i%2 else 0)) for i in range(2*n+1)]
        bead(b,line,.035,back,front,STONE,label)

def end_balcony(b,x,z,lod):
    left,right=x-.92,x+.92;d=.69
    slab(b,left,right,z-.15,z,-.06,d+.05,LINING,'End balcony slabs')
    slab(b,left,right,z,z+.65,d-.13,d,PLASTER,'End balcony solid front')
    for start,end in ((left,left+.13),(right-.13,right)):
        slab(b,start,end,z,z+.65,-.018,d+.005,PLASTER,'End balcony side returns')
    slab(b,left,right,z+.61,z+.68,d-.14,d+.035,STONE,'End balcony copings')
    chevrons(b,left+.12,right-.12,z+.19,.090,3,d+.002,d+.038,'End balcony zigzag',True)

def long_balcony(b,lod):
    half=5.66;z=6.93;d=.99
    slab(b,-half,half,z-.17,z,-.14,d,LINING,'Long balcony slab')
    slab(b,-half,half,z-.09,z+.025,d-.09,d+.075,STONE,'Light balcony nose')
    for k in range(8):
        x=-half+.10+(2*half-.20)*k/7
        b.tube([point(x,z+.02,d-.045),point(x,z+.86,d-.045)],.029,METAL,6 if lod else 10,'Long rail posts')
    for h in (.21,.44,.65,.86):
        pts=[point(-half+.10,z+h,.025),point(-half+.10,z+h,d-.19),point(-half+.07+.11,z+h,d-.04),point(half-.18,z+h,d-.04),point(half-.10,z+h,d-.16),point(half-.10,z+h,.025)]
        b.tube(pts,.035 if h==.86 else .026,METAL,7 if lod else 12,'Continuous rails with returns')

def woven_band(b,lod):
    top=4.49;bottom=3.30;l,r=-5.69,5.69
    slab(b,l,r,bottom,top,-.035,.109,STONE,'Base of woven frieze')
    for z in (bottom+.03,bottom+.76,top-.06):
        slab(b,l,r,z,z+.062,.100,.180,STONE,'Horizontal frieze mouldings')
    for side in (-1,1):
        a,c=(l+.12,-.25) if side<0 else (.25,r-.12)
        count=7;step=(c-a)/count
        for k in range(count):
            x=a+(k+.5)*step;z=bottom+.43
            rhomb=[(x-step*.47,z),(x,z+.27),(x+step*.47,z),(x,z-.27),(x-step*.47,z)]
            bead(b,rhomb,.045,.108,.160,STONE,'Interlocking diamond relief')
            for level in ([.145] if lod else [.11,.17]):
                bead(b,[(x-.18,z),(x,z+level),(x+.18,z)],.033,.108,.155,STONE,'Carved nested chevrons')
        chevrons(b,a,c,top-.19,.102,11,.110,.151,'Upper border of frieze',False)
    slab(b,-.118,.118,bottom-.10,top+.085,.085,.22,STONE,'Middle frieze pendant')
    for x in (-.11,.11):
        slab(b,x-.052,x+.052,bottom-.175,bottom-.07,.112,.214,STONE,'Pendant hem')

def add_building(b,lod):
    repeat_only_texture(b,'brick.png');hole_rows=[]
    for x in (*ENDS,*CENTRAL):
        for row,(bottom,top) in enumerate(WINDOWS):
            width=.96 if x in CENTRAL else 1.04
            win=box(x-width/2,bottom,x+width/2,top);hole_rows.append(win)
            pane(b,win,.18 if row!=1 else .22,lod)
    for index,x in enumerate(CENTRAL):
        door=index in (1,4);width=1.29 if door else 1.12;bottom=.025 if door else .62
        win=box(x-width/2,bottom,x+width/2,2.89);hole_rows.append(win);pane(b,win,.52 if door else .185,lod,door)
        if not door:slab(b,x-width/2-.055,x+width/2+.055,.52,.60,-.055,.115,STONE,'Street window sills')
    for x in ENDS:
        win=box(x-.48,.025,x+.48,2.64);hole_rows.append(win);pane(b,win,.47,lod,True)
    apertures=unary_union(hole_rows)
    shell=box(-HALF,0,HALF,15.82).difference(apertures)
    mesh(b,shell,-.86,0.,PLASTER,'Street wall with actual openings')
    # A narrow strip above each upper central opening and the broad red apron between levels.
    for z0,z1 in [(6.09,6.91),(8.96,10.43),(11.93,12.53)]:
        slab(b,-5.58,5.58,z0,z1,-.019,.037,TILE,'Central red tile spandrels')
    for x in ENDS:
        ring=box(x-.64,4.38,x+.64,12.02).difference(apertures)
        mesh(b,ring,-.020,.036,TILE,'Vertical tiled end bays')
        for z0,z1 in [(3.24,3.31),(10.18,10.25)]:end_balcony(b,x,z1,lod)
    long_balcony(b,lod);woven_band(b,lod)
    for x in (-3.72,.15,3.99):
        for h in (12.76,13.04,13.31):
            slab(b,x-.195,x+.195,h,h+.17,.003,.066,TILE,'Grouped tile keys')
    for l,r,n in [(-5.49,-3.99,3),(-3.43,-.17,5),(.43,3.65,5),(4.27,5.50,2)]:
        chevrons(b,l,r,12.89,.12,n,.002,.046,'Repeated parapet chevrons',True)
    for x in ENDS:
        slab(b,x-.65,x+.65,12.47,12.59,.012,.16,STONE,'End bay flat eyebrows')
    for z,d in [(14.99,.052),(15.24,.072),(15.65,.083)]:
        slab(b,-HALF,HALF,z,z+.061,-.16,d,STONE,'Upper parapet stringcourses')
    for x in (-7.30,-5.75,-3.58,-.10,3.88,6.90):
        slab(b,x-.19,x+.19,15.82,15.96,-.54,.004,PLASTER,'Raised parapet keys')
        if not lod:
            for dx in (-.085,0,.085):slab(b,x+dx-.012,x+dx+.012,15.64,15.95,.005,.028,STONE,'Parapet flutes')
    for part in b.parts:
        # Leave the original western party-wall return outside the replacement strip.
        part['vertices']=[(.96*x+.18,y,z) for x,y,z in part['vertices']]
        if part['material']==TILE:part['texcoords']=[wall_uv(*pt)for pt in part['vertices']]
