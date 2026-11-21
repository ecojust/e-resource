"""Trace architectural features in the three serialized 151 Wulumuqi South Road gates."""
from pathlib import Path
import argparse, hashlib, json, math, runpy

def check(scene):
    results=[]
    def ray(label,x,z,materials,minimum,maximum):
        origin=[x,-2,z]
        hit=scene.ray(origin,[0,1,0],4)
        assert hit and hit['material'] in materials and minimum < hit['distance_m'] < maximum,(label,x,z,hit,minimum,maximum)
        results.append(dict(part=label,origin=origin,direction=[0,1,0],hit=hit))
    for sign in (-1,1):
        for z in (.23,1.83,3.12):
            ray('tall gatepost',sign*1.92,z,{'warm gray render'},1.645,1.697)
        ray('projecting squared cap',sign*1.92,3.383,{'molded cap'},1.62,1.65)
        ray('sphere on each pier',sign*1.92,3.645,{'globe'},1.86,1.90)
        ray('rectangular earthward plinth',sign*3.48,.31,{'limestone'},1.13,1.18)
        ray('lion globe, muzzle or mouth',sign*3.48,1.62,{'limestone','carved limestone','carving hollows'},1.11,1.31)
        ray('guardian chest and mane',sign*3.48,1.42,{'limestone','carved limestone'},1.18,1.43)
        for dx in (-.16,.16):
            ray('separate guardian forepaws',sign*3.48+dx,.80,{'limestone'},1.12,1.33)
        ray('high rendered wall',sign*4.17,2.49,{'warm gray render'},1.83,1.92)
        ray('wall cap edge',sign*4.18,2.90,{'molded cap'},1.74,1.81)
        ray('wall base',sign*4.02,.21,{'gray plinth'},1.81,1.87)
        for dx in (-1,1):
            center=sign*((3.20-.085)/4+.012)+dx*(3.20-.085)/8
            ray('four rectangular recessed door panels',center-.087,2.03,{'gate recess','raised woodwork'},1.95,2.10)
            ray('four lower modeled fillets',center,.76,{'raised woodwork'},1.95,2.016)
            ray('four arched relief castings',center+.060,2.57,{'raised woodwork','gate recess'},1.95,2.10)
    ray('green enamel 151 number plate',-1.92+.122,2.58,{'number enamel'},1.60,1.64)
    ray('raised numeral on green enamel',-1.92-.083,2.60,{'enamel lettering'},1.59,1.62)
    ray('separate bronze-toned tablet',-2.65,2.58,{'weathered tablet'},1.82,1.88)
    ray('letter slot under tablet',-2.66,1.514,{'bronze'},1.79,1.85)
    for x,z in [(0,3.6),(-3.48,3.17),(3.48,3.17),(-4.65,1.4),(4.65,1.4)]:
        assert scene.ray([x,-2,z],[0,1,0],4) is None,(x,z)
        results.append(dict(part='open air beyond documented silhouette',origin=[x,-2,z],direction=[0,1,0],hit=None))
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
