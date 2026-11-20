"""Check the independently decoded doorway, civic plate, window bands and cropped party boundaries of No. 12."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='jingan-jinghua-village-no12'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']


def test(scene):
    samples=[]
    def front(label,x,z,expected,depth):
        origin=[x,-4,z];hit=scene.ray(origin,[0,1,0],9)
        ok=hit is None if expected is None else hit is not None and hit['material']==expected and abs(hit['distance_m']-(4-depth))<.015
        samples.append(dict(label=label,origin=origin,expected_material=expected,expected_outward_depth_m=depth,hit=hit,passed=ok))
    ground=(-.72,.74,3.15,2.22,4,[.72],'pale curtains behind glass')
    second=(-1.91,4.12,3.82,2.06,5,[.25,.50,.75],'smoke blue glass')
    third=(-1.91,7.64,3.82,1.35,5,[.34,.68],'smoke blue glass')
    for left,sill,width,height,count,transoms,material in [ground,second,third]:
        edges=[0,*transoms,1]
        for column in range(count):
            x=left+(column+.43)*width/count
            for a,b in zip(edges,edges[1:]):
                front('glazing by column and transom tier',x,sill+(a+b)*height/2,material,-.158)
            for fraction in transoms:
                front('painted horizontal glazing bar',x,sill+fraction*height,'deep green painted steel',-.051)
        for i in range(1,count):
            front('vertical mullion',left+i*width/count,sill+.18*height,'deep green painted steel',-.051)
    for z in (2.32,2.49,2.66):
        front('horizontal guard in the door transom',-1.79,z,'dark brown timber',-.2075)
    for z in (2.405,2.575,2.735):
        front('glazed door transom',-1.79,z,'smoke blue glass',-.298)
    for x in (-2.102,-1.77,-1.438):
        front('recessed door leaf',x,.64,'dark brown timber',-.279)
        front('raised timber panel edge',x-.112,.64,'raised door panel',-.258)
    for label,x,z,mat,d in [
        ('white door surround',-2.333,1.08,'ivory rendered trim',.068),
        ('green plate',-.84,1.940,'green enamel',.0375),
        ('numeral 1',-.98565,1.93065,'ivory enamel',.050),
        ('numeral 2',-.90325,1.92715,'ivory enamel',.050),
        ('planter face',.45,.135,'grey cement base',.610),
        ('cement plinth between the doors and windows',-1.03,.52,'grey cement base',.028),
        ('ground floor horizontal hood',.5,3.275,'ivory rendered trim',.4665),
        ('middle floor projecting hood',.5,6.49,'grooved buff render',.464),
        ('roof eave',.5,9.56,'ivory rendered trim',.4625),
        ('left boundary fin',-2.823,6.47,'grooved buff render',.363),
        ('right boundary fin',2.823,6.47,'grooved buff render',.363),
        ('beyond the left party line',-2.99,4.8,None,None),
        ('beyond the right party line',2.99,4.8,None,None),
        ('above the roof edge',.4,9.85,None,None)]:
        front(label,x,z,mat,d)
    return dict(samples=samples,passed=all(r['passed']for r in samples))


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
    result=dict(id=ID,manifest_sha256=digest(args.manifest),checker_sha256=digest(Path(__file__)),
                reader_sha256=digest(READER),decoder_sha256=digest(DECODER),results=rows)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for role,r in rows.items():print(role,'pass' if r['passed'] else [q for q in r['samples'] if not q['passed']])
    return all(r['passed'] for r in rows.values())


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
