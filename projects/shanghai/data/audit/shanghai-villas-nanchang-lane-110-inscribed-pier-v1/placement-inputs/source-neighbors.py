"""Decode the signed original near groups and coarse distant group for every preserved neighbor."""
from model import *
from collections import Counter
original=runpy.run_path(str(w/'decode-source.py'))
wanted={3695,*ri(w/'footprint-review.json')['checked_neighbors']};seen={};hashes=[]
for group in frame['groups']:
    for tier,t,owners,_ in original['decode'](group):
        for i in set(owners)&wanted:
            if (tier,int(i)) in seen:continue
            triangles=t[owners==i];bounds=[triangles.min(axis=(0,1)).tolist(),triangles.max(axis=(0,1)).tolist()]
            seen[(tier,int(i))]=dict(tier=tier,id=int(i),triangles=len(triangles),bounds=bounds,height_m=bounds[1][2],array_sha256=sha(triangles.astype('<f8').tobytes()))
    hashes.append(dict(group=group['file'],source_sha256=group['sha256']))
assert set(seen)=={(tier,i) for i in wanted for tier in ('near','far')},set(seen)
save(w/'retained-owner-measurements.json',dict(id=model_id,owned_source=3695,checked_neighbors=sorted(wanted-{3695}),unchanged_near_far=list(seen.values()),sources=hashes,original_triangle_clip_count=0,original_city_replacements=[]))
print('source groups',len(hashes),'true owner',[(role,seen[(role,3695)]['triangles'],seen[(role,3695)]['height_m'])for role in ('near','far')])
