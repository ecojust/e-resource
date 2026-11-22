"""Read the actual unfiltered first triangle at iron, clear openings and both numbered gateposts."""
import argparse
import json
from pathlib import Path
import sys

import numpy as np

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'source'),str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact')]
from glb_triangles import SerialScene
from court_gate import BRASS, CAP, DARK, GLOW, INK, PALE, PIER, PLANE, STEEL, SURVEY, x_at, z_at


def check(asset,local=False):
    mesh=SerialScene(asset)
    mat=np.eye(4)if local else np.array(json.loads((HERE/'garden-gate-placement.json').read_text())['gate_to_house'])
    scale=np.linalg.norm(mat[:3,0]);rows=[]
    def cast(label,origin,direction,limit,expected,**observed):
        point=(mat@np.r_[origin,1.])[:3]
        vec=mat[:3,:3]@np.asarray(direction)
        first=mesh.ray(point,vec,limit*scale)
        actual=first['material']if first else None
        rows.append(dict(label=label,passed=actual in expected,expected=expected,
                         first_material=actual,gate_origin=origin,gate_ray=direction,**observed))
    def face(name,x,z,expect,y=-.15,depth=.33):
        cast(name,[x,y,z],[0.,1.,0.],depth,expect)
    bands=SURVEY['bars'];top=np.array(SURVEY['top_rail_centres'])
    for i,centres in enumerate(bands):
        for n,u in enumerate(centres):
            for v in (279.,314.,353.,402.):
                face('Main gate upright',x_at(u),z_at(v),[STEEL])
            if n+1<len(centres):
                mid=(u+centres[n+1])*.5
                for v in (267.,310.,413.):
                    face('View through open iron rods',x_at(mid),z_at(v),[None])
    for u in (124,160,205,252,294,336,375,405,439,478,515,546,591,625,652):
        v=np.interp(u,top[:,0],top[:,1]);face('Curved rolled upper edge',x_at(u),z_at(v),[STEEL])
    for u in SURVEY['top_spears_x']:
        h=np.interp(u,top[:,0],top[:,1])-3.8
        scale_f=.93 if u in (137,640)else 1.
        face('Upper pointed fleur',x_at(u),z_at(h-19.0*scale_f),[STEEL])
    for u in (130,181,230,277,314,377,405,458,529,587,641):
        face('Top gallery rail',x_at(u),z_at(196.),[STEEL])
    for u in (138,218,301,384,582,613,644):
        face('Bottom gallery rail',x_at(u),z_at(221.6),[STEEL])
    for u in (435.,562.):
        for v in (242.,282.,330.,401.):
            face('Rectangular wicket frame',x_at(u),z_at(v),[STEEL])
    for u in (328,345,367,381.5):
        face('Projected hand pull',x_at(u),z_at(370.1),[STEEL])
    for c in (-2.697,2.57):
        for z,m in ((.69,PIER),(1.15,PALE),(1.56,PIER),(1.99,PALE),(2.72,PIER),(2.88,DARK)):
            face('Stone post strata and cornice',c,z,[m],-1.20,.65)
        cast('Face of lantern',[c,-1.05,3.22],[0,1,0],1.1,[GLOW])
        cast('Hipped lantern cap',[c,-1.05,3.388],[0,1,0],1.1,[CAP])
    for u in (2.40,2.45,2.51,2.61,2.69):
        face('Inscribed tablet body',u,2.485,[BRASS,INK],-1.1,.4)
    # Independent image point readings in the original editorial photograph, before any mesh rendering.
    # These native pixels are expressed on its 700px viewing copy then converted back to 4428px.
    controls=[(74,250,[PIER]),(70,307,[PIER]),(70,294,[PALE]),(589,245,[PIER]),(604,363,[PIER]),
              (594,280,[PALE]),(589,420,[PALE]),(561,199,[BRASS,INK]),
              (609,87,[GLOW]),(34,153,[GLOW]),(577,117,[DARK])]
    camera=np.array(PLANE['P_native']);eye=-np.linalg.solve(camera[:,:3],camera[:,3]);k=4428/700.
    for u,v,allowed in controls:
        uv=[u*k,v*k]
        direction=np.linalg.solve(camera[:,:3],[*uv,1.]);cast('2014 source photograph',eye.tolist(),direction.tolist(),15,allowed,native_px=uv)
    fail=[r for r in rows if not r['passed']]
    return dict(**mesh.asset,frame='gate local'if local else'house metric',count=len(rows),passed=not fail,checks=rows)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('asset',type=Path);parser.add_argument('output',type=Path)
    parser.add_argument('--local',action='store_true');args=parser.parse_args()
    result=check(args.asset,args.local);args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=1)+'\n')
    bad=[(r['label'],r.get('native_px',r['gate_origin']),r['first_material']) for r in result['checks'] if not r['passed']]
    print(result['count']-len(bad),result['count'],bad)
    sys.exit(bool(bad))
