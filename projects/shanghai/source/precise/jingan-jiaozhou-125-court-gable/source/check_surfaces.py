from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='jingan-jiaozhou-125-court-gable'
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
    # Front rays sample the projecting drip, each of the twelve lights and the verge.
    for side in (-1,1):
        for i in range(9):
            x=side*(.042+i*.088);z=3.30-.84/.82*abs(x)
            cast('cement verge cap',x,z,{'verge cement'},.469,.473)
            cast('pink gable field',x,z-.104,{'pink render','sand grains','pale grains'},.491,.502)
        for i in range(7):
            x=side*(.052+i*.117)
            cast('grey plinth',x,.18,{'grey plinth','weathered plinth'},.475,.483)
        for i in range(4):
            cast('gate iron',-1.50+.155*i if side<0 else .97+.148*i,1.13,{'gate iron'},.578,.582)
    a,c,base,head=-2.55,-1.82,.86,2.02
    width=(c-a)/2
    for i in range(2):
        left=a+i*width;right=left+width;middle=(left+right)/2
        for j in range(3):
            z=base+.065+(j+.5)*((head-base)-.13)/3
            for x in (left+.105,right-.105):
                cast('recessed glass beside bars',x,z,{'window glass'},.611,.615)
            cast('central vertical glazing bar',middle,z,{'wood edge'},.565,.569)
            cast('window meeting or outside stile',left+.015,z,{'wood'},.548,.552)
        for j in (1,2):
            z=base+.065+j*((head-base)-.13)/3
            cast('fine horizontal glazing bar',left+.093,z,{'wood edge'},.561,.565)
    for i in range(13):
        x=a+.03+i*.054
        cast('white sill',x,base-.03,{'window trim'},.403,.407)
        cast('white drip crown',x,head+.04,{'window trim'},.450,.454)
    # Vertical rays distinguish the overlapping tile courses from the flat verge face.
    for side in (-1,1):
        for row in range(4):
            x=side*(.096+row*.21)
            for col in (0,2,4,6):
                y=.09+.147*col+.065
                hit=scene.ray([x,y,3.7],[0,0,-1],1.5)
                expected=3.7-(3.30-.84*abs(x)/.82)
                ok=hit is not None and hit['material'] in {'tile burnt umber','tile dried earth','tile dark red'} and expected-.065<=hit['distance_m']<=expected-.015
                rows.append(dict(feature='rolled roof tile course',origin=[x,y,3.7],direction=[0,0,-1],hit=hit,passed=ok))
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
