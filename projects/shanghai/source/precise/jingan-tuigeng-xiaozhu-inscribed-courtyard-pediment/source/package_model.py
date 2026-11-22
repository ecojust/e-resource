"""Build, meshopt-encode, decode and compare the near and far meshes."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys
here=Path(__file__).resolve().parent
project=next((p for p in here.parents if (p/'source/precise/hongkou-general-post-office').is_dir()),None)
if project is None:
    import os
    project=Path(os.environ['E_RESOURCE_SHANGHAI'])
sys.path[:0]=[str(project/'source/precise/jingan-country-hospital/source'),str(project/'source/precise/jingan-jiaozhou-450-garden-residence/source')]
from check_meshes import check_pair
from asset_rights import retain_metadata,document
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pack(out,binary):
    out.mkdir(parents=True,exist_ok=True);result={}
    for role,source in [('full','raw'),('lod','source-lod')]:
        original=out/(source+'.glb');packed=out/(role+'.glb');decoded=out/('decoded-'+role+'.glb')
        subprocess.run([sys.executable,'-Bu',here/'build_model.py',original]+(['--lod'] if role=='lod' else []),check=True)
        subprocess.run([binary,'-i',original,'-o',packed,'-cc','-noq','-vnf','-km','-kn','-ke'],check=True)
        retain_metadata(packed,original);assert document(packed)['asset']['copyright']==document(original)['asset']['copyright']
        result[role]=dict(source_sha256=sha(original),packed_sha256=sha(packed),triangle_surfaces=check_pair(original,packed,decoded),decoded_sha256=sha(decoded),bytes=packed.stat().st_size)
    (out/'meshopt-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('output',type=Path);parser.add_argument('--gltfpack',default='gltfpack')
    a=parser.parse_args();pack(a.output,a.gltfpack)
