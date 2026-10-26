#!/usr/bin/env python3
"""Manifest only curated reconstruction sources; never include cached web pages."""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent
FILES=[
 'README.md','GLASS_FIT.md','build_model.py','refine_components.py','arch_grid_refinement.py','arch-grid-controls.json','check_arch_grid_revision.py','visual-acceptance.json','previews/bund07-photo-perspective.png','thai_sign.py','thai-sign-layout.json','fonts/NotoSansThaiBankSubset.ttf','fonts/OFL-NotoSansThai.txt','visual-refinement-controls.json','photo-camera-parameters.json','photo_camera.py','check_visual_refinement.py','verify_source_package.py','photo_glazing.py','register_photo_glass.py','check_geometry.py','check_photo_uv.py','make_source_package.py',
 'geometry-input.json','calibration.json','calibration-independent.json','calibration-independent-controls.json','calibration-axis-check.json','calibration-depth-check.json','calibration-independent-comparison.png','photo-glass-controls.json','photo-glass-inspection.png',
 'research/README.md','research/SOURCES.json','research/geometry-observations.json','research/identity-and-scale.json']
PHOTOS=['bund07-1908-arnold-wright-public-domain.jpg','bund07-2012-ferox-seneca-side-original.jpg','bund07-2016-xiquinhosilva-original.jpg','bund07-2024-chainwit-01-original.jpg','bund07-2025-suicasmo-original.jpg']
FILES += [f'research/{p}{suffix}' for p in PHOTOS for suffix in ['', '.metadata.json']]
COMMON=['photo_architecture.py','sign_lettering.py','photo_metric.py','PHOTO_METRIC.md','PHOTO_METRIC_NEXT.md','blender_finish.py','fonts/BundSignSubset-v6-1.otf','fonts/FONT-LICENSE.txt','fonts/manifest-v6-1.json']
def record(base,name):
 p=base/name;assert p.is_file() and p.stat().st_size<100_000_000
 return {'path':name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def main():
 files=[record(HERE,n) for n in FILES];common=[record(HERE.parent/'common',n) for n in COMMON]
 obj={'schema':'bund07-source-package-v1','required_sibling_files':['../common/'+n for n in COMMON],'required_sibling_sha256':common,'files':files,'total_bytes':sum(p['bytes'] for p in files),'source_output_directory_excluded':True,'copyrighted_article_fulltext_and_search_caches_excluded':True,'no_runtime_absolute_paths':True,'current_asset_sha256':hashlib.sha256((HERE/'output/bund07.glb').read_bytes()).hexdigest(),'source_condition':'2025 front, 2012/2016/2024 dated corroboration; hidden geometry explicitly estimated','portable_rebuild_check':'output/portable-rebuild-check.json','glass_fit_invariance_check':'historical 52a49d→77a72f stage only; current proof output/visual-refinement-check.json','visual_shape_review_status':'v3 calibrated-perspective native limited incremental pass; browser pending','visual_evidence':'visual-acceptance.json','visual_refinement_check':'output/arch-grid-revision-check.json','historical_raw_sha256':'3325262c62958cbfeb5a1ad07e19c42b1644b0b0e1a654558204e7d68562c832'}
 (HERE/'source-package-files.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'files':len(files),'total_bytes':obj['total_bytes'],'sibling_files':len(common),'asset_sha256':obj['current_asset_sha256']},indent=2))
if __name__=='__main__':main()
