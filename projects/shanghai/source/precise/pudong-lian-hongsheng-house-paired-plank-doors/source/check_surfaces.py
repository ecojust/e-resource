from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='pudong-lian-hongsheng-house-paired-plank-doors'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']








def test(scene,role):
    samples=[]
    def shoot(x,y,materials,lo,hi,label):
        origin=[(x-252)*.00345,-.26,(751-y)*.00345];hit=scene.ray(origin,[0,1,0],.55)
        ok=(hit is None) if not materials else bool(hit and hit['material'] in materials and lo<=hit['distance_m']<=hi)
        samples.append(dict(feature=label,pixel=[x,y],expected_material=materials,expected_distance_m=[lo,hi],hit=hit,passed=ok))
    wood=['dark oak','weathered board','inner strip','wood ridges','worn lower grain','fine split']
    for ix,x in enumerate([43,73,113,136,164,187,213,235,271,296,337,354,389,407,447,473]):
        for y in (84,208,492,691):
            d=.260 if x<252 else .272
            shoot(x,y,wood,d-.0017,d+.0017,'vertical timber board face')
    for row in (132,645):
        for idx,x in enumerate([33,69,104,139,172,205,238,277,311,345,381,416,451,486]):
            d=.26 if idx<7 else .272
            shoot(x,row+((idx%4)-2)*.9,['blackened iron'],d-.008,d-.004,'raised iron nail')
    for y in [68,183,295,482,615,718]:shoot(256.3,y,[],0.,.55,'daylight through the open central seam')
    for x,y,d in [(224,377,.26),(232,393,.26),(275,391,.272),(290,402,.272)]:
        shoot(x,y,['pale fitting'],d-.0065,d-.0043,'square metal plate on each leaf')
    shoot(240,412,['lock steel'],.222,.226,'separate padlock below the left eye')
    return dict(samples=samples,passed=all(s['passed']for s in samples))

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
