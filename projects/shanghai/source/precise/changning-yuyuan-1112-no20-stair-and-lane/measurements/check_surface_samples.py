from pathlib import Path
import argparse, json, hashlib, runpy
import numpy as np
HERE=Path(__file__).absolute().parent
def evaluate(mesh):
    src=json.loads((HERE/'observed-surface-samples.json').read_bytes())
    stations=json.loads((HERE/'two-stations.json').read_bytes())
    scene=runpy.run_path(str(HERE.parents[3]/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene'](mesh)
    records=[]
    for name,points in src.items():
        q=stations[name];eye=np.asarray(q['C']);axes=np.asarray(q['R']).T@np.linalg.inv(q['K'])
        for label,u,v,expected in points:
            trace=lambda x,y:scene.ray(eye,axes@[x,y,1],60)
            hit=trace(u,v)
            matches=lambda a:bool(a and any(a['material'].endswith(m)for m in expected))
            near=0 if matches(hit)else None
            if near is None:
                offsets=sorted([(x*x+y*y,x,y)for x in range(-6,7) for y in range(-6,7) if 0<x*x+y*y<=36])
                for dist,x,y in offsets:
                    if matches(trace(u+x,v+y)):
                        near=round(dist**.5,2);break
            records.append(dict(station=name,label=label,native_pixel=[u,v],expected=expected,first_hit=hit,nearest_compatible_pixel_distance=near))
    return dict(model_sha256=hashlib.sha256(mesh.read_bytes()).hexdigest(),count=len(records),direct=sum(r['nearest_compatible_pixel_distance']==0 for r in records),within6=sum(r['nearest_compatible_pixel_distance']is not None for r in records),samples=records)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args();out=evaluate(a.source);a.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(out['direct'],out['within6'],out['count'])

