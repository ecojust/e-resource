from pathlib import Path
import json,gzip,math,os,sys,subprocess
from shapely.geometry import shape
import argparse
here=Path(__file__).resolve().parent
p=here.parents[2] if here.name=='bank-of-east-asia-corner-v1' else Path(os.environ.get('SHANGHAI_PROJECT_ROOT','/workspace/e-resource/projects/shanghai'))
audit=p/'data/audit/bank-of-east-asia-corner-v1'
parser=argparse.ArgumentParser(description='Build the map test from the signed predecessor and the street frontage.')
scope=parser.add_mutually_exclusive_group(required=True)
scope.add_argument('--previous-catalog',type=Path)
scope.add_argument('--geometry-only',action='store_true')
parser.add_argument('--manifest',type=Path,default=p/'assets/models/candidates/huangpu-bank-of-east-asia-corner/manifest.json')
parser.add_argument('--table',type=Path,required=True)
parser.add_argument('--placement',type=Path,default=audit/'placement-geometry.json')
parser.add_argument('--contract',type=Path,default=audit/'final-placement-contract.json')
parser.add_argument('--out',type=Path,default=audit/'map-case.json')
args=parser.parse_args()
ident='huangpu-bank-of-east-asia-corner'
audit=p/'data/audit/bank-of-east-asia-corner-v1'
read=lambda path:json.loads(path.read_bytes())
parent=args.previous_catalog
catalog=read(parent) if parent else None
if catalog:assert catalog['models'][-1]['id']=='huangpu-hardoon-building-chamfer'
source=read(p/'source/precise'/ident/'footprint-review.json');place=read(args.placement);contract=read(args.contract)
assert len(source['near_tiles'])==1
group=set(source['near_tiles'][0]['feature_local_ids'])
prior=[r for r in (catalog['models'] if catalog else []) if r.get('owner',{}).get('macro_id')==source['frozen_macro']]
# Reconstruct the predecessor's three clip categories from the catalog itself.
# A height-limited colonnade can use an owner even when the row has no primary cut.
before = {}
height_clips = []
for row in catalog['models'] if catalog else []:
    if row.get('replacement_geometry'):
        before[row['id']] = {**row, 'geometry': row['replacement_geometry']}
    site = row.get('site_replacement')
    if site:
        before[site['id']] = site
    height_clips.extend(row.get('display_height_clips') or [])
affected_owners = set()
geometry = []
for clip in [*before.values(), *height_clips]:
    for owner in clip.get('owners') or [clip['owner']]:
        if owner['macro_id'] == source['frozen_macro'] and owner['feature_local_id'] in group:
            affected_owners.add(owner['feature_local_id'])
            geometry.append(clip['geometry'])
assert contract['owner']['feature_local_id'] not in affected_owners
geometry.append(contract['replacement_geometry'])
counts = json.loads(subprocess.check_output(['node', audit/'count-clip-triangles.mjs'], input=json.dumps(geometry).encode()))
assert len(counts) == len(geometry) and all(value > 0 for value in counts)
neighbors=sorted(int(k)for k in place['neighbors'])
with gzip.open(args.table) as fp: features=json.load(fp)['features']
centers={r['localId']:list(shape(r['geometry']).representative_point().coords[0]) for r in features if r['localId']in neighbors}
assert set(centers)==set(neighbors)
ground=[dict(name=g['name'],xy=g['xy'],expected=g['expected_map'],modelObstacle=g['model_obstacle'],cut=g['source_cut']) for g in place['ground_probes']]
# The vector renderer must preserve the rest of this owner's original building.
owner = next(row for row in features if row['localId'] == contract['owner']['feature_local_id'])
remainder = shape(owner['geometry']).difference(shape(contract['replacement_geometry']))
point = remainder.representative_point()
assert remainder.contains(point) and point.distance(remainder.boundary) > 0.00002
lon, lat = map(math.radians, [contract['lng'], contract['lat']])
east = (math.radians(point.x) - lon) * 6371008.8 * math.cos(lat)
north = (math.asinh(math.tan(math.radians(point.y))) - math.asinh(math.tan(lat))) * 6371008.8 * math.cos(lat)
heading = math.radians(contract['heading'])
xy = [east * math.cos(heading) - north * math.sin(heading), east * math.sin(heading) + north * math.cos(heading)]
ground.append(dict(name='原楼保留的内部地面', xy=xy, expected='building', modelObstacle=False, cut=False, ownerLocalId=owner['localId']))
bounds=read(args.manifest)['assets']['raw']['bounds_gltf_m'];height=bounds[1][1]-bounds[0][1];assert height>0
case=dict(id=ident,previous=catalog['models'][-1]['id'] if catalog else None,neighbors=neighbors,neighborGround=centers,existingCandidateOwners=sorted({r['owner']['feature_local_id']for r in prior}.intersection(neighbors)),existingGroupOwners=sorted(affected_owners),groupTriangles=sum(counts),addedTriangles=counts[-1],sourceSectionCount=place['seam_segments'],front=dict(center=[0,-.2],elevation=bounds[0][1]+height*.29,bearingOffset=-4,pitch=39,zoom=19.95),roof=dict(center=[0,.1],elevation=bounds[0][1]+height*.83,bearingOffset=4,pitch=32,zoom=20.1),ground=ground,residualCutProbe=next(g['xy']for g in ground if g['cut']and g['modelObstacle']))
assert len(ground)==len(place['ground_probes'])+1 and set(centers)==set(neighbors) and place['seam_segments']>0
if args.geometry_only:
 import hashlib
 for key in ('previous','existingCandidateOwners','existingGroupOwners','groupTriangles'):case.pop(key)
 case['schema']='bank-of-east-asia-corner-local-geometry-v1'
 case['inputs_sha256']={k:hashlib.sha256(v.read_bytes()).hexdigest() for k,v in [('placement',args.placement),('contract',args.contract),('manifest',args.manifest),('feature_table',args.table)]}
 case['source_group']=source['near_tiles'][0]['id']
 case['source_owner']=contract['owner']
 case['bounds_gltf_m']=bounds
 case['retained_percent']={k:100*v['retained_m2']/v['source_projected_m2']for k,v in place['native_variants'].items()}
 assert all(v['foreign_intersections']==0 for v in place['native_variants'].values())
args.out.write_text(json.dumps(case,ensure_ascii=False,indent=2)+'\n')
print(counts,len(centers),len(ground))
