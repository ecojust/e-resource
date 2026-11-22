"""Place the photographed courtyard wall in the frame of the two entrance piers."""
import json
from pathlib import Path
import numpy as np

MEASUREMENT=Path(__file__).resolve().parents[1]/"measurements/courtyard-to-entrance.json"
TRANSFORM=np.array(json.loads(MEASUREMENT.read_bytes())["matrix"])

def to_entrance(xyz):
    return np.asarray(xyz)@TRANSFORM[:3,:3].T+TRANSFORM[:3,3]

def add_courtyard(builder,lod=False):
    from courtyard_fabric import add_courtyard_fabric
    from courtyard_windows import add_windows
    start=len(builder.parts)
    add_courtyard_fabric(builder,lod)
    add_windows(builder,lod)
    for part in builder.parts[start:]:
        part["vertices"]=to_entrance(part["vertices"]).tolist()
