"""Intersect the digitised photographs with the documented lane return, in metres."""
import hashlib
import json
from pathlib import Path
import numpy as np
from register_street import Camera

HERE = Path(__file__).resolve().parent
CORNER_X = 2.387216635
DX_DY = .076
END_Y = 7.1
def surface(xyz):
    return xyz[0] - CORNER_X - DX_DY * xyz[1]
def intersect(camera, pixel, outset=0):
    direction = camera.ray(pixel)
    return camera.c + (outset-surface(camera.c))/(direction[0]-DX_DY*direction[1])*direction
def observations():
    original = json.loads((HERE/'lane-return-source-pixels.json').read_bytes())
    rows = {}
    for name, views in original['samples_at_original_pixel_centres'].items():
        pts = {key: intersect(Camera(key), point) for key,point in views.items()}
        xyz = np.mean(list(pts.values()),axis=0)
        rays={k:Camera(k).ray(p) for k,p in views.items()}
        weights={k:(np.eye(3)-np.outer(ray,ray)) for k,ray in rays.items()}
        tri=np.linalg.lstsq(sum(weights.values()),sum(a@Camera(k).c for k,a in weights.items()),rcond=None)[0] if len(pts)>1 else None
        rows[name]={'registered_xyz_m':np.around(xyz,4).tolist(),
                    'two_ray_intersection_m':np.around(tri,4).tolist() if tri is not None else None,
                    'original_station_reprojection_px':{k:round(float(np.linalg.norm(Camera(k).pixel(xyz)-p)),2)for k,p in views.items()}}
    return rows
if __name__=='__main__':
    data={'camera_sha256':hashlib.sha256((HERE/'street-cameras.json').read_bytes()).hexdigest(),
          'wall_x_at_y0_m':CORNER_X,'wall_dx_per_y':DX_DY,'measured_end_y_m':END_Y,
          'plane_basis':'Street-front corner from the eight-station fit. The upper and intermediate window jambs and the far material junction are registered independently in the 2015 and 2018 photographs. The wall terminates before the adjoining pink facade.',
          'source_points':observations()}
    (HERE/'lane-return-metric.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
