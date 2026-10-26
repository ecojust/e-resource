#!/usr/bin/env python3
"""Pinned Shanghai CI orchestration. No geometry changes; publishing is explicit.

The workflow defaults to a single reference macro. A reviewed mode.json change
enables 16 balanced full-build shards. Each full job calibrates its own runtime
against the same decoded reference before building/publishing its assigned list.
"""
from pathlib import Path,PurePosixPath
import argparse,collections,datetime,gzip,hashlib,importlib.metadata,json,os,platform,re,shutil,struct,subprocess,sys,tempfile,urllib.request,zlib

HERE=Path(__file__).resolve().parent
LIMIT=100_000_000
BATCH_LIMIT=400_000_000
PREFIX='projects/shanghai/assets/city-detail/macros/'
EXPECTED={'feature_count':1796419,'macro_count':1708,'protected_keys':103,'qualified_roofs':126,'renderable_exclusions':98,'residuals':401}
def need(ok,message):
    if not ok:raise RuntimeError(message)
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def sha_bytes(value):return hashlib.sha256(value).hexdigest()
def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(path):
    b=Path(path).read_bytes();return json.loads(gzip.decompress(b) if b[:2]==b'\x1f\x8b' else b)
def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(canonical(value)+b'\n')
def emit(event,**values):print(json.dumps({'event':event,**values},ensure_ascii=False,separators=(',',':')),flush=True)
def run(args,**kw):return subprocess.run([str(x) for x in args],check=True,**kw)
def safe_relative(name):
    need(isinstance(name,str) and name and '\\' not in name and all(ord(c)>=32 and ord(c)!=127 for c in name),'Unsafe relative path')
    p=PurePosixPath(name);need(not p.is_absolute() and '..' not in p.parts and not any(x.startswith('.') for x in p.parts),'Unsafe relative path '+name)
    return p
def bounded_gzip(path):
    pieces=[];total=0
    with gzip.open(path,'rb') as f:
        while True:
            piece=f.read(min(1024*1024,LIMIT-total))
            if not piece:break
            total+=len(piece);need(total<LIMIT,'Decoded file reaches 100MB: '+str(path));pieces.append(piece)
    return b''.join(pieces)
def lock():return read(HERE/'environment-lock.json')


def plan(project,mode=None):
    settings=read(HERE/'mode.json');mode=mode or settings['mode']
    need(mode in ('smoke','full'),'mode must be smoke or full')
    need(settings['workers_per_job']==2,'Frozen CI budget requires workers_per_job=2')
    baseline=read(project/'assets/city/manifest.json')
    need(sha(project/'assets/city/manifest.json')==lock()['input_hashes']['assets/city/manifest.json'],'Baseline manifest changed')
    rows=baseline['tiles'];ids=[r['id'] for r in rows]
    need(len(ids)==len(set(ids))==1708 and sum(r['building_count'] for r in rows)==1796419,'Baseline full-city conservation failed')
    count=int(settings['full_jobs']);need(1<=count<=16,'Only 1..16 standard jobs allowed')
    bins=[{'shard':i,'macro_ids':[],'building_count':0} for i in range(count)]
    # Longest-processing-time approximation, using source building counts.
    for row in sorted(rows,key=lambda r:(-r['building_count'],r['id'])):
        target=min(bins,key=lambda b:(b['building_count'],b['shard']))
        target['macro_ids'].append(row['id']);target['building_count']+=row['building_count']
    for b in bins:b['macro_ids'].sort();b['macro_list_sha256']=sha_bytes(canonical(b['macro_ids']))
    assigned=[m for b in bins for m in b['macro_ids']]
    need(len(assigned)==len(set(assigned))==1708 and set(assigned)==set(ids),'Macro assignment duplicates or omissions')
    smoke=settings['smoke_macro'];need(smoke=='14-13719-6695' and smoke in ids,'Smoke reference must remain the approved central macro')
    selected=bins if mode=='full' else [{'shard':0,'macro_ids':[smoke],'building_count':next(r['building_count'] for r in rows if r['id']==smoke),'macro_list_sha256':sha_bytes(canonical([smoke]))}]
    return {'mode':mode,'configuration_sha256':lock()['configuration_sha256'],'full_assignment':bins,
            'full_assignment_sha256':sha_bytes(canonical(bins)),'selected':selected,
            'matrix':{'include':[{'shard':b['shard'],'mode':mode} for b in selected]},
            'full_coverage':{'macros':1708,'features':1796419,'unique':True},
            'load_min':min(b['building_count'] for b in bins),'load_max':max(b['building_count'] for b in bins)}


