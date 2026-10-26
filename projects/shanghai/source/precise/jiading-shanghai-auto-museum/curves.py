"""Museum-specific periodic cubic controls in metres, east/north/up.

The knots are explicit reconstruction estimates in calibration.json. They are
independent of the frozen OSM identity ring and never overwrite that ring.
"""
import math
import numpy as np
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient


def controls(knots, tension=.12):
    p=np.asarray(knots,float)
    if p.ndim!=2 or p.shape[1]!=2 or len(p)<4 or not np.isfinite(p).all():
        raise ValueError('At least four finite plan knots required')
    # Cardinal interpolation, converted to explicit cubic Bezier controls.
    # Its derivatives are shared at adjoining knots; actual polygon validity
    # and minimum curve radii are separately reported by the design audit.
    k=(1-float(tension))/6
    return np.asarray([[p[i],p[i]+k*(p[(i+1)%len(p)]-p[i-1]),
                        p[(i+1)%len(p)]-k*(p[(i+2)%len(p)]-p[i]),
                        p[(i+1)%len(p)]] for i in range(len(p))])


def cubic(c,t):
    return (1-t)**3*c[0]+3*(1-t)**2*t*c[1]+3*(1-t)*t*t*c[2]+t**3*c[3]


def sample(knots, step=.55):
    curves=controls(knots);points=[]
    for c in curves:
        length=sum(np.linalg.norm(c[i+1]-c[i]) for i in range(3))
        count=max(5,int(math.ceil(length/step)))
        points.extend(cubic(c,j/count) for j in range(count))
    polygon=Polygon(points)
    if not polygon.is_valid or polygon.area<1:
        raise ValueError('Estimated cubic plan must be a single valid polygon')
    return orient(polygon,sign=1.)


def smooth(t):
    t=np.clip(t,0.,1.)
    return t*t*(3-2*t)


def lower_roof_z(x,y,estimated):
    return float(estimated['lower_roof_base_m']
        +estimated['lower_roof_south_rise_m']*smooth((-y-7)/43)
        +estimated['lower_roof_east_rise_m']*smooth((x-12)/34))


def lower_band_z(x,y,band,estimated):
    width=estimated['lower_ribbon_transition_width_m'][band]
    # Front band turns upward near the shoulder of the south diagonal arm.
    # East-side return has its own gradual step, observed in the waterside view.
    front=smooth((-y-10)/width)
    rear=smooth((x-20)/20)
    return float(estimated['lower_ribbon_front_base_m'][band]
        +estimated['lower_ribbon_south_rise_m'][band]*front
        +(.55 if band==0 else 1.0)*rear)


def upper_band_z(x,y,estimated):
    a,b=estimated['upper_ribbon_transition_y_enu_m']
    # Higher toward the north end, lower toward the connecting shoulder.
    return float(estimated['upper_ribbon_low_m']
        +(estimated['upper_ribbon_high_m']-estimated['upper_ribbon_low_m'])
        *smooth((y-a)/(b-a)))
