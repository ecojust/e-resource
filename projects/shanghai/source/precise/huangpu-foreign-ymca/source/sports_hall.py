"""Street podium, six-storey projecting wings and the recessed court of the Foreign YMCA."""
from math import cos, pi, sin
from pathlib import Path

from shapely import affinity
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade, opening
from sign_lettering import add_facade_lettering

PALETTE = {
    'pale buff brick': {'color':[.53,.41,.28],'roughness':.88},
    'ochre reveal brick': {'color':[.39,.29,.19],'roughness':.88},
    'brown diaper brick': {'color':[.28,.15,.105],'roughness':.84},
    'iron-fired brick': {'color':[.19,.121,.098],'roughness':.92},
    'buff header brick': {'color':[.40,.295,.20],'roughness':.88},
    'deep red-brown brick': {'color':[.225,.135,.114],'roughness':.88},
    'cream architectural stone': {'color':[.67,.60,.45],'roughness':.70},
    'stone door surround': {'color':[.47,.44,.34],'roughness':.76},
    'dark window joinery': {'color':[.081,.077,.065],'roughness':.62},
    'smoky window glass': {'color':[.12,.155,.17],'roughness':.27,'metallic':.14},
    'glass marquee roof': {'color':[.30,.34,.32],'roughness':.31,'metallic':.19},
    'weathered canopy iron': {'color':[.12,.117,.106],'roughness':.54,'metallic':.4},
    'bronze and gold': {'color':[.65,.43,.13],'roughness':.47,'metallic':.47},
    'roof membrane': {'color':[.32,.305,.27],'roughness':.94},
    'unseen masonry': {'color':[.43,.36,.27],'roughness':.91},
}
BRICK='pale buff brick'
BROWN='brown diaper brick'
DARK='deep red-brown brick'
STONE='cream architectural stone'
FRAME='dark window joinery'
GLASS='smoky window glass'
PODIUM=13.55
HALF=13.45
DEPTH=33.12
COURT=23.8
FONT=Path(__file__).with_name('fonts')/'SportsHallSign.otf'


def plan(left,right,front,back):
    """The frozen rear edge is 0.67 m northeast of the front alignment."""
    return Polygon([(left+.0201*front,front),(right+.0201*front,front),
                    (right+.0201*back,back),(left+.0201*back,back)])


def face(b,a,c,name):
    return Facade(b,(a[0]+.0201*a[1],a[1]),(c[0]+.0201*c[1],c[1]),name)


def glass(f,shape,lod,name,columns=3,rows=3,recess=.40):
    """A pane behind a pierced wall and a separate continuous window frame."""
    x0,z0,x1,z1=shape.bounds
    closed=shape.buffer(.015,join_style='mitre')
    f.prism(closed,-recess-.04,-recess,GLASS,name+' pane')
    inner=shape.buffer(-.065,join_style='mitre')
    bars=[]
    cols=min(columns,2) if lod else columns
    rows=min(rows,3) if lod else rows
    for i in range(1,cols):
        x=x0+(x1-x0)*i/cols;bars.append(box(x-.025,z0,x+.025,z1))
    for i in range(1,rows):
        z=z0+(z1-z0)*i/rows;bars.append(box(x0,z-.029,x1,z+.029))
    void=inner.difference(unary_union(bars)) if bars else inner
    f.prism(shape.difference(void),-recess+.018,-recess+.094,FRAME,name+' sash')


def rim(f,shape,width,material,name,lo=.006,hi=.093):
    surround=shape.buffer(width,join_style='mitre').difference(shape)
    if surround.bounds[1]<0:
        surround=surround.intersection(box(-50,.012,50,50))
    f.prism(surround,lo,hi,material,name)


def diamond(x,z,w,h):
    return Polygon([(x,z+h/2),(x+w/2,z),(x,z-h/2),(x-w/2,z)])


def diaper_wall(f,wall,lod):
    # Two nested clay geometries make the diamond diagonal, its pale field and a small centre.
    pitch=1.24;items=[];dots=[]
    for row in range(9):
        z=4.25+row*pitch
        for col in range(-12,13):
            x=col*pitch
            outer=diamond(x,z,pitch,pitch);inner=diamond(x,z,pitch-.29,pitch-.29)
            items.append(outer.difference(inner))
            dots.append(diamond(x,z,.20,.21))
    pattern=wall.intersection(unary_union(items))
    f.prism(pattern,.004,.030,BROWN,'diagonal brick diaper')
    if not lod:
        f.prism(wall.intersection(unary_union(dots)),.006,.035,'ochre reveal brick','diamond centres')


