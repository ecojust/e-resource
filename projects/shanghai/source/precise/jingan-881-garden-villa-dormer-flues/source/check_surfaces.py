from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='jingan-881-garden-villa-dormer-flues'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']








def test(scene,role):
    rows=[]
    def cast(kind,x,z,options,lo,hi):
        hit=scene.ray([x,-.5,z],[0,1,0],1.11)
        ok=hit is not None and hit['material'] in options and lo<=hit['distance_m']<=hi
        rows.append(dict(feature=kind,x=x,z=z,expected_material=sorted(options),depth_interval_m=[lo,hi],hit=hit,passed=ok))
    for x in (-.27,4.12):
        for n in range(10):
            z=2.39+n*.249
            if abs(z-3.91)<.05:continue
            for dx in (-.31,-.061,.31):
                h=scene.ray([x+dx,4.0,z],[0,1,0],1.4)
                if n==0:
                    rows.append(dict(feature='roof slope in front of the stack base',x=x+dx,z=z,hit=h,passed=h is not None and h['material']=='roof clay' and .22<h['distance_m']<.235))
                else:
                    rows.append(dict(feature='recessed shaft',x=x+dx,z=z,hit=h,passed=h is not None and h['material']=='raked brick' and .32<h['distance_m']<.34))
        for z,expected in [(3.91,.284),(4.93,.253),(5.077,.183),(5.23,.259)]:
            for dx in (-.28,0,.28):
                h=scene.ray([x+dx,4.0,z],[0,1,0],1.4)
                rows.append(dict(feature='projecting chimney bands',x=x+dx,z=z,hit=h,passed=h is not None and h['material']=='projecting stone' and abs(h['distance_m']-expected)<.009))
        for dx in (-.22,.22):
            for local in (-.033,.001,.039):
                h=scene.ray([x+dx+local,4.74,6.02],[0,0,-1],1.1)
                rows.append(dict(feature='real terminal recess',x=x+dx+local,hit=h,passed=h is not None and h['material']=='flue interior' and .59<h['distance_m']<.62))
            for local in (.080,-.080):
                h=scene.ray([x+dx+local,4.74,6.02],[0,0,-1],1.1)
                rows.append(dict(feature='earthenware rim',x=x+dx+local,hit=h,passed=h is not None and h['material']=='earthenware' and .14<h['distance_m']<.16))
    for x in (-1.0,-.81,.81,1.0):
        for z in (.16,.46,.93,1.21):cast('plaster beside window',x,z,{'white plaster'},.498,.502)
    for x in (-.55,-.31,.22,.53):
        for z in (.24,.65,.93,1.10):cast('front casement glass',x,z,{'pane'},.649,.658)
        for z in (.036,.448,1.267):cast('horizontal sash rail',x,z,{'sash'},.585,.594)
    for x in (-.692,0,.692):
        for z in (.23,.65,.94,1.1):cast('casement vertical',x,z,{'sash'},.585,.594)
    for x in (-.89,-.53,-.27,.09,.45,.89):
        cast('dormer gable fascia',x,2.50-.72*abs(x),{'bargeboard'},.350,.357)
    for x in (-.67,-.40,-.15,.15,.4,.67):
        cast('plain gable below fascia',x,1.70,{'white plaster'},.498,.502)
    return dict(samples=rows,passed=all(x['passed'] for x in rows))

def digest(p):
    return sha256(p.read_bytes()).hexdigest()


def main():
    ap=ArgumentParser(description=__doc__)
    ap.add_argument('--manifest',type=Path,default=PROJECT/'assets/models/candidates'/ID/'manifest.json')
    ap.add_argument('--out',required=True,type=Path)
    args=ap.parse_args()
    m=json.loads(args.manifest.read_bytes())
    assert m['id']==ID
    rows={}
    with tempfile.TemporaryDirectory() as directory:
        for role in ('raw','full','lod'):
            a=m['assets'][role]
            original=args.manifest.parent/a['file']
            assert original.stat().st_size==a['bytes'] and digest(original)==a['sha256']
            mesh=original
            if role!='raw':
                mesh=Path(directory)/(role+'.glb')
                subprocess.run(['node',UNPACK,original,mesh,DECODER],check=True,stdout=subprocess.DEVNULL)
            rows[role]=dict(sha256=a['sha256'],**test(SerialScene(mesh),role))
            if role!='raw':mesh.unlink()
    result=dict(id=ID,manifest_sha256=digest(args.manifest),checker_sha256=digest(Path(__file__)),
                reader_sha256=digest(READER),decoder_sha256=digest(DECODER),results=rows)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for role,r in rows.items():print(role,'pass' if r['passed'] else [q for q in r['samples'] if not q['passed']])
    return all(r['passed'] for r in rows.values())


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
