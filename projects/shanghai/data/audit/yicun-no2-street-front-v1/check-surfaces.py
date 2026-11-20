"""Check first hits on the photographed elevation, roof planes, chimneys and gate of Yicun No. 2."""
import argparse
import numpy as np
import math
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile


SOURCE = Path(__file__).resolve().parent
PROJECT = SOURCE.parents[2]
MODEL = 'xuhui-yicun-no2-street-front'
READER = PROJECT / 'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK = PROJECT / 'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER = PROJECT / 'vendor/meshopt_decoder.module.js'
SerialScene = runpy.run_path(str(READER))['SerialScene']


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def probes(mesh):
    scene=SerialScene(mesh);results=[]
    p=json.loads((PROJECT/'source/precise'/MODEL/'source/parameters.json').read_bytes())
    def hit(name,origin,direction,wanted,limit=5):
        origin=list(map(float,origin));direction=list(map(float,direction))
        first=scene.ray(np.array(origin),np.array(direction),limit)
        allowed=[wanted] if isinstance(wanted,str)else wanted
        ok=first is None if allowed is None else bool(first and first['material'] in allowed)
        results.append({'name':name,'origin_author_m':origin,'direction':direction,'expected_first_material':allowed,'first_hit':first,'passed':ok})
    ring=np.asarray(p['source_local_outline_m'])
    def casting(first,last,label):
        a,b=np.asarray(first),np.asarray(last)
        t=(b-a)/np.linalg.norm(b-a);n=np.array([t[1],-t[0]]);mid=(a+b)/2
        def cast(name,u,z,material):
            pos=mid+t*u+n*1.3
            hit(label+' '+name,[*pos,z],[*(-n),0],material,2.1)
        return cast
    glass='blue gray inner glass';shaft='aged cream turned stone';stone='worn stone slip'
    sash='dark bronze sash';plaster='warm cream stucco';iron='bronze black iron'
    for first,last,bay,rows in [
        (2,1,'forward gable',[(0,1.13,3.28,2.24),(0,4.69,6.29,2.35),(0,8.29,9.82,2.18)]),
        (4,3,'recessed bay',[(-1.08,1.03,3.12,1.75),(-1.08,4.68,6.12,1.73),(-1.09,8.10,9.34,1.76)])]:
        cast=casting(ring[first],ring[last],bay)
        for level,(axis,low,high,w)in enumerate(rows,1):
            for k in range(3):
                cast(f'floor {level} window {k+1}',axis-w/2+(k+.28)*w/3,low+(high-low)*.65,glass)
            for k in (1,2):
                cast(f'floor {level} turned pier {k}',axis-w/2+k*w/3,low+(high-low)*.51,shaft)
            cast(f'floor {level} sash transom',axis+w*.267,low+(high-low)*.74+.017,sash)
            # The projecting balcony deck hides the left middle sill from the street.
            if bay=='forward gable' or level!=2:cast(f'floor {level} sill',axis+w*.155,low-.055,stone)
    gable=casting(ring[2],ring[1],'forward gable')
    for h in (4.26,4.34,4.45,4.57):gable(f'stepped projecting stool at {h}',.38,h,stone)
    gable('semicircular blind recess center',.32,10.36,plaster)
    gable('raised semicircle crest',0,10.92,'pale raised plaster')
    gable('dark attic vent',0,11.17,'deep window reveal')
    gable('gable stucco',1.65,10.14,plaster)
    left=casting(ring[4],ring[3],'recessed bay')
    for text,u,z,mat in [('round glass',1.89,8.66,glass),('round exterior frame',2.082,8.66,sash),('round center mullion',1.70,8.66,sash),('stair window glass',1.67,5.58,glass),('balcony slab',-.72,4.51,'pale raised plaster'),('upper balcony rail',-.80,5.47,iron),('balcony lower rail',-.80,4.78,iron),('upper bay eaves',.16,9.84,stone)]:
        left(text,u,z,mat)
    tile=['ridge terracotta','umber roof tile','weathered terracotta']
    for x,y,name in [(1,-1,'western gable slope'),(3.2,-1,'eastern gable slope'),(-3.8,-3.4,'cross-roof street pitch'),(-2.3,2.6,'cross-roof back pitch'),(2.43,2.3,'long ridge')]:
        hit(name,[x,y,14],[0,0,-1],tile,5)
    for x,y,z in [(-5.63,-.1,12.49),(4.14,1.97,12.78)]:
        hit('chimney cap '+str(x),[x,y,14],[0,0,-1],stone,2)
        hit('chimney smoke vent '+str(x),[x,y-.7,z-.172],[0,1,0],'deep window reveal',1)
    gateends=np.asarray(p['private_gate_ends_m']);gate=casting(*gateends,'private gate')
    half=np.linalg.norm(gateends[1]-gateends[0])/2
    for sign in (-1,1):
        u=sign*half
        gate('stone pier '+str(sign),u+.099,1.25,plaster)
        gate('pier square cap '+str(sign),u+.145,2.29,stone)
        gate('pier basal block '+str(sign),u+.10,.16,'gate pier plinth')
        gate('glazed lantern '+str(sign),u,2.61,'wired lamp glass')
        gate('lantern hood '+str(sign),u,2.82,iron)
        gate('gate leaf panel '+str(sign),sign*.384,.98,[iron,'weathered bronze trim'])
        gate('iron leaf horizontals '+str(sign),sign*.384,.64,'weathered bronze trim')
    for xy in [(-3,-11),(0,-10),(3,-16),(-7,-17),(7,-2)]:
        hit('open yard or pavement '+str(xy),[*xy,15],[0,0,-1],None,16)
    return {'triangles':len(scene.tri),'probes':results,'passed':sum(r['passed'] for r in results)}


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
    assert all(r['passed']==len(r['probes']) and r['triangles']==manifest['assets'][role]['triangles'] for role,r in results.items())
    args.out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    for role,test in results.items():
        print(role,'passed' if test['passed'] else [r for r in test['probes'] if not r['passed']])
    return all(r['passed'] for r in results.values())


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