def selected(plan_,shard):
    rows=[r for r in plan_['selected'] if r['shard']==shard];need(len(rows)==1,'Unknown shard for selected mode');return rows[0]['macro_ids']


def input_paths(project,ids):
    env=lock();paths=set(env['input_hashes'])
    paths.update(['source/city/build_district_models.py','source/city/roof_geometry.py'])
    heights=read(project/'data/heights/height_sources_lock.json')
    for f in heights['files']:paths.add(('source/city/' if f['path'].endswith('.py') else 'data/heights/')+f['path'])
    for macro in ids:
        z,x,y=macro.split('-');paths.update([f'assets/city/records/{macro}.json',f'assets/city/state/{macro}.json',f'data/fullcity-raw/tiles/{z}/{x}/{y}.geojson.gz'])
    return sorted(paths)


def sparse_inputs(project,mode,shard,apply=False):
    p=plan(project,mode);ids=selected(p,shard)
    # Calibration is not an assigned/published extra macro in full mode.
    inputs=sorted(set(ids)|{read(HERE/'mode.json')['smoke_macro']})
    paths=input_paths(project,inputs)
    patterns=['/.github/workflows/shanghai-v5-build.yml','/projects/shanghai/ci/v5/**']+['/projects/shanghai/'+s for s in paths]
    if apply:
        repository=project.parents[1]
        run(['git','sparse-checkout','set','--no-cone','--stdin'],cwd=repository,input=('\n'.join(patterns)+'\n').encode())
        for f in paths:need((project/f).is_file(),'Sparse input missing '+f)
    return {'shard':shard,'mode':mode,'assigned_macros':ids,'calibration_macro':read(HERE/'mode.json')['smoke_macro'],'project_files':paths,'sparse_patterns':patterns,'forbidden_old_glbs_in_inputs':any(x.endswith('.glb') for x in paths)}


def environment_check(library=None):
    env=lock();actual={'python':platform.python_version(),'python_compiler':platform.python_compiler(),'platform':platform.platform(),'machine':platform.machine(),
        'zlib':{'compile':zlib.ZLIB_VERSION,'runtime':zlib.ZLIB_RUNTIME_VERSION},'packages':{n:importlib.metadata.version(n) for n in env['required_python_packages']}}
    need(actual['python']=='3.12.14' and actual['machine']=='x86_64','Requires CPython 3.12.14 on x86_64')
    need(actual['packages']==env['required_python_packages'],'Installed Python package versions differ from pinned local versions')
    import shapely,rasterio,pyproj,pyarrow
    actual.update(geos=shapely.geos_version_string,gdal=rasterio.__gdal_version__,proj=pyproj.proj_version_str,pyarrow_cpp=pyarrow.cpp_version)
    for name in ('geos','gdal','proj','pyarrow_cpp'):need(actual[name]==env[name],f'Native {name} differs: {actual[name]} != {env[name]}')
    actual['node']=run(['node','--version'],capture_output=True,text=True).stdout.strip()
    actual['npm']=run(['npm','--version'],capture_output=True,text=True).stdout.strip()
    need(actual['node']==env['node'] and actual['npm']==env['npm'],'Node/npm differs from the pinned local toolchain')
    package=Path(library).parent if library else HERE/'tooling/node_modules/gltfpack'
    for name,expected in env['gltfpack']['sha256'].items():need(sha(package/name)==expected,'gltfpack bytes differ: '+name)
    for name,expected in env['frozen_scripts'].items():need(sha(HERE/'freeze-v6'/name)==expected,'Frozen source changed: '+name)
    actual['gltfpack_sha256']={n:sha(package/n) for n in env['gltfpack']['sha256']}
    actual['gzip_environment_same_as_local']=actual['zlib']==env['zlib']
    return actual


