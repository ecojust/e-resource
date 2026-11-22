"""Check arch joints, real passageways, shafts and gaps against the whole delivered mesh."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'source'),str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact')]
from glb_triangles import SerialScene
import garden_arcade as g

def inspect(path):
    scene=SerialScene(path);results=[];photo=[]
    def read(o,d):
        return scene.ray(np.array(o),np.array(d),65)
    def check(o,dir,mats,label):
        hit=read(o,dir);mat=hit['material'] if hit else None
        passed=bool(mat in mats) if mats else hit is None or hit['distance_m']>.85
        results.append(dict(feature=label,expected=sorted(mats) or ['clear beyond the back of the front wall'],
            from_m=np.array(o).round(4).tolist(),first=mat,distance_m=round(hit['distance_m'],4) if hit else None,matched=passed))
    for a in g.ARCHES:
        ts=np.radians(a['joint_angles_degrees']);num=a['index']
        for j,(l,r) in enumerate(zip(ts,ts[1:])):
            t=(l+r)/2;x,z=g.edge(a,t,.234)
            check([x,-.38,z],[0,1,0],[g.RINGS[a['brick_tone'][j]]],f'{num} radial brick {j+1}')
        for j,t in enumerate(ts[1:-1]):
            x,z=g.edge(a,t,.20)
            check([x,-.38,z],[0,1,0],[g.JOINT],f'{num} mortar joint {j+1}')
        for t in np.linspace(.13,3.0,13):
            x,z=g.edge(a,t,-.13);check([x,-.34,z],[0,1,0],[],f'{num} clear intrados')
        for x in np.linspace(a['left']+.13,a['right']-.13,5):
            for z in [1.0,1.72,2.15]:check([x,-.34,z],[0,1,0],[],f'{num} passage')
    # The stem spans the measured height; its gaps must pass the rail plane.
    for n,first in enumerate(g.SECTIONS['balustrade']['front_first_shaft_centres_on_Y0_m'],1):
        spacing=.431 if first>8 else .435;cs=[u+(u+1.374)*g.SHAFT_Y/12.703 for u in (first+spacing*np.arange(7))]
        for x in cs:check([x,-.38,5.62],[0,1,0],[g.SPINDLE],f'south bay {n} turned stem')
        for x0,x1 in zip(cs,cs[1:]):check([(x0+x1)/2,-.38,5.72],[0,1,0],[],f'south bay {n} baluster gap')
    for i,y in enumerate(np.linspace(.84,3.20,6),1):check([-.38,y,5.62],[1,0,0],[g.SPINDLE],f'west return shaft {i}')
    cams=json.loads((HERE/'arcade-cameras.json').read_text())
    # Independently chosen, high-contrast visible surfaces in the 1080 and 600
    # pixel garden views. A point inside an arch can legitimately hit the wall
    # beyond the arcade; its first contact must be behind the masonry thickness.
    checks={'13':{'brick':[(117,978),(125,1068),(488,982),(500,1035),(780,995),(776,1050)],
                 'opening':[(217,1000),(310,1030),(406,999),(570,989),(635,1015),(705,1030),(839,980),(896,968)],
                 'fan':[(286,799),(316,778),(386,808),(540,889),(625,807),(898,823)],
                 'cap':[(264,576),(400,597),(605,630),(542,746),(715,760)]},
            '8':{'brick':[(252,565),(255,653),(481,576),(483,651)],
                 'opening':[(95,588),(162,622),(307,590),(377,667),(545,622)],
                 'fan':[(106,476),(136,465),(211,501),(329,485),(370,479)],
                 'cap':[(173,347),(293,354),(426,365)]}}
    for k,groups in checks.items():
        P=np.array(cams[k]['P']);eye=np.array(cams[k]['camera_position']);inv=np.linalg.inv(P[:,:3])
        for typ,pixels in groups.items():
            for u,v in pixels:
                h=read(eye,inv@[u,v,1]);mat=h['material'] if h else None;pos=h['point_enu_m'] if h else None
                if typ=='opening':ok=pos is None or pos[1]>.51
                elif typ=='fan':ok=mat in (*g.RINGS,g.JOINT)
                elif typ=='brick':ok=mat==g.FACE
                else:ok=mat in (g.CAP,g.SILL,g.DRIP)
                photo.append(dict(view=k,pixel=[u,v],expected=typ,first=mat,
                                  point_m=np.round(pos,3).tolist() if pos is not None else None,matched=bool(ok)))
    return dict(asset=scene.asset,physical_count=len(results),physical_pass=sum(r['matched'] for r in results),
                photo_count=len(photo),photo_direct=sum(r['matched'] for r in photo),physical=results,photographic=photo)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('glb',type=Path);ap.add_argument('report',type=Path);args=ap.parse_args()
    data=inspect(args.glb);args.report.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print({k:v for k,v in data.items() if k not in ('physical','photographic')})
