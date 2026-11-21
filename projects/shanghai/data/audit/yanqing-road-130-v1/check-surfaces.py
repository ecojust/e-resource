"""Cast independent rays through the photographed garden arcades, roof dormer and terrace railings."""
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
MODEL = 'xuhui-yanqing-road-130-residence'
READER = PROJECT / 'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK = PROJECT / 'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER = PROJECT / 'vendor/meshopt_decoder.module.js'
SerialScene = runpy.run_path(str(READER))['SerialScene']


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def probes(mesh,role):
    scene=SerialScene(mesh)
    records=[]
    def shot(label,origin,direction,material,depth,tolerance=.045):
        hit=scene.ray(origin,direction,8)
        passed=hit is None if material is None else hit is not None and hit['material']==material and abs(hit['distance_m']-depth)<tolerance
        records.append({'label':label,'from':origin,'direction':direction,'expected_material':material,'expected_distance_m':depth,'first_hit':hit,'passed':passed})
    # A ray at each photographed bay strikes the inset glazing or an explicit central mullion.
    front=[(-7.42,1.12),(-6.93,-.48),(-3.82,-.77),(-.12,-1.41),(3.55,-1.12),(6.65,-.48),(7.51,.73)]
    for index in range(1,5):
        a,b=front[index:index+2]
        dx,dy=b[0]-a[0],b[1]-a[1]
        length=math.hypot(dx,dy);tx,ty=dx/length,dy/length;nx,ny=ty,-tx
        mx,my=(a[0]+b[0])/2,(a[1]+b[1])/2
        recess=.90 if index in (2,3) else .26 if index==4 else 0.
        for u in (-.36,.36):
            shot('lower hall pane '+str(index),[mx+tx*u+nx*1.2,my+ty*u+ny*1.2,2.74],[-nx,-ny,0],'deep grey glazed garden hall',1.485+recess)
        shot('continuous transom '+str(index),[mx+tx*.21+nx,my+ty*.21+ny,.52+3.42*.72],[-nx,-ny,0],'blue grey timber frame',1.16+recess)
    for x,y in [(-3.82,-.77),(-.12,-1.41),(3.55,-1.12)]:
        shot('freestanding shaft',[x,y-1.07,2.45],[0,1,0],'pale carved stone',.70,.04)
    shot('visible lowest western door step',[-5.20,-1.80,1.4],[0,0,-1],'pale carved stone',1.259,.025)
    for index,x in enumerate((-5.225,5.195)):
        shot('upper room glass '+str(index),[x+.28,-.85,6.97],[0,1,0],'shadowed glazed opening',1.485)
        shot('upper room central frame '+str(index),[x,-.85,7.25],[0,1,0],'blue grey timber frame',1.36)
    for index,x in enumerate((-5.25,5.17)):
        shot('short pediment pier '+str(index),[x+1.54,-.87,11.45],[0,1,0],'pale carved stone',.845)
        shot('crown sash glass '+str(index),[x+.20,-.87,11.45],[0,1,0],'shadowed glazed opening',1.395)
        shot('segmental tympanum '+str(index),[x+.93,-.87,12.44],[0,1,0],'warm ivory render',.975)
        shot('pierced balcony spindle '+str(index),[x-1.49+2.97*.5/8,-1.0,10.0],[0,1,0],'pale carved stone',.70,.038)
        shot('gap between stone spindles '+str(index),[x-1.49+2.97/8,-.85,10.0],[0,1,0],None,0)
    for x in (-2.18,-.74,.74,2.18):
        shot('central shed dormer glass',[x+.18,2.12,11.16],[0,1,0],'shadowed glazed opening',.85)
    for x in (-6.25,6.56):
        for y in (2.17,3.47,5.06):
            z=10.64+(y-1.86)*.98 if y<4 else 12.737+(y-4)*.39
            shot('red roof pitch',[x,y,16.12],[0,0,-1],'weathered French red tile',16.12-z,.059)
    for x,y in ((0,-5),(4,-4.7),(-8.8,.7),(9.0,2.0),(0,9.6)):
        shot('courtyard, side passage or retained rear',[x,y,5.5],[0,0,-1],None,0)
    return {'passed':all(v['passed']for v in records),'probe_count':len(records),'probes':records}

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
            results[role]=dict(sha256=asset['sha256'],file=path.name,**probes(decoded,role))
    report={'id':MODEL,'script_sha256':digest(Path(__file__)),'manifest_sha256':digest(args.manifest),
            'decoder_sha256':digest(DECODER),'reader_sha256':digest(READER),'results':results,
            'scope':'Checks only the sampled physical geometry in local axes; placement and viewing use independent records.'}
    args.out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    for role,test in results.items():
        print(role,'passed' if test['passed'] else [r for r in test['probes'] if not r['passed']])
    return all(r['passed'] for r in results.values())


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
