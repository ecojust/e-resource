from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-former-german-post-office-fluted-bow-aprons'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    from math import sin,cos
    samples=[]
    def cast(label,t,z,material,projected):
        r=2.12+.43;origin=[r*sin(t),2.12-r*cos(t),z];direction=[-sin(t),cos(t),0.]
        value=scene.ray(origin,direction,.85)
        samples.append(dict(feature=label,origin=origin,direction=direction,expected_material=material,expected_radius=2.12+projected,observed=value,passed=bool(value and value['material']==material and abs(value['distance_m']-(.43-projected))<.004)))
    for a,b,count in [(-.99,-.50,9),(-.32,.32,13)]:
        step=(b-a)/count
        for i in range(count):
            t=a+(i+.50)*step
            for z in (.115,.733):cast('recessed flute centre',t,z,'light mineral finish',.003)
            cast('raised flute divider',a+(i+.012)*step,.42,'light mineral finish',.043)
            cast('projecting sill cap',t,.994,'curved sill stone',.108)
            cast('shaded sill bed',t,.936,'shaded fascia',.047)
            cast('base return',t,.016,'lower return',.038)
    for t in [-1.032,-.462,-.395,-.342,.375]:
        cast('plain pier',t,.66,'smooth pier facing',.020)
        cast('pier bed joint',t,.43,'narrow bed joint',.012)
    return dict(samples=samples,passed=all(x['passed'] for x in samples))

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
