"""Read rays through the finished window openings from both registered winter camera centres."""
import argparse,gzip,hashlib,json,struct
from pathlib import Path
import numpy as np

D=Path(__file__).resolve().parent

def mesh(path):
    data=path.read_bytes()
    magic,version,total,n,chunk=struct.unpack_from('<4sIII4s',data)
    assert (magic,version,total,chunk)==(b'glTF',2,len(data),b'JSON')
    scene=json.loads(data[20:20+n]);buf=memoryview(data)[28+n:]
    def accessor(i):
        a=scene['accessors'][i];v=scene['bufferViews'][a['bufferView']]
        dt=np.dtype({5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']])
        width={'SCALAR':1,'VEC2':2,'VEC3':3}[a['type']]
        return np.ndarray((a['count'],width),dt,buf,v.get('byteOffset',0)+a.get('byteOffset',0),
                          strides=(v.get('byteStride',width*dt.itemsize),dt.itemsize))
    labels=[m['name'] for m in scene['materials']];tris=[];ids=[];uv={}
    for node in scene['nodes']:
        if 'mesh' not in node:continue
        assert not set(node)&{'translation','scale','matrix','rotation'}
        for pr in scene['meshes'][node['mesh']]['primitives']:
            ps=accessor(pr['attributes']['POSITION']);v=ps[:,[0,2,1]].copy();v[:,1]*=-1
            a=accessor(pr['indices']).ravel().reshape(-1,3)
            tris.append(v[a]);ids.append(np.full(len(a),pr['material'],np.int16))
            name=labels[pr['material']]
            if name.startswith('Rongkang | ') and 'glass' in name:
                tex=accessor(pr['attributes']['TEXCOORD_0'])
                assert len(tex)==len(v) and np.isfinite(tex).all() and min(np.ptp(tex,axis=0))>.04
                uv[name]=uv.get(name,0)+len(tex)
    assert len(uv)==2
    return np.concatenate(tris),np.concatenate(ids),labels,uv,hashlib.sha256(data).hexdigest()

def projector(P,points):
    r=np.einsum('ij,...j->...i',P[:,:3],points)+P[:,3]
    return np.concatenate([r[...,:2]/r[...,2:],r[...,2:]],axis=-1)

def acceleration(P,tris,ids):
    coords=projector(P,tris.astype(float))
    valid=np.all(coords[:,:,2]>.015,axis=1)
    coords=coords[valid];a,b,c=coords.transpose(1,0,2)
    mn,mx=coords.min(1)[:,:2],coords.max(1)[:,:2]
    ba=b[:,:2]-a[:,:2];ca=c[:,:2]-a[:,:2]
    den=ba[:,0]*ca[:,1]-ba[:,1]*ca[:,0]
    return mn,mx,den,ba,ca,a[:,:2],1/coords[:,:,2],ids[valid]

def intersections(accel,px,py):
    mn,mx,den,ba,ca,a,inv,idx=accel
    i=np.flatnonzero((mn[:,0]<=px)&(mx[:,0]>=px)&(mn[:,1]<=py)&(mx[:,1]>=py)&(np.abs(den)>1e-9))
    dx,dy=px-a[i,0],py-a[i,1]
    b=(dx*ca[i,1]-dy*ca[i,0])/den[i];c=(ba[i,0]*dy-ba[i,1]*dx)/den[i];a=1-b-c
    hit=(a>-.00001)&(b>-.00001)&(c>-.00001)
    depths=1/(inv[i,0]*a+inv[i,1]*b+inv[i,2]*c)
    return sorted((float(d),int(k))for d,k in zip(depths[hit],idx[i][hit]))

def samples(o,far):
    u,v,b,t=[o[n] for n in ('u0','u1','z0','z1')]
    pale=o['frame']=='pale';rim=.040 if pale else .034
    frame='Rongkang | '+('pale painted window frame' if pale else 'dark painted glazing bars')
    glass='Rongkang | '+('glass in shade' if o['id'].endswith('2') or 'return' in o['id'] else 'reflected blue-grey glass')
    yield 'outer jamb',u+rim*.5,b+.4*(t-b),0,frame
    yield 'upper head',u+.28*(v-u),t-.48*rim,0,frame
    l,r,u0,u1=u+rim,v-rim,b+rim,t-rim
    zs=[u0,*[u0+(u1-u0)*f for f in o['horizontal_divisions']],u1]
    for z in zs[1:-1]:yield 'cross rail',l+.29*(r-l),z,.012,frame
    for j,(lo,hi) in enumerate(zip(zs,zs[1:])):
        cuts=o['vertical_divisions'] if j<len(zs)-2 or not o['upper_undivided'] else []
        us=[l,*[l+f*(r-l) for f in cuts],r]
        for u in us[1:-1]:yield 'central glazing bar',u,lo+.52*(hi-lo),.012,frame
        for ll,rr in zip(us,us[1:]):yield 'pane',.5*(ll+rr),lo+.52*(hi-lo),.051 if far else .032,glass

def inspect(path,cams,opening_table):
    tris,ids,labels,uv,signature=mesh(path);output=[];far='lod' in path.name
    for station,cam in cams.items():
        P=np.array(cam['local_xyz_to_image']);ac=acceleration(P,tris,ids)
        for o in opening_table['openings']:
            if station not in o['observed']:continue
            sf=opening_table['surfaces'][o['facade']]
            for component,u,z,d,expected in samples(o,far):
                dep=sf['frame_plane']+sf['depth_slope']*(u-sf['local_reference'])+d*sf.get('inward_sign',1)
                xyz=(u,dep,z)if sf['axis']=='X'else(dep,u,z)
                px,py,g=projector(P,xyz)
                hits=intersections(ac,px,py)
                match=next(((rh,labels[k])for rh,k in hits if labels[k]==expected and abs(rh-g)<.018),None)
                closest=(labels[hits[0][1]],round(hits[0][0]-g,5)) if hits else None
                output.append([station,o['id'],component,round(px,3),round(py,3),expected,closest,
                               round(match[0]-g,5)if match else None])
    return dict(file=path.name,sha256=signature,triangles=len(tris),uv_vertices=uv,rays=output,
                field_count=len(opening_table['openings']),samples=len(output),
                hits=sum(v[-1] is not None for v in output),first_surface_matches=sum(bool(v[6] and v[6][0]==v[5])for v in output))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('measurement_folder',type=Path);ap.add_argument('output',type=Path);ap.add_argument('models',nargs='+',type=Path);args=ap.parse_args()
    cams=json.loads((args.measurement_folder/'southern-neighbouring-cameras.json').read_bytes())
    north=json.loads((args.measurement_folder/'independent-north-window-station.json').read_bytes());cams[north['facade_source']]={'local_xyz_to_image':north['local_xyz_to_image']}
    cams.update(json.loads((args.measurement_folder/'south-outer-window-stations.json').read_bytes())['sources'])
    cams.update(json.loads((args.measurement_folder/'south-inner-window-stations.json').read_bytes())['sources'])
    openings=json.loads((args.measurement_folder/'street-window-openings.json').read_bytes())
    rows=[inspect(p,cams,openings)for p in args.models]
    args.output.mkdir(parents=True,exist_ok=True)
    b=gzip.compress((json.dumps(rows,ensure_ascii=False,separators=(',',':'))+'\n').encode(),mtime=0)
    (args.output/'assembled-window-rays.json.gz').write_bytes(b)
    stats=dict(columns=['actual_camera','opening','component','image_x','image_y','expected_material','first_surface_and_depth_difference','matching_surface_depth_difference'],rays_sha256=hashlib.sha256(b).hexdigest(),meshes=[{k:v for k,v in r.items()if k!='rays'}for r in rows])
    (args.output/'assembled-window-check.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(stats['meshes'],ensure_ascii=False))
    assert all(r['hits']==r['samples'] for r in rows)
