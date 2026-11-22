"""Evaluate photographed window pixels and material probes against an entire gatehouse GLB."""
from pathlib import Path
import argparse,json,sys
import numpy as np
m=Path(__file__).resolve().parent
project=m.parents[3]
reader=project/'source/precise/xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'
sys.path.insert(0,str(reader))
from glb_triangles import SerialScene
p=argparse.ArgumentParser();p.add_argument('glb',type=Path);p.add_argument('period',choices=['2018','2022']);p.add_argument('report',type=Path);args=p.parse_args()
L=json.loads((m.parent/'source/gatehouse-layout.json').read_bytes())
registered=json.loads((m/'registered-east-shopfronts.json').read_bytes())
poses={'2018-native':L['native_camera'],'winter-2021':registered['observations']['winter2021']['reprojection_P']}
new_tower=json.loads((m/'refurbished-tower-window.json').read_bytes())
poses.update({'refurbished-2021':new_tower['west_2021']['probe_P'],'refurbished-2025':new_tower['district_2025']['probe_P']})
scene=SerialScene(args.glb);results=[]
for row in json.loads((m/'street-shop-and-window-rays.json').read_bytes()):
    if args.period not in row['periods']:
        continue
    if row['view'] in poses:
        camera=np.asarray(poses[row['view']]);inverse=np.linalg.inv(camera[:,:3]);eye=-inverse@camera[:,3]
        direction=inverse@np.r_[row['pixel'],1.]
        length=90
    else:
        x,z=row['world_xz'];eye=[x,-1.0,z];direction=[0,1,0];length=3
    hit=scene.ray(eye,direction,length)
    results.append({**row,'first':hit,'matched':bool(hit and any(hit['material'].endswith(a) for a in row['allowed']))})
record={'period':args.period,'asset':scene.asset,'rays':len(results),'matches':sum(r['matched'] for r in results),'first_hits':results}
dated = [r for r in results if args.period == '2022' and r['view'] == '2018-native'
         and r['name'].startswith('tower lower light ')]
dated_names = {r['name'] for r in dated}
registered = [r for r in results if r['name'] not in dated_names]
record['period_registration'] = {
    'matches': sum(r['matched'] for r in registered),
    'rays': len(registered),
    'window_replacement_comparison': [r['name'] for r in dated],
    'explanation': 'The three 2018 lower tower lights retain their original image positions in both models. The refurbished rectangular window is checked separately against the January 2021 and district 2025 photographs.'
}
args.report.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
for row in results:
    if not row['matched']:print(row['name'],row['pixel'] if 'pixel' in row else row['world_xz'],row['first']['material'] if row['first'] else None)
print(args.period,record['matches'],record['rays'],flush=True)