def shaft(b,x,y,z0,z1,lod,label):
    width=.18
    b.lathe((x,y),[(z0,width*1.4),(z0+.12,width*1.35),(z0+.22,width),
                   (z1-.48,width*.86),(z1-.36,width*1.22),(z1-.17,width*1.51),(z1,width*1.53)],
            STONE,10 if lod else 20,label)
    b.box((x,y,z1+.035),(.53,.51,.10),STONE,label=label+' abacus')
    if not lod:
        for dx in [-.12,.12]:
            b.box((x+dx,y-.16,z1-.21),(.095,.095,.23),'ochre reveal brick',label=label+' capital leaves')


def marquee(b,f,lod):
    span=9.98; depth=1.5; z=3.96
    b.box((0,-.56,z),(span,depth,.12),'glass marquee roof',label='Marquee/translucent infill')
    for i in range(-5,6):
        b.box((i*.978,-.56,z+.018),(.077,depth+.1,.15),'weathered canopy iron',label='Marquee/glazing bars')
    b.box((0,-1.33,z+.05),(span+.10,.11,.31),'weathered canopy iron',label='Marquee/deep fascia')
    for x in [-4.99,4.99]:
        b.box((x,-.57,z+.045),(.12,depth+.08,.30),'weathered canopy iron',label='Marquee/side rails')
    front=face(b,(-span/2,-1.394),(span/2,-1.394),'Marquee')
    for j in range(-5,6):
        c=j*.86
        pts=[(c+.27*cos(i*2*pi/20),z+.068+.082*sin(i*2*pi/20)) for i in range(20 if not lod else 0)]
        if pts:front.prism(Polygon(pts),.006,.032,'bronze and gold','oval bosses')


def street_base(b,lod):
    f=face(b,(-HALF,.12),(HALF,.12),'Nanjing Road')
    base=[];upper=[];seg=12 if lod else 28
    for u in [-3.14,0,3.14]:
        door=opening(u,.19,1.62,2.93);base.append(door);glass(f,door,lod,'entrance',2,3,.64)
        rim(f,door,.29,'stone door surround','carved entrance frame',.01,.19)
        f.box(u,3.27,2.34,.18,.19,.035,'stone door surround','entrance head')
        tall=opening(u,4.22,2.76,8.19,1.36,seg);upper.append(tall);glass(f,tall,lod,'tall hall light',4,8,.66)
        # The dark middle spandrel and two horizontal window bars are visible in the close photograph.
        f.box(u,8.15,2.69,1.47,.08,-.50,'weathered canopy iron','opaque window spandrel')
        rim(f,tall,.145,'ochre reveal brick','central archivolt',.012,.144)
        rim(f,tall.buffer(.155,join_style='mitre'),.08,STONE,'fine archivolt',.01,.08)
    for side in (-1,1):
        center=side*8.93
        for x in [center-2.53,center+2.53]:
            bottom=opening(x,4.39,.95,2.88);upper.append(bottom);glass(f,bottom,lod,'flank lower lights',2,3)
            small=opening(x,9.10,.91,2.19,.45,seg);upper.append(small);glass(f,small,lod,'flank arched lights',2,3)
            rim(f,small,.11,'ochre reveal brick','small arch')
        pair=[]
        for dx in (-.55,.55):
            small=opening(center+dx,5.16,.95,5.99,.47,seg);upper.append(small);pair.append(small)
            glass(f,small,lod,'paired side hall lights',2,5,.51)
        # Each pair sits below a single pale semicircular hood.
        arch=opening(center,8.24,2.45,3.68,1.20,seg)
        trim=arch.difference(unary_union(pair)).intersection(box(center-1.4,10.62,center+1.4,12.5))
        f.prism(trim,.008,.106,STONE,'paired arch tympanum')
        hood=arch.buffer(.115,join_style='mitre').difference(arch).intersection(box(center-1.5,10.60,center+1.5,12.6))
        f.prism(hood,.006,.125,'ochre reveal brick','paired round hood')
        f.box(center,7.24,.145,4.28,.24,.08,STONE,'paired light central post')
        for dx in (-2.48,0,2.48):
            low=opening(center+dx,.38,1.59,2.53,.74,seg);base.append(low)
            glass(f,low,lod,'ground floor arched display',2,3)
            rim(f,low,.115,'ochre reveal brick','retail arch')
    f.wall(.10,4.1,base,.34,DARK);f.wall(4.1,PODIUM,upper,.39,BRICK)
    if not lod:
        masonry=box(-HALF,.12,HALF,4.07).difference(unary_union(base))
        faces=[[],[]]
        for row in range(24):
            bottom=.13+row*.163
            for column in range(-29,29):
                x=column*.49+(row%2)*.245
                patch=box(x+.012,bottom,x+.48,bottom+.147)
                faces[(row*5+column*3)%7==0].append(patch)
        for bricks,material in zip(faces,[DARK,'iron-fired brick']):
            f.prism(masonry.intersection(unary_union(bricks)),.008,.032,material,'ground floor running-bond brick')
    field=box(-HALF,4.1,HALF,PODIUM-.52).difference(unary_union(upper))
    diaper_wall(f,field,lod)
    for x in (-1.57,1.57):
        for dx in (-.19,.19):shaft(b,x+dx,.015,4.16,11.03,lod,'Arcade/paired stone piers')
    for z,wd,mat in [(4.03,.19,DARK),(13.06,.17,BROWN),(13.32,.30,'ochre reveal brick'),(13.49,.39,'roof membrane')]:
        f.beam(z,.13,wd,mat,label='stepped cornice')
    marquee(b,f,lod)
    if not lod:
        for x in [-4.48,-1.61,1.61,4.48]:
            f.box(x,1.92,.19,2.44,.11,.065,'bronze and gold','entrance pier plaques')


