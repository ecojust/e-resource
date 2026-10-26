"""Local photo-observed refinements; no edits to the frozen common generator.

All dimensions and sculptural relief depths are estimates. The original JPEG
is neither modified nor used to cover the wall or the whole bank emblem.
"""
import math
import numpy as np
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union
from shapely import affinity


def ground_window(fac,q,label):
    """Observed three columns, five rows; darker upper two, light lower three."""
    inner=q.buffer(-.09,join_style=2);x0,z0,x1,z1=inner.bounds
    # Approximate equal column widths; frame-free glass stays 20 mm behind frame.
    xs=np.linspace(x0,x1,4);zs=z0+(z1-z0)*np.array([0,.19,.39,.60,.80,1])
    panes=[]
    for row in range(5):
        for col in range(3):
            a=xs[col]+(.026 if col else 0);b=xs[col+1]-(.026 if col<2 else 0)
            lo=zs[row]+(.035 if row else 0);hi=zs[row+1]-(.035 if row<4 else 0)
            p=box(a,lo,b,hi);panes.append(p)
            material='ground upper dark glass' if row>=3 else 'ground curtained glass'
            fac.prism(p,-.20,-.18,material,label+f'-glass-r{row}-c{col}')
    frame=q.buffer(-.025,join_style=2).difference(unary_union(panes))
    fac.prism(frame,-.27,-.16,'bronze window frame',label+'-three-by-five-frame')
    fac.box((x0+x1)/2,z0-.16,x1-x0+.44,.14,.60,.10,label=label+'-sill')


def entrance_gate(fac,q,label):
    """Separate dark wrought gate in the observed central doorway, not a window."""
    x0,z0,x1,z1=q.buffer(-.10,join_style=2).bounds;cx=(x0+x1)/2;w=x1-x0;h=z1-z0
    inner=box(x0,z0,x1,z1)
    fac.prism(inner,-.25,-.23,'gate dark backing',label+'-dark-leaf-backing')
    bars=[q.buffer(-.025,join_style=2).difference(inner)]
    bars += [box(x-.013,z0,x+.013,z1) for x in np.linspace(x0,x1,11)]
    bars += [box(x0,z0+h*t-.027,x1,z0+h*t+.027) for t in [.13,.37,.67,.93]]
    bars.append(box(cx-.035,z0,cx+.035,z1))
    for leaf in [-1,1]:
        mid=cx+leaf*w*.25
        # Diagonal iron pattern is visible in the upper part and oval/lozenge below.
        for du in [-.15,0,.15]:
            bars.append(LineString([(mid+du-w*.18,z0+h*.69),(mid+du+w*.18,z0+h*.91)]).buffer(.012,cap_style=2))
            bars.append(LineString([(mid+du-w*.18,z0+h*.91),(mid+du+w*.18,z0+h*.69)]).buffer(.012,cap_style=2))
        ring=affinity.scale(Point(mid,z0+h*.37).buffer(1,quad_segs=28),w*.17,h*.15,origin=(mid,z0+h*.37))
        bars.append(ring.difference(ring.buffer(-.025)))
        diamond=Polygon([(mid,z0+h*.52),(mid+w*.15,z0+h*.37),(mid,z0+h*.22),(mid-w*.15,z0+h*.37)])
        bars.append(diamond.boundary.buffer(.016,join_style=2))
    grate=unary_union(bars).intersection(q.buffer(-.025,join_style=2))
    fac.prism(grate,-.205,-.145,'wrought iron',label+'-decorated-ironwork')
    for side in [-1,1]:
        fac.line((cx+side*.085,z0+h*.43,-.115),(cx+side*.085,z0+h*.56,-.115),.026,'gate old brass',label=label+'-handle')


