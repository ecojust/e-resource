"""Unfiltered first-contact tests in the 14.91 m publicly visible south passage segment."""
from pathlib import Path
import argparse,hashlib,json,sys
from collections import Counter
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'source'),str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact')]
from glb_triangles import SerialScene
import south_passage as model


def check(asset):
    data=json.loads(model.DATA.read_bytes());grid=np.array(data['pier_centres_x_y_m']);width=np.mean(data['column_grid_widths_m'])
    scene=SerialScene(asset);rows=[];center=grid.mean(axis=(0,1))[0];end=data['first_lateral_change_y_m']
    def ray(label,start,direction,length,materials):
        observed=scene.ray(np.array(start,float),direction,length)
        actual=observed['material'] if observed else None
        rows.append(dict(test=label,origin=np.round(start,4).tolist(),direction=direction,limit_m=round(length,3),
                         actual=actual,hit_enu_m=observed['point_enu_m'] if observed else None,passed=actual in materials))
    for pair in grid:
        for x,y in pair:
            k=1 if x>center else -1
            for z in (.4,1.2,2.6,4.10):
                ray('exposed structural pier',[center,y,z],[k,0,0],width*.72,[model.CONCRETE])
        y=pair[:,1].mean()
        for x in [-1.2,0.,1.2]:
            ray('beam soffit',[x,y,2.1],[0,0,1],3.5,[model.CONCRETE])
    for y in [1.15,3.59,5.98,9.75,11.3,13.68]:
        for sign in [-1,1]:
            axis=center+sign*2.46
            for off in [-.25,0.,.25]:
                ray('paired folded light' if off else 'continuous dark spine',[axis+off,y,2.1],[0,0,1],3.0,
                    [model.LIGHT if off else model.STEEL])
            ray('dark side paving',[center+sign*width/2,y,.8],[0,0,-1],1.0,[model.SIDE])
        for x in [-1.2,0.,1.2]:
            ray('continuous promenade stone',[x,y,.8],[0,0,-1],1.0,[model.WALK])
    for y in [3.87,4.75,6.51,8.65,9.75,10.85]:
        for sign in [-1,1]:
            ray('recessed shop glazing or photographed frame',[center,y,1.3],[sign,0,0],width*.71,
                [model.GLASS,model.GLASS2,model.STEEL])
    for x in [-1.94,-1.18,-.31,.42,1.26,1.94]:
        for z in [.35,.9,1.68,2.75]:
            ray('unobstructed longitudinal sightline',[x,-.06,z],[0,1,0],end+.06,[None])
    return dict(passed=all(v['passed']for v in rows),asset_sha256=hashlib.sha256(asset.read_bytes()).hexdigest(),
                checks=len(rows),by_purpose=dict(Counter(v['test'] for v in rows)),source_plan=29,photographic_check=[16,23,30,31],
                measured_length_m=end,results=rows,failures=[v for v in rows if not v['passed']])

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('asset',type=Path);p.add_argument('out',type=Path);args=p.parse_args()
    result=check(args.asset);args.out.write_text(json.dumps(result,ensure_ascii=False,indent=1)+'\n')
    print(result['checks'],len(result['failures']),result['failures'][:2]);raise SystemExit(not result['passed'])
