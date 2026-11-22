"""First visible surfaces of the period windows, vents and facade piers in the exported meshes."""
from pathlib import Path
import json
import runpy
import sys
import numpy as np
from shapely.geometry import Point,Polygon

HERE=Path(__file__).absolute().parent
SRC=HERE.parents[2]/'source/precise/huangpu-ruijin-207-historic-roof-ornament/source'
sys.path.insert(0,str(SRC))
from historic_facade import F,rect_xyz,RAIL,GLASS,VENT,COLUMN,MATERIAL,secondary_on,OPEN,projected_light
from rosholt_front_plane import PROJECTION
inspect=runpy.run_path(HERE.parent/'central-reserve-bank-changshu-front-v1/verify-export.py')['inspect']

def probes():
    cases=[]
    def sight(label,source,target,materials,tolerance=.12):
        source,target=np.array(source),np.array(target)
        distance=float(np.linalg.norm(target-source))
        cases.append(dict(name=label,origin=source.tolist(),direction=((target-source)/distance).tolist(),length=distance+tolerance+.005,allowed=materials,range_m=[distance-tolerance,distance+tolerance]))
    eye=-np.linalg.solve(PROJECTION[:,:3],PROJECTION[:,3])
    for win in F['regular_windows']:
        l,t,r,b=win['rectified_bounds']
        label=f"Bay {win['bay']} tier {win['tier_from_top']}"
        for i,u in enumerate(win['mullions_rectified_x_px']):
            v=(win['transoms_rectified_y_px'][0]+win['transoms_rectified_y_px'][1])/2
            if win['tier_from_top']==1 and win['bay'] in (1,4):
                # The moving sash overlaps the upper segment of the fixed mullions. Test the exposed wood across the lower pane.
                v=(win['transoms_rectified_y_px'][1]+b)/2
            target=rect_xyz(u,v,.58);sight(label+f' upright {i+1}',eye,target,[RAIL],.085)
        for i,v in enumerate(win['transoms_rectified_y_px']):
            u=(l+r)/2;target=rect_xyz(u,v,.564);sight(label+f' transom {i+1}',eye,target,[RAIL],.085)
        # Each glass ray comes from that same historical camera and uses the middle of a pane.
        rods=sorted([l,*win['mullions_rectified_x_px'],r])
        for i,(a,d) in enumerate(zip(rods,rods[1:])):
            if d-a<5:continue
            u=(a+d)/2;v=win['transoms_rectified_y_px'][-1]+(b-win['transoms_rectified_y_px'][-1])*.50
            target=rect_xyz(u,v,.651);sight(label+f' glass {i+1}',eye,target,[GLASS],.075)
    for idx,row in enumerate(F['photographed_vent_slots']):
        l,t,r,b=row['rectified_bounds']
        target=rect_xyz((l+r)/2,(t+b)/2,.255)
        sight(f'Photographed vent slot {idx+1}',eye,target,[VENT],.055)
    for i,(u,width) in enumerate(F['round_front_piers']):
        for v in [264,378,463]:
            target=rect_xyz(u,v,0)
            sight(f'Long round pier {i+1} at rectified row {v}',eye,target,[COLUMN],.57)
    for i,quad in enumerate(F['open_top_hung_lights']):
        pts=projected_light(quad)
        for j in range(4):
            at=(pts[j]+pts[(j+1)%4])*.5
            sight(f'Upper hinged sash {i+1}, frame edge {j+1}',eye,at,[OPEN],.077)
    return cases

if __name__=='__main__':
    rows={name:inspect(Path(path),probes())for name,path in zip(('raw','full','lod'),sys.argv[1:4])}
    Path(sys.argv[4]).write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    for role,row in rows.items():print(role,len(row['cases']),[(c['name'],(c['first_hit']or{}).get('material')) for c in row['cases']if not c['passed']])
    sys.exit(int(any(not r['passed']for r in rows.values())))
