"""Probe the three finished meshes for the cut northwest entrance, three-storey Corinthian colonnades, early attic and identifiable 1988 additions."""
import argparse
import math
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile


SOURCE = Path(__file__).resolve().parent
PROJECT = SOURCE.parents[2]
MODEL = 'huangpu-deutsch-asiatische-bank'
READER = PROJECT / 'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK = PROJECT / 'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER = PROJECT / 'vendor/meshopt_decoder.module.js'
SerialScene = runpy.run_path(str(READER))['SerialScene']


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def probes(mesh):
    scene=SerialScene(mesh)
    records=[]

    def expect(label,origin,direction,material,depth=None):
        hit=scene.ray(origin,direction,30)
        passed=hit is None if material is None else (
            hit is not None and hit['material']==material and abs(hit['distance_m']-depth)<.04)
        records.append({'label':label,'origin_m':origin,'direction':direction,
                        'material':material,'expected_distance_m':depth,'first_hit':hit,'passed':passed})

    def face(label,start,end,u,z,material,depth):
        dx,dy=end[0]-start[0],end[1]-start[1];length=math.hypot(dx,dy);tx,ty=dx/length,dy/length
        nx,ny=ty,-tx
        x=(start[0]+end[0])/2+u*tx;y=(start[1]+end[1])/2+u*ty
        expect(label,[x+2*nx,y+2*ny,z],[-nx,-ny,0],material,depth)
    portal=((-7.80,12.86),(-11.12,10.67))
    def front(label,u,z,material,depth):face(label,*portal,u,z,material,depth)
    front('deep paired portal behind the Baroque lintel',.06,2.32,'dark oak',2.63)
    front('raised central door-leaf panel',.68,2.32,'dark oak',2.51)
    front('pediment carved shield',.05,5.11,'pale carved facing stone',1.87)
    front('lower corner casement',.18,7.45,'inset cool glazing',2.32)
    front('third-storey corner casement',.17,12.22,'inset cool glazing',2.32)
    front('original fourth-storey corner opening',.18,17.38,'inset cool glazing',2.32)
    front('1988 addition round wreath centre',.10,20.79,'slate grey roof',1.992)
    front('1988 addition high corner window',.23,24.10,'inset cool glazing',2.32)
    for name,edge in [('Jiujiang',((10.45,13.10),(-7.80,12.86))),('Sichuan',((-11.12,10.67),(-11.20,-11.04)))]:
        a,end=edge;length=math.dist(a,end);span=length*.705;module=span/3
        for i in range(3):
            u=module*(i-1)
            face(name+' ground floor arched glazing '+str(i+1),a,end,u+.23,3.17,'inset cool glazing',2.32)
            for z,story in [(6.62,'second'),(11.29,'third')]:
                face(name+' '+story+' sash '+str(i+1),a,end,u+module*.145+.16,z,'inset cool glazing',2.32)
        for i in range(4):
            face(name+' giant Corinthian shaft '+str(i+1),a,end,-span/2+i*module,9.76,'granite Corinthian shaft',1.24)
        for i in range(5):
            u=(i+.5)*length/5-length/2
            face(name+' later top floor '+str(i+1),a,end,u+.12,24.22,'inset cool glazing',2.32)
    expect('upper roof above 1988 addition',[0,0,29],[0,0,-1],'slate grey roof',2.83)
    expect('open road outside northwest portal',[-14,16,26],[0,0,-1],None)
    return dict(triangles=len(scene.tri),probes=records,passed=all(r['passed'] for r in records))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,default=PROJECT/'assets/models/candidates'/MODEL/'manifest.json')
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    manifest=json.loads(args.manifest.read_bytes())
    assert manifest['id']==MODEL
    results={}
    with tempfile.TemporaryDirectory() as directory:
        for role in ('raw','full','lod'):
            asset=manifest['assets'][role]
            path=args.manifest.parent/asset['file']
            assert path.stat().st_size==asset['bytes'] and digest(path)==asset['sha256']
            decoded=path
            if role!='raw':
                decoded=Path(directory)/(role+'.glb')
                subprocess.run(['node',UNPACK,path,decoded,DECODER],check=True,stdout=subprocess.DEVNULL)
            results[role]=dict(sha256=asset['sha256'],file=path.name,**probes(decoded))
    report={'id':MODEL,'script_sha256':digest(Path(__file__)),'manifest_sha256':digest(args.manifest),
            'decoder_sha256':digest(DECODER),'reader_sha256':digest(READER),'results':results,
            'scope':'Checks only the sampled physical geometry in local axes; placement and viewing use independent records.'}
    args.out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    for role,test in results.items():
        print(role,'passed' if test['passed'] else [r for r in test['probes'] if not r['passed']])
    return all(r['passed'] for r in results.values())


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
