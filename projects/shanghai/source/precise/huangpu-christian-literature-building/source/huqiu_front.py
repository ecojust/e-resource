"""West street face of the 1930s paired buildings. All dimensions in metres."""
from pathlib import Path
from math import ceil,cos,sin,pi
from shapely import union_all
from shapely.affinity import translate
from shapely.geometry import box,Polygon
from photo_architecture import Facade
from sign_lettering import lettering_shapes
W=9.56
BACK=2.85
BASE=3.65
RISE=3.03
TOP=BASE+7*RISE
CENTER=2.93
ARCH=1.54
CROWN=28.12
FONT=Path(__file__).parent/'fonts/PlaqueSubset.otf'
PALETTE={k:{'color':c,'roughness':r}for k,c,r in [
 ('weathered mortar',[.322,.294,.279],.99),('violet-brown tile',[.25,.178,.159],.88),
 ('dark brown tile',[.219,.167,.152],.87),('umber tile',[.283,.205,.184],.88),
 ('rose stone',[.554,.402,.343],.91),('rose arris',[.585,.445,.368],.87),('rose joint',[.445,.35,.311],.96),
 ('sandstone',[.727,.678,.585],.93),('weathered sandstone',[.594,.556,.486],.96),('pale stone cap',[.704,.672,.594],.89),
 ('bronze sash',[.182,.165,.138],.71),('aged glazing',[.221,.268,.273],.38),
 ('decorated spandrel',[.371,.315,.253],.87),('cast spandrel rib',[.488,.414,.334],.84),
 ('recessed door',[.109,.122,.124],.88),('metal sign',[.129,.126,.111],.73),
 ('lead coping',[.278,.291,.285],.84),('neutral section',[.505,.487,.454],.99)]}

def pointed(x,base,width,spring,rise):
    # Two circular arcs meet at a true point above the vertical jambs.
    from math import atan2,hypot
    h=width/2;offset=(rise*rise-h*h)/(2*h)
    radius=offset+h;angle=atan2(rise,offset)
    right=[(x-offset+radius*cos(angle*i/15),spring+radius*sin(angle*i/15))for i in range(16)]
    return Polygon([(x-h,base),(x+h,base),*right,*[(2*x-a,z)for a,z in reversed(right[:-1])]])

def grid(f,shape,cols,rows,lod,label):
    x0,z0,x1,z1=shape.bounds;rim=.064 if x1-x0>2 else .042
    edge=shape.difference(shape.buffer(-rim,join_style=2))
    for j in range(1,cols):
        v=x0+(x1-x0)*j/cols;edge=edge.union(shape.intersection(box(v-.023,z0,v+.023,z1)))
    for j in range(1,rows):
        z=z0+(z1-z0)*(0.69 if rows==2 else j/rows);edge=edge.union(shape.intersection(box(x0,z-.024,x1,z+.024)))
    f.prism(shape.buffer(.008,join_style=2),-.315,-.291,'aged glazing',label+'/glazing')
    f.prism(edge,-.211,-.164,'bronze sash',label+'/metal grid')
    if not lod:f.box((x0+x1)/2,z0-.034,x1-x0+.055,.068,.21,.015,'dark brown tile',label+'/sill')