def crown_panel(f,u,z,lod):
    rim_shape=diamond(u,z,.91,.54)
    f.prism(rim_shape,.008,.040,'ochre reveal brick','spandrel lozenge')
    f.prism(diamond(u,z,.54,.32),.044,.070,STONE,'pale inset spandrel')
    if not lod:f.prism(diamond(u,z,.22,.15),.072,.087,'ochre reveal brick','small lozenge')


def tower_face(f,lod,street=True):
    count=3 if street else 7
    pitch=f.length/count
    levels=[14.18,17.13,20.08,23.03,25.98,28.93]
    cuts=[]
    for i in range(count):
        u=(i-(count-1)/2)*pitch
        ribbon=box(u-pitch*.30,PODIUM,u+pitch*.30,32.72)
        bay=[]
        for floor,z in enumerate(levels):
            if floor==5 and street:
                for offset in (-.35,.35):
                    top=opening(u+offset,z,.62,2.22,.30,12 if lod else 22);bay.append(top)
                    glass(f,top,lod,'paired upper sash',2,3)
                    rim(f,top,.064,STONE,'upper round head',.018,.083)
            else:
                width=1.48 if street else 1.30
                cut=opening(u,z,width,1.95);bay.append(cut)
                glass(f,cut,lod,'sash',3,4)
                f.box(u,z-.06,width+.13,.10,.19,.045,'ochre reveal brick','brick sill')
            if street and floor<5:
                if not lod or floor in (0,3):crown_panel(f,u,z+2.44,lod)
        cuts.extend(bay)
        f.prism(ribbon.difference(unary_union(bay)),.001,.012,DARK,'recessed spandrel strips')
        if street:
            crown_panel(f,u,32.04,lod)
            hood=opening(u,30.56,1.70,1.06,.78,10 if lod else 20)
            strip=hood.buffer(.092,join_style='mitre').difference(hood).intersection(box(u-.98,30.90,u+.98,32))
            f.prism(strip,.015,.092,'ochre reveal brick','paired sash outer arch')
        elif not lod:
            f.box(u,32.25,pitch*.71,.20,.17,.04,'ochre reveal brick','court cornice')
    f.wall(PODIUM,32.66,cuts,.34,BRICK)
    for i in range(count+1):
        edge=i in (0,count);u=-f.length/2+i*pitch
        if edge:u+=.405 if i==0 else -.405
        if street:
            width=.88 if edge else .73;top=34.89 if edge else 33.97
        else:
            width=.42;top=33.10 if not edge else 33.32
        f.box(u,(PODIUM+top)/2,width,top-PODIUM,.65,.16,BRICK,'projecting full-height piers')
        if street and not lod:
            for k in range(37):
                z=PODIUM+.31+k*.53
                if z>top-.36:break
                x=u+([-.20,.12,-.08,.21,.03][(k+2*i)%5])*width
                f.box(x,z,.15 if k%3 else .21,.058,.025,.492,'buff header brick','weathered pier headers')
        f.box(u,top-.12,width+.12,.22,.72,.17,'ochre reveal brick','pier head')
        f.box(u,top-.021,width+.16,.075,.80,.17,'roof membrane','pier coping')
    f.beam(32.59,.13,.16,'ochre reveal brick',label='castellated parapet base')


