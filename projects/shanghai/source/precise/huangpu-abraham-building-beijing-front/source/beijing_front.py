"""Brick northern street wall and chamfered west end of the Abraham Co. Building.

X increases from the shallow bay toward Yuanmingyuan Road. Measured photo
relationships set the openings, while the exact storey levels remain estimates.
"""
import math
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade, opening

BRICK='red-brown facing brick'
HEAD='warm brick lintel'
JOINT='dark brick course'
PALE='pale stone cornice and keys'
WINDOW='brown-black metal frames'
GLASS='blue-grey upper windows'
SHOP='shopfront glazing'
ROOF='terracotta mansard tiles'
PALETTE={
    BRICK:{'color':[.43,.205,.142],'roughness':.91},
    HEAD:{'color':[.50,.265,.19],'roughness':.90},
    JOINT:{'color':[.295,.145,.108],'roughness':.96},
    PALE:{'color':[.70,.67,.60],'roughness':.89},
    WINDOW:{'color':[.135,.133,.122],'roughness':.57},
    GLASS:{'color':[.245,.307,.335],'roughness':.34,'metallic':.14},
    SHOP:{'color':[.18,.205,.215],'roughness':.39,'metallic':.08},
    ROOF:{'color':[.425,.226,.163],'roughness':.87},
}
FLAT=(-10.28,8.50)
BAY=-8.39
BACK=3.74
GROUND=[(-8.39,1.82),(-4.89,1.92),(-1.53,2.02),(2.10,2.03),(5.87,2.13)]
UPPER=[(-5.21,1.12),(-3.69,1.10),(-2.18,1.15),(.63,1.39),(3.91,1.56),(7.15,1.32)]
CORNICE=14.48
STOREYS=[(4.95,2.20,.15),(8.26,2.27,.18),(11.66,2.18,0.)]


def cut_levels(face,centres,lod,include_corner=False):
    """The voussoir runs have true reveals, separate keys and recessed glazing."""
    cuts=[]
    for u,w in centres:
        cuts.append((opening(u,.11,w,3.82,.33 if include_corner else w*.47,10 if lod else 22),'corner door' if include_corner else 'shop'))
    slots=UPPER if not include_corner else [(0,1.32)]
    if not include_corner:
        slots=[(u-(FLAT[0]+FLAT[1])/2,w)for u,w in slots]
    for level,(sill,height,rise) in enumerate(STOREYS):
        for u,w in slots:
            cuts.append((opening(u,sill,w,height,rise,8 if lod else 16),level))
    return cuts


def keystone(face,u,crown,width,height):
    shape=Polygon([(u-width*.26,crown-.055),(u+width*.26,crown-.055),
        (u+width*.50,crown+height),(u-width*.50,crown+height)])
    face.prism(shape,.02,.13,PALE,'tapered keystone')


def frame_opening(face,opening_shape,role,lod):
    x0,z0,x1,z1=opening_shape.bounds;u=(x0+x1)/2;ww=x1-x0
    face.window(opening_shape,1,2 if role!='shop' else 3,frame=WINDOW,trim=False,
                glass=SHOP if role in ('shop','corner door') else GLASS,label='display arch' if role=='shop' else 'upper sash')
    if role=='corner door':
        surround=opening_shape.buffer(.165,join_style=2).difference(opening_shape).intersection(box(x0-.3,0,x1+.3,z1+.25))
        face.prism(surround,-.03,.145,PALE,'corner entrance pale surround')
        for sign in (-1,1):
            side=u+sign*(ww/2+.17)
            for z,width,h,depth in [(3.66,.33,.16,.14),(3.80,.39,.11,.18),(3.91,.43,.10,.22)]:
                face.box(side,z,width,h,depth,.10,PALE,'corner entrance corbel')
    elif role=='shop':
        spring=z1-ww*.47
        jacket=opening_shape.buffer(.21,join_style=2).difference(opening_shape).intersection(box(x0-.23,spring,x1+.23,z1+.24))
        face.prism(jacket,-.014,.032,HEAD,'arched brick head')
        steps=6 if lod else 12
        for j in range(1,steps):
            a=math.pi*j/steps
            r=ww*.5
            pts=[face.point(u+rr*math.cos(a),spring+(rr-.02)*math.sin(a)*.94,.039) for rr in (r+.005,r+.19)]
            face.builder.tube(pts,.009,JOINT,4,'radial shop-arch joints')
        keystone(face,u,z1,.29,.40)
    elif isinstance(role,int) and role<2:
        keystone(face,u,z1,.22,.27)
    else:
        face.box(u,z1+.046,ww+.23,.095,.11,.027,PALE,'flat window lintel')
    if role not in ('shop','corner door'):face.box(u,z0-.042,ww+.19,.095,.18,.067,PALE,'individual sill')


