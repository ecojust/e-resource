"""Rotate each gate camera to a new view cut from the same recorded panorama."""
from pathlib import Path
import json
import numpy as np
from render_lintel import camera, OBS

D=Path(__file__).resolve().parent


def axes(az,pitch):
    a,t=np.radians([az,pitch])
    f=np.array([np.sin(a),np.cos(a),0.]);r=np.array([np.cos(a),-np.sin(a),0.]);z=np.array([0.,0.,1.])
    # Positive screen coordinates run to the right and down.
    return np.stack([r, f*np.sin(t)-z*np.cos(t), f*np.cos(t)+z*np.sin(t)])


def intrinsics(w,h,hfov):
    focal=w/(2*np.tan(np.radians(hfov)/2))
    return np.array([[focal,0,w/2],[0,focal,h/2],[0,0,1.]])


def main():
    layout=json.loads((D/'southern-lane-registration.json').read_bytes())
    details=json.loads((D/'southern-neighbouring-facades.json').read_bytes())
    out={}
    for name,v in details['winter_station_measurements'].items():
        idx=next(i for i,o in enumerate(OBS) if o['station']==v['station'])
        parent=OBS[idx];old=camera(idx,layout)
        k=intrinsics(v['width'],v['height'],v['horizontal_fov'])
        old_k=intrinsics(parent['width'],parent['height'],parent['hfov'])
        rotate=axes(v['azimuth'],v['pitch'])@axes(parent['az'],parent['pitch']).T
        H=k@rotate@np.linalg.inv(old_k)
        P=H@old
        original_eye=np.linalg.solve(-old[:,:3],old[:,3])
        eye=np.linalg.solve(-P[:,:3],P[:,3])
        if np.linalg.norm(eye-original_eye)>1e-7:raise ValueError('Station center moved')
        out[name]={'native_size':[v['width'],v['height']],'sha256':v['sha256'],'source_date':v['date'],
                   'station_id':v['station'],'local_camera_xyz':eye.tolist(),'local_xyz_to_image':P.tolist(),
                   'gate_frame_to_view_homography':H.tolist(),'gate_frame':parent['name']}
    (D/'southern-neighbouring-cameras.json').write_text(json.dumps(out,indent=1)+'\n')


if __name__=='__main__':
    main()
