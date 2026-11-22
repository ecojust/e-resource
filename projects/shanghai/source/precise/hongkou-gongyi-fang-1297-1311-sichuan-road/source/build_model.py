"""Build the block-one paired frontage of Gongyi Fang in local metres."""
import argparse,json,sys,struct
from pathlib import Path
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'tools'))
from package_architectural_model import Builder
from gongyi_frontage import PALETTE,add_building
from materials import produce_textures,map_faces
ID='hongkou-gongyi-fang-1297-1311-sichuan-road'
SLUG='gongyi-fang-1297-1311-sichuan-road'
CAMERAS={
 'front':[[-3.68,6.8,-1],[0,.04,1],20.7,43.2],
 'oblique':[[-3.5,6.1,-3.1],[.29,.18,1],22.3,43.1],
 'above':[[-3.5,7.4,-5.45],[.21,.70,1],23.7,44.5],
 'balconies':[[8.1,8.75,-.15],[.24,.08,1],17.5,20.0],
 'ironwork':[[2.81,9.21,.075],[.14,.04,1],3.7,5.65],
 'south':[[ -10.9,8.6,-.16],[-.22,.09,1],20.0,23.1]}
META=dict(id=ID,name='公益坊一号楼南北两段商住楼街面',address='上海市虹口区四川北路1297–1311号',heritage_group='5F038',viewer_page=SLUG+'.html',
 scope='修缮后四川北路东立面，包含南段四间灰白商铺、北段三跨两层阳台、原有平坡屋面分界。',estimated='沿街尺寸从天华总平面比例尺与1931年南段图纸读得，窗与层线的测量来源、精度及屋面边界见研究表。',source_reference='source/precise/'+ID+'/SOURCES-LICENSE.md',geometry_license='MIT',code_license='MIT',photos_embedded=False,copyright='Original metric reconstruction and generated textures, MIT.',camera_views=CAMERAS)
def create(lod=False):
 palette={k:dict(v) for k,v in PALETTE.items()}
 for key,path in produce_textures().items():palette[key].update(texture=str(path),color=[1,1,1])
 b=Builder(palette);add_building(b,lod);map_faces(b);return b
def repeated_sampling(path):
 raw=path.read_bytes();size=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+size])
 for row in doc.get('samplers',[]):row.update(wrapS=10497,wrapT=10497)
 for m in doc['materials']:
  if m.get('name')=='1号楼 | 浅绿透光屏':
   m['alphaMode']='BLEND';m['pbrMetallicRoughness']['baseColorFactor'][3]=.60
 buf=json.dumps(doc,separators=(',',':'),ensure_ascii=False).encode();buf+=b' '*(-len(buf)%4)
 tail=raw[20+size:];path.write_bytes(struct.pack('<4sIIII',b'glTF',2,20+len(buf)+len(tail),len(buf),0x4e4f534a)+buf+tail)
def write_model(path,lod=False):
 import hashlib
 b=create(lod);rep=b.save(path,META);repeated_sampling(path)
 rep.update(bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest());path.with_suffix('.geometry.json').write_text(json.dumps(rep,ensure_ascii=False,indent=1)+'\n')
 return b,rep
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--lod',action='store_true');a=p.parse_args()
 b,report=write_model(a.output,a.lod);print(report['triangles'],report['parts'],report['bytes'],report['sha256'])
