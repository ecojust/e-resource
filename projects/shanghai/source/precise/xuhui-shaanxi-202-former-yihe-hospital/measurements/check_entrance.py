"""Read rays through the actual GLB at marks on the high-resolution 2018 photograph."""
from pathlib import Path
import argparse
import hashlib
import json
import runpy
import numpy as np
HERE=Path(__file__).absolute().parent
PROJECT=next(p for p in HERE.parents if (p/'data/audit/postal-office-v1/independent-glb-review-helpers.py').is_file())
MARKS=[
('barrel lip crown',169,13,['pale canopy moulding','grey metal barrel roof']),
('cream vault',155,48,['warm ivory vault']),
('canopy light',172,62,['aged lamp metal','amber opal glass']),
('tympanum field',180,125,['grey granite ashlar']),
('left stone pier',24,350,['grey granite ashlar']),
('right stone pier',308,350,['grey granite ashlar']),
('outer wood architrave',75,212,['dark stained surround']),
('transom central stile',166,237,['dark stained surround']),
('wood head over swinging leaves',161,254,['dark stained surround']),
('open central passage',166,388,['shaded vestibule','brown wood sash']),
('first warm globe',167,278,['illuminated vestibule globe']),
('second warm globe',165,315,['illuminated vestibule globe']),
('left grille',87,320,['pierced ornamental gate']),
('right grille',238,322,['pierced ornamental gate']),
('red mat',170,484,['muted red mat']),
('threshold outside the mat',88,500,['grey step granite','grey granite ashlar']),
('step at center',178,534,['grey step granite','grey granite ashlar']),
('lower step at center',179,567,['grey step granite','grey granite ashlar'])]
def check(mesh):
    api=runpy.run_path(str(PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))
    c=json.loads((HERE/'entrance-cameras.json').read_bytes())['close_view']
    inv=np.asarray(c['R']).T@np.linalg.inv(np.asarray(c['K']));eye=np.asarray(c['C'])
    scene=api['SerialScene'](mesh);rows=[]
    offsets=sorted((np.hypot(i,j),i,j) for i in range(-5,6) for j in range(-5,6) if np.hypot(i,j)<=5)
    for label,u,v,types in MARKS:
        materials=['Yihe | '+n for n in types];first=None;match=None
        for radius,dx,dy in offsets:
            direction=inv@np.r_[u+dx,v+dy,1.];direction/=np.linalg.norm(direction)
            h=scene.ray(eye,direction,24.)
            if radius==0:first=h
            if h and h['material'] in materials:
                match={'distance_px':float(radius),'offset_px':[dx,dy],'hit':h};break
        rows.append(dict(mark=label,pixel=[u,v],expected=materials,first=first,nearest=match))
    return dict(input_sha256=hashlib.sha256(mesh.read_bytes()).hexdigest(),working_size=c['size'],count=len(rows),
                direct=sum(bool(r['nearest'] and not r['nearest']['distance_px']) for r in rows),
                within_5px=sum(bool(r['nearest']) for r in rows),marks=rows)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mesh',type=Path);p.add_argument('report',type=Path)
    a=p.parse_args();d=check(a.mesh);a.report.write_text(json.dumps(d,indent=2)+'\n')
    print(d['direct'],d['within_5px'],d['count'],[r['mark'] for r in d['marks'] if not r['nearest']])
