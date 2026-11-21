from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='xuhui-defour-apartments-mosaic-stair'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    results=[]
    def sample(name,xyz,vector,accepted,distance):
        hit=scene.ray(list(xyz),list(vector),2.0)
        ok=bool(hit and hit['material'] in accepted and abs(hit['distance_m']-distance)<.0012)
        results.append(dict(check=name,origin=list(xyz),direction=list(vector),materials=accepted,distance_m=distance,hit=hit,passed=ok))
    charcoal=['graphite tile','grey umber tile']
    brown=['umber end tile','ochre end tile']
    for i in range(4):
        pitch=.027; width=40*pitch; rise=6*pitch; going=10*pitch
        face,level=i*going,(i+1)*rise
        for col in (1,4,7,12,19,27,31,35,38):
            x=-width/2+(col+.5)*pitch
            accept=brown if col<6 or col>=34 else charcoal
            for trace in (2,6):
                sample('tread tiles', (x,face+(trace+.5)*pitch,level+.08),(0,0,-1),accept,.0786)
            sample('riser tiles',(x,face-.04,level-2.5*pitch),(0,1,0),accept,.0385)
        for col in (2,13,26,37):
            x=-width/2+(col+.5)*pitch
            sample('horizontal joint in tread',(x,face+4*pitch,level+.08),(0,0,-1),['warm grey grout'],.08)
            sample('horizontal joint in vertical riser',(x,face-.04,level-3*pitch),(0,1,0),['warm grey grout'],.04)
        for col in (6,9,17,24,32):
            x=-width/2+(col+.52)*pitch
            sample('rounded front to central tiled run',(x,face-.03,level-.002),(0,1,0),['dark bullnose','pale worn strip'],.0218)
        for side in (-1,1):
            x=side*(width/2-.04)
            for row,material in ((1,'dark skirt tile'),(6,'russet cheek tile')):
                sample('tiled cheek above tread',(x,face+4.5*pitch,level+(row+.5)*.234/8),(side,0,0),[material],.0392)
    return dict(passed=all(r['passed'] for r in results),samples=results)


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
