"""Verify front-facing triangles in the entrance at the eye positions of the shipped directory cameras."""
from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
import json,math,runpy,sys
import numpy as np
from trimesh.triangles import closest_point

HERE=Path(__file__).resolve().parent
load=runpy.run_path(str(HERE.parent/'postal-office-v1/independent-glb-review-helpers.py'))['load_triangles']
sys.path.insert(0,str(HERE.parent/'daxin-tobacco-northeast-tower-v1'))
first_hit=runpy.run_path(str(HERE.parent/'daxin-tobacco-northeast-tower-v1/check-model-sightlines.py'))['first_hit']
TARGETS=[
 ('upper red enamel character',(.04,-.123,3.98),(.26,.13,.25),('Vermilion enamel',)),
 ('forged upper iron arc',(-.5,-.026,4.12),(.30,.09,.15),('Blackened structural iron','Worn black scrollwork')),
 ('suspended oval timber',(.04,.200,3.29),(.61,.13,.14),('Weathered oval timber','Brown engraved lettering')),
 ('western post cycle plate',(-1.97,-.05,1.24),(.11,.08,.13),('Dark inscription','Warm ivory enamel')),
 ('eastern post cycle plate',(1.97,-.05,1.24),(.11,.08,.13),('Dark inscription','Warm ivory enamel')),
 ('east leaf notice',(1.23,1.03,1.31),(.42,.55,.29),('Warm ivory enamel','Green enamel address plate')),
 ('western brick panel',(-3.4,-.018,.84),(.28,.06,.18),('Oxblood facing brick','Burnt red brick','Faded red brick')),
 ('heritage plaque',(-3.94,-.055,1.95),(.25,.09,.15),('Dull silver heritage plate','Dark inscription')),
 ('1124 lane address plate',(-3.32,-.043,2.0),(.25,.06,.08),('Green enamel address plate','Warm ivory enamel')),
 ('Ruan Lingyu memorial',(-2.595,-.092,2.00),(.18,.1,.19),('Warm ivory enamel','Graphite bronze memorial','Weathered bronze relief'))]
def read(f):return json.loads(f.read_bytes())
def digest(f):return sha256(f.read_bytes()).hexdigest()
def main():
    parser=ArgumentParser(description=__doc__);parser.add_argument('--manifest',required=True,type=Path);parser.add_argument('--out',type=Path,default=HERE);args=parser.parse_args()
    manifest=read(args.manifest);contract=read(args.out/'final-placement-contract.json')
    cameras=read(args.out/'overview-sightlines.json')['views']
    h=math.radians(contract['heading']);axes=np.array([[math.cos(h),-math.sin(h)],[math.sin(h),math.cos(h)]])
    out=[]
    for role,filename in [('raw','raw.glb'),('full','decoded-full.glb'),('lod','decoded-lod.glb')]:
        triangles,mi,materials,asset=load(args.manifest.parent/filename);centers=triangles.mean(1)
        assert len(triangles)==manifest['assets'][role]['triangles']
        mesh=(triangles[:,0],triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0],mi)
        rows=[]
        for view in cameras:
            eye_world=np.array(view['camera_enu']);eye=np.r_[eye_world[:2]@axes.T,eye_world[2]]
            for name,target,radius,acceptable in TARGETS:
                target=np.array(target);radius=np.array(radius)
                eligible=np.isin(mi,[materials.index(m) for m in acceptable if m in materials])
                eligible&=np.all(triangles.max(1)>=target-radius,axis=1)&np.all(triangles.min(1)<=target+radius,axis=1)
                ids=np.flatnonzero(eligible);assert len(ids),(role,name)
                surface=closest_point(triangles[ids],np.repeat(target[None,:],len(ids),axis=0))
                options=surface*.90+centers[ids]*.10
                result=None
                for n in np.argsort(np.linalg.norm((options-target)/radius,axis=1))[:80]:
                    for point in (options[n],centers[ids[n]]):
                        hit=first_hit(eye,point,mesh)
                        if hit:
                            idx,err=hit
                            if err<.011 and materials[mi[idx]] in acceptable:
                                result=dict(triangle=int(idx),material=materials[mi[idx]],endpoint_m=point.tolist(),difference_m=float(err));break
                    if result:break
                assert result,(role,view['view'],name)
                rows.append(dict(view=view['view'],eye_m=eye.tolist(),feature=name,hit=result))
        out.append(dict(role=role,encoded_sha256=manifest['assets'][role]['sha256'],decoded_sha256=asset['sha256'],physical_triangle_count=len(triangles),camera_results=rows))
    result=dict(passed=True,manifest_sha256=digest(args.manifest),placement_sha256=digest(args.out/'final-placement-contract.json'),roles=out,total_first_hit_tests=sum(len(x['camera_results'])for x in out))
    (args.out/'model-sightlines.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(result['total_first_hit_tests'])
if __name__=='__main__':main()
