"""1930s shopfront proportions and the surviving 2024 stepped corner and steel crown."""
import math

import numpy as np
from shapely.geometry import LineString, Point, Polygon, box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from photo_architecture import Facade, opening

STONE='carved pale stone'
LIGHT='warm ivory facing stone'
SHADE='grey recessed spandrels'
JOINT='weathered limestone joints'
GOLD='golden bronze ornament'
BRASS='muted bronze relief'
FRAME='aged dark steel sash'
GLASS='smoky blue window glass'
SHOP='dark shopfront plate glass'
ROOF='grey flat roofing'
LIGHTGLASS='honey lantern glass'
PALETTE={
    STONE:{'color':[.795,.737,.611], 'roughness':.81},
    LIGHT:{'color':[.846,.8,.694], 'roughness':.78},
    SHADE:{'color':[.638,.592,.511], 'roughness':.85},
    JOINT:{'color':[.46,.44,.389], 'roughness':.93},
    GOLD:{'color':[.71,.52,.25], 'metallic':.54, 'roughness':.49},
    BRASS:{'color':[.42,.335,.206], 'metallic':.53, 'roughness':.48},
    FRAME:{'color':[.13,.134,.134], 'metallic':.47, 'roughness':.5},
    GLASS:{'color':[.193,.234,.246], 'metallic':.28, 'roughness':.32},
    SHOP:{'color':[.15,.145,.144], 'metallic':.29, 'roughness':.31},
    ROOF:{'color':[.374,.363,.34], 'roughness':.92},
    LIGHTGLASS:{'color':[.839,.602,.301], 'metallic':.18, 'roughness':.39}}
# Measured horizontal intersections of the fixed footprint, relative to the 3.885 m
# chamfer. The short return to the first northwest bend is preserved explicitly.
CHAMFER=1.9425
EAST=np.array([-17.8789,16.4746])
EAST_FRONT=np.array([-CHAMFER,0.])
NORTH_FRONT=np.array([CHAMFER,0.])
NORTH_BEND=np.array([10.2469,9.106])
NORTH_END=NORTH_BEND + (np.array([66.4382,74.7967])-NORTH_BEND)/86.445*22.60
OFFSET=np.array([3.,4.])
BODY=25.57
SILL_ROWS=((9.2,2.46),(12.75,2.03),(15.91,2.00),(19.11,2.00),(22.33,2.01))


def along(a,b,metres):
    return a+(b-a)*metres/np.linalg.norm(b-a)


def sash(f,ap,kind,lod):
    x,z,X,Z=ap.bounds
    glass=SHOP if kind in ('shop','arched') else GLASS
    f.prism(ap.buffer(.014,join_style=2),-.325,-.30,glass,kind+' glazing')
    inset=ap.buffer(-.063,join_style=2)
    bars=[]
    if kind in ('shop','arched'):
        bars.append(box((x+X)/2-.032,z,(x+X)/2+.032,Z))
    if not lod or kind=='shop':
        transom=Z-(.60 if kind=='shop' else .34)
        bars.append(box(x,transom-.024,X,transom+.024))
    panes=inset.difference(unary_union(bars)) if bars else inset
    f.prism(ap.buffer(-.010,join_style=2).difference(panes),-.22,-.145,FRAME,kind+' sash')
    if kind=='upper':
        f.box((x+X)/2,z-.035,X-x+.09,.07,.115,.024,LIGHT,'flat sash sills')


def gold_panel(f,u,w,z,lod):
    """Two-tone flared, stepped inlays above each of the shallow second-storey arches."""
    h=.89
    # The broad gold stone panel has a bowed base following the arch over its glazing.
    panel=Polygon([(u-w/2,z-.17),(u-w*.24,z-.01),(u,z+.03),(u+w*.24,z-.01),
                   (u+w/2,z-.17),(u+w/2,z+h),(u-w/2,z+h)])
    f.prism(panel,.027,.082,BRASS,'bowed bronze arch panels')
    for n in range(-2,3):
        lean=n*.065; px=u+n*w/5.9; bw=w*.078
        for k in range(2 if lod else 4):
            rows=2 if lod else 4
            z0=z+.015+k*h/rows; z1=z+.018+(k+1)*h/rows-.025
            d0=lean*(k/rows);d1=lean*((k+1)/rows)
            mark=Polygon([(px-bw/2+d0,z0),(px+bw/2+d0,z0),
                          (px+bw*.7+d1,z1),(px-bw*.7+d1,z1)])
            f.prism(mark,.084,.11,GOLD,'gilded fan inlays')
    f.box(u,z+h+.064,w+.105,.11,.16,.038,LIGHT,'moulding over inlaid panels')


