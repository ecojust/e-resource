"""The north hall and its two inward-facing galleries, measured in a court-oriented frame."""
from math import ceil
from pathlib import Path
from shapely.geometry import box
from shapely.ops import unary_union
from photo_architecture import Facade
from sign_lettering import add_facade_lettering

WOOD = 'dark cinnabar timber'
PANEL = 'red lacquer lattice'
PLASTER = 'limewash'
BASE = 'dressed grey stone'
ROOF = 'charcoal clay pantiles'
BRONZE = 'aged bronze hardware'
GLASS = 'recessed dark windowpane'
PAINT = 'gilt hall inscription'
STEEL = 'later steel roof framing'
CLEAR = 'later translucent courtyard glazing'
PALETTE = {
    WOOD: dict(color=[.28,.071,.045],roughness=.68),
    PANEL: dict(color=[.42,.085,.049],roughness=.65),
    PLASTER: dict(color=[.737,.701,.635],roughness=.92),
    BASE: dict(color=[.386,.379,.349],roughness=.89),
    ROOF: dict(color=[.180,.186,.169],roughness=.89),
    BRONZE: dict(color=[.37,.238,.118],metallic=.6,roughness=.47),
    GLASS: dict(color=[.140,.167,.157],metallic=.1,roughness=.40),
    PAINT: dict(color=[.806,.531,.196],metallic=.44,roughness=.48),
    STEEL: dict(color=[.231,.245,.222],metallic=.5,roughness=.58),
    CLEAR: dict(color=[.75,.733,.583],metallic=.025,roughness=.21,alpha=.20),
}
FONT=Path(__file__).with_name('fonts')/'CixiuHallBoard.otf'
COURT_HALF=4.55
SOUTH=-8.80
NORTH=6.05
EAVES=6.34
LOFT=3.18


def sheet(b, corners, drop, material, label):
    """Make a closed inclined slab, with counterclockwise plan vertices."""
    lower=[(x,y,z-drop) for x,y,z in corners]
    b.add([*lower,*corners],[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],material,label)


def timber_frame(face, u, z, width, height, name, lower=False, low=False):
    bounds=box(u-width/2,z,u+width/2,z+height)
    face.prism(bounds,-.125,-.095,GLASS,name+' recessed glazing')
    inside=bounds.buffer(-.075,join_style='mitre')
    col=4 if low else 6
    bot=z+.62 if lower else z+.10
    bars=[box(u-width/2+i*width/col-.024,bot,u-width/2+i*width/col+.024,z+height-.04)for i in range(1,col)]
    bars.extend(box(u-width/2,h-.027,u+width/2,h+.027)for h in [bot,z+height*.70,z+height*.84])
    if lower:bars.append(box(u-width/2,z,u+width/2,bot))
    face.prism(bounds.difference(inside.difference(unary_union(bars))),-.088,.018,PANEL,name+' timber lattice')


def partition(face,bays,low,main=False):
    """Separate panelled doors and recessed glazing fill the photographic wall, behind the gallery."""
    step=face.length/bays;holes=[]
    for i in range(bays):
        u=step*(i+.5)-face.length/2
        if main:
            for x in [u-step*.24,u+step*.24]:
                w=step*.44
                holes.append(box(x-w/2,.18,x+w/2,2.45))
                timber_frame(face,x,.18,w,2.27,'six hall door leaves',lower=True,low=low)
            holes.append(box(u-step*.46,LOFT+.36,u+step*.46,5.80))
            timber_frame(face,u,LOFT+.36,step*.92,5.80-LOFT-.36,'upper casement',low=low)
        else:
            for z,h in [(.78,1.58),(LOFT+.40,1.91)]:
                w=step*.74; holes.append(box(u-w/2,z,u+w/2,z+h))
                timber_frame(face,u,z,w,h,'gallery room light',low=low)
        if not low:
            for dx in [-.28,.28]:
                face.box(u+dx,2.72,.38,.15,.03,.02,PANEL,'upper wooden panel')
    face.prism(box(-face.length/2,.08,face.length/2,EAVES-.08).difference(unary_union(holes)),-.22,-.12,WOOD if main else PLASTER,'wall between true window openings')
    face.box(0,.11,face.length,.19,.28,-.15,BASE,'stone plinth')


