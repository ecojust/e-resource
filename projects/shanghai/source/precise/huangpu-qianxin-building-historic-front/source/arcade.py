"""Model the six large arches visible in the dated street photograph."""
from math import cos, pi, sin
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade, opening

CREAM = 'warm stucco'
STONE = 'cream dressed stone'
SHADOW = 'recessed mortar in arch'
WOOD = 'oxidised red window joinery'
GLASS = 'muted blue grey glass'
BRICKS = ('terracotta brick 1', 'terracotta brick 2', 'terracotta brick 3')
PALETTE = {
    CREAM: {'color':[.835,.774,.665], 'roughness':.91},
    STONE: {'color':[.711,.635,.539], 'roughness':.84},
    SHADOW: {'color':[.442,.328,.265], 'roughness':.9},
    WOOD: {'color':[.391,.176,.120], 'roughness':.65},
    GLASS: {'color':[.35,.43,.455], 'roughness':.33, 'metallic':.11},
    BRICKS[0]: {'color':[.643,.351,.229], 'roughness':.91},
    BRICKS[1]: {'color':[.682,.396,.264], 'roughness':.89},
    BRICKS[2]: {'color':[.606,.321,.226], 'roughness':.92},
}

CENTRES = (-3.18, 0, 3.18)
SILLS = (.63, 4.29)
SPRINGS = (2.47, 6.16)
RADIUS = 1.26
TOP = 7.99


def band(x,z,inner,outer,a,b,segments):
    angles = [a+(b-a)*i/segments for i in range(segments+1)]
    outer_points = [(x+outer*cos(t),z+outer*sin(t)) for t in angles]
    inner_points = [(x+inner*cos(t),z+inner*sin(t)) for t in reversed(angles)]
    return Polygon(outer_points+inner_points)


