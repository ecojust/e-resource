"""Cast rays from the registered 1934 eye at independently readable dark panes, piers and panels."""
from pathlib import Path
import argparse,hashlib,json,runpy,sys
import numpy as np
from register_court import Camera
HERE=Path(__file__).absolute().parent
sys.path.insert(0,str(HERE.parent/'source'))
from auditorium_flank import WALL,CAST,GLASS,FRAME
def samples():
    d=json.loads((HERE/'1934-east-flank-observed.json').read_bytes());checks=[]
    for bay in d['bays']:
        for row in ['lower','upper']:
            for k,mark in enumerate(bay[row].get('apertures',[]),start=1):
                a,b=np.array(mark['frame'])
                checks.append((f"bay {bay['bay']} {row} light {k}",((a+b)*.5).tolist(),[GLASS,FRAME]))
    # Independent interior pixel readings rather than model vertices.
    for k,(u,v) in enumerate([(82,617),(190,612),(277,601),(359,620),(436,616),(499,636),(558,633),(607,635),(655,651)],start=1):
        checks.append((f'pale pier {k}',[u+1610,v+330],[CAST]))
    for k,(u,v) in enumerate([(132,623),(236,632),(329,639),(407,628),(470,632),(526,635),(582,648),(635,644)]):
        checks.append((f'ochre spandrel {k+1}',[u+1610,v+330],[WALL]))
    return checks
def inspect(path):
    scene=runpy.run_path(str(HERE.parents[3]/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene'](path)
    c=Camera(1934);results=[]
    for label,p,expected in samples():
        hit=scene.ray(c.c,c.ray(p),175)
        results.append(dict(label=label,source_pixel=p,expected=expected,hit=hit,matched=bool(hit and hit['material'] in expected)))
    return dict(asset=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),tested=len(results),matched=sum(x['matched'] for x in results),rays=results)
if __name__=='__main__':
    cli=argparse.ArgumentParser();cli.add_argument('mesh',type=Path);cli.add_argument('report',type=Path);args=cli.parse_args()
    result=inspect(args.mesh);args.report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(result['matched'],result['tested']);print([(q['label'],q['hit']['material']if q['hit']else None)for q in result['rays'] if not q['matched']])
