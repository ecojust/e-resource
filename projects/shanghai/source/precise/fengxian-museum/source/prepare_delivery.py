#!/usr/bin/env python3
"""Emit an explicit public authoring/preview whitelist; no private image pixels."""
from pathlib import Path
import argparse,json,hashlib
ROOT=Path(__file__).resolve().parent.parent
PREFIX='source/precise/fengxian-museum/'
def record(source,target):
 p=(ROOT/source).resolve();size=p.stat().st_size
 assert 0<size<100_000_000,(p,size)
 return {'file':PREFIX+target,'source':str(p),'bytes':size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--version',required=True);a=ap.parse_args();v=a.version;out=ROOT/('delivery-'+v);assert not out.exists();out.mkdir()
 sources=[('source/README.md','README.md'),('source/LICENSE','LICENSE')]
 for name in ['build_model.py','build_envelope.py','roof_details.py','render_model.py','package_assets.py','prepare_delivery.py','common/photo_architecture.py','geometry-input.json','facade-detail-controls.json','roof-detail-evidence-v2.json']:
  sources.append(('source/'+name,'source/'+name))
 for name in ['registration-v1/registration.json','registration-v1/registration.svg','roof-topology-v3a/roof-regions.json','roof-topology-v3a/roof-topology.svg','circular-components-proposal.json','exterior-veil-v4.json','outer-fit-correction-v2.json']:
  sources.append((name,name))
 sources += [(f'full-{v}/features.json','full-feature-register.json'),(f'lod-{v}/features.json','lod-feature-register.json'),(f'full-{v}/metadata.json','model-build-record.json'),(f'package-{v}/web-copyright-restoration.json','web-copyright-restoration.json'),(f'package-{v}/lod-copyright-restoration.json','lod-copyright-restoration.json')]
 src={'model_id':'fengxian-museum','status':'Frozen authoring and provenance; model/browser acceptance managed separately','private_reference_pixels_included':False,'runtime_files_managed_by_asset_contract':str(ROOT/f'package-{v}/model-metadata.json'),'model_metadata_target_managed_by_integrator':True,'reference_images_target_managed_by_integrator':True,'public_photo_register_target_managed_by_integrator':True,'authoring_layout':'Preserve nested source/ plus sibling registration-v1/ and roof-topology-v3a/ for executable relative paths.','files':[record(x,y) for x,y in sources]}
 (out/'source-delivery.json').write_text(json.dumps(src,ensure_ascii=False,indent=2)+'\n')
 report=json.loads((ROOT/f'preview-{v}/native-render-report.json').read_text());images=['south-east-full.png','north-west-full.png','east-entry-detail.png','roof-walk-detail.png','native-render-report.json'];assert {q['file']for q in report['images']}==set(images[:-1])
 preview={'id':'fengxian-museum','images_are_actual_blender_renders':True,'private_reference_pixels_included':False,'render_engine':'Cycles CPU32samples','native_unchanged_during_render':True,'files':[record(f'preview-{v}/'+n,'previews/'+n) for n in images]}
 (out/'preview-delivery.json').write_text(json.dumps(preview,indent=2)+'\n')
 print(json.dumps({'source_manifest':str(out/'source-delivery.json'),'source_count':len(src['files']),'preview_manifest':str(out/'preview-delivery.json'),'preview_count':len(preview['files'])}))
if __name__=='__main__':main()
