"""Run a selected real xuhui-empire-mansions-street-front map phase with signatures from the live origin."""
from pathlib import Path
import json,sys,hashlib,os,subprocess,datetime
from urllib.request import urlopen
w=Path(__file__).parent;project=Path('/workspace/e-resource/projects/shanghai');case=project/'data/audit/empire-mansions-v1/map-case.json'
sys.path.insert(0,'/tmp/shanghai-yongjia-porch')
from common import full
bound=json.loads((w/'bound-inputs.json').read_bytes())
phase=sys.argv[1];assert phase in ('before','phone','desktop','architecture','mouse','touch','distant')
ident='xuhui-empire-mansions-street-front';bank=Path(os.environ.get('CITY212_MATERIALIZED','/dev/shm/city-212-actual'))
import runpy
abi=runpy.run_path(str(w/'anonymous-inputs.py'))
before=phase=='before';n=211 if before else 212
fds,checks=abi['signed_inputs'](n,bound[str(n)]['origin'],full(n),ident)
try:
    if '--check-readers' in sys.argv:
        verified=subprocess.run(['node','-e',"const fs=require('node:fs'),crypto=require('node:crypto'),f=JSON.parse(process.argv[1]),r=JSON.parse(process.argv[2]);for(const [p,n] of Object.entries(f)){const b=fs.readFileSync('/proc/self/fd/'+n);if(crypto.createHash('sha256').update(b).digest('hex')!==r[p].sha256 || b.length!==r[p].bytes)process.exit(2)}",json.dumps(fds),json.dumps(checks)],pass_fds=tuple(fds.values()),check=True)
        print('served and sealed',n,len(checks),sum(x['bytes'] for x in checks.values()));sys.exit(0)
    d=w/phase;d.mkdir(exist_ok=True);tmp=bank/('profile-'+phase);tmp.mkdir(parents=True,exist_ok=True)
    k='data/candidate-city-integrations.json'
    env=dict(os.environ,SHANGHAI_PROJECT_ROOT=str(project),QA_SIGNED_INPUT_FDS=json.dumps(fds),QA_CONTROL_CATALOG='/proc/self/fd/'+str(fds[k]),QA_CONTROL_CATALOG_SHA256=bound['211']['catalog_sha256'],QA_CONTROL_CITY_COUNT='248',MODEL_BASE_URL=bound[str(n)]['origin'],QA_CDP_PORT='19412',QA_OUTPUT_DIR=str(d),TMPDIR=str(tmp),NODE_PATH='/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules')
    (d/'source-reads.json').write_text(json.dumps(dict(order=n,origin=bound[str(n)]['origin'],inputs=checks),indent=2)+'\n')
    flags=['before','--control'] if before else [phase]
    with (w/(phase+'.log')).open('wb')as out:
        result=subprocess.run(['node',w/'driver-versions'/(json.loads((w/'phase-drivers.json').read_bytes())[phase]+'.cjs'),case,*flags],env=env,stdout=out,stderr=subprocess.STDOUT,pass_fds=tuple(fds.values()))
    (w/(phase+'.exit')).write_text(str(result.returncode)+'\n');raise SystemExit(result.returncode)
finally:
    for fd in fds.values():os.close(fd)