def install_npm():
    expected=lock()['npm_tarball']
    need(expected['url']=='https://registry.npmjs.org/npm/-/npm-11.9.0.tgz','Unexpected npm source')
    with urllib.request.urlopen(expected['url'],timeout=60) as response:data=response.read(expected['bytes']+1)
    need(len(data)==expected['bytes'] and sha_bytes(data)==expected['sha256'],'npm tarball bytes differ')
    with tempfile.TemporaryDirectory(prefix='shanghai-npm-') as temp:
        path=Path(temp)/'npm.tgz';path.write_bytes(data)
        run(['npm','install','--global',path,'--ignore-scripts','--no-audit','--no-fund'])
    need(run(['npm','--version'],capture_output=True,text=True).stdout.strip()==expected['version'],'Pinned npm installation failed')


def glb_check(data):
    need(28<=len(data)<LIMIT,'Invalid decoded GLB size')
    need(struct.unpack_from('<4sII',data)==(b'glTF',2,len(data)),'Invalid GLB header')
    size,kind=struct.unpack_from('<II',data,12);need(kind==0x4e4f534a and 20+size<=len(data),'Invalid GLB JSON')
    g=json.loads(data[20:20+size]);need(g.get('meshes'),'GLB has no geometry')
    for resource in g.get('buffers',[])+g.get('images',[]):need('uri' not in resource,'External GLB dependency')
    total=0
    for node in g.get('nodes',[]):
        if 'mesh' not in node:continue
        attrs=node.get('extensions',{}).get('EXT_mesh_gpu_instancing',{}).get('attributes',{})
        counts={g['accessors'][a]['count'] for a in attrs.values()};need(len(counts)<=1,'Instance count mismatch')
        count=next(iter(counts)) if counts else 1
        for primitive in g['meshes'][node['mesh']]['primitives']:
            need(primitive.get('mode',4)==4,'Non-triangle primitive')
            a=g['accessors'][primitive['indices']];need(a['count']%3==0,'Invalid triangle indices');total+=count*a['count']//3
    return total


def validate_output(output,ids):
    env=lock();configuration=read(output/'build-configuration.json')
    need(sha_bytes(canonical(configuration))==env['configuration_sha256'],'Geometry configuration changed')
    ready_paths=list((output/'macros').glob('*/READY.json'))
    need({p.parent.name for p in ready_paths}==set(ids),'Missing or extra READY macros in job output')
    records=[];files=[];all_features=set();expected_config=env['configuration_sha256']
    for macro in sorted(ids):
        root=output/'macros'/macro;rp=root/'READY.json';r=read(rp)
        need(r.get('complete') is True and r['id']==macro and r['configuration_sha256']==expected_config,'Invalid READY '+macro)
        actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and p!=rp}
        need(actual==set(r['published_files']),'Untracked/missing files in '+macro)
        for name,meta in sorted(r['published_files'].items()):
            safe_relative(name);path=root/name;need(not path.is_symlink(),'Symlink output')
            need(0<path.stat().st_size<LIMIT and path.stat().st_size==meta['bytes'] and sha(path)==meta['sha256'],'Published bytes/SHA mismatch '+str(path))
            files.append({'path':PREFIX+macro+'/'+name,'source':str(path.resolve()),'bytes':meta['bytes'],'sha256':meta['sha256']})
        table=read(root/r['feature_table_file']);n=r['feature_count'];need(table['keys'][0] is None and len(table['keys'])==n+1,'Feature table size')
        keys=table['keys'][1:];need(len(set(keys))==n and not(set(keys)&all_features),'Duplicate feature key');all_features.update(keys)
        owners=[]
        for t in r['near']:
            p=root/t['file'];need(t['bytes']==t['size_bytes']==p.stat().st_size and t['sha256']==sha(p),'Near stored byte metadata mismatch');need(t['content_encoding']=='gzip' and t['file'].endswith('.glb.gz'),'Unexpected near encoding')
            data=bounded_gzip(p);need(len(data)==t['decoded_size_bytes'] and sha_bytes(data)==t['decoded_sha256'],'Decoded bytes/SHA mismatch')
            need(glb_check(data)==t['triangles']==t['expandedTriangles'],'Expanded triangle count mismatch')
            owners.extend(t['featureLocalIds'])
        need(len(owners)==n and set(owners)==set(range(1,n+1)),'Near ownership incomplete/duplicated')
        far=(root/r['far']['file']).read_bytes();need(glb_check(far)==r['far']['triangles'],'Far triangles mismatch')
        need(0<rp.stat().st_size<LIMIT,'Oversized READY')
        files.append({'path':PREFIX+macro+'/READY.json','source':str(rp.resolve()),'bytes':rp.stat().st_size,'sha256':sha(rp)})
        records.append(r)
    return {'configuration_sha256':expected_config,'macro_ids':sorted(ids),'macro_list_sha256':sha_bytes(canonical(sorted(ids))),
            'features':len(all_features),'files':files,'total_bytes':sum(x['bytes'] for x in files),'READY_sha256':{r['id']:sha(output/'macros'/r['id']/'READY.json') for r in records}}


