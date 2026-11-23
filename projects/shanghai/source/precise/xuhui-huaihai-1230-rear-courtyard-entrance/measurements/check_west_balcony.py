"""Probe the component or full mesh directly at western-bay pixels picked from Masa25."""
from pathlib import Path
from argparse import ArgumentParser
import hashlib,json
from check_registered_court import Camera,SerialScene,near_offsets

HERE=Path(__file__).absolute().parent
POINTS=HERE/'west-balcony-photo-controls.json'
def match(h,role):
    if h is None:return False
    n=h['material'].lower()
    x,y,z=h['point_enu_m']
    if role=='grey base':return 'base and bands' in n
    if role=='pane':return 'glass' in n or 'glazing' in n
    if role=='side pane':return ('glass' in n or 'glazing' in n) and -3.92<x<-3.78 and y>-.72
    if role=='cast':return 'precast balcony' in n
    if role=='return':return 'precast balcony' in n and -3.92<x<-3.78 and y>-.78
    if role in ('recess','slit'):return y>.12
    if role=='dark opening':return 'shadowed recess' in n and y>.18
    raise ValueError(role)
def check(mesh,points=POINTS):
    s=SerialScene(mesh);c=Camera('25');rows=[]
    for pick in json.loads(points.read_text())['first_hit_controls']:
        x,y=pick['xy'];h=s.ray(c.c,c.ray((x,y)),75)
        good=match(h,pick['role']);offset=(0,0) if good else None
        if not good:
            offset=next(((dx,dy) for dx,dy in near_offsets(pick['tol_native_px'])
                         if match(s.ray(c.c,c.ray((x+dx,y+dy)),75),pick['role'])),None)
        rows.append({**pick,'exact_hit':h,'exact':good,'nearest_matching_native_offset':offset})
    return {'asset':s.asset,'controls_sha256':hashlib.sha256(points.read_bytes()).hexdigest(),
            'exact':sum(i['exact'] for i in rows),'within':sum(i['nearest_matching_native_offset'] is not None for i in rows),'total':len(rows),'rows':rows}
if __name__=='__main__':
    p=ArgumentParser(description=__doc__);p.add_argument('mesh',type=Path);p.add_argument('report',type=Path);p.add_argument('--points',type=Path,default=POINTS);a=p.parse_args()
    j=check(a.mesh,a.points);a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(j,indent=2)+'\n')
    print(j['exact'],j['within'],j['total'])
