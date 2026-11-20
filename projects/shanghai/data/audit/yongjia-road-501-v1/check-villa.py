"""Trace architectural features in the three serialized 501 Yongjia Road deliveries."""
from pathlib import Path
import argparse, hashlib, json, math, runpy

def check(scene):
    results=[]
    def ray(name,origin,direction,wanted,near,far):
        hit=scene.ray(origin,direction,40)
        assert hit and hit['material'] in wanted and near<hit['distance_m']<far,(name,origin,hit,near,far)
        results.append(dict(part=name,origin=origin,direction=direction,hit=hit))
    center=(-7.12+8.31)/2
    for u in [-5.72,-3.00,-.77,1.51,3.63]:
        ray('north first-floor sash',[center+u+.15,-3,5.24],[0,1,0],{'window glass','old steel sash'},3.13,3.35)
    for u in [-4.40,-2.50,-.78,1.95,3.47,5.20]:
        ray('garden first-floor sash',[center-u+.13,12,5.24],[0,-1,0],{'window glass','old steel sash'},3.79,4.03)
    for u in [-4.28,-1.76,1.57,4.50]:
        ray('garden arched opening',[center-u+.16,12,2.27],[0,-1,0],{'window glass','old steel sash'},3.79,4.03)
    for x in [-3.30,-.72,1.95]:
        for y,dy in [(-3,1),(12,-1)]:
            ray('window of clay-roofed dormer',[x+.14,y,8.49],[0,dy,0],{'window glass','old steel sash'},3.86 if dy>0 else 4.54,4.18 if dy>0 else 4.88)
    for x in [-4.45,.79,4.61]:
        for y in [.21,2.4,4.17,5.94,8.12]:
            ray('roof pitch or ridge',[x,y,14.0],[0,0,-1],{'red clay tile','shadowed clay tile'},3.35,6.60)
    dx,dy=math.cos(-.39),math.sin(-.39)
    for z in [5.13,6.02,7.19,8.56]:
        ray('arched west-facing staircase slit',[6.98+dx*3.6,.22+dy*3.6,z],[-dx,-dy,0],
            {'window glass'},2.20,2.29)
    for a in [-2.47,-1.91,-1.3,-.98,-.76]:
        dx,dy=math.cos(a),math.sin(a)
        ray('plain tower shaft toward street',[6.98+dx*3.6,.22+dy*3.6,6.64],[-dx,-dy,0],
            {'pebble render'},2.10,2.15)
        ray('upper red-brick frieze',[6.98+dx*3.6,.22+dy*3.6,8.31],[-dx,-dy,0],
            {'red fired brick'},2.08,2.15)
    for z,r in [(9.16,1.8),(10.10,1.43),(11.37,.93),(12.84,.31)]:
        ray('tapering metal spire',[6.98,-4.6,z],[0,1,0],{'painted zinc'},4.82-r-.045,4.82-r+.045)
    for u in [-.74,.53]:
        ray('west low annexe windows',[12,4.515+u+.06,2.58],[-1,0,0],
            {'window glass','old steel sash'},2.43,2.70)
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
