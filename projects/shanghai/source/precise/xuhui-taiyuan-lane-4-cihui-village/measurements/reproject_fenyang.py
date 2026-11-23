"""Reproject the measured opening edges into the original 900 × 620 street photograph."""
import argparse
import json
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
def reproject(measured):
    camera=np.asarray(measured['registered_2020_station_projections']['5'])
    rows=[]
    for face in measured['face_sections']:
        a=np.asarray(face['a']);direction=np.asarray(face['b'])-a
        direction/=np.linalg.norm(direction)
        for w in face['windows']:
            p=w['along_m'];half=w['width_m']/2;z0=w['sill_m'];z1=w['head_m']
            window={}
            for name,pixel in w['raw_pixels_5'].items():
                offset={'head':0,'sill':0,'left':-half,'right':half}[name]
                z={'head':z1,'sill':z0,'left':(z1+z0)/2,'right':(z1+z0)/2}[name]
                vec=camera@[*list(a+direction*(p+offset)),z,1]
                uv=vec[:2]/vec[2]
                # The horizontal reading is meaningful at the jamb. The head/sill reading is vertical.
                component=0 if name in ('left','right') else 1
                window[name]={'recorded':pixel,'projected':uv.round(3).tolist(),
                              'edge_residual_px':round(float(uv[component]-pixel[component]),3)}
            independent={}
            extras=measured.get('east_pair_revision',{}).get('station_11',{}).get(w['id'],{})
            street11=np.asarray(measured['registered_2020_station_projections']['11'])
            for name,pixel in extras.items():
                height={'head':z1,'sill':z0,'center':(z1+z0)/2}[name]
                vec=street11@[*list(a+direction*p),height,1]
                corresponding=vec[:2]/vec[2]
                independent[name]={'recorded':pixel,'projected':corresponding.round(3).tolist(),
                                   'delta_xy_px':(corresponding-np.asarray(pixel)).round(3).tolist()}
            rows.append({'shape':w['id'],'face':face['face'],'edges':window,'station_11':independent})
    return rows
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('output',type=Path);a=parser.parse_args()
    data=json.loads((HERE/'fenyang-wing-street-registration.json').read_bytes())
    a.output.write_text(json.dumps(reproject(data),indent=2,ensure_ascii=False)+'\n')
