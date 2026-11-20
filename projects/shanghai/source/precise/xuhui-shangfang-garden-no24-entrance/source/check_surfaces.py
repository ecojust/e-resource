"""Independently measure the documented open lane wall, shelter, plaques and meter cabinet."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='xuhui-shangfang-garden-no24-entrance'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']


def test(scene,role):
    rows=[]
    def ray(label,start,direction,length,materials,span=None):
        hit=scene.ray(start,direction,length)
        ok=hit is None if not materials else bool(hit and hit['material']in materials and (not span or span[0]<=hit['distance_m']<=span[1]))
        rows.append(dict(test=label,origin=start,direction=direction,maximum_m=length,
                         expected_materials=materials,expected_distance_m=span,hit=hit,passed=ok))
    def front(label, x, z, material, span=None):
        ray(label, [x,-.5,z], [0,1,0], .8, [material] if material else [], span)
    for x in [-.79,-.51,-.20]:
        for h in [.14,.98,1.86]:
            ray('open doorway through its full depth',[x,-.60,h],[0,1,0],1.85,[])
    for x in [-1.83,-1.09,.032,1.14,1.90]:
        front('solid roughcast beside the opening',x,.67,'sandy yellow roughcast',[.498,.502])
    for x in [-.73,-.33,.82]:
        front('solid lintel and high wall',x,2.33,'sandy yellow roughcast',[.498,.502])
    for x in [-1.74,-.61,.86,1.40]:
        front('blue-grey wall cap',x,2.41,'blue grey coping and sill',[.471,.477])
        front('ventilation slit below sheet',x,2.62,None)
    for x,z in [(-1.58,1.79),(-1.41,1.77),(-1.12,1.52)]:
        front('engraved stone plaque surrounding sign',x,z,'pale stone heritage plaque',[.455,.460])
    for char,x,z in [('张',-1.5104,1.646),('元',-1.4362,1.646),('济',-1.356,1.650),('故',-1.2948,1.656),('居',-1.2206,1.650)]:
        front('raised title stroke '+char,x,z,'dark brown inscription',[.453,.457])
    for x in [-1.591,-1.109]:
        for z in [1.505,1.795]:
            front('four mounting studs',x,z,'dark patinated bronze marker',[.448,.453])
    front('circular district marker face',-1.421,1.238,'dark patinated bronze marker',[.458,.464])
    front('circular marker rim',-1.51,1.225,'aged brass lettering and studs',[.455,.461])
    for x in [.287,.50,.713]:
        for z in [1.118,1.375,1.632]:
            front('nine dark utility readouts',x,z,'dark meter windows',[.357,.362])
    front('metal cabinet and door gasket',.50,.875,'weathered pale grey electrical cabinet',[.368,.374])
    front('surface-mounted wiring conduit',1.35,2.199,'grey surface conduit',[.378,.385])
    for x in [-1.99,-1.99+3.98/44,-.95,.32,1.16,1.85]:
        ray('continuous folded steel canopy',[x,.60,3.22],[0,0,-1],.70,['weathered corrugated steel'])
    for x in [-1.82,1.20]:
        ray('open sky behind the bounded shed',[x,1.16,3.20],[0,0,-1],3.1,[])
    for x in [-2.20,2.20]:
        front('neighboring house frontages excluded',x,.80,None)
    return dict(triangles=len(scene.tri),samples=rows,passed=all(r['passed']for r in rows))


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
