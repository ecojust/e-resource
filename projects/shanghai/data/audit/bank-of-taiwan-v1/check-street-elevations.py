"""Independently trace the Bund colonnade, layered Jiujiang Road bays and 2014 exterior lettering."""
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
    glazing={'green-grey glass','pressed dark frames'}
    for u in (-7.56,-2.52,2.52,7.56):
        ray('freestanding round shaft, east', [u,-5,6.3],[0,1,0],{'silver grey granite'},(5.0,5.35))
        ray('neck or carved leaf collar, east',[u,-5,13.41],[0,1,0],{'silver grey granite','pale carved stone'},(5.0,5.38))
    for u in (-5.04,0,5.04):
        ray('lower entrance or side sash',[u+.22,-5,4.20],[0,1,0],glazing|{'bronze door','smoked door panel'},(7.03,7.53))
        ray('recessed clerestory, east',[u+.21,-5,12.14],[0,1,0],glazing,(7.06,7.33))
        for z in (16.67,21.99):
            ray('upper office glazing, east',[u+.23,-5,z],[0,1,0],glazing,(5.15,5.33))
    sideA=np.array([-9.055-.11189*39.71,39.71]);sideB=np.array([-9.055,0])
    axis=(sideB-sideA)/np.linalg.norm(sideB-sideA);outward=np.array([axis[1],-axis[0]])
    middle=(sideA+sideB)/2;step=(np.linalg.norm(sideB-sideA)-4.12)/7
    def side(u,z):return list((middle+axis*u+outward*5).tolist())+[z]
    inward=[-outward[0],-outward[1],0]
    for j in range(6):
        ray('square order pier, south',side((j-2.5)*step,6.3),inward,{'silver grey granite'},(4.98,5.12))
    for j in range(7):
        u=(j-3)*step
        for z in (3.21,11.34):ray('recessed lower sash, south',side(u+.17,z),inward,glazing,(6.35,6.56))
        for dx in (-1.27,.16,1.27):
            for z in (16.51,21.47):ray('tripartite upper glazing, south',side(u+dx,z),inward,glazing,(5.14,5.34))
    ray('east plinth links the column bases',[-5.10,-5,.74],[0,1,0],{'honed bases'},(4.95,5.20))
    ray('clear central door panel at plinth height',[.36,-5,1.49],[0,1,0],{'bronze door','smoked door panel'},(7.29,7.53))
    ray('mitered corner at upper cornice',[-9.055-.55,-.55,21.5],[0,0,-1],{'pale carved stone'},(1.78,1.90))
    # Check actual gold triangle faces and project sample centroids into each
    # separate inscription plane. The assembled, visible first hit must be brass.
    mat=scene.materials.index('polished brass');gold=scene.tri[scene.mi==mat]
    samples=[];mid=gold.mean(axis=1)
    for name,lo,hi in [('entablature English sign',14.1,14.85),('four gold bank characters',20.0,21.45),('east circular bank mark',22.0,23.7)]:
        faces=(mid[:,2]>lo)&(mid[:,2]<hi)&(mid[:,1]<-.10)
        candidates=mid[faces]
        assert len(candidates)>8
        for pt in candidates[::max(1,len(candidates)//15)]:
            hit=scene.ray([float(pt[0]),-5,float(pt[2])],[0,1,0],7)
            if hit and hit['material']=='polished brass':
                samples.append({'label':name,'material':hit['material'],'distance_m':hit['distance_m']});break
        else:raise AssertionError((variant,name))
    assert len(samples)==3;tests.extend(samples)
    rows.append({'variant':variant,'asset_sha256':sha(file),'decoded_sha256':sha(chk),'triangles':len(scene.tri),'probes':tests})
report={'manifest_sha256':sha(args.manifest),'script_sha256':sha(Path(__file__)),'id':doc['id'],'passed':True,'count':sum(len(r['probes'])for r in rows),'variants':rows}
args.out.parent.mkdir(exist_ok=True,parents=True);args.out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n');print(report['count'])
