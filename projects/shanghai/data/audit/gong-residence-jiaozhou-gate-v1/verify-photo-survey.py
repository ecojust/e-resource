"""Replay the calibrated photographic elevation and the separate 2015/2020 station pairs."""
from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
import json
import numpy as np
from PIL import Image

def elevation(measurement):
    corners=np.asarray(measurement['controlled_aperture_pixels'])
    unit=np.array([[0,0],[1,0],[1,1],[0,1]],float)
    equations=[]
    for (x,y),(u,v) in zip(unit,corners):
        equations.extend([[x,y,1,0,0,0,-u*x,-u*y,-u],[0,0,0,x,y,1,-v*x,-v*y,-v]])
    h=np.linalg.svd(equations,full_matrices=True)[2][-1].reshape(3,3)
    h/=h[2,2]
    px=measurement['working_width']
    width,height=measurement['photograph']['size']
    focal=measurement['calibrated_focal_px']
    k=np.array([[focal,0,px/2],[0,focal,px*height/(2*width)],[0,0,1.0]])
    calibrated=np.linalg.solve(k,h)
    ratio=np.linalg.norm(calibrated[:,1])/np.linalg.norm(calibrated[:,0])
    assert abs(np.dot(calibrated[:,0],calibrated[:,1])/(np.linalg.norm(calibrated[:,0])*np.linalg.norm(calibrated[:,1])))<.006
    clear=measurement['known_clear_width_m'];heights={}
    for name,uv in measurement['pixel_samples'].items():
        xyw=np.linalg.solve(h,[*uv,1]);z=xyw[1]/xyw[2]*ratio*clear
        assert abs(measurement['heights_m'][name]-z)<1.e-7
        heights[name]=z
    assert abs(measurement['spring_height_m']-ratio*clear)<1.e-7
    return heights

def survey_pair(pair):
    first,second=pair['stations'];answers={}
    for mark in pair['meter_points']:
        rays=[]
        for image in (first,second):
            camera=np.asarray(image['station_xyz']);px,py=image['pixel_landmarks'][mark]
            x,z=np.asarray(image['origin_m'])+np.array([px,-py])/image['pixels_m']
            rays.append((camera,np.array([x,0,z])-camera))
        (a,u),(b,v)=rays
        depths=np.linalg.solve(np.column_stack((u[:2],-v[:2])),b[:2]-a[:2])
        assert min(depths)>0
        va,vb=a+u*depths[0],b+v*depths[1]
        point=(va+vb)/2;dz=float(abs(va[2]-vb[2]))
        old,old_dz=pair['meter_points'][mark]
        assert np.allclose(point,old) and abs(dz-old_dz)<1.e-8
        answers[mark]=point
    clear=np.linalg.norm((answers['ri']-answers['li'])[:2])
    assert abs(clear-pair['clear_span_m'])<1.e-7
    return float(clear)

def main():
    ap=ArgumentParser(description=__doc__);ap.add_argument('--survey',type=Path,required=True)
    ap.add_argument('--original-jpeg',type=Path);a=ap.parse_args();m=json.loads(a.survey.read_bytes())
    source=m['calibrated_elevation']['photograph']
    if a.original_jpeg:
        assert sha256(a.original_jpeg.read_bytes()).hexdigest()==source['sha256']
        with Image.open(a.original_jpeg)as photo:assert list(photo.size)==source['size']
    h=elevation(m['calibrated_elevation'])
    print('2015 outer coping, inner crown',h['outer_crown'],h['inner_crown'])
    print('separate station pairs',[(pair['date'],survey_pair(pair))for pair in m['independent_stereo']])

if __name__=='__main__':main()
