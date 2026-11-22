"""Check the two camera paths and the retained 3343 roof against actual macro and delivered triangles."""
from collections import Counter
from contextlib import ExitStack
from tempfile import TemporaryDirectory
from model import *
import subprocess

crossings = runpy.run_path(str(project/'data/audit/daxin-tobacco-northeast-tower-v1/check-physical-city-rays.py'))['crossings']
physical = ri(w/'selected-camera.json')
cut = G.shape(crop['cut_local'])
source = ri(w/'metadata.json')
def get_file(name, expected):
    with urlopen(source['source']+name,timeout=25) as r:
        data = r.read()
        assert r.status == 200 and sha(data) == expected, name
    return data

ready = json.loads(get_file('READY.json', source['ready_sha256']))
table = json.loads(gzip.decompress(get_file('feature-table.json.gz',orig['sources']['table'])))['features']
polygons = {r['localId']:g.transform(G.shape(r['geometry']),loc) for r in table}
scenes = make_scenes()
views = physical['physical']
cases = [(role,row['screen'],np.array(row['eye_local']),sample['feature'],np.array(sample['first_hit']['point_enu_m']))
         for role,rows in views.items() for row in rows for sample in row['samples'] if sample['visible']]
corridor=g.union_all([G.LineString([eye[:2],end[:2]]) for _,_,eye,_,end in cases]).convex_hull.buffer(2.5)
nearby={key for key,polygon in polygons.items() if polygon.intersects(corridor)}
def tile_rows(obj):
    if isinstance(obj,dict):
        if 'featureLocalIds' in obj and 'file' in obj:
            yield obj
        else:
            for val in obj.values(): yield from tile_rows(val)
    if isinstance(obj,list):
        for val in obj: yield from tile_rows(val)
groups={r['file']:r for r in tile_rows(ready) if nearby.intersection(r['featureLocalIds'])}
assert groups and 3343 in nearby and nearby.issubset(set().union(*(set(r['featureLocalIds']) for r in groups.values())))
def decode(group):
    with TemporaryDirectory(dir=w,prefix='cpu-') as directory, ExitStack() as stack:
        base=Path(directory)
        def mem(name,data=b''):
            fd=os.memfd_create(name)
            stack.callback(os.close,fd); os.write(fd,data)
            (base/name).symlink_to(f'/proc/{os.getpid()}/fd/{fd}')
            return fd
        mem('baseline-far.glb',far_bytes)
        mem('baseline-near.glb.gz',get_file(group['file'],group['sha256']))
        mem('macro-READY.json',json.dumps(dict(origin_longitude=source['origin'][0],origin_latitude=source['origin'][1])).encode())
        mem('initial-local-frame.json',json.dumps({'anchor':orig['anchor']}).encode())
        mem('context-features.json',json.dumps([{'localId':i} for i in group['featureLocalIds']]).encode())
        dest={(v,s):mem(f'baseline-{v}-{s}') for v in ('near','far') for s in ('triangles.f64','owners.u32')}
        mem('source-decode.json')
        subprocess.run(['node',project/'data/audit/postal-office-v1/map-decode-source.mjs'],
                       env={**os.environ,'POSTAL_MAPPING_WORK':str(base)},check=True,stdout=subprocess.DEVNULL)
        for level in ('near','far'):
            def array(s,dtype):
                fd=dest[level,s]; return np.frombuffer(os.pread(fd,os.fstat(fd).st_size,0),dtype)
            tri=array('triangles.f64',np.float64).copy().reshape(-1,3,3)
            tri[:,:,:2]=tri[:,:,:2]@axes.T
            group_ids=np.array(group['featureLocalIds'])
            if level=='far': owner=array('owners.u32',np.uint32)
            else:
                center=g.points(tri[:,:,:2].mean(axis=1))
                distances=np.stack([g.distance(center,polygons[i]) for i in group_ids],axis=1)
                owner=group_ids[distances.argmin(axis=1)]
            yield level,tri,owner

