#!/usr/bin/env python3
"""Independent actual-GLB neighbor screen, with explicit source-height clipping.

No navigation, camera, image, or complete model acceptance is performed.
Source heights and polygons are mapped estimates, not an as-built survey.
"""
import hashlib, importlib.util, json, sys, time
from pathlib import Path
import numpy as np
import shapely
from shapely.geometry import Polygon, LineString, Point, shape
from shapely.strtree import STRtree

sys.dont_write_bytecode=True
OUT=Path(__file__).resolve().parent
BASE=OUT.parent
MAIN=Path('/workspace/shanghai_project')
MODEL=BASE.parents[1]/'model/hudec-residence-detailed-v1/final-review'
RAW_SHA='0ccd906149afa7d0cae8af24879e46be39f308162002ccdc208782b86a026828'
CONTEXT_SHA='0e88ea824d1f573f2fb9db5dcfddb42b64b049dfcae36882d3c1b12bb2c25008'
FROZEN_SHA='3304b88742474b2c796b8f8246ae4d5d4c1de30850d08b6aee2a9977fc49a22b'
KEEP={873,2697,2774,3819}
EDGE_EPSILON=1e-5
AREA_EPSILON=1e-8

def need(ok,message):
    if not ok:raise ValueError(message)

def read(path):return json.loads(Path(path).read_text())

def desc(path):
    path=Path(path).resolve();data=path.read_bytes()
    return {'path':str(path),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}

def save(path,value):
    with Path(path).open('x') as handle:
        json.dump(value,handle,ensure_ascii=False,indent=2,allow_nan=False);handle.write('\n')

def geometry(vertices):
    xy=np.asarray(vertices)[:,:2]
    p=Polygon(xy) if len(xy)>=3 else None
    if p is not None and p.area>0:return p
    if len(xy)>1 and np.ptp(xy,axis=0).max()>0:return LineString(xy)
    return Point(xy[0])

def zclip(vertices,z,keep_above):
    """Exact linear edge interpolation against a horizontal plane."""
    vertices=list(vertices);result=[]
    if not vertices:return result
    a=vertices[-1];a_in=a[2]>=z if keep_above else a[2]<=z
    for b in vertices:
        b_in=b[2]>=z if keep_above else b[2]<=z
        if b_in!=a_in:
            t=(z-a[2])/(b[2]-a[2]);q=a+t*(b-a);q[2]=z;result.append(q)
        if b_in:result.append(b)
        a=b;a_in=b_in
    return result

def slab_geometry(triangle,base,roof):
    clipped=zclip(zclip(triangle,base,True),roof,False)
    return geometry(clipped) if clipped else None

def intersection_summary(items):
    if not items:return {'area_m2':0.0,'length_m':0.0,'geometry_type':'GeometryCollection','empty':True}
    u=shapely.union_all(items)
    return {'area_m2':float(u.area),'length_m':float(u.length),'geometry_type':u.geom_type,'empty':u.is_empty}

def height_range(triangle,intersection):
    """Height extrema on an actual triangle above its clipped XY intersection.

    Nonvertical triangles have affine z(x,y). For a vertical triangle the
    projection is one dimensional; evaluate its edges at all intersection
    endpoints, plus original vertices inside the interval. No guessed roof.
    """
    coords=shapely.get_coordinates(intersection)
    if len(coords)==0:return None
    xy=triangle[:,:2];delta=xy[1:]-xy[0]
    det=np.linalg.det(delta)
    if det!=0:
        slope=np.linalg.solve(delta,triangle[1:,2]-triangle[0,2])
        heights=(coords-xy[0])@slope+triangle[0,2]
        if heights.min()<triangle[:,2].min()-1e-3 or heights.max()>triangle[:,2].max()+1e-3:
            return [float(triangle[:,2].min()),float(triangle[:,2].max())], 'conservative_actual_triangle_z_bounds_nearly_degenerate_projection'
        return [float(heights.min()),float(heights.max())], 'affine_height_over_actual_projected_intersection'
    axis=int(np.argmax(np.ptp(xy,axis=0)))
    if np.ptp(xy,axis=0)[axis]==0:return [float(triangle[:,2].min()),float(triangle[:,2].max())], 'point_projection_actual_triangle_z_bounds'
    lo,hi=coords[:,axis].min(),coords[:,axis].max();heights=[]
    for p in triangle:
        if lo-1e-9<=p[axis]<=hi+1e-9:heights.append(p[2])
    for a,b in zip(triangle,np.roll(triangle,-1,axis=0)):
        if a[axis]==b[axis]:continue
        for endpoint in (lo,hi):
            t=(endpoint-a[axis])/(b[axis]-a[axis])
            if -1e-9<=t<=1+1e-9:heights.append(a[2]+t*(b[2]-a[2]))
    need(heights,'Vertical triangle overlap has no height sample')
    return [float(min(heights)),float(max(heights))], 'vertical_triangle_edges_at_actual_intersection_endpoints'

