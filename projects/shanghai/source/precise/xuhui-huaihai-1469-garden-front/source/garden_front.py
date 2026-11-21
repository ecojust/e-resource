"""Historic garden-facing middle bays. All dimensions are photographic estimates in metres."""
from shapely.geometry import box
from shapely.ops import unary_union
from photo_architecture import Facade

WALL='pale warm masonry'
TRIM='cream mouldings and columns'
SOFFIT='warm shadowed soffit'
CAP='slate grey cornice edge'
GLASS='muted blue green glazing'
SASH='deep green painted glazing bars'
DOOR='dark red brown timber'
STONE='grey tan stair stone'
METAL='aged dark bronze'
PALETTE={
    WALL:dict(color=[.781,.763,.685],roughness=.93),TRIM:dict(color=[.856,.835,.754],roughness=.81),
    SOFFIT:dict(color=[.649,.635,.546],roughness=.92),CAP:dict(color=[.415,.435,.407],roughness=.79),
    GLASS:dict(color=[.300,.392,.382],metallic=.16,roughness=.32),SASH:dict(color=[.201,.228,.192],roughness=.68),
    DOOR:dict(color=[.285,.195,.145],roughness=.65),STONE:dict(color=[.623,.609,.544],roughness=.88),
    METAL:dict(color=[.370,.333,.228],metallic=.46,roughness=.58),
}
HALF=8.28
LOW=(-.13,.04)
WINDOWS=[(-5.52,2.10,4.18,2.21),(5.52,2.10,4.18,2.21),
         (-5.52,5.68,4.26,1.86),(0,5.68,4.26,1.86),(5.52,5.68,4.26,1.86)]


def ribbon(f,z,h,projection,mat,label,back=-.32):
    f.prism(box(-HALF,z,HALF,z+h),back,projection,mat,label)


def light(f,u,z,w,h,upper,low):
    x0,x1=u-w/2,u+w/2
    z0,z1=z-h/2,z+h/2
    outer=box(x0,z0,x1,z1)
    inner=box(x0+.075,z0+.080,x1-.075,z1-.075)
    f.prism(inner,-.147,-.118,GLASS,'separate recessed glazing')
    f.prism(outer.difference(inner),-.144,-.045,SASH,'perimeter sash')
    # Upper bands have a high transom. The lower lights are more evenly divided.
    rail=z0+h*(.71 if upper else .60)
    for frac in [.25,.50,.75]:
        x=x0+w*frac
        f.prism(box(x-.020,z0+.03,x+.020,z1-.03),-.121,-.064,SASH,'main vertical mullions')
    f.prism(box(x0+.04,rail-.025,x1-.04,rail+.025),-.073,-.045,SASH,'horizontal transom')
    if not low:
        for frac in ([.125,.375,.625,.875] if not upper else [.125,.875]):
            x=x0+w*frac
            f.prism(box(x-.009,z0+.085,x+.009,rail-.027),-.118,-.096,SASH,'fine sash divisions')
    f.prism(box(x0-.076,z0-.095,x1+.076,z0-.025),-.090,.115,TRIM,'projecting window sill')
    f.prism(box(x0-.053,z1+.008,x1+.053,z1+.073),-.035,.094,TRIM,'window head moulding')


