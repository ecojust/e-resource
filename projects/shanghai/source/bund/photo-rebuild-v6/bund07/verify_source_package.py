#!/usr/bin/env python3
"""Validate curated source hashes and optionally rebuild in a clean directory."""
from pathlib import Path,PurePosixPath
import argparse,hashlib,json,os,shutil,subprocess,sys,tempfile
HERE=Path(__file__).resolve().parent

def main():
 p=argparse.ArgumentParser();p.add_argument('--rebuild',action='store_true');a=p.parse_args();manifest=json.loads((HERE/'source-package-files.json').read_text());verified=[]
 for base,entries,kind in [(HERE,manifest['files'],'building'),(HERE.parent/'common',manifest['required_sibling_sha256'],'common')]:
  for item in entries:
   name=PurePosixPath(item['path']);assert not name.is_absolute() and '..' not in name.parts
   path=base/str(name);data=path.read_bytes();assert len(data)==item['bytes'] and len(data)<100_000_000 and hashlib.sha256(data).hexdigest()==item['sha256'],name
   verified.append((kind,str(name),path))
 report={'schema':'bund07-portable-source-package-check-v1','passed':True,'source_files_verified':len(verified),'rebuild_performed':False,'expected_raw_sha256':manifest['current_asset_sha256'],'no_production_or_network_access':True}
 if a.rebuild:
  with tempfile.TemporaryDirectory(prefix='bund07-portable-refined-') as tmp:
   root=Path(tmp)
   for kind,name,path in verified:
    out=root/('bund07' if kind=='building' else 'common')/name;out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,out)
   env=dict(os.environ);env['PYTHONDONTWRITEBYTECODE']='1'
   r=subprocess.run([sys.executable,str(root/'bund07/build_model.py'),'--output',str(root/'new-output')],cwd=root,env=env,capture_output=True,text=True)
   assert r.returncode==0,r.stderr[-6000:]
   data=(root/'new-output/bund07.glb').read_bytes();sha=hashlib.sha256(data).hexdigest();assert sha==manifest['current_asset_sha256'],sha
   report.update({'rebuild_performed':True,'rebuilt_raw_sha256':sha,'rebuilt_bytes':len(data),'byte_exact':True,'dependencies':'Only curated files and named sibling common dependencies were copied; no output/native/cachedresearch/production assets copied.'})
 (HERE/'output/portable-rebuild-check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
