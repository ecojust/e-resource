"""South front of the Picardie Apartments after its 2023 restoration, in metres."""
import json
from pathlib import Path
from shapely.geometry import box
from shapely.ops import unary_union
from photo_architecture import Facade, opening

P = json.loads(Path(__file__).with_name('parameters.json').read_text())
HALF = P['front_half_width_m']
REAR = P['section_depth_m']
PITCH = P['storey_pitch_m']
BASE = P['upper_storey_start_m']
CANOPY = P['canopy_projection_m']
OCHRE = 'warm water washed aggregate'
CREAM = 'pale water washed aggregate'
BLADE = 'light vertical tower ribs'
GLASS = 'gray garden glazing'
SASH = 'dark casement metal'
IRON = 'bronze balcony rail'
TILES = 'black square ceramic'
GROUT = 'ceramic tile joints'
WHITE = 'cut artificial stone'
SOFFIT = 'coffer shadow'
WOOD = 'warm entrance timber'
PANEL = 'recessed timber panel'
BRASS = 'door hardware'
EDGE = 'dark roof metal'
CUT = 'neutral section finish'
PALETTE = {
    OCHRE: dict(color=[.68,.551,.355],roughness=.87), CREAM: dict(color=[.82,.79,.68],roughness=.88),
    BLADE: dict(color=[.84,.75,.565],roughness=.81), GLASS: dict(color=[.165,.216,.236],roughness=.34,metallic=.13),
    SASH: dict(color=[.145,.162,.168],roughness=.56), IRON: dict(color=[.168,.154,.124],roughness=.55,metallic=.28),
    TILES: dict(color=[.135,.137,.145],roughness=.58), GROUT: dict(color=[.267,.265,.256],roughness=.83),
    WHITE: dict(color=[.871,.846,.766],roughness=.72), SOFFIT: dict(color=[.49,.475,.432],roughness=.86),
    WOOD: dict(color=[.353,.224,.136],roughness=.61), PANEL: dict(color=[.248,.157,.109],roughness=.61),
    BRASS: dict(color=[.45,.349,.198],roughness=.51,metallic=.44), EDGE: dict(color=[.325,.315,.278],roughness=.83),
    CUT: dict(color=[.46,.442,.393],roughness=.92),
}
DOORS = [(-4.15,1.55),(0.,3.35),(4.15,1.55)]

def sash(face,x,z,w,h,lod,leaves=2,label='window',depth=0):
    pane=opening(x,z,w,h)
    face.prism(pane.buffer(.009,join_style=2),depth-.27,depth-.25,GLASS,label+' glazing')
    frame=pane.buffer(-.016,join_style=2)
    inner=pane.buffer(-.072,join_style=2)
    bars=[]
    for j in range(1,leaves):
        xx=x-w/2+w*j/leaves
        bars.append(box(xx-.022,z,xx+.022,z+h))
    if not lod:
        bars.append(box(x-w/2,z+h*.68-.020,x+w/2,z+h*.68+.020))
    face.prism(frame.difference(inner.difference(unary_union(bars))),depth-.18,depth-.105,SASH,label+' frame')
    return pane

def solid(builder,x,z,w,h,y,depth,mat,label):
    builder.box((x,y,z),(w,depth,h),mat,label=label)

def wing(builder,side,lod):
    # Moving outward from the two loggias, the principal ochre bays and the
    # narrow secondary lights meet the lower, pale end return at the street side.
    sectors=[(4.47,7.45,12,5.83,1.88,OCHRE,.0),
             (7.45,11.12,11,9.08,2.00,OCHRE,.0),
             (11.12,13.23,11,12.12,.77,OCHRE,.0),
             (13.23,HALF,9,14.42,1.66,CREAM,.50)]
    for i,(left,right,levels,xc,ww,material,y) in enumerate(sectors):
        x0,x1=sorted((side*left,side*right)); center=(x0+x1)/2
        face=Facade(builder,(x0,y),(x1,y),('East' if side>0 else 'West')+f'/wing {i+1}')
        h=BASE+PITCH*levels+.32
        lights=[]
        for k in range(levels):
            bottom=BASE+PITCH*k+.72
            lights.append(sash(face,side*xc-center,bottom,ww,2.04,lod,1 if ww<1 else 3,'casement'))
        face.wall(BASE,h,lights,thickness=.33,material=material)
        builder.plan_prism(box(x0,y-.035,x1,REAR+.025),h-.03,h+.045,EDGE,face.label+'/terrace coping')
        if side==1:perimeter=x1
        else:perimeter=x0
        next_top=BASE+PITCH*sectors[i+1][2]+.32 if i+1<len(sectors) else BASE
        if h>next_top+.01:
            solid(builder,perimeter-side*.085,(h+next_top)/2,.17,h-next_top,(REAR+.35)/2,REAR-.35,material,face.label+'/exposed setback return')
        if i==3:
            # Small return in the exterior plane links the pale and ochre planes.
            solid(builder,side*(left-.06),(h+BASE)/2,.12,h-BASE,.39,.23,OCHRE,face.label+'/white wing shoulder')
        solid(builder,center,(h+BASE)/2,x1-x0,h-BASE,REAR-.09,.18,CUT,face.label+'/back of section')

