"""Trace the selected ordinary-camera rays into the original near and distant city and record the retained roof."""
from model import *
from collections import Counter
from shapely.geometry import LineString

m,scenes=make_scenes(Path(sys.argv[1]));selected=ri(w/'selected-camera.json');contract=ri(w/'final-placement-contract.json')
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
assert groups
for group in groups:
    for tier,tri,owners,gap in original['decode'](group):
        checks=[]
        for role,screen,eye,name,end in samples:
            ids,hits=intersect(eye,end,tri);removed=np.zeros(len(ids),dtype=bool)
            checks.append(dict(mesh=role,view=screen,feature=name,original_crossings=len(ids),removed_crossings=int(removed.sum()),retained_blockers=[dict(owner=int(i),point=p.tolist()) for i,p in zip(owners[ids][~removed],hits[~removed])]))
        levels.append(dict(group=group['file'],sha256=group['sha256'],lod=tier,triangle_count=len(tri),checks=checks))
        counts=Counter(int(i)for i in owners);neighbor_tables.append(dict(group=group['file'],source_lod=tier,source_sha256=group['sha256'],original_triangle_counts=dict(counts)))
blockers=[r for block in levels for r in block['checks']if r['retained_blockers']];base=sha((w/'final-placement-contract.json').read_bytes())
save(w/'original-city-sightlines.json',dict(id=m['id'],passed=not blockers,contract_sha256=base,model_rays_sha256=sha((w/'model-sightlines.json').read_bytes()),ray_corridor_owner_ids=sorted(nearby),unique_model_rays=len(samples),results=levels,retained_blocker_count=len(blockers)))
source=ri(w/'placement-geometry.json')
save(w/'neighbor-meshes.json',dict(id=m['id'],owner=3695,source_triangle_counts=neighbor_tables,independently_checked_neighbors=ri(w/'footprint-review.json')['checked_neighbors'],source_roof_m=16.5,source_measurements_sha256=sha((w/'placement-geometry.json').read_bytes())))
print('source rays',sum(len(b['checks']) for b in levels),'unique real two-tier/two-screen rays',len(samples),'retained blockers',len(blockers),flush=True)
assert not blockers,blockers[:2]
