"""The three garden-facing facets, recessed sash windows and their festoons."""
from math import cos, pi, sin
from shapely.geometry import Polygon, box
from photo_architecture import Facade, opening

WALL = 'Warm ivory ashlar'
TRIM = 'carved pale stone'
ACCENT = 'Sand-coloured moulding'
FRAME = 'Dark painted sash'
GLASS = 'Grey-green glazing'
SHADOW = 'Stone joint'
IRON = 'Painted iron'
FLOOR = 'Veranda stone floor'
ROOF = 'Weathered red metal panels'
RIB = 'Aged copper seams'
OCHRE = 'Dark copper finial'


def slab(builder, outline, bottom, top, material, name):
    builder.prism(outline,bottom,top,lambda x,y,z:(x,y,z),material,name)


def surround(face, hole, width, depth, name):
    edge = hole.buffer(width,join_style=2).difference(hole)
    face.prism(edge,-.015,depth,TRIM,name)


def garland(f, z, width, lod):
    """Cabled swags below the middle sash. Leaves and two tails turn with the sloping faces."""
    length=width*.46
    def point(q):return f.point(q*length,z-.31*(1-q*q),.117)
    count=10 if lod else 26
    f.builder.tube([point(-1+2*i/count)for i in range(count+1)],.035,ACCENT,6 if lod else 9,f.label+'/festoon cord')
    # The low centre hangs beneath overlapping berry clusters. Alternate carved
    # branches catch light on different sides of the braided central stem.
    leaves=8 if lod else 13
    for index in range(leaves):
        q=-.89+1.78*index/(leaves-1)
        x=q*length; center=z-.31*(1-q*q)
        for side in (-1,1):
            lean=side*.061-.043*q
            tip=(x+lean,center-.093)
            leaf=Polygon([(x-.022,center+.018),(x+.43*lean-.031,center-.042),
                          tip,(x+.48*lean+.031,center-.039),(x+.022,center+.022)])
            if not leaf.is_valid:leaf=leaf.buffer(0)
            f.prism(leaf,.119,.151,TRIM,'overlapping festoon leaves')
        if not lod or index%2==0:
            bead=f.point(x,center-.017,.157)
            vertices=[bead,f.point(x,center-.017,.195)]
            for k in range(8):
                vertices.append(f.point(x+.032*cos(k*pi/4),center-.017+.031*sin(k*pi/4),.166))
            faces=[(1,2+k,2+(k+1)%8)for k in range(8)]+[(0,2+(k+1)%8,2+k)for k in range(8)]
            f.builder.add(vertices,faces,ACCENT,f.label+'/festoon berry clusters')
    for sign in (-1,1):
        x=sign*length
        for shift in (-.034,.034):
            f.line((x+shift,z-.02,.13),(x+shift+sign*.055,z-.23,.138),.020,ACCENT,6,'pendant ribbons')
        f.builder.tube([f.point(x+.072*cos(i*pi/8),z+.070*sin(i*pi/8),.13) for i in range(17)],.022,TRIM,6,f.label+'/festoon rosettes')


def sash(f, shape, division, arched, label):
    x,z,r,t=shape.bounds;w=r-x;h=t-z
    f.prism(shape.buffer(-.008),-.328,-.300,GLASS,label+' glass')
    inside=shape.buffer(-.067,join_style=2)
    panes=inside
    bars=[box(-.023,z,.023,t)]
    for portion in division:
        y=z+h*portion;bars.append(box(x,y-.028,r,y+.028))
    for bar in bars:panes=panes.difference(bar)
    f.prism(shape.difference(panes),-.264,-.165,FRAME,label+' sash')
    surround(f,shape,.116 if arched else .107,.087,label+' stone architrave')
    f.box(0,z-.052,w+.30,.105,.29,.046,TRIM,label+' sill')
    if arched:
        crown=Polygon([(-.108,t-.095),(.108,t-.095),(.145,t+.168),(-.145,t+.168)])
        f.prism(crown,.088,.176,TRIM,label+' keystone')


def tower(builder, dims, lod):
    face_width=dims['central_face_width_m'];a=face_width/2; dx,dy=dims['return_x_y_m']
    roof=dims['fitted_elevations_m']; belt=dims['assumed_first_belt_m']
    upper=roof['upper']; cornice=roof['cornice']; top=roof['parapet']
    back=dy+1.82
    ring=[(-a,0),(a,0),(a+dx,dy),(a+dx,back),(-a-dx,back),(-a-dx,dy)]
    outline=Polygon(ring)
    names=['Garden centre','Garden east chamfer','East return','Main-house junction','West return','Street west chamfer']
    for i,name in enumerate(names):
        f=Facade(builder,ring[i],ring[(i+1)%len(ring)],name)
        windows=[]
        if i in (0,1,5):
            ground=opening(0,.78,1.12,belt-1.22,.49,12 if lod else 27)
            middle=opening(0,belt+1.08,1.12,upper-belt-1.92)
            attic=opening(0,upper+1.07,1.06,cornice-upper-1.94)
            windows=[ground,middle,attic]
        f.wall(.07,cornice,windows,.30,WALL)
        for j,hole in enumerate(windows):
            sash(f,hole,(.36,.66,.79)if j==0 else (.43,.78),j==0,'lower arched window'if j==0 else('garden sash'if j==1 else'attic sash'))
        if windows:
            garland(f,middle.bounds[1]-.19,1.49,lod)
            # Locate shallow joints around each opening, continuing across each visible facet.
            wall=box(-f.length/2+.014,.14,f.length/2-.014,cornice-.10)
            for hole in windows:wall=wall.difference(hole.buffer(.14,join_style=2))
            for index in range(1,int(cornice/.49)):
                level=index*.49
                horizontal=wall.intersection(box(-f.length,level-.007,f.length,level+.007))
                if not horizontal.is_empty and horizontal.area>.0003:f.prism(horizontal,.0005,.005,SHADOW,'shallow horizontal ashlar joints')
    for z,h,d,mat,label in [
        (.08,.16,.08,ACCENT,'garden plinth'),(belt-.33,.10,.055,ACCENT,'belt lower fillet'),
        (belt-.19,.20,.105,TRIM,'belt bed'),(belt-.045,.12,.18,TRIM,'belt projecting lip'),
        (upper-.27,.15,.085,ACCENT,'upper bed'),(upper-.11,.16,.163,TRIM,'upper cornice'),
        (upper+.16,.095,.062,TRIM,'attic sill line'),(cornice-.34,.18,.106,ACCENT,'roof frieze'),
        (cornice-.16,.18,.185,TRIM,'roof soffit'),(cornice-.025,.11,.235,TRIM,'roof cornice cap')]:
        band=outline.buffer(d,join_style=2).difference(outline.buffer(-.14,join_style=2))
        slab(builder,band,z-h/2,z+h/2,mat,label)
    for i in (0,1,5):
        f=Facade(builder,ring[i],ring[(i+1)%len(ring)],names[i])
        for z in (upper-.28,cornice-.38):
            num=round(f.length/(.30 if lod else .18))
            for k in range(num):
                f.box((k+.5)*f.length/num-f.length/2,z,.073,.095,.11,.044,TRIM,'cornice dentils')
    slab(builder,outline.buffer(-.03,join_style=2),cornice,top-.11,WALL,'attic parapet')
    slab(builder,outline.buffer(.035,join_style=2),top-.12,top,TRIM,'attic raised coping')
    slab(builder,outline,.01,.09,FLOOR,'tower ground slab')
    return a+dx,dy,back
