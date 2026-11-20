"""Check the east-front portals, four figures, actual rose panes, belfry and court."""
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
MODEL = 'huangpu-st-joseph-church-east-front'
READER = PROJECT / 'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK = PROJECT / 'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER = PROJECT / 'vendor/meshopt_decoder.module.js'
SerialScene = runpy.run_path(str(READER))['SerialScene']


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def probes(mesh):
    scene=SerialScene(mesh)
    records=[]
    def check(label,origin,direction,mat,dist=None,limit=12,tol=.052):
        origin=np.asarray(origin,dtype=float)
        direct=np.asarray(direction,dtype=float)
        hit=scene.ray(origin,direct,limit)
        ok=hit is None if mat is None else bool(hit and hit['material']==mat and
            (dist is None or abs(hit['distance_m']-dist)<tol))
        records.append({'label':label,'origin_m':origin.tolist(),'direction':direct.tolist(),
                        'material':mat,'distance_m':dist,'first_hit':hit,'passed':ok})

    def front(name,x,h,material,dist=None,limit=12,tolerance=.08):
        check(name,[x,-2.0,h],[0,1,0],material,dist,limit,tolerance)

    for section,x,width,height,face_y in [('south door',-7.36,1.82,4.09,.74),('main door',0,3.19,7.55,.25),('north door',7.36,1.82,4.09,.74)]:
        spring=.055+height-width/2
        for side in [-1,1]:
            for level in [0,1,2]:
                z=.17+(level+.45)*(spring-.45)/3
                front(section+' panel '+str((side,level)),x+side*(width*.25+.115*(width-.18)),z,'raised oak')
            front(section+' glazed transom '+str(side),x+side*width*.187,spring+width*.18,'glass milk')
        front(section+' meeting stile',x,.84,'door bronze')
        front(section+' recessed jamb',x+width/2+.075,spring*.70,'weathered trim')
    r=1.59;cz=17.13
    outer=['glass green','glass violet','glass ruby','glass amber','glass green','glass milk','glass ruby','glass amber']
    inner=['glass ruby','glass amber','glass green','glass ruby','glass ruby','glass amber','glass green','glass violet']
    for k in range(8):
        ang=math.tau*k/8;front('rose outer pane '+str(k+1),math.sin(ang)*r*.721,cz+math.cos(ang)*r*.721,outer[k],2.61)
        ang+=math.pi/8;front('rose inner pane '+str(k+1),math.sin(ang)*r*.412,cz+math.cos(ang)*r*.412,inner[k],2.60)
    front('rose blue medallion',0,cz,'glass blue',2.595)
    front('rose terracotta mullion',r*.161,cz,'terracotta tracery',2.503)
    for x,start in [(-7.36,5.19),(-3.92,5.35),(3.92,5.35),(7.36,5.19)]:
        front('niche head '+str(x),x,start+1.59,'carved figure')
        front('niche robe '+str(x),x+.04,start+.44,'carved figure')
        front('niche shadow behind statue '+str(x),x+.24,start+1.91,'recess')
        front('niche stone sill '+str(x),x+.35,start-.12,'weathered trim')
    for x in [-1.31,1.31]:
        for side in (-1,1):front('paired blind arched recess '+str((x,side)),x+side*.49,12.32,'recess',2.65)
        front('paired arch stone divider '+str(x),x,12.32,'limewash',2.165)
        front('blind arch red roundel '+str(x),x+.093,14.50+.22,'terracotta tracery')
    for x in [-7.16,7.16]:front('quatrefoil shadow '+str(x),x,11.82,'recess',3.03)
    front('central bell shutter',.07,21.09,'louver red')
    front('central bell louvre recess',.07,22.41,'louver shadow')
    front('slate of main spire',.05,30.35,'slate')
    for side in [-1,1]:
        front('open flanking pinnacle '+str(side),side*3.54,22.35,None,limit=3.8)
        front('flanking pinnacle roof '+str(side),side*3.54,27.05,'slate')
        front('independent cross arm '+str(side),side*.45,36.04,'rail iron')
        front('clear space beside central spire '+str(side),side*2.76,30.61,None)
    for x,y in [(0,-1),(7,-.78),(-9,-.73),(0,8.3),(-10,7.63)]:
        check('unmodeled ground '+str((x,y)),[x,y,1.80],[0,0,-1],None,limit=2.2)
    return {'triangles':len(scene.tri),'probes':records,'passed':all(r['passed']for r in records)}


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
