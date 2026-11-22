"""Pack the raw and far source surfaces with meshoptimizer and verify their independent decodes."""
import argparse,hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
from build_model import HERE,PROJECT,ID,META,write_model
from package_architectural_model import check_pair,glb_stats
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-st-lukes-hospital-changzhi-nanxun-corner/source'))
from asset_rights import retain_metadata
def write(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def package(work,out,tool,existing=False):
 work.mkdir(parents=True,exist_ok=True);out.mkdir(parents=True,exist_ok=True)
 roles={};checks={}
 for role,name in [('raw','raw'),('full','web'),('lod','lod')]:
  target=out/f'{ID}-{name}.glb'
  if role=='raw':
   src=work/'raw.glb'
   if not existing:write_model(src,False)
   shutil.copyfile(src,target)
  else:
   src=work/('raw.glb' if role=='full' else 'lod.glb')
   if not existing and role=='lod':write_model(src,True)
   subprocess.run([tool,'-i',src,'-o',target,'-cc','-noq','-vnf','-km','-kn','-ke'],check=True)
   retain_metadata(target,src);checks[role]=check_pair(src,target,work/f'decoded-{role}.glb')
  stats=glb_stats(target);roles[role]={**stats,'file':target.name,'sha256':sha(target),'bytes':target.stat().st_size}
 assert roles['raw']['triangles']==roles['full']['triangles']>roles['lod']['triangles']
 write(out/'manifest.json',{**META,'assets':roles});write(work/'oriented-surface-checks.json',checks)
 return roles
if __name__=='__main__':
 arg=argparse.ArgumentParser(description=__doc__);arg.add_argument('--work',type=Path,required=True);arg.add_argument('--out',type=Path,required=True);arg.add_argument('--gltfpack',default='gltfpack');arg.add_argument('--existing-source',action='store_true');q=arg.parse_args();print(package(q.work,q.out,q.gltfpack,q.existing_source))
