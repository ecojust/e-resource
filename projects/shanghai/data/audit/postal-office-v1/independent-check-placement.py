"""Independent final-model structural collision and retained-neighbor review.

Decode actual authored GLB triangles directly. Exclude only the specifically
identified shallow court floor from obstacles; retain all U-base/wall/column
triangles. No author or mapping projection routine is imported.
"""
from pathlib import Path
import argparse,hashlib,importlib.util,json,math
import numpy as np
import shapely
from shapely.geometry import Polygon,shape,Point
from shapely.ops import transform
HELPER=Path(__file__).with_name('independent-glb-review-helpers.py')
SPEC=importlib.util.spec_from_file_location('postal_independent_glb_review',HELPER);MOD=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(MOD)


def clip_height(vertices,z,keep_above):
    out=[]
    for i in range(len(vertices)):
        prev=vertices[i-1];cur=vertices[i]
        pin=prev[2]>=z if keep_above else prev[2]<=z
        cin=cur[2]>=z if keep_above else cur[2]<=z
        if pin!=cin:
            f=(z-prev[2])/(cur[2]-prev[2]);point=prev+(cur-prev)*f;point[2]=z;out.append(point)
        if cin:out.append(cur)
    return out


def projections(path,court):
    tri,mi,names,asset=MOD.load_triangles(path);xy=tri[:,:,:2]
    edge_a=xy[:,1]-xy[:,0];edge_b=xy[:,2]-xy[:,0];area2=np.abs(edge_a[:,0]*edge_b[:,1]-edge_a[:,1]*edge_b[:,0]);nonzero=xy[area2>1e-10]
    batches=[shapely.union_all(shapely.polygons(nonzero[i:i+8192])) for i in range(0,len(nonzero),8192)]
    full=shapely.union_all(batches)
    # The authored floor has exactly12 serialized triangles, spans z0..0.16,
    # and projects to the court plan. U-base top0.18 is deliberately retained.
    candidates=(mi==names.index('dark stone'))&(tri[:,:,2].min(axis=1)>=-1e-6)&(tri[:,:,2].max(axis=1)<.160001)
    floor=np.zeros(len(tri),dtype=bool);tolerance=court.buffer(1e-5,join_style=2)
    for idx in np.flatnonzero(candidates):
        if all(tolerance.covers(Point(v)) for v in xy[idx]):floor[idx]=True
    floor_shape=shapely.union_all(shapely.polygons(xy[floor]));checks={'floor_exactly12_triangles':int(floor.sum())==12,'floor_plan_matches_author_court':floor_shape.symmetric_difference(court).area<.001}
    low=(tri[:,:,2].min(axis=1)<=2)&(tri[:,:,2].max(axis=1)>=0)&~floor;pieces=[]
    for t in tri[low]:
        poly=clip_height(list(t.copy()),0,True)
        if len(poly)<3:continue
        poly=clip_height(poly,2,False)
        if len(poly)<3:continue
        planar=Polygon([v[:2] for v in poly])
        if planar.area>1e-10:pieces.append(planar)
    ground=shapely.union_all(pieces)
    return full,ground,{'asset':asset,'triangles':len(tri),'floor_excluded_triangles':int(floor.sum()),'floor_plan_symmetric_difference_m2':floor_shape.symmetric_difference(court).area,'all_height_projection_m2':full.area,'structural_low_projection_m2':ground.area,'checks':checks}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',type=Path,required=True);ap.add_argument('--mapping',type=Path,required=True);ap.add_argument('--raw',type=Path,required=True);ap.add_argument('--lod-decoded',type=Path,required=True);ap.add_argument('--lod-original',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    p=a.repo/'projects/shanghai';cp=p/'source/precise/hongkou-general-post-office/footprint-contract.json';contract=json.loads(cp.read_text());catalog_path=p/'data/candidate-city-integrations.json';catalog=json.loads(catalog_path.read_text());target=next(r for r in catalog['models'] if r['id']=='hongkou-general-post-office')
    anchor=contract['anchor'];k=6371008.8*math.cos(math.radians(anchor['lat']));log0=math.log(math.tan(math.pi/4+math.radians(anchor['lat'])/2))
    def local(x,y,z=None):return math.radians(x-anchor['lng'])*k,(math.log(math.tan(math.pi/4+math.radians(y)/2))-log0)*k
    collision=transform(local,shape(target['collision_geometry']));court=shape(contract['courtyard_canopy_plan_local_enu'])
    context_path=a.mapping/'context-features.json';profile_path=a.mapping/'source-profiles.geojson';contexts=json.loads(context_path.read_text());native=json.loads(profile_path.read_text())['features']
    protected={str(r['localId']):shape(r['geometry_local_enu']) for r in contexts if r['localId']!=1959}
    protected.update({r['properties']['name']:shape(r['geometry']) for r in native if r['properties']['name'] in ['near_3148','near_814','near_1780']})
    rows={};grounds=[]
    for name,path,original in [('raw',a.raw,a.raw),('lod',a.lod_decoded,a.lod_original)]:
        full,ground,row=projections(path,court);grounds.append(ground)
        row['production_asset']={'file':original.name,'bytes':original.stat().st_size,'sha256':hashlib.sha256(original.read_bytes()).hexdigest()}
        neighbors=[{'id':key,'model_intersection_m2':poly.intersection(full).area,'structure_intersection_m2':poly.intersection(ground).area,'collision_intersection_m2':poly.intersection(collision).area,'model_distance_m':poly.distance(full)} for key,poly in protected.items()]
        row['checks']['17_sources_plus3_actual_near_profiles_preserved']=len(neighbors)==20 and all(r['model_intersection_m2']<1e-8 and r['structure_intersection_m2']<1e-8 and r['collision_intersection_m2']<1e-8 for r in neighbors)
        row['checks']['collision_covers_actual_structural_low']=ground.difference(collision).area<1e-7
        row['uncovered_structure_m2']=ground.difference(collision).area;row['neighbors']=neighbors;row['passed']=all(row['checks'].values());rows[name]=row
        print(json.dumps({'variant':name,'checks':row['checks'],'structure_m2':ground.area}),flush=True)
    combined=shapely.union_all(grounds);ring_counts=[len(collision.exterior.coords),*[len(r.coords) for r in collision.interiors]] if collision.geom_type=='Polygon' else []
    frame=contract['facade_uv_frame'];o=np.array(frame['origin_enu_m']);u=np.array(frame['u_axis_enu']);v=np.array(frame['v_axis_enu']);probes=[]
    for name,x,y,expected in [('south wing',35,10,True),('north wing',35,53,True),('east wing',84,32,True),('tower base',85,8,True),('court center',32,32,False),('court west',6,32,False),('south street',35,-3,False)]:
        xy=o+u*x+v*y;actual=collision.covers(Point(xy));probes.append({'name':name,'uv_m':[x,y],'actual_contains':actual,'expected_contains':expected,'passed':actual==expected})
    checks={'all_variant_checks':all(r['passed'] for r in rows.values()),'valid_single_collision_polygon':collision.is_valid and collision.geom_type=='Polygon','collision_existing_vertex_budget':bool(ring_counts) and len(ring_counts)<=32 and max(ring_counts)<=256 and sum(ring_counts)<=4096,'collision_no_excessive_padding':collision.difference(combined.buffer(.35001,join_style=2)).area<1e-7,'ground_probe_semantics':all(r['passed'] for r in probes)}
    result={'schema':'postal-independent-placement-v1','model_id':'hongkou-general-post-office','passed':all(checks.values()),'checks':checks,'variants':rows,'collision_ring_counts':ring_counts,'collision_area_m2':collision.area,'collision_padding_m2':collision.difference(combined).area,'courtyard_free_area_m2':court.difference(collision).area,'probes':probes,'bindings':[{'file':str(path),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()} for path in [Path(__file__),HELPER,cp,catalog_path,context_path,profile_path]],'scope':'Independent raw and decoded production LOD projections and catalog collision; full/web equivalence is checked separately by exact oriented FLOAT32 per-material triangle digests. Ground-floor semantic exclusion is not acceptance of an indoor walking route.'}
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'passed':result['passed'],'checks':checks}));raise SystemExit(0 if result['passed'] else 1)
if __name__=='__main__':main()
