"""Ningbo Road elevation, based on the street photographs and 2017 restoration report."""
from math import cos, sin, pi
from pathlib import Path
from repeat import repeat_only_texture
from stone import wall_uv
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade

WALL = 'buff masonry'
TRIM = 'warm carved stone'
GLASS = 'recessed glass'
WOOD = 'red brown window joinery'
IRON = 'balcony ironwork'
DARK = 'deep door bronze'
PALETTE = {
    WALL: {'color':[1.,1.,1.], 'roughness':.91, 'texture':str(Path(__file__).with_name('guild-stone.png'))},
    TRIM: {'color':[.72,.64,.52], 'roughness':.87},
    GLASS:{'color':[.23,.29,.29], 'roughness':.32},
    WOOD: {'color':[.235,.10,.067], 'roughness':.65},
    IRON: {'color':[.17,.17,.15], 'roughness':.67},
    DARK: {'color':[.18,.15,.11], 'roughness':.72},
}
HALF = 7.54
AXES = (-4.88,0.,4.88)
BALCONY = 8.60

def arch(x, half, spring, rise, steps):
    return Polygon([(x-half,.03),(x+half,.03),*[(x+half*cos(pi*i/steps), spring+rise*sin(pi*i/steps)) for i in range(steps+1)]])

def glazed(front, cut, frame, rows, columns, label):
    x0,z0,x1,z1=cut.bounds
    front.prism(cut,-.365,-.34,GLASS,label+' glass')
    bars=[cut.difference(cut.buffer(-.065,join_style=2))]
    for i in range(1,columns):
        x=x0+(x1-x0)*i/columns
        bars.append(box(x-.032,z0,x+.032,z1).intersection(cut))
    for i in rows:
        z=z0+(z1-z0)*i
        bars.append(box(x0,z-.029,x1,z+.029).intersection(cut))
    front.prism(unary_union(bars),-.332,-.225,frame,label+' joinery')

def line(front, points, radius, material, sides, name):
    front.builder.tube([front.point(*p)for p in points],radius,material,sides,name)

def street_wall(front, distant):
    holes=[]
    central=arch(0,1.32,3.08,1.20,14 if distant else 28)
    holes.append(central);glazed(front,central,DARK,[.13,.70],2,'Entrance')
    upper=box(-1.33,3.08,1.33,4.3)
    head=central.intersection(upper)
    frame=head.buffer(.135).difference(head).intersection(box(-1.5,3.08,1.5,4.53))
    front.prism(frame,.014,.22,TRIM,'Entrance arch moulding')
    front.box(0,4.35,.29,.35,.37,.16,TRIM,'Entrance crown stone')
    for x in (-1.45,1.45):
        profile=[(.06,.235),(.16,.235),(.21,.201),(.31,.174),(2.87,.16),(2.96,.174),(3.02,.204),(3.10,.21)]
        front.builder.lathe((x,-.24),profile,TRIM,20 if distant else 32,'Entrance paired stone shafts')
        front.box(x,3.13,.49,.12,.58,.21,TRIM,'Entrance imposts')
    for x in (AXES[0],AXES[2]):
        light=box(x-1.80,.89,x+1.80,3.70);holes.append(light)
        glazed(front,light,WOOD,[.17,.81],3,'Shop windows')
        front.box(x,.78,3.88,.14,.34,.07,TRIM,'Shop window sills')
    for x in AXES:
        for z0,z1,name in [(5.25,8.28,'Second floor'),(8.67,11.18,'Balcony doors'),(12.65,14.49,'Fourth floor')]:
            for offset in (-1.10,0,1.10):
                light=box(x+offset-.457,z0,x+offset+.457,z1);holes.append(light)
                glazed(front,light,WOOD,[.80] if distant else [.76,.87],1,name)
            front.box(x,z0-.09,3.74,.15,.37,.055,TRIM,name+' foot ledge')
        for j in (-1,0,1):
            u=x+j*1.12
            chain=[(u-.27,4.45,.039),(u,4.24,.039),(u+.27,4.45,.039)]
            line(front,chain,.018,TRIM,5,'Second floor incised panel detail')
    front.prism(box(-HALF,.0,HALF,15.65).difference(unary_union(holes)),-.96,0,WALL,'Revealed street wall')
    for x in (-7.20,-2.44,2.44,7.20):
        width=.55 if abs(x)>5 else .52
        for j in range(24):
            z=.30+j*.64
            front.box(x,z,width,.608,.17,.055,TRIM,'Coursed piers')
    for x in AXES:
        front.box(x,14.74,4.07,.21,.52,.19,TRIM,'Window head architraves')
        front.box(x,14.94,4.28,.13,.68,.21,TRIM,'Projecting upper cornice')
        for i in range(9):
            front.box(x-1.76+i*.44,14.79,.14,.22,.28,.26,TRIM,'Cornice small consoles')
        front.box(x,15.20 if x else 15.33,4.10,.27 if x else .51,.35,.10,TRIM,'Stepped upper panels')
    front.box(0,15.63,4.32,.13,.55,.15,TRIM,'Central rising cornice')

