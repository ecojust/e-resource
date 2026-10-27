#!/usr/bin/env python3
"""Package actual reviewed raw/LOD via Meshopt lossless FLOAT32 positions."""
from pathlib import Path
import argparse,hashlib,json,os,struct,subprocess
ID='baoshan-confucian-dacheng-hall'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):
 b=Path(p).read_bytes();n,t=struct.unpack_from('<II',b,12);assert t==0x4e4f534a
 return json.loads(b[20:20+n]),b[20+n:]
def save(p,d,tail):
 data=json.dumps(d,ensure_ascii=False,separators=(',',':')).encode();data+=b' '*((-len(data))%4)
 Path(p).write_bytes(struct.pack('<4sII',b'glTF',2,20+len(data)+len(tail))+struct.pack('<II',len(data),0x4e4f534a)+data+tail)
def tris(p):
 d,_=load(p);return sum(d['accessors'][p['indices']]['count']//3 for m in d['meshes'] for p in m['primitives'])
def record(p,triangle=False):
 r={'path':str(p.resolve()),'bytes':p.stat().st_size,'sha256':sha(p)}
 assert r['bytes']<100000000
 if triangle:r['triangles']=tris(p)
 return r
def main():
 p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,required=True);p.add_argument('--lod-source',type=Path,required=True);p.add_argument('--native',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--gltfpack',type=Path,default=Path('/workspace/shanghai_tools/node_modules/.bin/gltfpack'));a=p.parse_args()
 assert not a.out.exists();a.out.mkdir(parents=True);assets={}
 raw=a.out/(ID+'-raw.glb');os.link(a.raw,raw);assets['raw']=record(raw,True)
 for role,src in [('web',raw),('lod',a.lod_source)]:
  dest=a.out/(ID+'-'+role+'.glb');cmd=[str(a.gltfpack),'-i',str(src),'-o',str(dest),'-cc','-noq','-km','-ke','-r',str(a.out/(role+'-gltfpack.json'))]
  subprocess.run(cmd,check=True,capture_output=True,text=True)
  d,tail=load(dest);original,_=load(src);d['extras']=original['extras'];d['asset']['copyright']=original['asset']['copyright'];save(dest,d,tail)
  assets[role]=record(dest,True);assert assets[role]['triangles']==tris(src)
 native=a.out/(ID+'.blend');os.link(a.native,native);assets['native']=record(native)
 meta=json.loads(a.raw.with_name('metadata.json').read_text());bounds=meta['raw']['bounds_glb'];height=bounds['max'][1]-bounds['min'][1]
 result={'id':ID,'name':'宝山孔庙大成殿','anchor':meta['anchor'],'ground_base_m':0,'rotation_y':0,'height_estimate_m':height,'height_nominal_m':13,'height_note':'Actual mesh envelope; approximately13m documentary secondary height, not a measured survey. Roof levels and camera constrained from modern rear photograph with explicit perspective assumptions. Footprint may denote eaves; dimensional extent unverified.','architecture_style':'清代三间重檐歇山顶；环廊、暗红木构、灰瓦与石月台','detail_note':'三组真实透空格扇、三段后白墙、灰瓦筒垄、斗栱、石栏、御路石；现代外观，不含旧纪念馆横匾。','uncertainty':'无测绘柱网或完整侧山墙照片；木构尺寸、兽饰与龙纹细节为有出处的推估；13m为二手辞典高度。','asset_license':'Geometry/code MIT; font subset SIL OFL1.1; source map ODbL1.0; no photo pixels embedded','assets':assets,'bounds_glb':bounds,'source_geometry_sha256':meta['source_geometry_sha256'],'declared_triangle_counts_preserved':True,'expanded_geometry_count_verified':False,'meshopt_decoded_geometry_verified':False,'browser_verified':False,'appearance_review_passed':False,'packing':['-cc','-noq','-km','-ke'],'lod_policy':'Authored simplification retaining three bay massing, true door lattice openings, wrap corridor, double xieshan roof, stairs and balustrade apertures; reduces tile/pan repetitions and micro relief; not exact triangle subset.'}
 (a.out/'model-metadata.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(assets),flush=True)
if __name__=='__main__':main()