def returned_fret(face,u,z,w,low):
    """Stepped open fret below the eave, simplified at distance."""
    size=.13 if low else .10
    for sign in [-1,1]:
        start=u+sign*(w/2-.19);end=u+sign*(w/2-.84)
        path=[(start,z,0),(start,z-.42,0),(end,z-.42,0),(end,z-.23,0)]
        if not low:path.extend([(end+sign*.23,z-.23,0),(end+sign*.23,z-.34,0)])
        face.builder.tube([face.point(*point) for point in path], size*.49,WOOD,4,face.label+'/stepped fret brackets')


def gallery(face,bays,low,hall=False):
    """Build clear air between posts, genuine open vase balusters and the two-storey side gallery."""
    step=face.length/bays
    for i in range(bays+1):
        u=-face.length/2+i*step
        pt=face.point(u,0,0)[:2]
        face.builder.lathe(pt,[(.07,.146),(.18,.159),(.22,.128),(.32,.115)],BASE,8 if low else 14,face.label+'/stone post bases')
        face.builder.lathe(pt,[(.27,.115),(LOFT-.14,.110),(EAVES-.17,.099)],WOOD,8 if low else 14,face.label+'/circular red columns')
        face.box(u,EAVES-.25,.31,.32,.27,-.035,WOOD,'post capitals')
    for z,hh,ww in [(LOFT-.07,.22,.25),(EAVES-.06,.22,.27)]:
        face.box(0,z,face.length+.10,hh,ww,-.01,WOOD,'continuous wooden head beam')
    if hall:
        for i in range(bays):returned_fret(face,step*(i+.5)-face.length/2,EAVES-.17,step,low)
        return
    for z,h,d in [(LOFT+.15,.12,.12),(LOFT+.29,.095,.087),(LOFT+.98,.112,.119)]:
        face.box(0,z,face.length,h,d,0,WOOD,'upper gallery rails')
    for i in range(bays):
        cx=step*(i+.5)-face.length/2
        returned_fret(face,cx,EAVES-.17,step,low)
        for rank in range(1,8):
            z=LOFT
            u=cx-step/2+step*rank/8
            x,y=face.point(u,0,0)[:2]
            profile=[(z+.29,.047),(z+.38,.081),(z+.49,.037),(z+.61,.046),(z+.71,.073),(z+.83,.064),(z+.92,.042)]
            face.builder.lathe((x,y),profile,WOOD,6 if low else 10,face.label+'/vase-shaped balusters')


def roof_tiles(b,xmin,xmax,ymin,ymax,axis,low,label,rise=.97):
    """Two pitched tile beds; visible cylindrical rolls on the high-detail roof."""
    if axis=='east':
        mid=(ymin+ymax)/2
        north=lambda x,y:EAVES+rise*(1-abs(y-mid)/(ymax-mid))
        pieces=[(xmin,ymin,xmax,mid),(xmin,mid,xmax,ymax)]
    else:
        mid=(xmin+xmax)/2
        north=lambda x,y:EAVES+rise*(1-abs(x-mid)/(xmax-mid))
        pieces=[(xmin,ymin,mid,ymax),(mid,ymin,xmax,ymax)]
    for x0,y0,x1,y1 in pieces:
        corners=[(x,y,north(x,y))for x,y in [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]]
        sheet(b,corners,.105,ROOF,label+'/tile bed')
    if axis=='east':
        ridge=[(xmin,mid,EAVES+rise+.055),(xmax,mid,EAVES+rise+.055)]
        limits=(xmin,xmax)
    else:
        ridge=[(mid,ymin,EAVES+rise+.055),(mid,ymax,EAVES+rise+.055)]
        limits=(ymin,ymax)
    b.tube(ridge,.083,ROOF,8 if low else 12,label+'/ridge crest')
    count=ceil((limits[1]-limits[0])/(.45 if low else .225))
    for i in range(count+1):
        pos=limits[0]+(limits[1]-limits[0])*i/count
        ends=[(pos,ymin),(pos,mid),(pos,ymax)]if axis=='east' else [(xmin,pos),(mid,pos),(xmax,pos)]
        b.tube([(x,y,north(x,y)+.021)for x,y in ends],.033,ROOF,5 if low else 7,label+'/tile rolls')


