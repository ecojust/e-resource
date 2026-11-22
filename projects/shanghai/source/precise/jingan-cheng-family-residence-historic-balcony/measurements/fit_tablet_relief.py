"""Unproject the measured stone outlines onto their separate stepped face planes."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.optimize import minimize_scalar


def on_plane(P,uv,y):
    plane = np.column_stack((P[:,0],P[:,2],P[:,3]+P[:,1]*y))
    x,z,w = np.linalg.solve(plane,[*uv,1.])
    return np.array([x/w,y,z/w])


def pixel(P,xyz):
    q=P@np.r_[xyz,1.]
    return q[:2]/q[2]


def reconstruct(data,camera):
    P=np.array(camera['gao2018']['P'])
    mount_y=-.022  # Shallow plastered mount, overlapping the common Y=0 wall.
    # Separation normal to the visible straight edges, within the same stone slab.
    # There are no matched rear corners behind the hood. Its depth is approximate.
    offsets=[([1550,1077.3],1,6.6),([1666.9,972.0],0,4.1),([1570.,1076.9],1,6.2)]
    def displacements(d):
        out=[]
        for uv,axis,observed in offsets:
            front=on_plane(P,uv,mount_y-d)
            out.append((pixel(P,front+[0,d,0])[axis]-uv[axis],observed))
        return np.asarray(out)
    d=minimize_scalar(lambda depth:np.sum(np.diff(displacements(depth),axis=1)**2),bounds=(.025,.25),method='bounded').x
    # The optical separation includes the small cut bevel as well as the return.
    # Allow ~1 px for its face expansion before placing the rear shoulder.
    depth=round(float(d)-.019,3)
    planes={'mount':mount_y,'tablet':round(mount_y-depth,3),'hood':-.15,'cap':-.123,'plinth':-.145}
    outlines={'mount':[[1429,866],[1703,861],[1708,1087],[1428,1091]],
      'tablet':data['tablet_outline_native_px'],'hood':data['hood_front_fascia_outline_native_px'],
      'cap':data['hood_upper_cap_ridge_native_px'],
      'plinth':data['plinth_top_edge_native_px']+[[1721,1127],[1410,1134]]}
    mapped={key:np.round([on_plane(P,uv,planes[key])[[0,2]] for uv in points],6).tolist() for key,points in outlines.items()}
    return {'datum':camera['axes'],'2018_P':P.tolist(),'metric_scale_reference_m':camera['nominal_cap_z_m'],
            'metric_scale_note':camera['scale_basis'],'native_px':outlines,'xz_m':mapped,'front_planes_m':planes,
            'plinth_lip_evidence':{'outside_left_uv':[[1369,1095],[1389,1095]],'inside_left_uv':[[1437,1088],[1454,1089]],'inside_right_uv':[1690,1088],'outside_right_uv':[1732,1091],'adjacent_course_typical_y_m':-.090,'projection_in_front_of_adjacent_course_m':.055,'reading':'Both shoulders step up at the short stone and return to the continuous course. Horizontal highlight position combines a small raised lip with outwards relief; individual contributions are approximate.'},
            'edge_separations':[{'front_uv':uv,'component':'uv'[axis],'observed_px':obs,'calculated_px':round(float(est[0]),3)} for (uv,axis,obs),est in zip(offsets,displacements(d))],
            'relative_depth_fit_including_bevel_m':round(float(d),4),'relative_depth_after_bevel_m':depth,
            'depth_uncertainty_m':.04,'visible_profile':'Plain exposed-aggregate tablet with a small bevel, clipped corners, two ends beneath the lintel hood, a short pale cap and projecting plinth. Back faces are estimated. Faint variations on the historical tablet could not be read as text.',
            'rgb_percentiles_10_50_90':[{'rectangle':a,'rgb':b} for a,b in [([1510,938,1608,1009],[[140,142,130],[155,156,145],[171,172,161]]),([1465,821,1530,849],[[140,146,149],[150,157,160],[160,168,170]]),([1425,1104,1540,1125],[[164,161,142],[175,170,150],[183,177,157]])]]}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ['outline','camera','out']:p.add_argument(k,type=Path)
    a=p.parse_args();result=reconstruct(json.loads(a.outline.read_text()),json.loads(a.camera.read_text()))
    result['camera_file_sha256']=hashlib.sha256(a.camera.read_bytes()).hexdigest()
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=1)+'\n')
