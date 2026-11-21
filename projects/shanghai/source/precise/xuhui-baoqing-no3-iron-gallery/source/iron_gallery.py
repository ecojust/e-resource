"""The three central upper-floor bays of house 3 on the south garden front."""
from shapely.geometry import box, LineString
from shapely.ops import unary_union
from photo_architecture import Facade

MATERIALS = {
    'warm red brick': ([.409,.220,.161],.90),
    'brown red brick': ([.339,.174,.142],.92),
    'fine mortar': ([.310,.250,.226],.97),
    'cast pale stone': ([.702,.687,.629],.88),
    'weathered stone edge': ([.505,.518,.493],.90),
    'painted steel': ([.155,.181,.183],.64),
    'white window frame': ([.720,.725,.676],.78),
    'shaded window glass': ([.085,.128,.149],.38),
    'rebate shadow': ([.331,.321,.279],.96),
}
PALETTE = {key:{'color':c,'roughness':r} for key,(c,r) in MATERIALS.items()}
PITCH=2.53
BAY=1.98
TOP=3.18
SILL=.385


def bar(face,u,z,w,h,y,depth,material,name):
    face.box(u,z,w,h,depth,-y,material,name)


def brickwork(face,lod):
    for i in range(4):
        x=(i-1.5)*PITCH
        w=PITCH-BAY
        bar(face,x,TOP/2,w,TOP,.243,.486,'fine mortar','masonry pier %d'%(i+1))
        bar(face,x,TOP/2,w,TOP,-.007,.012,'warm red brick','masonry pier face')
        if not lod:
            for row in range(38):
                z=row*.084
                segs=[-w/2,w/2] if row%2==0 else [-w/2,-.045,w/2]
                if row%2==0:segs.insert(1,.112)
                for j,(lo,hi) in enumerate(zip(segs,segs[1:])):
                    surface=box(x+lo+.003,z+.002,x+hi-.003,min(z+.080,TOP))
                    if surface.area>1e-5:
                        face.prism(surface,.010,.018,'brown red brick' if (row+2*j+i)%7==0 else 'warm red brick','laid red brickwork')
        bar(face,x,3.015,w+.056,.077,-.025,.097,'weathered stone edge','pier neck')
        bar(face,x,3.102,w+.101,.09,-.044,.146,'cast pale stone','pier capital')


def geometric_guard(face,center,lod):
    reach=BAY-.055
    # The photographed rails have three continuous horizontal bars and, in the
    # middle of each bay, a small opposed-lozenge panel between vertical bars.
    for z in [SILL+.055,SILL+.218,SILL+.385,SILL+.552,SILL+.712]:
        bar(face,center,z,reach,.022 if lod else .018,.037,.034,'painted steel','straight railing courses')
    for dx in [-reach/2,-.374,.374,reach/2]:
        bar(face,center+dx,SILL+.382,.028,.696,.038,.041,'painted steel','square balusters')
    for dx in [-.201,.201]:
        bar(face,center+dx,SILL+.382,.020,.696,.038,.027,'painted steel','paired slim uprights')
    profile=[]
    points=[(-.188,.228),(-.125,.308),(0,.381),(.125,.453),(.188,.537)]
    for flip in (-1,1):
        network=[(center+flip*u,SILL+v) for u,v in points]
        profile.append(LineString(network).buffer(.012 if lod else .009,cap_style=2,join_style=2))
    face.prism(unary_union(profile),-.054,-.021,'painted steel','opposing diagonal design')
    bar(face,center,SILL+.739,reach+.044,.048,.039,.055,'painted steel','hand rail')


def sashes(face,center):
    width=BAY-.091
    z0=SILL+.816
    z1=2.805
    # A closed, white-painted sash plane is independently recessed behind the railing.
    bar(face,center,(z0+z1)/2,width,z1-z0,.303,.034,'shaded window glass','inset upper window panes')
    bar(face,center,(SILL+z0)/2,width,z0-SILL,.364,.026,'rebate shadow','rail backing behind iron')
    for z in [z0,z1]:
        bar(face,center,z,width+.04,.052,.264,.067,'white window frame','outer window frame')
    for j in range(5):
        u=center+(j-2)*width/4
        bar(face,u,(z0+z1)/2,.052 if j%2==0 else .031,z1-z0,.264,.067,'white window frame','sash uprights')
    for j in range(4):
        u=center+((j+.5)/4-.5)*width
        bar(face,u,(z0+z1)/2,.018,z1-z0-.034,.279,.029,'white window frame','inner glazing bars')
    for z in [z1-.215,z0+.52,z0+1.02]:
        bar(face,center,z,width,.018,.280,.029,'white window frame','inner glazing bars')
    bar(face,center,z0-.067,width+.070,.082,.175,.211,'cast pale stone','recessed sash sill')
    for side in (-1,1):
        bar(face,center+side*(BAY/2-.034),(z1+z0)/2,.060,z1-z0+.145,.224,.207,'rebate shadow','masonry window reveals')
    bar(face,center,(z1+TOP)/2,BAY,TOP-z1,.181,.36,'rebate shadow','recessed bay lintel')


def add_building(builder,lod=False):
    face=Facade(builder,(-4.07,0),(4.07,0),'south gallery')
    brickwork(face,lod)
    for center in [-PITCH,0,PITCH]:
        bar(face,center,.183,BAY,.366,.185,.477,'cast pale stone','pale gallery apron')
        bar(face,center,.034,BAY+.046,.068,.143,.521,'weathered stone edge','apron lower moulding')
        bar(face,center,SILL-.025,BAY+.060,.067,.151,.530,'cast pale stone','balcony stone coping')
        sashes(face,center)
        geometric_guard(face,center,lod)
    length=3*PITCH+PITCH-BAY
    for z,h,depth,y,mat in [
        (3.16,.09,.57,.20,'weathered stone edge'),(3.24,.088,.64,.182,'cast pale stone'),
        (3.315,.064,.70,.160,'weathered stone edge'),(3.39,.101,.78,.142,'cast pale stone')]:
        bar(face,0,z,length+.10,h,y,depth,mat,'continuous raised cornice')