far_bytes=get_file(source['far']['file'],source['far']['sha256'])
ray_rows=[];roof_rows=[];target_owners=set();neighbor_tables=[]
for group in groups.values():
    print('checking',group['file'],flush=True)
    for level,tri,owner in decode(group):
        checks=[]
        for role,label,eye,name,end in cases:
            ids,points=crossings(eye,end,tri);removed=(owner[ids]==3343)&g.covers(cut,g.points(points[:,:2]))
            blockers=[{'owner':int(k),'hit':p.tolist()} for k,p in zip(owner[ids[~removed]],points[~removed])]
            checks.append(dict(mesh=role,view=label,feature=name,original_crossings=len(ids),removed_crossings=int(removed.sum()),retained_blockers=blockers))
        ray_rows.append(dict(group=group['file'],sha256=group['sha256'],lod=level,triangle_count=len(tri),checks=checks))
        counts=Counter(int(k) for k in owner)
        neighbor_tables.append(dict(group=group['file'],source_lod=level,source_sha256=group['sha256'],original_triangle_counts=counts))
        target_owners.update(counts)
        if not counts[3343]: continue
        source_tri=tri[owner==3343]
        roof_points=[]
        for x in (-4,0,4):
            seam_y=5.48+(x+9.39)*(4.5-5.48)/(8.50+9.39)
            for y in (seam_y+.12,seam_y+2.30):
                _,hits=crossings(np.array([x,y,65.]),np.array([x,y,-.5]),source_tri)
                assert len(hits) and not cut.covers(Point(x,y))
                roof=hits[np.argmax(hits[:,2])]
                assert 25.70 < roof[2] < 25.80
                roof_points.append(roof)
        for view in views['full']:
            label=view['screen']; eye=np.array(view['eye_local'])
            for role in ('full','lod'):
                for point in roof_points:
                    ray=point-eye;distance=np.linalg.norm(ray)
                    hit=scenes[role].ray(eye,ray.copy(),distance-.015)
                    roof_rows.append(dict(level=level,model=role,view=label,eye=eye.tolist(),roof_point=point.tolist(),model_occluder=hit,clears_detailed_model=hit is None))
        for distance in (11,14,18,30):
            eye=np.array([0.,-float(distance),1.65]);point=roof_points[2]
            for role in ('full','lod'):
                hit=scenes[role].ray(eye,point-eye,np.linalg.norm(point-eye)-.015)
                roof_rows.append(dict(level=level,model=role,view=f'garden-{distance}m',eye=eye.tolist(),roof_point=point.tolist(),model_occluder=hit,clears_detailed_model=hit is None))
assert len(cases)==64
blockers=[k for r in ray_rows for k in r['checks'] if k['retained_blockers']]
save(w/'original-city-sightlines.json',dict(id=m['id'],passed=not blockers,contract_sha256=sha((w/'final-placement-contract.json').read_bytes()),model_rays_sha256=sha((w/'model-sightlines.json').read_bytes()),method='Two-sided triangle intersections with each real near and far group touching the camera-ray corridor plus 2.5 metres. Exclude only owner 3343 fragments physically inside the local cut.',ray_corridor_owner_ids=sorted(nearby),unique_model_rays=len(cases),results=ray_rows,retained_blocker_count=len(blockers)))
save(w/'neighbor-meshes.json',dict(id=m['id'],owner=3343,near_group_count=len(groups),source_triangle_counts=neighbor_tables,all_group_owners=sorted(target_owners),source_ready_sha256=source['ready_sha256'],collision_negatives=ri(w/'map-case.json')['neighborGround'],untouched_in_cut=ri(w/'proposed-source-cut.json')['other_owners']))
save(w/'retained-roof.json',dict(id=m['id'],measured_roof_height_m=25.75,delivered_crown_elevation_m=float(scenes['full'].tri[:,:,2].max()),method='Vertical intersections on the signed original near/far roof behind the retained cut; then cast toward the resulting point against both final detailed meshes. Garden views are hypothetical local eye heights, not observed camera positions.',observations=roof_rows))
print('groups',len(groups),'ray checks',sum(len(r['checks'])for r in ray_rows),'retained blockers',len(blockers),'roof observations',len(roof_rows),flush=True)
assert not blockers,blockers[:2]
