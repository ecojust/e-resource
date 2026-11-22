"""Estimate the grille plane from the three enamel numerals in two dated pictures."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image,ImageOps
from scipy.optimize import least_squares
from shapely.geometry import shape

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'source'))
from marconi_photo_plane import on_wall,pixel

def measure(photo):
    trace=json.loads((HERE/'portal-enamel-traces.json').read_text())
    source=json.loads((HERE/'portal-photo-traces.json').read_text())
    assert hashlib.sha256(photo.read_bytes()).hexdigest()==source['second']['sha256']
    image=np.asarray(ImageOps.exif_transpose(Image.open(photo)).convert('RGB'))
    front=[]
    for row in trace['outlines']:
        if row['field']=='numeral':
            c=shape(row['outline']).centroid
            front.append(pixel([c.x,trace['plane_y_m'],c.y]))
    front=np.array(sorted(front))
    trials=[]
    for threshold in (75,92,107):
        side=[]
        for x0,x1 in [(1943,1958),(1959,1974),(1974,1990)]:
            lum=image[4798:4838,x0:x1].astype(float)@np.array([.27,.54,.19])
            y,x=np.where(lum>threshold)
            side.append([x.mean()+x0,y.mean()+4798])
        def residual(y):
            return np.array([np.array(pixel(on_wall(*uv,y[0]),'2015_oblique'))-point
                             for uv,point in zip(front,side)])
        # Depth and height are separable to first order here. A small common
        # vertical mismatch remains in this lower part of the independent view.
        fit=least_squares(lambda y:residual(y)[:,0],[.80])
        joint=least_squares(lambda y:residual(y).ravel(),[.80])
        trials.append(dict(luminance_threshold=threshold,observed_2015_pixels=side,
                           depth_from_horizontal_m=float(fit.x[0]),full_2d_estimate_m=float(joint.x[0]),
                           reprojection_residual_xy_px=residual(fit.x).tolist()))
    return dict(facade_depth_m=round(trials[1]['depth_from_horizontal_m'],3),
                photo_centres_2017=front.tolist(),trials=trials,
                uncertainty='Estimated metric depth. Centroids reproduce the oblique horizontal alignment, with a common vertical mismatch near ten native pixels. The two photographs were taken two years apart.',
                source_2017=source['primary'],source_2015=source['second'])
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('photo_2015',type=Path)
    p.add_argument('output',type=Path)
    a=p.parse_args()
    a.output.write_text(json.dumps(measure(a.photo_2015),ensure_ascii=False,indent=1)+'\n')
