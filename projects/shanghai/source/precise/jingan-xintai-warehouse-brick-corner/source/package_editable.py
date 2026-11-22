"""Create and separately reopen the editable warehouse, verify its UVs and render with Cycles."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,tempfile,time
from build_model import META,PALETTE,ID,SOURCE,PROJECT,Builder,add_building
from package_architectural_model import group_parts

def sha(path):
    with Path(path).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(path,data):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def package(asset_dir,audit,assets,blender,oidn,magick):
    blend=asset_dir/(ID+'.blend');raw=asset_dir/assets['raw']['file'];assert sha(raw)==assets['raw']['sha256']
    audit.mkdir(exist_ok=True,parents=True)
    builder=Builder(PALETTE);add_building(builder,False);groups=group_parts(builder)
    for name,group in groups.items():
        parts=[p for p in builder.parts if p['label']==name]
        group['uv']=(sum([p.get('texcoords',[[0,0]for _ in p['vertices']]) for p in parts],[])
                     if any('texcoords'in p for p in parts) else None)
    events=[]
    def execute(stage,args,env):
        path=audit/(stage+'.log');start=time.time()
        with path.open('wb')as output:
            cmd=['taskset','-c',str(min(os.sched_getaffinity(0))),*map(str,args)]
            p=subprocess.Popen(cmd,env=env,stdout=output,stderr=subprocess.STDOUT);pid=p.pid;code=p.wait()
        events.append(dict(stage=stage,pid=pid,exit_code=code,started=start,finished=time.time(),log_sha256=sha(path)))
        write(audit/'native-events.json',events)
        if code:raise subprocess.CalledProcessError(code,cmd)
    with tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR') or None)as temp:
        tmp=Path(temp);groupfile=tmp/'mesh-groups.json'
        write(groupfile,dict(groups=groups,palette=builder.palette,scope=META['scope'],center=[3.75,5.70,-.425],size=[7.77,11.4,1.39]))
        image=tmp/'cycles.png';preview=audit/'native-preview.png'
        env={**os.environ,'TMPDIR':temp,'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','CUDA_VISIBLE_DEVICES':'','PAGE_NATIVE_SOURCE':str(groupfile),
             'PAGE_NATIVE_UV':str(audit/'native-uv.json'),'XINTAI_RENDER':str(image)}
        base=[blender,'-b','-t','1','--python-exit-code','1']
        execute('blender-create',[*base,'--python',SOURCE/'create_editable.py','--',groupfile,blend],env)
        execute('blender-reopen',[*base,'--python',PROJECT/'tools/verify_editable_model.py','--python',SOURCE/'verify_texture_and_render.py','--',blend,raw,audit/'native-surfaces.json'],env)
        assert json.loads((audit/'native-surfaces.json').read_bytes())['match_raw']
        execute('convert',[magick,image,'-colorspace','sRGB','-endian','LSB',tmp/'in.pfm'],env)
        if Path(oidn).is_absolute():
            env['LD_LIBRARY_PATH']=str(Path(oidn).resolve().parents[1]/'lib')+':'+env.get('LD_LIBRARY_PATH','')
        execute('oidn',[oidn,'-d','cpu','--threads','1','--ldr',tmp/'in.pfm','--srgb','-o',tmp/'filtered.pfm'],env)
        execute('preview',[magick,tmp/'filtered.pfm','-set','colorspace','sRGB','-depth','8',preview],env)
        uv=json.loads((audit/'native-uv.json').read_bytes());surfaces=json.loads((audit/'native-surfaces.json').read_bytes())
        assert uv['passed'] and surfaces['mesh_count']==len(groups) and surfaces['triangles']==assets['raw']['triangles']
        assets['native']=dict(file=blend.name,bytes=blend.stat().st_size,sha256=sha(blend))
        write(asset_dir/'manifest.json',{**META,'model_id':ID,'assets':assets})
        write(audit/'geometry-native.json',dict(id=ID,passed=True,editable_meshes=len(groups),materials=surfaces['materials'],faces=surfaces['triangles'],
              native_reopened_and_compared=surfaces,uv=uv,samples=24,render='Cycles, CPU, 512 × 576, reopened Blender scene, OIDN RT sRGB',
              source_render_sha256=sha(image),preview_sha256=sha(preview),manifest_sha256=sha(asset_dir/'manifest.json'),
              assets=assets))
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True);parser.add_argument('--audit',type=Path,required=True);parser.add_argument('--mesh-manifest',type=Path,required=True)
    parser.add_argument('--blender',default='blender');parser.add_argument('--oidn',default='oidnDenoise');parser.add_argument('--magick',default='magick')
    args=parser.parse_args();package(args.out.resolve(),args.audit.resolve(),json.loads(args.mesh_manifest.read_bytes()),args.blender,args.oidn,args.magick)
