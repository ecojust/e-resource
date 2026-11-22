"""Test the nested stone arch, recessed entrance, six tall windows, balcony railing and gable in three real meshes."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='jingan-science-hall-school-arched-entrance'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    rows=[]
    def ray(label,x,z,materials,interval,from_y=-1.2):
        hit=scene.ray([x,from_y,z],[0,1,0],3.0)
        ok=hit is None if not materials else bool(hit and hit['material'] in materials and interval[0]<=hit['distance_m']<=interval[1])
        rows.append(dict(check=label,x=x,z=z,from_y=from_y,materials=materials,distance_interval=interval,intersection=hit,passed=ok))
    for side in [-1,1]:
        for z in [1.17,1.59,1.92]:
            for x,materials,interval in [(1.59,['sandstone'],(1.15,1.17)),(1.22,['sandstone'],(1.15,1.18)),(1.04,['stone reveal'],(1.24,1.27)),(.87,['sandstone'],(1.32,1.36))]:
                ray('stone doorway stepped return',side*x,z,materials,interval)
        ray('outer granite plinth',side*1.57,.49,['granite base'],(1.05,1.10))
        ray('red brick side pier',side*1.95,7.14,['red field brick','dark fired brick','salmon brick'],(1.18,1.21))
        ray('balcony side rail',side*.83,14.34,['balcony iron'],(.39,.46))
        ray('empty outside the authored wall',side*2.45,8.2,[],(0,0))
    for x in [-.57,-.24,.24,.57]:
        for z in [.45,1.37,1.88]:
            ray('deep inner entrance remains recessed',x,z,['dark timber'],(1.87,1.90))
    for z,materials,interval in [(2.70,['dark timber'],(1.87,1.91)),(2.90,['sandstone'],(1.33,1.36)),(3.06,['stone reveal'],(1.24,1.28)),(3.23,['sandstone'],(1.15,1.18)),(4.15,['sandstone'],(1.15,1.17))]:
        ray('arched head concentric depths',0,z,materials,interval)
    for s0,s1 in [(5.22,8.27),(9.50,12.42)]:
        for x,width in [(-.88,.48),(0,.79),(.88,.48)]:
            for dx in [-.11,.10]:
                for t in [.13,.38,.63,.81]:
                    ray('tall recessed steel window pane',x+dx,s0+(s1-s0)*t,['window glass'],(1.43,1.46))
            ray('steel window transom',x+.11,s0+.48*(s1-s0),['painted steel'],(1.35,1.41))
        ray('squared vertical stone separating lights',.56,(s0+s1)/2,['sandstone'],(1.17,1.20))
    for x in [-.27,.27]:ray('upper recessed balcony door glazing',x,14.65,['window glass'],(1.42,1.47))
    for x in [-.50,.26,.55]:
        ray('projecting balcony slab',x,13.48,['cap stone'],(.35,.46))
        ray('projecting iron front handrail',x,14.34,['balcony iron'],(.40,.46))
    for k in range(4):ray('stepped gable shaft tab',0,17.94-.42-k*.207,['sandstone'],(1.06,1.11))
    for x in [-1.6,.74,1.56]:
        z=17.94-abs(x)/2.20*(17.94-16.09)+.029
        ray('raked gable coping edge',x,z,['cap stone'],(1.10,1.14))
    ray('sky above the central ridge',0,18.30,[],(0,0))
    return dict(passed=all(row['passed']for row in rows),samples=rows)

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
            rows[role]=dict(sha256=a['sha256'],**test(SerialScene(mesh)))
            if role!='raw':mesh.unlink()
    result=dict(id=ID,manifest_sha256=digest(args.manifest),checker_sha256=digest(Path(__file__)),
                reader_sha256=digest(READER),decoder_sha256=digest(DECODER),results=rows)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for role,r in rows.items():print(role,'pass' if r['passed'] else [q for q in r['samples'] if not q['passed']])
    return all(r['passed'] for r in rows.values())


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
