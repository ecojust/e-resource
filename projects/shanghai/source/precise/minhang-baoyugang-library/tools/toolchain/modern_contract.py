"""Stage-only input guards for actual modern-building packaging, not acceptance."""
from pathlib import Path
import hashlib,json,re

LIMIT=100_000_000
IDS={'jiading-shanghai-auto-museum','minhang-baoyugang-library'}
HERE=Path(__file__).resolve().parent

def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def require(ok,message):
    if not ok:raise ValueError(message)

def load(path):return json.loads(Path(path).read_text())

def bound(record):
    require(isinstance(record,dict),'Actual descriptor is pending')
    require(isinstance(record.get('source'),str),'Descriptor source must be explicit')
    p=Path(record['source'])
    require(p.is_absolute() and p.is_file() and not any(x.is_symlink() for x in (p,*p.parents)),'Actual regular source path required')
    require(type(record.get('bytes')) is int and 0<record['bytes']<LIMIT,'Source must be strictly below100000000 bytes')
    require(re.fullmatch('[a-f0-9]{64}',str(record.get('sha256',''))) is not None,'Actual SHA256 required')
    require(p.stat().st_size==record['bytes'] and sha(p)==record['sha256'],'Descriptor changed: '+str(p))
    return p

def target(path):
    t=load(path)
    require(t.get('schema')=='modern-building-target-spec-v11','Unsupported target schema')
    require(t.get('status')=='ready','Pending target cannot produce a package or acceptance record')
    require(t.get('id') in IDS,'Unknown target')
    require(t.get('browser_accepted') is False,'Packaging cannot assert browser acceptance')
    g=load(bound(t['source_geometry']))
    require(g['id']==t['id'] and g['source']['owner_macro_id']==t['owner_macro_id'],'Frozen owner identity mismatch')
    require(g['source']['key']==t['source_key'],'Frozen owner key mismatch')
    require(t['district']=={'id':g['district_id'],'name':g['district_name']},'Frozen source district mismatch')
    expected_paths={role:f'assets/{"native" if role=="native" else "models"}/precise/{t["owner_macro_id"]}/{t["id"]}/{t["id"]}{".blend" if role=="native" else "-"+role+".glb"}' for role in ('raw','web','lod','native')}
    require(t['paths']==expected_paths,'Target asset namespace is not the exact model/owner namespace')
    require(t['limits']['exclusive_per_file_bytes']==LIMIT,'File limit cannot be relaxed')
    require(t['lod_policy']['mode'] in ('compression-only','authored-subtraction'),'No automatic QEM mode')
    require(t['lod_policy']['no_automatic_qem'] is True,'Whole-model simplification forbidden')
    allowed=t['lod_policy']['allowed_omission_label_patterns']
    require(allowed==([] if t['id']=='jiading-shanghai-auto-museum' else ['(?:^|/)fine-tile-joints-[0-9]+$']),'LOD omission allowlist changed; new explicit revision required')
    for key in ('source_freeze','package_spec','raw','raw_geometry','native'):bound(t['actual'][key])
    freeze_path=bound(t['actual']['source_freeze']);freeze=load(freeze_path)
    require(freeze.get('id',freeze.get('building_id'))==t['id'] and isinstance(freeze.get('files'),list) and freeze['files'],'Actual nonempty author dependency freeze required')
    seen=set();geometry_bound=False
    for row in freeze['files']:
        if 'source' in row:dependency=bound(row)
        else:
            relative=Path(row.get('path',row.get('file','')))
            require(str(relative) not in ('','.') and not relative.is_absolute() and '..' not in relative.parts,'Frozen dependency must be canonical source-relative')
            dependency=bound({'source':str(freeze_path.parent/relative),'bytes':row['bytes'],'sha256':row['sha256']})
        require(str(dependency) not in seen,'Duplicate frozen dependency');seen.add(str(dependency))
        if dependency.name=='geometry-input.json' and row['sha256']==t['source_geometry']['sha256']:geometry_bound=True
    require(geometry_bound,'Frozen author source does not bind the exact original owner geometry')
    if t['lod_policy']['mode']=='authored-subtraction':
        for key in ('authored_lod','authored_lod_geometry'):bound(t['actual'][key])
    else:
        require(t['actual'].get('authored_lod') is None and t['actual'].get('authored_lod_geometry') is None,'Compression-only target cannot carry an unused authored LOD')
    package=load(bound(t['actual']['package_spec']))
    require(package.get('id')==t['id'] and package.get('paths')==t['paths'],'Package specification identity/paths differ')
    require(package['provenance'].get('geometry_input_sha256')==t['source_geometry']['sha256'],'Package source geometry not bound')
    require(package['provenance'].get('browser_accepted') is False,'Provenance cannot assert browser acceptance')
    return t

def upstream(project):
    project=Path(project).resolve()
    for row in load(HERE/'upstream-lock.json')['files']:
        p=project/row['project_relative']
        require(p.is_file() and p.stat().st_size==row['bytes'] and sha(p)==row['sha256'],'Frozen upstream changed: '+str(p))
        if 'snapshot' in row:
            p=HERE/row['snapshot'];require(p.stat().st_size==row['bytes'] and sha(p)==row['sha256'],'Local upstream copy changed')

def external_gltfpack(executable):
    lock=load(HERE/'external-tool-lock.json')
    require(Path(executable).resolve()==Path(lock['executable']),'Unreviewed gltfpack executable')
    for row in lock['files']:bound(row)
    return lock

