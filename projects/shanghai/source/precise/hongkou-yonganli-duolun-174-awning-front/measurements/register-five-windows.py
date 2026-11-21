"""Relate the five authored sash axes to three independently observed positions on Duolun Road."""
from pathlib import Path
import argparse,hashlib,json,math
import numpy as np

HERE=Path(__file__).parent
DIM=json.loads((HERE.parent/'source/dimensions.json').read_bytes())


def register(observations):
    obs=json.loads(observations.read_bytes());origin=np.array(DIM['central_axis_wgs84'])
    scale=np.array([111320*math.cos(math.radians(origin[1])),110950.])
    to_xy=lambda p:(np.array(p)-origin)*scale
    a=math.radians(DIM['yaw_enu_deg'])
    rot=np.array([[math.cos(a),-math.sin(a)],[math.sin(a),math.cos(a)]])
    rows=[]
    for name,u in zip(('north_second','north_first','over_lane','south_first','south_second'),DIM['sash_centres_u']):
        model=rot@np.array([0.,-u]);record=obs['points'][name];measured=to_xy(record['wgs84'])
        bearings=[]
        for m in record['observations']:
            cam=to_xy(m['camera_ll']);ray=model-cam;az=math.degrees(math.atan2(ray[0],ray[1]))%360
            diff=(az-m['azimuth']+180)%360-180
            bearings.append(dict(original_image_sha256=m['image_sha256'],station=m['station'],measured_azimuth=m['azimuth'],projected_model_azimuth=az,angular_residual_deg=diff,transverse_m=math.sin(math.radians(diff))*np.linalg.norm(ray)))
        rows.append(dict(axis=name,model_x_y_m=model.tolist(),measured_x_y_m=measured.tolist(),separation_m=float(np.linalg.norm(model-measured)),observations=bearings))
    diff=np.array([s['separation_m']for s in rows]);rr=np.array([d['transverse_m']for s in rows for d in s['observations']])
    return dict(source_dataset_sha256=hashlib.sha256(observations.read_bytes()).hexdigest(),axis_count=5,station_observations=15,upper_axis_wgs84=origin.tolist(),model_yaw_degrees=DIM['yaw_enu_deg'],extent='Five upper sash axes only. The geographic origin lies at the central sash. Relative intervals and camera positions are survey estimates.',axis_rms_m=float(np.sqrt(np.mean(diff**2))),max_axis_separation_m=float(max(diff)),three_station_cross_track_rms_m=float(np.sqrt(np.mean(rr**2))),rows=rows)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('measurements',type=Path);parser.add_argument('output',type=Path);o=parser.parse_args()
    r=register(o.measurements);o.output.write_text(json.dumps(r,indent=2)+'\n');print(r['axis_rms_m'],r['max_axis_separation_m'],r['three_station_cross_track_rms_m'])
