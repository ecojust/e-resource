"""Measure the exposed enclosure and rainwater head; preserve discrepancies between street stations."""
from pathlib import Path
import json
import numpy as np
from register_street import Camera

HERE = Path(__file__).parent
NAMES = ('2017','2015-12-front','2021-01-front')
GRILLE = {
    'top left': ((4372,1693),(855,511),(1155,473)),
    'top right': ((4686,1672),(932,512),(1263,468)),
    'bottom left': ((4387,1886),(856,571),(1160,544)),
    'bottom right': ((4700,1866),(933,573),(1271,539)),
}
def intersect(cameras, pixels):
    normals = []
    centres = []
    for camera, pixel in zip(cameras, pixels):
        ray = camera.ray(pixel)
        normals.append(np.eye(3) - np.outer(ray, ray))
        centres.append(normals[-1] @ camera.c)
    xyz = np.linalg.solve(sum(normals),sum(centres))
    return {'xyz':xyz.round(5).tolist(),'reprojection_error_px':{
        c.name:round(float(np.linalg.norm(c.pixel(xyz)-p)),2) for c,p in zip(cameras,pixels)}}

def run():
    cams = [Camera(n) for n in NAMES]
    report = {'source_views':list(NAMES),'front_y':1.94,'wall_y':2.20,
              'setback_uncertainty_m':.45, 'enclosure_corner_native_pixels':GRILLE,
              'description':'The model follows the 2017 original for the front of the projecting enclosure. Its depth is approximate. The two winter stations give different off-plane intersections from the 2017 and winter combined solution. All readings are retained. Pavement/window-wall measurements constrain the base camera registration more strongly than the side wing.',
              'shape_observations':'Ten pale slats are distinguishable on the 2017 enclosure, including a low slat which bows down between its ends. A dark, closely finned unit is visible through the openings behind it. The lower edge is partly covered by the foreground wall coping.',
              '2017_bright_peak_rows_at_native_x4425':[1695,1722,1740,1757,1775,1792,1810,1827,1846,1862,1880],
              'peaks_order':'Upper frame followed by ten repeated slats, last partly obscured. 2017 source luminance, mean of seven adjacent columns, Gaussian sigma 1 native pixel. The bent member departs from the regular pitch near its middle.',
              'points':{}}
    for feature, pixels in GRILLE.items():
        report['points'][feature] = {'anchored_2017':cams[0].wall(pixels[0],1.94).round(5).tolist(),
            'unconstrained_three_station':intersect(cams,pixels),
            'winter_pair':intersect(cams[1:],pixels[1:]),
            'front_plane_estimates':{c.name:c.wall(p,1.94).round(5).tolist()for c,p in zip(cams,pixels)}}
    report['other_2017_controls']={}
    for name, y, pts in (
        ('rainwater hopper sides and outlet',2.10,[(4869,1249),(4967,1236),(4883,1319),(4950,1317),(4980,1833)]),
        ('corner services upper and lower ends',0.,[(3252,1844),(3289,1841),(3321,1842),(3295,2510),(3343,2510)]),
        ('side wing dark sash right head and sill',2.20,[(3738,1444),(3753,1755)])):
        report['other_2017_controls'][name]=[{'pixel':p,'plane_y':y,'xyz':cams[0].wall(p,y).round(5).tolist()}for p in pts]
    (HERE/'recessed-wing-readings.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__ == '__main__':
    run()
