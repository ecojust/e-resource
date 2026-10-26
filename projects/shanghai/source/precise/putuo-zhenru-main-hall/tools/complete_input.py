#!/usr/bin/env python3
"""Fill missing descriptors in one explicitly chosen pending input; no staging or acceptance."""
from pathlib import Path
import argparse,hashlib,json

def describe(row):
 p=Path(row['source']);assert p.is_absolute() and p.is_file() and not p.is_symlink(), 'Actual input missing: '+str(p)
 with p.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
 n=p.stat().st_size
 assert 0<n<100_000_000
 if row.get('bytes') is not None:assert row['bytes']==n and row['sha256']==h, 'Previously selected file changed: '+str(p)
 return {**row,'bytes':n,'sha256':h}
def main():
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--template',type=Path,required=True);a.add_argument('--output',type=Path,required=True);args=a.parse_args()
 assert not args.output.exists();cfg=json.loads(args.template.read_text());assert cfg['inputs_ready'] is False
 for key in ['build_manifest','raw_source_manifest','packaging_spec','package_record','code_license']:cfg[key]=describe(cfg[key])
 package=json.loads(Path(cfg['package_record']['source']).read_text());assert package['building_id']==cfg['id'] and package['packaging_passed'] is True
 for i,row in enumerate(cfg['extra_source_files']):
  row=describe(row)
  for role,expected in row.get('asset_bindings',{}).items():
   actual=package['assets'][role]['sha256'];assert expected in (None,actual),'Existing asset binding changed';row['asset_bindings'][role]=actual
  cfg['extra_source_files'][i]=row
 cfg['inputs_ready']=True;cfg['completion_note']='Only actual file descriptors filled. This does not create, infer, or change any review verdict.'
 args.output.parent.mkdir(parents=True,exist_ok=True)
 with args.output.open('x') as f:json.dump(cfg,f,ensure_ascii=False,indent=2);f.write('\n')
 print(json.dumps({'source':str(args.output.absolute()),'bytes':args.output.stat().st_size,'sha256':hashlib.sha256(args.output.read_bytes()).hexdigest()},indent=2))
if __name__=='__main__':main()
