"""Triangulate the four upper north-window corners independently for April and December 2015."""
from pathlib import Path
import json,math
import numpy as np
HERE=Path(__file__).absolute().parent
def triangulate():
    controls=json.loads((HERE/'winter-camera-rays.json').read_bytes());origin=controls['marker_wgs84'];scale=np.array([111320*math.cos(math.radians(origin[1])),110890.]);out={}
    for epoch,stations in controls['same_epoch'].items():
        corners=[]
        for corner in range(4):
            left=[];right=[];rays=[]
            for station in stations:
                c=np.r_[(np.array(station['wgs84'])-origin)*scale,station['eye_height_m']]
                u,v=station['pixel_corners'][corner];f=400/math.tan(math.radians(station['horizontal_fov_deg']/2))
                az,p=map(math.radians,[station['bearing_deg'],station['pitch_deg']]);rightward=np.array([math.cos(az),-math.sin(az),0]);upward=np.array([-math.sin(az)*math.sin(p),-math.cos(az)*math.sin(p),math.cos(p)]);forward=np.array([math.sin(az)*math.cos(p),math.cos(az)*math.cos(p),math.sin(p)])
                direction=forward+rightward*(u-400)/f+upward*(360-v)/f;direction/=np.linalg.norm(direction);m=np.eye(3)-np.outer(direction,direction);left.extend(m);right.extend(m@c);rays.append((c,direction))
            x=np.linalg.lstsq(left,right,rcond=None)[0];corners.append(dict(enu=x.tolist(),line_misses_m=[float(np.linalg.norm(np.cross(x-c,t))) for c,t in rays]))
        xyz=np.array([p['enu']for p in corners])
        out[epoch]=dict(corners=corners,centre=xyz.mean(axis=0).tolist(),width_m=float((np.linalg.norm(xyz[1]-xyz[0])+np.linalg.norm(xyz[2]-xyz[3]))/2),height_m=float((np.linalg.norm(xyz[3]-xyz[0])+np.linalg.norm(xyz[2]-xyz[1]))/2))
    return out
if __name__=='__main__':print(json.dumps(triangulate(),indent=2))