def arch_bricks(face,x,z,distant,label):
    count = 23 if distant else 47
    arc = pi/count
    # The front ring returns around the soffit. Mortar remains visible in each joint.
    face.prism(band(x,z,RADIUS-.003,RADIUS+.189,0,pi,count),
               -.684,.020,SHADOW,label+'/mortar bed')
    for i in range(count):
        shape = band(x,z,RADIUS-.009,RADIUS+.186,i*arc+.0025,(i+1)*arc-.0025,2)
        face.prism(shape,-.675,.036,BRICKS[(5*i+i//5)%3],label+'/radial bricks')
    for side in (-1,1):
        edge=x+side*RADIUS
        for j,(width,h,protrusion) in enumerate(((.29,.068,.095),(.36,.057,.14),(.44,.064,.18))):
            mid=edge+side*.078
            face.box(mid,z-.163+j*.060,width,h,.68+protrusion,
                     (protrusion-.68)/2,STONE,label+'/stepped impost')
        # Paired curved corbels are visible below the coffered capital bands.
        foot=edge+side*.092
        boss=[(foot-side*.145,z-.110),(foot+side*.115,z-.110),
              (foot+side*.105,z-.228),(foot+side*.040,z-.305),
              (foot-side*.071,z-.260)]
        face.prism(Polygon(boss),-.01,.085,STONE,label+'/impost corbels')
        for k in range(2):
            centre=foot+side*(k*.09-.045)
            path=[face.point(centre+.038*cos(t*pi/11),
                             z-.173+.026*sin(t*pi/11),.089) for t in range(12)]
            face.builder.tube(path,.011,STONE,5 if distant else 8,label+'/impost moulding')


def glazing(face,x,sill,spring,fan,distant,label):
    r=RADIUS-.045
    # The glass and its timber casement are at the back of the deep brick reveal.
    aperture=opening(x,sill,r*2,spring-sill+r,r,24 if distant else 48)
    inset=aperture.buffer(-.071,join_style='mitre')
    frame=[aperture.difference(inset),box(x-r,spring-.043,x+r,spring+.034)]
    for offset in (-r/3,r/3):
        frame.append(box(x+offset-.029,sill,x+offset+.029,spring))
        if not fan:
            frame.append(box(x+offset-.023,spring,x+offset+.023,spring+r))
    if fan:
        from shapely.geometry import LineString
        for i in range(1,7):
            t=i*pi/7
            frame.append(LineString([(x,spring),(x+r*cos(t),spring+r*sin(t))])
                         .buffer(.015 if distant else .012,cap_style='flat'))
    # A small concealed lap at the outer frame prevents back-light through its perimeter.
    face.prism(aperture.buffer(.080),-.744,-.724,GLASS,label+'/glass')
    face.prism(unary_union(frame).intersection(aperture),-.716,-.655,WOOD,label+'/casement')


def balustrade(face,x,sill,distant,label):
    w=2*RADIUS
    face.box(x,sill+.056,w+.13,.115,.34,-.014,STONE,label+'/bottom rail')
    face.box(x,sill+.563,w+.14,.105,.36,.004,STONE,label+'/handrail')
    face.box(x,sill+.624,w+.23,.058,.40,.010,STONE,label+'/handrail cap')
    for side in (-1,1):
        face.box(x+side*(RADIUS-.027),sill+.300,.13,.50,.29,-.012,
                 STONE,label+'/rail end')
    # Eleven broad-faced balusters can be counted in the unobscured right-hand bay.
    profile=[(.103,.065),(.134,.065),(.159,.052),(.206,.049),
             (.265,.067),(.337,.068),(.372,.055),(.424,.049),
             (.475,.061),(.495,.070),(.526,.070)]
    from shapely.geometry import Point
    for i in range(11):
        x0=x-1.12+i*.224
        silhouette=[(x0-width,sill+height) for height,width in profile]
        silhouette.extend((x0+width,sill+height) for height,width in reversed(profile))
        face.prism(Polygon(silhouette),-.080,.081,STONE,label+'/carved stone balusters')
        centre=Point(x0,sill+.285)
        surround=centre.buffer(.042,quad_segs=4 if distant else 10)
        hollow=centre.buffer(.027,quad_segs=4 if distant else 10)
        face.prism(surround.difference(hollow),.079,.088,STONE,label+'/pier medallions')
    face.box(x,sill+.568,w+.17,.030,.386,.008,STONE,label+'/coping bead')



def add_building(builder,distant):
    face=Facade(builder,(-4.84,0),(4.84,0),'Street arcade')
    holes=[]
    for sill,spring in zip(SILLS,SPRINGS):
        for x in CENTRES:
            holes.append(opening(x,sill,RADIUS*2,spring-sill+RADIUS,
                                 RADIUS,30 if distant else 60))
    face.wall(.13,TOP,holes,.677,CREAM)
    for k,(sill,spring) in enumerate(zip(SILLS,SPRINGS)):
        for j,x in enumerate(CENTRES):
            label=('Lower' if k==0 else 'Upper')+' bay '+str(j+1)
            arch_bricks(face,x,spring,distant,label)
            glazing(face,x,sill,spring,(k,j) in ((0,0),(1,2)),distant,label)
            if k==0:
                balustrade(face,x,sill,distant,label)
            else:
                face.box(x,sill+.025,RADIUS*2+.15,.115,.31,.05,STONE,label+'/sill')
    # The continuous ledge below the lower arcade has a projecting stepped edge
    # and a row of small, rounded ornaments visible along its underside.
    size=face.length
    for z,h,depth in ((.09,.18,.30),(.227,.10,.45),(.414,.283,.398),(.60,.115,.54)):
        face.box(0,z,size,h,.69+depth,(depth-.69)/2,STONE,'base moulding')
    for i in range(44):
        u=-4.685+i*.218
        builder.lathe((u,-.387),[(.31,.046),(.339,.078),(.391,.088),
                                  (.450,.056),(.467,.026)],STONE,
                      5 if distant else 9,'Short cornice / rounded relief')
    # Both floors use the same three arches, separated by a plain plaster spandrel.
    for z,h,d in ((4.173,.068,.075),(4.249,.082,.128)):
        face.box(0,z,size,h,.62+d,(d-.62)/2,STONE,'upper continuous sill')
