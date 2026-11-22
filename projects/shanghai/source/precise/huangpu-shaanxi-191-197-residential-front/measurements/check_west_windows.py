"""Check real nearest surfaces in the editable GLBs and the integrated facade."""
import argparse,json,sys
from pathlib import Path
M=Path(__file__).resolve().parent
sys.path.insert(0,str(M.parent/'source'))
sys.path.insert(0,str(M.parents[1]/'xuhui-pathe-records-office'/'measurements'/'city-contact'))
from glb_triangles import SerialScene
from west_upper_windows import openings,sections,FRAME_SETBACK,BAR,FRAME,SKY,LIGHT,STONE

def probes(row):
    xs,zs=sections(row);label=row['label'];middle=(row['bottom']+row['top'])/2
    for i,(a,b,mat) in enumerate(xs):
        yield f'Vertical {i+1}',(a+b)/2,middle,mat,FRAME_SETBACK+(.016 if mat==BAR else 0.)
    for col in range(len(xs)-1):
        x=(xs[col][1]+xs[col+1][0])/2
        for n,(a,b,mat) in enumerate(zs):
            yield f'Horizontal {col+1}/{n+1}',x,(a+b)/2,mat,FRAME_SETBACK+(.017 if mat==BAR else .001)
        for n in range(len(zs)-1):
            yield f'Glazing {col+1}/{n+1}',x,(zs[n][1]+zs[n+1][0])/2,SKY if n>=2 else LIGHT,FRAME_SETBACK+.043
    a,b=row['sill_x']
    for n,p in enumerate((.06,.37,.82,.95)):
        yield f'Ledge front {n+1}',a+(b-a)*p,row['bottom']-.5*row['sill_height'],STONE,-.125
def check(model,out):
    scene=SerialScene(model);result=[]
    for row in openings():
        for feature,x,z,material,depth in probes(row):
            hit=scene.ray([x,-3.,z],[0,1,0],4.)
            y=None if hit is None else hit['point_enu_m'][1]
            result.append(dict(window=row['label'],feature=feature,x=x,z=z,expected_material=material,expected_depth_m=depth,
                               actual_material=None if hit is None else hit['material'],actual_depth_m=y,
                               passed=hit is not None and hit['material']==material and abs(y-depth)<.004))
    audit={**scene.asset,'triangles':len(scene.tri),'rays':len(result),'passed':all(t['passed'] for t in result),'checks':result}
    out.write_text(json.dumps(audit,indent=2)+'\n')
    print(model.name,audit['triangles'],audit['rays'],audit['passed']);return audit['passed']
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('model',type=Path);p.add_argument('out',type=Path);a=p.parse_args()
    raise SystemExit(0 if check(a.model,a.out) else 1)
