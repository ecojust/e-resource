"""Three small radial-brick windows on the wall adjoining the projecting porch.

Coordinates use metres. The five-arch elevation lies on Y=0; the smaller
windows increase in Y on its X=0 return. Positive X points out of that wall.
"""
from math import cos, pi, radians, sin
from shapely.geometry import Polygon, box
from shapely import set_precision
from shapely.ops import unary_union

MORTAR='Triple windows | warm lime joints'
BRICKS=('Triple windows | muted scarlet brick','Triple windows | russet brick','Triple windows | pale fired red brick')
TRIM='Triple windows | worn oxblood paint'
INNER='Triple windows | shadowed red joinery'
LIGHT='Triple windows | aged glass'
GLASS_CAP='Triple windows | shaded fanlight glass'
LEDGE='Triple windows | buff stone sill'
PALETTE={MORTAR:{'color':[.36,.285,.211],'roughness':.97},
         BRICKS[0]:{'color':[.312,.097,.057],'roughness':.91},
         BRICKS[1]:{'color':[.262,.074,.045],'roughness':.93},
         BRICKS[2]:{'color':[.377,.143,.091],'roughness':.91},
         TRIM:{'color':[.249,.044,.024],'roughness':.68},
         INNER:{'color':[.127,.040,.025],'roughness':.79},
         LIGHT:{'color':[.117,.158,.146],'roughness':.33},
         GLASS_CAP:{'color':[.095,.116,.104],'roughness':.42},
         LEDGE:{'color':[.544,.457,.341],'roughness':.90}}
# Angles of the uninterrupted fan joints, clockwise from the right spring.
# Digitised from the rectified 2018 photograph. The shaded right arc has a
# few closely spaced cracks; only lines that continue across two radii are kept.
JOINTS_DEG=(
 (0,7.4,13.8,20.2,26.4,33.4,40.1,46.6,53.8,60.6,66.9,73.4,80.5,87.3,94.2,100.2,106.4,112.2,118.7,123.4,129.4,135.5,142,148.6,155.3,162.4,168.7,174.1,180),
 (0,5.1,11.4,17.5,24.4,31.8,39,45.8,51.6,58.4,65.5,72.6,79.3,86.6,93.2,100.3,106.2,112,117.6,123.6,129.3,135.4,140.8,145.4,150.9,156.6,162,167.6,173.3,180),
 (0,2.5,8.9,15.3,22.1,28.2,34.8,40.6,46.9,53.7,60.7,67.3,73.8,79.2,85.7,91.6,97.1,101.5,106.4,111.5,116.8,122.1,127.5,133.0,138.8,145.0,151.5,157.5,168.5,174.2,180))
PITCH=1.64175
HEIGHT=2.381
RISE=.480
OUT_WIDTH=.988
OUT_RISE=.976

def settings(layout):
    row=layout.get('three_arches',{})
    return (row.get('face_x',0.),row.get('first_center_y',3.65),
            row.get('clear_width',.66),row.get('sill_z',1.55))

def rings(cx,cz,rx,rz,left=0.,right=pi,count=48):
    return [(cx+rx*cos(left+(right-left)*i/count),cz+rz*sin(left+(right-left)*i/count)) for i in range(count+1)]

def opening_contours(layout):
    """Closed Y/Z outlines of three full-through openings at the X wall plane."""
    face,first,w,sill=settings(layout); rows=[]
    for i in range(3):
        c=first+i*PITCH*w; top=sill+HEIGHT*w
        outline=[(c-w/2,sill),(c+w/2,sill),*rings(c,top,.5*w,RISE*w), (c-w/2,sill)]
        rows.append(dict(id=f'three-window-{i+1}',face_x=face,center_y=c,spring_z=top,
                         clear_width=w,outline_yz=outline))
    return rows

def arch_mask(layout):
    """Outer scalloped border in Y/Z. Behind it the masonry wall may remain solid."""
    _,first,w,sill=settings(layout); spring=sill+HEIGHT*w
    return unary_union([Polygon(rings(first+i*PITCH*w,spring,OUT_WIDTH*w,OUT_RISE*w)) for i in range(3)])

def sectors(y,z,r1,r2,h1,h2,a,b,n):
    return Polygon(rings(y,z,r2,h2,a,b,n)+list(reversed(rings(y,z,r1,h1,a,b,n))))

