from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-nanguan-customs-upper-timber-windows'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    results=[]
    def sample(name,x,z,y,mats):
        eye=[x,-.3,z];r=scene.ray(eye,[0,1,0],.70)
        results.append(dict(feature=name,origin=eye,expected_y=y,materials=mats,observed=r,passed=bool(r and r['material']in mats and abs(r['distance_m']-.30-y)<.008)))
    glass=['left dark glass','muted glass','smoky green glass','glass reflected sky']
    for i,(lo,hi) in enumerate([(-1.42,-.47),(.47,1.42)]):
        middle=(lo+hi)/2
        for x in (lo+.019,hi-.018,middle):
            for z in (.40,.82,1.20,1.84,2.20):sample('outer jamb',x,z,.018,['dark red jamb'])
        for x in (lo+.19,lo+.26,hi-.18):
            sample('sill projected nose',x,.278,-.103,['sill top']); sample('lower stone underside',x,.240,-.096,['shaded sill fascia'])
        for upper,(z0,z1) in enumerate([(.356,1.565),(1.617,2.274)]):
            for side,(x0,x1) in enumerate([(lo+.045,middle-.020),(middle+.020,hi-.045)]):
                m='green transom' if i and upper else 'oxblood sash';sx=(x0+x1)/2
                for z in (z0+.18,z1-.15):
                    sample('painted casement edge',x0+.014,z,.039,[m]); sample('narrow glazing bar',sx,z,.065,[m]);sample('recessed glazing',sx-.053,z,.110,glass);sample('recessed glazing',sx+.057,z,.110,glass)
                if not upper:sample('horizontal lower glazing bar',sx+.07,(z0+z1)/2,.064,[m])
    for x in (-1.56,-.32,.13,.33,1.56):sample('plaster pier',x,1.22,0,['limewash'])
    return dict(passed=all(r['passed']for r in results),samples=results)

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
