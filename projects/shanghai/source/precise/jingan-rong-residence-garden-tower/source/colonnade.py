"""One whole garden bay of the two-level veranda beside the tower."""
from math import cos, pi, sin
from shapely.geometry import box
from photo_architecture import Facade, opening
from garden_tower import WALL,TRIM,ACCENT,FRAME,GLASS,IRON,FLOOR,slab


def column(builder, x, y, bottom, top, lod, storey):
    base_radius=.255 if storey=='lower' else .215
    radius=base_radius
    tag=storey+' veranda'
    def block(z,wide,h,stone,name):
        builder.box((x,y,z),(wide,wide,h),stone,label=tag+'/'+name)
    block(bottom+.083,radius*2.75,.164,TRIM,'square plinth')
    mould=[(bottom+.16,1.23*radius),(bottom+.195,1.29*radius),(bottom+.259,1.27*radius),
           (bottom+.304,1.08*radius),(bottom+.350,1.12*radius),(bottom+.403,radius)]
    n=16 if lod else 30
    builder.lathe((x,y),mould,TRIM,n,tag+'/turned base')
    builder.lathe((x,y),[(bottom+.4,radius),(bottom+.82,radius*1.015),(top-.48,radius*.84)],TRIM,n,tag+'/tapered shaft')
    builder.lathe((x,y),[(top-.50,radius*.86),(top-.443,radius*1.01),(top-.388,radius*.97),
                         (top-.298,radius*1.19),(top-.229,radius*1.27)],ACCENT,n,tag+'/capital neck')
    block(top-.125,radius*2.88,.251,TRIM,'square abacus')
    for sign in (-1,1):
        cx=x+sign*(radius*1.04)
        path=[]
        for j in range(15 if lod else 32):
            t=j/(14 if lod else 31);a=t*pi*1.9; r=.074*(1-.65*t)
            path.append((cx+sign*r*cos(a),y-radius*1.22,top-.253+r*sin(a)))
        builder.tube(path,.025,TRIM,6 if lod else 9,tag+'/paired volutes')


def veranda(builder, dims, east, shoulder, lod):
    roof=dims['fitted_elevations_m'];belt=dims['assumed_first_belt_m'];upper=roof['upper']
    # The visible tower return projects forward of the veranda. The rear enclosure and
    # two deep openings are read through the free-standing columns from the garden.
    left=east+.12;span=3.54;right=left+span;front=shoulder+.38;rear=front+2.42
    width=span+.62;mid=(left+right)/2
    outline=box(left-.32,front-.30,right+.32,rear+.20)
    slab(builder,outline,.00,.18,FLOOR,'Veranda / ground walk')
    for x in (left,right):
        column(builder,x,front,.18,belt-.36,lod,'lower')
        column(builder,x,front,belt+.055,upper-.31,lod,'upper')
    for z,h,extension,stone,label in [
        (belt-.30,.16,.035,ACCENT,'lower architrave'),
        (belt-.165,.115,.104,TRIM,'lower fascia'),
        (belt-.066,.105,.146,TRIM,'upper balcony edge'),
        (upper-.36,.185,.06,ACCENT,'upper architrave'),
        (upper-.17,.165,.106,TRIM,'upper bed'),
        (upper-.058,.098,.16,TRIM,'balcony roof cornice')]:
        builder.box((mid,front,z),(width+extension*2,.51+extension,h),stone,label='Veranda / '+label)
    for z,name in [(belt,'balcony'),(upper,'roof terrace')]:
        slab(builder,outline,z-.085,z+.054,FLOOR,'Veranda / '+name+' slab')
    f=Facade(builder,(left-.3,rear),(right+.3,rear),'Recessed garden wall')
    doors=[opening(0,.28,1.38,belt-.85),opening(0,belt+.16,1.33,upper-belt-.76)]
    f.wall(0,upper+.05,doors,.29,WALL)
    for i,door in enumerate(doors):
        f.prism(door.buffer(-.008),-.27,-.234,GLASS,'glazed doors')
        inside=door.buffer(-.075,join_style=2)
        a,z,b,t=door.bounds
        panes=inside.difference(box(-.023,z,.023,t)).difference(box(a,t-.47,b,t-.40))
        f.prism(door.difference(panes),-.205,-.154,FRAME,'dark door frames')
        f.prism(door.buffer(.096,join_style=2).difference(door),.008,.086,TRIM,'stone door surrounds')
    rail=Facade(builder,(left+.16,front+.062),(right-.16,front+.062),'Upper veranda ironwork')
    for h in (.17,.77,.84):rail.box(0,belt+h,rail.length,.035,.039,.013,IRON,'iron horizontal rails')
    for k in range(13):
        u=(k+.5)*rail.length/13-rail.length/2
        rail.box(u,belt+.485,.026,.651,.026,.024,IRON,'iron balusters')
    for i in range(5):
        u=(i+.5)*rail.length/5-rail.length/2
        poly=[rail.point(u+.112*cos(j*pi/10),belt+.48+.224*sin(j*pi/10),.035)for j in range(21)]
        rail.builder.tube(poly,.013,IRON,5 if lod else 7,'Upper veranda ironwork/oval ornaments')
    for x in (left-.06,right+.06):
        builder.box((x,front+.015,upper+.33),(.35,.38,.59),TRIM,label='Roof terrace / parapet piers')
        builder.box((x,front+.015,upper+.665),(.436,.46,.10),TRIM,label='Roof terrace / pier caps')
    for z,h,depth in [(upper+.125,.14,.39),(upper+.615,.125,.43),(upper+.71,.063,.47)]:
        builder.box((mid,front+.015,z),(span+.44,depth,h),TRIM,label='Roof terrace / stone balustrade rails')
    for k in range(1,11):
        x=left+k*span/11
        builder.lathe((x,front+.015),[(upper+.18,.082),(upper+.22,.080),(upper+.257,.055),
                      (upper+.315,.047),(upper+.391,.087),(upper+.435,.085),(upper+.495,.054),(upper+.57,.066)],
                      TRIM,9 if lod else 16,'Roof terrace / turned balusters')
