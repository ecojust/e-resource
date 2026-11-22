"""Check the surviving house’s loggias, faceted bay windows, attic lights and garden roof."""
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
ID='jingan-wenlian-old-house'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']


def test(scene,role):
    rows=[]
    def ray(label,point,direction,length,wanted,lo=0,hi=20):
        hit=scene.ray(point,direction,length)
        ok=hit is None if wanted is None else bool(hit and hit['material']==wanted and lo<=hit['distance_m']<=hi)
        rows.append(dict(test=label,origin=list(map(float,point)),direction=list(map(float,direction)),length_m=length,expected_material=wanted,range_m=[lo,hi],hit=hit,passed=ok))
    glass='grey blue glazing'
    trim='carved pale stone'
    for x in [-6.08,-3.68,-1.25,1.25,3.68,6.08]:
        ray(f'upper garden window {x}',[x+.22,-3,10.39],[0,1,0],8,glass,4.72,4.78)
        ray(f'segmental hood {x}',[x,-3,12.205],[0,1,0],7,trim,4.07,4.27)
    for x in [-5.5,0,5.5]:
        ray(f'living room garden door {x}',[x+.12,-3,1.58],[0,1,0],8,glass,5.84,5.92)
    for x in [-5.96,-4.09,-1.37,1.37,4.09,5.96]:
        ray(f'middle loggia rear window {x}',[x+.12,.6,6.1],[0,1,0],4,glass,2.25,2.32)
    for x in [-6.88,-2.96,2.96,6.88]:
        for offset in (-.245,.245):
            for h in (1.48,5.93):
                ray(f'paired loggia post {x+offset:.3f} at {h}',[x+offset,-3,h],[0,1,0],5,trim,2.79,2.90)
        ray(f'balustrade stone pier {x}',[x,-3,4.91],[0,1,0],4,trim,2.74,2.86)
    for x in (-11.255,11.255):
        ray(f'gable small square light {x}',[x+.19,-3,15.19],[0,1,0],7,glass,3.65,3.70)
        ray(f'gable crest finial {x}',[x,.16,18.5],[0,0,-1],5,trim,.97,1.04)
        ray(f'upper balcony door {x}',[x+.18,-3,10.87],[0,1,0],7,glass,3.65,3.70)
    for x in (-11.04,11.04):
        for z in (2.18,6.07):
            ray(f'lower faceted bay window {x} at {z}',[x+.15,-4,z],[0,1,0],5,glass,1.80,1.85)
    for x in (-5.,0.,5.):
        ray(f'open lower colonnade {x}',[x,.52,1.68],[0,0,-1],3,'grey loggia paving',1.35,1.37)
        ray(f'upper colonnade floor {x}',[x,.60,5.90],[0,0,-1],3,'grey loggia paving',1.53,1.55)
        ray(f'clear pavement {x}',[x,-1.3,1.6],[0,0,-1],2,None)
        ray(f'central roof pitch {x}',[x,3.5,16.5],[0,0,-1],5,'weathered terracotta',3.17,3.29)
    ray('second garden step',[.4,-.61,1],[0,0,-1],1,'grey granite',.78,.80)
    ray('open column bay between paired shafts',[0,-2,1.7],[0,1,0],3.5,None)
    for x,width in [(-5.5,2.35),(0,3.14),(5.5,2.35)]:
        for sign in (-1,1):
            ray(f'lower timber door leaf {x}/{sign}',[x+sign*width*.195,-1,.86],[0,1,0],4,'dark timber window sash',3.56,3.67)
        ray(f'porch pendant {x}',[x+.031,1.24,3.0],[0,0,1],1,'opal porch light',.30,.37)
    for x in (-6.42,6.43):
        ray(f'chimney is seated on the roof {x}',[x,4.67,13.93],[0,1,0],.8,'warm grey pebble render',.19,.24)
    return dict(passed=all(x['passed']for x in rows),samples=rows)


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
