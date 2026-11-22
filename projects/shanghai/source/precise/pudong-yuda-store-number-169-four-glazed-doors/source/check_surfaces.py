from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='pudong-yuda-store-number-169-four-glazed-doors'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']








def test(scene,role):
    from math import cos,sin,radians
    samples=[]
    for k,(c,angle,pivot)in enumerate(zip((-.747,-.249,.249,.747),(0,-7.5,10.,0),(-.249,-.249,.249,.249))):
        a=radians(angle);dx,dy=-sin(a),cos(a)
        def check(u,z,materials,depth,label):
            start=-.29;origin=[c+pivot+(u-pivot)*cos(a)-start*sin(a),(u-pivot)*sin(a)+start*cos(a),z]
            direction=[dx,dy,0];hit=scene.ray(origin,direction,.60)
            passed=bool(hit and hit['material'] in materials and abs(hit['distance_m']-(depth-start))<.003)
            samples.append(dict(feature=label,leaf=k+1,origin=origin,direction=direction,expected_face=depth,hit=hit,passed=passed))
        for u in (-.225,.225):
            for z in (.081,.319,.68,1.07,1.54,1.89,2.15):check(u,z,['ebonised stile'],-.023,'long stile on measured tilt')
        for u in (-.17,-.091,.09,.17):
            for z in (.138,.773,2.118):check(u,z,['dark rail'],-.021,'timber horizontal rail')
        for u in (-.044,0,.044):
            for z in (1.412,1.475,1.529):check(u,z,['dark square pane'],.041,'central dark rectangular light')
        for u in (-.121,.121):
            for z in (.386,.460):check(u,z,['faded plank'],-.001,'recessed lower panel')
        for u in (-.157,.157):check(u,.423,['carved wood'],-.014,'outer frame around recessed lower panel')
        for u in (-.055,.055):check(u,1.815,['blue grey glass','reflected grey glass'],.044,'glazing behind geometric muntins')
    for x in (-1.175,1.175):
        for y in (-.474,-.396,-.171,-.099):
            o=[x,y,.67];hit=scene.ray(o,[0,0,-1],1)
            samples.append(dict(feature='round-fronted stone threshold guard',origin=o,direction=[0,0,-1],hit=hit,passed=bool(hit and hit['material']=='stone block'and .267<hit['distance_m']<.365)))
    for x in (-.71,-.34,0,.34,.71):
        hit=scene.ray([x,-.246,.54],[0,0,-1],1)
        samples.append(dict(feature='forward granite threshold',hit=hit,passed=bool(hit and hit['material']=='stone threshold'and abs(hit['distance_m']-.505)<.003)))
    return dict(samples=samples,passed=all(row['passed']for row in samples))

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
