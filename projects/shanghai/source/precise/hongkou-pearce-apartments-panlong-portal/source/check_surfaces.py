"""Probe the photographed arch, open passage, remaining sidelights, title lettering and dentils."""
from pathlib import Path
from math import pi,cos,sin
import json, os, runpy
from shapely.geometry import shape
from panlong_portal import *
root=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',Path(__file__).resolve().parents[4]))
Reader=runpy.run_path(str(root/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
def check(reader):
    rows=[]
    def ray(label,x,z,material,lo,hi):
        origin=[float(x),-.75,float(z)];hit=reader.ray(origin,[0,1,0],1.5)
        ok=(hit is None) if material is None else bool(hit and hit['material']==material and lo<=hit['distance_m']-.75<=hi)
        rows.append(dict(part=label,origin=origin,hit=hit,passed=ok))
    for x in (-.61,0,.61):
        for z in (.12,1.2,2.54):
            ray('Open centre into passage',x,z,None,0,0)
    for side in (-1,1):
        x=side*(R-SIDE/2)
        ray('Recessed panel',x,.37,PANEL,.093,.104)
        ray('Panel border',x+SIDE/2-.082,.48,FRAME,.028,.039)
        ray('Transverse sidelight bar',x,SPRING-.159,FRAME,.064,.076)
        for z in (1.12,1.78,2.59):
            ray('Sidelight glazing',x+.085,z,GLASS,.165,.176)
            ray('Narrow sidelight mullion',x-.195,z,FRAME,.068,.089)
        ray('Solid top transom across each side',x,SPRING-.031,FRAME,.047,.057)
        ray('Darker plinth',side*1.88,.245,FOOT,-.022,-.004)
        for h in (.84,2.25):
            ray('Moulded straight jamb',side*(R+.09),h,BEAD,-.069,-.059)
    for pos in (.18,.35,.59,.795):
        a=pi*pos
        for offset,mat,depth in ((.088,BEAD,-.064),(.138,BEAD,-.043),(.184,BEAD,-.026)):
            ray('Nested segmental arch',cos(a)*(R+offset),SPRING+sin(a)*(RISE+offset),mat,depth-.012,depth+.012)
    for t in (.115,.235,.365,.48,.59,.73,.865):
        a=pi*t
        ray('Radial fan spoke',.65*R*cos(a),SPRING+.65*RISE*sin(a),FRAME,.072,.106)
    for t in (.173,.30,.415,.533,.65,.792,.914):
        a=pi*t
        ray('Separate fanlight panes',.67*R*cos(a),SPRING+.67*RISE*sin(a),GLASS,.156,.172)
    for j in range(39):
        ray('Individual cornice dentil',(j-19)*.101,4.398,BEAD,-.131,-.117)
    ray('Green enamel address',R-.282+.102,2.33,GREEN,.005,.013)
    for r in json.loads(Path(__file__).with_name('letter-contours.json').read_bytes()):
        g=shape(r['geometry']);g=max(getattr(g,'geoms',[g]),key=lambda p:p.area)
        shrunk=g.buffer(-.0015);point=(shrunk if not shrunk.is_empty else g).representative_point()
        ray(r['group'],point.x,point.y,r['material'],r['front']-.004,r['front']+.004)
    return dict(passed=all(i['passed']for i in rows),samples=rows)
