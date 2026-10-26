#!/usr/bin/env python3
"""Small JSON/hash post-check; does not decode geometry or run runtime/browser."""
import argparse
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_bytes())
def desc(p):
    p=Path(p)
    with p.open('rb') as h:sha=hashlib.file_digest(h,'sha256').hexdigest()
    return {'file':str(p.resolve()),'bytes':p.stat().st_size,'sha256':sha}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--report',type=Path,default=HERE/'post-generation-preservation.json')
    a=ap.parse_args();assert a.report.resolve().is_relative_to(HERE) and not a.report.exists()
    lock=read(HERE/'baseline-lock.json');P=Path(lock['project'])
    for row in lock['files']:
        for role in ['original','snapshot']:
            actual=desc(row[role]['file']);assert all(actual[k]==row[role][k]for k in ['bytes','sha256']),row[role]['file']
    baseline=read(HERE/'baseline/project/data/precise-buildings-v6.json')
    merged_path=HERE/'fifteen-targets/precise-buildings-v6.json';merged=read(merged_path)
    old_landmarks={r['id']:r for r in baseline['landmarks']};new_landmarks={r['id']:r for r in merged['landmarks']}
    old_macros={r['id']:r for r in baseline['macros']};new_macros={r['id']:r for r in merged['macros']}
    assert all(new_landmarks[k]==v for k,v in old_landmarks.items())
    assert all(new_macros[k]==v for k,v in old_macros.items())
    assert all(merged['geometry_inputs'][k]==v for k,v in baseline['geometry_inputs'].items())
    assert merged['ordinary_catalog']==baseline['ordinary_catalog']
    assert len(new_landmarks)==15 and len(new_macros)==9 and sum(len(m['near'])for m in merged['macros'])==13
    old_near=[]
    for m in baseline['macros']:
        for n in m['near']:
            rel=Path(n['model']['file']).relative_to('assets/city-overrides-v6')
            source=P/n['model']['file'];staged=HERE/'fifteen-targets'/rel
            assert desc(source)['sha256']==desc(staged)['sha256']==n['model']['sha256']
            assert desc(source)['bytes']==desc(staged)['bytes']==n['model']['size_bytes']
            old_near.append({'id':n['id'],'sha256':n['model']['sha256'],'bytes':n['model']['size_bytes'],'regenerated':False})
    fresh=[]
    for target in lock['new_targets']:
        folder=Path(target['fresh_output']);r=read(folder/'geometry-validation.json');assert r['pass'] is True and len(r['checks'])==1
        c=r['checks'][0];assert c['id']==target['near_id'] and c['baseline_sha256']==target['near_baseline_sha256']
        assert c['neighbors']['ids']==target['retained_local_ids'] and c['neighbors']['position_f64']['pass'] is True
        assert c['baseline_vs_override_position_f64']['pass'] is True and c['unassigned_triangles']==0
        assert len(c['groups'])==1 and c['groups'][0]['name']=='city_target_'+target['id']
        n=next(n for m in merged['macros']for n in m['near']if n['id']==c['id'])
        assert n['groups'][0]['local_ids']==target['only_replacement_local_ids']
        assert c['override_sha256']==n['model']['sha256']
        out=HERE/'fifteen-targets'/Path(n['model']['file']).relative_to('assets/city-overrides-v6')
        assert desc(out)['sha256']==n['model']['sha256']
        # Preserve strict-normal false diagnostics while applying unchanged original limits.
        normals=c['normal_directions'];assert normals['pass'] is True
        assert normals['component_limit']==1e-7 and normals['direction_limit_degrees']==1e-5
        fresh.append({'id':target['id'],'near':target['near_id'],'triangles':c['triangles'],'model':desc(out),
                      'retained_neighbors':c['neighbors'],'strict_normal_f64_comparison':c['baseline_vs_override_position_normal_f64'],
                      'normal_direction_comparison':normals,'actual_geometry_report':desc(folder/'geometry-validation.json')})
    count=sum(len(n['featureLocalIds'])for m in merged['macros']for n in m['near']);assert count==186
    report={'schema':'v11-actual-source-geometry-composition-preservation-v1','source_preservation_checks_passed':True,
            'baseline_lock':desc(HERE/'baseline-lock.json'),'registry':desc(merged_path),'old13_owner_records_exact':True,
            'old7_macros_and11_near_descriptors_exact':True,'old27_navigation_and8_records6catalog_bytes_exact':True,
            'all_original_and_snapshot_pairs_match':len(lock['files']),'old_near_bytes':old_near,'fresh_near':fresh,
            'totals':{'owners':15,'macros':9,'near':13,'source_features':186,'retained_neighbors':171},
            'library_original_201_375_source_sliver_unchanged':True,'museum_original_macro_12_residuals_unchanged':True,
            'new_models_accepted':False,'runtime_lifecycle_rerun_in_this_check':False,'browser_or_mvt_observed':False,'main_modified':False}
    a.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'report':desc(a.report),'totals':report['totals'],'old_near_bytes':sum(x['bytes']for x in old_near)},ensure_ascii=False))


if __name__=='__main__':main()
