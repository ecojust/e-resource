#!/usr/bin/env python3
"""Fail-closed audit of the Shanghai v5 physical city delivery.

Default requires all 16 districts / 1,708 macros / 1,796,419 unique features.
Use --allow-partial explicitly for a builder pilot. No browser, GPU or network.
Checks actual file hashes, 100MB ceiling, ownership, frozen-source conservation,
GLB structure/self-containment and GPU-instancing-expanded triangle counts.
Compressed vertex values are not decoded here; optional far.raw.glb supplies
per-triangle feature-ID checks when retained. Reports explicitly count this
coverage. Browser shader/appearance tests remain separate.
"""
from __future__ import annotations
import argparse
import collections
import gzip
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
import tempfile
import time
import zlib

LIMIT = 100_000_000
EXPECTED = {'feature_count': 1_796_419, 'macro_count': 1708,
            'renderable_exclusions': 98, 'residuals': 401,
            'qualified_roofs': 126, 'protected_keys': 103}
DISTRICTS = {'310101','310104','310105','310106','310107','310109','310110',
             '310112','310113','310114','310115','310116','310117','310118',
             '310120','310151'}
COMPONENTS = {5120:(1,'b'),5121:(1,'B'),5122:(2,'h'),5123:(2,'H'),
              5125:(4,'I'),5126:(4,'f')}
WIDTHS = {'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT2':4,'MAT3':9,'MAT4':16}


class Invalid(ValueError):
    pass


def need(condition, message):
    if not condition:
        raise Invalid(message)


def integer(value, label, minimum=0):
    need(type(value) is int and value >= minimum, f'{label}: invalid integer {value!r}')
    return value


def read_json(path):
    raw=Path(path).read_bytes()
    if raw[:2]==b'\x1f\x8b':
        raw=gzip.decompress(raw)
    def bad_constant(value):
        raise Invalid(f'{path}: nonfinite JSON number {value}')
    return json.loads(raw,parse_constant=bad_constant)


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):
            h.update(chunk)
    return h.hexdigest()


def inside(base, name, *, source_symlink=False):
    need(isinstance(name,str) and name and not Path(name).is_absolute(),f'Invalid relative asset path: {name!r}')
    need('://' not in name and '?' not in name and '#' not in name,f'External asset reference: {name}')
    need('..' not in Path(name).parts,f'Parent traversal in asset path: {name}')
    target=(base/name).resolve()
    need(source_symlink or target.is_relative_to(base.resolve()),f'Asset escapes delivery root: {name}')
    need(target.is_file(),f'Missing asset: {target}')
    return target


def file_check(path, metadata):
    size=path.stat().st_size
    need(0<size<LIMIT,f'{path}: {size} bytes is outside (0,100000000)')
    declared=metadata.get('size_bytes',metadata.get('bytes'))
    need(size==declared,f'{path}: byte count {size} != {declared}')
    need(digest(path)==metadata.get('sha256'),f'{path}: SHA-256 mismatch')


def is_glb_file(path):
    return path.name.lower().endswith(('.glb','.glb.gz'))


def load_glb_bytes(path, metadata=None):
    """Bounded gzip decoding; stored and decoded files must both be <100MB.

    Near records supply encoding plus decoded digest/size. Generic orphan-file
    inspection can omit metadata, but still checks the actual decoded payload.
    """
    path=Path(path);size=path.stat().st_size
    need(0<size<LIMIT,f'{path}: stored GLB size must be below {LIMIT} bytes')
    zipped=path.name.lower().endswith('.glb.gz')
    if metadata is not None:
        encoding=metadata.get('content_encoding')
        if zipped:
            need(encoding=='gzip',f'{path}: .glb.gz must declare content_encoding:gzip')
            decoded_size=integer(metadata.get('decoded_size_bytes'),f'{path} decoded_size_bytes',28)
            need(decoded_size<LIMIT,f'{path}: declared decoded size must be below {LIMIT} bytes')
            declared_hash=metadata.get('decoded_sha256')
            need(isinstance(declared_hash,str) and len(declared_hash)==64 and all(c in '0123456789abcdef' for c in declared_hash),
                 f'{path}: invalid decoded_sha256')
        else:
            need(encoding in (None,'identity'),f'{path}: content_encoding does not match .glb filename')
    if zipped:
        with path.open('rb') as stream:
            need(stream.read(2)==b'\x1f\x8b',f'{path}: .glb.gz does not contain gzip bytes')
        chunks=[];total=0
        try:
            with gzip.open(path,'rb') as stream:
                while True:
                    chunk=stream.read(min(1024*1024,LIMIT-total))
                    if not chunk:
                        break
                    total+=len(chunk)
                    need(total<LIMIT,f'{path}: actual decoded size reaches/exceeds {LIMIT} bytes')
                    chunks.append(chunk)
        except (OSError,EOFError,zlib.error) as error:
            raise Invalid(f'{path}: invalid gzip payload: {error}') from error
        data=b''.join(chunks)
    else:
        data=path.read_bytes()
    need(28<=len(data)<LIMIT,f'{path}: invalid/oversized decoded GLB length')
    if zipped and metadata is not None:
        need(len(data)==decoded_size,f'{path}: decoded byte count {len(data)} != {decoded_size}')
        need(hashlib.sha256(data).hexdigest()==declared_hash,f'{path}: decoded SHA-256 mismatch')
    return data


