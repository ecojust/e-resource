"""Measure inset stones, joints, soil and step-side kerbs in the delivered mesh."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'source'))
sys.path.insert(0,str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact'))
from garden_planters import sections, PLASTER, STONE, STONE_EDGE, EARTH, PANEL
from glb_triangles import SerialScene


def review(mesh):
    scene=SerialScene(mesh)
    obs=json.loads((HERE/'garden-planter-corners.json').read_bytes())
    cameras=json.loads((HERE/'south-garden-two-view-registration.json').read_bytes())['cameras']
    P5=cameras[0]['projection']
    P8=json.loads((HERE/'south-veranda-depth-and-third-camera.json').read_bytes())['camera_08']
    physical=[];photo=[]
    def shoot(note,origin,direction,expected):
        hit=scene.ray(origin,direction,.62)
        physical.append(dict(test=note,origin=list(origin),direction=list(direction),
                             expected=expected,hit=hit,passed=bool(hit and hit['material']==expected)))
    def sight(name,P,uv,target):
        P=np.asarray(P);inv=np.linalg.inv(P[:,:3]);eye=-inv@P[:,3];d=inv@np.array([*uv,1])
        hit=scene.ray(eye,d,55.)
        photo.append(dict(photo=name,uv=list(uv),expected=target,first=hit,
                          matches=bool(hit and hit['material']==target)))
    for side,info in obs['walls'].items():
        points,joins,lengths=sections(obs,side)
        for i,(row,length) in enumerate(zip(info['segments'],lengths)):
            a,b=points[i:i+2]
            tangent=(b-a)/length;normal=np.array([-tangent[1],tangent[0]])
            name=f'{side} {i+1}'
            positions=row['center_fractions']
            def face(f,z,mat,title):
                xy=(1-f)*a+f*b-normal*.15
                shoot(name+' '+title,[*xy,z],[*normal,0.],mat)
            for j,f in enumerate(positions):
                face(f,.173,PANEL,'inset '+str(j+1))
            for j,(l,r) in enumerate(zip(positions,positions[1:])):
                face((l+r)/2,.173,PLASTER,'joint '+str(j+1))
            for f in (.31,.73):
                face(f,.371,STONE_EDGE,'drip')
                # Coping and soil are measured vertically on their own surface.
                for offset,title,mat in ((.072,'coping',STONE),(.310,'soil',EARTH)):
                    xy=(1-f)*a+f*b+((1-f)*joins[i]+f*joins[i+1])*offset
                    shoot(name+' '+title,[*xy,.713],[0.,0.,-1.],mat)
    # Native centres marked on 05 and 08. The full scene is intersected,
    # including underlying yard, stairs and material seen through foliage.
    samples={5:[(56,455),(76,462),(99,464),(125,469),(154,472),(183,475),(218,478),
                (254,482),(298,478),(346,477),(388,472),(418,462),(620,440),
                (654,446),(673,442),(693,439),(710,436),(726,432),(742,429),(753,425)],
             8:[(13,459),(65,462),(126,460),(195,453),(597,453),(656,465),(703,464),(768,463)]}
    for n,P in ((5,P5),(8,P8)):
        for uv in samples[n]:sight(f'{n:02}',P,uv,PANEL)
    initial=photo[:]
    s,r,tx,ty=obs['southwest_yard_fit']['photo05_to_08_ground_similarity']
    yard_transform=np.array([[s,-r,0,tx],[r,s,0,ty],[0,0,1,0],[0,0,0,1.]])
    local05=np.asarray(P5)@np.linalg.inv(yard_transform)
    photo=[]
    for uv in samples[5]:sight('05 yard, four feet registered',local05,uv,PANEL)
    local=photo
    photo=initial
    return dict(forecourt_05=local,forecourt_05_matched=sum(v['matches'] for v in local),
                alternate_camera='05 yard-only similarity from four corresponding feet; fixed native grey panel coordinates unchanged; building camera is retained above.',
                mesh=mesh.name,sha256=hashlib.sha256(mesh.read_bytes()).hexdigest(),
                passed=sum(p['passed'] for p in physical),total=len(physical),surface_tests=physical,
                photo_matched=sum(p['matches'] for p in photo),photo_total=len(photo),photo_first_hits=photo,
                camera_limit='Camera 05 was calibrated on the building. Its four courtyard feet differ from 08 on a common Z0 plane; the measured yard transformation is retained in garden-planter-corners.json. These native pixels are unadjusted.')

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mesh',type=Path)
    ap.add_argument('output',type=Path);args=ap.parse_args();res=review(args.mesh)
    data=(json.dumps(res,ensure_ascii=False,indent=2)+'\n').encode()
    args.output.parent.mkdir(parents=True,exist_ok=True);tmp=args.output.with_name(args.output.name+'.new')
    tmp.write_bytes(gzip.compress(data,mtime=0) if args.output.suffix=='.gz' else data);tmp.replace(args.output)
    print(res['sha256'],res['passed'],res['total'],res['photo_matched'],res['photo_total'])
    for entry in res['surface_tests']:
        if not entry['passed']:print(entry['test'],entry['hit'])
