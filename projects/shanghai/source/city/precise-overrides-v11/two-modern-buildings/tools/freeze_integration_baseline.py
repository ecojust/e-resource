#!/usr/bin/env python3
"""Freeze actual installed V10 metadata for bounded V11 preparation; no MAIN writes."""
import argparse
import datetime
import gzip
import hashlib
import json
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
V10_PLAN = HERE.parent.parent / 'building-by-building-v10/integration-two-district-app-shadow-v2/final27-shadow-v2/installation-plan.json'
PLAN_SHA = '8bb8c7c99a61b7b938279c6237c6b1aa246d42cb69822014f354e365e7e3bb11'
LIGHT_SHA = '6cb2fb4dc1cca564d70f2718014c11600ba5846915df4d707caa5b56a873838c'
NEW = {'jiading-shanghai-auto-museum': ('research-a', '14-13706-6691', 870, [735, 797]),
       'minhang-baoyugang-library': ('research-b-library', '14-13718-6705', 201, [35, 60, 299, 333, 375, 466, 947])}


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def desc(p): return {'file':str(Path(p).resolve()),'bytes':Path(p).stat().st_size,'sha256':sha(p)}
def read(p):
    p=Path(p);b=p.read_bytes();return json.loads(gzip.decompress(b) if p.suffix=='.gz' else b)
def write(p,x):
    assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')