def footprint_bounds(geometry):
    need(geometry.get('type') in ('Polygon','MultiPolygon'),'Feature is not a polygon footprint')
    polygons=geometry['coordinates'] if geometry['type']=='MultiPolygon' else [geometry['coordinates']]
    points=[point for polygon in polygons for ring in polygon for point in ring]
    need(points and all(len(p)>=2 and math.isfinite(p[0]) and math.isfinite(p[1]) for p in points),'Invalid geographic footprint coordinates')
    return [min(p[0] for p in points),min(p[1] for p in points),max(p[0] for p in points),max(p[1] for p in points)]


def inspect_glb(path, *, metadata=None, far=False, feature_count=None, check_raw_ids=False):
    """Count rendered active-scene triangles, including every GPU instance."""
    data=load_glb_bytes(path,metadata)
    magic,version,length=struct.unpack_from('<4sII',data)
    need(magic==b'glTF' and version==2 and length==len(data),f'{path}: bad GLB header')
    chunks=[];cursor=12
    while cursor<len(data):
        need(cursor+8<=len(data),f'{path}: truncated chunk header')
        n,kind=struct.unpack_from('<II',data,cursor);cursor+=8
        need(n%4==0 and cursor+n<=len(data),f'{path}: invalid chunk bounds/alignment')
        chunks.append((kind,data[cursor:cursor+n]));cursor+=n
    need(len(chunks)==2 and chunks[0][0]==0x4e4f534a and chunks[1][0]==0x004e4942,
         f'{path}: expected one JSON and one embedded BIN chunk')
    g=json.loads(chunks[0][1]);binary=chunks[1][1]
    need(g.get('asset',{}).get('version')=='2.0',f'{path}: wrong glTF version')
    buffers=g.get('buffers',[]);views=g.get('bufferViews',[]);accessors=g.get('accessors',[])
    need(buffers and buffers[0].get('byteLength',0)<=len(binary)<=buffers[0].get('byteLength',0)+3,
         f'{path}: BIN length differs from primary buffer')
    for i,b in enumerate(buffers):
        need('uri' not in b,f'{path}: buffer {i} is external')
        integer(b.get('byteLength'),f'{path}: buffer {i} byteLength')
        if i:
            need(b.get('extensions',{}).get('EXT_meshopt_compression',{}).get('fallback') is True,
                 f'{path}: extra buffer is not a meshopt virtual fallback')
    for i,v in enumerate(views):
        bi=integer(v.get('buffer'),f'view {i} buffer')
        need(bi<len(buffers),f'{path}: invalid buffer reference')
        off=integer(v.get('byteOffset',0),f'view {i} offset');n=integer(v.get('byteLength'),f'view {i} length')
        need(off+n<=buffers[bi]['byteLength'],f'{path}: view {i} overflows buffer')
        compression=v.get('extensions',{}).get('EXT_meshopt_compression')
        if compression:
            need(compression.get('buffer')==0,f'{path}: meshopt source must be embedded BIN')
            co=integer(compression.get('byteOffset',0),'meshopt offset');cn=integer(compression.get('byteLength'),'meshopt length')
            need(co+cn<=buffers[0]['byteLength'],f'{path}: meshopt payload overflows BIN')
            count=integer(compression.get('count'),'meshopt count');stride=integer(compression.get('byteStride'),'meshopt stride',1)
            need(count*stride==n,f'{path}: meshopt decoded byte length mismatch')
        elif bi:
            raise Invalid(f'{path}: virtual fallback view lacks compressed payload')
    for i,a in enumerate(accessors):
        count=integer(a.get('count'),f'accessor {i} count');component=a.get('componentType');typ=a.get('type')
        need(component in COMPONENTS and typ in WIDTHS,f'{path}: unsupported accessor {i}')
        need('sparse' not in a,f'{path}: sparse accessors not emitted by this pipeline')
        vi=integer(a.get('bufferView'),f'accessor {i} bufferView');need(vi<len(views),f'{path}: missing view')
        view=views[vi];width=COMPONENTS[component][0]*WIDTHS[typ];stride=view.get('byteStride',width)
        need(type(stride) is int and stride>=width,f'{path}: invalid accessor stride')
        size=integer(a.get('byteOffset',0),f'accessor {i} offset')+(max(0,count-1)*stride+width if count else 0)
        need(size<=view['byteLength'],f'{path}: accessor {i} overflows view')
    for image in g.get('images',[]):
        need('uri' not in image and type(image.get('bufferView')) is int,
             f'{path}: nonembedded image')
        need(0<=image['bufferView']<len(views),f'{path}: bad image bufferView')
    def acc(i):
        need(type(i) is int and 0<=i<len(accessors),f'{path}: missing accessor {i}')
        return accessors[i]
    def scalars(i):
        a=acc(i);v=views[a['bufferView']]
        need(a['type']=='SCALAR' and v['buffer']==0 and not v.get('extensions'),
             f'{path}: raw-ID audit requires uncompressed scalar buffer')
        size,fmt=COMPONENTS[a['componentType']];stride=v.get('byteStride',size)
        start=v.get('byteOffset',0)+a.get('byteOffset',0)
        return [struct.unpack_from('<'+fmt,binary,start+j*stride)[0] for j in range(a['count'])]
    mesh_triangles=[];raw_seen=set()
    for mesh in g.get('meshes',[]):
        tris=0
        for primitive in mesh.get('primitives',[]):
            need(primitive.get('mode',4)==4,f'{path}: expected TRIANGLES primitive')
            attrs=primitive.get('attributes',{});position=acc(attrs.get('POSITION'))
            need(position['type']=='VEC3',f'{path}: invalid POSITION type')
            for attribute in attrs.values():
                need(acc(attribute)['count']==position['count'],f'{path}: vertex attribute counts differ')
            indices=acc(primitive['indices']) if 'indices' in primitive else None
            if indices:
                need(indices['type']=='SCALAR' and indices['componentType'] in (5121,5123,5125),f'{path}: invalid indices')
            n=indices['count'] if indices else position['count']
            need(n%3==0,f'{path}: triangle index count not divisible by 3');tris+=n//3
            if far:
                need('_FEATURE_ID_0' in attrs,f'{path}: solid far primitive lacks feature ID mask attribute')
                ids=acc(attrs['_FEATURE_ID_0'])
                need(ids['type']=='SCALAR' and not ids.get('normalized',False),f'{path}: invalid far IDs')
                if check_raw_ids:
                    values=scalars(attrs['_FEATURE_ID_0']);order=scalars(primitive['indices']) if indices else list(range(n))
                    need(all(type(v) is int and 1<=v<=feature_count for v in values),f'{path}: far feature ID outside 1..N')
                    need(all(0<=v<len(values) for v in order),f'{path}: far index outside vertices')
                    for j in range(0,n,3):
                        a,b,c=(values[order[j+k]] for k in range(3))
                        need(a==b==c,f'{path}: one triangle mixes feature IDs; mask interpolation unsafe')
                        raw_seen.add(a)
        mesh_triangles.append(tris)
    nodes=g.get('nodes',[]);scenes=g.get('scenes',[]);scene=g.get('scene',0)
    need(type(scene) is int and 0<=scene<len(scenes),f'{path}: missing active scene')
    visited=set();expanded=0;instances=0;instanced_nodes=0
    def visit(index):
        nonlocal expanded,instances,instanced_nodes
        need(type(index) is int and 0<=index<len(nodes),f'{path}: bad scene node')
        need(index not in visited,f'{path}: cyclic/multiply-parented scene node')
        visited.add(index);node=nodes[index]
        if 'mesh' in node:
            mi=node['mesh'];need(type(mi) is int and 0<=mi<len(mesh_triangles),f'{path}: bad mesh index')
            attributes=node.get('extensions',{}).get('EXT_mesh_gpu_instancing',{}).get('attributes')
            count=1
            if attributes is not None:
                need(isinstance(attributes,dict) and attributes,f'{path}: empty instancing extension')
                counts={acc(a)['count'] for a in attributes.values()}
                need(len(counts)==1,f'{path}: GPU instance attribute counts disagree')
                count=counts.pop();instances+=count;instanced_nodes+=1
                for semantic,typ in [('TRANSLATION','VEC3'),('ROTATION','VEC4'),('SCALE','VEC3')]:
                    if semantic in attributes:
                        need(acc(attributes[semantic])['type']==typ,f'{path}: invalid instance {semantic}')
            expanded+=mesh_triangles[mi]*count
        for child in node.get('children',[]):
            visit(child)
    for index in scenes[scene].get('nodes',[]):
        visit(index)
    if check_raw_ids:
        need(raw_seen==set(range(1,feature_count+1)),f'{path}: far geometry does not represent exactly every feature')
    extras=dict(g.get('extras',{}))
    # The baseline mesh writer stores geographic provenance on its single
    # node. A packed model may preserve it there or move it to root extras.
    for index in visited:
        metadata=nodes[index].get('extras',{})
        if 'macro_id' in metadata:
            for name,value in metadata.items():
                need(name not in extras or extras[name]==value,f'{path}: conflicting embedded provenance {name}')
                extras[name]=value
    return {'expanded_triangles':expanded,'instances':instances,'instanced_nodes':instanced_nodes,
            'base_mesh_triangles':sum(mesh_triangles),'extras':extras,
            'decoded_size_bytes':len(data),'decoded_sha256':hashlib.sha256(data).hexdigest()}