def compare_smoke(output):
    expected=read(HERE/'smoke-reference.json');macro=expected['macro_id'];audit=validate_output(output,[macro]);root=output/'macros'/macro;r=read(root/'READY.json')
    need(set(r['published_files'])==set(expected['published_files']),'Smoke asset layout differs')
    differences=[]
    for name,e in expected['published_files'].items():
        p=root/name;actual_sha=sha(p)
        if name.endswith('.gz'):
            decoded=bounded_gzip(p)
            need(len(decoded)==e['decoded_size_bytes'] and sha_bytes(decoded)==e['decoded_sha256'],'Smoke decoded payload differs: '+name)
            if actual_sha!=e['sha256']:
                header=p.read_bytes()[:10];need(header[:4]==b'\x1f\x8b\x08\x00' and header[4:8]==b'\0'*4,'Unexpected nondeterministic gzip header')
                differences.append({'file':name,'local_sha256':e['sha256'],'remote_sha256':actual_sha,'local_bytes':e['bytes'],'remote_bytes':p.stat().st_size})
        else:
            need(actual_sha==e['sha256'] and p.stat().st_size==e['bytes'],'Smoke uncompressed asset differs: '+name)
    actual_zlib={'compile':zlib.ZLIB_VERSION,'runtime':zlib.ZLIB_RUNTIME_VERSION}
    need(not differences or actual_zlib!=lock()['zlib'],'Gzip bytes differ under the identical frozen zlib runtime')
    # The only exempt READY aggregate is exactly the stored gzip byte sum.
    for key,value in expected['stable_READY'].items():
        if key=='near_total_bytes':continue
        need(r.get(key)==value,'Smoke stable READY field differs: '+key)
    need(r['near_total_bytes']==sum(t['size_bytes'] for t in r['near']),'Stored near byte aggregate invalid')
    expected_near={t['file']:t for t in expected['near']}
    for t in r['near']:
        e=expected_near[t['file']]
        for key,value in e.items():
            if key not in ('bytes','size_bytes','sha256'):need(t.get(key)==value,'Smoke near metadata differs: '+t['file']+'/'+key)
    return {'passed':True,'status':'byte_exact' if not differences else 'decoded_exact_gzip_container_difference',
        'far_GLBS_byte_exact':True,'decoded_near_GLBS_byte_exact':500,'source_geometry_properties_heights_exact':True,
        'configuration_sha256':audit['configuration_sha256'],'gzip_container_differences':differences,'zlib':actual_zlib,
        'local_near_stored_bytes':expected['stable_READY']['near_total_bytes'],'remote_near_stored_bytes':r['near_total_bytes']}


