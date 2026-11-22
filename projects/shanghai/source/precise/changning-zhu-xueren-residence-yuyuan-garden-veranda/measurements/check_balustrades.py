"""First intersection tests for the south garden railings in a serialized mesh."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact'))
sys.path.insert(0,str(HERE.parent/'source'))
from glb_triangles import SerialScene
from garden_railings import member_positions,spindle_fractions,BOTTLE,CAP,POST,BASE


def read(p):
    return json.loads(p.read_bytes())


def check(mesh):
    scene=SerialScene(mesh)
    layout=read(HERE.parent/'source/garden-layout.json')
    runs,posts=member_positions(layout)
    checks=[]
    def shoot(label,origin,direction,length,expected):
        result=scene.ray(origin,direction,length)
        mat=result['material'] if result else None
        checks.append(dict(sample=label,origin=np.round(origin,5).tolist(),
                           direction=np.round(direction,5).tolist(),length_m=length,
                           expected=expected,actual=result,pass_surface=mat==expected))
    for run in runs:
        p=np.array(run['p']); q=np.array(run['q']); delta=q-p
        if run['id'] in ('UE','LE'):direction=np.array([-1.,0,0])
        else:direction=np.array([0,1.,0])
        def across(fraction,z,target,label):
            x,y=p+fraction*delta
            point=np.array([x,y,z]);shoot(run['id']+' '+label,point-direction*.32,direction,.58,target)
        bottom=run['base']+.041
        spindle=run['top']-.094-bottom
        fractions=spindle_fractions(run)
        for i,frac in enumerate(fractions):
            for h,name in ((.25,'taper'),(.530,'collar'),(.866,'neck')):
                across(frac,bottom+spindle*h,BOTTLE,name+' '+str(i+1))
            if i:
                across((frac+fractions[i-1])/2,bottom+spindle*.52,None,'opening '+str(i))
        across(.50,run['top']-.045,CAP,'handrail')
        across(.50,run['base']+.034,CAP,'sill')
    for x,y,z,t,half,name in posts:
        for height,mat,desc in ((z+.14,BASE,'plinth'),(z+1.18,POST,'shaft'),
                                (t-.041,CAP,'capital')):
            shoot(name+' '+desc,[x,y-.65,height],[0,1.,0],1.,mat)
    cams=read(HERE/'south-garden-two-view-registration.json')['cameras']
    matrices={5:cams[0]['projection'],13:cams[1]['projection'],
              8:read(HERE/'south-veranda-depth-and-third-camera.json')['camera_08']}
    observations=[]
    for row in read(HERE/'south-balustrade-photo-readings.json')['measurements']:
        if row['image'] not in matrices:continue
        P=np.array(matrices[row['image']]);inv=np.linalg.inv(P[:,:3]);eye=-inv@P[:,3]
        for u,v in row['points']:
            direction=inv@np.array([u,v,1])
            hit=scene.ray(eye,direction,55)
            observations.append(dict(image=row['image'],run=row['series'],point_px=[u,v],
                                     first=hit,stone_spindle_seen=bool(hit and hit['material']==BOTTLE)))
    refined=[]
    for measured in read(HERE/'upper-east-baluster-second-camera.json')['samples']:
        number=measured['photo'];P=np.array(matrices[number])
        inv=np.linalg.inv(P[:,:3]);eye=-inv@P[:,3]
        for index,u in enumerate(measured['centers_u']):
            w=P@np.array([13.39575336+index*.27659723,.086965,5.45,1.])
            v=float(w[1]/w[2])
            hit=scene.ray(eye,inv@np.array([u,v,1]),55)
            refined.append(dict(photo=number,read_u=u,section_v=v,first=hit,
                                matched=bool(hit and hit['material']==BOTTLE)))
    return dict(east_refined_horizontal_section=refined,mesh=mesh.name,sha256=hashlib.sha256(mesh.read_bytes()).hexdigest(),
                surface_samples=len(checks),surface_pass=sum(r['pass_surface']for r in checks),
                surface_rays=checks,fixed_photo_rays=observations,
                fixed_photo_spindles=sum(r['stone_spindle_seen']for r in observations),
                fixed_photo_count=len(observations),
                criteria='Positive surface and opening checks use the real first intersection; the fixed photograph pixels are counted separately, including foreground masonry and parallax discrepancies.')


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mesh',type=Path)
    ap.add_argument('report',type=Path);args=ap.parse_args()
    proof=check(args.mesh);payload=(json.dumps(proof,ensure_ascii=False,indent=2)+'\n').encode()
    args.report.parent.mkdir(parents=True,exist_ok=True)
    data=gzip.compress(payload,mtime=0) if args.report.suffix=='.gz' else payload
    tmp=args.report.with_name(args.report.name+'.new');tmp.write_bytes(data);tmp.replace(args.report)
    print(proof['sha256'],proof['surface_pass'],proof['surface_samples'],
          proof['fixed_photo_spindles'],proof['fixed_photo_count'])
    for r in proof['surface_rays']:
        if not r['pass_surface']:print(r['sample'],r['expected'],
                                     r['actual']['material'] if r['actual'] else None)
