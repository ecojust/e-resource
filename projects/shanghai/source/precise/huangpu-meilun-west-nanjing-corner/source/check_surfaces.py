"""Probe the entrance recesses, two pediments and adjoining stone fronts at 161 East Nanjing Road."""
from argparse import ArgumentParser
import numpy as np
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-meilun-west-nanjing-corner'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']


def test(scene,role):
    study=json.loads((SOURCE.parent/'corner-study.json').read_bytes())['corner']
    north,west=study['nanjing_end'],study['west_end']
    edge_defs=[([north[0]+12.8,north[1]],north,2,.74,'Nanjing'),
               (north,west,1,.86,'diagonal'),
               (west,study['west_study_end'],1,.67,'Jiangxi')]
    rows=[]
    for a,b,bays,depth,street in edge_defs:
        a,b=np.array(a),np.array(b)
        length=float(np.linalg.norm(b-a))
        t=(b-a)/length
        n=np.array([t[1],-t[0]])
        def check(name,u,z,expected,lo,hi,offset=2.):
            xy=(a+b)/2+t*u+n*offset
            origin=[float(xy[0]),float(xy[1]),float(z)]
            direction=[float(-n[0]),float(-n[1]),0.]
            hit=scene.ray(origin,direction,5.)
            success=(hit is None) if expected is None else bool(hit and hit['material']==expected and lo<=hit['distance_m']<=hi)
            rows.append(dict(test=street+' '+name,origin=origin,direction=direction,
                             expected=expected,allowed_distance_m=[lo,hi],hit=hit,passed=success))
        bay=length/bays; corner=street=='diagonal'
        for i in range(bays):
            ax=-length/2+bay*(i+.5);tag=f'bay {i+1} '
            for dx in (-.24,.21):
                check(tag+'shop glazing',ax+dx,1.39,'shop and office glazing',2.30+depth,2.34+depth)
            check(tag+'shop transom',ax+.21,2.20,'dark bronze sash',2.14+depth,2.18+depth)
            check(tag+'belt course',ax+.16,4.82,'dressed grey stone',1.62,1.66)
            groups=[(ax-bay*.227,bay*.111),(ax,bay*.261),(ax+bay*.227,bay*.111)] if corner else [(ax-bay*.226,bay*.31),(ax+bay*.226,bay*.31)]
            for j,(x,width) in enumerate(groups):
                for floor,z in enumerate([5.93,10.18],start=2):
                    check(tag+f'floor {floor} light {j+1}',x+width*.16,z,'shop and office glazing',2.30,2.34)
                    if width>1.:
                        check(tag+f'floor {floor} mullion {j+1}',x,z,'dark bronze sash',2.14,2.18)
            check(tag+'stone pier',max(-length/2+.32,ax-bay/2+.32),1.85,'grey facing stone',1.71,1.77)
            check(tag+'projecting cornice',ax+.16,13.27,'dressed grey stone',1.415,1.45)
            if corner:
                for side in (-1,1):
                    check('small column',ax+side*bay*.158,6.43,'dressed grey stone',1.74,1.79)
                check('lower pediment tympanum',ax,8.55,'grey facing stone',1.70,1.74)
                check('upper pediment tympanum',ax,13.94,'grey facing stone',1.70,1.74)
            else:
                check(tag+'balustrade rail',ax+.32,13.72,'dressed grey stone',1.86,1.90)
            check(tag+'sky above roof',ax,15.1,None,0,5)
    return dict(passed=all(q['passed'] for q in rows),samples=rows)


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
    result=dict(id=ID,manifest_sha256=digest(args.manifest),checker_sha256=digest(Path(__file__)),
                reader_sha256=digest(READER),decoder_sha256=digest(DECODER),results=rows)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for role,r in rows.items():print(role,'pass' if r['passed'] else [q for q in r['samples'] if not q['passed']])
    return all(r['passed'] for r in rows.values())


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