def add_three_arches(builder,lod=False,layout=None):
    if layout is None: layout={}
    face,first,w,sill=settings(layout)
    for name,mat in PALETTE.items(): builder.palette.setdefault(name,mat)
    spring=sill+HEIGHT*w
    def put(poly,rear,front,mat,label):
        if poly.is_empty or poly.area<=1e-9:return
        builder.prism(set_precision(poly,1e-7),rear*w,front*w,
                      lambda yy,zz,d:(face+d,yy,zz),mat,label)
    for i,row in enumerate(opening_contours(layout)):
        center=row['center_y']; label=f'Three windows | {i+1} '
        left=center-(PITCH*.5 if i else OUT_WIDTH+.02)*w
        right=center+(PITCH*.5 if i<2 else OUT_WIDTH+.02)*w
        clipped=box(left,sill-.1*w,right,spring+1.10*w)
        # A shallow chevron occurs where two neighbouring fans meet.
        # Each side occupies exactly half of that pier, including its mortar.
        radius=.50; rise=RISE
        area=sectors(center,spring,radius*w,OUT_WIDTH*w,rise*w,OUT_RISE*w,0,pi,72)
        put(area.intersection(clipped),-.150,.002,MORTAR,label+'arched mortar bed')
        angles=JOINTS_DEG[i]
        for j,(a0,a1) in enumerate(zip(angles,angles[1:])):
            a=radians(a0+(.36 if j else 0.)); b=radians(a1-(.36 if j+2<len(angles) else 0.))
            # The photograph shows alternating continuous lengths and one
            # transverse joint. A fully separate concentric row is absent.
            bands=[(.50,OUT_WIDTH,rise,OUT_RISE)] if j%2==0 else [(.50,.745,rise,.721),(.754,OUT_WIDTH,.730,OUT_RISE)]
            for n,(ri,ro,hi,ho) in enumerate(bands):
                geo=sectors(center,spring,ri*w,ro*w,hi*w,ho*w,a,b,2 if lod else 4)
                mat=BRICKS[(7*j+3*n+i)%len(BRICKS)] if not lod else BRICKS[0]
                put(geo.intersection(clipped),-.148,.011,mat,label+'radial brick')
        # Reveal and fanlight sit behind the brick face.
        leftj=center-.497*w;rightj=center+.497*w
        transom=sill+2.02*w; mid=sill+.4563*HEIGHT*w
        fan_outer=Polygon(rings(center,spring,.497*w,.476*w,count=42)).union(
            box(leftj,transom+.01*w,rightj,spring+.001*w))
        fan_inner=Polygon(rings(center,spring,.395*w,.359*w,count=42)).union(
            box(center-.395*w,transom+.089*w,center+.395*w,spring+.001*w))
        put(fan_outer.difference(fan_inner),-.231,-.155,INNER,label+'arched frame')
        put(fan_inner,-.227,-.214,GLASS_CAP,label+'fanlight')
        # One horizontal glazing bar separates the two panes of each sash.
        gl,gr=[(-.310,.252),(-.296,.253),(-.265,.274)][i]
        frame=box(leftj,sill,rightj,transom+.025*w).difference(unary_union([
            box(center+gl*w,sill+.145*w,center+gr*w,mid-.025*w),
            box(center+gl*w,mid+.025*w,center+gr*w,transom-.103*w)]))
        put(frame,-.120,-.034,TRIM,label+'sash frame and glazing bar')
        for bot,top in [(sill+.14*w,mid-.021*w),(mid+.021*w,transom-.10*w)]:
            put(box(center+(gl-.006)*w,bot,center+(gr+.006)*w,top),-.107,-.089,LIGHT,label+'glazing')
        put(box(leftj,transom-.04*w,rightj,transom+.049*w),-.135,-.022,TRIM,label+'transom')
    left=first-.60*w;right=first+(2*PITCH+.60)*w
    put(box(left,sill-.116*w,right,sill-.017*w),-.13,.165,LEDGE,'Three windows | continuous sill')
    put(box(left+.037*w,sill-.171*w,right-.037*w,sill-.115*w),-.11,.130,LEDGE,'Three windows | sill lower lip')