def street_face(b,a,z,groups,lod,label,tower=False):
    f=Facade(b,a,z,label);pitch=f.length/groups;half=f.length/2
    cuts=[];windows=[];panels=[];groups_mid=[];upper={}
    def add(ap,kind):
        cuts.append(ap);windows.append((ap,kind))
    for j in range(groups):
        u=-half+(j+.5)*pitch
        groups_mid.append(u)
        add(opening(u,.17,pitch*.735,3.77),'shop')
        arched_centres=[u] if tower else [u-pitch*.205,u+pitch*.205]
        for pos in arched_centres:
            w=pitch*(.50 if tower else .374)
            add(opening(pos,4.66,w,3.15,arch=.36,segments=10 if lod else 18),'arched')
            panels.append((pos,w,7.84))
        narrow=[u+(n-.5)*pitch*.205 for n in range(2)] if tower else [u+(n-1.5)*pitch*.185 for n in range(4)]
        for pos in narrow:
            width=pitch*(.165 if tower else .150)
            for i,(base,height) in enumerate(SILL_ROWS):
                add(opening(pos,base,width,height),'upper')
                if i<4:upper[(pos,i)]=(width,base+height,SILL_ROWS[i+1][0])
    wall=f.wall(0,BODY,cuts,thickness=.34,material=STONE)
    for ap,kind in windows:sash(f,ap,kind,lod)
    for pos,w,h in panels:gold_panel(f,pos,w,h,lod)
    for (pos,_),(w,bottom,top) in upper.items():
        h=top-bottom-.22
        f.box(pos,(bottom+top)/2,w*.93,h,.075,-.003,SHADE,'inset sash spandrels')
        if not lod:
            for side in (-1,1):
                f.box(pos+side*w*.34,(bottom+top)/2,.029,h*.83,.053,.046,LIGHT,'raised spandrel reeds')
    for j in range(groups+1):
        u=-half+j*pitch
        # Each face ends in a half pier. Winches and retail banners are temporary.
        width=(.29 if j in (0,groups) else .56)
        centre=u+(.5*width if j==0 else -.5*width if j==groups else 0)
        f.box(centre,14.78,width,20.6,.17,.045,LIGHT,'continuous fluted stone piers')
        if not lod:
            for side in (-1,1):
                f.box(centre+width*side*.24,14.70,.03,20.3,.045,.139,STONE,'stepped pier fillets')
        for seam in np.arange(5.16,25.1,.83 if not lod else 1.66):
            f.box(centre,seam,width*.94,.026,.018,.135,JOINT,'pier course joints')
    for z0,h,depth,mat in ((.10,.17,.13,SHADE),(4.06,.16,.34,SHADE),(4.24,.20,.40,LIGHT),
                              (4.41,.085,.45,STONE),(24.99,.13,.15,LIGHT),(25.51,.14,.14,LIGHT)):
        f.beam(z0,h,depth,mat,width=f.length,label='shop lintel and coping')
    for u in groups_mid:
        # Low parapets of the wings are divided into rectangular capped sections.
        if not tower:f.box(u,25.61,pitch*.56,.28,.34,-.055,STONE,'stepped parapet panels')
    return f


def corner_shoulder(f,corner_at_end):
    """At both returns, the broad tower pier rises in three shallow set-backs."""
    w=f.length
    # The current street photograph shows pilasters stepping up level by level into
    # the corner. Each has a real top, side return and back above the lower wing.
    strips=[(0.,.27,25.91),(.27,.55,26.43),(.55,.80,27.04),(.80,1.,27.62)]
    for lo,hi,top in strips:
        u=-w/2+(lo+hi)*w/2
        if not corner_at_end:u=-u
        f.box(u,(BODY+top)/2,(hi-lo)*w+.009,top-BODY,.79,-.342,STONE,'tower shoulder ashlar')
        f.box(u,top+.024,(hi-lo)*w+.02,.053,.83,-.335,LIGHT,'tower shoulder copings')
        if top>26.30:
            f.box(u,26.06,(hi-lo)*w-.04,.025,.027,.060,JOINT,'shoulder stone joints')


