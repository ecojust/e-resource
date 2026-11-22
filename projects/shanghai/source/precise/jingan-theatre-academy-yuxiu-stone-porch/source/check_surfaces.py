from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='jingan-theatre-academy-yuxiu-stone-porch'
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
    def probe(kind,start,direction,limit,materials,lo,hi):
        h=scene.ray(start,direction,limit)
        rows.append(dict(feature=kind,start=start,direction=direction,expected=sorted(materials),depth_m=[lo,hi],hit=h,passed=h is not None and h['material'] in materials and lo<=h['distance_m']<=hi))
    for i in range(4):
        base=i*.163
        for x in (-.78,-.61,-.48,-.32,-.08,.12,.28,.42,.66,.78):
            probe('stone riser',[x,i*.32-.17,base+.071],[0,1,0],.32,{'stone tread'},.168,.172)
            probe('tread surface',[x,i*.32+.15,base+.32],[0,0,-1],.24,{'stone tread','limestone','tread joint'},.146,.162)
    for side in (-1,1):
        for y in (.23,.43,.67,.89,1.07,1.19):
            top=.374+(y-.13)*(.938-.374)/(1.31-.13)
            probe('sloping side wall',[side*1.125,y,1.35],[0,0,-1],1.15,{'limestone'},1.35-top-.004,1.35-top+.004)
        for y in (-.22,-.09,.03):
            probe('low front pier cap',[side*1.125,y,.65],[0,0,-1],.60,{'stone tread'},.256,.262)
        for course in (4,6,8,10,12,14,16):
            z=.65+course*.112+.054
            probe('laid brick pier',[side*1.125+.09,1.05,z],[0,1,0],.40,{'rose brick','dun brick','gray brick'},.239,.247)
    import math
    for x in (-.96,-.80,-.61,-.45,-.27,.27,.45,.61,.80,.96):
        z=3.326+math.sqrt(1.68**2-x*x)-1.68
        for y in (.80,1.16,1.43):
            if abs(x)>.9:
                material,depth={.80:('trim',.265),1.16:('trim',.049),1.43:('limestone',.294)}[y]
                probe('impost or sloping bracket carries the end of the canopy',[x,y,2.61],[0,0,1],.80,{material},depth-.007,depth+.007)
            else:
                probe('curved light soffit',[x,y,2.61],[0,0,1],.80,{'soffit'},z-.052-2.61-.006,z-.052-2.61+.005)
        probe('brown front edge',[x,0,z+.036],[0,1,0],.90,{'trim'},.662,.668)
    for x in (-.69,-.49,-.28,0,.28,.49,.69):
        probe('timber transom behind the pendant',[x,1.46,2.976],[0,1,0],.4,{'recessed wood'},.182,.186)
    for x in (-.65,-.51,-.33,-.21):
        for z in (1.78,1.97,2.15,2.34):
            probe('left glazed panel',[x,1.45,z],[0,1,0],.45,{'glazing'},.258,.267)
    for x in (.17,.43,.69):
        for z in (.87,1.12,1.63,1.91,2.43):
            h=scene.ray([x,1.45,z],[0,1,0],.56)
            rows.append(dict(feature='open door leaf',x=x,z=z,hit=h,passed=h is None))
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
