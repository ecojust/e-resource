#!/usr/bin/env python3
"""Pack final web/LOD; reference immutable raw/native without copying them."""
from pathlib import Path
import argparse,hashlib,json,os,struct,subprocess
ID='xuhui-wukang-mansion'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def doc(p):
 data=Path(p).read_bytes();size=struct.unpack_from('<I',data,12)[0];return json.loads(data[20:20+size])
def info(p,tri=None):
 value={'path':str(p.resolve()),'bytes':p.stat().st_size,'sha256':sha(p)}
 if tri is not None:value['triangles']=tri
 if not 0<value['bytes']<100_000_000:raise ValueError('Asset must be below 100,000,000 bytes')
 return value
def restore_attribution(p,copyright):
 old=p.read_bytes();n=struct.unpack_from('<I',old,12)[0];j=json.loads(old[20:20+n]);tail=old[20+n:];j['asset']['copyright']=copyright
 raw=json.dumps(j,ensure_ascii=False,separators=(',',':')).encode();raw+=b' '*((-len(raw))%4)
 new=struct.pack('<4sII',b'glTF',2,20+len(raw)+len(tail))+struct.pack('<II',len(raw),0x4e4f534a)+raw+tail
 temporary=p.with_suffix('.tmp');temporary.write_bytes(new);os.replace(temporary,p)
 return {'field':'asset.copyright','all_post_json_chunks_unchanged':p.read_bytes()[20+len(raw):]==tail,'post_json_sha256':hashlib.sha256(tail).hexdigest(),'old_sha256':hashlib.sha256(old).hexdigest(),'new_sha256':sha(p)}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--raw',type=Path,required=True);ap.add_argument('--lod-source',type=Path,required=True);ap.add_argument('--native',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--gltfpack',type=Path,default=Path('/workspace/shanghai_tools/node_modules/.bin/gltfpack'));a=ap.parse_args()
 if a.out.exists():raise ValueError('Fresh output directory required')
 a.out.mkdir(parents=True);meta=json.loads((a.raw.parent/'metadata.json').read_text());assets={'raw':info(a.raw,meta['raw']['triangles']),'native':info(a.native)}
 parameters=['-cc','-noq','-vtf','-vnf','-km','-ke']
 for role,source in [('web',a.raw),('lod',a.lod_source)]:
  target=a.out/(ID+'-'+role+'.glb');report=a.out/(role+'-gltfpack.json')
  subprocess.run([str(a.gltfpack),'-i',str(source),'-o',str(target),*parameters,'-r',str(report)],check=True)
  repair=restore_attribution(target,doc(source)['asset']['copyright']);(a.out/(role+'-copyright-restoration.json')).write_text(json.dumps(repair,indent=2))
  packed=json.loads(report.read_text());assets[role]=info(target,packed['render']['triangleCount'])
 result={k:meta[k] for k in ['id','name','anchor','ground_base_m','rotation_y','source_geometry_sha256','architecture_style','detail_note','uncertainty']}
 result.update(height_estimate_m=meta['raw']['bounds_glb']['max'][1],height_nominal_m=30.,height_note='Published secondary source says eight-storey building30m without defined endpoints. Model parapet30.10m and inferred roof flues31.37m are authored estimates, not surveyed heights.',assets=assets,bounds_glb=meta['raw']['bounds_glb'],packing=parameters,expected_images={'raw':3,'web':3,'lod':3},asset_license=[{'id':'MIT','url':'https://opensource.org/license/mit/','attribution':'Authored geometry/code by agent','role':'authored_geometry_and_code'},{'id':'ODbL-1.0','url':'https://opendatacommons.org/licenses/odbl/1-0/','attribution':'Source footprint ©OpenStreetMap contributors / Overture Maps Foundation','role':'source_footprint_data'},{'id':'CC0-1.0','url':'https://creativecommons.org/publicdomain/zero/1.0/','attribution':'Original procedural brick material by agent; generic inferred material, not a scan','role':'embedded_generic_procedural_material'},{'id':'CC-BY-SA-4.0','url':'https://creativecommons.org/licenses/by-sa/4.0/','attribution':'Building reference photographs by Windmemories, SSYoung, 钉钉 and others per photo register; no photograph pixels embedded','role':'reference_photographs'}],lod_policy='Authored lower curved-wall sampling and turned-baluster sides; ornamental rail ovals and corbel incised spirals removed at distance. Main openings, true recessed volumes, fanlight pattern, balcony structure and all eight storeys retained.',source_photos_register='source/precise/'+ID+'/public-photo-register.json',browser_verified=False,appearance_review_passed=False,freeze_note='Raw/native referenced at original final paths; no second large copies. Read-only filesystem freeze occurs after independent acceptance.')
 (a.out/'model-metadata.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps({'assets':assets,'metadata':str(a.out/'model-metadata.json')},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
