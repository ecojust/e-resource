"""Reproject measured features of the Changning district photograph into its 438 by 678 frame."""
import json
from pathlib import Path
import sys
import numpy as np
from red_corner import pos, roof_point, WINDOWS, BELTS, PLINTH, DRAIN_S, CROWN_LIFT

CAMERA=(.03566565,.406697321,.03393846,-.167055085,-6.00084968,1.10536908,489.272452)
# Values are azimuth, elevation, roll in radians, three local metre positions and focal length in pixels.
def project(point):
    az,elevation,roll,ex,ey,ez,focal=CAMERA
    forward=np.array((np.sin(az)*np.cos(elevation),np.cos(az)*np.cos(elevation),np.sin(elevation)))
    right=np.array((np.cos(az),-np.sin(az),0.));up=np.cross(right,forward)
    r=right*np.cos(roll)+up*np.sin(roll);u=-right*np.sin(roll)+up*np.cos(roll)
    ray=np.asarray(point)-[ex,ey,ez];depth=ray@forward
    return np.array([219+focal*(ray@r)/depth,339-focal*(ray@u)/depth])

def measure():
    rows=[]
    def record(label,point,pixels,axes='xy',held=False):
        pred=project(point);delta=pred-np.array(pixels)
        error=float(np.linalg.norm(delta)) if axes=='xy' else float(abs(delta[1]))
        rows.append(dict(feature=label,world_xyz_local_m=list(point),source_px=pixels,model_px=pred.tolist(),axes=axes,withheld=held,error_px=error))
    for i,xy in enumerate([[(188,541),(220,542),(223,477),(190,477)],[(52,525),(73,527),(81,469),(61,473)],[(79,387),(115,376),(121,326),(89,340)],[(108,257),(128,252),(136,213),(114,224)]]):
        l,r,lo,hi=WINDOWS[i]
        for k,((s,z),pixel) in enumerate(zip([(l,lo),(r,lo),(r,hi),(l,hi)],xy)):
            record('Masonry reveal '+str(i+1)+' corner '+str(k+1),pos(s,z,-.11),pixel,held=i*4+k in [1,5,11,14])
    for z,pixels in [(0,(119,660)),(BELTS[0][0],(146,408)),(BELTS[1][0],(169,163))]:
        record('Downpipe elevation '+str(z),pos(DRAIN_S,z,.08),pixels)
    for name,z,y in [('Plinth',PLINTH,609),('Lower band soffit',BELTS[0][0],408),('Lower band coping',BELTS[0][1],347),('Upper band soffit',BELTS[1][0],147),('Upper band coping',BELTS[1][1],113)]:
        record(name,pos(0,z,.08),(208,y),'y')
    record('Upper corner coping',roof_point(0,8.98+CROWN_LIFT,.23),(226,22))
    held=[r['error_px']for r in rows if r['withheld']]
    tested=[r['error_px']for r in rows];assert len(rows)==25 and np.max(held)<5 and np.max(tested)<6
    return dict(source_url='https://www.shcn.gov.cn/col7698/20211207/1151493.html',photo_sha256='0ccbfeed125e78baea2ff535f1a737850ea7931f6f0c2cae2dbcac9cef9ff0b7',original_size=[438,678],coordinate_origin='upper-left',local_camera=CAMERA,control_count=len(rows),withheld_count=len(held),rms_error_px=float(np.sqrt(np.mean(np.square(tested)))),withheld_rms_px=float(np.sqrt(np.mean(np.square(held)))),max_withheld_px=max(held),controls=rows,measurement_limit='Single-photo proportional fit. Four preselected window corners were excluded from fitting. Band checks measure height in pixels. Camera and scale are local reconstruction estimates.')
if __name__=='__main__':Path(sys.argv[1]).write_text(json.dumps(measure(),indent=2)+'\n')
