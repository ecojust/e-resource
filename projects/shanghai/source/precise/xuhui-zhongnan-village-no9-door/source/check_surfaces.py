"""Measure the boarded leaf, iron step, glazed cells, lock, handle and No. 9 plate."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='xuhui-zhongnan-village-no9-door'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']


def test(scene,role):
    rows=[]
    def ray(label,start,direction,length,materials,span=None):
        hit=scene.ray(start,direction,length)
        ok=hit is None if not materials else bool(hit and hit['material']in materials and (not span or span[0]<=hit['distance_m']<=span[1]))
        rows.append(dict(test=label,origin=start,direction=direction,maximum_m=length,
                         expected_materials=materials,expected_distance_m=span,hit=hit,passed=ok))
    def front(label, x, z, material, span):
        ray(label, [x,-.5,z], [0,1,0], .8, [material] if material else [], span)
    for x in [-.31, -.23, -.14, -.04, .04, .14, .23, .31]:
        front('individual lower plank',x,1.03,'slightly lighter green boards',[.471,.475])
    for x in [-.27225,-.18150,-.09075,0,.09075,.18150,.27225]:
        front('recess between adjacent board edges',x,.752,'deep green painted timber',[.479,.483])
    for x,z in [(-.415,1.50),(.416,1.70),(0,1.49),(0,2.06)]:
        front('stiles and rails retain the actual opening',x,z,'deep green painted timber',[.460,.464])
    for x in [-.491,.493]:
        front('outer jamb',x,.63,'deep green painted timber',[.434,.438])
    for x,z in [(-.10,1.842),(0,1.842),(.10,1.842),(-.228,1.780),(.228,1.780),(-.301,1.720),(.301,1.720)]:
        front('continuous stepped iron profile',x,z,'dark painted transom iron',[.450,.454])
    for x in [-.074,.074]:
        for z in [1.613,1.78,1.940]:
            front('two independent vertical iron rods',x,z,'dark painted transom iron',[.450,.455])
    for x,z in [(-.32,1.62),(-.15,1.63),(0,1.64),(.15,1.63),(.32,1.62),(-.32,1.85),(-.12,1.92),(0,1.93),(.12,1.92),(.32,1.85)]:
        front('unobscured glazing on either side of bars',x,z,'grey glass in the transom',[.484,.488])
    for x,z,span in [(-.437,1.142,[.447,.453]),(-.432,.945,[.391,.403]),(-.470,.890,[.401,.414])]:
        front('lock or projecting brass pull',x,z,'worn brass lock and pull',span)
    for x,z,material,span in [(.406,2.207,'cream enamel digit',[.415,.419]),(.430,2.175,'cream enamel digit',[.415,.419]),
                                (.408,2.174,'blue green enamel address plaque',[.420,.424]),(.477,2.188,'blue green enamel address plaque',[.420,.424])]:
        front('solid raised 9 and green plate',x,z,material,span)
    for x,z in [(-.56,1.4),(.60,.9),(0,2.40)]:
        front('adjacent wall and upper stories are outside this door study',x,z,None,None)
    return dict(triangles=len(scene.tri),samples=rows,passed=all(r['passed']for r in rows))


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
    result=dict(id=ID,manifest_sha256=digest(args.manifest),checker_sha256=digest(Path(__file__)),
                reader_sha256=digest(READER),decoder_sha256=digest(DECODER),results=rows)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for role,r in rows.items():print(role,'pass' if r['passed'] else [q for q in r['samples'] if not q['passed']])
    return all(r['passed'] for r in rows.values())


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