def balcony(front,x,distant):
    front.box(x,BALCONY,4.47,.20,1.13,.47,TRIM,'Separate projecting balcony decks')
    front.box(x,BALCONY+.085,4.57,.085,1.22,.50,TRIM,'Balcony drip mould')
    bracket=Polygon([(-.07,0),(.91,0),(.92,-.105),(.81,-.145),(.70,-.164),(.54,-.25),(.39,-.36),(.23,-.53),(.11,-.69),(-.07,-.69)])
    for off in (-1.70,0,1.70):
        u=x+off
        def to_side(d,z,thick):return front.point(u-thick,BALCONY-.10+z,d)
        front.builder.prism(bracket,-.12,.12,to_side,TRIM,'Carved balcony brackets')
    z=BALCONY+.13
    front.box(x,z+.88,4.49,.066,.076,1.042,IRON,'Rail crowning bars')
    front.box(x,z+.105,4.44,.041,.042,1.042,IRON,'Rail foot bars')
    for u in (-2.19,2.19):
        front.box(x+u,z+.90,.068,.062,1.06,.54,IRON,'Balcony return tops')
        for d in (.19,.45,.70,.94):
            front.box(x+u,z+.48,.035,.83,.034,d,IRON,'Return pickets')
    for i in range(17):
        u=x-2.16+4.32*i/16
        front.box(u,z+.49,.033,.83,.035,1.042,IRON,'Balcony straight pickets')
    for i in range(8):
        u=x-1.89+i*.54
        points=[(u+.195*cos(2*pi*k/(9 if distant else 16)),z+.48+.28*sin(2*pi*k/(9 if distant else 16)),1.046)for k in range((9 if distant else 16)+1)]
        line(front,points,.018,IRON,5 if distant else 7,'Pierced oval rail motifs')

def festoons(front,x,distant):
    for i in range(3):
        u=x+(i-1)*1.02
        count=7 if distant else 13
        for rad,offset in ((.040,.0),(.026,-.085)):
            points=[(u-.48+.96*j/count,11.98+offset-.286*sin(pi*j/count),.096)for j in range(count+1)]
            line(front,points,rad,TRIM,6 if distant else 8,'Swag relief')
        if not distant:
            for j in (1,2,3,4,5):
                xx=u-.48+.96*j/6;zz=11.98-.286*sin(pi*j/6)
                shape=Polygon([(xx-.05,zz-.03),(xx,zz-.17),(xx+.04,zz-.03),(xx,zz+.035)])
                front.prism(shape,.055,.14,TRIM,'Swag leaf drops')
    for i in range(4):
        u=x-1.53+i*1.02
        front.box(u,12.03,.12,.17,.15,.083,TRIM,'Swag bosses')
    for zz in (11.52,12.18):
        front.box(x,zz,3.94,.075,.27,.066,TRIM,'Fascia mouldings')

def add_building(builder, distant):
    repeat_only_texture(builder, 'guild-stone.png')
    front=Facade(builder,(-HALF,0),(HALF,0),'Money guild')
    street_wall(front,distant)
    for x in AXES:
        balcony(front,x,distant);festoons(front,x,distant)
    for part in builder.parts:
        if part['material']==WALL:
            part['texcoords']=[wall_uv(*v)for v in part['vertices']]
