"""Read the exported triangles at the recorded steel and pane observations."""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0,str(ROOT/'xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'))
from glb_triangles import SerialScene
from register_street import Camera

# Directly marked on 2015 reverse oblique (1050 x 800), one visible pane per opening.
HOLDOUT = [(404.601,283.026),(498.706,321.003),(571.479,322.605),(412.077,467.070),
           (498.248,481.678),(595.465,460.114),(607.124,584.003)]
STEEL = 'Xinlefang | green-black rolled steel sash'
EDGE  = 'Xinlefang | worn green transom nosing'


def verify(asset):
    scene=SerialScene(asset)
    data=json.loads((HERE/'front-window-photo-points.json').read_bytes())
    hits=[]
    cameras={k:Camera(k) for k in ['2018','1512-6']}
    def hit(station,row,label,uv,materials):
        cam=cameras[station]
        impact=scene.ray(cam.c,cam.ray(uv),45)
        actual=impact['material'] if impact else None
        hits.append(dict(station=station,window=row['name'],feature=label,pixel=uv,
                         expected=materials,hit=impact,matched=actual in materials))
    for row,extra in zip(data['windows'],HOLDOUT):
        bright=bool(row.get('transom_2018_original_px'))
        glass='Xinlefang | '+('sky-lit' if bright else 'shaded')+' steel window glass'
        hit('2018',row,'centre closing stile',row['meeting_stile_px'],[STEEL,EDGE])
        for uv in row['crossbars_2018_original_px']:
            hit('2018',row,'horizontal glazing bar',uv,[STEEL])
        if bright:
            hit('2018',row,'transom',row['transom_2018_original_px'],[STEEL,EDGE])
        for uv in row['glass_control_2018_px']:
            hit('2018',row,'glass',uv,[glass])
        hit('1512-6',row,'held-out pane',extra,[glass])
    return dict(asset=scene.asset,observations=hits,
                summary={k:[sum(x['matched'] for x in hits if x['station']==k),
                            sum(x['station']==k for x in hits)] for k in cameras})


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('asset',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args()
    result=verify(args.asset)
    args.output.parent.mkdir(exist_ok=True,parents=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(result['asset']['sha256'],result['summary'])
