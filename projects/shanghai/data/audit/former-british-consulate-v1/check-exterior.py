"""Independently trace both principal verandas, the historic court and their roof details."""
from pathlib import Path
import argparse,hashlib,json,runpy
import numpy as np
pa=argparse.ArgumentParser(description=__doc__)
for key in ('project','manifest','decoded','out'):pa.add_argument('--'+key,type=Path,required=True)
args=pa.parse_args()
Scene=runpy.run_path(str(args.project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
doc=json.loads(args.manifest.read_bytes())
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
rows=[]
for variant in ('raw','full','lod'):
    file=args.manifest.parent/doc['assets'][variant]['file'];chk=file if variant=='raw'else args.decoded/(variant+'.glb')
    assert sha(file)==doc['assets'][variant]['sha256'];scene=Scene(chk);tests=[]
    def ray(label,origin,dir,expected,extent):
        hit=scene.ray(origin,dir,70)
        assert hit and hit['material']in expected and extent[0]<=hit['distance_m']<=extent[1],(variant,label,hit,extent)
        tests.append({'label':label,'origin':origin,'direction':dir,'material':hit['material'],'distance_m':hit['distance_m']})
    pane={'aged glazing','painted sash','dark hardwood'}
    for side,count,L,center in [('south',9,29.03,6.115),('east',13,40.30,21.40)]:
        direction=[0,1,0] if side=='south'else[-1,0,0]
        for j in range(count):
            u=(j-(count-1)/2)*L/count;central=abs(j-count//2)<=2
            for h in [2.8,8.38]:
                z= [center+u+.17,-5,h] if side=='south'else[31,center+u+.17,h]
                default=(7.95,9.25)if side=='south'else(12.55,13.65);ends=(5.75,6.4)if side=='south'else(10.25,10.95)
                ray(f'{side} bay {j+1}, height {h}',z,direction,pane,default if central else ends)
        for pair in [-1,1]:
            u=center+pair*L/count*.5
            origin=[u,-5,2.25]if side=='south'else[31,u,2.25]
            ray(side+' central arch pier',origin,direction,{'buff ashlar','lime trim','rusticated joint'},(5.60,5.83)if side=='south'else(10.22,10.48))
    for u in (-4.83,-1.61,1.61,4.83):
        ray('original court upper stone column',[-30,28.8-u,7.45],[1,0,0],{'lime trim'},(7.71,8.12))
    for x,y in [(-2.50,10.2),(9.1,19.2),(-2.50,28.2),(9.1,37.1),(-17,14.2),(-16,36.1)]:
        ray('chimney cap',[x,y,25],[0,0,-1],{'pale sill'},(9.42,10.38))
    for x,y in [(-7.6,18.1),(-4.64,25.2),(-2.75,31.3)]:
        ray('rectangular west rooftop glazing',[x,y,25],[0,0,-1],{'roof light'},(11.93,12.02))
    ray('west side of supported roof-light curb',[-8.42,24,12.42],[-1,0,0],{'roof light frame'},(.17,.25))
    ray('solid north narrow return',[-9.40,41.10,3.3],[1,0,0],{'warm render'},(.95,1.05))
    ray('south-east corner against joined masonry',[21.0,1.02,2.0],[-1,0,0],{'buff ashlar'},(.32,.42))
    ray('garden office raised terrace',[23.14,21,4],[0,0,-1],{'terrace paving'},(3.24,3.38))
    for x,y in [(17,7),(13,35),(-18,21)]:
        ray('grey tiled roof plane',[x,y,22],[0,0,-1],{'grey butterfly tile','ridge tile'},(7.1,10.65))
    rows.append({'variant':variant,'asset_sha256':sha(file),'decoded_sha256':sha(chk),'triangles':len(scene.tri),'probes':tests})
report={'manifest_sha256':sha(args.manifest),'script_sha256':sha(Path(__file__)),'id':doc['id'],'passed':True,'count':sum(len(r['probes'])for r in rows),'variants':rows}
args.out.parent.mkdir(exist_ok=True,parents=True);args.out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n');print(report['count'])
