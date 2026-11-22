"""Cast camera rays into the actual GLB and count open louvre slots in its centre sections."""
from argparse import ArgumentParser
from collections import Counter
from hashlib import sha256
from pathlib import Path
import json
import sys
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact'))
from glb_triangles import SerialScene
def code(material):
    if not material:return ''
    return material.removeprefix('Huaya windows | ')
MATCH={
 'shutter':{'aged rose shutter rails','faded red timber blades','deep shutter recess'},
 'stone':{'warm grey cast stone','carved pale relief','recessed pediment field'},
 'field':{'recessed pediment field'},'carved':{'carved pale relief'},
}
def digest(p):
    return sha256(p.read_bytes()).hexdigest()
def tests(path):
    scene=SerialScene(path); probes=HERE/'2016-photographic-probes.json';cameras=HERE/'2016-two-window-cameras.json'
    detail=json.loads(probes.read_bytes())['observations']; cam=json.loads(cameras.read_bytes());observed=[]
    for item in detail:
        p=np.asarray(cam[item['camera']]['P']);inv=np.linalg.inv(p[:,:3])
        hit=scene.ray(-inv@p[:,3],inv@[*item['pixel'],1.],35.)
        mat=code(hit['material']) if hit else ''
        observed.append({**item,'first_material':mat,'direct':mat in MATCH[item['expected']]})
    # Unpack each real GLB; intersect only the columns crossing the sash midlines.
    from struct import unpack_from
    raw=path.read_bytes();n=unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+n]);binbuf=raw[28+n:]
    def accessor(idx):
        a=g['accessors'][idx];b=g['bufferViews'][a['bufferView']]
        length={'VEC2':2,'VEC3':3,'SCALAR':1}[a['type']]
        return np.frombuffer(binbuf,dtype={5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']],
            count=a['count']*length,offset=b.get('byteOffset',0)+a.get('byteOffset',0)).reshape(a['count'],length)
    blades=[]
    for mesh in g['meshes']:
        for pr in mesh['primitives']:
            if code(g['materials'][pr['material']]['name'])!='faded red timber blades':continue
            pos=accessor(pr['attributes']['POSITION']);ids=accessor(pr['indices']).ravel()
            blades.append(pos[ids].reshape(-1,3,3))
    triangles=np.concatenate(blades)
    # GLTF axes X, Z-height, -Y. A connected projected interval is one distinct blade.
    bands=[]
    for c in (-2.4,0.,2.4):
        for i in range(4):
            x=c+(i-1.5)*.286
            candidates=triangles[(triangles[:,:,0].min(1)<x)&(triangles[:,:,0].max(1)>x)]
            intervals=[]
            for tr in candidates:
                z=[]
                for a,b in zip(tr,np.roll(tr,-1,axis=0)):
                    if (a[0]-x)*(b[0]-x)>=0:continue
                    w=(x-a[0])/(b[0]-a[0]);z.append(a[1]+w*(b[1]-a[1]))
                if len(z)>=2:intervals.append((min(z),max(z)))
            merged=[]
            for l,h in sorted(intervals):
                if merged and l<merged[-1][1]+.0001:merged[-1][1]=max(merged[-1][1],h)
                else:merged.append([l,h])
            lower=sum(float(h)<1.91 for l,h in merged);upper=len(merged)-lower
            bands.append(dict(bay=c,leaf=i+1,lower=lower,upper=upper))
    return dict(mesh=path.name,sha256=digest(path),direct=sum(i['direct'] for i in observed),tested=len(observed),by_camera={k:dict(hits=sum(i['direct'] for i in observed if i['camera']==k),total=sum(i['camera']==k for i in observed))for k in ('front','oblique')},by_part={t:dict(hits=sum(i['direct'] for i in observed if i['part']==t),total=sum(i['part']==t for i in observed))for t in dict.fromkeys(i['part']for i in observed)},observations=observed,shutter_sections=bands,all_slats_counted=all(r['lower']==30 and r['upper']==11 for r in bands),camera_sha256=digest(cameras),observation_sha256=digest(probes))
if __name__=='__main__':
    ap=ArgumentParser(description=__doc__);ap.add_argument('meshes',nargs='+',type=Path);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    results=[tests(p)for p in a.meshes];a.output.write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
    for r in results:print(r['mesh'],r['by_camera'],r['all_slats_counted'],r['by_part'])
