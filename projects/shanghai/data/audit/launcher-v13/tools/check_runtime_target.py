#!/usr/bin/env python3
"""Compare actual archive bytes against current runtime baseline and installed Yangpu target."""
from __future__ import annotations
import argparse,hashlib,json,zipfile
from pathlib import Path

def h(b):return hashlib.sha256(b).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive',type=Path,required=True);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--project',type=Path,required=True);p.add_argument('--expected-commit',required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
 assert not a.report.exists(), 'Preserve prior review'
 baseline=json.loads(a.baseline.read_text());assert baseline['file_count']==len(baseline['files'])==31
 rows=[]
 with zipfile.ZipFile(a.archive) as z:
  manifest=json.loads(z.read('shanghai/LAUNCHER-MANIFEST.json'))
  assert manifest['commit']==a.expected_commit and not manifest.get('candidate_only')
  assert manifest['landmark_count']==31 and manifest['bundled_landmark_count']==14 and manifest['streamed_landmark_count']==17
  for expected in baseline['files']:
   name=expected['file'];b=z.read('shanghai/'+name);local=(a.project/name).read_bytes()
   assert {'file':name,'bytes':len(b),'sha256':h(b)}==expected
   assert b==local
   rows.append(expected)
  nav=json.loads(z.read('shanghai/data/landmarks.json'));live=json.loads((a.project/'data/landmarks.json').read_text())
  item=next(r for r in nav if r['id']=='yangpu-library');main_item=next(r for r in live if r['id']=='yangpu-library')
  assert item['accepted'] is True and item['pending_stages']==[] and not item.get('candidate_only')
  prefix=f'https://rawcdn.githack.com/ecojust/e-resource/{a.expected_commit}/projects/shanghai/'
  def localize(v):
   if isinstance(v,dict):return {k:localize(x) for k,x in v.items()}
   if isinstance(v,list):return [localize(x) for x in v]
   return v[len(prefix):] if isinstance(v,str) and v.startswith(prefix) else v
  assert localize(item)==main_item, 'Archived new target differs after URL normalization'
  assets=[]
  for role in ('raw','web','lod','native'):
   entry=main_item['assets'][role];b=(a.project/entry['file']).read_bytes()
   assert len(b)==entry['bytes']<100_000_000 and h(b)==entry['sha256']
   assert item['assets'][role]['file']==prefix+entry['file']
   assets.append({'role':role,**entry,'actual_installed_bytes_verified':True})
  result={'schema':'yangpu-launcher-runtime-target-actual-v13','passed':True,'expected_commit':a.expected_commit,
   'archive':str(a.archive.resolve()),'archive_bytes':a.archive.stat().st_size,'archive_sha256':h(a.archive.read_bytes()),
   'runtime_baseline_sha256':h(a.baseline.read_bytes()),'runtime_file_count':31,'runtime_files':rows,
   'navigation_count':len(nav),'bundled_count':14,'streamed_count':17,'target_id':'yangpu-library',
   'target_navigation_matches_installed_after_url_normalization':True,'target_assets':assets,
   'scope':'Actual ZIP runtime bytes and new target metadata versus installed project; no remote asset fetch or browser result.'}
 a.report.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('runtime_files','target_assets')},indent=2))
if __name__=='__main__':main()
