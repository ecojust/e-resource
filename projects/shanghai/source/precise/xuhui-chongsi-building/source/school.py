"""South entrance axis, north projecting blocks and the restored Chongsi Building exterior."""
import math
import numpy as np
from shapely.geometry import box,Polygon,LineString
from shapely.ops import unary_union
from photo_architecture import Facade
from window_bays import BRICK,FIELD,STONE,BASE,SHUTTER,GLASS,DARK,ROOF,SEAM,PALETTE,arch_window,column,central_axis,panel
from mansard import HALF,DEPTH,EAVE,SECTIONS,roof,dormer,ornamental_gable

PIERS=(2.35,7.03,11.08,15.02,18.89,22.98,25.66,30.82,33.72)

def exterior_band(f,z,w,mat=BRICK):
    for dh,h,projection in [(0,.13,.19),(.10,.075,.25)]:
        panel(f,0,z+dh,w+.035,h,-.15,projection,mat,'moulded courses')

def span_windows(f,x0,x1,world_center,side,lod,north):
    width=x1-x0
    u=((x0+x1)/2-world_center)*side
    pair=width>3.50
    panes=([u-.85,u+.85] if pair else [u])
    if pair and width<4:panes=[u-.75,u+.75]
    ww=1.04 if pair else 1.12;holes=[]
    for level,(z,h) in enumerate([(1.07,3.18),(5.89,3.47),(10.63,3.39)]):
        for i,x in enumerate(panes):
            closed=not(level==2 and (round(abs((x0+x1)/2)/3)+i)%5 in (0,1))
            holes.append(arch_window(f,x,z,ww,h,lod,closed,label='paired sash'))
        if level==0 and not lod:
            # A cream garland joins the heads of ground-floor shutters under the raised brick stringcourse.
            for x in panes:
                curve=[f.point(x+t*.49,4.60-.19*math.cos(t*math.pi/2),.094)for t in np.linspace(-1,1,9)]
                f.builder.tube(curve,.043,STONE,5,f.label+'/stone swags')
                panel(f,x,4.38,.10,.14,.051,.13,STONE,'pendant stones')
    return holes

def main_wall(b,x0,x1,y,north,lod,idx):
    side=-1 if north else 1
    a=(x1,y)if north else(x0,y);c=(x0,y)if north else(x1,y)
    f=Facade(b,a,c,('North' if north else'South')+'/'+str(idx))
    ctr=(x0+x1)/2
    pts=sorted([-v for v in PIERS]+list(PIERS))
    holes=central_axis(f,lod)if x0<0<x1 else []
    for left,right in zip(pts,pts[1:]):
        center=(left+right)/2
        if x0<center<x1 and not left<0<right:
            holes.extend(span_windows(f,left,right,ctr,side,lod,north))
    fa=f.wall(.11,EAVE,holes,.34,FIELD)
    if not lod:
        # Shallow red brick frame fields at each paired opening. Mortar courses stay outside window apertures.
        for z in np.arange(.49,EAVE-.1,.38):
            strip=fa.intersection(box(-f.length/2,z-.007,f.length/2,z+.007))
            if strip.area>.0001:f.prism(strip,.001,.008,BASE,'masonry lines')
    for xx in pts:
        if x0<xx<x1:column(f,(xx-ctr)*side,lod)
    exterior_band(f,5.02,f.length); exterior_band(f,14.58,f.length)
    panel(f,0,14.78,f.length,.27,-.16,.25,BRICK,'brick entablature')
    panel(f,0,EAVE,f.length+.06,.13,-.23,.34,BASE,'slate eave')
    if idx in (0,2,4):
        xg=0 if idx==2 else -28.12 if idx==0 else 28.12
        ornamental_gable(f,(xg-ctr)*side,5.07 if idx==2 else 4.75,idx==2,lod)
    # The lower slope has alternating triangular/round pediments. Higher bull-eye dormers are smaller.
    window_positions=[-30.8,-21.1,-17.0,-12.97,-8.89,-3.78,3.78,8.89,12.97,17.0,21.1,30.8]
    for order,xx in enumerate(window_positions):
        if x0<xx<x1 and abs(xx)<28:dormer(f,(xx-ctr)*side,15.07,1.70,1.40,'round'if order%2==0 else'tri',.38,lod)
    for xx in (-28.16,-17.0,-8.94,-2.65,2.65,8.94,17.0,28.16):
        if x0<xx<x1:
            # Dormer front is near the upper pitch and its sill joins the roofing.
            dormer(f,(xx-ctr)*side,18.34,.94,.69,'tri',-1.78,lod)

