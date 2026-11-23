"""First-surface tests on the exported reliefs, including their real hollow incisions."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'source'))
sys.path.insert(0,str(ROOT.parent/'xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'))
from glb_triangles import SerialScene
from materials import PALE, SHADE
from scroll_panels import measured_layout

def samples(row):
    lintel = row['kind']=='lintel'
    h=row['height']
    depth=min(.055,.12*h)
    ridge=min(.037,.082*h)
    # Cross sections use the solid part of the central stem, the plate rim and a horizontal cut.
    section=[('plain upper rim',.50,.975,PALE,depth),
             ('inscribed horizontal line',.50,.88 if lintel else .887,SHADE,depth*.72),
             ('central foot',.50,.035,PALE,depth),
             ('left shoulder',.08,.38 if lintel else .70,PALE,depth),
             ('right shoulder',.92,.38 if lintel else .70,PALE,depth),
             ('left curl crest',.386 if lintel else .352,.448 if lintel else .45,PALE,depth+ridge),
             ('right curl crest',.614 if lintel else .648,.448 if lintel else .45,PALE,depth+ridge)]
    # At the two open corners the window plaque is narrow below; the overdoor is narrow above.
    for k,t in [('left',.09),('right',.91)]:
        section.append((k+' cut-away',t,.90 if lintel else .14,None,None))
    return section

def verify(mesh):
    scene=SerialScene(mesh)
    rows=[]
    for row in measured_layout():
        for name,u,v,material,projection in samples(row):
            x=row['x']+(u-.5)*row['width']
            z=row['z']+v*row['height']
            hit=scene.ray((x,-.70,z),(0,1,0),.75)
            observed=-hit['point_enu_m'][1] if hit else None
            if projection is None:
                ok=hit is None or hit['material'] not in [PALE,SHADE] or observed<.004
            else:
                ok=bool(hit and hit['material']==material and abs(observed-projection)<.001)
            rows.append(dict(plaque=row['id'],detail=name,centre=[x,z],expected_projection_m=projection,
                             expected_material=material,observed_projection_m=observed,
                             observed_material=hit['material'] if hit else None,passed=ok))
    return dict(file=mesh.name,sha256=hashlib.sha256(mesh.read_bytes()).hexdigest(),passed=sum(r['passed'] for r in rows),
                total=len(rows),checks=rows)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mesh',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    result=verify(args.mesh)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(result['passed'],result['total'],[(r['plaque'],r['detail']) for r in result['checks'] if not r['passed']])
    raise SystemExit(result['passed']!=result['total'])
