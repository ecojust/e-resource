#!/usr/bin/env python3
"""Rebuild the complete Bund street, its lossless web GLB and matching interaction data."""
from pathlib import Path
import argparse,hashlib,json,os,runpy,shutil,struct,subprocess,sys
P=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write_json(path,value):
 path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_name(path.name+'.tmp');tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,path)
def copy(source,destination):
 destination.parent.mkdir(parents=True,exist_ok=True);tmp=destination.with_name(destination.name+'.tmp');shutil.copy2(source,tmp);os.replace(tmp,destination)
def glb_document(path):
 data=path.read_bytes();length=struct.unpack_from('<I',data,12)[0];return json.loads(data[20:20+length]),data[20+length:]
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--gltfpack',required=True);args=parser.parse_args()
 street=P/'source/bund/street';sys.path.insert(0,str(street));sys.argv=[str(street/'build_street.py'),str(P)]
 ns=runpy.run_path(str(street/'build_street.py'));raw=street/'bund-streets.glb';web=street/'bund-streets-web.glb'
 subprocess.run([args.gltfpack,'-i',str(raw),'-o',str(web),'-cc','-noq','-kn','-km','-ke'],check=True)
 original,_=glb_document(raw);doc,rest=glb_document(web);doc['asset']['copyright']=original['asset']['copyright'];doc['asset']['generator']='Shanghai Bund streets v5.0; gltfpack Meshopt, no position quantization'
 js=json.dumps(doc,separators=(',',':'),ensure_ascii=False).encode();js+=b' '*((-len(js))%4)
 web.write_bytes(struct.pack('<4sII',b'glTF',2,20+len(js)+len(rest))+struct.pack('<II',len(js),0x4e4f534a)+js+rest)
 from ground_sidecar import export_ground_sidecar
 ground_path=P/'data/bund/street-interaction-v5.json';ground=export_ground_sidecar(ns,ground_path,raw,web)
 furniture=ns['furniture'].interaction();ground['local_obstacles']=furniture['obstacles'];ground['furniture_coordinate_system']=furniture['coordinate_system']
 # Planting beds already block walking. Actual tree trunks additionally stop
 # an elevated camera without treating the whole crown as a solid wall.
 greenery=json.loads((P/'data/bund/greenery-v4.5.json').read_text())
 for tree in greenery['trees']:
  ground['local_obstacles'].append({'id':'tree-'+tree['id'],'type':'vertical_frustum','center_xz':[tree['x'],tree['z']],
   'bottom':tree['ground_altitude_m'],'top':tree['ground_altitude_m']+tree['height_m']*.42,
   'bottom_radius':.16,'top_radius':.065,'kind':'tree','blocks_walk':True,'blocks_camera':True,'source':'2010 photo-estimated tree root; inferred trunk shape'})
 ground['greenery_data_sha256']=sha(P/'data/bund/greenery-v4.5.json');write_json(ground_path,ground)
 copy(raw,P/'assets/models/bund/bund-streets.glb');copy(web,P/'assets/models/bund/web/bund-streets.glb')
 metadata=ns['metadata'];metadata.update({'web_sha256':sha(web),'web_bytes':web.stat().st_size,'interaction_file':str(ground_path.relative_to(P)),
  'interaction_sha256':sha(ground_path),'greenery':{'trees':7,'data':'data/bund/greenery-v4.5.json','reference_date':'2010-09-18','geometry_is_inferred':True}})
 write_json(street/'bund-streets.json',metadata);write_json(P/'data/bund/models/bund-streets.json',metadata)
 props=json.loads((P/'data/scene-props.json').read_text());record=next(x for x in props if x['id']=='bund-streets')
 record.update({'version':5.0,'raw_sha256':sha(raw),'raw_bytes':raw.stat().st_size,'web_sha256':sha(web),'sha256':sha(web),'web_bytes':web.stat().st_size,'bytes':web.stat().st_size,
  'triangles':metadata['triangles'],'interaction_file':str(ground_path.relative_to(P)),'interaction_sha256':sha(ground_path),'interaction_bytes':ground_path.stat().st_size,
  'validation':'data/bund/validation/street-v5.json','detail_note':'OSM道路、步道、过街与岸线；按可定位立面补齐楼前铺装。灯具、栏杆和七棵树参考2010—2025照片，树位及构件尺寸为推定；不代表统一年代的精测现状。'})
 write_json(P/'data/scene-props.json',props)
 write_json(P/'data/bund/models/bund-streets-web.json',record)
 checks={'version':5,'raw_bytes':raw.stat().st_size,'web_bytes':web.stat().st_size,'raw_sha256':sha(raw),'web_sha256':sha(web),'triangles':metadata['triangles'],
  'frontage':metadata['frontage_paving'],'shoreline':metadata['shoreline_validation'],'road':metadata['road_validation'],'geometry':metadata['geometry_validation'],
  'interaction_sha256':sha(ground_path),'interaction_features':len(ground['features']),'interaction_local_obstacles':len(ground['local_obstacles']),'web_position_quantization':False}
 assert all(0<p.stat().st_size<100_000_000 for p in [raw,web,ground_path])
 write_json(P/'data/bund/validation/street-v5.json',checks)
 print(json.dumps({k:checks[k] for k in ['raw_bytes','web_bytes','triangles','interaction_features','interaction_local_obstacles']}))
if __name__=='__main__':main()
