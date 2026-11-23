"""Registered garden-corner coordinates before the independent street-scale comparison.

Bounds are (u_min,z_min,u_max,z_max). Meshes occupy the visible street and
entrance elevations. Positive depth is inward from the exposed pebbledash.
"""
from shapely.geometry import box

COURT_WINDOWS={
    'high landing window':(-8.31,5.02,-6.85,6.61),
    'landing louvres':(-8.51,1.37,-7.09,2.91),
    'stair upper light':(-5.14,4.42,-4.02,5.58),
    'stair side light':(-3.58,1.44,-3.04,2.29),
    'court upper sash':(-2.34,3.17,-.60,4.29),
    'court lower sash':(-1.78,.68,-.99,1.74),
}
STREET_WINDOWS={
    'near-open':(1.06,3.07,2.54,4.24),
    'attic-green':(3.95,4.62,5.58,5.54),
    'attic-pale':(6.65,4.52,8.00,5.44),
    'middle shutters':(3.96,2.66,5.73,3.82),
    'far shutters':(6.72,2.63,8.00,3.74),
    'garden lower divided sash':(1.06,.66,2.47,1.76),
    'screened lower opening':(3.64,.21,5.34,1.60),
    'far lower sash':(6.76,.48,7.93,1.58),
}
COURT_END=-9.08
STREET_END=8.65
DOOR_CENTER=-4.54
ARCH_BOTTOM=.61
ARCH_SPRING=2.23
ARCH_HEIGHT=2.54

def apertures(mapping):
    return {name:box(*bounds) for name,bounds in mapping.items()}
