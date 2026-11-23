"""The two dark green upper windows, tilted lower panels, recessed doors and set-back render wall."""
from pathlib import Path
import json
import math
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from photo_architecture import Facade
from street_finishes import UPPER,LOWER,GREEN,BASE

SILL='Changle | weathered pale sill'
GLASS='Changle | shaded glass'
GLASS_LIGHT='Changle | sky reflected in opening sash'
DARK='Changle | shaded stairwell'
PIPE='Changle | yellow painted service pipe'
IRON='Changle | iron drain and fittings'
LOUVER='Changle | cream louvre screen'
RED='Changle | weathered red timber at wing end'
PALETTE={SILL:{'color':[.34,.34,.29],'roughness':.88},GLASS:{'color':[.042,.064,.064],'metallic':.13,'roughness':.37},
         GLASS_LIGHT:{'color':[.16,.23,.24],'metallic':.21,'roughness':.26},DARK:{'color':[.013,.018,.016],'roughness':.91},
         PIPE:{'color':[.37,.23,.057],'roughness':.7},IRON:{'color':[.065,.064,.053],'metallic':.25,'roughness':.7},
         LOUVER:{'color':[.65,.60,.46],'roughness':.7},RED:{'color':[.155,.066,.045],'roughness':.86}}
HERE=Path(__file__).absolute().parent
DATA=HERE.parent/'measurements/street-cameras.json'
LEFT=-5.57
UPPER_LEFT=-2.06
RIGHT=4.10
HOUSE_EAVE=5.34
REAR_Y=3.10

def arch_shape(cx,w,z0,top,rise):
    shoulder=top-rise
    curve=[(cx+.5*w*math.cos(t*math.pi/18),shoulder+rise*math.sin(t*math.pi/18)) for t in range(19)]
    return Polygon([(cx-w/2,z0),(cx+w/2,z0),*curve])

def rotated_leaf(builder,hinge,width,z0,z1,angle,sense,label,pale=False):
    """Rotate a complete divided sash about its own outer hinge, keeping the panes in its frame."""
    theta=math.radians(angle)
    dx=sense*math.cos(theta);dy=-math.sin(theta)
    end=(hinge[0]+dx*width,hinge[1]+dy*width)
    # The local helper's horizontal tangent follows physical +X for either leaf.
    a,b=(hinge,end) if sense>0 else (end,hinge)
    f=Facade(builder,a,b,label)
    h=z1-z0;outer=box(-width/2,z0,width/2,z1)
    border_x=min(.056,width*.19);border_z=min(.065,h*.14)
    stop=box(-width/2+border_x,z0+border_z,width/2-border_x,z1-border_z)
    bars=[box(-.010,z0,.010,z1)]
    for fraction in (1/3,2/3):
        z=z0+border_z+(h-2*border_z)*fraction
        bars.append(box(-width/2,z-.009,width/2,z+.009))
    panes=stop.difference(unary_union(bars))
    f.prism(outer.difference(panes),-.018,.020,GREEN,'six-light-opening-leaf')
    for idx,piece in enumerate(panes.geoms):
        f.prism(piece,-.016,-.005,GLASS_LIGHT if pale else GLASS,f'pane-{idx+1}')

def upper_pair(builder,front,label,bounds,angle_right):
    x0,z0,x1,z1=bounds;w=x1-x0
    face=box(x0,z0,x1,z1);clearance=.033
    inside=box(x0+clearance,z0+clearance,x1-clearance,z1-clearance)
    front.prism(face.difference(inside),-.119,-.059,GREEN,label+'/outer-rebated-frame')
    # A shadow plane fills the sight gap when the moving leaf opens.
    front.prism(face,-.25,-.235,DARK,label+'/dark-interior')
    for side in (1,-1):
        hinge_x=x0+clearance if side==1 else x1-clearance
        angle=0 if side==1 else angle_right
        rotated_leaf(builder,(hinge_x,.082),(w-2*clearance)/2-.003,z0+clearance,z1-clearance,angle,side,
                     label+('/left' if side==1 else '/right'),pale=angle_right>0 and side==1)
    front.box((x0+x1)/2,z0-.033,w+.10,.068,.16,.009,SILL,label+'/projecting-sill')

