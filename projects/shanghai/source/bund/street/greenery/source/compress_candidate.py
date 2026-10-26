from pathlib import Path
import argparse,json,struct,subprocess,hashlib
p=argparse.ArgumentParser();p.add_argument('--gltfpack',required=True);p.add_argument('--project',type=Path,required=True);args=p.parse_args();root=Path(__file__).resolve().parent.parent;out=root/'output';raw=out/'bund17-18-greenery-candidate.glb';web=out/'bund17-18-greenery-web.glb'
def chunks(path):
 b=path.read_bytes();p=12;items=[]
 while p<len(b):
  n,t=struct.unpack_from('<II',b,p);items.append((t,b[p+8:p+8+n]));p+=8+n
 return items
subprocess.run([args.gltfpack,'-i',str(raw),'-o',str(web),'-cc','-noq','-km','-ke'],check=True)
a=json.loads(chunks(raw)[0][1]);parts=chunks(web);b=json.loads(parts[0][1]);b['asset']['copyright']=a['asset']['copyright'];b['asset']['extras']=a['asset']['extras'];j=json.dumps(b,separators=(',',':')).encode();j+=b' '*((-len(j))%4);parts[0]=(0x4e4f534a,j);body=b''.join(struct.pack('<II',len(v),t)+v for t,v in parts);web.write_bytes(struct.pack('<III',0x46546c67,2,len(body)+12)+body)
subprocess.run(['node',str(args.project/'tools/qa/compare_model_compression.mjs'),str(args.project),str(raw),str(web),str(out/'greenery-compression-validation.json')],check=True)
files={}
for name in [raw.name,web.name]:
 f=out/name;assert f.stat().st_size<100_000_000;files[name]={'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
(out/'asset-files.json').write_text(json.dumps({'files':files,'license':'Original geometry MIT; OSM-derived placements ODbL-1.0; unchanged CC0 reference is not a texture'},indent=2)+'\n');print(json.dumps(files))
