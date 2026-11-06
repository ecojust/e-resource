#!/usr/bin/env python3
"""One private audit server; frozen public-city bytes verified by Git blob."""
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import unquote,urlsplit,quote
from urllib.request import Request,urlopen
import hashlib,json,mimetypes,subprocess,threading,time,shutil
import os
REPO=Path(os.environ.get('SHANGHAI_REPO_ROOT','/workspace/e-resource')).resolve()
ROOT=REPO/'projects/shanghai'
BASE=os.environ.get('QA_BASELINE_COMMIT','c59174528765c104f09295ef10132b4bb4f63ce5')
WORK=Path(os.environ.get('QA_WORK_DIR','/workspace/shanghai-postal-qa')).resolve()
CACHE=WORK/'server-cache'/BASE
OLD_CACHES=[Path(p) for p in json.loads(os.environ.get('QA_PRIOR_CACHE_DIRS','[]'))]
source_file=os.environ.get('QA_SOURCE_BINDINGS')
EXTRA={b['repository_path'].removeprefix('projects/shanghai/'):Path(b['private_path']) for b in json.loads(Path(source_file).read_text())} if source_file and Path(source_file).is_file() else {}
LOCK=threading.Lock();PATH_LOCKS={};TREE={};LOG=CACHE/'served.jsonl';NETWORK=threading.Semaphore(3)
def identity(rel):
 with LOCK:
  if rel in TREE:return TREE[rel]
 text=subprocess.check_output(['git','--no-lazy-fetch','ls-tree',BASE,'--','projects/shanghai/'+rel],cwd=REPO,text=True).strip()
 value=text.split()[2] if text else None
 with LOCK:TREE[rel]=value
 return value
def blob(data):return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
def baseline(rel):
 with LOCK:path_lock=PATH_LOCKS.setdefault(rel,threading.Lock())
 with path_lock:
  expected=identity(rel)
  if not expected:raise FileNotFoundError(rel)
  dst=CACHE/'objects'/rel;receipt=dst.with_name(dst.name+'.receipt.json')
  if dst.is_file():
   data=dst.read_bytes();assert blob(data)==expected,rel
   return dst,'git-blob-verified-cache:'+BASE
  dst.parent.mkdir(parents=True,exist_ok=True);local=ROOT/rel
  data=None;origin=None;url=None
  for p,label in [(local,'working-tree-baseline-city'),(EXTRA.get(rel,Path('/nonexistent-qa-source')),'current-source-mapping-cache')]+[(p/rel,'prior-private-cache') for p in OLD_CACHES]:
   if p.is_file():
    candidate=p.read_bytes()
    if blob(candidate)==expected:data=candidate;origin=label;break
  if data is None:
   run=subprocess.run(['git','--no-lazy-fetch','show',BASE+':projects/shanghai/'+rel],cwd=REPO,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
   if run.returncode==0:data=run.stdout;origin='local-git-object'
  if data is None:
   url='https://raw.githack.com/ecojust/e-resource/'+BASE+'/projects/shanghai/'+quote(rel,safe='/')
   with NETWORK:
    with urlopen(Request(url,headers={'User-Agent':'Shanghai-model-publication-check/1.0'}),timeout=90) as response:
     assert response.status==200;data=response.read()
   origin='immutable-public-http'
  actual=blob(data);assert actual==expected,'Frozen blob mismatch: '+rel
  tmp=dst.with_name(dst.name+'.tmp');tmp.write_bytes(data);tmp.replace(dst)
  receipt.write_text(json.dumps({'path':rel,'baseline_commit':BASE,'git_blob':expected,'actual_git_blob':actual,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'origin':origin,'url':url})+'\n')
  return dst,'git-blob-verified-'+origin+':'+BASE
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_HEAD(self):self.serve(False)
 def do_GET(self):self.serve(True)
 def serve(self,content):
  rel=unquote(urlsplit(self.path).path).lstrip('/') or 'index.html';requested=(ROOT/rel).resolve()
  if not requested.is_relative_to(ROOT):self.send_error(403);return
  if rel=='qa-blank.html':
   data=b'<!doctype html><meta charset="utf-8"><title>Private clip GPU fixture</title><link rel="icon" href="data:,">'
   self.send_response(200);self.send_header('Content-Type','text/html');self.send_header('Content-Length',str(len(data)));self.end_headers()
   if content:self.wfile.write(data)
   return
  try:
   if rel.startswith('assets/city-detail/macros/') or not requested.is_file():requested,origin=baseline(rel)
   else:origin='working-tree'
  except FileNotFoundError:self.send_error(404);return
  except Exception as error:
   CACHE.mkdir(parents=True,exist_ok=True)
   with LOCK:
    with (CACHE/'server-errors.jsonl').open('a') as f:f.write(json.dumps({'path':rel,'error':str(error),'at':time.time()})+'\n')
   self.send_error(502,'Frozen baseline retrieval failed');return
  data=requested.read_bytes();size=len(data);start=0;end=size-1;ranged=False;value=self.headers.get('Range','')
  if value.startswith('bytes=') and ',' not in value:
   try:
    a,b=value[6:].split('-');start=int(a) if a else max(0,size-int(b));end=min(int(b) if b else size-1,size-1) if a else size-1
    if start>end or start>=size:raise ValueError()
    ranged=True
   except ValueError:self.send_error(416);return
  sha=hashlib.sha256(data).hexdigest();self.send_response(206 if ranged else 200)
  for k,v in [('Content-Type',mimetypes.guess_type(rel)[0] or 'application/octet-stream'),('Content-Length',str(end-start+1 if size else 0)),('Cache-Control','no-cache'),('Accept-Ranges','bytes'),('X-Audit-Origin',origin),('X-Audit-SHA256',sha)]:self.send_header(k,v)
  if ranged:self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
  self.end_headers()
  try:
   if content:self.wfile.write(data[start:end+1])
  except (BrokenPipeError,ConnectionResetError):pass
  with LOCK:
   with LOG.open('a') as f:f.write(json.dumps({'at':time.time(),'path':rel,'origin':origin,'bytes':size,'sha256':sha,'status':206 if ranged else 200})+'\n')
if __name__=='__main__':
 assert subprocess.check_output(['git','rev-parse',BASE+'^{commit}'],cwd=REPO,text=True).strip()==BASE
 CACHE.mkdir(parents=True,exist_ok=True)
 import os
 (WORK/'server-pid.txt').write_text(str(os.getpid())+'\n')
 ThreadingHTTPServer(('127.0.0.1',int(os.environ.get('QA_HTTP_PORT','8784'))),Handler).serve_forever()
