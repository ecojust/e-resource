from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='jingan-fumin-village-four-sign-panels'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']








def test(scene,role):
    from shapely.geometry import Point
    src=runpy.run_path(str(SOURCE/'sign_panels.py'))
    glyphs=json.loads((SOURCE/'four-letters.json').read_bytes())['glyphs']
    out=[]
    def ray(x,z,expected,depth,label):
        hit=scene.ray([x,-.4,z],[0,1,0],.9)
        ok=hit is not None and hit['material'] in expected and abs(hit['distance_m']-(.4-depth))<.0015
        out.append(dict(label=label,x=x,z=z,expected_material=sorted(expected),expected_depth=depth,hit=hit,passed=ok))
    for index,g in enumerate(glyphs):
        geom=src['ink_geometry'](g,index);dense=geom.buffer(-.009)
        lo,bottom,hi,top=geom.bounds
        for i in range(17):
            for j in range(17):
                x=lo+(hi-lo)*(i+.43)/17;z=bottom+(top-bottom)*(j+.51)/17
                if dense.contains(Point(x,z)):
                    ray(x,z,{'claret face'},.072,g['character']+' 字面')
        cx,width,height=src['PANELS'][index]
        for t in (.12,.37,.58,.81):
            ray(cx-width/2+.018,.40+t*(height-.03),{'buff panel','quartz light','grey inclusions','paler ochre'},.044,g['character']+' 牌面')
        for t in (.12,.31,.55,.77):ray(cx+(t-.5)*width,.392,{'raised stone margin'},.047,'下口')
    return dict(samples=out,passed=all(item['passed']for item in out))

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
