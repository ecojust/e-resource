"""Recreate the primary gatehead camera poses from retained pixel and station measurements."""
from pathlib import Path
import json
import numpy as np
from scipy.optimize import least_squares

HERE=Path(__file__).resolve().parent
def reconstruct(record,name,parameters):
    v=record['views'][name];ang=np.radians(np.array(v['nominal_orientation'])+parameters[:3])
    a,p,r=ang
    look=np.array([np.sin(a)*np.cos(p),np.cos(a)*np.cos(p),np.sin(p)])
    right=np.array([np.cos(a),-np.sin(a),0.]);up=np.cross(right,look)
    rotation=np.array([right*np.cos(r)+up*np.sin(r),right*np.sin(r)-up*np.cos(r),look])
    width,height=v['size'];f=width/2/np.tan(np.radians(v['field_deg']/2))
    K=np.array([[f,0.,width/2],[0.,f,height/2],[0.,0.,1.]])
    en=(np.array(v['station_mc'])-record['local_grid_origin_mc'])*record['local_grid_m_per_mc']
    eye=np.r_[en,v['eye_height_m']-v['source_relative_grade_m']]+parameters[3:6]
    origin=np.r_[record['origin_east_north_m'],0.]
    return K@rotation@np.column_stack((record['axes_world_en'],origin-eye))

def calculate(record):
    matrices={}
    for name,row in record['views'].items():
        if 'reference_frame' in row:continue
        points=record['post_reference_points']
        def residual(p):
            m=reconstruct(record,name,p);out=[]
            for label,read in row['observed_base_pixels'].items():
                if label not in points:continue
                q=m@np.r_[points[label],1.];s=[1.9,2.6] if label.endswith('cap')else[2.8,3.1]
                out.extend((q[:2]/q[2]-read)/s)
            primary=name in ('center15','west15')
            prior=np.array([.65 if primary else 8.,1.8,1.,.18 if primary else 1.55,.18 if primary else 1.55,.16 if primary else .30])
            return np.r_[out,p/prior]
        fitted=least_squares(residual,np.zeros(6),loss='soft_l1')
        matrices[name]=reconstruct(record,name,fitted.x)
    for name,row in record['views'].items():
        if 'reference_frame' in row:
            matrices[name]=np.linalg.solve(row['to_reference'],matrices[row['reference_frame']])
    return matrices

if __name__=='__main__':
    record=json.loads((HERE/'zhengjia-entrance-cameras.json').read_bytes())
    matrices=calculate(record)
    delta=max(np.max(np.abs(m-np.array(record['views'][name]['projection'])))for name,m in matrices.items())
    print(f'{len(matrices)} registered perspectives, maximum matrix difference {delta:.6g}')
    if delta>1e-4:raise SystemExit('Primary solved matrices differ from the published calibration')
