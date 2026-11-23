"""The photographed twin-flight terrazzo stair and iron balustrade inside the rear stairwell."""
from math import pi,cos,sin
import numpy as np
from shapely.geometry import Polygon
from materials import TERRAZZO,IRON,WOOD,GREEN,WHITE,BAND
from plan import xy,trace,segment,LEVELS

def flight(b,x0,x1,y0,y1,z0,z1,n,lod,name):
    riser=(z1-z0)/n
    going=(y1-y0)/n
    profile=[(y0,z0+riser)]
    for i in range(n):
        y=y0+(i+1)*going
        profile.append((y,z0+(i+1)*riser))
        if i+1<n:profile.append((y,z0+(i+2)*riser))
    profile.extend([(y1,z1-.18),(y0,z0-.18)])
    b.prism(Polygon(profile),x0,x1,lambda y,z,x:(x,y,z),TERRAZZO,name+' terrazzo flight')
    if not lod:
        sign=1 if going>0 else -1
        for i in range(n):
            y=y0+i*going
            for dy in [.036,.066]:
                h=z0+(i+1)*riser+.003
                b.tube([(x0+.04,y+dy*sign,h),(x1-.04,y+dy*sign,h)],.006,IRON,6,name+' incised tread line')

def balustrade(b,x,y0,y1,z0,z1,lod,name):
    def p(t,h):
        return [x,y0+(y1-y0)*t,z0+(z1-z0)*t+h]
    def rail(line,r,material,detail):
        b.tube(line,r,material,6 if lod else 9,name+' '+detail)
    rail([p(0,.9),p(1,.9)],.042,WOOD,'rounded wooden handrail')
    for h in [.11,.21,.30,.86]:
        rail([p(0,h),p(1,h)],.011,IRON,'inclined iron flat')
    for t in [0.,.5,1.]:
        rail([p(t,.11),p(t,.88)],.015,IRON,'iron baluster')
    # Arched panels and scrolls are mounted between the narrow bars under the
    # handrail. Shapes stay in the sloping panel plane.
    for t in [0.,.5]:
        loop=[]
        for k in range(13 if lod else 25):
            u=k/(12 if lod else 24)
            loop.append(p(t+u*.35,.29+.36*sin(pi*u)))
        rail(loop,.010,IRON,'shallow fan arch')
        for f in [.114,.128,.243,.255]:
            rail([p(t+f,.233),p(t+f,.29+.36*sin(pi*f/.35))],.008,IRON,'fan uprights')
        diamond=[p(t+.177+(.018 if k%2 else 0),.27+k*.061) for k in range(7)]
        rail(diamond,.009,IRON,'fan concertina strip')
        coil=[]
        for k in range(13 if lod else 30):
            f=k/(12 if lod else 29)
            theta=(-.04+1.37*f)*2*pi
            rr=(1-.78*f)
            coil.append(p(t+.425+.058*rr*cos(theta),.575+.20*rr*sin(theta)))
        rail([p(t+.36,.29)]+coil,.011,IRON,'iron scroll')

def add_stairs(b,lod=False):
    left,right=xy(502,304)[0],xy(609,304)[0]
    mid=xy(551,304)[0]
    y0=xy(551,304)[1];y1=xy(551,195)[1]
    landing=trace([(501,194),(519,156),(588,156),(609,194)])
    lower_landing=trace([(500,326),(610,326),(610,304),(500,304)])
    for k,(low,high) in enumerate(zip(LEVELS,LEVELS[1:])):
        h=(low+high)/2
        n=8 if k==0 else 10
        name=f'level {k+1} rear stair'
        flight(b,left,mid-.055,y0,y1,low,h,n,lod,name+' outbound')
        flight(b,mid+.085,right,y1,y0,h,high,n,lod,name+' return')
        b.plan_prism(landing,h-.18,h,TERRAZZO,name+' angled half landing')
        b.plan_prism(lower_landing,high-.18,high,TERRAZZO,name+' upper threshold')
        balustrade(b,mid-.07,y0,y1,low,h,lod,name+' outbound')
        balustrade(b,mid+.09,y1,y0,h,high,lod,name+' return')
        curved=[(mid+.01-.08*cos(pi*i/12),y1+.08*sin(pi*i/12),h+.90) for i in range(13)]
        b.tube(curved,.042,WOOD,7 if lod else 11,name+' curved return')
    # Stair hall walls follow the angled end marked on the original drawing.
    # Internal paint is observed in the post-restoration photographs.
    outline=[(496,304),(496,191),(520,150),(592,150),(615,192),(615,304)]
    for a,c in zip(outline,outline[1:]):
        p,q=xy(*a),xy(*c)
        # Thin interior skins terminate below each slab. The two angled end
        # walls are part of the historical rear contour above the ground level.
        for floor,height in zip(LEVELS,LEVELS[1:]):
            if a==(520,150):
                # Opening in the back wall admits daylight on each landing.
                d=q-p
                for lo,hi in [(0.,.30),(.70,1.)]:
                    segment(b,p+d*lo,p+d*hi,floor,height,-.03,.03,WHITE,'rear stair window jamb')
                segment(b,p+d*.30,p+d*.70,floor,floor+.89,-.03,.03,GREEN,'stair window breast')
                segment(b,p+d*.30,p+d*.70,height-.43,height,-.03,.03,WHITE,'stair window lintel')
            else:
                segment(b,p,q,floor,floor+1.07,-.035,.035,GREEN,'stair hall dark painted dado')
                segment(b,p,q,floor+1.07,height,-.034,.034,WHITE,'stair hall white upper wall')