def self_checks():
    square=Polygon([(0,0),(1,0),(1,1),(0,1)])
    upper=np.array([[.1,.1,3],[.9,.1,3],[.1,.9,3]],float)
    wall=np.array([[.2,.2,-1],[.8,.2,3],[.2,.2,3]],float)
    a=slab_geometry(upper,0,2);b=slab_geometry(wall,0,2)
    need(a is None,'High overhang must not be counted in lower source prism')
    need(b is not None and b.intersects(square) and b.length>0,'Vertical wall must be detected despite zero planar area')
    clipped=zclip(zclip(wall,0,True),2,False)
    need(min(v[2] for v in clipped)==0 and max(v[2] for v in clipped)==2,'Horizontal clipping failed')
    return {'above_roof_triangle_rejected_from_prism':True,'zero_area_vertical_wall_detected':True,'crossing_triangle_clipped_at_both_heights':True}

def main():
    started=time.time();need(not (OUT/'model-neighbor-screen.json').exists(),'Use a fresh result; no overwrite')
    context_path=BASE/'source-neighborhood-v1.json';frozen_path=BASE/'source-owner-input-v1/changning-hudec-residence/geometry-input.json'
    metadata_path=BASE/'screen-inputs-v2/raw-screen-metadata.json';raw_path=MODEL/'hudec-C-full.glb'
    decoder_path=Path('/workspace/shanghai_expansion/building-by-building-v18/integration/wukang-mansion/owner-tools-v1/screen_draft_neighborhood.py')
    inputs=[context_path,frozen_path,metadata_path,raw_path,decoder_path,Path(__file__)]
    before={str(p.resolve()):desc(p) for p in inputs}
    need(before[str(context_path)]['sha256']==CONTEXT_SHA,'Frozen 44-neighbor context changed')
    need(before[str(frozen_path)]['sha256']==FROZEN_SHA,'Frozen coordinate contract changed')
    need(before[str(raw_path)]['sha256']==RAW_SHA,'Wrong author-confirmed release raw model')
    context=read(context_path);frozen=read(frozen_path);metadata=read(metadata_path)
    need(len(context['features'])==44,'Expected frozen 44 neighbors')
    need(metadata['id']=='changning-hudec-residence' and metadata['anchor']==frozen['anchor']==context['anchor'],'Identity/anchor differs')
    need(metadata['rotation_y']==metadata['ground_base_m']==0,'Nonzero model transform')
    need(metadata['source_geometry_sha256']==FROZEN_SHA,'Model source contract differs')
    need(all(metadata['raw'][k]==before[str(raw_path)][k] for k in ('bytes','sha256')),'Metadata/raw byte binding differs')
    baseline=read(BASE/'freeze-v1/baseline.json');protected={}
    for row in baseline['files']+baseline['runtime_files']:
        p=MAIN/row['file'];d=desc(p)
        need(all(d[k]==row[k] for k in ('bytes','sha256')),'MAIN differs from frozen baseline: '+str(p))
        protected[str(p)]=d
    for row in context['source_files']:
        d=desc(row['path']);need(d==row,'Frozen source table changed');protected[d['path']]=d
    save(OUT/'input-preimages.json',{'inputs':list(before.values()),'protected_main_and_source':list(protected.values())})
    spec=importlib.util.spec_from_file_location('bound_raw_decoder',decoder_path);decoder=importlib.util.module_from_spec(spec);spec.loader.exec_module(decoder)
    parts,doc=decoder.raw_triangles(raw_path)
    triangles=np.concatenate([p['triangles'] for p in parts]);need(len(triangles)==metadata['raw']['triangles']==85101,'Actual triangle count differs')
    part_ids=np.concatenate([np.full(len(p['triangles']),i,dtype=np.int16) for i,p in enumerate(parts)])
    starts=np.cumsum([0]+[len(p['triangles']) for p in parts])
    points=triangles.reshape(-1,3);geoms=shapely.polygons(triangles[:,:,:2]);areas=shapely.area(geoms)
    zero=np.flatnonzero(areas==0)
    for i in zero:geoms[i]=geometry(triangles[i])
    need(bool(np.all(shapely.is_valid(geoms))),'Invalid projected triangle geometry')
    tree=STRtree(geoms);hull=shapely.MultiPoint(points[:,:2]).convex_hull
    print(json.dumps({'phase':'decoded_actual_triangles','triangles':len(triangles),'primitives':len(parts),'zero_area_projections':len(zero)}),flush=True)
    checks=[];crossing_evidence=[]
    for row in context['features']:
        geom=shape(row['geometry_local_east_north_m']);need(geom.is_valid,'Invalid frozen neighbor')
        deep=geom.buffer(-EDGE_EPSILON);ids=tree.query(geom,predicate='intersects')
        raw_intersections=[];deep_intersections=[];slab_intersections=[];slab_deep_intersections=[]
        low=float(row['source_base_estimate_m']);roof=low+float(row['source_height_estimate_m'])
        per_part={};height_ranges=[];prism_ids=[];deep_ids=[]
        for idx in ids:
            idx=int(idx);tri=triangles[idx];intersection=geoms[idx].intersection(geom)
            raw_intersections.append(intersection);height,height_method=height_range(tri,intersection);height_ranges.append(height)
            inter_deep=geoms[idx].intersection(deep)
            if not inter_deep.is_empty:deep_intersections.append(inter_deep);deep_ids.append(idx)
            clipped=slab_geometry(tri,low,roof)
            ci=clipped.intersection(geom) if clipped is not None else None
            cdi=clipped.intersection(deep) if clipped is not None else None
            if ci is not None and not ci.is_empty:slab_intersections.append(ci)
            if cdi is not None and not cdi.is_empty:slab_deep_intersections.append(cdi);prism_ids.append(idx)
            pidx=int(part_ids[idx]);p=parts[pidx];key=pidx
            if key not in per_part:
                per_part[key]={k:p[k] for k in ('node','mesh','primitive','material')}|{'overlap_triangle_count':0,'deep_overlap_triangle_count':0,'estimated_height_prism_interior_triangle_count':0,'overlap_height_range_m':[1e100,-1e100]}
            group=per_part[key];group['overlap_triangle_count']+=1
            group['deep_overlap_triangle_count']+=int(not inter_deep.is_empty)
            group['estimated_height_prism_interior_triangle_count']+=int(cdi is not None and not cdi.is_empty)
            group['overlap_height_range_m'][0]=min(group['overlap_height_range_m'][0],height[0]);group['overlap_height_range_m'][1]=max(group['overlap_height_range_m'][1],height[1])
            crossing_evidence.append({'neighbor_macro':row['macro'],'neighbor_local_id':row['local_id'],'actual_global_triangle_index':idx,'primitive':p['primitive'],'material':p['material'],'primitive_triangle_index':idx-int(starts[pidx]),'triangle_enu_m':tri.tolist(),'overlap_height_range_m':height,'overlap_height_range_method':height_method,'raw_overlap_area_m2':float(intersection.area),'deep_overlap_area_m2':float(inter_deep.area),'deep_overlap_length_m':float(inter_deep.length),'intersects_estimated_height_prism_interior':bool(cdi is not None and not cdi.is_empty)})
        raw_sum=intersection_summary(raw_intersections);deep_sum=intersection_summary(deep_intersections);slab_sum=intersection_summary(slab_intersections);slab_deep_sum=intersection_summary(slab_deep_intersections)
        check={k:row[k] for k in ('key','macro','local_id','name','same_near_neighbor','source_base_estimate_m','source_height_estimate_m','source_height_quality','source_height_not_independently_surveyed')}
        overlap_height=[min(r[0] for r in height_ranges),max(r[1] for r in height_ranges)] if height_ranges else None
        check.update({'source_roof_estimate_m':roof,'actual_surface_projection_distance_m':float(geoms[int(tree.nearest(geom))].distance(geom)),'projected_intersecting_triangle_count':len(ids),'raw_projection_overlap':raw_sum,'deep_projection_overlap':deep_sum,'overlap_height_range_m':overlap_height,'minimum_overlap_clearance_above_estimated_roof_m':overlap_height[0]-roof if overlap_height else None,'estimated_height_prism_overlap':slab_sum,'estimated_height_prism_deep_overlap':slab_deep_sum,'estimated_height_prism_deep_triangle_count':len(prism_ids),'no_actual_surface_in_estimated_neighbor_interior':len(prism_ids)==0,'convex_hull_overlap_area_m2_diagnostic_only':float(hull.intersection(geom).area),'intersecting_material_groups':list(per_part.values())})
        checks.append(check)
    keep=[r for r in checks if r['same_near_neighbor']]
    need({r['local_id'] for r in keep}==KEEP and len(keep)==4,'Same-near preserved identity differs')
    after={p:desc(p) for p in before};protected_after={p:desc(p) for p in protected}
    need(before==after and protected==protected_after,'Input or MAIN changed during read-only screen')
    save(OUT/'intersecting-triangles.json',{'method':'Every actual triangle whose projected geometry intersects a frozen neighbor; includes zero-area vertical faces. Indices reference the bound raw GLB active scene traversal.','triangles':crossing_evidence})
    checks.sort(key=lambda r:(-r['deep_projection_overlap']['area_m2'],r['actual_surface_projection_distance_m']))
    report={'schema':'hudec-v19-release-raw-actual-triangle-height-aware-neighbor-screen','created_epoch':time.time(),'scope':'Independent actual author-confirmed release raw geometry versus all frozen 44 source neighbors. Source footprint and source roof heights are estimates.','passed_source_estimated_height_prism_screen':all(r['no_actual_surface_in_estimated_neighbor_interior'] for r in checks),'any_planar_overlap':any(r['projected_intersecting_triangle_count'] for r in checks),'actual_model_identity':metadata['id'],'raw_asset':before[str(raw_path)],'metadata':before[str(metadata_path)],'geometry_input':before[str(frozen_path)],'source_neighborhood':before[str(context_path)],'tools':[before[str(Path(__file__).resolve())],before[str(decoder_path)]],'source_files':context['source_files'],'actual_triangle_count':len(triangles),'actual_primitive_count':len(parts),'author_declared_semantic_part_count':metadata['raw'].get('parts'),'bounds_enu_m':{'min':points.min(axis=0).tolist(),'max':points.max(axis=0).tolist()},'projection_method':'Decode indexed static triangles and active node transforms; map glTF [east,up,-north] to source [east,north,up]. An STRtree queries every actual polygon/line/point projection. Union only the actual clipped intersections per neighbor. A convex hull is diagnostic only.','height_annotation_note':'Nearly degenerate projected triangles whose affine height interpolation is unstable use conservative full actual triangle z bounds, explicitly flagged per triangle. Actual height-prism intersection uses independent 3D clipping and does not depend on this annotation.','conservative_height_annotation_count':sum(r['overlap_height_range_method'].startswith('conservative_') for r in crossing_evidence),'height_method':'Clip every actual intersecting 3D triangle to each source [base,base+height] slab by horizontal-plane edge interpolation, then intersect projected clipped surfaces with original and 10-micrometre-inset neighbor polygons. Count zero-area vertical face intersections too; never waive a wall merely because its planar overlap area is zero.','numeric_policy':{'neighbor_boundary_epsilon_m':EDGE_EPSILON,'area_reporting_threshold_m2':AREA_EPSILON,'acceptance_rule':'No actual triangle projection clipped to the estimated source height slab may intersect the polygon after the 10-micrometre boundary inset; even line/point intersections are retained. No height uncertainty allowance is applied. Raw overlaps are always disclosed.'},'source_neighbor_count':len(checks),'same_near_neighbors_preserved_count':len(keep),'all_same_near_actual_projection_clear':all(r['projected_intersecting_triangle_count']==0 for r in keep),'neighbor_checks':checks,'intersecting_triangles':desc(OUT/'intersecting-triangles.json'),'numeric_self_checks':self_checks(),'numeric_self_checks_reused_unchanged_from_v18':True,'input_and_main_preservation':{'all_exact':True,'protected_main_and_source_paths':len(protected),'input_preimages':desc(OUT/'input-preimages.json')},'elapsed_seconds':time.time()-started,'final_model_accepted':False,'source_owner_polygon_is_architectural_wall':False,'navigation_or_camera_tested':False,'browser_passed':False,'main_written':False,'limitations':['This is a mapped-source estimated-height prism screen, not a survey of adjacent building roofs or legally surveyed parcel boundaries.','An overhang above an estimated neighbor roof is explicitly reported and requires human interpretation; the height source does not establish real-world separation.','No navigation, camera, source-ground support, runtime collision, rendering, material, interior, or complete model acceptance is performed.','The screen checks actual triangle surfaces and projections; it is not a watertight-solid collision or structural analysis.']}
    save(OUT/'model-neighbor-screen.json',report)
    print(json.dumps({'report':str(OUT/'model-neighbor-screen.json'),'passed_source_estimated_height_prism_screen':report['passed_source_estimated_height_prism_screen'],'actual_triangles':len(triangles),'source_neighbors':len(checks),'intersecting_triangles':len(crossing_evidence),'elapsed_seconds':report['elapsed_seconds']},ensure_ascii=False),flush=True)

if __name__=='__main__':main()
