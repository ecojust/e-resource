from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='changning-yang-garden-triple-parapet'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    from math import sqrt, sin, cos, pi
    def arch_y(x, radius, segments):
        points=[(radius*cos(pi*i/segments),radius*sin(pi*i/segments))for i in range(segments+1)]
        for (a,u),(b,v) in zip(points,points[1:]):
            if b<=x<=a:return u+(v-u)*(a-x)/(a-b)
        raise ValueError(x)
    rows=[]
    def ray(label,x,z,material,depth):
        result=scene.ray([x,-.55,z],[0,1,0],2.0)
        passed=bool(result and result['material']==material and abs(result['distance_m']-(depth+.55))<.012)
        rows.append(dict(label=label,origin=[x,-.55,z],direction=[0,1,0],expected_material=material,expected_distance_m=depth+.55,observed=result,passed=passed))
    for c in (-2.13,0,2.13):
        for dx in (-.53,-.32,.22,.47):
            for z in (1.04,1.55,1.87,2.16):
                ray('recessed casement panes',c+dx,z,'window glass',.158)
        for z in (1.04,1.32,1.71,2.10,2.22):
            ray('meeting stile',c,z,'sash metal',.086)
            for side in (-1,1):
                ray('light window jamb',c+side*.831,z,'cast stone',-.043)
                ray('casement side edge',c+side*.747,z,'sash metal',.1)
                ray('window reveal lining',c+side*.779,z,'reveal shade',.027)
        for dx in (-.61,-.432,-.205,0,.35,.60):
            ray('flat lintel',c+dx,2.395,'cast stone',-.046)
            ray('elliptical cap step',c+dx,2.975+sqrt(.768**2-dx**2)+.027,'cast stone',-.112)
            ray('crest face',c+dx,2.85,'warm render',0)
            ray('sill top',c+dx,.850,'cast stone',-.141)
            ray('sill drip',c+dx,.785,'drip edge',-.105)
            ray('inset panel field',c+dx,.56,'panel face',-.038)
            ray('base lip',c+dx,.045,'cast stone',-.14)
        for dx in (-.54,.18,.52):ray('outer panel shadow line',c+dx,.289,'recessed joint',-.008)
        for dx in (-.408,-.218,.318,.506):
            top_of_crown=max(arch_y(dx,.768,n)+.061 for n in (14,44))
            top_of_strip=min(arch_y(dx,.762,n)+.078 for n in (14,44))
            assert top_of_strip>top_of_crown
            ray('top strip',c+dx,2.975+(top_of_crown+top_of_strip)/2,'drip edge',-.08)
    for x in (-1.065,1.065):
        for z in (.41,1.5,1.9,2.65):ray('dividing pier',x,z,'cast stone',-.047)
        ray('pier neck',x,2.865,'drip edge',-.068)
    return dict(passed=all(k['passed'] for k in rows),samples=rows)

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
