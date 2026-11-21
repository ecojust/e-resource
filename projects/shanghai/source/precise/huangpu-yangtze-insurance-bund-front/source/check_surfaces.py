"""Probe the street entrances, five-axis windows, double-column gallery and attic pavilions of Bund number 26."""
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
ID='huangpu-yangtze-insurance-bund-front'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']


def test(scene,role):
    rows=[]
    def ray(name,point,direction,length,material,limits=(0,20)):
        hit=scene.ray(point,direction,length)
        passed=(hit is None) if material is None else bool(hit and hit['material']==material and limits[0]<=hit['distance_m']<=limits[1])
        rows.append(dict(test=name,origin=point,direction=direction,length_m=length,
                         expected_material=material,range_m=list(limits),hit=hit,passed=passed))
    def street(name,x,z,material,lo,hi):
        ray(name,[x,-2.5,z],[0.,1.,0.],8.,material,(lo,hi))
    for i,x in enumerate((-6.07,-2.52,0,2.52,6.07)):
        label=f'axis {i+1}'
        street(label+' lower entrance or central window',x+.23,1.16,
               'recessed entrance joinery' if i in (0,4) else 'recessed glass',2.80,2.84)
        street(label+' projecting key in dressed stone arch',x,10.17,'carved pale stone',2.27,2.32)
        for floor,z in enumerate((7.13,12.59,17.26,21.85),start=2):
            street(label+f' floor {floor} glass',x+.21,z,'recessed glass',2.79,2.84)
            street(label+f' floor {floor} mullion',x,z,'bronze window frame',2.64,2.68)
    for x in (-8.68,-4.39,4.39,8.68):
        street('giant pilaster '+str(x),x,17.53,'limestone',2.22,2.29)
        street('projecting circular pier ornament '+str(x),x,24.77,'carved pale stone',2.13,2.19)
    for x in (-1.52,-1.05,1.05,1.52):
        street('Ionic shaft '+str(x),x,27.86,'carved pale stone',2.74,2.81)
    for x in (-2.13,0,2.13):
        street('window behind open sixth-storey colonnade',x+.16,27.25,'recessed glass',5.05,5.10)
    for x in (-6.13,6.13):
        street('attic pavilion glass '+str(x),x+.27,31.03,'recessed glass',3.43,3.49)
        street('attic pavilion mullion '+str(x),x,31.03,'bronze window frame',3.28,3.34)
        ray('pavilion roof '+str(x),[x,1.56,36.0],[0.,0.,-1.],4.0,'carved pale stone',(1.87,1.97))
    street('central cartouche',.28,10.56,'carved pale stone',2.30,2.36)
    street('cornice projection',3.81,25.82,'carved pale stone',1.65,1.83)
    street('clear sky beyond eastern roof',8.95,35.82,None,0,8)
    ray('central iron flagstaff tip',[0,2.47,40.0],[0.,0.,-1.],5.,'wrought iron',(2.06,2.11))
    ray('clear south alley next to frontage',[-10.42,-1.,2.],[0.,1.,0.],4.,None)
    ray('clear north alley next to frontage',[10.42,-1.,2.],[0.,1.,0.],4.,None)
    return dict(passed=all(r['passed']for r in rows),samples=rows)


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