def audit(root, project, allow_partial=False):
    started=time.monotonic();report={'passed':False,'scope':'partial pilot' if allow_partial else 'complete city',
        'root':str(root),'errors':[],'expected':EXPECTED,'checked_files':0,'checked_glbs':0,'checked_gzip_glbs':0,
        'largest_file':None,'far_id_audit':{'raw_values_checked_macros':0,'packed_layout_only_macros':0},
        'checks':['100000000-byte exclusive stored AND decoded limits','stored SHA-256 and bytes; declared gzip encoding plus decoded SHA-256 and bytes',
        'one near owner per feature','frozen 16-district source conservation',
        'all embedded GLBs structurally valid','actual GPU-instance-expanded triangle counts',
        'far feature ID attribute layout; optional raw IDs constant per triangle and complete'],
        'limitations':['No compressed-vertex decoding, WebGL shader execution or visual fidelity assessment.']}
    try:
        manifest=read_json(root/'manifest.json');config=read_json(root/'build-configuration.json')
        baseline=read_json(project/'assets/city/manifest.json');baseline_rows={t['id']:t for t in baseline['tiles']}
        exclude=read_json(project/'data/landmark-exclusions.json')
        protected={layer+':'+str(k) for layer in ('building','building_part') for k in exclude[layer+'_ids']}
        residuals=read_json(project/'data/parent-residual-overrides.json')['parent_geometry_overrides']
        roofs={r['key']:r for r in read_json(project/'data/roofs/qualified-roofs.json')['roofs']}
        need(manifest.get('schema')=='shanghai-city-v5-v1','Unsupported city manifest schema')
        need(manifest.get('expected_city')==EXPECTED and config.get('expected_city')==EXPECTED,'Expected conservation constants changed')
        need(len(protected)==103 and len(roofs)==126,'Frozen protected/roof source changed')
        need({str(d['id']) for d in baseline['districts']}==DISTRICTS,'Baseline does not contain exact 16 Shanghai districts')
        need(not manifest.get('errors') and not manifest.get('duplicate_keys'),'Builder reports errors or duplicate feature keys')
        if not allow_partial:
            need(manifest.get('complete') is True,'Full city required; manifest is incomplete. Use --allow-partial only for a pilot.')
        confighash=hashlib.sha256(canonical(config)).hexdigest()
        need(manifest.get('configuration_sha256')==confighash,'Configuration digest mismatch')
        for name,expected_hash in config['input_hashes'].items():
            need(digest(inside(project,name,source_symlink=True))==expected_hash,f'Frozen input changed: {name}')
        tiles=manifest.get('tiles',[]);ids=[t['id'] for t in tiles]
        need(tiles and len(ids)==len(set(ids)),'Empty/duplicate macro index')
        need(set(ids)<=set(baseline_rows),'Unknown macro in manifest')
        ready_paths={str(p.relative_to(root)) for p in (root/'macros').glob('*/READY.json')}
        need({t['near_manifest_file'] for t in tiles}==ready_paths,'Manifest/READY coverage differs')
        all_keys=set();all_roofs=set();all_excluded=set();all_near_ids=set();district_counts=collections.Counter();totals=collections.Counter()
        referenced_glbs=set()
        for t in tiles:
            macro=t['id']
            try:
                ready_path=inside(root,t['near_manifest_file']);directory=ready_path.parent;r=read_json(ready_path);row=baseline_rows[macro]
                need(r.get('id')==macro and r.get('complete') is True,f'{macro}: not a matching READY macro')
                need(r.get('configuration_sha256')==confighash,f'{macro}: mixed build configuration')
                n=integer(r.get('feature_count'),f'{macro} feature count',1)
                need(n==row['building_count']==t.get('feature_count')==t.get('building_count'),f'{macro}: feature count differs from frozen baseline/index')
                need(r.get('source_sha256')==row['source_sha256'] and r.get('baseline_far_sha256')==row['sha256'],f'{macro}: source/far baseline changed')
                need(r.get('feature_id_base')==1,f'{macro}: feature ID base is not 1')
                need(r.get('source_height_and_footprint_preserved') is True,f'{macro}: source preservation declaration missing')
                for name in ('origin_longitude','origin_latitude','geographic_bbox','geometry_bbox'):
                    need(r[name]==t[name],f'{macro}: index/{name} differs')
                published=r['published_files'];actual={str(p.relative_to(directory)) for p in directory.rglob('*') if p.is_file() and p!=ready_path}
                need(set(published)==actual,f'{macro}: untracked/missing published files')
                for name,metadata in published.items():
                    file_check(inside(directory,name),metadata)
                for name in ('feature_table_file','feature_ids_file'):
                    need(inside(root,t[name])==inside(directory,r[name]),f'{macro}: index/{name} points elsewhere')
                table=read_json(inside(directory,r['feature_table_file']));keys=table['keys'];features=table['features']
                need(table.get('feature_id_base')==1 and len(keys)==n+1 and keys[0] is None,f'{macro}: invalid reserved ID0 feature table')
                need(len(features)==n and len(set(keys[1:]))==n,f'{macro}: missing/duplicate features')
                need(not(set(keys[1:])&protected),f'{macro}: landmark-protected feature reappears')
                need(not(set(keys[1:])&all_keys),f'{macro}: duplicate key across macro boundary')
                quality=collections.Counter();local_districts=collections.Counter();local_roofs=set();residual_count=0;feature_bounds={}
                for i,f in enumerate(features,1):
                    need(f.get('localId')==i and f.get('key')==keys[i],f'{macro}: feature ID/key order mismatch')
                    props=f['properties'];need(f['key']==str(props['source_layer'])+':'+str(props['id']),f'{macro}: feature key/property identity mismatch')
                    district=str(props['district_id']);need(district in DISTRICTS,f'{macro}: unknown district {district}');local_districts[district]+=1
                    need(math.isfinite(f['base']) and math.isfinite(f['height']) and f['height']>f['base'],f'{macro}: invalid height')
                    quality[f['height_quality']]+=1
                    feature_bounds[i]=footprint_bounds(f['geometry'])
                    if f.get('residual'):
                        residual_count+=1;need(f['geometry']==residuals.get(str(props['id'])),f'{macro}: residual footprint changed')
                    if f.get('roof'):
                        need(f['roof']==roofs.get(f['key']),f'{macro}: sourced roof parameters changed')
                        need(f['geometry']==f['roof']['geometry'] and f['base']==f['roof']['base'] and f['height']==f['roof']['height'],f'{macro}: sourced roof geometry/height changed')
                        local_roofs.add(f['key'])
                need(dict(quality)=={k:v for k,v in row['height_quality'].items() if v}==r['height_quality'],f'{macro}: height-quality distribution changed')
                need(dict(local_districts)=={str(k):v['features'] for k,v in row['district_counts'].items() if v['features']},f'{macro}: district feature counts changed')
                need(residual_count==r['residual_count']==row.get('residual_parent_features',0),f'{macro}: residual count changed')
                need(local_roofs==set(r['source_roof_keys'])==set(row.get('source_roof_enhancement',{}).get('keys',[])),f'{macro}: sourced roof coverage changed')
                excluded=r['excluded_renderable_keys'];need(len(excluded)==len(set(excluded)) and set(excluded)<=protected,f'{macro}: invalid excluded landmark list')
                need(not(set(excluded)&all_excluded),f'{macro}: duplicated exclusion')
                near=r['near'];need(near==r['tiles'] and near,f'{macro}: near/tiles alias mismatch')
                near_ids=[x['id'] for x in near];need(len(near_ids)==len(set(near_ids)),f'{macro}: duplicate near tile ID')
                need(not(set(near_ids)&all_near_ids),f'{macro}: near tile ID repeated across macros')
                owners={};near_triangles=0;near_bytes=0;budget_exceptions=0
                for tile in near:
                    filename=inside(directory,tile['file']);file_check(filename,tile)
                    glb=inspect_glb(filename,metadata=tile);referenced_glbs.add(filename)
                    need(glb['expanded_triangles']==tile['triangles']==tile['expandedTriangles'],f'{macro}/{tile["id"]}: understated/incorrect expanded triangle count')
                    local_ids=tile['featureLocalIds'];need(tile.get('feature_id_base')==1 and len(local_ids)==tile['feature_count'] and local_ids,f'{macro}: near feature metadata mismatch')
                    need(glb['extras'].get('featureLocalIds')==local_ids and glb['extras'].get('macro_id')==macro,f'{macro}: embedded near ownership differs')
                    need(glb['extras'].get('expandedTriangles')==tile['triangles'],f'{macro}: embedded expanded triangle count differs')
                    for local_id in local_ids:
                        need(type(local_id) is int and 1<=local_id<=n and local_id not in owners,f'{macro}: missing, duplicate or out-of-range near feature ownership')
                        owners[local_id]=tile['id']
                    boxes=[feature_bounds[i] for i in local_ids]
                    bbox=[min(b[0] for b in boxes),min(b[1] for b in boxes),max(b[2] for b in boxes),max(b[3] for b in boxes)]
                    need(tile.get('geographic_bbox')==bbox,f'{macro}: near bounds do not cover assigned footprint geometry exactly')
                    padded=tile.get('geometry_bbox',[])
                    need(len(padded)==4 and all(math.isfinite(x) for x in padded) and padded[0]<=bbox[0] and padded[1]<=bbox[1] and padded[2]>=bbox[2] and padded[3]>=bbox[3],f'{macro}: near streaming bounds truncate geometry')
                    need(tile.get('origin_longitude')==r['origin_longitude'] and tile.get('origin_latitude')==r['origin_latitude'],f'{macro}: near model origin differs')
                    exception=tile['triangles']>config['target_triangles']
                    need(tile.get('budgetException') is exception,f'{macro}: incorrect triangle budget exception')
                    if exception:
                        need(len(local_ids)==1 and tile.get('budgetExceptionReason'),f'{macro}: multi-building/undocumented budget exception')
                    near_triangles+=tile['triangles'];near_bytes+=filename.stat().st_size;budget_exceptions+=exception
                need(set(owners)==set(range(1,n+1)),f'{macro}: not every feature has exactly one near owner')
                ownership=read_json(inside(directory,r['ownership_file']))
                need(ownership.get('feature_id_base')==1 and ownership.get('owners')==[[i,owners[i]] for i in range(1,n+1)],f'{macro}: ownership sidecar differs')
                need(near_triangles==r['near_total_triangles'] and near_bytes==r['near_total_bytes'],f'{macro}: near totals differ')
                far_path=inside(directory,r['far']['file']);file_check(far_path,r['far']);file_check(inside(root,t['file']),t)
                need(inside(root,t['file'])==far_path,f'{macro}: index points to wrong far model')
                far=inspect_glb(far_path,metadata=r['far'],far=True);referenced_glbs.add(far_path)
                checked_far=[far]
                if r['far'].get('raw_file'):
                    raw_path=inside(directory,r['far']['raw_file']);raw=inspect_glb(raw_path,far=True,feature_count=n,check_raw_ids=True);referenced_glbs.add(raw_path)
                    need(raw['expanded_triangles']==far['expanded_triangles'],f'{macro}: raw/packed far triangles differ')
                    checked_far.append(raw);report['far_id_audit']['raw_values_checked_macros']+=1
                else:
                    report['far_id_audit']['packed_layout_only_macros']+=1
                need(far['expanded_triangles']==r['far']['triangles']==t['triangles']==row['triangles'],f'{macro}: far triangle count changed')
                for model in checked_far:
                    need(model['extras'].get('feature_count')==n,f'{macro}: embedded far feature count differs')
                    need(model['extras'].get('macro_id')==macro and model['extras'].get('configuration_sha256')==confighash,
                         f'{macro}: embedded far macro/config provenance differs')
                    need(model['extras'].get('source_sha256')==row['source_sha256'],f'{macro}: embedded far source provenance differs')
                all_keys.update(keys[1:]);all_roofs.update(local_roofs);all_excluded.update(excluded);all_near_ids.update(near_ids);district_counts.update(local_districts)
                totals.update(features=n,macro_count=1,residuals=residual_count,renderable_exclusions=len(excluded),qualified_roofs=len(local_roofs),near_tiles=len(near),near_bytes=near_bytes,far_bytes=far_path.stat().st_size,near_expanded_triangles=near_triangles,budget_exception_tiles=budget_exceptions)
            except (Invalid,KeyError,TypeError,ValueError,OSError) as error:
                report['errors'].append(f'{macro}: {error}')
                if len(report['errors'])>=30:
                    break
        for file in root.rglob('*'):
            if not file.is_file():
                continue
            size=file.stat().st_size;need(size<LIMIT,f'{file}: single file exceeds 100MB limit')
            report['checked_files']+=1
            if not report['largest_file'] or size>report['largest_file']['bytes']:
                report['largest_file']={'file':str(file.relative_to(root)),'bytes':size}
            if is_glb_file(file):
                if file.resolve() not in referenced_glbs:
                    need(not file.name.lower().endswith('.glb.gz'),
                         f'{file}: gzip GLB lacks a validated model record with decoded size/SHA metadata')
                    inspect_glb(file)
                report['checked_glbs']+=1
                if file.name.lower().endswith('.glb.gz'):
                    report['checked_gzip_glbs']+=1
        need(not report['errors'],'One or more macros failed; see errors')
        for name,value in totals.items():
            need(value==manifest['totals'].get(name),f'Global total {name}: observed {value} != manifest {manifest["totals"].get(name)}')
        expected_totals={'features':EXPECTED['feature_count'],'macro_count':EXPECTED['macro_count'],'residuals':401,'renderable_exclusions':98,'qualified_roofs':126}
        if not allow_partial or manifest.get('complete') is True:
            need(all(totals[k]==v for k,v in expected_totals.items()),'Incomplete full-city conservation counts')
            need(set(ids)==set(baseline_rows),'Full city is missing baseline macros')
            need(dict(district_counts)=={str(d['id']):d['features'] for d in baseline['districts']},'Full 16-district coverage/counts differ')
            need(all_roofs==set(roofs),'Not all 126 sourced roofs represented')
        else:
            need(all(totals[k]<=v for k,v in expected_totals.items()),'Partial pilot exceeds whole-city conservation bounds')
        report.update(passed=True,totals=dict(totals),district_counts=dict(sorted(district_counts.items())),
                      protected_keys=len(protected),unique_features=len(all_keys),manifest_complete=manifest.get('complete'))
    except (Invalid,KeyError,TypeError,ValueError,OSError) as error:
        report['errors'].append(str(error))
    report['seconds']=round(time.monotonic()-started,3)
    return report


