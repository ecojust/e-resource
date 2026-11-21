"""Check window recesses, open verandas, timber gables, roofs and separate flues on Wukang Road No. 99."""
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
MODEL = 'xuhui-caldbeck-manager-residence'
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
    def face(first,last,label):
        a,b=ring[first],ring[last]
        axis=(b-a)/np.linalg.norm(b-a); normal=np.array([axis[1],-axis[0]]);mid=(a+b)/2
        def cast(name,u,z,expected,depth=1.3,reach=2.1):
            xy=mid+axis*u+normal*depth
            hit(label+' '+name,[*xy,z],[*(-normal),0],expected,reach)
        return cast,np.linalg.norm(b-a)/2
    gable,half=face(5,4,'projecting garden gable')
    for level,(low,high,width,lights) in enumerate([(1.02,2.77,3.40,4),(4.09,5.99,3.57,4),(7.24,8.67,2.67,3)],1):
        for light in range(lights):
            gable(f'level {level} casement {light+1}',-width/2+(light+.31)*width/lights,low+(high-low)*.52,'shaded window')
        for bar in range(1,lights):
            gable(f'level {level} vertical frame {bar}',-width/2+bar*width/lights,low+(high-low)*.46,'vermilion window joinery')
        gable(f'level {level} transom',width*.177,low+.69*(high-low),'vermilion window joinery')
        gable(f'level {level} sill',.327,low-.054,'brick sill')
    for label,u,z,mat in [('upper tie beam',.32,6.59,'oxidized Tudor timber'),('right post',1.93,5.53,'oxidized Tudor timber'),('left post',-2.47,5.29,'oxidized Tudor timber'),('roughcast infill',2.79,4.54,'ivory roughcast'),('corner bonds',half-.11,.945,['garden brick','brick sill']),('brick plinth',.7,.35,'garden brick')]:
        gable(label,u,z,mat)
    west,half=face(0,5,'Wukang Road balcony')
    for k,(axis,low,high,width) in enumerate([(-1.28,3.64,5.67,1.30),(1.43,3.68,5.60,1.40),(-1.03,7.32,8.43,1.30)],1):
        for j in range(2):
            west(f'opening {k} light {j+1}',axis-width/2+(j+.3)*width/2,low+.59*(high-low),'light window',.34,1.3)
        west(f'opening {k} mullion',axis,low+.55*(high-low),'vermilion window joinery',.34,1.3)
    for label,u,z,mat in [('upper rail',.272,4.29,'balcony wood'),('lower rail',.272,3.52,'balcony wood'),('slab edge',.32,3.3,'worn stone'),('southern support',3.24,1.5,'garden brick'),('northern support',-2.99,1.5,'garden brick')]:
        west(label,u,z,mat)
    terrace,half=face(3,2,'south garden terrace')
    left,right=-half+.10,half-2.21
    columns=np.linspace(left+.14,right-.14,4)
    for k,u in enumerate(columns,1):
        terrace(f'ground pier {k}',u,1.7,'garden brick')
        terrace(f'brick capital {k}',u,3.12,'brick sill')
        terrace(f'terrace cap {k}',u,4.34,'worn stone')
    for k,(a,b) in enumerate(zip(columns,columns[1:]),1):
        terrace(f'open porch span {k}',(a+b)/2,1.52,None,.65,1.15)
        a+=.155;b-=.155;separation=(b-a)/max(2,round((b-a)/.68))
        terrace(f'pierced brick opening {k}',a+separation*.5,3.88,None,.65,1.15)
        terrace(f'solid brick bar {k}',a+separation,3.88,'garden brick')
        terrace(f'coping {k}',(a+b)/2,4.276,'brick sill')
    center=(left+right)/2;width=right-left
    terrace('recessed central garden door',center,1.77,'recessed door wood',-1.19,1.50)
    for k,u in enumerate([center-width*.32,center+width*.32],1):
        terrace(f'lower sheltered window {k}',u+.19,1.89,'light window',-1.19,1.50)
    for k,u in enumerate(np.linspace(center-width*.34,center+width*.34,4),1):
        terrace(f'upper terrace window {k}',u+.17,4.84,'light window',-1.19,1.50)
    for label,x,y,span,low,high,lights in [('hipped attic dormer',.13,-3.75,2.60,8.48,9.32,3),('east gabled dormer',6.66,-3.92,3.47,8.39,9.31,4)]:
        w=span*.75
        for i in range(lights):
            hit(f'{label} light {i+1}',[x-w/2+(i+.27)*w/lights,y-.40,(low+high)/2],[0,1,0],'shaded window',.95)
        hit(label+' window sill',[x+.16,y-.40,low-.055],[0,1,0],'brick sill',.95)
    tile=['baked tile','tile ridge','terracotta tile bed']
    for x,y,name in [(9,1.80,'north main slope'),(9.38,-2.51,'south main slope'),(-7.,-6.4,'cross roof western slope'),(-4.13,-6.1,'cross roof eastern slope'),(6.74,-2.57,'gable dormer roof'),(.13,-3.53,'hip front slope')]:
        hit(name,[x,y,16],[0,0,-1],tile,9)
    for name,x,y in [('main ridge',1.9,.65),('cross ridge',-6.03,-5.7)]:
        hit(name,[x,y,16],[0,0,-1],'tile ridge',9)
    # Sample both main pitches near the long ridge and both slopes of the cross
    # wing. A single triangle spanning two pitches can keep the tile material yet
    # put the roof metres below the true crest; check the first height as well.
    for side,x in [('west',-9.16),('middle',1.82),('east',8.73)]:
        for y in (-1.70,-.37,.37,.97,1.82,3.87):
            expected=p['estimated_main_ridge_m']-.851*abs(y-.65)
            hit(f'{side} main pitched surface at {y}',[x,y,16],[0,0,-1],tile,12)
            probe=results[-1]
            z=probe['first_hit']['point_enu_m'][2] if probe['first_hit'] else None
            probe['expected_roof_z_m']=round(expected,4)
            probe['height_tolerance_m']=.095
            probe['passed']=probe['passed'] and z is not None and abs(z-expected)<=.095
    for x,y in [(-7.36,-7.3),(-6.52,-5.15),(-5.24,-5.32),(-4.29,-7.15)]:
        expected=10.87-1.004*abs(x+6.03)
        hit(f'transverse wing slope {x} {y}',[x,y,16],[0,0,-1],tile,12)
        probe=results[-1]
        z=probe['first_hit']['point_enu_m'][2] if probe['first_hit'] else None
        probe['expected_roof_z_m']=round(expected,4)
        probe['height_tolerance_m']=.095
        probe['passed']=probe['passed'] and z is not None and abs(z-expected)<=.095
    for group,x,y,count in [('western chimney',-6.45,2.18,3),('four-flue chimney',3.55,1.34,4)]:
        width=count*.34+.16
        for j in range(count):
            u=x-width/2+.25+j*.34;v=y+(j%2-.5)*.135
            hit(f'{group} flue {j+1}',[u,v,16],[0,0,-1],'charcoal flue',5)
            hit(f'{group} cap {j+1}',[u,v+.179,16],[0,0,-1],'brick sill',5)
    for x,y in [(-8,-11),(0,-8),(7.2,-7.8),(-12,1)]:
        hit(f'ungated open yard {x} {y}',[x,y,16],[0,0,-1],None,17)
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
