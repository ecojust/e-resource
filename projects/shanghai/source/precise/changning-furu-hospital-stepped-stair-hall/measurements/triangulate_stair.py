"""Triangulate six independent steel-frame corners from three 2020 roadside stations."""
from pathlib import Path
import json,numpy as np
HERE=Path(__file__).absolute().parent
def solve():
    q=json.loads((HERE/'three-street-readings.json').read_bytes())
    stations=q['stations'];record=[]
    for i,name in enumerate(q['point_order']):
        rows=[];targets=[];lines=[]
        for tag,cam in stations.items():
            rotation=np.asarray(cam['R']);origin=np.asarray(cam['C']);uv=cam['picks'][i]
            ray=rotation.T@np.linalg.solve(cam['K'],[*uv,1]);ray/=np.linalg.norm(ray)
            normal=np.eye(3)-np.outer(ray,ray);rows.append(normal);targets.append(normal@origin)
            lines.append((tag,rotation,origin,np.asarray(cam['K']),np.asarray(uv)))
        p=np.linalg.solve(np.sum(rows,axis=0),np.sum(targets,axis=0));res={}
        for k,r,c,K,v in lines:
            a=K@r@(p-c);res[k]=dict(error_px=(a[:2]/a[2]-v).round(3).tolist())
        record.append(dict(name=name,xyz_from_poi=p.tolist(),reprojection=res))
    pairs=np.array([r['xyz_from_poi']for r in record]).reshape(3,2,3)
    ab=(pairs[:,1,:2]-pairs[:,0,:2]).mean(axis=0);L=np.linalg.norm(ab);axis=ab/L
    return dict(corners=record,measured_three_light_span_m=L,positive_x_bearing_deg=float(np.degrees(np.arctan2(*axis))%360),successive_same_corner_rises_m=np.diff(pairs[:,:,2],axis=0).tolist(),meter_note='Unadjusted three-camera rays. Native panorama positions, street camera heights and picked corners determine the conditional site scale. Published relocation of the institution in 2002 separates the archive plate from this 2020 frontage.')
if __name__=='__main__':
    a=solve();(HERE/'stair-survey-result.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n');print(a['measured_three_light_span_m'],a['positive_x_bearing_deg'],a['successive_same_corner_rises_m']);print([(r['name'],np.round(r['xyz_from_poi'],2).tolist(),r['reprojection']['centre'])for r in a['corners']])
