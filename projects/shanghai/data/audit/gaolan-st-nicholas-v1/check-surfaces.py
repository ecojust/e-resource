"""Inspect the actual 3-D front faces of the two street wings, groin crown, gate, and surviving terminals."""
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
MODEL = 'huangpu-gaolan-st-nicholas-church'
READER = PROJECT / 'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK = PROJECT / 'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER = PROJECT / 'vendor/meshopt_decoder.module.js'
SerialScene = runpy.run_path(str(READER))['SerialScene']


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def probes(mesh):
    scene=SerialScene(mesh);results=[]
    p=json.loads((PROJECT/'source/precise'/MODEL/'source/plan-parameters.json').read_bytes())
    sc=p['uniform_m_per_reduced_plan_px'];dx,dy=p['plan_anchor_px'];south=p['southern_threshold_y_m']
    def xy(x,y):return ((x-dx)*sc,south+(dy-y)*sc)
    cx,cy=xy(350,349)
    def hit(name,origin,direction,wanted,limit=5):
        origin=list(map(float,origin));direction=list(map(float,direction))
        first=scene.ray(np.array(origin),np.array(direction),limit)
        allowed=[wanted] if isinstance(wanted,str)else wanted
        ok=first is None if allowed is None else bool(first and first['material'] in allowed)
        results.append({'name':name,'origin_author_m':origin,'direction':direction,'expected_first_material':allowed,'first_hit':first,'passed':ok})
    def front(name,x,z,mat):hit(name,[x,south-1.6,z],[0,1,0],mat,3.3)
    for j,u in enumerate((296,351)):
        x=xy(u,525)[0]
        for z in (.735,1.23,1.76,2.23):front(f'Front wing {j+1} arched glass {z}',x+.135,z,'green leaded glass')
        front(f'Front wing {j+1} centre mullion',x,1.0,'deep mullions')
        front(f'Front wing {j+1} second transom',x+.135,1.89,'deep mullions')
        front(f'Front wing {j+1} recessed wood jamb',x+.49,.99,'cobalt window jamb')
        front(f'Front wing {j+1} modelled pointed tympanum',x+.18,2.92,'buff reveals')
    gx=xy(403,525)[0]
    for t in (-.31,.31):front('Closed double door leaf '+str(t),gx+t,1.12,'green leaded glass')
    front('Door central meeting stile',gx,1.1,'deep mullions')
    front('Upper bell recess sill',gx+.26,4.61,'buff reveals')
    front('Upper bell recess back behind inner arch',gx+.20,5.24,'roof metal')
    front('Left pier to elevated opening',gx-1.10,5.12,'buff reveals')
    wx,wy=xy(199,348)
    for k in (-.37,.37):
        hit('Twin west entrance gable light '+str(k),[wx-.87,xy(0,348)[1]-k+.06,4.02],[1,0,0],'green leaded glass',2)
    for j in range(4):
        t=j*math.pi/2-math.pi/2;n=np.array([math.cos(t),math.sin(t)]);u=np.array([-n[1],n[0]])
        c=np.array([cx,cy])+4.20*n+.14*u
        for z in (5.24,6.12,7.12,8.17):
            hit('Crossing tall window %d at %.2f'%(j+1,z),[*c,z],[*(-n),0],'green leaded glass',2.8)
    for j in range(8):
        t=j*math.pi/4-math.pi/2;n=np.array([math.cos(t),math.sin(t)]);u=np.array([-n[1],n[0]])
        c=np.array([cx,cy])+3.0*n+.10*u
        hit('Upper drum %02d recessed light or blind arch'%(j+1),[*c,11.16],[*(-n),0],'buff reveals' if j%2 else 'amber drum glass',2.15)
    gold=['gold dome','gold sheet seam']
    for j in range(12):
        t=(j+.31)*math.pi/6;n=np.array([math.cos(t),math.sin(t)]);c=np.array([cx,cy])+2.8*n
        hit('Gold main dome shoulder %02d'%(j+1),[*c,14.74],[*(-n),0],gold,3.3)
    for t in (-3*math.pi/4,3*math.pi/4):
        px=cx+2.20*math.cos(t);py=cy+2.20*math.sin(t)
        hit('Visible small gilded terminal '+str(t),[px+.09,py,14.12],[0,0,-1],gold,1.35)
    hit('East spiral staircase curved roof',[2.9,-6.9,16.9],[0,0,-1],'apse roof',17.5)
    for k,(x,y) in enumerate([(-7.9,0),(7.65,0),(0,-9.70),(5.9,-7.4),(-4.3,5.3)]):
        hit(f'Observed unoccupied court and neighboring open space {k+1}',[x,y,16.9],[0,0,-1],None,17.5)
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