def lower_panel(builder,front,label,bounds,outward=.26):
    x0,z0,x1,z1=bounds;w=x1-x0;h=z1-z0
    glazing=box(x0+.045,z0+.03,x1-.045,z1-.046)
    mid=(x0+x1)/2
    bars=unary_union([box(mid-.031,z0,mid+.031,z1),
                      box(x0+w*.25-.010,z0,x0+w*.25+.010,z1),
                      box(x0+w*.75-.010,z0,x0+w*.75+.010,z1)])
    panes=glazing.difference(bars);rim=box(x0,z0,x1,z1).difference(panes)
    front.prism(rim,-.071,-.030,GREEN,label+'/four-glazed-lights')
    for idx,pane in enumerate(panes.geoms):front.prism(pane,-.065,-.052,GLASS,label+f'/upper-light-{idx+1}')
    # The photographed green panel is solid below the glazed lights. The top
    # leans streetward and hides part of the glazing behind it.
    bottom_y=-.025;top_y=-outward
    top=z0+h*.657;dz=top-z0
    length=math.hypot(dz,top_y-bottom_y)
    basis=[(1,0,0),(0,dz/length,-(top_y-bottom_y)/length),(0,(top_y-bottom_y)/length,dz/length)]
    builder.box((mid,(bottom_y+top_y)/2,(z0+top)/2),(w+.006,.034,length),GREEN,basis,label+'/solid-outward-tilting-panel')
    front.box(mid,z0+.018,w-.074,.035,.06,.005,IRON,label+'/lower-hinge-bar')

def street_doors(f,doors):
    for n,(x,w,head,depth) in enumerate(doors):
        mouth=arch_shape(x,w,.024,head,.084)
        leaf=arch_shape(x,w-.082,.036,head-.041,.072)
        f.prism(mouth,-depth-.042,-depth-.028,DARK,f'door{n+1}/shaded-reveal')
        f.prism(mouth.difference(leaf),-depth-.025,-depth+.002,GREEN,f'door{n+1}/frame')
        f.prism(leaf,-depth-.025,-depth-.005,GREEN,f'door{n+1}/recessed-leaf')
        f.box(x,.018,w+.014,.036,depth+.055,-depth/2,SILL,f'door{n+1}/threshold')

def fitted_windows(points):
    return [(points['AL'][0],points['aL'][2],points['AR'][0],points['AL'][2]),
            (points['BL'][0],points['bL'][2],points['BR'][0],points['BL'][2])]

def add_front(b,lod=False):
    pts=json.loads(DATA.read_bytes())['points'];upper=fitted_windows(pts)
    widths=pts['HR'][0]-pts['HL'][0]
    lower=[(pts['HL'][0],.89,pts['HR'][0],pts['HL'][2]),
           (pts['IL'][0],.91,pts['IL'][0]+widths,pts['IL'][2])]
    doors=[(pts['DH'][0],.72,pts['DH'][2],.18),(-3.38,.69,1.94,.16)]
    f=Facade(b,(-1,0),(1,0),'337 street wall')
    openings=[arch_shape(x,w,.024,h,.084) for x,w,h,_ in doors]+[box(*bounds) for bounds in lower+upper]
    # The white wall continues further toward 335, outside this measured part.
    shape=unary_union([box(LEFT,0,RIGHT,2.87),box(UPPER_LEFT,2.865,RIGHT,HOUSE_EAVE)])
    wall=shape.difference(unary_union(openings));z_split=2.81
    plinth=box(LEFT-1,-1,RIGHT+1,.245);upper_band=box(LEFT-1,z_split,RIGHT+1,HOUSE_EAVE+.05)
    f.prism(wall.intersection(plinth),-.222,.006,BASE,'street-plinth')
    f.prism(wall.difference(plinth).difference(upper_band),-.22,0,LOWER,'pale-lower-storey')
    f.prism(wall.intersection(upper_band),-.223,0,UPPER,'ochre-upper-storey')
    # The low wall is capped where the photographed hipped roof steps back.
    f.box((LEFT+UPPER_LEFT)/2,2.878,UPPER_LEFT-LEFT,.040,.253,-.087,SILL,'low-wall-coping')
    for i,bounds in enumerate(upper):upper_pair(b,f,f'upper-{i+1}',bounds,0 if i==0 else 14.)
    for i,bounds in enumerate(lower):lower_panel(b,f,f'lower-{i+1}',bounds)
    street_doors(f,doors)
    service_pipe(f,lod)

