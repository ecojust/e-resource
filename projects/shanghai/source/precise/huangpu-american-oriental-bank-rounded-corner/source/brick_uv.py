"""Map the original brick atlas once across each full-height strip."""
from math import atan2, pi

def station(x,y,registration):
    cx,cy=registration['arc_center_m']
    radius=registration['arc_radius_m']
    sweep=registration['corner_sweep_deg']*pi/180
    theta=atan2(y-cy,x-cx)+pi/2
    if theta<=0:return x-registration['south_tangent_m'][0]
    if theta>=sweep:
        ex,ey=registration['east_tangent_m']
        tx,ty=registration['east_street_direction']
        return radius*sweep+(x-ex)*tx+(y-ey)*ty
    return radius*theta

def brick_uv(vertex,bounds,registration):
    left,right,low,high=bounds
    x,y,z=vertex
    clamp=lambda v:max(0.,min(1.,v))
    return clamp((station(x,y,registration)-left)/(right-left)),clamp((z-low)/(high-low))
