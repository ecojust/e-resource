"""Independently intersect the historic pavilion windows, hip roofs and free-standing curved portico."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='xuhui-huaihai-1431-historic-garden-front'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']


def test(scene,role):
    rows=[]
    def ray(label,origin,direction,length,material,lo=None,hi=None):
        hit=scene.ray(origin,direction,length)
        passed=(hit is None) if material is None else bool(hit and hit['material']==material and
            (lo is None or lo<=hit['distance_m']<=hi))
        rows.append(dict(test=label,origin=origin,direction=direction,length_m=length,
                         expected_material=material,expected_range_m=[lo,hi],hit=hit,passed=passed))
    def front(label,x,z,mat,lo=None,hi=None):
        ray(label,[x,-5,z],[0,1,0],9,mat,lo,hi)
    for u in (-6.97,6.97):
        for dx in [-1.68,0,1.68]:
            for z in (2.72,3.33,7.14,8.30):
                front('paired projecting wings with three lights on each floor',u+dx+.185,z,'grey blue glass',5.163,5.167)
        for z in [2.64,3.69,7.44,8.27]:
            front('sash in the broad middle wing light',u,z,'deep timber joinery',5.072,5.076)
        for dx in [-2.89,2.89]:
            front('vertical upper pilaster',u+dx+.06,7.90,'pale limestone',4.908,4.912)
        for dx in [-1.12,1.12]:
            ray('hip roof front pitch',[u+dx,.55,14.7],[0,0,-1],5,'weathered grey brown tile')
        ray('high finial at each pavilion ridge',[u,2.18,15.2],[0,0,-1],2.2,'dark finial metal',.884,.895)
        for z in [.60,.84]:
            ray('recessed foundation openings',[u-1.56+.12,-.43,z],[0,1,0],1.3,'grey blue glass',.59,.60)
    from math import sqrt
    for x in (-3.20,-1.12,1.12,3.20):
        y=-.15-1.93*sqrt(1-(x/3.94)**2)+.165
        ray('detached column shaft at mid-height',[x,y-.5,3.29],[0,1,0],.80,'pale limestone',.363,.383)
        ray('open interval beside each slender column',[x+.34,y-.48,3.29],[0,1,0],.70,None)
    for x in [-2.44,-1.48,1.48,2.44]:
        front('two upper pairs of smaller sashes',x+.13,7.39,'grey blue glass',5.842,5.847)
    for x in [-1.16,-.38,.38,1.16]:
        front('continuous dormer lights',x+.09,10.46,'grey blue glass',5.723,5.727)
    for i in range(7):
        top=1.48*(i+1)/8
        ray('separate step below porch landing',[0,-4.37+.315*i+.17,2.7],[0,0,-1],3,
            'coursed foundation stone',2.7-top-.002,2.7-top+.002)
    ray('final elevation of raised curved porch',[.11,-1.96,2.2],[0,0,-1],1.2,'coursed foundation stone',.718,.722)
    for x in [-2.63,2.63]:
        front('solid stone support below the curved porch',x,.83,'coursed foundation stone')
    for x in [-2.45,-.5,.5,2.45]:
        ray('curved porch soffit across the four-column span',[x,-.83,4.9],[0,0,1],.7,'shaded stone',.348,.352)
    front('flat left annex parapet coping',-12.58,5.77,'pale limestone')
    front('glazed central right conservatory facets',12.08+.11,3.31,'grey blue glass')
    ray('right annex faceted roof top',[12.08,.92,7.4],[0,0,-1],1.4,'dark finial metal',.536,.544)
    for x,y,z in [(-15.4,-1,4),(14.36,-1,4),(.1,2.76,6.70),(.3,-4.78,.2)]:
        ray('open space beyond photographic section',[x,y,z],[0,0,1],.63,None)
    return dict(triangles=len(scene.tri),samples=rows,passed=all(q['passed'] for q in rows))

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
