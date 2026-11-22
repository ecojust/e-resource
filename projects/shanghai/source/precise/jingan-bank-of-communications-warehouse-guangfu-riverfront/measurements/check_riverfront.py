"""Probe the actual decoded wall, gutters, open door, return planes and apertures."""
import argparse,json,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact'),str(HERE.parent/'source')]
from glb_triangles import SerialScene
import river_masonry as wall
import south_entrance as entrance
import warehouse_window_sashes as windows
import roof_terrace as roof

def check(mesh):
    layout=json.loads((HERE/'riverfront-layout.json').read_bytes())
    survey=json.loads((HERE/'four-station-front-height.json').read_bytes())['estimates']
    sc=SerialScene(mesh);checks=[]
    def test(label,origin,dir,depth,allowed,*,expected=None,tolerance=.08):
        hit=sc.ray(origin,dir,depth);actual=hit['material']if hit else None
        error=(float(hit['distance_m'])-expected if expected is not None and hit else None)
        checks.append(dict(feature=label,origin=np.round(origin,5).tolist(),direction=dir,
            max_distance_m=depth,allowed=allowed,obtained=actual,distance_error_m=error,
            passed=actual in allowed and (expected is None or (error is not None and abs(error)<tolerance))))
    glazing=[windows.SKY,windows.CLEAR,windows.DARK,windows.FIXED,windows.SASH]
    for g in layout['bays']:
        name=g['bay'];point=wall.face_at(g);ops=[o for o in layout['openings']if o['bay']==name]
        top=next(o for o in ops if o['level']==4);u0,u1=top['x0'],top['x1']
        for o in ops:
            x=o['x0']+.46*(o['x1']-o['x0']);z=o['z0']+.312*(o['z1']-o['z0'])
            test(o['key']+' open wall and steel or glass',point(x,z,1.0),[0,1,0],1.6,glazing)
        for f in (.25,.75):
            x=u0+(u1-u0)*f;z=top['z1']+.38
            test(name+' upper open vent',point(x,z,.7),[0,1,0],1.25,[wall.DARK],expected=.972)
            test(name+' paired aggregate relief',point(x,top['z1']+.68,.75),[0,1,0],1.,[wall.STONE],expected=.693)
        test(name+' ordinary roof coping',point((u0+u1)/2,layout['bay_wall_top']+.70,0),[0,0,-1],1.,[wall.LIP],expected=.692)
    for unit in (layout['bays'][:5],layout['bays'][5:]):
        for l,g in zip(unit,unit[1:]):
            x=g['x0'];f=wall.face_at(g)
            test(l['bay']+'-'+g['bay']+' gabled spine',f(x,layout['pier_peak_top']-.08,.85),[0,1,0],1.45,[wall.STONE,wall.LIP])
            test(l['bay']+'-'+g['bay']+' structural crown',f(x,layout['pier_peak_top']+.55,.102),[0,0,-1],1.1,[wall.LIP],expected=.535)
    # Each narrow opening must still be visible from the street through the stone tower around the common steel frame.
    for o in layout['openings']:
        if not o['bay'].startswith('C'):continue
        test(o['key']+' central window',[(o['x0']+o['x1'])/2,-.8,o['z0']+.286*(o['z1']-o['z0'])],[0,1,0],1.6,glazing)
    for dx in (-1.51,-.60,0.,1.37):
        for height in (.72,1.91,2.63):
            test('central through route',[dx,-.9,height],[0,1,0],15.65,[None])
    street,end=np.array(layout['west_return']);axis=end-street;axis/=np.linalg.norm(axis)
    outward=np.array([-axis[1],axis[0]])
    for o in layout['west_return_windows']:
        along=(o['d0']+o['d1'])/2
        front=street+axis*along
        pos=front+.49*outward
        test(o['key']+' actual west gable opening',[*pos,o['z0']+.316*(o['z1']-o['z0'])],
             [-float(outward[0]),-float(outward[1]),0.],.87,glazing)
    for x in (-22,-6,4,22):
        test('terrace pavement in place',[x,5.8,layout['roof_deck_z']+.5],[0,0,-1],.71,[roof.PAVING],expected=.5)
    # Mesh envelope height is checked against the independent four-station building estimate.
    # The four-station height is recorded relative to the street threshold.
    target=survey['middle_parapet_crest_above_threshold_m']
    crest=float(sc.highs[:,2].max()-.0)
    return dict(asset=sc.asset,passed=all(k['passed']for k in checks) and target['sensitivity_p05_p95'][0]<=crest<=target['sensitivity_p05_p95'][1],hits=checks,
                crest_height_m=crest,independent_crown=target,triangles=len(sc.tri))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mesh',type=Path);p.add_argument('output',type=Path);q=p.parse_args()
    result=check(q.mesh);q.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    if not result['passed']:
        print('failed',[h['feature']for h in result['hits']if not h['passed']]);raise SystemExit(1)
