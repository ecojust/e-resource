"""Local brick and coping coordinates shared by GLB export and Blender reopening."""
from math import cos, pi, sin

PALE="Weathered coping stone"

def texture_coordinates(material,position,label):
    x,y,z=position
    if label.startswith('Hex '):
        i=int(label[4]);theta=(195+60*i+30)*pi/180;t=(-sin(theta),cos(theta))
        across=x*t[0]+y*t[1]
    elif label.startswith('End wall cut return'):
        across=y
    else:
        across=x
    if material==PALE:
        return .45+across/25,(z%1.64)/1.64 if ('sloping parapet' not in label) else .10+(z-15.48)/2.08
    return .34+across/21.50,(z+.30)/19.3

