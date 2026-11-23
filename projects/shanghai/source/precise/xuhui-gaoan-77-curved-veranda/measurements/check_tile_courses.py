"""Measure actual exposed noses of the front clipped-hip tiles on the supplied GLB."""
from pathlib import Path
import argparse,json,hashlib,sys,numpy as np
here=Path(__file__).resolve().parent
sys.path.insert(0,str(here))
from check_curved_veranda import SerialScene,settings
from curved_veranda import world

def verify(mesh,layout):
    p=settings(layout);scene=SerialScene(mesh);w=p['post_span']; fy=-p['fascia_projection_ratio'];back=p['ridge_setback_ratio']
    peak=p['ridge_height_ratio']; floor=.416+(peak-.416)*(1-.496/.809)
    slope=(peak-floor)/(back-fy)
    stations=[.151,.256,.355,.457,.565,.670,.778,.878,.957]
    rows=[]
    for index,t in enumerate(stations,2):
        y=fy+t*(back-fy);x=-.024+.09*.496*(1-t)
        readings=[]
        for dy in [-.0028,.0004,.0037]:
            target=world(p,x,y+dy,floor+(y+dy-fy)*slope)
            eye=(target[0],target[1],target[2]+w*.43)
            h=scene.ray(eye,(0,0,-1),w*.60)
            if not h:raise ValueError(f'Missing roof course {index}')
            readings.append(dict(offset_d_m=dy*w,height_above_pitch_m=h['point_enu_m'][2]-target[2],material=h['material']))
        step=readings[-1]['height_above_pitch_m']-readings[0]['height_above_pitch_m']
        rows.append(dict(course=index,fraction=t,readings=readings,step_m=step,positive_step=step>.004*w))
    return {'file':mesh.name,'sha256':hashlib.sha256(mesh.read_bytes()).hexdigest(),'timber_span_m':w,'courses':10,'measured_internal_edges':len(rows),'positive_edges':sum(r['positive_step']for r in rows),'observations':rows}

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mesh',type=Path);ap.add_argument('output',type=Path);ap.add_argument('--layout',type=Path)
    a=ap.parse_args();r=verify(a.mesh,json.loads(a.layout.read_text()) if a.layout else None);a.output.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(r['positive_edges'],r['measured_internal_edges'],[round(v['step_m'],3)for v in r['observations']])
