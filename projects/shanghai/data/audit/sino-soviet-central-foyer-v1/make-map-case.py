from pathlib import Path
import json,gzip,math,sys,subprocess
from shapely.geometry import shape
import argparse
audit=Path(__file__).resolve().parent
p=audit.parents[2]
parser=argparse.ArgumentParser(description='Build the map test from the signed predecessor and the street frontage.')
parser.add_argument('--previous-catalog',type=Path,required=True)
parser.add_argument('--table',type=Path,required=True)
parser.add_argument('--placement',type=Path,default=audit/'placement-geometry.json')
parser.add_argument('--contract',type=Path,default=audit/'final-placement-contract.json')
parser.add_argument('--out',type=Path,default=audit/'map-case.json')
parser.add_argument('--expected-predecessor-id',default='huangpu-south-money-guild-gucheng-gate',help='A different real predecessor can be used for an explicitly saved rehearsal.')
args=parser.parse_args()
ident='jingan-sino-soviet-central-foyer'
audit=p/'data/audit/sino-soviet-central-foyer-v1'
read=lambda path:json.loads(path.read_bytes())
parent=args.previous_catalog
catalog=read(parent);assert catalog['models'][-1]['id']==args.expected_predecessor_id
source=read(p/'source/precise'/ident/'footprint-review.json');place=read(args.placement);contract=read(args.contract)
assert len(source['near_tiles'])==1
group=set(source['near_tiles'][0]['feature_local_ids'])
prior=[r for r in catalog['models'] if r.get('owner',{}).get('macro_id')==source['frozen_macro']]
affected=[r for r in prior if r['owner']['feature_local_id'] in group]
assert {1650,370,1799,2452} <= {r['local_id'] for r in source['owners']}  # a separate original street building
assert all(r['owner']['feature_local_id'] != 969 for r in affected)
geometry=[r['replacement_geometry']for r in affected]+[contract['replacement_geometry']]
counts=json.loads(subprocess.check_output(['node',audit/'count-clip-triangles.mjs'],input=json.dumps(geometry).encode()))
assert len(counts)==len(affected)+1 and all(value>0 for value in counts)
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
case=dict(id=ident,previous=catalog['models'][-1]['id'],neighbors=neighbors,neighborGround=centers,existingCandidateOwners=sorted({r['owner']['feature_local_id']for r in prior}.intersection(neighbors)),existingGroupOwners=list(dict.fromkeys(r['owner']['feature_local_id'] for r in affected)),groupTriangles=sum(counts),addedTriangles=counts[-1],sourceSectionCount=place['seam_segments'],front=dict(center=[0.,8.0],elevation=13.15,bearingOffset=0,pitch=69,zoom=19.25),roof=dict(center=[0.,22.5],elevation=51.,bearingOffset=-18,pitch=54,zoom=18.45),ground=ground,residualCutProbe=next(g['xy']for g in ground if g['cut']and g['modelObstacle']))
assert len(ground)==85 and len(neighbors)==12 and case['sourceSectionCount']>=3
args.out.write_text(json.dumps(case,ensure_ascii=False,indent=2)+'\n')
print(counts,len(centers),len(ground))