def balcony_tower(b,lod):
    face=Facade(b,(-4.47,0),(4.47,0),'Tower')
    center_top=BASE+13*PITCH+1.10
    spine=box(-1.48,BASE,1.48,center_top)
    windows=[]
    for k in range(13):
        for x in (-.56,.56):
            windows.append(sash(face,x,BASE+k*PITCH+.73,.73,1.99,lod,1,'narrow axis lights'))
    face.prism(spine.difference(unary_union(windows)),-.35,0,OCHRE,'central spine')
    solid(b,0,center_top-.025,2.96,.14,REAR/2,REAR+.07,EDGE,'Tower/central flat roof')
    solid(b,0,(BASE+center_top)/2,2.96,center_top-BASE,REAR-.10,.20,CUT,'Tower/back section')
    loggia_depth=P['balcony_clear_depth_m']
    for s in (-1,1):
        mid=s*3.0
        top=BASE+13*PITCH+.27
        back=Facade(b,(mid-1.02,loggia_depth),(mid+1.02,loggia_depth),'East loggia' if s>0 else 'West loggia')
        holes=[]
        for k in range(13):
            z=BASE+k*PITCH
            holes.append(sash(back,0,z+.19,1.62,2.63,lod,2,'recessed French lights'))
            solid(b,mid,z-.009,2.10,.28,.49,2.94,BLADE,back.label+'/balcony slab')
            # Crossbars and vertical spindles frame real air in front of the recessed doors.
            for bar in (.19,.61,1.02):
                solid(b,mid,z+bar,2.00,.045,-.895,.044,IRON,back.label+'/front rails')
            for j in range(1,10 if not lod else 6):
                px=mid-1+2*j/(10 if not lod else 6)
                solid(b,px,z+.57,.024,.88,-.895,.034,IRON,back.label+'/rail spindles')
            for j in (-1,1):
                solid(b,mid+j*.98,z+1.02,.045,.045,-.445,.91,IRON,back.label+'/side returns')
            if not lod:
                solid(b,mid,z-.097,2.12,.073,-.98,.05,WHITE,back.label+'/slab nosing')
        back.wall(BASE,top,holes,thickness=.33,material=OCHRE)
        for xx,w,proj,cap in ((1.73,.50,.39,center_top),(4.245,.45,.11,top)):
            solid(b,s*xx,(BASE+cap)/2,w,cap-BASE,(REAR-proj)/2,REAR+proj,BLADE,back.label+'/continuous vertical pylon')
        solid(b,mid,top-.12,2.04,.24,(REAR-.59)/2,REAR+.59,BLADE,back.label+'/roof above loggia')
        solid(b,mid,(top+BASE)/2,2.04,top-BASE,REAR-.09,.18,CUT,back.label+'/back of section')

def tile_joints(face,shape,lod,label):
    x0,z0,x1,z1=shape.bounds
    pitch=.17 if not lod else .34
    thickness=.012 if not lod else .015
    for axis in range(2):
        start,end=(x0,x1) if axis==0 else (z0,z1)
        for k in range(int(start/pitch)-1,int(end/pitch)+2):
            v=k*pitch
            if not start+.015<v<end-.015:continue
            stripe=box(v-thickness/2,z0,v+thickness/2,z1) if axis==0 else box(x0,v-thickness/2,x1,v+thickness/2)
            face.prism(shape.intersection(stripe),.001+axis*.003,.004+axis*.003,GROUT,label)

