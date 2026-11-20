"""Measured frontage of the No. 25 courtyard on Lane 1025, Nanjing West Road.

Local X follows the front toward No. 27, local Y points into the courtyard,
and Z is vertical. The two leaves and each pierced panel are separate meshes.
"""
from math import ceil, cos, pi, sin
from shapely.geometry import LineString, box
from photo_architecture import Facade

BRICK='burnt sienna facing brick'
RED='red-brown alternate facing brick'
DARK='dark fired header brick'
JOINT='warm grey brick joints'
PLINTH='bush-hammered granite plinth'
STONE='grey rendered pier dressings'
CAP='weathered grey projecting caps'
CREAM='off-white painted transom surround'
IRON='black gate and grille iron'
PANEL='charcoal leaf panels'
GREEN='enamel-green street plate'
WHITE='ivory enamel numerals'
PALETTE={
    BRICK:{'color':[.494,.230,.146],'roughness':.88},
    RED:{'color':[.555,.273,.170],'roughness':.90},
    DARK:{'color':[.418,.200,.145],'roughness':.87},
    JOINT:{'color':[.536,.466,.397],'roughness':.96},
    PLINTH:{'color':[.489,.481,.458],'roughness':.84},
    STONE:{'color':[.422,.420,.397],'roughness':.90},
    CAP:{'color':[.350,.348,.338],'roughness':.88},
    CREAM:{'color':[.706,.688,.649],'roughness':.86},
    IRON:{'color':[.105,.111,.110],'roughness':.50,'metallic':.42},
    PANEL:{'color':[.078,.084,.084],'roughness':.62,'metallic':.19},
    GREEN:{'color':[.074,.246,.209],'roughness':.44,'metallic':.14},
    WHITE:{'color':[.855,.857,.761],'roughness':.56},
}
LEFT,RIGHT=-2.40,1.98
GATE=-.64
OPEN=1.50
PIER=.39

def block(b,x,y,z,w,d,h,mat,name):
    b.box((x,y,z),(w,d,h),mat,label=name)

def line(b,points,r,mat,name,lod):
    b.tube(points,r,mat,4 if lod else 7,name)

def masonry(b,start,end,z0,z1,depth,name,lod):
    if end<=start:return
    block(b,(start+end)/2,depth/2,(z0+z1)/2,end-start,depth,z1-z0,BRICK if lod else JOINT,name+'/bed')
    if lod:return
    # The original running bond is visible on the jambs as well as the wing.
    course=.067;brick=.242
    for row in range(ceil((z1-z0)/course)):
        base=z0+row*course;top=min(z1,base+course)
        if top-base<.01:continue
        x=start-(brick/2 if row%2 else 0);col=0
        while x<end:
            l=max(start,x)+.003;r=min(end,x+brick)-.003
            if r-l>.014:
                mat=[BRICK,BRICK,RED,BRICK,DARK,RED,BRICK][(5*row+3*col)%7]
                block(b,(r+l)/2,-.005,(base+top)/2,r-l,.010,top-base-.005,mat,name+'/running-bond')
            col+=1;x+=brick

def pier(b,x,index,lod):
    name='gateway pier '+str(index)
    block(b,x,.175,.195,PIER+.056,.407,.39,PLINTH,name+'/stone foot')
    block(b,x,.175,.408,PIER+.044,.395,.05,STONE,name+'/plinth mould')
    masonry(b,x-PIER/2,x+PIER/2,.424,2.69,.35,name,lod)
    face=Facade(b,(x-PIER/2,0),(x+PIER/2,0),name+'/projecting shoulder')
    for part,(offset,width,bottom) in enumerate([(-.134,.121,2.55),(0,.140,2.47),(.134,.121,2.55)]):
        # Three dropped render tabs under each square crowning block.
        face.box(offset,(2.83+bottom)/2,width,2.83-bottom,.058,.012,STONE,'pendant '+str(part))
    for height,width,thick,mat in [(2.755,.428,.11,STONE),(2.832,.483,.059,CAP),(2.893,.469,.075,STONE),(2.963,.514,.076,CAP),(3.018,.494,.042,STONE)]:
        block(b,x,.165,height,width,width-.022,thick,mat,name+'/tiered coping')

def lattice(b,center,w,bottom,top,name,lod):
    low=bottom+.055;high=top-.055
    panel=box(center-w/2+.06,low,center+w/2-.06,high)
    slope=(high-low)/(w*1.28);step=w*(.72 if lod else .52)
    for direction in (-1,1):
        for i in range(-4,5):
            intercept=(low+high)/2+i*step*slope
            a=center-w;beyond=center+w
            geom=LineString([(a,intercept+direction*slope*(a-center)),(beyond,intercept+direction*slope*(beyond-center))]).intersection(panel)
            if geom.geom_type!='LineString' or geom.length<.04:continue
            start,end=list(geom.coords)
            line(b,[(start[0],-.052,start[1]),(end[0],-.052,end[1])],.011,IRON,name+'/diamond strap',lod)

