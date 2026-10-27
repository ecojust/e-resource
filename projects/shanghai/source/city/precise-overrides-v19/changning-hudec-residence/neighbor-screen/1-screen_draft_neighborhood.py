#!/usr/bin/env python3
"""Read actual uncompressed GLB triangles and frozen source neighborhoods.

This is a draft footprint-overlap screen only. No navigation, material, visual
appearance, accurate collision, structural or final model acceptance is made.
"""
import argparse, gzip, hashlib, json, math, struct, sys
from pathlib import Path
import numpy as np
from shapely.geometry import LineString, Point, Polygon, mapping, shape
from shapely.ops import transform, unary_union

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
BASE=HERE.parent
MAIN=Path('/workspace/shanghai_project')
ID='xuhui-wukang-mansion'; MACRO='14-13718-6695'; LOCAL=1235
KEEP={593,1151,1545,1776,1834,3220,3299,4033,4146}
R=6378137.0
EDGE_EPSILON=1e-5
AREA_EPSILON=1e-8

def need(value,message):
    if not value:raise ValueError(message)

def read(path):
    path=Path(path);data=path.read_bytes();return json.loads(gzip.decompress(data) if path.suffix=='.gz' else data)

def descriptor(path):
    data=Path(path).read_bytes();return {'path':str(Path(path).resolve()),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}

def save(path,value):
    with Path(path).open('x') as handle:json.dump(value,handle,ensure_ascii=False,indent=2,allow_nan=False);handle.write('\n')