def build(project,output,mode,shard,summary):
    need(not output.exists(),'Use a new CI output directory')
    p=plan(project,mode);ids=selected(p,shard);environment=environment_check()
    package=HERE/'tooling/node_modules/gltfpack';settings=read(HERE/'mode.json')
    def generate(target,macros,workers):
        run([sys.executable,HERE/'freeze-v6/build_city_v5.py','--project',project,'--output',target,
             '--macros',','.join(macros),'--gltfpack',package/'cli.js','--gltfpack-library',package/'library.js',
             '--workers',str(workers),'--target-triangles','180000','--microcell-m','250.0'])
    if mode=='full':
        calibration=output.with_name(output.name+'-calibration')
        need(not calibration.exists(),'Calibration directory already exists')
        generate(calibration,[settings['smoke_macro']],1);smoke=compare_smoke(calibration);shutil.rmtree(calibration)
    else:smoke=None
    generate(output,ids,int(settings['workers_per_job']))
    result=validate_output(output,ids)
    if mode=='smoke':smoke=compare_smoke(output)
    result.update(mode=mode,shard=shard,environment=environment,smoke=smoke,assignment_sha256=p['full_assignment_sha256'])
    write(summary,result)
    emit('SHANGHAI_V5_BUILD_VALIDATED',mode=mode,shard=shard,macros=len(ids),macro_list_sha256=result['macro_list_sha256'],files=len(result['files']),bytes=result['total_bytes'],smoke_status=smoke['status'],gzip_container_difference_count=len(smoke['gzip_container_differences']),environment=environment)


def git_environment(extra=None):
    # Retain checkout's repository-local credential header, but never inherit
    # injected Git config, alternate object databases, global URL rewrites, etc.
    env={k:v for k,v in os.environ.items() if not k.startswith('GIT_')}
    env.update(GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull,GIT_CONFIG_SYSTEM=os.devnull)
    if extra:
        allowed={'GIT_INDEX_FILE','GIT_AUTHOR_NAME','GIT_AUTHOR_EMAIL','GIT_COMMITTER_NAME','GIT_COMMITTER_EMAIL'}
        need(set(extra)<=allowed,'Unexpected explicit Git environment override');env.update(extra)
    return env

def git(repo,args,*,env=None,input=None):
    return run(['git','-c','core.hooksPath=/dev/null','-c','remote.origin.mirror=false','-c','push.followTags=false',*args],cwd=repo,env=git_environment(env),input=input,capture_output=True).stdout.decode().strip()

def assert_remote(repo):
    allowed={'https://github.com/ecojust/e-resource','https://github.com/ecojust/e-resource.git'}
    for opts in (['--all'],['--push','--all']):
        urls=git(repo,['remote','get-url',*opts,'origin']).splitlines()
        need(len(urls)==1 and urls[0] in allowed,'Effective origin fetch/push URL is not the approved repository')

def remote_head(repo,branch):
    value=git(repo,['ls-remote','origin','refs/heads/'+branch]);return value.split()[0] if value else None


