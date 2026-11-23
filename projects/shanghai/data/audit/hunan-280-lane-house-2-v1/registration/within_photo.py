"""Retain the cropped E3TR projection as a diagnostic and test the measured C3TR in photo 86."""
from pathlib import Path
import json
import numpy as np
import runpy

def check_measured_corner(mesh, views, measurements):
    from check_house_cameras import projection, project, HELPER
    from register_house import Camera
    survey=json.loads((measurements/'house-cameras.json').read_bytes())
    cameras=json.loads((measurements.parent/'source/cameras.json').read_bytes())
    view=next(v for v in cameras if v['name']=='street-windows')
    photo=Camera('86');width,height=photo.size
    trace=views['views']['street-windows']
    samples=trace['samples'];point=samples[-1]
    assert np.allclose(point['source'],photo.pixel(survey['points']['E3TR'])) and point['source'][0]>=width-.5
    trace['outside_source_image']={'landmark':'E3TR','source_size':list(photo.size),'original_result':samples.pop()}
    pixel=photo.pixel(survey['points']['C3TR'])
    assert -.5<pixel[0]<width-.5 and -.5<pixel[1]<height-.5
    scene=runpy.run_path(str(HELPER))['SerialScene'](mesh)
    original=scene.ray(photo.c,photo.ray(pixel),100.0)
    assert original is not None
    p=np.array(original['point_enu_m']);eye=np.array(view['eye'])
    v=scene.ray(eye,p-eye,100.);assert v is not None
    xy=project(projection(view),[p])[0]
    separation=float(np.linalg.norm(p-v['point_enu_m']))
    samples.append({'landmark':'C3TR','source':pixel.tolist(),'material':original['material'],'view_px':xy.tolist(),'first':v['material'],'obstruction_distance_m':separation,'in_frame':bool(0<=xy[0]<view['width'] and 0<=xy[1]<view['height']),'same_surface':separation<.085})
    return views
