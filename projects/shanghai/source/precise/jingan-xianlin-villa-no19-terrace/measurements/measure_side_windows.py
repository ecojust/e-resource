"""Rectify original photograph picks and estimate depth from the return at each head."""
import json
from pathlib import Path
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'source'))
from courtyard_photo_plane import CAMERA, on_side, pixel

def measure(row):
    corners=np.array([on_side(*xy) for xy in row['front_opening_px']])
    left=(corners[0,0]+corners[3,0])/2
    right=(corners[1,0]+corners[2,0])/2
    bottom=(corners[2,2]+corners[3,2])/2
    top=(corners[0,2]+corners[1,2])/2
    camera=np.array(CAMERA['camera_origin_xyz_m'])
    front=np.array([left,0,top])
    rear_pixel=row['rear_upper_left_px']
    rear=np.array(on_side(*rear_pixel))
    # At the same upper-left arris, the rear point lies on a line normal to the wall.
    # The remaining residual includes moulding width and reading the two visible edges.
    direction=(rear-camera)/(-camera[1])
    component=direction[[0,2]]
    depth=float(np.dot((front-rear)[[0,2]],component)/np.dot(component,component))
    individual=np.divide((front-rear)[[0,2]],component).tolist()
    square_return_depth=depth
    depth=individual[0]
    rear_head=on_side(*rear_pixel,depth)[2]
    rear_sill=on_side(*row['rear_sill_left_px'],depth)[2]
    fitted_px=pixel([left,square_return_depth,top])
    features={}
    for name,xy in row['source_detail_px'].items():
        surface=0 if name.startswith(('jamb','cap','sill','apron')) else depth
        features[name]=on_side(*xy,surface)
    return dict(key=row['key'],title=row['title'],left=left,right=right,bottom=bottom,top=top,
        frame_depth_m=depth,rear_head_z_m=rear_head,rear_sill_z_m=rear_sill,square_return_depth_m=square_return_depth,horizontal_vertical_depth_estimates_m=individual,depth_tie_residual_px=float(np.linalg.norm(np.array(fitted_px)-rear_pixel)),features=features)

if __name__=='__main__':
    obs=json.loads((HERE/'side-window-pixels.json').read_text())
    rows=[measure(row) for row in obs['observations']]
    data=dict(windows=rows,depth_method='Intersect the rear upper-left jamb ray with the X of its front masonry jamb. At that depth, the separate photographed inner head and sill define their actual height. Compare with a square, level reveal and report its residual; single-image frame depth remains an estimate.',
              unit='metres, estimated from the photographed brick courses',camera_sha256=__import__('hashlib').sha256((HERE/'courtyard-camera.json').read_bytes()).hexdigest())
    (HERE/'side-window-measurements.json').write_text(json.dumps(data,indent=2)+'\n')
    for row in rows:
        print(row['key'],*[round(row[k],3)for k in ('left','right','bottom','top','frame_depth_m','depth_tie_residual_px')],row['horizontal_vertical_depth_estimates_m'])
