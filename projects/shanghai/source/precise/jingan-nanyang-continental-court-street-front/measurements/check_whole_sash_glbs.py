"""Compare first intersections in all three delivered whole-building GLBs."""
import gzip,hashlib,json,struct,sys
from pathlib import Path
import numpy as np

project=Path(__file__).resolve().parents[1]
pack=Path(sys.argv[1])
outdir=Path(sys.argv[2]).resolve() if len(sys.argv)>2 else project.parents[2]/'data/audit/nanyang-continental-court-street-front-v1/sashes'
sys.path.insert(0,str(project/'source'))
from continental_street_wall import Bay,SCHEDULE


def load(path):
    raw=path.read_bytes()
    assert struct.unpack_from('<4sII',raw)==(b'glTF',2,len(raw))
    sz,kind=struct.unpack_from('<I4s',raw,12);assert kind==b'JSON'
    doc=json.loads(raw[20:20+sz]);buf=memoryview(raw)[28+sz:]
    assert len(doc['nodes'])==1 and 'mesh' in doc['nodes'][0] and not any(k in doc['nodes'][0] for k in ('matrix','translation','rotation','scale'))
    def access(i):
        a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']]
        d=np.dtype({5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']]);cols={'SCALAR':1,'VEC3':3,'VEC2':2}[a['type']]
        return np.ndarray((a['count'],cols),d,buf,v.get('byteOffset',0)+a.get('byteOffset',0),(v.get('byteStride',cols*d.itemsize),d.itemsize))
    mats=[m['name'] for m in doc['materials']]
    tris=[];materials=[];uv_counts={}
    for p in doc['meshes'][0]['primitives']:
        v=access(p['attributes']['POSITION']);f=access(p['indices']).reshape(-1,3)
        tri=v[f][:,:,[0,2,1]].copy();tri[:,:,1]*=-1
        tris.append(tri);materials.append(np.full(len(f),p['material'],np.int16))
        if mats[p['material']].startswith('Windows |') and mats[p['material']].endswith('glass'):
            uv=access(p['attributes']['TEXCOORD_0'])
            assert np.isfinite(uv).all()
            uv_counts[mats[p['material']]]=dict(vertices=len(uv),faces=len(f))
    assert len(uv_counts)==3
    return np.concatenate(tris),np.concatenate(materials),mats,uv_counts,hashlib.sha256(raw).hexdigest()


def projected_hit(v,ids,ox,oy):
    a,b,c=v.transpose((1,0,2))
    ab=b-a;ac=c-a
    det=ab[:,0]*ac[:,2]-ab[:,2]*ac[:,0]
    use=abs(det)>1.e-10
    a,ab,ac,ids,det=a[use],ab[use],ac[use],ids[use],det[use]
    u=((ox-a[:,0])*ac[:,2]-(oy-a[:,2])*ac[:,0])/det
    w=(ab[:,0]*(oy-a[:,2])-ab[:,2]*(ox-a[:,0]))/det
    use=(u>=-2e-7)&(w>=-2e-7)&(u+w<=1+2e-7)
    depths=a[:,1]+ab[:,1]*u+ac[:,1]*w
    return sorted(zip(depths[use],ids[use]))


def main(variant):
    triangles,material,mats,uv,sha=load(pack/(variant+'.glb'))
    all_rays=[];results={};failing=[]
    for row in SCHEDULE:
        i=row['bay'];bay=Bay(i)
        for fl in row['floors']:
            floor=fl['floor'];lo,hi=fl['sill_z'],fl['head_z'];front=fl['face_depth_m']+fl['sash_recess_m']
            use=(triangles[:,:,2].min(axis=1)<=hi+.1)&(triangles[:,:,2].max(axis=1)>=lo-.1)
            tris=triangles[use];ids=material[use]
            for k,(a,b) in enumerate(fl['openings_u_m']):
                width=b-a;height=hi-lo
                tests=[('jamb',a+.028,lo+.40),('head',a+.315*width,hi-.024),('sill-frame',a+.387*width,lo+.027),
                       ('lower sample A',a+width*.31,lo+height*.36),('lower sample B',a+width*.79,lo+height*.56),
                       ('upper sample',a+width*.254,lo+height*.848)]
                if (i,floor,k)==(7,4,0):
                    tests.extend([('open left',a+.42*width,lo+.81),('open right',a+.54*width,lo+.81),('inner stile',(a+b)/2,lo+.83)])
                if k+1<len(fl['openings_u_m']):
                    tests.append(('masonry between windows',(b+fl['openings_u_m'][k+1][0])/2,lo+.92))
                for role,u,z in tests:
                    start=np.array(bay.point(u,-1.8,z));face=np.array(bay.point(u,front,z))
                    direction=(face-start);direction/=np.linalg.norm(direction)
                    perp=np.array((direction[1],-direction[0],0))
                    xy=tris[:,:,0]*perp[0]+tris[:,:,1]*perp[1];sx=start@perp
                    use2=(tris[:,:,2].min(axis=1)<=z)&(tris[:,:,2].max(axis=1)>=z)&(xy.min(axis=1)<=sx)&(xy.max(axis=1)>=sx)
                    cand=tris[use2];v=np.empty_like(cand)
                    v[:,:,0]=xy[use2];v[:,:,2]=cand[:,:,2];v[:,:,1]=cand[:,:,0]*direction[0]+cand[:,:,1]*direction[1]-(start@direction)
                    hits=projected_hit(v,ids[use2],sx,z)
                    hits=[(float(t),mats[m]) for t,m in hits if t>0]
                    first=hits[0] if hits else None
                    sash=next((r for r in hits if r[1].startswith('Windows |')),None)
                    cat='open' if first is None else first[1]
                    results.setdefault(role,{});results[role][cat]=results[role].get(cat,0)+1
                    all_rays.append([i,floor,k,role,round(u,5),round(z,5),np.round(start,5).tolist(),
                                     np.round(direction,7).tolist(),first,sash])
                    if role in ('jamb','head','sill-frame','inner stile'):
                        good=first and first[1].startswith('Windows |') and not first[1].endswith('glass')
                    elif role=='masonry between windows':
                        good=first and not first[1].startswith('Windows |')
                    elif role.startswith('open '):
                        good=sash is None or sash[0]>np.linalg.norm(face-start)+2
                    else:good=True
                    if not good:failing.append(all_rays[-1])
    return dict(variant=variant,sha256=sha,triangles=len(triangles),counts=results,glass_uvs=uv,ray_count=len(all_rays),unexpected=failing),all_rays


summaries=[];all_values={}
for variant in ('raw','decoded-full','decoded-lod'):
    s,values=main(variant);summaries.append(s);all_values[variant]=values
    print(variant,s['ray_count'],len(s['unexpected']),flush=True)
outdir.mkdir(exist_ok=True,parents=True)
data=dict(schedule_sha256=hashlib.sha256((project/'measurements/street-window-schedule.json').read_bytes()).hexdigest(),scope='First hit on the entire building; first window hit is also retained when another object is closer.',rays_fields=['bay','storey','opening','sample','u_m','z_m','world_origin','world_direction','first_overall','first_window'],variants=summaries)
(outdir/'whole-export-sash-checks.json').write_text(json.dumps(data,indent=2)+'\n')
(outdir/'whole-export-sash-rays.json.gz').write_bytes(gzip.compress(json.dumps(all_values,separators=(',',':')).encode(),mtime=0))
if any(s['unexpected'] for s in summaries):raise SystemExit(1)
