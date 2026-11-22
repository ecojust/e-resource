"""Read the first surface on the original model, two meshopt decodes or a component trial."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
SRC=HERE.parent/'source'
sys.path[:0]=[str(SRC),str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact'),str(HERE/'camera-fit')]
from glb_triangles import SerialScene
from hospital_sashes import BACK, CASE, DIM, EDGE, GLASS, IRON, SHADE, STONE
from hospital_finish import BRICK
import registered
import court_registered


def read(path):
    return json.loads(path.read_bytes())


def inspect(path):
    scene=SerialScene(path)
    layout=read(SRC/'sash-layout.json')
    measurements=[]
    photographic=[]
    def query(origin,direction,materials,labels,limit):
        h=scene.ray(origin,direction,limit)
        first=h['material']if h else None
        p=np.round(h['point_enu_m'],4).tolist()if h else None
        return dict(**labels,allowed_materials=materials,first_material=first,first_xyz=p,
                    triangle_index=h['triangle_index']if h else None,matched=first in materials)
    def from_plane(face,o,u,d,z):
        if face=='north':return np.array([u,d,z])
        if face=='east':return np.array([o['wall_x']+d,u,z])
        return np.array([u,o['wall_y']-d,z])
    for face,rows in layout['faces'].items():
        for o in rows:
            c,w,lo,hi=(o[k]for k in ('center','width','sill','head'))
            rim=min(.055,.034*w)
            g0,g1=c-w/2+rim,c+w/2-rim
            b0,b1=lo+rim,hi-rim
            def sample(u,z,mats,feature):
                eye=from_plane(face,o,u,-1.50,z); target=from_plane(face,o,u,0,z)
                measurements.append(query(eye,target-eye,mats,{'opening':o['id'],'feature':feature,'target_xz':[round(u,4),round(z,4)]},3.0))
            sample(c-w/2+(.013*w+rim)/2,lo+.67*(hi-lo),[CASE],'fixed left upright')
            sample(c,lo+.57*(hi-lo),[IRON,CASE],'central meeting bar')
            rz=b0+2*(b1-b0)/o['rows']
            sample(g0+.5*(g1-g0)/o['cols'],rz,[IRON],'transverse steel bar')
            for i in (0,o['cols']-1):
                sample(g0+(i+.55)*(g1-g0)/o['cols'],b0+1.46*(b1-b0)/o['rows'],[GLASS,DIM],f'glass column {i+1}')
            if o['style']in ('base','ground'):continue
            sample(c,lo-.065*w,[STONE],'sill front')
            if o['style']in ('segment','triangle'):
                sample(c,hi+.46*w,[STONE],'central keystone')
                sample(c+.63*w,hi+.46*w,[EDGE],'broken cornice wing')
                sample(c,hi+1.085*w,[EDGE],'outer crown')
                sample(c-.61*w,(hi+lo)/2,[STONE],'jamb strip')
    for face,rows in layout['faces'].items():
        lower={o['axis']:o for o in rows if o['level']==2}
        for o in rows:
            if o['level']!=3 or o['axis'] not in lower:
                continue
            if face=='east':
                continue
            below=lower[o['axis']]
            if 'backing_span' in o:
                left,right=o['backing_span']
                z=below['head']+.38*(o['sill']-below['head'])
                for frac in (.17,.47,.81):
                    u=left+(right-left)*frac
                    eye=from_plane(face,o,u,-1.5,z);t=from_plane(face,o,u,0,z)
                    measurements.append(query(eye,t-eye,[STONE],{'opening':o['id'],'feature':'continuous stone panel field','section_fraction':frac},3.))
            elif face=='court' and o['axis']in (2,4,6,8):
                z=(o['sill']+below['head'])/2.
                eye=from_plane(face,o,o['center'], -1.50,z);t=from_plane(face,o,o['center'],0,z)
                measurements.append(query(eye,t-eye,[BRICK],{'opening':o['id'],'feature':'uninterrupted court brick between independent flat stone heads'},3.))
    north=read(HERE/'qiao-north-window-pixels.json')
    for r in north['native_wide_pixels']:
        if 'center_uv'not in r:continue
        u,v=r['center_uv']
        photographic.append(query(registered.eye,registered.ray((u,v)),[CASE,IRON,GLASS,DIM,BACK],
            {'photo':'Qiao00','native_uv':[u,v],'axis':r['axis'],'level':r['level'],'feature':'dark aperture'},120))
    for r in read(HERE/'dai-courtyard-window-pixels.json')['observations']:
        corners=np.array(r['upper_left_right_then_lower_right_left'])
        uv=.45*corners[0]+.55*corners[2]
        ray=court_registered.R.T@np.linalg.solve(court_registered.K,[*uv,1.])
        photographic.append(query(court_registered.eye,ray,[CASE,IRON,GLASS,DIM,BACK],
            {'photo':'Dai2020','native_uv':np.round(uv,3).tolist(),'opening':r['id'],'feature':'inside photographed aperture'},110))
    for tag,cam,uv in [('Qiao00',registered,(352,424)),('Qiao00',registered,(449,454)),('Dai2020',court_registered,(455,271)),('Dai2020',court_registered,(251,278))]:
        ray=cam.R.T@np.linalg.solve(cam.K,[*uv,1.])
        photographic.append(query(cam.eye,ray,[STONE],{'photo':tag,'native_uv':list(uv),'feature':'stone field between second and third storeys'},120))
    cam=read(HERE/'east-recess-independent-camera.json');P=np.array(cam['camera_P']);eye=np.array(cam['camera_eye'])
    for r in cam['openings']:
        if r['source']!='facade-10-present':continue
        u0,v0,u1,v1=r['pixels'];u=.45*u0+.55*u1;v=.65*v0+.35*v1
        ray=np.linalg.solve(P[:,:3],[u,v,1.])
        photographic.append(query(eye,ray,[CASE,IRON,GLASS,DIM,BACK],
            {'photo':'2019 east','native_uv':[u,v],'opening':r['id'],'feature':'independent recessed-wall window'},100))
    for r in measurements:
        if r['feature']=='sill front' and r['first_material'] in (EDGE,SHADE):
            r['observed_order_contact']='The projecting lower crown touches the upper window sill at this centreline in the source photograph.'
    return dict(asset_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                control_sha256={f.name:hashlib.sha256(f.read_bytes()).hexdigest()for f in
                  (SRC/'sash-layout.json',SRC/'hospital_sashes.py',HERE/'qiao-north-window-pixels.json',
                   HERE/'dai-courtyard-window-pixels.json',HERE/'east-recess-independent-camera.json')},
                first_surfaces_only=True,normal_samples=len(measurements),normal_matches=sum(x['matched']for x in measurements),
                photo_samples=len(photographic),photo_matches=sum(x['matched']for x in photographic),
                normal_rays=measurements,registered_photo_rays=photographic)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('scene',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();result=inspect(args.scene)
    raw=(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n').encode()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_bytes(gzip.compress(raw,mtime=0)if args.output.suffix=='.gz'else raw)
    print(result['asset_sha256'],result['normal_matches'],result['normal_samples'],result['photo_matches'],result['photo_samples'])
