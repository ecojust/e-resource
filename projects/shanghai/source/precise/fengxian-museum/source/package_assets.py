#!/usr/bin/env python3
"""Freeze four authored assets without changing raw/native bytes."""
from pathlib import Path
import argparse,json,hashlib,os,subprocess,struct
ID='fengxian-museum'
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def glb_doc(p):
 d=Path(p).read_bytes();n=struct.unpack_from('<I',d,12)[0];return json.loads(d[20:20+n])
def restore_copyright(path,copyright):
 # gltfpack1.3 does not retain asset.copyright even with -ke. Restore only this
 # required attribution field, preserving every BIN byte and all scene data.
 old=path.read_bytes();n=struct.unpack_from('<I',old,12)[0];doc=json.loads(old[20:20+n]);tail=old[20+n:];doc['asset']['copyright']=copyright
 raw=json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode();raw+=b' '*((-len(raw))%4)
 new=struct.pack('<4sII',b'glTF',2,20+len(raw)+len(tail))+struct.pack('<II',len(raw),0x4e4f534a)+raw+tail
 temporary=path.with_suffix('.attribution.tmp');temporary.write_bytes(new);os.replace(temporary,path)
 return {'old_glb_sha256':hashlib.sha256(old).hexdigest(),'new_glb_sha256':sha(path),'all_chunks_after_json_identical':path.read_bytes()[20+len(raw):]==tail,'unchanged_post_json_sha256':hashlib.sha256(tail).hexdigest(),'restored_field':'asset.copyright'}
def info(p,tri=None):
 x={'path':str(p.resolve()),'bytes':p.stat().st_size,'sha256':sha(p)}
 if tri is not None:x['triangles']=tri
 assert 0<x['bytes']<100_000_000
 return x
def main():
 p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,required=True);p.add_argument('--lod-source',type=Path,required=True);p.add_argument('--native',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--gltfpack',type=Path,default=Path('/workspace/shanghai_tools/node_modules/.bin/gltfpack'));a=p.parse_args();assert not a.out.exists();a.out.mkdir(parents=True)
 meta=json.loads(a.raw.parent.joinpath('metadata.json').read_text());lodmeta=json.loads(a.lod_source.parent.joinpath('metadata.json').read_text());assets={}
 for role,source in [('raw',a.raw),('native',a.native)]:
  dest=a.out/(ID+('-raw.glb' if role=='raw' else '.blend'));os.link(source,dest);assets[role]=info(dest,meta['raw']['triangles'] if role=='raw' else None)
 parameters=['-cc','-noq','-vtf','-vnf','-km','-ke']
 for role,source,tri in [('web',a.raw,meta['raw']['triangles']),('lod',a.lod_source,lodmeta['raw']['triangles'])]:
  dest=a.out/(ID+'-'+role+'.glb');subprocess.run([str(a.gltfpack),'-i',str(source),'-o',str(dest),*parameters,'-r',str(a.out/(role+'-gltfpack.json'))],check=True)
  repair=restore_copyright(dest,glb_doc(source)['asset']['copyright']);(a.out/(role+'-copyright-restoration.json')).write_text(json.dumps(repair,indent=2)+'\n');assets[role]=info(dest,tri)
 bounds=meta['raw']['bounds_glb'];result={k:meta[k] for k in ['id','name','anchor','rotation_y','ground_base_m','uncertainty','source_geometry_sha256']}
 result.update(height_estimate_m=bounds['max'][1],height_nominal_m=21,height_note='Actual authored envelope21.469999m includes an approximate0.47m small vent above the trial21m pavilion cap. SUAD reports overall15–21m, while an earlier construction table gives18m with unresolved boundaries. Neither those scopes nor this software bounding height constitute a measured as-built elevation.',architecture_style='2019现代曲线三体博物馆；独立连体铜百叶外幕、分层内庭与公共绿屋顶环道',detail_note='真实密百叶及C侧稀疏矩形截断、退后玻璃门窗和白圆柱、连接主体的钢架/外缘路径、三叶绿顶内缘和白圆平台、玻璃环道栏杆、分叶曲线路径/种植分区及可见设备。',assets=assets,bounds_glb=bounds,packing=parameters,expected_images={'raw':0,'web':0,'lod':0},asset_license=[{'id':'MIT','url':'https://opensource.org/license/mit/','attribution':'Authored model geometry and code by agent','role':'authored_geometry_and_code'},{'id':'CC-BY-SA-4.0','url':'https://creativecommons.org/licenses/by-sa/4.0/','attribution':'Building reference photograph by Stevenliuyi; reference only, not embedded texture','role':'building_reference_photograph'},{'id':'ODbL-1.0','url':'https://opendatacommons.org/licenses/odbl/1-0/','attribution':'Source footprint ©OpenStreetMap contributors / Overture Maps Foundation','role':'source_footprint_data'}],lod_policy='Authored reduced plants and railing/mullion density. Copper fin pitch, width and depth scale together2x to preserve projected coverage; extra depth extends inward rather than changing the external silhouette. True gaps, continuous veil and all layered court/platform types remain.',browser_verified=False,appearance_review_passed=False,source_photos_register='source/precise/'+ID+'/public-photo-register.json')
 (a.out/'model-metadata.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'assets':assets,'metadata':str(a.out/'model-metadata.json')}),flush=True)
if __name__=='__main__':main()