def service_pipe(f,lod):
    lines=[[(LEFT,2.29),(-1.46,2.29),(-1.46,.68),(-.43,.68),(-.43,.52),(-.35,.52),(-.35,.03)],
           [(-1.46,.68),(-1.46,3.30)],
           [(-1.46,2.29),(3.98,2.29),(3.98,5.19)]]
    for i,line in enumerate(lines):
        for n,(a,b) in enumerate(zip(line,line[1:])):
            f.line((*a,.034),(*b,.034),.019,PIPE,8 if lod else 12,f'service-pipe-{i+1}/span-{n+1}')
    for x,z in ((-4.83,2.29),(-1.46,1.68),(-.89,.68),(2.7,2.29),(3.98,3.72)):
        f.box(x,z,.061,.047,.060,.022,IRON,'wall-fastened-pipe-strap')
    f.box(-.53,.68,.065,.06,.072,.041,IRON,'service-pipe-coupling')

def add_rear_wing(b,lod=False):
    f=Facade(b,(-1,REAR_Y),(1,REAR_Y),'337 recessed wing')
    x0,x1=3.69,10.10;top=5.64
    window=(3.85,3.28,5.47,4.60);hole=box(*window)
    wall=box(x0,0,x1,top).difference(hole)
    f.prism(wall,-.22,0,UPPER,'roughcast-face-with-recessed-window')
    f.prism(hole,-.235,-.22,DARK,'dark-window-backing')
    a,lo,c,hi=window
    frame=box(a,lo,c,hi).difference(box(a+.067,lo+.054,c-.065,hi-.057))
    f.prism(frame,-.115,-.063,GREEN,'sash-surround')
    f.prism(box(a+.71,lo+.05,a+.755,hi-.045),-.103,-.065,GREEN,'window-mullion')
    f.prism(box(a+.74,lo+.058,c-.065,hi-.063),-.155,-.132,GLASS,'shaded-right-light')
    wing=Facade(b,(a+.076,REAR_Y-.25),(a+.675,REAR_Y+.02),'337 rear opening light')
    frame=box(-wing.length/2,lo+.062,wing.length/2,hi-.06)
    glass=frame.buffer(-.047,join_style=2)
    wing.prism(frame.difference(glass),-.018,.019,GREEN,'painted-casement')
    wing.prism(glass,-.011,.002,GLASS_LIGHT,'glass-pane')
    f.box((a+c)/2,lo-.04,c-a+.10,.080,.149,.008,SILL,'window-sill')
    # A shallow closed panel extends from the lower sash to the foreground
    # wall coping. The roughcast return and wooden sill remain visible above it.
    f.box((a+c)/2,lo-.234,c-a-.09,.37,.11,-.036,SILL,'below-sash rendered panel')
    add_louvred_unit(b,f,lod)
    # 2017 hopper, outlet and inclined downpipe are measured independently.
    f.line((9.73,2.52,.042),(9.83,4.78,.087),.037,IRON,8 if lod else 14,'rainwater-downpipe')
    f.prism(Polygon([(9.73,4.78),(9.938,4.78),(10.00,5.086),(9.68,5.076)]),.024,.153,IRON,'rainwater-hopper')
    f.line((9.85,5.075,.077),(9.82,top,.077),.043,IRON,8 if lod else 14,'upper-pipe')
    for z in (3.17,4.13,4.79):f.box(9.73+(z-2.52)*.10/2.26,z,.12,.046,.117,.049,IRON,'downpipe-collar')
    wing_end(b,lod)


