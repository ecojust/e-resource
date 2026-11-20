"""Read actual decoded triangles and check the Fuzhou Road exterior in each delivery."""
import argparse,hashlib,json,runpy
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser(description=__doc__)
for key in ['project','manifest','decoded','out']:p.add_argument('--'+key,type=Path,required=True)
a=p.parse_args();doc=json.loads(a.manifest.read_bytes())
Scene=runpy.run_path(str(a.project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
results=[]
for role in ['raw','full','lod']:
    src=a.manifest.parent/doc['assets'][role]['file'];assert sha(src)==doc['assets'][role]['sha256']
    path=src if role=='raw'else a.decoded/(role+'.glb');s=Scene(path);obs=[]
    def sample(label,x,y,z,vector,allowed,range_m=None):
        o=[.965*x+.25,y,z];hit=s.ray(o,vector,30)
        assert hit and hit['material'] in allowed,(role,label,hit)
        if range_m:assert range_m[0]<=hit['distance_m']<=range_m[1],(role,label,hit)
        obs.append({'location':label,'origin_m':o,'direction':vector,'material':hit['material'],'distance_m':hit['distance_m']})
    front=[0,1,0];down=[0,0,-1]
    for center in [-11.24,11.12]:
        for j,u in enumerate([-1.42,-.47,.47,1.42]):
            sample('projecting gable light '+str(j+1),center+u+.07,-4,5.71,front,['historic glass'])
        sample('projecting gable upper central stud',center,-4,9.37,front,['oxblood timber'])
        sample('triangular gable plaster panel',center+.49,-4,9.39,front,['sand render'])
        sample('perpendicular gable ridge',center,-.42,17,down,['ridge roll'])
    sample('western shutter field',-11.5,-4,2.24,front,['window shadow','rebated wood'])
    sample('eastern lamp bank',10.18,-4,1.37,front,['historic glass'])
    sample('recess behind central street opening',0,-4,1.80,front,['inner dark reveal'],[5.22,5.26])
    for side in [-1,1]:
        sample('small light beside center',side*3.76+.12,-4,1.04,front,['historic glass'])
        sample('brick ground floor',side*5.55,-4,1.64,front,['warm mortar','dark kiln brick','rose brick','umber brick','washed brick'])
    for x in [-4.82,-1.95,-.98,0,.98,1.94,2.93,5.42,6.37]:
        sample('upper street casement',x+.09,-4,5.72,front,['historic glass'])
    for x in [-7.18,6.58]:
        sample('chimney opening',x,4.87,17,down,['window shadow'],[3.24,3.30])
    tiles=['brick rust tile','weathered red tile','russet tile','ridge roll']
    sample('front tiles',2.4,.88,16,down,tiles,[7.4,7.9])
    sample('rear tiles',-2,7.6,16,down,tiles,[7.6,8.2])
    sample('west end hip',-15.0,4.2,16,down,tiles,[7.6,7.95])
    sample('east end hip',15.0,4.2,16,down,tiles,[7.6,7.95])
    sample('rear section closure',0,12,3,[0,-1,0],['neutral section'])
    results.append(dict(role=role,file_sha256=sha(src),decoded_sha256=sha(path),triangle_count=len(s.tri),surfaces=obs))
report={'model':doc['id'],'manifest_sha256':sha(a.manifest),'script_sha256':sha(Path(__file__)),'passed':True,'count':sum(len(v['surfaces'])for v in results),'variants':results}
a.out.parent.mkdir(exist_ok=True,parents=True);a.out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n');print(report['count'])
