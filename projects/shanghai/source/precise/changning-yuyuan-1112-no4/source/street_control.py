"""Six panorama stations constrain the width and height of the projecting three-window elevation."""
import json
from pathlib import Path
import numpy as np

CONTROL=json.loads((Path(__file__).absolute().parents[1]/'measurements/forward-wing-constrained.json').read_bytes())
P=dict(zip(CONTROL['parameter_names'],CONTROL['parameters']))
SCALE=(P['roof_lip_height']-P['waist_upper_edge_height'])/(11.42-4.25)
OFFSET=P['waist_upper_edge_height']-4.25*SCALE
HINGE=5.53
WING_SCALE=P['waist_frontage_width']/9.45

def final_xyz(p):
    x,y,z=p
    return (HINGE*SCALE+(x-HINGE)*WING_SCALE if x>HINGE else x*SCALE,y*SCALE,z*SCALE+OFFSET)

def wing_registration():
    """Map the native 2020 front view to the provisional coordinate frame before its global adjustment."""
    west=np.array(CONTROL['control_points']['waist_west_outer_corner_top'][:2])
    tangent=np.array([np.cos(P['east_baseline_azimuth_from_east_radians']),np.sin(P['east_baseline_azimuth_from_east_radians'])])
    uv=[];xz=[]
    for key,obs in CONTROL['pixels'].items():
        p=next((v[1:] for v in obs if v[0]=='front-7-2002'),None)
        if p is None:continue
        e,n,z=CONTROL['control_points'][key]
        uv.append(p);xz.append([HINGE+(np.array([e,n])-west)@tangent/WING_SCALE,(z-OFFSET)/SCALE])
    return uv,xz

def apply(builder):
    for part in builder.parts:
        part['vertices']=[final_xyz(v)for v in part['vertices']]
    return builder