def add_louvred_unit(b,f,lod):
    # A 2017 transect at native x=4425 records ten exposed slats, spaced
    # 17–18 px apart. The penultimate member visibly bends toward its middle.
    survey=json.loads((DATA.parent/'grille-third-station.json').read_bytes())
    corners=next(v for v in survey.values() if isinstance(v,dict) and 'bottom left' in v)
    tl,tr,bl,br=(corners[k]['three_station_xyz'] for k in ('top left','top right','bottom left','bottom right'))
    left,right=(tl[0]+bl[0])/2,(tr[0]+br[0])/2
    bottom,head=(bl[2]+br[2])/2,(tl[2]+tr[2])/2
    depth=REAR_Y-sum(p[1] for p in (tl,tr,bl,br))/4
    cx=(left+right)/2;cz=(bottom+head)/2
    f.prism(box(left,bottom,right,head).difference(box(left+.040,bottom+.031,right-.040,head-.053)),depth-.033,depth,LOUVER,'louvre/front-frame')
    f.box(cx,head-.024,right-left,.048,depth,depth/2,LOUVER,'louvre/top-return')
    # The casing, closely finned black coil and pale uprights are all visible
    # behind the screen on the original. A fan profile is concealed.
    f.box(cx-.018,cz-.018,(right-left)*.85,(head-bottom)*.84,.077,.037,SILL,'louvre/condensing-unit-case')
    f.box(cx-.055,cz-.02,.552,.503,.036,.093,DARK,'louvre/dark-heat-exchanger')
    fins=39 if not lod else 19
    for n in range(fins):
        a=cx-.313+.514*n/(fins-1)
        f.box(a,cz-.016,.0045 if not lod else .007,.49,.012,.114,IRON,'louvre/coil fins')
    for a in (left+.018,right-.018):
        f.box(a,(bottom+head)/2,.036,head-bottom,.042,depth-.021,LOUVER,'louvre/front-stile')
        f.box(a,(bottom+head)/2,.026,head-bottom,.030,.021,LOUVER,'louvre/wall-stile')
    for n in range(10):
        z=head-.095-n*(head-bottom-.135)/9
        sag=.028 if n==8 else 0.
        if sag:
            # Two sloping splits visibly follow the lowered centre of this member.
            for a,za,c,zc in ((left+.032,z,cx,z-sag),(cx,z-sag,right-.032,z)):
                f.prism(Polygon([(a,za-.012),(c,zc-.012),(c,zc+.012),(a,za+.012)]),depth-.034,depth-.001,LOUVER,'louvre/dropped horizontal slat')
        else:
            f.box(cx,z,right-left-.063,.023,.039,depth-.019,LOUVER,'louvre/horizontal-slat')
        for a in (left+.014,right-.014):
            f.box(a,z,.027,.022,depth-.049,depth/2-.002,LOUVER,'louvre/return slat')

def wing_end(b,lod):
    # The offset between the pipe's wall and the red timber reveal is
    # supported by the oblique station. Only this western return recedes.
    turn=Facade(b,(10.10,REAR_Y),(11.075,3.94),'western ochre return')
    turn.wall(0.,5.64,thickness=.17,material=UPPER)
    face=Facade(b,(11.075,3.94),(11.55,3.94),'western red timber opening')
    w=face.length
    for x in (-w/2+.024,w/2-.024):face.box(x,3.965,.048,2.99,.104,-.030,RED,'outside timber jamb')
    face.box(0,5.457,w,.083,.113,-.024,RED,'timber head')
    face.box(0,3.415,w,.083,.113,-.024,RED,'timber sill')
    face.box(0,3.004,w-.091,.725,.066,-.092,LOWER,'inset lower render panel')
    face.line((-.190,2.724,-.013),(.193,3.330,-.013),.027,RED,6 if lod else 8,'lower timber brace')
    outline=box(-w/2+.041,3.454,w/2-.041,5.418)
    inner=outline.buffer(-.036,join_style=2)
    face.prism(outline.difference(inner),-.112,-.069,GREEN,'green casement frame')
    face.prism(inner,-.135,-.123,GLASS,'shaded western glazing')
    for z in (4.05,4.60):face.box(0,z,w-.115,.026,.035,-.091,GREEN,'glazing rail')
    face.box(-.09,4.432,.018,1.86,.026,-.094,GREEN,'off-centre glazing bar')
    face.box(0,1.32,w,2.64,.16,-.074,UPPER,'concealed base at west cut')
