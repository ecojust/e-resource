from pathlib import Path
import subprocess,hashlib,os,time,json,urllib.parse,urllib.request,errno,concurrent.futures,threading,datetime
w=Path(__file__).parent;old=Path('/dev/shm/qingxin138-final');base='ae55637ce1d7cbc4d21fd94934c8309aca1dcd09';repo=Path('/workspace/e-resource');short=Path('/dev/shm/x146');short.mkdir(exist_ok=True)
oldlist=[]
import sys
inputFile=Path(sys.argv[1]);i=json.loads(inputFile.read_bytes())
rels={urllib.parse.urlsplit(r['url']).path.lstrip('/')for r in i['failed']}
roots=[Path(f'/tmp/shanghai-additional-inputs-{n}/server-cache/{base}/objects')for n in [15138,17138]]
peers=[*roots,*map(Path,json.loads((old/'peer-objects.json').read_bytes())),repo/'projects/shanghai']
def blob(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def recover(rel):
 assert rel.startswith('assets/') and '..'not in Path(rel).parts
 oid=subprocess.check_output(['git','-C',repo,'--no-lazy-fetch','ls-tree','--format=%(objectname)',base,'--','projects/shanghai/'+rel],text=True).strip();assert len(oid)==40
 peer=None
 for p in [*(r/rel for r in peers),old/'prior-objects'/oid,short/oid]:
  if p.is_file()and blob(p.read_bytes())==oid:peer=p.resolve();break
 if not peer:
  git=subprocess.run(['git','-C',repo,'--no-lazy-fetch','cat-file','blob',oid],capture_output=True);b=git.stdout
  if git.returncode or blob(b)!=oid:
   url='https://raw.githubusercontent.com/ecojust/e-resource/'+base+'/projects/shanghai/'+urllib.parse.quote(rel,safe='/')
   with urllib.request.urlopen(url,timeout=40)as r:b=r.read()
  assert blob(b)==oid;peer=short/oid;peer.write_bytes(b)
 for root in roots:
  dest=root/rel
  while not dest.is_file():
   try:
    dest.parent.mkdir(parents=True,exist_ok=True)
    if peer.stat().st_dev==dest.parent.stat().st_dev:os.link(peer,dest)
    else:
     linkto=peer
     if len(str(peer))>=60:
      linkto=short/oid
      if not linkto.exists():linkto.symlink_to(peer)
     dest.symlink_to(linkto)
   except FileExistsError:pass
   except OSError as e:
    if e.errno!=errno.ENOSPC:raise
    time.sleep(.4)
  assert blob(dest.read_bytes())==oid
 bound={}
 for port in (24145,24146):
  with urllib.request.urlopen(f'http://127.0.0.1:{port}/'+rel,timeout=50)as r:b=r.read();assert r.status==200
  assert blob(b)==oid,(port,rel)
  bound[str(port)]={'status':200,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
 print(rel,flush=True)
 return {'file':rel,'git_blob':oid,'retained':str(peer),'checked':bound}
with concurrent.futures.ThreadPoolExecutor(max_workers=4)as ex:
 records=list(ex.map(recover,sorted(rels)))
out=dict(passed=True,checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),baseline_commit=base,original_urls=len(oldlist),current_browser_unique=len({r['url']for r in i['failed']}),unique_paths=len(rels),total_actual_http_requests=len(rels)*2,ports=[24145,24146],records=records)
(Path(sys.argv[2])).write_text(json.dumps(out,indent=2)+'\n')
print('done',len(records),flush=True)
