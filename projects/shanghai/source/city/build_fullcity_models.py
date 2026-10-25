"""Resumable real-footprint Shanghai full-city GLB tile exporter.

Reads atomically finalized, globally de-duplicated GeoJSON(.gz) owner tiles.
Writes tiles/*.glb and ids/*.json before atomically publishing records/*.json.
A record is the ready signal for uploaders. Manifest is a recoverable aggregate.

Dependencies: numpy, mapbox-earcut; gltfpack for default meshopt compression.
--no-compress emits ordinary uncompressed GLBs for editors without meshopt.
"""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from collections import Counter, defaultdict
import argparse, datetime, gzip, hashlib, json, math, os, shutil, struct, subprocess, sys, tempfile, time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_district_models import Mesh, cleaned_ring, building_height, write_glb

VERSION = 'shanghai-fullcity-v2.0'
_SAMPLER = None
_RESIDUALS = None
LIMIT = 100_000_000
HEIGHT_KEYS = ['source_height', 'floor_estimate', 'cmab_estimate_matched_rooftop', 'cnbh_estimate_10m', 'raster_estimate_2018', 'fallback_12m']
HEIGHT_NOTICE = ('Source height > num_floors * 3.2m > CMAB predicted rooftop height with strict footprint overlap > '
                 'CNBH2020 10m footprint pixel median > GHSL2018 regional 3-arcsecond cell mean > explicit 12m fallback. '
                 'CMAB, CNBH, GHSL and floor-derived values are estimates, never surveyed individual heights.')
