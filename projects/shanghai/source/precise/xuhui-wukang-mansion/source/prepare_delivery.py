#!/usr/bin/env python3
"""Small exact whitelists for public authoring/proof; private photos excluded."""
from pathlib import Path
import argparse,hashlib,json
ROOT=Path(__file__).resolve().parent.parent
V18=ROOT.parents[1]
PREFIX='source/precise/xuhui-wukang-mansion/'
def record(source,target):
 p=Path(source).resolve();size=p.stat().st_size
 if not 0<size<100_000_000:raise ValueError(str(p))
 return {'file':PREFIX+target,'source':str(p),'bytes':size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 if a.out.exists():raise ValueError('Fresh output directory required')
 a.out.mkdir(parents=True)
 pairs=[(ROOT/'source/README.md','README.md'),(ROOT/'source/LICENSE','LICENSE')]
 for name in ['build_detailed_v1.py','curved_facade.py','trim_shared_end.py','common/photo_architecture.py','render_detailed_v1.py','render_final_v5.py','package_assets.py','prepare_delivery.py','rebuild.py']:
  pairs.append((ROOT/'source'/name,'source/'+name))
 pairs.append((V18/'integration/wukang-mansion/freeze-v1/xuhui-wukang-mansion/geometry-input.json','source/geometry-input.json'))
 pairs.append((ROOT/'source/public-material.json','materials/wukang-brick-v1/material.json'))
 for name in ['generate_material.py','README.md','LICENSE']:
  source=V18/'materials/wukang-brick-v1'/name
  if source.exists():pairs.append((source,'materials/wukang-brick-v1/'+name))
 for name in ['brick-basecolor.png','brick-normal.png','brick-orm.png']:
  pairs.append((V18/'materials/wukang-brick-v1/maps'/name,'materials/wukang-brick-v1/maps/'+name))
 for directory,name,target in [('full-v5','features.json','full-feature-register.json'),('lod-v5','features.json','lod-feature-register.json'),('full-v5','metadata.json','model-build-record.json'),('full-v5','face-layout.json','face-layout.json'),('package-v2','web-copyright-restoration.json','web-copyright-restoration.json'),('package-v2','lod-copyright-restoration.json','lod-copyright-restoration.json'),('review-detail-v1','nose-inset-v4-component-check.json','nose-inset-component-check.json')]:
  pairs.append((ROOT/directory/name,target))
 pairs.append((ROOT/'full-v5/shared-end-clip.json','shared-end-clip.json'))
 pairs.append((ROOT/'source/final-revision.json','final-revision.json'))
 source={'model_id':'xuhui-wukang-mansion','private_reference_pixels_included':False,'runtime_model_assets_managed_separately':str(ROOT/'package-v2/model-metadata.json'),'reference_photos_managed_by_integrator':True,'authoring_layout':'source/ plus sibling materials/wukang-brick-v1; rebuild.py normalizes material lookup for portable public tree','scope':'Authored exterior main building only; reconstruction uncertainty retained','files':[record(s,t) for s,t in pairs]}
 (a.out/'source-delivery.json').write_text(json.dumps(source,ensure_ascii=False,indent=2))
 previews=[];versions=[]
 for version,note in [('preview-v4','V4 unchanged-area overview evidence; these pixels are not V5 renders'),('preview-v5','New V5 final three-part shared-end correction detail renders')]:
  report=json.loads((ROOT/version/'native-render-report.json').read_text())
  report['raw']['path']=Path(report['raw']['path']).name;report['native']['path']=Path(report['native']['path']).name
  report['provenance_note']=note
  public_report=a.out/(version+'-native-render-report.json');public_report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
  for im in report['images']:
   previews.append(record(ROOT/version/im['file'],'previews/'+version+'/'+im['file']))
  previews.append(record(public_report,'previews/'+version+'/native-render-report.json'))
  versions.append({'version':version,'note':note,'raw_sha256':report['raw']['sha256'],'native_sha256':report['native']['sha256'],'image_count':len(report['images'])})
 preview={'id':'xuhui-wukang-mansion','images_are_actual_blender_renders':True,'private_reference_pixels_included':False,'native_unchanged_during_render':True,'render_engine':'Cycles CPU24 samples','version_provenance':versions,'files':previews}
 (a.out/'preview-delivery.json').write_text(json.dumps(preview,ensure_ascii=False,indent=2))
 combined={'id':'xuhui-wukang-mansion','private_reference_pixels_included':False,'files':source['files']+previews}
 (a.out/'combined-delivery.json').write_text(json.dumps(combined,ensure_ascii=False,indent=2))
 print(json.dumps({'source_files':len(pairs),'preview_files':len(previews),'output':str(a.out)}))
if __name__=='__main__':main()
