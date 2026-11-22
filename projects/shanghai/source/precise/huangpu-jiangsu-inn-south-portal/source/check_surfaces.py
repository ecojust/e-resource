"""Probe the lane portal, green number 50, twin columns, red-brown glazing and stepped gable."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-jiangsu-inn-south-portal'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    samples=[]
    def cast(name,x,z,names,lo,hi):
        hit=scene.ray([x,-2,z],[0,1,0],5)
        allowed=names if isinstance(names,list)else[names]
        ok=hit is None if not allowed else bool(hit and hit['material']in allowed and lo-.003<=hit['distance_m']<=hi+.003)
        samples.append({'check':name,'start':[x,-2,z],'direction':[0,1,0],'surfaces':allowed,'distance_range_m':[lo,hi],'actual':hit,'passed':ok})
    for x in [-.56,-.18,.19,.57]:
        for z in [.30,.96,1.73]:
            cast('clear central doorway to shaded back',x,z,'unlit entry beyond sightline',2.985,3.015)
        for z in [2.283,2.442,2.604,2.785]:cast('open transom horizontal bar',x,z,'dark transom grille',2.107,2.120)
    for x in [-1.46,1.46]:
        for z in [.64,1.47,2.35]:cast('paired entrance column shaft',x,z,'grey carved stone',1.713,1.742)
        for dx in [-.166,.166]:
            cast('volute disc',x+dx,2.69,'light raised stucco',1.625,1.64)
            cast('volute rim',x+dx+.061,2.69,'grey carved stone',1.605,1.63)
        cast('column plinth',x,.092,'weathered limestone edge',1.66,1.685)
    cast('address plate ground',1.138,2.60,'green enamel address',1.953,1.970)
    cast('painted digit five',.982,2.575,'ivory number strokes',1.95,1.960)
    cast('painted zero top',1.068,2.573,'ivory number strokes',1.95,1.960)
    for x in [-.68,-.24,.18,.66]:
        for z in [4.82,5.01,5.36]:cast('upper window inset panes',x,z,'grey blue glazing',2.178,2.199)
    for x in [-.44,0,.44]:cast('four-panel dividing mullion',x,5.40,'red brown sash',2.078,2.101)
    cast('raised court cartouche rim',.156,6.44,'light raised stucco',1.857,1.879)
    for x in [-1.56,1.56]:cast('upper pier capital',x,6.73,'light raised stucco',1.793,1.820)
    for x in [-1.36,1.36]:cast('roof shoulder',x,8.28,'light raised stucco',1.872,1.899)
    for x in [-.24,.24]:
        for z in [7.92,8.65]:cast('attic clear panes',x,z,'grey blue glazing',2.178,2.199)
    cast('attic central sash',0,8.17,'red brown sash',2.078,2.101)
    cast('triangular gable face',0,9.28,'weathered pale lime plaster',1.989,2.008)
    for x in [-.69,0,.69]:cast('sloped gable cap',x,9.60-abs(x)*.69/1.26,'weathered limestone edge',1.87,1.89)
    for x,z in [(-2.3,1.5),(2.37,5.41),(-1.85,9.1),(1.98,8.96),(0,9.77)]:cast('open beyond documented architectural limits',x,z,[],0,0)
    return {'passed':all(s['passed']for s in samples),'samples':samples}

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
