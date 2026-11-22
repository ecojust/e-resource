"""Check the outer material and relief of the architectural exhibit in its own coordinates."""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact'),str(HERE.parent/'source')]
from glb_triangles import SerialScene
import crown_masonry as clay

def check(mesh):
    layout=json.loads((HERE/'crown-layout.json').read_bytes())
    U=layout['display_units_per_plaque_width']
    scene=SerialScene(mesh);hits=[]
    def sample(label,origin,direction,material,expected=None):
        ray=scene.ray(np.array(origin)*U,direction,1.1*U)
        actual=ray['material'] if ray else None
        observed=round(float(ray['distance_m'])/U,6) if ray else None
        ok=actual==material and (expected is None or observed is not None and abs(expected-observed)<.003)
        hits.append(dict(part=label,material=actual,expected_material=material,depth_in_plaque_widths=observed,
                         expected_depth=expected,passed=ok))
    for x in layout['centre']['pier_x']:
        for dx in [-.060,-.033,.010,.059]:
            for z in [.75,.862,.989]:
                sample('Fluted pale end capital',[x+dx,-.75,z],[0,1,0],clay.LIGHT)
    for x in layout['centre']['fin_x']:
        for z in [-.030,.22,.66,.88,.958]:
            sample('Thin central folded rib',[x,-.75,z],[0,1,0],clay.LIGHT)
    for x in [-.82,-.61,-.33,0.,.32,.62,.79]:
        sample('Narrow parapet coping',[x,-.7,1.287],[0,1,0],clay.SILL,.694)
        sample('Ochre parapet above flutes',[x,-.7,1.045],[0,1,0],clay.PLASTER,.7)
    spec=layout['towers']
    for side in [-1,1]:
        edge=np.array(spec['front_outline_in_plaque_widths'])*[side,1]
        for a,b in zip(edge[1:-1],edge[2:]):
            t=b-a;dim=np.linalg.norm(t);t=t/dim;n=side*np.array([t[1],-t[0]]);mid=(a+b)/2
            start=mid+n*.20;direc=[-n[0],-n[1],0.]
            for z in [0.,.08,.145]:
                sample('Blind recessed tower panel',[*start,z],direc,clay.PLASTER,.225)
            for m in [-.32,.32]:
                point=start+t*(m*dim)
                sample('Full thickness beside recess',[*point,.08],direc,clay.PLASTER,.20)
            sample('Warm upper tower face',[*start,1.22],direc,clay.PLASTER,.20)
            sample('Stepped dark crown on every facet',[*(mid-n*.055),1.68],[0,0,-1],clay.CAP,1.68-spec['cap_top'])
        for i in spec['ribs_at_vertices']:
            a=edge[i]-edge[i-1];b=edge[i+1]-edge[i];t=a/np.linalg.norm(a)+b/np.linalg.norm(b);t/=np.linalg.norm(t)
            n=side*np.array([t[1],-t[0]])
            for z in [.02,.29,.59,.679]:
                sample('Pale tower arris',[*(edge[i]+n*.2),z],[-n[0],-n[1],0.],clay.LIGHT)
    return dict(passed=all(r['passed']for r in hits),asset=dict(sha256=hashlib.sha256(mesh.read_bytes()).hexdigest(),bytes=mesh.stat().st_size),
                triangles=len(scene.tri),hits=hits,units='Dimensionless local display ratios relative to the date cartouche width.')
