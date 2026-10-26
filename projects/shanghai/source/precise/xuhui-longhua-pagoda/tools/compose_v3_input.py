#!/usr/bin/env python3
"""Describe actual selected v3 delivery files. No generation, review, or staging."""
import argparse,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent.parent/'v3'
RUN=SOURCE/'run-v3'
def descriptor(p):
 p=Path(p).absolute()
 if not p.is_file() or p.is_symlink():raise ValueError('Actual regular input missing: '+str(p))
 with p.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
 return {'source':str(p),'bytes':p.stat().st_size,'sha256':h}
def main():
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--output',type=Path,required=True);args=a.parse_args()
 if args.output.exists():raise ValueError('Existing input protected')
 pack=RUN/'package/packaging-record.json';package=json.loads(pack.read_text())
 assert package['building_id']=='xuhui-longhua-pagoda' and package['packaging_passed'] is True
 assets={k:v['sha256'] for k,v in package['assets'].items()}
 lock=json.loads((SOURCE/'build-source-files.json').read_text());frozen={r['file'] for r in lock['files']}
 extra=[]
 def add(path,target,role,bindings=(),note=''):
  if target in frozen:raise ValueError('Extra duplicates frozen destination: '+target)
  extra.append({**descriptor(path),'file':target,'role':role,'asset_bindings':{k:assets[k] for k in bindings},'selection_note':note})
 add(HERE/'prepare_source_delivery.py','tools/prepare_source_delivery.py','source_assembler')
 add(HERE/'compose_v3_input.py','tools/compose_v3_input.py','delivery_input_composer')
 add(SOURCE/'prepare_registration_v3.py','prepare_registration_v3.py','v3_registration_adapter')
 add(SOURCE/'independent-review/audit_v3_preservation_contact.py','independent-review/audit_v3_preservation_contact.py','v3_contact_checker',note='Replaying v2-to-v3 preservation needs the explicitly hash-bound historical v2 raw/part map; those rejected large model assets are not duplicated in this delivery.')
 add(SOURCE/'independent-review/probe_ridge_seat.py','independent-review/probe_ridge_seat.py','finite_ridge_seat_probe')
 add(RUN/'raw/xuhui-longhua-pagoda-raw.geometry.json','audit/raw-part-map.json','raw_part_map',('raw',))
 add(RUN/'raw/geometry-report.json','audit/actual-raw-geometry-report.json','raw_geometry_report',('raw',))
 add(RUN/'raw/asset-metadata.json','audit/raw-stage-metadata.json','raw_stage_metadata',('raw',),'Original raw-stage fields retained unchanged; this is not the final metadata.')
 add(SOURCE/'independent-review/actual-raw-structure.json','audit/actual-raw-structure.json','actual_raw_review',('raw',))
 add(SOURCE/'independent-review/actual-raw-roof-pairs.json','audit/actual-raw-roof-pairs.json','actual_raw_roof_samples',('raw',),'Finite sample coverage only; not whole-tower intersection freedom.')
 add(SOURCE/'independent-review/actual-v3-preservation-contact.json','audit/actual-v3-preservation-contact.json','actual_v3_preservation_contact',('raw',),'Exact old-part preservation and finite seat contact checks; not whole-model continuous contact or intersection freedom.')
 add(RUN/'decoded-package-check.json','audit/decoded-package-check.json','decoded_package_check',('raw','web','lod'))
 add(RUN/'native/native-render-report.json','audit/native-render-report.json','native_build_report',('raw','native'))
 for view in ['full','detail','low']:
  filename=f'xuhui-longhua-pagoda-{view}.png'
  add(RUN/'native'/filename,'previews/'+filename,'native_preview_'+view,('raw','native'))
 add(RUN/'native/root-native-visual-review.json','audit/native-visual-review.json','native_visual_review',('raw','native'))
 add(RUN/'prebrowser-acceptance-summary.json','audit/prebrowser-acceptance-summary.json','prebrowser_summary',('raw','web','lod','native'))
 add(RUN/'model-metadata.json','model-metadata.json','model_metadata',('raw','web','lod','native'))
 cfg={'schema':'longhua-source-delivery-input-v1','inputs_ready':True,'id':'xuhui-longhua-pagoda','selected_revision':'v3','source_root':str(SOURCE),'output':str(RUN/'final-delivery'),'build_manifest':descriptor(SOURCE/'build-source-files.json'),'packaging_spec':descriptor(SOURCE/'packaging-input.json'),'package_record':descriptor(pack),'code_license':descriptor(HERE.parent/'LICENSE-MIT.txt'),'code_license_id':'MIT','geometry_license':'CC-BY-SA-4.0','extra_source_files':extra,'selection_note':'Explicit v3 input assembled only from existing real descriptors. Input completeness does not synthesize acceptance; separate preserved reports supply their own scoped verdicts. Frozen source and raw-stage metadata remain unchanged.'}
 args.output.parent.mkdir(parents=True,exist_ok=True)
 with args.output.open('x') as f:json.dump(cfg,f,ensure_ascii=False,indent=2);f.write('\n')
 print(json.dumps(descriptor(args.output),indent=2))
if __name__=='__main__':main()