def observed_crest(fac):
    """Layered approximate Garuda: feathers, raised arms, crown, knees and scroll.

    No claim of exact bank sculpture reproduction; visible silhouette/color only.
    Coordinates based on 2025 crop [3030,2140,3310,2530].
    """
    zc=7.23
    def solid(poly,lo,hi,mat,label):
        fac.prism(affinity.translate(poly,yoff=zc),lo,hi,mat,'bank-crest-'+label)
    # Widening wings with individually separate raised feather lobes.
    for side in [-1,1]:
        root=(side*.18,.07)
        for i in range(13):
            t=i/12; tip=(side*(.40+.83*t),.05+1.01*t**.70)
            start=(side*(.18+.27*t),-.07+.36*t)
            feather=LineString([start,tip]).buffer(.055-.018*t,cap_style=1)
            solid(feather,.466,.506,'crest feather bronze',f'wing-{side}-feather-{i}')
        arm=LineString([(side*.15,.42),(side*.56,.60),(side*.70,.81)]).buffer(.060,cap_style=1)
        solid(arm,.515,.575,'sign red',f'raised-arm-{side}')
        hand=Polygon([(side*.65,.77),(side*.68,.95),(side*.75,1.0),(side*.73,.83),(side*.81,.81)])
        solid(hand,.53,.59,'sign red',f'hand-{side}')
        thigh=LineString([(side*.10,-.18),(side*.49,-.29),(side*.26,-.46)]).buffer(.085,cap_style=1)
        solid(thigh,.52,.61,'crest feather bronze',f'bent-leg-{side}')
        # Gold lower talons and curled ends are based on visible color/outline.
        leg=LineString([(side*.25,-.43),(side*.30,-.62),(side*.53,-.54)]).buffer(.035,cap_style=1)
        solid(leg,.56,.625,'sign gold',f'talon-{side}')
    torso=Polygon([(-.19,.47),(.19,.47),(.24,.10),(.16,-.20),(-.16,-.20),(-.24,.10)])
    solid(torso,.53,.62,'sign red','torso')
    solid(Point(0,.61).buffer(.12,quad_segs=18),.55,.64,'sign red','head')
    crown=Polygon([(-.15,.67),(-.12,.89),(-.05,.96),(0,1.13),(.045,.96),(.12,.89),(.15,.67)])
    solid(crown,.57,.65,'sign gold','pointed-crown')
    for z in [.03,.34]:
        solid(box(-.20,z-.022,.20,z+.022),.622,.646,'sign gold','torso-gold-band')
    drape=Polygon([(-.16,-.19),(.16,-.19),(.13,-.45),(.25,-.57),(0,-.82),(-.25,-.57),(-.13,-.45)])
    solid(drape,.60,.65,'crest blue green','lower-drapery')
    for k in [-1,0,1]:
        solid(LineString([(k*.07,-.22),(k*.11,-.56),(0,-.75)]).buffer(.018,cap_style=2),.651,.669,'sign gold','drapery-trim')
    # Curved inscription scroll is relief geometry, not invented tiny lettering.
    points=[(.69*math.cos(t),-.50-.40*math.sin(t)) for t in np.linspace(0,math.pi,45)]
    scroll=LineString(points).buffer(.105,cap_style=1)
    solid(scroll,.49,.535,'crest blue green','curved-lower-scroll')
    for delta in [-.075,.075]:
        solid(LineString([(x,z+delta) for x,z in points]).buffer(.015,cap_style=1),.536,.56,'sign gold','scroll-edge')
    return {'type':'layered approximate observed Garuda','photo_crop_original_px':[3030,2140,3310,2530],'width_m':2.55,'height_m':2.14,'microcarving_and_scroll_inscription_unresolved':True}


def dense_perimeter(poly,step=.24):
    out=[];a=list(poly.exterior.coords)
    for p,q in zip(a[:-1],a[1:]):
        p=np.array(p);q=np.array(q);n=max(1,int(math.ceil(np.linalg.norm(q-p)/step)))
        out.extend(tuple(p+(q-p)*t) for t in np.linspace(0,1,n,endpoint=False))
    return out


def dense_cap_profile(crown_scale):
    # Monotone cubic Hermite through original silhouette controls, with fine
    # subdivisions. This changes faceting, not the nominated 24 m crown height.
    knots=np.array([[0,1,1],[.23,.95,.94],[.52,.79,.81],[.76,.54,.65],[.93,.27,.52],[1,.07,crown_scale]])
    t=knots[:,0];vals=knots[:,1:];slopes=np.diff(vals,axis=0)/np.diff(t)[:,None]
    tang=np.zeros_like(vals);tang[0]=slopes[0];tang[-1]=slopes[-1]
    for i in range(1,len(t)-1):
        for j in range(2):
            a,b=slopes[i-1,j],slopes[i,j];tang[i,j]=0 if a*b<=0 else 2*a*b/(a+b)
    out=[]
    for z in np.linspace(0,1,37):
        i=min(len(t)-2,int(np.searchsorted(t,z,side='right')-1));h=t[i+1]-t[i];u=(z-t[i])/h
        v=(2*u**3-3*u*u+1)*vals[i]+(u**3-2*u*u+u)*h*tang[i]+(-2*u**3+3*u*u)*vals[i+1]+(u**3-u*u)*h*tang[i+1]
        out.append((float(z),float(v[0]),float(v[1])))
    return out