def publish(repo,summary,push=False):
    need(push,'Publishing requires explicit --push; this command is not a planning step')
    need(os.environ.get('GITHUB_ACTIONS')=='true' and os.environ.get('GITHUB_REPOSITORY')=='ecojust/e-resource','Publish only in the intended GitHub Actions repository')
    need(os.environ.get('GITHUB_REF')=='refs/heads/codex/shanghai-v5-build','Publishing source branch is restricted')
    assert_remote(repo)
    report=read(summary);need(report['smoke']['passed'],'Missing successful actual smoke')
    base=os.environ['GITHUB_SHA'];run_id=os.environ['GITHUB_RUN_ID'];shard=int(report['shard'])
    need(re.fullmatch(r'[0-9a-f]{40}',base) and run_id.isdigit() and 0<=shard<16,'Invalid CI identity')
    branch=f'codex/shanghai-v5-assets-{run_id}-{shard:02d}'
    need(git(repo,['rev-parse','HEAD'])==base,'Checkout must remain at the exact triggering commit')
    need(remote_head(repo,branch) is None,'Target assets branch already exists; start a new run instead of overwriting it')
    files=report['files'];need(files and len({f['path'] for f in files})==len(files),'Empty/duplicate upload list')
    need(report['configuration_sha256']==lock()['configuration_sha256'],'Publish configuration changed')
    need(report['macro_ids']==sorted(set(report['macro_ids'])) and report['macro_list_sha256']==sha_bytes(canonical(report['macro_ids'])),'Publish macro list/hash mismatch')
    need(report['total_bytes']==sum(f['bytes'] for f in files),'Publish byte aggregate mismatch')
    need({f['path'] for f in files if f['path'].endswith('/READY.json')}=={PREFIX+m+'/READY.json' for m in report['macro_ids']},'Publish READY set mismatch')
    existing=set(git(repo,['ls-tree','-r','--name-only',base,'--',PREFIX]).splitlines())
    for f in files:
        safe_relative(f['path']);need(f['path'].startswith(PREFIX) and f['path'].split('/')[5] in report['macro_ids'],'Upload outside assigned macros')
        need(f['path'] not in existing,'Immutable asset already exists in build base: '+f['path'])
        source=Path(f['source']);need(all(ord(c)>=32 and ord(c)!=127 for c in str(source)),'Unsafe source path');need(source.is_file() and not source.is_symlink() and 0<f['bytes']<LIMIT and source.stat().st_size==f['bytes'] and sha(source)==f['sha256'],'Upload input changed')
    # Assets precede their READY marker. No global manifest/config/HTML is staged.
    files.sort(key=lambda f:(f['path'].split('/')[5],f['path'].endswith('/READY.json'),f['path']))
    batches=[];current=[];size=0
    for f in files:
        if current and size+f['bytes']>BATCH_LIMIT:batches.append(current);current=[];size=0
        current.append(f);size+=f['bytes']
    if current:batches.append(current)
    commits=[];parent=base
    with tempfile.TemporaryDirectory(prefix='shanghai-git-index-') as temp:
        env={'GIT_INDEX_FILE':str(Path(temp)/'index')}
        env.update(GIT_AUTHOR_NAME='github-actions[bot]',GIT_AUTHOR_EMAIL='41898282+github-actions[bot]@users.noreply.github.com',GIT_COMMITTER_NAME='github-actions[bot]',GIT_COMMITTER_EMAIL='41898282+github-actions[bot]@users.noreply.github.com')
        git(repo,['read-tree',base],env=env)
        for number,batch in enumerate(batches,1):
            expected_remote=None if number==1 else parent
            need(remote_head(repo,branch)==expected_remote,'Assets branch moved outside this job')
            oids=git(repo,['hash-object','-w','--no-filters','--stdin-paths'],input=('\n'.join(f['source'] for f in batch)+'\n').encode()).splitlines()
            need(len(oids)==len(batch),'Git blob write count mismatch')
            cat=subprocess.Popen(['git','cat-file','--batch'],cwd=repo,env=git_environment(),stdin=subprocess.PIPE,stdout=subprocess.PIPE)
            try:
                for f,oid in zip(batch,oids):
                    need(re.fullmatch(r'[0-9a-f]{40}',oid),'Invalid blob object ID')
                    cat.stdin.write((oid+'\n').encode());cat.stdin.flush();header=cat.stdout.readline().decode().split()
                    need(header==[oid,'blob',str(f['bytes'])],'Actual Git blob size/type differs')
                    remaining=f['bytes'];digest=hashlib.sha256()
                    while remaining:
                        chunk=cat.stdout.read(min(1024*1024,remaining));need(chunk,'Truncated Git blob');digest.update(chunk);remaining-=len(chunk)
                    need(cat.stdout.read(1)==b'\n' and digest.hexdigest()==f['sha256'],'Actual Git blob SHA differs')
                    need(Path(f['source']).stat().st_size==f['bytes'] and sha(Path(f['source']))==f['sha256'],'Source changed during blob import')
            finally:
                cat.stdin.close();cat.wait(timeout=30);cat.stdout.close()
            entries=''.join(f'100644 {oid}\t{f["path"]}\n' for f,oid in zip(batch,oids))
            git(repo,['update-index','--add','--index-info'],env=env,input=entries.encode())
            # Existing base blobs may be promisor-missing; all added blobs were verified above.
            tree=git(repo,['write-tree','--missing-ok'],env=env)
            message=f'Shanghai v5 {report["mode"]} run {run_id} shard {shard:02d} assets {number}/{len(batches)}\n'
            commit=git(repo,['commit-tree',tree,'-p',parent],env=env,input=message.encode())
            # No force and no master update. Official checkout credentials apply.
            assert_remote(repo)
            git(repo,['push','origin',commit+':refs/heads/'+branch])
            need(remote_head(repo,branch)==commit,'Remote tip did not match accepted batch commit')
            commits.append(commit);parent=commit
            emit('SHANGHAI_V5_ASSETS_BATCH',branch=branch,commit=commit,batch=number,batches=len(batches),files=len(batch),bytes=sum(f['bytes'] for f in batch))
    final={'branch':branch,'tip':parent,'base':base,'run_id':run_id,'shard':shard,'mode':report['mode'],
           'macro_ids':report['macro_ids'],'macro_list_sha256':report['macro_list_sha256'],'assignment_sha256':report['assignment_sha256'],
           'configuration_sha256':report['configuration_sha256'],'files':len(files),'bytes':report['total_bytes'],'commits':commits,
           'smoke_status':report['smoke']['status'],'decoded_smoke_exact':True,'gzip_container_difference_count':len(report['smoke']['gzip_container_differences'])}
    emit('SHANGHAI_V5_ASSETS_COMPLETE',**final)
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'],'a') as f:f.write('```json\n'+json.dumps({'event':'SHANGHAI_V5_ASSETS_COMPLETE',**final},indent=2)+'\n```\n')


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    for name in ('plan','inputs','build'):
        s=sub.add_parser(name);s.add_argument('--project',type=Path,required=True);s.add_argument('--mode',choices=['smoke','full'])
        if name!='plan':s.add_argument('--shard',type=int,required=True)
        if name=='plan':s.add_argument('--output',type=Path);s.add_argument('--github-output',type=Path)
        if name=='inputs':s.add_argument('--apply-sparse',action='store_true');s.add_argument('--output',type=Path)
        if name=='build':s.add_argument('--output',type=Path,required=True);s.add_argument('--summary',type=Path,required=True)
    s=sub.add_parser('environment');s.add_argument('--library',type=Path)
    sub.add_parser('install-npm')
    s=sub.add_parser('smoke-check');s.add_argument('--output',type=Path,required=True)
    s=sub.add_parser('publish');s.add_argument('--repo',type=Path,required=True);s.add_argument('--summary',type=Path,required=True);s.add_argument('--push',action='store_true')
    a=p.parse_args()
    if a.command=='plan':
        r=plan(a.project.resolve(),a.mode)
        if a.output:write(a.output,r)
        if a.github_output:
            with a.github_output.open('a') as f:f.write('matrix='+json.dumps(r['matrix'],separators=(',',':'))+'\n')
        emit('SHANGHAI_V5_PLAN',mode=r['mode'],matrix=r['matrix'],full_coverage=r['full_coverage'],load_min=r['load_min'],load_max=r['load_max'],assignment_sha256=r['full_assignment_sha256'])
    elif a.command=='inputs':
        r=sparse_inputs(a.project.resolve(),a.mode,a.shard,a.apply_sparse)
        if a.output:write(a.output,r)
        emit('SHANGHAI_V5_INPUTS',mode=r['mode'],shard=a.shard,macros=len(r['assigned_macros']),files=len(r['project_files']),old_GLBS=False)
    elif a.command=='install-npm':install_npm()
    elif a.command=='environment':emit('SHANGHAI_V5_ENVIRONMENT',**environment_check(a.library))
    elif a.command=='smoke-check':emit('SHANGHAI_V5_SMOKE_CHECK',**compare_smoke(a.output.resolve()))
    elif a.command=='build':build(a.project.resolve(),a.output.resolve(),a.mode,a.shard,a.summary.resolve())
    elif a.command=='publish':publish(a.repo.resolve(),a.summary.resolve(),a.push)
if __name__=='__main__':main()
