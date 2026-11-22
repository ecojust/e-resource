"""Trace the selected ordinary-camera rays into the original near and distant city and record the retained roof."""
from model import *
from collections import Counter
from shapely.geometry import LineString

m,scenes=make_scenes(Path(sys.argv[1]));selected=ri(w/'selected-camera.json');cutinfo=ri(w/'proposed-source-cut.json');cut=G.shape(cutinfo['cut_local'])
original=runpy.run_path(str(w/'decode-source.py'));intersect=runpy.run_path(str(project/'data/audit/daxin-tobacco-northeast-tower-v1/check-physical-city-rays.py'))['crossings']
ready=json.loads(original['take']('READY.json',original['hashes']['READY.json']));samples=[];neighbor_tables=[];roof_rows=[];levels=[]
for role,views in selected['physical'].items():
    for view in views:
        for sample in view['samples']:
            if sample['visible']:
                samples.append((role,view['screen'],np.array(view['eye_local']),sample['feature'],np.array(sample['first_hit']['point_enu_m'])))
corridor=g.union_all([LineString([eye[:2],end[:2]]) for _,_,eye,_,end in samples]).convex_hull.buffer(2.5)
nearby={i for i,s in original['polygons'].items() if s.intersects(corridor)}
groups=[dict(id=t['id'],file=t['file'],sha256=t['sha256'],owners=t['featureLocalIds'],triangles=t['expandedTriangles']) for t in ready['tiles'] if nearby.intersection(t['featureLocalIds'])]
assert 1292 in nearby and groups
for group in groups:
    for tier,tri,owners,gap in original['decode'](group):
        checks=[]
        for role,screen,eye,name,end in samples:
            ids,hits=intersect(eye,end,tri);removed=(owners[ids]==1292)&g.covers(cut,g.points(hits[:,:2]))
            checks.append(dict(mesh=role,view=screen,feature=name,original_crossings=len(ids),removed_crossings=int(removed.sum()),retained_blockers=[dict(owner=int(i),point=p.tolist()) for i,p in zip(owners[ids][~removed],hits[~removed])]))
        levels.append(dict(group=group['file'],sha256=group['sha256'],lod=tier,triangle_count=len(tri),checks=checks))
        counts=Counter(int(i)for i in owners);neighbor_tables.append(dict(group=group['file'],source_lod=tier,source_sha256=group['sha256'],original_triangle_counts=dict(counts)))
        if 1292 not in group['owners']:continue
        cells=tri[owners==1292];assert len(cells)>40
        for x,y in [(-4.,4.50),(0,4.80),(4.,4.50),(-3.5,7.2),(0,7.2),(3.5,7.2)]:
            assert not cut.covers(Point(x,y));_,hits=intersect(np.array([x,y,60.]),np.array([x,y,0.]),cells);assert len(hits)
            roof=hits[np.argmax(hits[:,2])];assert 29.47<roof[2]<29.54
            eyes={v['screen']:np.array(v['eye_local']) for v in selected['physical']['full']}
            eyes.update({'garden-'+str(n)+'m':np.array([0.,-float(n),1.65])for n in (10,15,22)})
            for view,eye in eyes.items():
                for role in ('full','lod'):
                    dv=roof-eye;distance=np.linalg.norm(dv);first=scenes[role].ray(eye,dv.copy(),distance-.015)
                    roof_rows.append(dict(original=tier,role=role,viewport=view,eye=eye.tolist(),original_roof=roof.tolist(),model_occluder=first,clears_portico=first is None))
blockers=[r for block in levels for r in block['checks']if r['retained_blockers']];base=sha((w/'final-placement-contract.json').read_bytes())
save(w/'original-city-sightlines.json',dict(id=m['id'],passed=not blockers,contract_sha256=base,model_rays_sha256=sha((w/'model-sightlines.json').read_bytes()),ray_corridor_owner_ids=sorted(nearby),unique_model_rays=len(samples),results=levels,retained_blocker_count=len(blockers)))
save(w/'retained-roof.json',dict(id=m['id'],measured_roof_height_m=29.50,portico_max_height=float(scenes['full'].tri[:,:,2].max()),source='Each signed near and distant original roof intersection was tested against the detailed portico. Ground eyes are illustrative meter offsets from its front.',observations=roof_rows))
save(w/'neighbor-meshes.json',dict(id=m['id'],owner=1292,source_triangle_counts=neighbor_tables,independently_checked_neighbors=cutinfo['other_owners'],retained_roof=ri(w/'retained-roof.json')['measured_roof_height_m']))
print('source rays',sum(len(b['checks'])for b in levels),'unique',len(samples),'retained blockers',len(blockers),'roof visible',sum(r['clears_portico']for r in roof_rows),'/',len(roof_rows),flush=True)
assert not blockers,blockers[:2]
