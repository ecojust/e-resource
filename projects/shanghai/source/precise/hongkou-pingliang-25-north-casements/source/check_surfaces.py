from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='hongkou-pingliang-25-north-casements'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']








def test(scene,role):
    from math import cos,sin,radians
    rows=[]
    def cast(feature,x,z,material,depth,tol=.009):
        h=scene.ray([x,-.62,z],[0,1,0],1.03)
        if isinstance(material,str):material={material}
        rows.append(dict(feature=feature,x=x,z=z,materials=sorted(material),depth=depth,hit=h,passed=h is not None and h['material']in material and abs(h['distance_m']-depth)<tol))
    for x in (-.936,.936):
        for z in (.34,.55,.87,1.12,1.40,1.74,2.04):
            cast('shallow inset stone panel',x,z,'panel inset',.525)
            cast('projecting edge of tablet',x-.136,z,'stone arris',.507)
            cast('outer body beside tablet',x+.163,z,'stone face',.536)
    for x in (-.93,-.71,-.38,-.07,.26,.70,.91):
        cast('raised stone sill',x,.146,'stone arris',.476)
        cast('continuous lower sill bed',x,.098,'stone face',.499)
    w=.740;half=.748;h=2.13-.378-.253+.01
    for right in (False,True):
        a=radians(14) if right else 0
        for u in (.083,.19,.52,.65):
            for v in (.15,.31,.70,.83,1.23):
                x=half-(w-u)*cos(a)if right else-half+u
                d=.078-(w-u)*sin(a)if right else .085
                cast('glass on the open or closed leaf',x,.253+v,{'reflected glass','aged glass'},.62+d+.017)
        for u in (.12,.46,.62):
            x=half-(w-u)*cos(a)if right else-half+u
            d=.078-(w-u)*sin(a)if right else .085
            for v in (h/3,2*h/3):cast('two glazing bars of lower casement',x,.253+v,'steel edge',.62+d-.006)
    tilt=radians(17);height=.378+.035
    for u in (.14,.49,.88,1.26):
        for v in (.081,.14,.279,.347):
            x=-half+u;z=2.13+.085-(height-v)*cos(tilt);d=.064-(height-v)*sin(tilt)
            cast('projecting two-row top light',x,z,{'reflected glass','aged glass'},.62+d+.017)
    return dict(samples=rows,passed=all(q['passed'] for q in rows))

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