def leaf(b,left,right,index,lod):
    xm=(left+right)/2;w=right-left;name='black iron leaf '+str(index)
    block(b,xm,.001,1.076,w-.018,.048,2.12,PANEL,name+'/back panel')
    for x in [left+.027,right-.027]:
        block(b,x,-.035,1.075,.043,.06,2.15,IRON,name+'/edge stile')
    for z in [.055,.14,.99,1.055,1.125,1.988,2.055,2.12]:
        block(b,xm,-.037,z,w-.028,.068,.032,IRON,name+'/rail')
    lattice(b,xm,w,.13,.985,name,lod)
    lattice(b,xm,w,1.13,1.99,name,lod)
    if not lod:
        for i in range(4):
            pts=[]
            for j in range(13):
                t=j*2*pi/12
                dx=.0275*(1+cos(t));dz=.020*sin(t)
                th=i*pi/2
                pts.append((xm+dx*cos(th)-dz*sin(th),-.076,1.53+dx*sin(th)+dz*cos(th)))
            line(b,pts,.008,IRON,name+'/four-leaf ironwork',lod)

def plaque(b,x,lod):
    block(b,x,-.021,2.227,.158,.029,.221,GREEN,'25 enamel address sign')
    # Model the two major white numerals directly. The small full address label
    # remains in the source record at these rendering scales.
    strokes=[[(.008,.091),(.015,.11),(.035,.113),(.042,.10),(.04,.084),(.007,.048),(.044,.048)],
             [(.050,.110),(.086,.11),(.081,.085),(.061,.085),(.075,.083),(.086,.074),(.085,.058),(.078,.051),(.055,.051)]]
    for n,points in enumerate(strokes):
        if n==1:
            points=[(.085,.110),(.055,.110),(.053,.084),(.072,.087),(.084,.077),(.084,.06),(.077,.051),(.055,.051)]
        line(b,[(x+xx-.047,-.04,2.172+zz)for xx,zz in points],.0036,WHITE,'enamel digit '+str(n),lod)
    if not lod:
        for dx in [-.068,.068]:
            for dz in [-.099,.099]:block(b,x+dx,-.038,2.227+dz,.005,.005,.005,STONE,'plaque fastener')

def add_building(b,lod=False):
    l=GATE-OPEN/2;r=GATE+OPEN/2
    for start,end in [(LEFT,l-PIER),(r+PIER,RIGHT)]:
        if start < GATE:
            masonry(b,start,end,.39,2.11,.20,'court street wall',lod)
        else:
            opening_left=start+.19;opening_right=end-.14
            masonry(b,start,end,.39,1.65,.20,'brick below the side vent',lod)
            masonry(b,start,opening_left,1.65,2.11,.20,'vent west jamb',lod)
            masonry(b,opening_right,end,1.65,2.11,.20,'vent east jamb',lod)
            masonry(b,opening_left,opening_right,1.97,2.11,.20,'brick vent head',lod)
            for i in range(1,7 if lod else 12):
                x=opening_left+(opening_right-opening_left)*i/(7 if lod else 12)
                block(b,x,.083,1.81,.018,.034,.32,IRON,'brick wing ventilation grille')
            block(b,(opening_left+opening_right)/2,.08,1.81,opening_right-opening_left,.036,.019,IRON,'wing grille cross rail')
        block(b,(start+end)/2,.10,.195,end-start,.236,.39,PLINTH,'coursed grey base')
        block(b,(start+end)/2,.10,2.122,end-start+.024,.238,.055,CAP,'narrow street wall coping')
    pier(b,l-PIER/2,1,lod);pier(b,r+PIER/2,2,lod)
    # Lower iron leaves, ventilating transom and the pale rendered rectangle
    # form a continuous portal, with actual openings between the grille bars.
    leaf(b,l+.005,GATE-.005,1,lod);leaf(b,GATE+.005,r-.005,2,lod)
    for x in [l+.047,r-.047]:block(b,x,.098,2.48,.094,.21,.69,CREAM,'rendered transom upright')
    block(b,GATE,.098,2.763,OPEN,.211,.258,CREAM,'rendered gateway head')
    block(b,GATE,.102,2.918,OPEN+.09,.27,.075,CAP,'gate head projecting course')
    for z in [2.213,2.571]:
        block(b,GATE,.072,z,OPEN-.19,.048,.037,IRON,'transom horizontal rail')
    count=6 if lod else 11
    for i in range(count+1):
        x=l+.113+(OPEN-.226)*i/count
        block(b,x,.072,2.393,.017,.042,.359,IRON,'transom vertical bar')
    if not lod:
        for dx in [-.15,0,.15]:
            line(b,[(GATE+dx-.087,-.029,2.125),(GATE+dx,-.029,2.189),(GATE+dx+.087,-.029,2.125)],.009,IRON,'low crest over gate',lod)
    plaque(b,l-PIER/2,lod)