def courses(face,bottom,top,positions,*,project=.11):
    for z,h,dept in positions:
        if bottom<=z<=top:face.box(0,z,face.length+.012,h,dept,project*.36,PALE,'continuous stone course')


def oriel(builder,lod):
    # The shallow canted bay has three glazed faces. The portion above its
    # second continuous lintel is brick rather than a third row of windows.
    base=[(BAY-1.68,0),(BAY-1.31,-.37),(BAY+1.26,-.37),(BAY+1.67,0)]
    outline=Polygon([*base,(BAY+1.66,.18),(BAY-1.66,.18)])
    for z,h,spread in [(4.05,.22,.09),(4.27,.11,.15),(7.67,.15,.09),(9.08,.15,.07),(10.94,.18,.12)]:
        builder.plan_prism(outline.buffer(spread,join_style=2),z,z+h,PALE,'oriel stepped band')
    for i in range(3):
        face=Facade(builder,base[i],base[i+1],'shallow three-face bay')
        holes=[]
        for z,h in ((4.76,2.47),(7.96,.92),(9.34,1.44)):
            width=face.length-(.39 if i==1 else .16)
            sh=opening(0,z,width,h,0);holes.append(sh)
            face.window(sh,2 if i==1 else 1,1 if h<1 else 2,frame=WINDOW,trim=False,glass=GLASS,label='oriel glazing')
        face.wall(4.12,11.28,holes,.15,BRICK)
    # The upper sign panel is visible by outline only. No guessed lettering.
    plain=Facade(builder,(BAY-1.72,0),(BAY+1.72,0),'brick panel above oriel')
    plain.box(0,11.64,3.39,.12,.07,.038,HEAD,'top of shallow oriel')


def dormer(b,cx,width,height,round_head,lod):
    bottom=CORNICE+.43
    f=Facade(b,(cx-width/2,.07),(cx+width/2,.07),'front mansard dormer')
    if round_head:
        sh=opening(0,bottom,width,height,width*.25,12 if lod else 26)
    else:
        sh=Polygon([(-width/2,bottom),(width/2,bottom),(width/2,bottom+height*.72),(0,bottom+height),(-width/2,bottom+height*.72)])
    glass=opening(0,bottom+.08,width*.53,height*.49)
    f.prism(sh.difference(glass),-.29,0,BRICK,'dormer cheek and head')
    f.window(glass,2 if width>1.6 else 1,1,frame=WINDOW,trim=False,glass=GLASS,label='dormer pane')
    border=sh.buffer(.085,join_style=2).difference(sh).intersection(box(-width,bottom+height*.6,width,bottom+height+.15))
    f.prism(border,-.27,.12,PALE,'dormer stepped pediment')


def oculus(face,u,z,lod):
    circular=Point(u,z).buffer(.32,quad_segs=6 if lod else 18)
    face.prism(circular.buffer(.007),-.19,-.145,GLASS,'recessed oculus')
    face.prism(circular.buffer(.12).difference(circular),-.04,.092,PALE,'pale oculus surround')
    return circular