def tower(b,lod):
    """Recessed two-tier octagonal shaft, active lantern cage and slender flagstaff."""
    c=np.array([.0,2.19])
    # The shaft is narrower above the main vertical paired window slots. A full ring of
    # drawn walls and caps closes each step on oblique and rooftop views.
    def octagon(width,depth,cut):
        w,h=width/2,depth/2
        return [c+v for v in [(-w+cut,-h),(w-cut,-h),(w,-h+cut),(w,h-cut),
                               (w-cut,h),(-w+cut,h),(-w,h-cut),(-w,-h+cut)]]
    def level(coords,base,top,glazed):
        for i,(a,d) in enumerate(zip(coords,coords[1:]+coords[:1])):
            f=Facade(b,a,d,'Northeast stepped tower/'+('axial' if i%2==0 else 'chamfer'))
            count=2 if i%2==0 else 1
            holes=[opening((n-(count-1)/2)*f.length*.34,base+.40,f.length*(.22 if count==2 else .36),
                           (top-base)*.55) for n in range(count)] if glazed else []
            f.wall(base,top,holes,thickness=.22,material=LIGHT)
            for ap in holes:sash(f,ap,'upper',lod)
            f.box(0,top-.025,f.length+.025,.054,.13,-.02,STONE,'narrow tier edge')
        b.plan_prism(Polygon(coords),top-.12,top,ROOF,'Northeast stepped tower/closed tier caps')
    # Tip is behind the chamfer's paired windows, as on the 2024 axial photograph.
    level(octagon(6.04,4.28,.90),25.50,27.71,True)
    level(octagon(4.82,3.75,.89),27.70,29.32,True)
    level(octagon(3.25,2.75,.65),29.31,30.47,False)
    level(octagon(1.91,1.87,.38),30.46,31.16,False)
    b.lathe(c,[(31.14,.67),(31.25,.67),(31.31,.55),(33.42,.52),(33.56,.61)],
            LIGHTGLASS,8,'Roof lantern/ochre glazing')
    for n in range(8):
        t=math.tau*n/8
        b.tube([(c[0]+.60*math.cos(t),c[1]+.60*math.sin(t),31.14),
                (c[0]+.54*math.cos(t),c[1]+.54*math.sin(t),33.51)],.045,BRASS,5 if lod else 8,'Roof lantern/corner mullions')
    for height in (31.49,31.88,32.33,32.79,33.26):
        pts=[(c[0]+1.12*math.cos(t),c[1]+1.12*math.sin(t),height)
             for t in np.linspace(0,math.tau,17 if lod else 33)]
        b.tube(pts,.029,BRASS,5 if lod else 7,'Roof lantern/large open circular hoops')
    for t in (0,math.pi/2,math.pi,3*math.pi/2):
        b.tube([(c[0]+1.12*math.cos(t),c[1]+1.12*math.sin(t),31.44),
                (c[0]+1.12*math.cos(t),c[1]+1.12*math.sin(t),33.42)],.024,BRASS,5,'Roof lantern/outside cage uprights')
    b.lathe(c,[(33.43,.6),(33.53,.59),(33.89,.10)],BRASS,8,'Roof lantern/cap')
    b.tube([(*c,33.79),(*c,35.28)],.042,FRAME,6 if lod else 10,'Roof lantern/flag staff')


def add_geometry(b,lod):
    east_shoulder=along(EAST_FRONT,EAST,3.46)
    north_shoulder=along(NORTH_FRONT,NORTH_BEND,3.58)
    street_face(b,EAST,east_shoulder,3,lod,'Shandong Road/window groups')
    east_return=street_face(b,east_shoulder,EAST_FRONT,1,lod,'Shandong Road/tower return',True)
    corner_shoulder(east_return,True)
    street_face(b,EAST_FRONT,NORTH_FRONT,1,lod,'Chamfer/paired window stack',True)
    north_return=street_face(b,NORTH_FRONT,north_shoulder,1,lod,'Nanjing Road/tower return',True)
    corner_shoulder(north_return,False)
    street_face(b,north_shoulder,NORTH_BEND,1,lod,'Nanjing Road/first window group')
    street_face(b,NORTH_BEND,NORTH_END,3,lod,'Nanjing Road/window groups')
    frontage=LineString([EAST,EAST_FRONT,NORTH_FRONT,NORTH_BEND,NORTH_END])
    # Model only the depth needed to close the photographed street fronts and tower.
    band=frontage.buffer(3.18,cap_style='flat',join_style='mitre',single_sided=True)
    b.plan_prism(band,BODY-.20,BODY-.07,ROOF,'Street fronts/roof behind parapet')
    for endpoint,direction in ((EAST,east_shoulder),(NORTH_END,NORTH_BEND)):
        p=np.asarray(endpoint); t=(direction-p)/np.linalg.norm(direction-p)
        inward=np.array([-t[1],t[0]]) if np.array_equal(endpoint,EAST) else np.array([t[1],-t[0]])
        q=p+3.18*inward
        f=Facade(b,q,p,'Section/short plain reveal')
        f.wall(0,BODY-.08,thickness=.123,material=SHADE)
    inner_edges=list(orient(band,sign=1.).exterior.coords)
    for a,end in zip(inner_edges,inner_edges[1:]):
        # The plain rear face closes the surveyed-depth section in the standalone
        # view. Its straight surface records a cut, with no invented shop fittings.
        if min(frontage.distance(Point(a)),frontage.distance(Point(end)))>1.:
            rear=Facade(b,a,end,'Section/plain inner cut')
            rear.wall(0,BODY-.08,thickness=.12,material=SHADE)
    tower(b,lod)
    for part in b.parts:
        part['vertices']=[(x-OFFSET[0],y-OFFSET[1],z)for x,y,z in part['vertices']]
