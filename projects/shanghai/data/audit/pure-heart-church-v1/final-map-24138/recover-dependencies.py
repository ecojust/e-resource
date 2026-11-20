"""Locate immutable basemap bytes and retest every URL that returned HTTP 502 on the first run."""
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import urlsplit
import hashlib,subprocess,json,os,sys
w=Path(__file__).parent;rep=json.loads((w/'post/main-browser.json').read_bytes())
base='ae55637ce1d7cbc4d21fd94934c8309aca1dcd09';repo=Path('/workspace/e-resource')
cache=Path('/tmp/shanghai-additional-inputs-15138/server-cache')/base/'objects'
roots=sorted(map(Path,json.loads((w/'peer-objects.json').read_bytes())),key=lambda p:(base not in str(p),str(p)))
def sha_blob(data):return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
records=[]
for url in sorted({f['url'] for f in rep['failed']}):
 rel=urlsplit(url).path.lstrip('/');assert not '..'in rel and rel.startswith('assets/')
 oid=subprocess.check_output(['git','-C',repo,'--no-lazy-fetch','ls-tree','--format=%(objectname)',base,'--','projects/shanghai/'+rel],text=True).strip();assert len(oid)==40
 peer=None
 for root in roots:
  p=root/rel
  if p.is_file() and sha_blob(p.read_bytes())==oid:
   peer=p.resolve();break
 records.append({'url':url,'rel':rel,'git_blob':oid,'verified_peer':str(peer)if peer else None})
(w/'cache-source-plan.json').write_text(json.dumps(records,indent=2)+'\n')
print('private peers',sum(bool(r['verified_peer'])for r in records),'/',len(records),flush=True)
if sys.argv[1]=='prepare':sys.exit()
import time
for r in records:
 dest=cache/r['rel'];peer=r['verified_peer']
 while not dest.parent.is_dir():
  try:dest.parent.mkdir(parents=True,exist_ok=True)
  except OSError as e:
   if e.errno!=28:raise
   time.sleep(.45)
for r in records:
 dest=cache/r['rel'];peer=r['verified_peer']
 if not peer and not dest.exists():
  from urllib.parse import quote
  cdn='https://raw.githack.com/ecojust/e-resource/'+base+'/projects/shanghai/'+quote(r['rel'],safe='/')
  b=Path('/dev/shm/qingxin138-final/prior-objects');b.mkdir(exist_ok=True)
  retained=b/r['git_blob']
  if not retained.exists():
   for u in [cdn,cdn.replace('raw.githack.com','raw.githubusercontent.com')]:
    try:
     with urlopen(u,timeout=20)as res:data=res.read()
     assert sha_blob(data)==r['git_blob'];temp=retained.with_suffix('.incoming');temp.write_bytes(data);os.replace(temp,retained);break
    except Exception as e:print('other immutable host',r['rel'],str(e),flush=True)
  if retained.is_file():peer=str(retained);r['retained_immutable_peer']=peer

 if peer and not dest.exists():
  dest.parent.mkdir(exist_ok=True,parents=True)
  try:os.link(peer,dest)
  except FileExistsError:pass
  except OSError as e:
   if e.errno!=18:raise
   try:dest.symlink_to(peer)
   except FileExistsError:pass
 with urlopen(r['url'],timeout=35)as res:
  data=res.read();assert res.status==200 and sha_blob(data)==r['git_blob']
 r['status']=200;r['bytes']=len(data);r['sha256']=hashlib.sha256(data).hexdigest()
(w/'cache-recovery.json').write_text(json.dumps({'baseline_commit':base,'failed_requests_in_initial_browser':len(rep['failed']),'unique_urls':len(records),'recovered':records},indent=2)+'\n')