def brick_field(f,face,lod,label):
    x0,z0,x1,z1=face.bounds
    width,height=(.53,.26) if lod else (.262,.154)
    for row in range(ceil((z1-z0)/height)):
        left=x0-width/2*(row%2);z=z0+row*height
        for n in range(ceil((x1-left)/width)):
            x=left+n*width
            a=face.intersection(box(x+.007,z+.006,min(x+width-.006,x1),min(z+height-.006,z1)))
            if a.area<.001:continue
            mat=('dark brown tile','violet-brown tile','umber tile')[(row*13+n*17+n//4+row//5)%3]
            f.prism(a,-.004,.011,mat,label)

def crown_pier(b,x,front,z0,z1,size,label,lod):
    # Five faces form the paired points visible on the piers and their caps.
    plan=Polygon([(x-size/2,front+.17),(x-size/2,front-.035),(x-size*.32,front-.135),
                  (x-size*.17,front-.086),(x,front-.205),(x+size*.17,front-.086),
                  (x+size*.32,front-.135),(x+size/2,front-.035),(x+size/2,front+.17)])
    b.plan_prism(plan,z0,z1,'dark brown tile',label+'/faceted brick')
    step=.37 if lod else .183
    for j in range(1,int((z1-z0)/step)):
        z=z0+j*step;b.plan_prism(plan.buffer(.002,join_style=2),z,z+.012,'weathered mortar',label+'/bedded joints')
    cap=plan.buffer(.025,join_style=2)
    b.plan_prism(cap,z1,z1+.115,'pale stone cap',label+'/stone neck')
    from shapely.geometry import Point
    contour=list(cap.exterior.coords)[:-1];tip=(x,front-.075,z1+.44)
    b.add([(u,y,z1+.115)for u,y in contour]+[tip],[(j,(j+1)%len(contour),len(contour))for j in range(len(contour))],'pale stone cap',label+'/pointed stone cap')

def entry(b,lod):
    f=Facade(b,(-W,0),(W,0),'Stone street base')
    portal=box(-.83,.05,.83,2.69);lancets=[pointed(side*2.12,.09,.70,1.62,.65)for side in (-1,1)]
    shops=[box(-9.24,.43,-3.27,2.83),box(3.27,.43,9.24,2.83)]
    openings=[portal,*lancets,*shops]
    stone=f.wall(.09,BASE,openings,.47,'weathered sandstone')
    for j in range(3):
        z=.10+j*1.13;width=1.44 if j%2 else 1.51
        for i in range(-8,8):
            lo=max(-W,i*width+.014);hi=min(W,(i+1)*width-.011)
            if lo>=hi:continue
            tile=stone.intersection(box(lo,z+.013,hi,min(z+1.12,BASE)))
            if tile.area>.008:f.prism(tile,0,.025,'sandstone','staggered ashlar')
    for side,ap in zip((-1,1),shops):
        grid(f,ap,4,1,lod,'shop glazing')
        near=lancets[0 if side<0 else 1];f.prism(near,-.64,-.61,'recessed door','narrow pointed side light')
        f.prism(near.buffer(.095,join_style=2).difference(near),.025,.095,'pale stone cap','lancet arris')
    f.prism(portal,-.573,-.55,'recessed door','recessed double street doors')
    for side in (-1,1):
        x=side*.408;f.box(x,1.64,.63,1.53,.052,-.49,'aged glazing','door glass')
    f.prism(portal.buffer(.12,join_style=2).difference(portal),-.08,.07,'sandstone','returning entry jamb')
    for side in (-1,1):f.box(side*.13,1.15,.034,.34,.085,-.42,'bronze sash','door pull')
    # Lettering follows the two surviving rows visible in the pre-repair 2022 press photo.
    for text,w,h,z in [('CHRISTIAN LITERATURE SOCIETY BUILDING',5.36,.167,3.30),('廣學大樓',1.38,.196,2.98)]:
        for ch,outline in lettering_shapes(text,w,h,font=FONT):
            f.prism(translate(outline,yoff=z),.028,.048,'metal sign','inscription/'+ch)
    for lo,hi in [(-W,-.83),(.83,W)]:
        f.box((lo+hi)/2,.068,hi-lo,.136,.48,-.17,'weathered sandstone','base course')

def flanks(b,lod):
    front=Facade(b,(-W,0),(W,0),'Main street flanks')
    for side in (-1,1):
        lo,hi=sorted((side*CENTER,side*W));span=hi-lo;spacing=span/5;w=spacing-.245
        holes=[]
        for i in range(5):
            u=lo+(i+.5)*spacing
            for j in range(7):
                z=BASE+.31+j*RISE
                ap=box(u-w/2,z,u+w/2,z+2.02);holes.append(ap);grid(front,ap,2,2,lod,'wing casements')
        field=box(lo,BASE,hi,TOP+.78).difference(union_all(holes))
        front.prism(field,-.39,0,'weathered mortar','upper wall')
        brick_field(front,field,lod,'tile spandrels')
        for i in range(6):
            x=lo+i*spacing
            if abs(abs(x)-CENTER)<.001:continue
            peak=TOP+1.18 if i%2 else TOP+1.02
            crown_pier(b,x,.018,BASE,peak,.245 if i%2 else .29,'Street piers',lod)
        for i in range(5):
            x=lo+(i+.5)*spacing
            pane=box(x-.34,TOP-.31,x+.34,TOP+.51)
            front.prism(pane,-.005,.025,'dark brown tile','recessed parapet panel')
            front.prism(pane.buffer(.038,join_style=2).difference(pane),.016,.067,'umber tile','parapet rim')
            for offset in (-.22,.22):
                tag=Polygon([(x+offset-.075,TOP+.13),(x+offset,TOP+.42),(x+offset+.075,TOP+.13),(x+offset,TOP+.21)])
                front.prism(tag,.022,.075,'pale stone cap','pointed parapet accents')

def center_arch(b,lod):
    f=Facade(b,(-W,-.126),(W,-.126),'Giant stone pointed surround')
    ap=pointed(0,BASE,2*ARCH,23.83,2.98)
    out=box(-CENTER,BASE,CENTER,CROWN)
    surface=out.difference(ap);f.prism(surface,-.47,.235,'rose joint','continuous outer mass')
    for row in range(27):
        low=BASE+row*.924
        for x0,x1 in [(-CENTER,-1.48),(-1.48,0),(0,1.48),(1.48,CENTER)]:
            stone=surface.intersection(box(x0+.004,low+.006,x1-.004,min(CROWN,low+.917)))
            if stone.area>.001:f.prism(stone,.231,.250,'rose stone','rose stone ashlar')
    f.prism(ap.buffer(.095,join_style=2).difference(ap).intersection(out),.214,.285,'rose arris','deep pointed arris')
    backing=Facade(b,(-W,.26),(W,.26),'Central window stack')
    for j in range(7):
        z=BASE+.27+j*RISE;top=z+2.02
        for i in range(3):
            x=(i-1)*1.002;window=box(x-.454,z,x+.454,top)
            grid(backing,window,1,2,lod,'three centre lights')
        band=box(-ARCH,top,ARCH,min(top+1.015,25.20))
        if band.area>0:
            backing.prism(band,-.22,0,'decorated spandrel','cast window spandrel')
            for i in range(3):
                x=(i-1)*1.002
                pattern=Polygon([(x-.310,top+.44),(x,top+.74),(x+.310,top+.44),(x,top+.14)])
                if pattern.within(band):
                    ridge=pattern.difference(pattern.buffer(-.04,join_style=2))
                    backing.prism(ridge,0,.028,'cast spandrel rib','cast lozenge')
    for x in [-1.51,-.5,.5,1.51]:
        head=24.08 if abs(x)>1 else 26.18
        backing.box(x,(BASE+head)/2,.096,head-BASE,.18,.095,'pale stone cap','vertical stone mullion')
    head=ap.intersection(box(-ARCH,24.85,ARCH,27.4))
    backing.prism(head,-.285,-.245,'decorated spandrel','pointed head infill')
    backing.prism(head.buffer(-.075,join_style=2),-.24,-.22,'rose joint','recessed head panel')
    b.box((0,.58,CROWN+.038),(2*CENTER+.11,1.46,.076),'lead coping',label='Central crown/metal coping')

def returns(b,lod):
    for side in (-1,1):
        if side>0:f=Facade(b,(W,0),(W,BACK))
        else:f=Facade(b,(-W,BACK),(-W,0))
        f.label='Shallow side return'
        end=f.length*.5;holes=[box(-.47,BASE+.36+j*RISE,.47,BASE+2.34+j*RISE)for j in range(7)]
        ground=box(-.95,.38,.95,2.75)
        f.wall(.09,BASE,[ground],.27,'weathered sandstone');grid(f,ground,2,1,lod,'side ground glazing')
        wall=f.wall(BASE,TOP+.76,holes,.28,'weathered mortar')
        brick_field(f,wall,lod,'side brick courses')
        for ap in holes:grid(f,ap,2,2,lod,'side casements')
        for x in [-.77,.77]:f.box(x,(BASE+TOP+.73)/2,.17,TOP+.73-BASE,.25,.07,'dark brown tile','side rib')
    b.box((0,BACK-.075,(TOP+.70)/2),(2*W-.30,.15,TOP+.70),'neutral section',label='Section/back of street slice')
    b.box((0,BACK/2,TOP+.76),(2*W-.16,BACK-.04,.12),'lead coping',label='Section/low outer parapet cap')
    b.box((0,1.37,(CROWN+TOP+.74)/2),(2*CENTER,.74,CROWN-TOP-.74),'rose joint',label='Crown/raised return')
    for side in (-1,1):
        b.box((side*(CENTER-.085),.46,(CROWN+TOP+.74)/2),(.17,1.14,CROWN-TOP-.74),'rose stone',label='Crown/solid side return')
def add_west(b,lod):
    entry(b,lod)
    flanks(b,lod)
    center_arch(b,lod)
    returns(b,lod)