def raw_triangles(path):
    blob=Path(path).read_bytes();need(struct.unpack_from('<4sII',blob)==(b'glTF',2,len(blob)),'Invalid raw GLB header')
    offset=12;chunks={}
    while offset<len(blob):
        length,kind=struct.unpack_from('<II',blob,offset);offset+=8
        need(kind not in chunks and length%4==0 and offset+length<=len(blob),'Invalid raw GLB chunk')
        chunks[kind]=memoryview(blob)[offset:offset+length];offset+=length
    need(set(chunks)=={0x4E4F534A,0x004E4942},'Expected JSON and BIN chunks')
    doc=json.loads(bytes(chunks[0x4E4F534A]));binary=chunks[0x004E4942]
    need(len(doc['buffers'])==1 and 'uri' not in doc['buffers'][0],'Expected embedded raw geometry')
    need(not doc.get('skins') and not doc.get('animations'),'Skins or animations require a separate screen')
    dtype={5121:'<u1',5123:'<u2',5125:'<u4',5126:'<f4'};size={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}
    def accessor(index):
        a=doc['accessors'][index];need(not a.get('sparse') and not a.get('normalized') and a['count']>0,'Unsupported raw accessor')
        v=doc['bufferViews'][a['bufferView']];need(v['buffer']==0 and not v.get('extensions'),'Compressed or external view is not a raw geometry input')
        dt=np.dtype(dtype[a['componentType']]);width=size[a['type']];stride=v.get('byteStride',width*dt.itemsize)
        start=v.get('byteOffset',0)+a.get('byteOffset',0);end=start+(a['count']-1)*stride+width*dt.itemsize
        need(stride>=width*dt.itemsize and end<=v.get('byteOffset',0)+v['byteLength']<=len(binary),'Accessor outside its bufferView')
        return np.ndarray((a['count'],width),dtype=dt,buffer=binary,offset=start,strides=(stride,dt.itemsize))
    def matrix(node):
        need(not node.get('extensions'),'Raw node extensions/instancing require explicit decode support')
        if 'matrix' in node:
            need(not any(k in node for k in ('translation','rotation','scale')),'Ambiguous node transform')
            result=np.array(node['matrix'],dtype=float).reshape(4,4).T
        else:
            x,y,z,w=node.get('rotation',[0,0,0,1]);need(abs(x*x+y*y+z*z+w*w-1)<1e-5,'Nonunit quaternion')
            rot=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                          [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
                          [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
            result=np.eye(4);result[:3,:3]=rot@np.diag(node.get('scale',[1,1,1]));result[:3,3]=node.get('translation',[0,0,0])
        need(np.isfinite(result).all() and np.allclose(result[3],[0,0,0,1]),'Invalid node transform')
        return result
    visited=set();parts=[]
    def visit(index,parent):
        need(index not in visited,'Repeated or cyclic active node');visited.add(index)
        node=doc['nodes'][index];world=parent@matrix(node)
        if 'mesh' in node:
            mesh=doc['meshes'][node['mesh']]
            for pi,primitive in enumerate(mesh['primitives']):
                need(primitive.get('mode',4)==4 and not primitive.get('targets'),'Only static triangle primitives are screened')
                positions=accessor(primitive['attributes']['POSITION']);need(positions.shape[1]==3 and np.isfinite(positions).all(),'Invalid position buffer')
                indices=accessor(primitive['indices']).ravel() if 'indices' in primitive else np.arange(len(positions))
                need(len(indices)%3==0 and indices.min()>=0 and indices.max()<len(positions),'Invalid triangle indices')
                points=np.asarray(positions,dtype=float)@world[:3,:3].T+world[:3,3]
                enu=points[:,[0,2,1]]*[1,-1,1]
                material=doc.get('materials',[])[primitive['material']].get('name') if 'material' in primitive else None
                parts.append({'node':node.get('name',str(index)),'mesh':mesh.get('name',str(node['mesh'])),'primitive':pi,'material':material,
                              'triangles':enu[indices].reshape(-1,3,3)})
        for child in node.get('children',[]):visit(child,world)
    for index in doc['scenes'][doc.get('scene',0)]['nodes']:visit(index,np.eye(4))
    need(parts,'No active triangles')
    return parts,doc

def projected_parts(parts):
    all_geometry=[];counts={'positive_area_triangles':0,'line_degenerate_triangles':0,'point_degenerate_triangles':0};out=[]
    for part in parts:
        geometry=[]
        for tri in part['triangles']:
            xy=tri[:,:2];poly=Polygon(xy)
            if poly.area>0:
                geometry.append(poly);counts['positive_area_triangles']+=1
            elif np.ptp(xy,axis=0).max()>0:
                geometry.append(LineString(xy));counts['line_degenerate_triangles']+=1
            else:
                geometry.append(Point(xy[0]));counts['point_degenerate_triangles']+=1
        projection=unary_union(geometry);need(projection.is_valid,'Invalid actual triangle projection union')
        all_geometry.append(projection);out.append({**{k:v for k,v in part.items() if k!='triangles'},'triangle_count':len(part['triangles']),'geometry':projection})
    return unary_union(all_geometry),out,counts

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--metadata',type=Path,required=True);parser.add_argument('--expected-raw-sha256',required=True)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    output=args.output.resolve();need(output.parent==BASE and not output.exists(),'Use a fresh integration output child')
    frozen=BASE/'freeze-v1'/ID/'geometry-input.json';source=read(frozen);identity_path=BASE/'owner-study-v1.json';identity=read(identity_path)
    lon0,lat0=source['anchor'];cos0=math.cos(math.radians(lat0));y0=math.asinh(math.tan(math.radians(lat0)))
    def local(lon,lat,z=None):return R*math.radians(lon-lon0)*cos0,R*(math.asinh(math.tan(math.radians(lat)))-y0)*cos0
    target=transform(local,shape(source['geometry']));need(target.is_valid,'Invalid source target')
    need(target.hausdorff_distance(shape(source['model_geometry_local_east_north_m']))<1e-8,'Frozen coordinate contract differs')
    table_inputs=[r for r in identity['inputs'] if r['file'].endswith('/feature-table.json.gz')]
    need(len(table_inputs)==9 and len({r['file'] for r in table_inputs})==9,'Expected nine unique frozen effective tables')
    contexts=[];source_files=[];scanned=0;owners=0;outside_invalid=[]
    for row in table_inputs:
        path=MAIN/row['file'];d=descriptor(path);need(all(d[k]==row[k] for k in ('bytes','sha256')),'Source table differs from owner study')
        source_files.append(d);macro=path.parent.name
        for f in read(path)['features']:
            scanned+=1
            if f['key']==source['source']['key']:
                owners+=1;need(macro==MACRO and f['localId']==LOCAL and f['geometry']==source['geometry'],'Unexpected duplicate source owner');continue
            geom=transform(local,shape(f['geometry']))
            distance=target.distance(geom)
            if distance>180:
                if not geom.is_valid:outside_invalid.append({'macro':macro,'local_id':f['localId'],'distance_m':distance})
                continue
            need(geom.is_valid,'Invalid source neighbor geometry within requested 180m context')
            contexts.append({'key':f['key'],'macro':macro,'local_id':f['localId'],'name':f.get('properties',{}).get('@name'),
              'geometry_geographic':f['geometry'],'geometry_local_east_north_m':mapping(geom),
              'source_base_estimate_m':f['base'],'source_height_estimate_m':f['height'],'source_height_quality':f['height_quality'],
              'source_height_not_independently_surveyed':True,'distance_to_source_owner_m':distance,'retained':True,
              'same_near_neighbor':macro==MACRO and f['localId'] in KEEP,'touching_separate_local320':macro==MACRO and f['localId']==320})
    need(owners==1,'Expected one source owner in bounded nine-table scan')
    contexts.sort(key=lambda r:(r['distance_to_source_owner_m'],r['macro'],r['local_id']))
    need(len({(r['macro'],r['local_id']) for r in contexts})==len(contexts),'Duplicate source local identity')
    need(KEEP<={r['local_id'] for r in contexts if r['macro']==MACRO},'Same-near neighbor outside collected context')
    context={'schema':'wukang-v18-unchanged-effective-neighbors','anchor':source['anchor'],'target_key':source['source']['key'],
             'scope':'All effective source features within 180m of the original target polygon, from nine frozen effective tables. Mapped polygons and source heights are not surveyed architectural measurements.',
             'coordinate_contract':source['coordinate_contract'],'features':contexts,'source_files':source_files,
             'source_identity':descriptor(identity_path),'source_geometry':descriptor(frozen),'effective_features_scanned':scanned,
             'unique_target_occurrences':owners,'projected_invalid_shapes_outside_requested_neighborhood':outside_invalid,
             'model_projection_overlap_review_pending':True}
    context_path=BASE/'source-neighborhood-v1.json'
    if context_path.exists():need(read(context_path)==json.loads(json.dumps(context)),'Existing frozen neighborhood differs')
    else:save(context_path,context)
    metadata=read(args.metadata);need(metadata['id']==ID and metadata['anchor']==source['anchor'],'Wrong draft model identity/anchor')
    need(metadata['rotation_y']==0 and metadata['ground_base_m']==0,'Draft model transform differs')
    need(metadata['source_input_sha256']==descriptor(frozen)['sha256'],'Draft source contract SHA differs')
    raw=metadata['raw'];path=args.metadata.parent/raw['file'];raw_descriptor=descriptor(path)
    need(raw_descriptor['sha256']==args.expected_raw_sha256 and all(raw_descriptor[k]==raw[k] for k in ('bytes','sha256')),'Draft raw model bytes differ')
    parts,doc=raw_triangles(path);triangles=np.concatenate([r['triangles'] for r in parts]);points=triangles.reshape(-1,3)
    need(len(triangles)==raw['triangles'],'Actual draft triangle count differs')
    projection,part_projections,counts=projected_parts(parts);hull=projection.convex_hull
    checks=[]
    for row in contexts:
        geom=shape(row['geometry_local_east_north_m']);deep=geom.buffer(-EDGE_EPSILON)
        raw_area=projection.intersection(geom).area;deep_area=projection.intersection(deep).area
        crossing=[{k:p[k] for k in ('node','mesh','primitive','material','triangle_count')}|{'deep_overlap_area_m2':p['geometry'].intersection(deep).area}
                  for p in part_projections if p['geometry'].intersection(deep).area>AREA_EPSILON]
        checks.append({k:row[k] for k in ('key','macro','local_id','name','same_near_neighbor','touching_separate_local320')}|
            {'distance_to_actual_projection_m':geom.distance(projection),'raw_overlap_area_m2':raw_area,
             'overlap_area_inside_neighbor_minus_boundary_epsilon_m2':deep_area,
             'no_significant_interior_overlap':deep_area<=AREA_EPSILON,
             'conservative_convex_hull_overlap_area_m2':hull.intersection(geom).area,'interior_crossing_parts':crossing})
    checks.sort(key=lambda r:(-r['overlap_area_inside_neighbor_minus_boundary_epsilon_m2'],r['distance_to_actual_projection_m']))
    contact=next(r for r in checks if r['touching_separate_local320'])
    output.mkdir()
    report={'schema':'wukang-v18-actual-draft-triangle-neighbor-screen','draft_only':True,
       'passed_draft_neighbor_screen':all(r['no_significant_interior_overlap'] for r in checks),
       'final_model_accepted':False,'navigation_or_camera_tested':False,'browser_passed':False,'main_written':False,
       'raw_asset':raw_descriptor,'metadata':descriptor(args.metadata),'geometry_input':descriptor(frozen),
       'source_neighborhood':descriptor(context_path),'source_files':source_files,'tool':descriptor(Path(__file__)),
       'actual_triangle_count':len(triangles),'actual_primitive_count':len(parts),'actual_referenced_vertex_instances':len(points),
       'author_declared_semantic_part_count':raw.get('parts'),'part_count_note':'Author semantic parts are batched into GLB material primitives; they are not the same count. Actual indexed triangle count is checked independently.',
       'bounds_enu_m':{'min':points.min(axis=0).tolist(),'max':points.max(axis=0).tolist()},
       'projection':{'method':'Union of every actual transformed triangle projected from glTF [east,up,-north] to east/north; retain zero-area line and point projections.',
          'geometry_type':projection.geom_type,'area_m2':projection.area,'convex_hull_area_m2':hull.area,
          'original_source_area_m2':target.area,'outside_original_owner_area_m2':projection.difference(target).area,
          'outside_original_owner_buffered_epsilon_area_m2':projection.difference(target.buffer(EDGE_EPSILON)).area,
          'triangle_counts':counts},
       'numeric_policy':{'boundary_epsilon_m':EDGE_EPSILON,'residual_area_threshold_m2':AREA_EPSILON,
          'reason':'Raw Float32 vertices can differ from frozen double-precision map coordinates by a few micrometres. Report unadjusted overlap, then test neighbor interior after removing only a 10 micrometre boundary strip. This is numerical handling, not a survey allowance or height-based waiver.'},
       'source_neighbor_count':len(checks),'same_near_neighbors_preserved_count':sum(r['same_near_neighbor'] for r in checks),
       'touching_local320':contact,'neighbor_checks':checks,
       'limitations':['Draft massing only; detailed balconies/cornices/roof changes require a new actual-mesh screen.',
          'Mapped source footprint proximity is not real-world survey accuracy or independent legal parcel ownership.',
          'No navigation point, camera pose, actual browser rendering, material verification or complete collision/support check was performed.',
          'Zero planar distance at a retained source boundary is allowed only when no significant interior overlap remains; every raw overlap value is disclosed.',
          'A convex hull can fill legitimate recesses; its overlaps are diagnostic and cannot alone establish actual model intrusion.']}
    save(output/'model-neighbor-screen.json',report)
    total=descriptor(context_path)['bytes']+sum(p.stat().st_size for p in output.rglob('*') if p.is_file())+Path(__file__).stat().st_size
    need(total<2_000_000,'Independent context/screen exceeds 2MB additional budget')
    print(json.dumps({'report':str(output/'model-neighbor-screen.json'),'passed_draft_neighbor_screen':report['passed_draft_neighbor_screen'],
       'neighbors':len(checks),'triangles':len(triangles),'local320':contact,'new_bytes':total},ensure_ascii=False))

if __name__=='__main__':main()