def rear_court(b,lod):
    f=face(b,(-4.55,COURT),(4.55,COURT),'Recessed north court facade')
    cuts=[];levels=[14.24,17.20,20.15,23.10,26.05,29.00]
    for u in (-3.50,-2.19,2.19,3.50):
        for i,z in enumerate(levels):
            cut=opening(u,z,.73,1.68,.34 if i in (3,5) else 0,10 if lod else 20)
            cuts.append(cut);glass(f,cut,lod,'return sash',2,3)
    for z,h in [(14.3,2.4),(17.40,2.47),(20.4,5.34),(27.5,2.3)]:
        cut=opening(0,z,1.07,h,.52 if z in (20.4,27.5) else 0,12 if lod else 22)
        cuts.append(cut);glass(f,cut,lod,'central raised panel sash',2,4)
    f.wall(PODIUM,31.56,cuts,.35,BRICK)
    for u in [-4.42,-1.63,1.63,4.42]:
        f.box(u,22.57,.29,18.05,.48,.10,'ochre reveal brick','court pilasters')
    for u in (-.94,.94):
        f.box(u,24.15,.19,11.3,.44,.10,'ochre reveal brick','recessed arch side')
    f.beam(31.58,.17,.12,'roof membrane',label='court coping')


def make_hall(b,lod):
    street_base(b,lod)
    # Ground is the solid mass bounded by the three independently pierced entrance bays.
    base=plan(-HALF,HALF,.13,DEPTH)
    for x in [-3.14,0,3.14]:base=base.difference(box(x-.86,0,x+.86,.79))
    b.plan_prism(base,0,.13,'unseen masonry','Podium/enclosed floor')
    b.plan_prism(plan(-HALF,HALF,.13,DEPTH),PODIUM-.17,PODIUM,'roof membrane','Podium/court terrace')
    for left,right,label in [(-HALF,-4.54,'West wing'),(4.54,HALF,'East wing')]:
        tower_face(face(b,(left,.62),(right,.62),label+' street'),lod)
        if left<0:inside=[(right,.64),(right,COURT)]
        else:inside=[(left,COURT),(left,.64)]
        tower_face(face(b,*inside,label+' light court'),lod,street=False)
        b.plan_prism(plan(left,right,.65,COURT+.28),32.39,32.63,'roof membrane',label+'/flat roof')
        outside=left if left<0 else right
        side_points=[(outside,.62),(outside,DEPTH)]
        if left<0:side_points.reverse()
        edge=face(b,*side_points,label+' concealed side')
        edge.wall(.12,32.67,[],.14,'unseen masonry')
        # The lower rear roof meets both wings below their parapets.
        return_edge=face(b,(right,COURT+.22),(left,COURT+.22),label+' rear roof return')
        return_edge.wall(31.47,32.65,[],.17,'ochre reveal brick')
        short=[(outside,.13),(outside,.68)]
        if left<0:short.reverse()
        edge=face(b,*short,label+' podium return')
        edge.wall(.10,PODIUM,[],.14,DARK)
    rear_court(b,lod)
    b.plan_prism(plan(-HALF,HALF,COURT,DEPTH),31.31,31.56,'roof membrane','Rear block/flat roof')
    rear=face(b,(HALF,DEPTH),(-HALF,DEPTH),'Rear block')
    rear.wall(.10,31.61,[],.23,'unseen masonry')
    rear.beam(31.59,.11,.07,'roof membrane',label='rear coping')
    for u in [-4.5,-2.25,0,2.25,4.5]:
        b.box((u,1.12,13.93),(.065,.065,.79),'weathered canopy iron',label='Roof name/sign posts')
    sign=face(b,(-4.55,1.09),(4.55,1.09),'Roof name')
    add_facade_lettering(sign,'体育大厦',0,14.35,7.66,1.12,.030,.119,'bronze and gold',label='golden characters',font=FONT)
