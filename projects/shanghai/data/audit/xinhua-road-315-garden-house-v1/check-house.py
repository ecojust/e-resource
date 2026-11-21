"""Probe the serialized garden and north courtyard facades, roof and open arcade."""
from pathlib import Path
import argparse, hashlib, json, runpy

def check(scene):
    results=[]
    def trace(name,origin,direction,length,allowed,low,high):
        hit=scene.ray(origin,direction,length)
        if allowed is None:
            assert hit is None,(name,hit)
        else:
            assert hit and hit['material'] in allowed and low<hit['distance_m']<high,(name,origin,hit,(low,high))
        results.append(dict(part=name,origin=origin,direction=direction,hit=hit))
    def south(name,x,z,d,mats):
        trace(name,[x,-5,z],[0,1,0],25,mats,d-.08,d+.08)
    def north(name,x,z,d,mats):
        trace(name,[x,24,z],[0,-1,0],30,mats,d-.09,d+.09)
    glass={'old casement glass','dark oak framing'}
    rendered={'rough lime render'};brick={'red garden brick','brick course'}
    for u in [-1.64,0,1.66]:
        south('three lower windows of south gable',-3.16+u+.14,1.95,3.746,glass)
    south('garden gable brick base',-5.93,2.74,3.48,brick)
    south('garden gable lime render',-5.19,4.60,3.48,rendered)
    south('garden timber upright',-4.36,4.50,3.408,{'dark oak framing'})
    south('upper gable casement',-3.06,10.22,3.746,glass)
    south('garden gable diagonal timber',-5.26,10.19,3.408,{'dark oak framing','rough lime render'})
    south('central garden glass opening',4.84,1.32,6.616,{'garden door glass','painted steel'})
    south('east arcade brick side pier',9.11,1.12,5.21,brick)
    south('second arcade brick side pier',14.80,1.12,5.21,brick)
    south('eastern veranda rear glazed door',12.10,1.37,8.235,{'garden door glass','painted steel'})
    south('upper veranda casement behind railing',12.13,5.67,8.235,glass)
    for x in [10.42,11.95,13.34]:
        trace('outdoor depth beneath brick arch',[x,-1,1.57],[0,1,0],3.75,None,0,0)
    for pos in [-8.70,2.415]:
        front,d=(19.64,4.36) if pos<0 else (13.64,10.36)
        north('north courtyard tall gable stair window',pos+.13,5.12,d+.266,glass)
        north('north exposed timber post',pos+.77,6.33,d-.072,{'dark oak framing'})
        north('north gable lime infill',pos+1.38,7.56,d,rendered)
    for x,y,minz,maxz in [(1.16,.76,8.1,9.15),(5.85,4.84,11.1,12.05),(-3.16,-1.19,13.5,14.55),
                           (-8.58,18.87,13.0,13.9),(2.36,13.17,11.6,12.65),(11.21,6.01,12.05,12.50)]:
        trace('slope or ridge at surveyed roof section',[x,y,25],[0,0,-1],24,{'terracotta roof','tile edges','old clay ridge'},25-maxz,25-minz)
    trace('raised garden chimney cap and open flue',[8.08,5.67,21],[0,0,-1],14,{'recess shadow'},7.02,7.17)
    for x,y in [(2.99,-3.9),(-2.45,16.25),(11.79,14.06),(-15.96,5.25)]:
        trace('documented open courtyard and roof silhouette',[x,y,25],[0,0,-1],25.5,None,0,0)
    return results

def run():
    parser=argparse.ArgumentParser()
    for flag in ('project','manifest','decoded','out'):parser.add_argument('--'+flag,type=Path,required=True)
    a=parser.parse_args();manifest=json.loads(a.manifest.read_bytes())
    helper=runpy.run_path(str(a.project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))
    h=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
    variants=[]
    for role in ['full','lod','raw']:
        rec=manifest['assets'][role];file=a.manifest.parent/rec['file']
        assert h(file)==rec['sha256']
        decoded=file if role=='raw' else a.decoded/(role+'.glb')
        scene=helper['SerialScene'](decoded);probes=check(scene)
        assert len(scene.tri)==rec['triangles']
        variants.append(dict(role=role,triangles=len(scene.tri),sha256=h(file),decoded_sha256=h(decoded),samples=probes))
    data=dict(id=manifest['id'],passed=True,manifest_sha256=h(a.manifest),script_sha256=h(Path(__file__)),
              count=sum(len(v['samples'])for v in variants),variants=variants)
    a.out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':run()
