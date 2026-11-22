"""Reproject the original bearings onto the eight recorded 1,250 by 945 pixel rectilinear views."""
from pathlib import Path
import json
import numpy as np
def verify(directory):
    data=json.loads((directory/'west-courtyard-camera-registration.json').read_text());errors=[]
    for pt in data['features'].values():
        for reading in pt['observations']:
            cam=data['cameras'][reading['camera']];p=np.array(cam['P'])@np.r_[pt['xyz'],1.];uv=p[:2]/p[2]
            error=float(np.linalg.norm(uv-reading['uv']));assert abs(error-reading['fit_error_px'])<.0075,(pt,reading,error)
            errors.append(error)
    assert len(errors)==data['summary']['observations']
    return dict(stations=len(data['cameras']),landmarks=len(data['features']),observations=len(errors),median_px=round(float(np.median(errors)),3),maximum_px=round(max(errors),3))
if __name__=='__main__':print(json.dumps(verify(Path(__file__).resolve().parent),indent=1))