def stair_tower(b,x,lod):
    # Independently identified in the protection designer's northern photograph.
    w=3.05;y0=21.40;y1=23.2;top=16.19
    f=Facade(b,(x+w/2,y1),(x-w/2,y1),'North/stair riser')
    q=[]
    for z in (1.70,5.03,8.35,11.63,14.68):
        for xx in (-.59,.59):
            q.append(arch_window(f,xx,z,.63,1.12 if z>14 else 1.99,lod,False,label='staggered lights'))
    f.wall(.15,top,q,.28,FIELD)
    for xx in (-w/2+.13,w/2-.13):
        panel(f,xx,top/2,.23,top,-.06,.08,BRICK,'stair corner strips')
    for xx in (-w/2,w/2):
        b.box((x+xx,(y1+y0)/2,top/2),(.16,y1-y0,top),BRICK,label='North/stair ends')
    b.box((x,(y1+y0)/2,top+.06),(w+.31,y1-y0+.36,.14),SEAM,label='North/stair eaves')

def build_on_footprint_grid(b,lod):
    for idx,(x0,x1,fy,by)in enumerate(SECTIONS):
        main_wall(b,x0,x1,fy,False,lod,idx)
        main_wall(b,x0,x1,by,True,lod,idx)
        # The ground-floor interiors are closed to outdoor navigation.
        b.box(((x0+x1)/2,(fy+by)/2,.095),(x1-x0,by-fy,.19),BASE,label='Foundation/raised masonry plinth')
        if idx:
            prev=SECTIONS[idx-1]
            for y0,y1 in ((prev[2],fy),(prev[3],by)):
                d=abs(y0-y1)
                if d>.06:
                    b.box((x0,(y0+y1)/2,EAVE/2),(.235,d,EAVE),BRICK,label='Wall/pavilion returns')
    for x in (-15.5,15.5):
        stair_tower(b,x,lod)
    for xx in (-HALF,HALF):
        # End elevations appear obliquely in the north/south reference pair; use restrained brick returns.
        side=1 if xx>0 else -1
        f=Facade(b,(xx,0)if side>0 else(xx,DEPTH),(xx,DEPTH)if side>0 else(xx,0),'East end'if side>0 else'West end')
        holes=[]
        for x in (-8.38,-4.16,0,4.16,8.38):
            for level,(z,h)in enumerate([(1.08,3.12),(5.85,3.43),(10.65,3.37)]):
                holes.append(arch_window(f,x,z,1.26,h,lod,level!=2,label='end opening'))
        f.wall(.11,EAVE,holes,.32,FIELD)
        for x in (-11.67,-6.25,-2.07,2.07,6.25,11.67):column(f,x,lod)
        exterior_band(f,5.02,f.length);exterior_band(f,14.6,f.length)
        panel(f,0,EAVE,f.length,.16,-.22,.27,BASE,'end cornice')
    for z,depth in [(.040,1.06),(.089,.72),(.132,.38)]:
        b.box((0,-depth/2-.04,z/2),(2.57,depth,z),BASE,label='South entrance/granite steps')
    roof(b,lod)

def model(b,lod):
    # The project survey gives 66.140 by 25.144 m between exterior wall axes.
    # The named mapping polygon has a slightly different envelope; retain its centre and bearing.
    build_on_footprint_grid(b,lod)
    east_scale=66.140/(2*HALF)
    north_scale=25.144/DEPTH
    centre=DEPTH/2
    for part in b.parts:
        part['vertices']=[(x*east_scale,centre+(y-centre)*north_scale,z*east_scale)
                          for x,y,z in part['vertices']]
