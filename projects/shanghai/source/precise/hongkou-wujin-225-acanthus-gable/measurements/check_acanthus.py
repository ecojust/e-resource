"""Probe the independent image observations against the first triangle hit in an actual GLB."""
import argparse,json,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact'))
from glb_triangles import SerialScene
SCROLL='Wujin | carved brick'
LEAF='Wujin | raised leaf face'
BED='Wujin | red relief ground'

# Centres and inspection points were read on the Commons photograph rectified
# to 720 x 370. They are independent of the mesh's Hermite control knots.
TARGETS={
    'eight terminal bosses': (SCROLL,[(50,53),(678,49),(260,64),(463,72),
                                      (27,326),(653,300),(235,326),(461,327)]),
    'eight surrounding curls':(SCROLL,[(18,38),(696,38),(220,42),(501,45),
                                       (18,285),(680,271),(211,318),(495,326)]),
    'central fan and crown':(LEAF,[(356,34),(357,101),(355,145),(356,187),
                                    (355,229),(357,269),(355,312),(355,347)]),
    'folded leaves':(LEAF,[(155,71),(164,169),(88,178),(125,278),
                            (561,82),(651,153),(573,269),
                            (319,182),(399,207),(329,250),(407,243)]),
    'exposed recessed brick':(BED,[(33,111),(178,92),(200,65),(340,95),
                                     (397,100),(539,151),(574,128),(683,111),(75,289),
                                     (131,319),(191,317),(557,353),(689,341)])}
def inspect(path,row):
    scene=SerialScene(path);w=row['x1']-row['x0'];h=row['z1']-row['z0']
    reference=json.loads((HERE/'acanthus-photographs.json').read_bytes())
    H=np.array(reference['primary']['drawing_to_metric_rectangle'])
    report=[]
    for name,(mat,targets) in TARGETS.items():
        for u,v in targets:
            sample=H@np.array([u,v,1.]);uu,vv=sample[:2]/sample[2]
            x=row['x0']+w*uu/720;z=row['z1']-h*vv/370;start=row['face_y']-.16*w
            hit=scene.ray([x,start,z],[0,1,0],w)
            found=hit['material'] if hit else None
            face=hit['point_enu_m'][1] if hit else None
            depth_ratio=(row['face_y']-face)/w if face is not None else None
            if found==BED:height_ok=abs(depth_ratio-.009*row.get('depth_scale',1))<.0015
            else:height_ok=depth_ratio is not None and depth_ratio>.010*row.get('depth_scale',1)
            report.append(dict(feature=name,rectified_xy=[u,v],expected_material=mat,
                               first_material=found,face_projection_per_panel_width=depth_ratio,
                               passed=bool(found==mat and height_ok)))
    return dict(file_sha256=scene.asset['sha256'],bytes=scene.asset['bytes'],rays=len(report),
                matched=sum(q['passed'] for q in report),passed=all(q['passed'] for q in report),observations=report)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('row',type=Path);p.add_argument('output',type=Path);p.add_argument('models',type=Path,nargs='+')
    a=p.parse_args();row=json.loads(a.row.read_bytes())
    data=[inspect(x,row) for x in a.models];a.output.write_text(json.dumps(data,indent=2)+'\n')
    raise SystemExit(0 if all(r['passed'] for r in data)else 1)