def later_canopy(b,low):
    """Independent steel and translucent glazing of the glass-covered court documented by 2019."""
    left,right=-COURT_HALF,COURT_HALF
    def high(x):return 8.11-abs(x)*.205
    for x0,x1 in [(left,0),(0,right)]:
        sheet(b,[(x,y,high(x)) for x,y in [(x0,SOUTH),(x1,SOUTH),(x1,.42),(x0,.42)]],.022,CLEAR,'Later canopy/glazing')
    for y in [SOUTH,SOUTH*.67,SOUTH*.33,.42]:
        b.tube([(left,y,high(left)-.04),(0,y,high(0)-.04),(right,y,high(right)-.04)],.047,STEEL,6,'Later canopy/transverse frames')
        b.tube([(left,y,high(left)-.13),(right,y,high(right)-.13)],.032,STEEL,6,'Later canopy/truss tie')
        for x in [-3,-1.5,0,1.5,3]:
            b.tube([(x,y,high(left)-.13),(x,y,high(x)-.05)],.022,STEEL,5,'Later canopy/truss struts')
    for x in [-4.55,-3.02,-1.51,0,1.51,3.02,4.55]:
        b.tube([(x,SOUTH,high(x)+.012),(x,.42,high(x)+.012)],.029,STEEL,5,'Later canopy/longitudinal glazing bars')
    for x in [left,right]:
        for y in [SOUTH,SOUTH*.67,SOUTH*.33,.42]:
            b.tube([(x,y,EAVES),(x,y,high(x))],.052,STEEL,6,'Later canopy/clerestory posts')


def make_courtyard(builder,low=False):
    lo,hi=-6.84,7.15
    builder.plan_prism(box(-COURT_HALF,SOUTH,COURT_HALF,0),-.03,.035,BASE,'Court/grey paved floor')
    main=Facade(builder,(-COURT_HALF,1.03),(COURT_HALF,1.03),'North hall')
    partition(main,3,low,main=True)
    gallery(Facade(builder,(-COURT_HALF,.09),(COURT_HALF,.09),'North hall porch'),3,low,hall=True)
    builder.plan_prism(box(lo,0,hi,NORTH),.015,.16,BASE,'North hall/stone threshold and floor')
    main.box(0,2.80,3.12,.57,.12,.03,WOOD,'wood plaque')
    main.box(0,2.80,3.01,.47,.08,.10,PANEL,'red inscribed face')
    add_facade_lettering(main,'殿寶雄大',0,2.80,2.84,.36,.145,.185,PAINT,label='main hall gilt characters',font=FONT)
    for code,x,outer in [('West',-COURT_HALF,lo),('East',COURT_HALF,hi)]:
        rev=1 if code=='West' else -1
        near=(x,SOUTH if rev==1 else .02);far=(x,.02 if rev==1 else SOUTH)
        face=Facade(builder,near,far,code+' gallery');gallery(face,3,low)
        xwall=x-rev*1.15
        room=Facade(builder,(xwall,near[1]),(xwall,far[1]),code+' gallery room')
        partition(room,3,low)
        for z in [.04,LOFT]:
            builder.plan_prism(box(min(outer,x),SOUTH,max(outer,x),.08),z-.05,z+.035,BASE if z<1 else WOOD,code+' gallery/floor')
        roof_tiles(builder,min(outer,x)-.11,max(outer,x)+.11,SOUTH-.12,.08,'north',low,code+' gallery roof',.54)
        builder.box(((outer+xwall)/2,SOUTH+.08,3.10),(abs(outer-xwall),.16,6.17),PLASTER,label=code+' gallery/southern return')
        builder.box((outer,(SOUTH+NORTH)/2,3.11),(.15,NORTH-SOUTH,6.20),PLASTER,label=code+' outer wall')
    builder.box(((lo+hi)/2,NORTH-.075,3.12),(hi-lo,.15,6.23),PLASTER,label='North hall/plain north return')
    for x1,x2 in [(lo,-COURT_HALF),(COURT_HALF,hi)]:
        builder.box(((x1+x2)/2,.12,3.12),(x2-x1,.15,6.23),PLASTER,label='North hall/lateral junction')
    roof_tiles(builder,lo-.13,hi+.13,-.12,NORTH+.10,'east',low,'North hall roof',1.04)
    later_canopy(builder,low)
