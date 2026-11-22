from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='jingan-customs-library-stone-roundel'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']








def test(scene,role):
    rows=[]
    def cast(kind,x,z,options,lo,hi):
        hit=scene.ray([x,-.5,z],[0,1,0],1.11)
        ok=hit is not None and hit['material'] in options and lo<=hit['distance_m']<=hi
        rows.append(dict(feature=kind,x=x,z=z,expected_material=sorted(options),depth_interval_m=[lo,hi],hit=hit,passed=ok))
    for x in (-.54,-.39,-.18,.08,.24,.43,.55):
        for z in (.126,.390,.592,1.412):
            if abs(x)>.53 and z==.592:
                cast('lower collar crosses the nominal ashlar point',x,z,{'stone ties'},.443,.464)
            else:
                cast('ashlar face',x,z,{'sandstone','light ashlar','cool ashlar'},.514,.519)
    for i in range(13):
        x=-.68+i*.11
        for z,depth in [(1.481,.485),(1.550,.458),(1.600,.436),(1.645,.448),(1.709,.429)]:
            cast('stepped cornice',x,z,{'light ashlar','sandstone'},depth-.002,depth+.002)
    for x in (-.273,.273):
        for z in (.675,.745,.91,1.018,1.145,1.24):
            cast('recess around the roundel',x,z,{'recess'},.579,.583)
    for x in (-.145,-.083,0,.11,.156):
        for z in (.867,.930,.997,1.057):
            cast('carved relief',x,z,{'sculpted stone'},.512,.538)
    for x in (-.609,.609):
        for level in (.686,.857,1.028):
            cast('centre of oblique tie',x,level,{'stone ties'},.422,.431)
            cast('exposed central rod',x,level+.074,{'flutes'},.423,.434)
        for z in (.574,1.381):
            cast('top and bottom collars',x,z,{'stone ties'},.421,.434)
    from math import sin,cos,pi
    for j in range(16):
        angle=2*pi*j/16;radius=.258*.98
        cast('raised bead round the stone carving',radius*cos(angle),.965+radius*1.01*sin(angle),{'round rim'},.492,.511)
    return dict(samples=rows,passed=all(x['passed'] for x in rows))

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