def entrance(b,lod):
    face=Facade(b,(-HALF,0),(HALF,0),'534 entrance')
    vestibule=Facade(b,(-HALF,.49),(HALF,.49),'Timber vestibule')
    # The white reveals frame three separate closed doorways under the cantilever.
    door_top=3.64
    opening_group=box(-6.02,0,6.02,4.30)
    cuts=[opening(x,0,w,door_top) for x,w in DOORS]
    face.prism(opening_group.difference(unary_union(cuts)),-.47,.01,WHITE,'pale jointed door piers')
    for x,w in DOORS:
        solid(b,x,door_top/2,w,door_top,.49,.10,WOOD,'Timber vestibule/closed doors')
        leaves=2 if x==0 else 1
        for j in range(leaves):
            xx=x-w/2+(j+.5)*w/leaves; lw=w/leaves
            for bottom,height in ((.22,1.03),(1.42,1.69)):
                vestibule.box(xx,bottom+height/2,lw-.21,height,.09,.103,PANEL,'inset leaf panels')
                frame=opening(xx,bottom,lw-.21,height)
                vestibule.prism(frame.difference(frame.buffer(-.065,join_style=2)),.145,.17,WOOD,'panel bead')
            if not lod:
                vestibule.box(xx+lw*.29,1.13,.044,.37,.06,.18,BRASS,'pulls')
    for x in (-5.50,-2.59,2.59,5.50):
        for z in (1.00,1.82,2.66,3.46):
            face.box(x,z,.80,.016,.020,.016,CREAM,'horizontal masonry joints')
        if abs(x)<3:
            face.box(x,2.79,.275,1.06,.15,.12,BRASS,'long entrance lamps')
            face.box(x,2.79,.16,.82,.075,.23,WHITE,'milk glass of lamp')
    # The middle pavilion bay has two narrow independent lights separated by
    # the original dark tiled pier, between two larger side windows.
    openings=[]
    for x,ww,leaves in ((-3.90,1.87,3),(-.60,.72,1),(.60,.72,1),(3.90,1.87,3)):
        openings.append(sash(face,x,5.62,ww,1.67,lod,leaves,'second storey pavilion'))
    extra=[]
    for s in (-1,1):
        for xx in (7.70,9.95,12.20,14.45):
            extra.append(sash(face,s*xx,3.83,.84,1.90,lod,1,'upper base lights'))
        for xx in (8.25,10.71):
            extra.append(sash(face,s*xx,.60,1.14,1.85,lod,1,'garden-level base lights'))
    # The raised dark rectangular pavilion stands above the two lower outer parapets.
    profile=unary_union([box(-HALF,0,HALF,6.36),box(-5.22,0,5.22,BASE)])
    dark=profile.difference(unary_union([opening_group,*openings,*extra]))
    face.prism(dark,-.38,0,TILES,'black square tile body')
    tile_joints(face,dark,lod,'tile joints')
    for s in (-1,1):
        center=s*(HALF+6.02)/2;w=HALF-6.02
        solid(b,center,6.46,w,.26,.025,.72,WHITE,'534 entrance/white outer belt')
        # The light-coloured lower windows continue one row below the central
        # black pavilion parapet. Its top entirely hides the two loggia bases.
        for xl,xr,y,color,lights in [
                (5.22,13.23,0.,OCHRE,[(6.29,1.66),(9.08,2.0),(12.12,.77)]),
                (13.23,HALF,.5,CREAM,[(14.42,1.66)])]:
            x0,x1=sorted((s*xl,s*xr))
            row=Facade(b,(x0,y),(x1,y),'534 entrance/low wing lights')
            holes=[sash(row,s*x-(x0+x1)/2,6.70,ww,1.36,lod,1 if ww<1 else 3,'garden light') for x,ww in lights]
            row.wall(6.36,BASE,holes,thickness=.34,material=color)
    solid(b,0,BASE-.075,HALF*2,.11,(REAR+.36)/2,REAR-.36,EDGE,'534 entrance/base roof')
    solid(b,0,BASE/2,HALF*2,BASE,REAR-.10,.20,CUT,'534 entrance/section back')
    for s in (-1,1):
        solid(b,s*(HALF-.09),BASE/2,.18,BASE,(REAR+.38)/2,REAR-.38,TILES,'534 entrance/side closure')
    width=P['canopy_width_m']
    # Coffers remain recessed. A solid top skin, perimeter fascia and horizontal
    # and transverse soffit ribs leave distinct box recesses without through-holes.
    solid(b,0,4.53,width-.12,.19,-(CANOPY-.10)/2,CANOPY-.10,SOFFIT,'Suspended canopy/coffer ceilings')
    solid(b,0,4.36,width,.30,-CANOPY+.10,.20,WHITE,'Suspended canopy/garden fascia')
    for s in (-1,1):
        solid(b,s*(width/2-.10),4.36,.20,.30,-(CANOPY-.21)/2,CANOPY-.21,WHITE,'Suspended canopy/perimeter side')
    # The restoration team's underside photograph shows three rows in the
    # projection direction. Each coffer opens into the darker ceiling above.
    coffers=[box(i*1.12-.34,y-.38,i*1.12+.34,y+.38)
             for i in range(-6,7) for y in (-.86,-2.18,-3.53)]
    panel=box(-width/2+.20,-CANOPY+.20,width/2-.20,-.018)
    b.plan_prism(panel.difference(unary_union(coffers)),4.235,4.445,WHITE,'Suspended canopy/recessed coffer grid')
    solid(b,0,4.71,width+.09,.14,-CANOPY/2,CANOPY+.07,WHITE,'Suspended canopy/top drip')
    # The shorter screen is set back from the garden fascia. Three visible
    # openings, the middle one wider, leave the two reveals and their shadow.
    half_screen=5.08
    screen=Facade(b,(-half_screen,-1.31),(half_screen,-1.31),'Suspended canopy')
    front=box(-half_screen,4.77,half_screen,5.90)
    slots=[opening(x,4.78,w,.425) for x,w in [(-3.57,1.28),(0.,2.38),(3.57,1.28)]]
    screen.prism(front.difference(unary_union(slots)),-.29,0,WHITE,'three opening screen')
    screen.box(0.,5.94,2*half_screen+.12,.13,.40,.065,WHITE,'screen upper coping')
    screen.box(0.,5.31,2*half_screen+.04,.075,.36,.035,WHITE,'screen lower drip')

def add_south_front(builder,lod):
    entrance(builder,lod)
    wing(builder,-1,lod)
    wing(builder,1,lod)
    balcony_tower(builder,lod)
