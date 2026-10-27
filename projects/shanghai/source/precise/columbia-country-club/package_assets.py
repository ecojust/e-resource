#!/usr/bin/env python3
"""Freeze four authored assets without changing raw/native bytes."""
from pathlib import Path
import argparse,json,hashlib,os,subprocess,struct
ID='columbia-country-club'
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
 result.update(height_estimate_m=bounds['max'][1],height_nominal_m=14,height_note='Actual model envelope14m; documentary drawing-derived estimate, not measured height. Independent section scaling supports rounded levels0.75/5.4/9/12/14m, with at least±0.5–1m uncertainty.',architecture_style='西班牙传教会复兴风格；2018修缮后的完整主楼和保留东加建，现代蔦屋書店字牌',detail_note='分体实体筒瓦、后退露台与山花、真实墙洞和细格木窗、北成对科林斯柱、南扭柱/铁艺阳台、暗灰细花格透孔、台阶与圆端楼梯。',assets=assets,bounds_glb=bounds,packing=parameters,expected_images={'raw':3,'web':3,'lod':1},asset_license=[{'scope':'authored geometry and code','license':'MIT','author':'agent'},{'scope':'generic Plaster001 images','license':'CC0-1.0','author':'ambientCG','url':'https://ambientcg.com/view?id=Plaster001'},{'scope':'building reference photographs; not embedded textures','license':'CC-BY-SA-4.0','author':'WQL','url':'https://creativecommons.org/licenses/by-sa/4.0/'},{'scope':'font glyph subset','license':'OFL-1.1','author':'Noto project'},{'scope':'source footprint data','license':'ODbL-1.0','author':'OpenStreetMap contributors / Overture Maps Foundation'}],lod_policy='Authored lower tile density and fewer roof/column subdivisions; retains real openings and defining architectural parts. Only original albedo remains embedded.',browser_verified=False,appearance_review_passed=False,source_photos_register='source/precise/'+ID+'/public-photo-register.json')
 (a.out/'model-metadata.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'assets':assets,'metadata':str(a.out/'model-metadata.json')}),flush=True)
if __name__=='__main__':main()