DISTRICTS = {'310101':'黄浦区','310104':'徐汇区','310105':'长宁区','310106':'静安区','310107':'普陀区','310109':'虹口区','310110':'杨浦区','310112':'闵行区','310113':'宝山区','310114':'嘉定区','310115':'浦东新区','310116':'金山区','310117':'松江区','310118':'青浦区','310120':'奉贤区','310151':'崇明区'}


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def atomic_json(path, value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name('.'+path.name+'.tmp')
    temporary.write_text(json.dumps(value,ensure_ascii=False,separators=(',',':'))+'\n')
    os.replace(temporary,path)


def tile_bounds(z,x,y):
    n=2**z
    def lat(v):return math.degrees(math.atan(math.sinh(math.pi*(1-2*v/n))))
    return [x/n*360-180,lat(y+1),(x+1)/n*360-180,lat(y)]


def coordinates(geometry):
    if geometry['type']=='Polygon':
        for ring in geometry['coordinates']:
            yield from ring
    elif geometry['type']=='MultiPolygon':
        for polygon in geometry['coordinates']:
            for ring in polygon:yield from ring


def geometry_bounds(features):
    west=south=math.inf;east=north=-math.inf
    for feature in features:
        for lon,lat,*_ in coordinates(feature['geometry']):
            west=min(west,lon);south=min(south,lat);east=max(east,lon);north=max(north,lat)
    return [west,south,east,north]


def validate_glb(path):
    with open(path,'rb') as f:
        header=f.read(20)
        assert len(header)==20,path
        magic,version,length,json_size,kind=struct.unpack('<4sIIII',header)
        assert magic==b'glTF' and version==2 and length==path.stat().st_size,path
        assert kind==0x4E4F534A and length<LIMIT,path
        doc=json.loads(f.read(json_size))
    assert doc.get('meshes') and doc.get('accessors'),path
    triangles=0
    for mesh in doc['meshes']:
        for primitive in mesh['primitives']:
            assert primitive.get('mode',4)==4,path
            accessor=doc['accessors'][primitive['indices']]
            assert accessor['count']%3==0,path
            triangles+=accessor['count']//3
    for accessor in doc['accessors']:
        for key in ('min','max'):
            assert all(math.isfinite(v) for v in accessor.get(key,[])),path
    return doc,triangles


def read_raw(path):
    opener=gzip.open if path.suffix=='.gz' else open
    with opener(path,'rt',encoding='utf8') as f:return json.load(f)


def raw_tile(source, collection):
    meta=collection.get('metadata',{})
    t=meta.get('tile') or meta.get('source_tile')
    if isinstance(t,dict):t=[t['z'],t['x'],t['y']]
    if not t:
        p=source.name.replace('.geojson.gz','').replace('.geojson','')
        t=[int(source.parent.parent.name),int(source.parent.name),int(p)]
    z,x,y=map(int,t)
    bbox=meta.get('bbox') or collection.get('bbox') or tile_bounds(z,x,y)
    origin=meta.get('origin') or [(bbox[0]+bbox[2])/2,(bbox[1]+bbox[3])/2]
    return (z,x,y),list(origin),list(bbox),meta


def feature_center(feature):
    props=feature['properties']
    c=props.get('centroid')
    if isinstance(c,(list,tuple)) and len(c)>=2:return c[:2]
    bounds=geometry_bounds([feature]);return [(bounds[0]+bounds[2])/2,(bounds[1]+bounds[3])/2]


def split_features(features,bbox):
    # Median partition keeps complete buildings and makes pathological dense
    # chunks split even if the owner cell contains a crowded small neighborhood.
    xs=[feature_center(f) for f in features]
    sx=(bbox[2]-bbox[0])*math.cos(math.radians((bbox[1]+bbox[3])/2))
    axis=0 if sx >= bbox[3]-bbox[1] else 1
    pairs=sorted(zip(features,xs),key=lambda p:(p[1][axis],str(p[0]['properties'].get('id',''))))
    mid=len(pairs)//2
    cut=(pairs[mid-1][1][axis]+pairs[mid][1][axis])/2
    left,right=list(bbox),list(bbox)
    if axis==0:left[2]=cut;right[0]=cut
    else:left[3]=cut;right[1]=cut
    return [(list(x[0] for x in pairs[:mid]),left),(list(x[0] for x in pairs[mid:]),right)]


def create_meshes(features,origin,sampler,roof_overrides=None):
    meshes=[Mesh() for _ in range(4)]
    quality=Counter({k:0 for k in HEIGHT_KEYS});districts=defaultdict(lambda:Counter({k:0 for k in HEIGHT_KEYS}))
    ids={'building':set(),'building_part':set()};sources=Counter();invalid=[]
    represented=[];polygon_count=0;building_count=part_count=0
    for feature in features:
        props=feature['properties'];layer=props.get('source_layer','building')
        roof_override=(roof_overrides or {}).get(layer+':'+str(props.get('id','')))
        if props.get('id'):ids[layer].add(str(props['id']))
        if layer=='building_part' and props.get('building_id'):ids['building'].add(str(props['building_id']))
        if props.get('renderable') is False or props.get('_landmark_replaced'):
            if roof_override:raise ValueError(f'Qualified roof is not renderable: {props.get("id")}')
            continue
        geometry=feature['geometry']
        if geometry['type'] not in ('Polygon','MultiPolygon'):
            raise ValueError(f'Unexpected non-polygon renderable feature {props.get("id")}')
        district=str(props.get('district_id') or props.get('district') or '')
        if district not in DISTRICTS:raise ValueError(f'Unknown district_id {district} for {props.get("id")}')
        if props.get('_parent_residual'):
            # A parent's height/floor count can describe its tallest child,
            # not the unknown podium. Keep original properties for provenance
            # but estimate only the exact uncovered residual geometry.
            residual_props={k:v for k,v in props.items() if k not in ('height','num_floors')}
            base,height,kind=building_height(residual_props)
        else:base,height,kind=building_height(props)
        if kind=='fallback_12m' and sampler is not None:
            sampled=sampler.sample_geometry(geometry)
            if sampled and sampled['height_m']>base+.1:
                height=sampled['height_m'];kind=sampled['height_quality']
                if kind not in HEIGHT_KEYS:raise ValueError(f'Unknown height quality {kind}')
        roof=1 if height<18 else 2 if height<60 else 3
        polygons=geometry['coordinates'] if geometry['type']=='MultiPolygon' else [geometry['coordinates']]
        if roof_override:
            if geometry['type']!='Polygon' or len(polygons)!=1 or len(polygons[0])!=1 or props.get('_parent_residual'):
                raise ValueError(f'Qualified roof topology changed: {props.get("id")}')
            for name,actual in [('base',base),('height',height)]:
                if name in roof_override and abs(float(roof_override[name])-actual)>1e-6:
                    raise ValueError(f'Qualified roof {name} changed: {props.get("id")}')
        successful=0
        for polygon in polygons:
            rings=[cleaned_ring(r,origin,i==0) for i,r in enumerate(polygon)]
            if not rings or not rings[0]:
                if roof_override:raise ValueError(f'Qualified roof exterior is degenerate: {props.get("id")}')
                invalid.append({'id':props.get('id'),'reason':'degenerate exterior ring'});continue
            if roof_override:
                from roof_geometry import append_roof_shell
                stats=append_roof_shell(meshes[roof],meshes[0],rings,base=base,height=height,
                    roof_height=roof_override['roof_height'],roof_shape=roof_override['roof_shape'],
                    ridge_unit=roof_override.get('ridge_unit'),down_slope_unit=roof_override.get('down_slope_unit'))
                props['_applied_source_roof']={'key':layer+':'+str(props['id']),'id':str(props['id']),
                    'source_layer':layer,'district_id':district,'roof_shape':roof_override['roof_shape'],
                    'roof_height':roof_override['roof_height'],'base':base,'height':height,'geometry_stats':stats}
                successful+=1
            else:
                try:successful+=int(meshes[roof].polygon(rings,base,height,meshes[0]))
                except (ValueError,IndexError) as e:invalid.append({'id':props.get('id'),'reason':type(e).__name__})
        if not successful:
            # Source export already repairs polygon topology. Fail visibly so a
            # failed footprint is never silently omitted from a complete city.
            raise ValueError(f'No renderable polygons for {props.get("id")}: {invalid[-3:]}')
        represented.append(feature);polygon_count+=successful;quality[kind]+=1
        props['_applied_height_quality']=kind
        districts[district]['features']+=1;districts[district][kind]+=1
        if props.get('_parent_residual'):
            districts[district]['residual_parent_features']+=1
            districts[district]['residual_parent_area_m2']+=props.get('_parent_residual_area_m2',0)
        source_name=props.get('@geometry_source','unknown');sources[str(source_name)]+=1
        if layer=='building_part':
            part_count+=1;districts[district]['building_parts']+=1
            if props.get('id'):ids['building_part'].add(str(props['id']))
            if props.get('building_id'):ids['building'].add(str(props['building_id']))
        else:
            building_count+=1;districts[district]['building_footprints']+=1
            if props.get('id'):ids['building'].add(str(props['id']))
    return meshes,represented,dict(quality),{k:dict(v) for k,v in districts.items()},{k:sorted(v) for k,v in ids.items()},dict(sources),invalid,polygon_count,building_count,part_count


def publish_chunk(features,origin,bbox,tile,chunk_id,raw_hash,source_meta,options,depth=0):
    output=Path(options['output'])
    fixed=options.get('fixed_output_ids',{}).get('-'.join(map(str,tile)))
    if fixed and chunk_id not in fixed:
        if not any(identity.startswith(chunk_id+'-s') for identity in fixed):
            raise ValueError(f'Unknown retained partition: {chunk_id}')
        result=[]
        for n,(group,group_bbox) in enumerate(split_features(features,bbox)):
            if group:result.extend(publish_chunk(group,origin,group_bbox,tile,chunk_id+f'-s{n}',raw_hash,source_meta,options,depth+1))
        return result
    meshes,represented,quality,districts,ids,sources,invalid,polygon_count,buildings,parts=create_meshes(features,origin,_SAMPLER,options.get('roof_overrides'))
    if not represented:return []
    residual_features=[f for f in represented if f['properties'].get('_parent_residual')]
    residual_quality=Counter(f['properties']['_applied_height_quality'] for f in residual_features)
    extra={'district_name':'上海全域建筑分块','tile_id':chunk_id,'source_tile':list(tile),
           'origin_longitude':origin[0],'origin_latitude':origin[1],
           'geographic_bbox':bbox,'geometry_bbox':geometry_bounds(represented),
           'scope':'Complete source building footprints assigned uniquely to geographic owner tiles within the Shanghai 16-district boundary.',
           'source':'Overture Maps Foundation','source_release':source_meta.get('release','2026-10-21.0'),
           'represented_features':len(represented),'building_footprints':buildings,'building_parts':parts,
           'height_quality':quality,'height_fallback_m':12,'floor_estimate_m_per_floor':3.2,
           'height_sources':{'notice':HEIGHT_NOTICE,'priority':HEIGHT_KEYS,'estimated_quality_keys':HEIGHT_KEYS[1:],
                             'sampler_version':options['sampler_version'],'configuration_sha256':options['configuration_sha256']},
           'residual_parent_features':len(residual_features),
           'residual_parent_area_m2':sum(f['properties'].get('_parent_residual_area_m2',0) for f in residual_features),
           'residual_height_policy':'Parent height and floor count are retained as raw source attributes but not treated as podium height. Exact residual footprints use explicitly estimated CMAB/CNBH/GHSL/default heights; source min_height is retained.',
           'district_counts':districts,'geometry_sources':sources}
    roof_stats=[f['properties']['_applied_source_roof'] for f in represented if f['properties'].get('_applied_source_roof')]
    if roof_stats:
        extra['source_roof_enhancement']={'count':len(roof_stats),'keys':sorted(r['key'] for r in roof_stats),
            'roofs_by_shape':dict(Counter(r['roof_shape'] for r in roof_stats)),
            'roofs_by_district':dict(Counter(r['district_id'] for r in roof_stats)),
            'qualification_sha256':options['roof_qualification_sha256'],'geometry_version':options['roof_geometry_version'],
            'roof_stats':roof_stats}
    tempdir=output/'.work';tempdir.mkdir(parents=True,exist_ok=True)
    uncompressed=tempdir/(chunk_id+'.raw.glb')
    triangles=write_glb(uncompressed,meshes,extra)
    uncompressed_size=uncompressed.stat().st_size
    del meshes
    if not fixed and uncompressed_size>options['target_bytes'] and len(features)>1 and depth<16:
        uncompressed.unlink()
        result=[]
        for n,(group,group_bbox) in enumerate(split_features(features,bbox)):
            if group:result.extend(publish_chunk(group,origin,group_bbox,tile,chunk_id+f'-s{n}',raw_hash,source_meta,options,depth+1))
        return result
    if options['compress']:
        staged=tempdir/(chunk_id+'.compressed.glb')
        command=[options['gltfpack'],'-i',str(uncompressed),'-o',str(staged),'-cc','-vp','16','-vn','12','-km','-ke','-kn']
        result=subprocess.run(command,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        if result.returncode:raise RuntimeError(f'gltfpack failed for {chunk_id}: {result.stderr[-1500:]}')
        doc,checked_triangles=validate_glb(staged)
        if checked_triangles!=triangles:raise ValueError(f'Triangle count changed in {chunk_id}: {triangles} vs {checked_triangles}')
        # Meshopt is lossless on mesh topology; position quantization is local to
        # this metre-space tile and is much finer than source vector geometry.
        assert 'EXT_meshopt_compression' in doc.get('extensionsUsed',[]),chunk_id
        compression={'type':'EXT_meshopt_compression','position_bits':16,'normal_bits':12,'triangle_simplification':False,'original_size_bytes':uncompressed_size}
        uncompressed.unlink()
    else:
        staged=uncompressed;validate_glb(staged)
        compression={'type':'none','original_size_bytes':uncompressed_size}
    tile_path=output/'tiles'/(chunk_id+'.glb');tile_path.parent.mkdir(parents=True,exist_ok=True)
    os.replace(staged,tile_path)
    ids_path=output/'ids'/(chunk_id+'.json')
    atomic_json(ids_path,ids)
    record={'id':chunk_id,'tile':list(tile),'file':f'tiles/{chunk_id}.glb','feature_ids_file':f'ids/{chunk_id}.json',
            'origin_longitude':origin[0],'origin_latitude':origin[1],'geographic_bbox':bbox,
            'geometry_bbox':extra['geometry_bbox'],'building_count':len(represented),'building_footprints':buildings,'building_parts':parts,
            'polygon_count':polygon_count,'triangles':triangles,'size_bytes':tile_path.stat().st_size,
            'feature_ids_size_bytes':ids_path.stat().st_size,'sha256':sha256(tile_path),'feature_ids_sha256':sha256(ids_path),
            'height_quality':quality,'district_counts':districts,'geometry_sources':sources,
            'residual_parent_features':len(residual_features),'residual_parent_area_m2':extra['residual_parent_area_m2'],
            'residual_parent_height_quality':dict(residual_quality),
            'compression':compression,'source_sha256':raw_hash,'source_release':extra['source_release'],
            'invalid_polygon_count':len(invalid),'invalid_polygons':invalid,'build_version':VERSION,'completed_at':utc()}
    if roof_stats:record['source_roof_enhancement']=extra['source_roof_enhancement']
    atomic_json(output/'records'/(chunk_id+'.json'),record)
    return [record]


def export_source(source_name,options):
    global _SAMPLER,_RESIDUALS
    if _SAMPLER is None:
        from building_height_sampler import BuildingHeightSampler
        _SAMPLER=BuildingHeightSampler(cnbh_path=options['cnbh_raster'],ghsl_path=options['height_raster'],cmab_path=options['cmab_shards'])
    if _RESIDUALS is None:
        _RESIDUALS=json.loads(Path(options['parent_residuals']).read_text()) if options.get('parent_residuals') else {}
    source=Path(source_name);output=Path(options['output'])
    collection=read_raw(source)
    tile,origin,bbox,meta=raw_tile(source,collection)
    base_id='-'.join(map(str,tile));raw_hash=sha256(source)
    features=collection.get('features',[])
    residual_overrides=_RESIDUALS.get('parent_geometry_overrides',{})
    relevant_residuals={str(f['properties']['id']):residual_overrides[str(f['properties']['id'])]
                        for f in features if str(f['properties']['id']) in residual_overrides}
    # Only cells whose restored parent geometry changes invalidate their cache.
    # Unaffected previously published cells remain byte-identical and reusable.
    residual_hash=hashlib.sha256(json.dumps(relevant_residuals,sort_keys=True,separators=(',',':')).encode()).hexdigest() if relevant_residuals else None
    state_path=output/'state'/(base_id+'.json')
    if state_path.exists():
        state=json.loads(state_path.read_text())
        if state.get('source_sha256')==raw_hash and state.get('build_version')==VERSION and state.get('configuration_sha256')==options['configuration_sha256'] and state.get('parent_residual_sha256')==residual_hash:
            valid=True
            for model in state.get('models',[]):
                record_path=output/'records'/(model+'.json')
                if not record_path.exists():valid=False;break
                record=json.loads(record_path.read_text())
                if not (output/record['file']).exists() or not (output/record['feature_ids_file']).exists():valid=False;break
                if (output/record['file']).stat().st_size!=record['size_bytes']:valid=False;break
            if valid:return {'tile':base_id,'status':'cached','models':len(state['models'])}
    replacements=Counter();overrides=Counter();expected=Counter();residuals=Counter();residual_areas=Counter();nonrenderable=0
    exclusions=options['landmark_exclusions']
    excluded={'building':set(exclusions.get('building_ids',[])), 'building_part':set(exclusions.get('building_part_ids',[]))}
    for feature in features:
        props=feature['properties'];layer=props.get('source_layer','building');code=str(props['district_id'])
        identity=str(props.get('id',''));key=layer+':'+identity
        if props.get('renderable') is False:
            nonrenderable+=1
            if identity in residual_overrides and identity not in excluded[layer]:
                feature['geometry']=residual_overrides[identity]
                props['renderable']=True;props['_parent_residual']=True
                item=_RESIDUALS.get('parent_metadata',{}).get(identity,{})
                area=float(item.get('residual_area_m2',item.get('area_m2',0)))
                props['_parent_residual_area_m2']=area
                residuals[code]+=1;residual_areas[code]+=area
            else:continue
        else:expected[code]+=1
        if key in exclusions.get('geometry_overrides',{}):
            feature['geometry']=exclusions['geometry_overrides'][key];overrides[code]+=1
        elif identity in excluded[layer]:
            props['_landmark_replaced']=True;replacements[code]+=1
    records=publish_chunk(features,origin,bbox,tile,base_id,raw_hash,meta,options)
    if options.get('roof_overrides') is not None:
        expected_roofs={key for key in options['roof_overrides'] if any(key==f['properties'].get('source_layer','building')+':'+str(f['properties'].get('id','')) for f in features)}
        applied=[key for record in records for key in record.get('source_roof_enhancement',{}).get('keys',[])]
        if set(applied)!=expected_roofs or len(applied)!=len(expected_roofs):
            raise ValueError(f'Qualified roof coverage mismatch in {base_id}: expected {sorted(expected_roofs)}, applied {applied}')
    rendered=Counter()
    for record in records:
        for code,counts in record['district_counts'].items():rendered[code]+=counts['features']
    for code,count in expected.items():
        if rendered[code]+replacements[code]!=count+residuals[code]:
            raise ValueError(f'Coverage mismatch {base_id}/{code}: {rendered[code]} rendered + {replacements[code]} custom landmarks != {count} source + {residuals[code]} residual parents')
    for code in residuals:
        if rendered[code]+replacements[code]!=expected[code]+residuals[code]:raise ValueError(f'Residual coverage mismatch {base_id}/{code}')
    state={'tile':list(tile),'source_file':str(source),'source_sha256':raw_hash,'source_feature_count':len(collection.get('features',[])),
           'models':[r['id'] for r in records],'empty':not records,'build_version':VERSION,'compress':options['compress'],
           'configuration_sha256':options['configuration_sha256'],'target_bytes':options['target_bytes'],
           'source_renderable_count':sum(expected.values()),'nonrenderable_parent_count':nonrenderable,
           'source_district_counts':dict(expected),'landmark_replacement_counts':dict(replacements),
           'residual_parent_counts':dict(residuals),'residual_parent_area_m2':dict(residual_areas),'parent_residual_sha256':residual_hash,
           'landmark_geometry_override_counts':dict(overrides),'completed_at':utc()}
    if options.get('roof_overrides') is not None:
        state['source_roof_enhancement']={'count':len(applied),'keys':sorted(applied),
            'qualification_sha256':options['roof_qualification_sha256'],'geometry_version':options['roof_geometry_version']}
    atomic_json(state_path,state)
    return {'tile':base_id,'status':'done','models':len(records),'features':sum(r['building_count'] for r in records),'bytes':sum(r['size_bytes'] for r in records)}


def source_is_complete(raw):
    if (raw/'COMPLETE').exists():return True
    for name in ('manifest.json','coverage.json'):
        path=raw/name
        if path.exists():
            try:
                j=json.loads(path.read_text())
                if j.get('complete') is True or j.get('status')=='complete':return True
            except (ValueError,OSError):pass
    return False


def build_manifest(output,raw,complete,errors):
    records=[]
    for path in sorted((output/'records').glob('*.json')):
        records.append(json.loads(path.read_text()))
    districts={k:{'id':k,'name':v,'features':0,'building_footprints':0,'building_parts':0,**{q:0 for q in HEIGHT_KEYS}} for k,v in DISTRICTS.items()}
    totals=Counter({k:0 for k in HEIGHT_KEYS});source_counts=Counter()
    for record in records:
        totals.update(record['height_quality']);source_counts.update(record['geometry_sources'])
        for code,counts in record['district_counts'].items():
            for key,value in counts.items():districts[code][key]=districts[code].get(key,0)+value
    states=[json.loads(p.read_text()) for p in (output/'state').glob('*.json')]
    replaced=Counter();overrides=Counter();source_districts=Counter();residuals=Counter();residual_areas=Counter()
    for state in states:
        replaced.update(state.get('landmark_replacement_counts',{}))
        overrides.update(state.get('landmark_geometry_override_counts',{}))
        source_districts.update(state.get('source_district_counts',{}))
        residuals.update(state.get('residual_parent_counts',{}))
        residual_areas.update(state.get('residual_parent_area_m2',{}))
    for code,d in districts.items():
        d['landmark_replacement_count']=replaced[code]
        d['landmark_geometry_override_count']=overrides[code]
        d['source_renderable_count']=source_districts[code]
        d['residual_parent_features']=residuals[code]
        d['residual_parent_area_m2']=residual_areas[code]
        d['coverage_balanced']=d['features']+replaced[code]==source_districts[code]+residuals[code]
    raw_manifest=json.loads((raw/'manifest.json').read_text()) if (raw/'manifest.json').exists() else {}
    renderable_count=sum(s.get('source_renderable_count',0) for s in states)
    source_count=sum(s['source_feature_count'] for s in states)
    coverage_ok=all(d['coverage_balanced'] for d in districts.values())
    if complete and raw_manifest:
        coverage_ok=coverage_ok and renderable_count==raw_manifest.get('renderable_feature_count',raw_manifest.get('renderable_count'))
        coverage_ok=coverage_ok and source_count==raw_manifest.get('unique_feature_count',raw_manifest.get('feature_count'))
        for d in raw_manifest.get('districts',[]):
            code=str(d.get('id',d.get('district_id','')))
            if code in districts:
                coverage_ok=coverage_ok and source_districts[code]==d.get('renderable_feature_count',d.get('renderable_count'))
    raw_paths=sorted((raw/'tiles').rglob('*.geojson.gz'))+sorted((raw/'tiles').rglob('*.geojson'))
    payload={'version':VERSION,'complete':bool(complete and coverage_ok),'generated_at':utc(),
             'coordinate_system':'WGS84 origins; local metres, X east Y up Z south',
             'coverage':'Full available Overture building/part geometry within all 16 Shanghai district display polygons, assigned uniquely to geographic cells.',
             'partition_method':'Whole renderable building feature assigned by centroid to an owner tile; oversized owner cells median-split without slicing buildings. geographic_bbox is owner grid, geometry_bbox is actual expanded geometry.',
             'source_raw_directory':str(raw),'source_complete':source_is_complete(raw),'processed_source_tiles':len(states),'available_source_tiles':len(raw_paths),
             'model_count':len(records),'feature_count':sum(r['building_count'] for r in records),
             'source_feature_count':source_count,'source_renderable_count':renderable_count,
             'landmark_replacement_count':sum(replaced.values()),'landmark_geometry_override_count':sum(overrides.values()),
             'residual_parent_features':sum(residuals.values()),'residual_parent_area_m2':sum(residual_areas.values()),
             'residual_parent_height_quality':dict(sum((Counter(r.get('residual_parent_height_quality',{})) for r in records),Counter())),
             'residual_height_policy':'Parent height/floors may describe maximum tower height and are not used as podium height; exact residual footprints receive separately classified height estimates, with source min_height retained.',
             'nonrenderable_parent_count':sum(s.get('nonrenderable_parent_count',0) for s in states),
             'coverage_balanced':coverage_ok,'excluded_underground_count':raw_manifest.get('excluded_underground_unique_count',0),
             'building_footprints':sum(r['building_footprints'] for r in records),'building_parts':sum(r['building_parts'] for r in records),
             'triangle_count':sum(r['triangles'] for r in records),'total_model_bytes':sum(r['size_bytes'] for r in records),'max_file_bytes':max((r['size_bytes'] for r in records),default=0),
             'height_quality':dict(totals),'height_notice':HEIGHT_NOTICE,
             'geometry_sources':dict(source_counts),'districts':list(districts.values()),
             'license':'ODbL-1.0 (Overture buildings theme / derived footprint data)',
             'attribution':'© Overture Maps Foundation; © OpenStreetMap contributors; East Asian buildings / Qian Shi et al. (CC BY 4.0), doi:10.5281/zenodo.8174931; CMAB v2 predicted rooftops, CNBH2020 10m estimated heights, European Commission JRC GHSL2018 regional heights (all CC BY 4.0; see locked source provenance)',
             'errors':errors,'tiles':records}
    atomic_json(output/'manifest.json',payload)
    return payload


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True,help='Raw directory containing tiles/z/x/y.geojson.gz and COMPLETE marker')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--gltfpack',default=os.environ.get('GLTFPACK') or shutil.which('gltfpack'))
    parser.add_argument('--no-compress',action='store_true')
    parser.add_argument('--height-raster',type=Path,required=True,help='Official GHSL2018 WGS84 clip; regional estimates never override source heights/floors')
    parser.add_argument('--cnbh-raster',type=Path,required=True,help='CNBH2020 10m clip with embedded scale metadata')
    parser.add_argument('--cmab-shards',type=Path,required=True,help='CMAB rooftop parquet directory containing manifest.json')
    parser.add_argument('--height-lock',type=Path,required=True,help='Locked sampler version and source data checksums')
    parser.add_argument('--landmark-exclusions',type=Path,required=True,help='Verified exact UUID replacements and optional footprint differences')
    parser.add_argument('--parent-residuals',type=Path,required=True,help='Exact parent footprint minus complete building-part union; required to retain mapped podiums')
    parser.add_argument('--target-mb',type=float,default=9.0,help='Maximum target before compression; individual huge features may exceed target but never 100 MB')
    parser.add_argument('--workers',type=int,default=2)
    parser.add_argument('--watch',action='store_true')
    parser.add_argument('--poll-seconds',type=float,default=3)
    args=parser.parse_args()
    if not args.no_compress and not args.gltfpack:parser.error('gltfpack is required; pass --gltfpack PATH or --no-compress')
    args.output.mkdir(parents=True,exist_ok=True)
    for sub in ('tiles','ids','records','state','.work'):(args.output/sub).mkdir(exist_ok=True)
    lock=json.loads(args.height_lock.read_text())
    exclusions=json.loads(args.landmark_exclusions.read_text())
    configuration={'build_version':VERSION,'sampler_version':lock['sampler_version'],
                   'compress':not args.no_compress,'target_bytes':int(args.target_mb*1_000_000),
                   'height_lock_sha256':sha256(args.height_lock),'landmark_exclusions_sha256':sha256(args.landmark_exclusions),
                   'height_raster_sha256':sha256(args.height_raster),'cnbh_raster_sha256':sha256(args.cnbh_raster),
                   'cmab_manifest_sha256':sha256(args.cmab_shards/'manifest.json'),
                   'sampler_source_sha256':sha256(Path(__file__).parent/'building_height_sampler.py'),
                   'raster_sampler_source_sha256':sha256(Path(__file__).parent/'raster_height_sampler.py')}
    options={**configuration,'output':str(args.output),'gltfpack':args.gltfpack,
             'height_raster':str(args.height_raster),'cnbh_raster':str(args.cnbh_raster),'cmab_shards':str(args.cmab_shards),
             'landmark_exclusions':exclusions,
             'parent_residuals':str(args.parent_residuals) if args.parent_residuals else None,
             'configuration_sha256':hashlib.sha256(json.dumps(configuration,sort_keys=True).encode()).hexdigest()}
    atomic_json(args.output/'build-configuration.json',{**configuration,
                'parent_residual_file_sha256':sha256(args.parent_residuals) if args.parent_residuals else None,
                'exporter_source_sha256':sha256(Path(__file__)),
                'mesh_writer_source_sha256':sha256(Path(__file__).parent/'build_district_models.py'),
                'cache_compatibility_policy':'Base geometry engine version and height source hashes plus per-owner-cell residual geometry hash. Residual restoration does not invalidate unrelated cells.'})
    seen=set();errors=[];batch=0
    while True:
        paths=sorted((args.input/'tiles').rglob('*.geojson.gz'))+sorted((args.input/'tiles').rglob('*.geojson'))
        pending=[p for p in paths if str(p) not in seen]
        if pending:
            print('BATCH_START',len(pending),'raw tiles',flush=True)
            with ProcessPoolExecutor(max_workers=max(1,args.workers)) as pool:
                futures={pool.submit(export_source,str(p),options):p for p in pending}
                for future in as_completed(futures):
                    path=futures[future]
                    try:
                        result=future.result();seen.add(str(path));batch+=1
                        print('TILE',json.dumps(result,ensure_ascii=False),flush=True)
                    except Exception as exc:
                        error={'file':str(path),'error':str(exc),'at':utc()};errors.append(error);seen.add(str(path))
                        print('ERROR',json.dumps(error,ensure_ascii=False),flush=True)
                    if batch and batch%20==0:build_manifest(args.output,args.input,False,errors)
        complete=source_is_complete(args.input)
        current=sorted((args.input/'tiles').rglob('*.geojson.gz'))+sorted((args.input/'tiles').rglob('*.geojson'))
        all_seen=all(str(p) in seen for p in current)
        done=complete and all_seen and not errors
        payload=build_manifest(args.output,args.input,done,errors)
        if done and not payload['complete']:
            errors.append({'error':'Final source/model district coverage mismatch'})
            build_manifest(args.output,args.input,False,errors)
        print('PROGRESS',payload['model_count'],'models',payload['feature_count'],'features',payload['total_model_bytes'],'bytes','complete',payload['complete'],flush=True)
        if done or not args.watch or errors:break
        time.sleep(max(.5,min(args.poll_seconds,30)))
    if errors:raise SystemExit(1)


if __name__=='__main__':main()