def self_test():
    """Small real binary fixtures prove instancing and rejection paths."""
    with tempfile.TemporaryDirectory(prefix='city-detail-validator-') as temp:
        p=Path(temp)/'fixture.glb';binary=b'\0'*120
        g={'asset':{'version':'2.0'},'scene':0,'scenes':[{'nodes':[0]}],
           'nodes':[{'mesh':0,'extensions':{'EXT_mesh_gpu_instancing':{'attributes':{'TRANSLATION':2}}}}],
           'meshes':[{'primitives':[{'attributes':{'POSITION':0},'indices':1}]}],
           'buffers':[{'byteLength':120}],
           'bufferViews':[{'buffer':0,'byteOffset':0,'byteLength':72},{'buffer':0,'byteOffset':72,'byteLength':12},{'buffer':0,'byteOffset':84,'byteLength':36}],
           'accessors':[{'bufferView':0,'componentType':5126,'count':6,'type':'VEC3'},
                        {'bufferView':1,'componentType':5123,'count':6,'type':'SCALAR'},
                        {'bufferView':2,'componentType':5126,'count':3,'type':'VEC3'}]}
        def write():
            j=canonical(g);j+=b' '*((-len(j))%4)
            p.write_bytes(struct.pack('<4sII',b'glTF',2,28+len(j)+len(binary))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(binary),0x004e4942)+binary)
        write();need(inspect_glb(p)['expanded_triangles']==6,'Instancing multiplier regression')
        zipped=p.with_suffix('.glb.gz');decoded=p.read_bytes();zipped.write_bytes(gzip.compress(decoded,mtime=0))
        metadata={'size_bytes':zipped.stat().st_size,'sha256':digest(zipped),
                  'content_encoding':'gzip','decoded_size_bytes':len(decoded),
                  'decoded_sha256':hashlib.sha256(decoded).hexdigest()}
        file_check(zipped,metadata)
        need(inspect_glb(zipped,metadata=metadata)['expanded_triangles']==6,'Gzip must retain full instance inspection')
        for broken in [dict(metadata,decoded_sha256='0'*64),dict(metadata,decoded_size_bytes=LIMIT),dict(metadata,content_encoding='identity')]:
            try:
                inspect_glb(zipped,metadata=broken)
            except Invalid:
                pass
            else:
                raise Invalid('Invalid gzip metadata accepted')
        g['nodes'].append({'mesh':0});g['scenes'][0]['nodes'].append(1);write()
        need(inspect_glb(p)['expanded_triangles']==8,'Repeated mesh node count regression')
        g['buffers'][0]['uri']='https://example.invalid/external.bin';write()
        try:
            inspect_glb(p)
        except Invalid:
            pass
        else:
            raise Invalid('External-buffer rejection regression')
        del g['buffers'][0]['uri'];g['accessors'][2]['count']=4;write()
        try:
            inspect_glb(p)
        except Invalid:
            pass
        else:
            raise Invalid('Accessor overflow rejection regression')
        g['accessors'][2]['count']=3
        binary=binary[:72]+struct.pack('<6H',0,1,2,3,4,5)+binary[84:]+struct.pack('<6I',1,1,1,2,2,2)
        g['buffers'][0]['byteLength']=len(binary)
        g['bufferViews'].append({'buffer':0,'byteOffset':120,'byteLength':24})
        g['accessors'].append({'bufferView':3,'componentType':5125,'count':6,'type':'SCALAR'})
        g['meshes'][0]['primitives'][0]['attributes']['_FEATURE_ID_0']=3
        write();inspect_glb(p,far=True,feature_count=2,check_raw_ids=True)
        binary=binary[:120]+struct.pack('<6I',1,2,1,2,2,2);write()
        try:
            inspect_glb(p,far=True,feature_count=2,check_raw_ids=True)
        except Invalid:
            pass
        else:
            raise Invalid('Mixed triangle feature-ID rejection regression')
    return {'passed':True,'checks':['three GPU instances multiply two triangles to six','one additional shared-mesh node adds two triangles','external buffer rejected','accessor overflow rejected','complete raw far IDs accepted; mixed-ID triangle rejected','gzip payload receives full instance audit','wrong decoded digest, excessive decoded size and wrong gzip encoding rejected']}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    project_default=Path(__file__).resolve().parents[1]
    parser.add_argument('--project',type=Path,default=project_default,help='Frozen baseline project (default: this project)')
    parser.add_argument('--root',type=Path,help='City-detail delivery root (default: PROJECT/assets/city-detail)')
    parser.add_argument('--output',type=Path,help='Write JSON report; stdout always prints it')
    parser.add_argument('--allow-partial',action='store_true',help='Explicit pilot-only audit; never reports full-city completion')
    parser.add_argument('--self-test',action='store_true',help='Run binary parser rejection/instancing fixtures only')
    args=parser.parse_args()
    report=self_test() if args.self_test else audit((args.root or args.project/'assets/city-detail').resolve(),args.project.resolve(),args.allow_partial)
    result=json.dumps(report,ensure_ascii=False,indent=2)+'\n'
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(result)
    print(result,end='')
    raise SystemExit(0 if report['passed'] else 1)


if __name__=='__main__':
    main()
