"""Estimate shared tower elevations from the street and restored garden photographs."""
import argparse
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares

# The protected building's plan, the resolved dome edge and both photographs set scale.
# The oblique roof image spans roughly 4.2 m across the dome. The photographs resolve three garden-side facets. The central masonry face is estimated at 3.3 m. The obscured garden grade makes
# the first-floor belt less certain than the distances between the visible upper bands.
WIDTH = 3.30
FIRST_BELT = 4.50
# Local left-front, right-front and right-return coordinates refer to the visible
# pair of faces in each photograph. The garden and road observers see different sides.
PHOTOS = [
    {'source': 'Livelikerw, 2015, Commons 186 North Shanxi Rd. Shanghai.JPG',
     'size': [960,638], 'focal_from_exif_px': 960*37/36,
     'marks': {'first': [(0,416,469),(1,525,469),(2,565,479)],
               'upper': [(1,524,340),(2,561,356)],
               'cornice': [(0,414,226),(1,521,225),(2,565,247)],
               'parapet': [(0,429,202),(1,515,201),(2,552,225)],
               'tip': [(3,476,109)]}},
    {'source': 'Prada Group, garden elevation after restoration, image Gallery1_1rongzhai.jpg',
     'size': [950,448], 'focal_from_exif_px': None,
     'marks': {'first': [(0,162,354),(1,254,354),(2,319,370)],
               'upper': [(0,161,225),(1,254,224),(2,319,257)],
               'cornice': [(0,158,107),(1,253,104),(2,319,151)],
               'parapet': [(0,171,86),(1,253,84),(2,303,123)],
               'tip': [(3,250,12)]}},
]


def project(camera, point):
    angle, distance, eye_height, pitch, focal, cx, cy = camera
    azimuth, pitch = np.radians([angle, pitch])
    eye = np.array([distance*np.sin(azimuth), WIDTH/2-distance*np.cos(azimuth), eye_height])
    forward = np.array([-np.sin(azimuth)*np.cos(pitch), np.cos(azimuth)*np.cos(pitch), np.sin(pitch)])
    right = np.array([np.cos(azimuth), np.sin(azimuth), 0])
    up = np.cross(right, forward)
    ray = point-eye
    return np.array([cx + focal*(ray@right)/(ray@forward), cy - focal*(ray@up)/(ray@forward)])


def measure():
    def residuals(params, details=False):
        upper, cornice, parapet, head_rise = params[:4]
        tip = parapet + head_rise
        shoulder_x, shoulder_y, apex_y = params[18:21]
        band = {'first':(FIRST_BELT,.13), 'upper':(upper,.13), 'cornice':(cornice,.22),
                'parapet':(parapet,-.09), 'tip':(tip,0)}
        errors, records = [], []
        for i, photo in enumerate(PHOTOS):
            camera = params[4+7*i:11+7*i]
            for key, marks in photo['marks'].items():
                z, overhang = band[key]
                edge = WIDTH/2+overhang
                points = [(-edge,-overhang,z),(edge,-overhang,z),(edge+shoulder_x,shoulder_y,z),(0,apex_y,z)]
                for corner,x,y in marks:
                    expected = project(camera,np.array(points[corner]))
                    expected[1] += params[21+i] * (expected[0] - camera[5])
                    err = expected-[x,y]
                    errors.extend(err)
                    records.append({'photo':i,'band':key,'corner':corner,'marked':[x,y],
                                    'projected_px':expected.round(2).tolist(),'error_px':round(float(np.linalg.norm(err)),3)})
        # The street EXIF gives 37 mm equivalent. The published garden image has a wide crop.
        errors.extend([(params[8]-PHOTOS[0]['focal_from_exif_px'])/8,(params[6]-1.7)*2,
                       (tip-parapet-3.75)/.14, (shoulder_x-1.22)/.18, (shoulder_y-1.95)/.35])
        return records if details else errors

    initial=[8.7,12.5,13.2,3.7,12,32,1.7,9,987,477,325,24,30,3,10,800,236,272,1.25,1.80,2.2,0,0]
    lo=[7,10.5,11,2.90,0,18,.7,-10,850,355,100,0,15,1,-10,460,80,40,.65,1.0,1.5,-.28,-.28]
    hi=[11,15,16,4.2,58,65,3.5,25,1100,595,570,68,91,11,28,2000,463,565,1.9,3.3,2.9,.28,.28]
    sol=least_squares(residuals,initial,bounds=(lo,hi),loss='soft_l1',f_scale=4,max_nfev=1600)
    points=residuals(sol.x,True)
    e=np.array([r['error_px']for r in points])
    return {'method':'Shared elevations of the projecting faceted bay, estimated 3.30 m central face. The width range and chamfer are constrained by the garden colonnade, planted site outline and two roof views. The garden grade and absolute height are estimates. The 2015 original supplies 37 mm full-frame-equivalent EXIF.',
            'central_face_width_m':WIDTH,'return_x_y_m':np.round(sol.x[18:20],3).tolist(),'dome_axis_setback_m':round(float(sol.x[20]),3), 'assumed_first_belt_m':FIRST_BELT, 'photographs':PHOTOS,
            'fitted_elevations_m':dict(zip(('upper','cornice','parapet','finial'),np.round([*sol.x[:3],sol.x[2]+sol.x[3]],4))),
            'cameras':sol.x[4:18].tolist(), 'vertical_skew':sol.x[21:].tolist(), 'dome_height_prior_m':3.75, 'points':points, 'rms_px':round(float(np.mean(e**2)**.5),3),
            'median_px':round(float(np.median(e)),3), 'maximum_px':round(float(e.max()),3)}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('output',type=Path)
    args=parser.parse_args();report=measure();args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(report['fitted_elevations_m'],report['rms_px'],report['median_px'],report['maximum_px'])