def portico(b,low):
    for x in (-3.08,3.08):
        for y in (-1.79,-.38):
            # The two column lines align with the paired supports seen from the garden.
            b.box((x,y,.677),(.483,.483,.105),STONE,label='portico square feet')
            rings=[(.729,.218),(.771,.219),(.803,.189),(.842,.166),(3.523,.151),
                   (3.570,.168),(3.602,.188),(3.631,.203),(3.681,.211)]
            b.lathe((x,y),rings,TRIM,segments=14 if low else 32,label='porch slender round columns')
            b.box((x,y,3.716),(.486,.455,.071),TRIM,label='portico abaci')
    for z,depth,h,mat,name in [(3.798,2.08,.110,SOFFIT,'level porch soffit'),(3.958,2.17,.234,TRIM,'broad porch fascia'),
                               (4.096,2.24,.063,CAP,'porch drip and stone cap')]:
        b.box((0,-depth/2+.055,z),(6.75,depth,h),mat,label=name)
    b.box((0,-.83,.299),(6.81,1.90,.598),STONE,label='raised porch platform')
    b.box((0,-.83,.615),(6.84,1.95,.033),TRIM,label='porch stone nosing')
    # Building steps terminate with the documented porch. Garden routes are outside the elevation.
    for i in range(6):
        top=.104*(i+1);ay=-3.575+i*.300
        b.box((0,ay+.15,top/2),(3.70,.306,top),STONE,label='six shallow central treads')
        if not low:b.box((0,ay+.02,top-.012),(3.72,.063,.024),TRIM,label='fine stair nosings')
    for x in (-2.16,2.16):
        b.box((x,-1.79,.363),(.57,.71,.726),STONE,label='low stair-side stone plinths')
        b.box((x,-1.79,.751),(.62,.75,.064),TRIM,label='plinth capstones')


def make_front(b,low=False):
    f=Facade(b,(-HALF,0),(HALF,0),'garden-front middle bays')
    holes=[box(u-w/2,z-h/2,u+w/2,z+h/2) for u,z,w,h in WINDOWS]
    porch=box(-2.68,.598,2.68,3.54)
    f.prism(box(-HALF,0,HALF,6.98).difference(unary_union([*holes,porch])),-.38,0,WALL,'two-storey wall cut across three bays')
    for u,z,w,h in WINDOWS:light(f,u,z,w,h,z>4,low)
    for z,h,d,mat,name in [(.46,.12,.08,STONE,'continuous plinth course'),(3.72,.105,.115,TRIM,'lower edge of belt'),
                            (3.845,.162,.171,WALL,'continuous masonry belt'),(4.03,.071,.205,CAP,'belt drip'),
                            (4.29,.084,.110,TRIM,'upper sill course'),(6.67,.130,.116,TRIM,'upper frieze moulding'),
                            (6.82,.128,.166,TRIM,'cornice fascia'),(6.96,.088,.212,CAP,'visible top edge of cornice')]:
        if z<1:
            for left,right in [(-HALF,-2.70),(2.70,HALF)]:
                f.prism(box(left,z,right,z+h),-.067,d,mat,name)
        else:ribbon(f,z,h,d,mat,name)
    for x in [-2.76,2.76]:
        for offset in [-.140,.140]:
            f.prism(box(x+offset-.101,4.25,x+offset+.101,6.655),-.04,.113,TRIM,'paired shallow upper pilaster strips')
            f.prism(box(x+offset-.125,4.24,x+offset+.125,4.33),-.02,.152,TRIM,'individual square pilaster bases')
    for x in [-7.98,-3.06,3.06,7.98]:
        f.prism(box(x-.103,.58,x+.103,3.69),-.035,.101,TRIM,'lower inter-window pilasters')
    for u in [-5.52,0,5.52]:
        for i in range(23 if not low else 12):
            spacing=4.2/(23 if not low else 12)
            x=u-2.1+(i+.5)*spacing
            f.prism(box(x-.016,4.117,x+.016,4.242),-.015,.054,SOFFIT,'short recessed frieze divisions')
    # The archival dark backdrop is shallow and closed at the model section.
    f.prism(porch,-.80,-.74,DOOR,'dark recessed porch wall')
    for u in [-1.56,1.56]:
        f.prism(box(u-.293,1.105,u+.293,2.666),-.744,-.719,SASH,'recessed joinery within porch')
        f.prism(box(u-.255,1.186,u+.255,2.592),-.721,-.708,GLASS,'small glazed leaves')
    portico(b,low)
