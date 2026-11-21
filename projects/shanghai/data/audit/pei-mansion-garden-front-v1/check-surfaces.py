"""Check the stepped gallery stonework, recessed openings, casement grids, stairs and roof on the garden elevation."""
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
MODEL = 'jingan-pei-mansion-garden-front'
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
    xc=(ring[2,0]+ring[3,0])/2;y0=ring[3,1]
    def pt(x,y):return np.array([xc+x,y0+y])
    corners=[pt(-9.34,1.13),pt(-8.37,0),pt(-5.37,0),pt(-3.71,1.03),pt(3.71,1.03),pt(5.37,0),pt(8.37,0),pt(9.34,1.13)]
    def face(a,b):
        vec=b-a;t=vec/np.linalg.norm(vec);n=np.array([t[1],-t[0]]);mid=(a+b)/2
        def probe(label,u,z,mat,depth=.65,reach=1.20):
            hit(label,[*(mid+t*u+n*depth),z],[*-n,0],mat,reach)
        return probe,np.linalg.norm(vec)/2
    for ix,(a,b)in enumerate(zip(corners,corners[1:])):
        if ix==3:continue
        f,h=face(a,b);cols=4 if ix in (1,5) else 3 if ix in (2,4) else 2;lo=-h+.107;w=2*(h-.107)
        for j,(low,high)in enumerate([(1.25,5.10),(6.97,9.32),(11.29,13.61)]):
            for k in range(cols):
                f(f'facet {ix+1} storey {j+1} glass light {k+1}',lo+w*(k+.41)/cols,low+.49*(high-low),['grey glazed lights','reflecting glass'])
            for k in range(1,cols):
                f(f'facet {ix+1} storey {j+1} mullion {k}',lo+w*k/cols,low+.49*(high-low),'steel casements')
            f(f'facet {ix+1} storey {j+1} sill',0,low-.06,'light sandstone')
        f(f'facet {ix+1} darker aggregate course',.19,6.03,'dark aggregate band')
    front,_=face(corners[3],corners[4]);rear,_=face(pt(-3.71,3.05),pt(3.71,3.05))
    for k in range(4):
        front(f'gold entrance glass {k}',-3.57+(k+.37)*(7.14/4),3.25,['shadowed glazing','grey glazed lights'])
    front('entrance pull',.12,2.06,'bronze handle')
    period=7.42/3
    for i,floor in enumerate((5.18,9.49),1):
        for k in range(3):
            key=-3.71+k*period
            front(f'gallery {i} stone vertical {k}',key+.14*period,floor+.85+.39*.89,'carved rail stone')
            front(f'gallery {i} open rectangular aperture {k}',key+.73*period,floor+.85+.53*.89,None,.46,.95)
            front(f'gallery {i} upper fret horizontal {k}',key+.25*period,floor+.85+.87*.89,'carved rail stone')
        for x in (-1.83,1.83):
            rear(f'gallery {i} recessed door {x}',x+.38,floor+2.31,['shadowed glazing','grey glazed lights'])
        front(f'gallery {i} lower parapet',-.65,floor+.45,'light sandstone')
        front(f'gallery {i} real open volume',-.38,floor+2.32,None,.45,1.35)
    front('central face of roof key',.10,15.02,'buff tooling')
    for k in range(5):
        depth=(4.5-k)*.274
        pos=pt(.34,1.03-depth)
        hit(f'stone stair tread {k+1}',[*pos,2.0],[0,0,-1],'pale steps',2.1)
    for name,x,y,z,mat in [('flat roof',-.7,6.4,13.82,'roof grey'),('roof shaft',4.3,4.2,17.165,'buff tooling'),('shaft raised tooth',4.16,3.66,17.42,'light sandstone')]:
        pos=pt(x,y);hit(name,[*pos,19.0],[0,0,-1],mat,7.0)
        actual=results[-1]['first_hit'];zval=actual['point_enu_m'][2]if actual else None
        results[-1].update(expected_height_m=z,passed=actual is not None and results[-1]['passed']and abs(zval-z)<.035)
    for x,y in [(-7.2,-1.4),(1,-1.4),(6,-1.4),(12,2),(1,29)]:
        hit(f'outside separate garden or neighbor {x} {y}',[*pt(x,y),18],[0,0,-1],None,18.4)
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