def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--project',type=Path,default=Path('/workspace/shanghai_project'))
    a.add_argument('--output',type=Path,default=HERE/'integration-v1')
    args=a.parse_args();P=args.project.resolve();O=args.output.resolve()
    assert O.is_relative_to(HERE) and O!=HERE and not O.exists()
    assert sha(V10_PLAN)==PLAN_SHA
    plan=read(V10_PLAN);planfiles={r['file']:r for r in plan['files']}
    registry=read(P/'data/precise-buildings-v6.json');nav=read(P/'data/landmarks.json');catalog=read(P/'data/precise-buildings/catalog.json')
    counts={'navigation':len(nav),'ordinary_records':catalog['record_count'],'catalog_macros':len(catalog['macros']),
            'owners':len(registry['landmarks']),'owner_macros':len(registry['macros']),'near':sum(len(m['near'])for m in registry['macros'])}
    assert counts=={'navigation':27,'ordinary_records':8,'catalog_macros':6,'owners':13,'owner_macros':7,'near':11}
    assert sha(P/'src/realistic-lighting.js')==LIGHT_SHA
    assert set(NEW).isdisjoint(r['id'] for r in registry['landmarks'])
    assert set(x[1] for x in NEW.values()).isdisjoint(m['id'] for m in registry['macros'])
    assert registry['ordinary_catalog']['sha256']==sha(P/'data/precise-buildings/catalog.json')
    O.mkdir(); files=[]
    def snapshot(src,dst,kind):
        s=desc(src);assert s['bytes']<100_000_000
        dst.parent.mkdir(parents=True,exist_ok=True);assert not dst.exists();shutil.copyfile(src,dst)
        assert sha(dst)==s['sha256'];files.append({'kind':kind,'original':s,'snapshot':desc(dst)})
    selected={'index.html','package.json','data/landmarks.json','data/districts.json','data/scene-props.json',
              'data/precise-buildings-v6.json','data/precise-buildings/catalog.json','assets/city-detail/manifest.json',
              'source/city/detail/geometry_engine.py','source/city/build_district_models.py','source/city/roof_geometry.py',
              'source/city/detail/requirements.lock'}
    selected.update(p.relative_to(P).as_posix() for p in (P/'src').glob('*.js'))
    selected.update(p.relative_to(P).as_posix() for p in (P/'data/precise-buildings/by-id').glob('*.json'))
    for macro in catalog['macros']:
        index=P/macro['file'];assert sha(index)==macro['sha256']
        selected.add(macro['file']);selected.add(str(Path(macro['file']).with_name('replacement.json')))
    for macro in registry['macros']:
        for near in macro['near']:
            assert sha(P/near['model']['file'])==near['model']['sha256']
            selected.add(near['model']['file'])
    selected.add(registry['validation']['file'])
    for rel in sorted(selected):
        p=P/rel;assert p.is_file(),p
        if rel in planfiles:
            expected=planfiles[rel];assert p.stat().st_size==expected['bytes'] and sha(p)==expected['sha256'],rel
        snapshot(p,O/'baseline/project'/rel,'actual_main_baseline')
    snapshot(V10_PLAN,O/'baseline/v10-installed-plan.json','root_confirmed_install_plan')
    upstream=P/'source/city/precise-overrides-v10/two-districts'
    for ident,evidence in registry['geometry_inputs'].items():
        src=upstream/'inputs'/evidence['file'];assert sha(src)==evidence['sha256']
        snapshot(src,O/'inputs'/evidence['file'],'existing_exact_owner_geometry')
        if evidence.get('mapping_report'):
            spec=evidence['mapping_report'];src=upstream/'inputs'/spec['file'];assert sha(src)==spec['sha256']
            snapshot(src,O/'inputs'/spec['file'],'existing_provider_mapping')
    recipes=[]
    for ident,(research,mid,lid,retained) in NEW.items():
        src=HERE.parent/research/'geometry-input.json';g=read(src)
        snapshot(src,O/'inputs'/ident/'geometry-input.json','new_exact_owner_geometry')
        c=g['current_city_detail'];assert c['owner_macro_id']==mid and c['feature_local_id']==lid
        folder=P/'assets/city-detail/macros'/mid;ready=read(folder/'READY.json');owners=read(folder/'ownership.json.gz')
        near=next(n for n in ready['near'] if n['id']==c['near_owner_id'])
        assert sorted(near['featureLocalIds'])==sorted([lid]+retained)
        assert sorted(r[0] for r in owners['owners'] if r[1]==near['id'])==sorted([lid]+retained)
        for k in ['feature_table_source_file','ready_source_file','ownership_source_file']:
            e=c[k];p=P/e['project_relative_path'];assert sha(p)==e['sha256'] and p.stat().st_size==e['bytes']
        raw=g['source']['raw_macro_source_file'];assert sha(P/raw['project_relative_path'])==raw['sha256']
        for rel in [raw['project_relative_path'],*[c[k]['project_relative_path']for k in ['feature_table_source_file','ready_source_file','ownership_source_file']],
                    f'assets/city-detail/macros/{mid}/{near["file"]}',f'assets/city-detail/macros/{mid}/far.glb']:
            snapshot(P/rel,O/'baseline/project'/rel,'new_target_original_source')
        recipes.append({'id':ident,'macro':mid,'local_id':lid,'near_id':near['id'],'source_geometry_sha256':sha(src),
                        'only_replacement_local_ids':[lid],'retained_local_ids':retained,
                        'source_roof_count_to_preserve':len(ready['source_roof_keys']),'residual_count_to_preserve':ready['residual_count'],
                        'near_baseline_sha256':near['sha256'],'near_baseline_decoded_sha256':near['decoded_sha256'],
                        'fresh_output':str(O/'fresh'/ident),'runtime_asset_prefix':'assets/city-overrides-v6/'+mid,
                        'generated':False,'actual_geometry_verified':False,'model_accepted':False,'navigation_ready':False})
    upstream_tools=[]
    for rel in ['tools/build_precise_overrides.py','tools/verify_override_geometry.mjs','tools/verify_override_runtime.mjs','compose_incremental.py']:
        src=upstream/rel;snapshot(src,O/'upstream-v10'/rel,'unchanged_tool_provenance');upstream_tools.append(desc(O/'upstream-v10'/rel))
    oldvariants=[{'near_id':n['id'],'file':n['model']['file'],'bytes':(P/n['model']['file']).stat().st_size,'sha256':sha(P/n['model']['file'])}
                 for m in registry['macros'] for n in m['near']]
    lock={'schema':'v11-actual-main27-source-integration-baseline-v1','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'project':str(P),'counts':counts,'root_confirmed_install_plan':desc(V10_PLAN),'public_commit':None,
          'runtime_lighting_sha256':LIGHT_SHA,'files':files,'existing_owner_ids':[r['id']for r in registry['landmarks']],
          'unchanged_near_variants':oldvariants,'upstream_tools':upstream_tools,
          'baseline_configuration_sha256':registry['baseline_configuration_sha256'],'engine_sha256':registry['engine_sha256'],
          'new_targets':recipes,'expected_after_two_geometry_audits':{'owners':15,'owner_macros':9,'near':13,'source_features':186,'target_source_features':15,'retained_source_features':171},
          'expected_after_separate_actual_app_acceptance':{'navigation':29,'ordinary_records':10,'catalog_macros':8},
          'source_geometry_scope_only':True,'new_near_generated':False,'new_models_or_browser_accepted':False,'main_modified':False}
    write(O/'baseline-lock.json',lock)
    write(O/'pending-owner-additions.json',{'schema':'v11-pending-exact-owner-additions-v1','inputs_ready':False,'baseline_lock':desc(O/'baseline-lock.json'),'targets':recipes,
                                          'prior_audited_root':str(HERE.parent.parent/'building-by-building-v10/two-district-integration/thirteen-targets'),
                                          'existing11_variants_must_not_be_regenerated':True,'registry_written':False,'registration_accepted':False})
    print(json.dumps({'baseline_lock':desc(O/'baseline-lock.json'),'counts':counts,'files':len(files),'copied_bytes':sum(r['snapshot']['bytes']for r in files)},ensure_ascii=False))


if __name__=='__main__':main()
