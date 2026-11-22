"""Position the independently measured Lane 244 exhibit in the Lane 212 coordinate system."""
from pathlib import Path
import json
import numpy as np
from lane_244 import add_244
D=Path(__file__).resolve().parents[1]/'measurements'
def location():
    source=json.loads((D/'lane-244/placement-from-212.json').read_bytes())
    m=np.array(source['local_transform_matrix_xyz1'],dtype=float)
    primary=json.loads((D/'212-and-244-placement.json').read_bytes())
    m[:3,3]=primary['244_plaque_foot_in_212_xyz_m']
    return m
def add_second_entry(builder,lod=False):
    start=len(builder.parts);add_244(builder,lod)
    m=location()
    for part in builder.parts[start:]:
        part['vertices']=(np.asarray(part['vertices'])@m[:3,:3].T+m[:3,3]).tolist()
