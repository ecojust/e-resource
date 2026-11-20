"""Check the real chapel solids, selected photo pixels, fourteen crown openings, lower apse, cross and detached tower exclusion."""
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
MODEL = 'changning-xiyan-church'
READER = PROJECT / 'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK = PROJECT / 'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER = PROJECT / 'vendor/meshopt_decoder.module.js'
SerialScene = runpy.run_path(str(READER))['SerialScene']


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def probes(mesh):
    scene=SerialScene(mesh);results=[]
    def probe(name,point,direction,wanted,limit,depth=None,tol=.055):
        hit=scene.ray(np.array(point,dtype=float),np.array(direction,dtype=float),limit)
        mats=[wanted] if isinstance(wanted,str) else wanted
        ok=hit is None if wanted is None else bool(hit and hit['material'] in mats and (depth is None or abs(hit['distance_m']-depth)<tol))
        results.append({'name':name,'origin_author_m':point,'direction':direction,'expected_materials':mats,'first_hit':hit,'passed':ok})
    def front(label,u,z,material,distance=None):
        probe(label,[u+.12,-11.,z],[0,1,0],material,4,distance)
    for side in [-1,1]:
        for j,z in enumerate([.41,1.13]):
            front('grey entry panel %s/%s'%(side,j),side*.40,z,'grey door',1.792)
            front('raised panel edges %s/%s'%(side,j),side*.68,z,'raised grey panels',1.75)
        front('door arch lower reveal '+str(side),side*.825,1.07,'chamfer shadow',1.403)
        front('lancet outer frame '+str(side),side*.94,3.66,'sandstone highlight',1.317)
        front('lancet middle frame '+str(side),side*.86,3.66,'weathered brown stone',1.406)
        front('rough forecourt wall '+str(side),side*3.2,4.0,['rough ochre stucco','roughcast aggregate','roughcast shadow'],1.50)
    front('wooden centre stile',0,1.16,'chamfer shadow',1.753)
    front('window sill drip',0,2.55,'chamfer shadow')
    samples=json.loads((PROJECT/'source/precise'/MODEL/'source/glass-colour-samples.json').read_bytes())
    for col in [1,3,6,8]:
        for row in [5,10,14,17,20,25]:
            x=-.695+(col+.5)*1.39/10;z=6.24-(row+.5)*3.52/27
            if row==5 and col in [1,8]:continue
            front('coloured front glazing %d/%d'%(col,row),x,z,'forecourt glazing %02d'%(samples['rows_from_top'][row][col]+1),1.662)
    for j in range(2,11):
        z=2.72+.13+j*(3.52-.27)/12
        front('raised saddlebar '+str(j),.271,z,'dark lead',1.619)
    for k in range(14):
        a=math.tau*(k+.5)/14;c=math.cos(a);s=math.sin(a);cx,cy=.35,2.25
        probe('fourteen dark crown openings %02d'%(k+1),[cx+6*c,cy+6*s,7.83],[-c,-s,0],'glazing recess',2.45)
        probe('crown base sill %02d'%(k+1),[cx+6*c,cy+6*s,7.525],[-c,-s,0],'roof edge',2.35)
    for k in range(7):
        a=math.pi/2+(k+.5)*math.pi/7;c=math.cos(a);s=math.sin(a)
        probe('apse pointed opening '+str(k+1),[-7.78+4.9*c,.2+4.9*s,4.26],[-c,-s,0],['apse glass','dark lead'],2.12)
    for k in range(14):
        a=math.tau*(k+.44)/14
        probe('copper canopy petal '+str(k+1),[.35+2.8*math.cos(a),2.25+2.8*math.sin(a),12],[0,0,-1],['copper pale','copper shaded'],3.25)
    for side in [-1,1]:
        probe('separate cross arm '+str(side),[.35+side*.19,2.25-1.0,10.68],[0,1,0],'aged cross',1.2,.9625)
    for label,x,y in [('separate northeast tower',5.11,-12.16),('church forecourt',0,-11.60),('riverbank outside apse',-12.75,0),('rear boundary',0,11.15)]:
        probe(label,[x,y,15],[0,0,-1],None,16)
    return {'triangles':len(scene.tri),'probes':results,'passed':all(q['passed']for q in results)}


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