def parapet(f,u,level,lod,reverse=False):
    # Two oculi appear on adjacent wall planes. The upper wall lines step
    # toward the corner and frame the pair, without a second dome at this end.
    width=f.length
    profile=[(-.50,.28),(-.43,.88),(-.33,1.50),(-.18,1.97),(.01,2.27),(.23,2.42),(.50,2.45)]
    top=[(x*width*(-1 if reverse else 1),level+z)for x,z in profile]
    top.sort()
    crown=Polygon([(-width/2,level),(width/2,level),*reversed(top)])
    sh=oculus(f,u,level+1.52,lod)
    f.prism(crown.difference(sh),-.36,0,BRICK,'corner parapet with round window')
    from shapely.geometry import LineString
    rim=LineString(top).buffer(.073,cap_style=2,join_style=2)
    f.prism(rim,-.39,.12,PALE,'corner parapet pale outline')


def facade(b,lod=False):
    start,end=FLAT;mid=(start+end)*.5
    front=Facade(b,(start,0),(end,0),'Beijing Road brick frontage')
    turn=Facade(b,(end,0),(end+2.00,2.08),'angled west corner')
    for f,groups,corner in [(front,[(x-mid,w)for x,w in GROUND],False),(turn,[(0,1.43)],True)]:
        cuts=cut_levels(f,groups,lod,corner)
        holes=[s for s,role in cuts]
        if not corner:holes.append(box(BAY-mid-1.54,4.23,BAY-mid+1.54,11.13))
        f.wall(0,CORNICE,holes,.40,BRICK)
        for shape,role in cuts:frame_opening(f,shape,role,lod)
        courses(f,0,CORNICE,[(.14,.17,.095),(4.41,.18,.23),(4.56,.09,.17),(7.57,.11,.20),(7.69,.075,.145),(14.25,.11,.16),(14.44,.15,.23)])
        # Thin recessed-looking joints are modelled across opaque brick only.
        if not lod:
            mask=box(-f.length/2,.32,f.length/2,4.33).difference(unary_union(holes))
            for z in (.43,.82,1.21,1.60,1.99,2.38,2.77,3.16,3.55,3.94,4.24):
                line=box(-f.length/2,z,f.length/2,z+.018).intersection(mask)
                f.prism(line,.002,.016,JOINT,'rusticated lower horizontal joints')
            wall=box(-f.length/2,4.58,f.length/2,14.20).difference(unary_union(holes))
            for course in range(92):
                z=4.65+course*.103
                # Fine running courses are visible on the original north wall.
                # Keep openings, pale keys and the shallow bay free of joint lines.
                strip=box(-f.length/2,z,f.length/2,z+.009).intersection(wall)
                f.prism(strip,.0005,.004,JOINT,'upper brick bed joints')
        for s,role in cuts:
            if role!=1:continue
            x0,z0,x1,z1=s.bounds;u=(x0+x1)/2
            f.box(u,z1+.47,x1-x0+.14,.085,.07,.018,HEAD,'brick hood over middle floor')
    # The upper two storeys alternate grouped windows and shallow engaged
    # brick piers, distinct from the broad rusticated piers at pavement level.
    for xx in (-6.48,-1.04,5.44,8.34):
        u=xx-mid
        front.box(u,10.89,.17,6.72,.07,.032,HEAD,'tall brick pier strip')
        if not lod:
            front.box(u-.09,10.89,.025,6.64,.06,.042,JOINT,'return line of pier')
    corner_bracket=Facade(b,(end-1.10,0),(end,0),'corner stone entrance transition')
    for level,depth,height in ((3.83,.20,.15),(4.02,.25,.22),(4.22,.18,.13)):
        corner_bracket.box(0,level,corner_bracket.length,height,depth,.08,PALE,'cut-end entrance entablature')
    oriel(b,lod)
    slope=[(start,0,CORNICE),(end,0,CORNICE),(end+1.99,2.08,CORNICE),(end+1.85,BACK,CORNICE+1.52),(start,BACK,CORNICE+1.52)]
    b.add(slope,[(0,1,2),(0,2,3),(0,3,4)],ROOF,'cropped lower mansard')
    for x,wd,h,rounded in [(-7.45,2.06,1.61,True),(-1.94,1.74,1.29,True),(3.70,1.25,1.14,False)]:dormer(b,x,wd,h,rounded,lod)
    parapet(Facade(b,(end-3.12,0),(end,0),'west end of northern parapet'),.55,CORNICE,lod)
    parapet(turn,-.12,CORNICE,lod,reverse=True)
