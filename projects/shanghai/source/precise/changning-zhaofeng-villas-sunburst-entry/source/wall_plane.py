"""Project the original inscription tracings into the surveyed wall plane."""
import json
from pathlib import Path
import numpy as np

HERE=Path(__file__).absolute().parent
survey=json.loads((HERE/'street-scale.json').read_bytes())
primary=json.loads((HERE/'close-camera.json').read_bytes())
previous=np.array(json.loads((HERE/'registered-name.json').read_bytes())['image_to_initial_xz'])
projection=np.array(primary['P'])
wall_y=survey['adjusted_curb_face_y_m']
wall_homography=np.column_stack([projection[:,0],projection[:,2],projection[:,3]+wall_y*projection[:,1]])
initial_to_wall=np.linalg.inv(wall_homography)@np.linalg.inv(previous)

def plane_xz(points):
    xy=np.atleast_2d(points)
    transformed=np.column_stack([xy,np.ones(len(xy))])@initial_to_wall.T
    return transformed[:,:2]/transformed[:,2,None]

def pixel_to_world(uv,depth):
    initial=previous@[*uv,1.]
    x,z=plane_xz(initial[:2]/initial[2])[0]
    return [float(x),wall_y-depth,float(z)]
