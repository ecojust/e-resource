"""Test the photographed 2020 western street elevation against original and decoded GLBs."""
from pathlib import Path
import argparse
import hashlib
import json
import runpy
import numpy as np

HERE=Path(__file__).resolve().parent
SerialScene=runpy.run_path(str(HERE.parents[3]/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']

def camera(data,pixel,attitude=False):
    origin=np.array([121.453558,31.210602])
    c=np.r_[(np.asarray(data['eye_wgs84'])-origin)*[95180.,110867.],data['camera_height_m']]
    s=data['projection']
    yaw,pitch=np.radians([s['az'],s['pitch']])
    f=np.array([np.sin(yaw)*np.cos(pitch),np.cos(yaw)*np.cos(pitch),np.sin(pitch)])
    right=np.array([np.cos(yaw),-np.sin(yaw),0.])
    focal=s['width']*.5/np.tan(np.deg2rad(s['hfov']*.5))
    u,v=pixel
    direction=f+right*(u-.5*s['width'])/focal-np.cross(right,f)*(v-.5*s['height'])/focal
    if attitude and data.get("local_attitude_check"):
        direction=np.asarray(data["local_attitude_check"]["photo_to_enu_rotation"])@direction
    return c,direction/np.linalg.norm(direction)

def check(mesh,attitude=False):
    src=HERE/'street-window-photo-probes.json';q=json.loads(src.read_bytes())
    scene=SerialScene(mesh);readings=[]
    for t in q['controls']:
        station=q['stations'][t['station']]
        def hit(u,v):
            c,d=camera(station,[u,v],attitude);result=scene.ray(c,d,65)
            return result and result['material']
        u,v=t['pixel'];material=hit(u,v);match=t['expected'].lower()
        direct=bool(material and match in material.lower());offset=None
        if not direct:
            r=t['click_radius_px']
            offsets=sorted(((du,dv) for du in range(-r,r+1) for dv in range(-r,r+1) if 0<du*du+dv*dv<=r*r),key=lambda a:a[0]**2+a[1]**2)
            for du,dv in offsets:
                candidate=hit(u+du,v+dv)
                if candidate and match in candidate.lower():
                    offset=[du,dv];break
        readings.append(dict(**t,centre_material=material,centre_match=direct,offset=offset,within_tolerance=direct or offset is not None))
    return {'asset':scene.asset,'southern_station_attitude':'two independent controls' if attitude else 'vendor','frozen_source_controls':hashlib.sha256(src.read_bytes()).hexdigest(),'count':len(readings),'centre_matches':sum(r['centre_match']for r in readings),'within_radius':sum(r['within_tolerance']for r in readings),'observations':readings}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--south-attitude',action='store_true');p.add_argument('mesh',type=Path);p.add_argument('report',type=Path);a=p.parse_args()
    j=check(a.mesh,a.south_attitude);a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n')
    print(j['centre_matches'],j['within_radius'],j['count'],[(r['label'],r['centre_material'])for r in j['observations']if not r['within_tolerance']])
