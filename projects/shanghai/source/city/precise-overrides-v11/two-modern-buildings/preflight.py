#!/usr/bin/env python3
"""Check the actual frozen baseline and emit future commands, without generation."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def desc(p):return {'file':str(Path(p).resolve()),'bytes':Path(p).stat().st_size,'sha256':sha(p)}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--report',type=Path,default=HERE/'preflight-report.json')
    ap.add_argument('--gltfpack',type=Path,default=Path('/workspace/shanghai_tools/node_modules/.bin/gltfpack'))
    args=ap.parse_args();out=args.report.resolve()
    assert out.is_relative_to(HERE) and not out.exists()
    lock=read(HERE/'baseline-lock.json');project=Path(lock['project'])
    for row in lock['files']:
        for key in ['original','snapshot']:
            expected=row[key];actual=desc(expected['file'])
            assert actual['bytes']==expected['bytes'] and actual['sha256']==expected['sha256'],expected['file']
    current=read(project/'data/precise-buildings-v6.json')
    prior_root=HERE.parent.parent.parent/'building-by-building-v10/two-district-integration/thirteen-targets'
    # HERE.parent.parent is V11; the sibling V10 is one further parent.
    assert prior_root.is_dir(),prior_root
    prior=read(prior_root/'precise-buildings-v6.json')
    for key in ['macros','landmarks','geometry_inputs','baseline_configuration_sha256','engine_sha256']:
        assert current[key]==prior[key],key
    prior_report=prior_root/prior['validation']['file'];assert sha(prior_report)==prior['validation']['sha256'] and read(prior_report)['pass'] is True
    spec=importlib.util.spec_from_file_location('v11_override_preflight',HERE/'tools/build_precise_overrides.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    ids=sorted(p.name for p in (HERE/'inputs').iterdir() if (p/'geometry-input.json').is_file())
    inputs,claimed,boundaries=module.parse_inputs(project,[HERE/'inputs'],ids)
    assert len(inputs)==15 and len(claimed)==9 and sum(len(x)for x in claimed.values())==15
    byid={x['id']:x for x in boundaries}
    assert all(byid[x['id']]==x for x in current['landmarks'])
    tool=args.gltfpack
    assert tool.is_file(),tool
    external_lock=read(HERE/'external-tool-lock.json')
    for expected in external_lock['files']:
        actual=desc(expected['source'])
        assert actual['bytes']==expected['bytes'] and actual['sha256']==expected['sha256']
    assert tool.resolve()==Path(external_lock['executable']).resolve()
    commands=[]
    for target in lock['new_targets']:
        fresh=Path(target['fresh_output']);assert fresh.is_relative_to(HERE) and not fresh.exists()
        commands.append({'id':target['id'],'generate_near_argv':[sys.executable,str(HERE/'tools/build_precise_overrides.py'),
                         '--project',str(project),'--output',str(fresh),'--geometry-input-root',str(HERE/'inputs'),
                         '--ids',target['id'],'--asset-prefix',target['runtime_asset_prefix'],'--gltfpack',str(tool)],
                         'actual_geometry_decoder_argv':['node',str(HERE/'tools/verify_override_geometry.mjs'),str(fresh/'geometry-comparison-input.json')],
                         'output_currently_exists':False,'commands_executed':False})
    compose=[sys.executable,str(HERE/'compose_incremental.py'),'--project',str(project),'--prior-root',str(prior_root)]
    for target in lock['new_targets']:compose+=['--fresh-root',target['fresh_output']]
    compose+=['--inputs',str(HERE/'inputs'),'--output',str(HERE/'fifteen-targets')]
    d={'schema':'v11-owner-integration-preflight-v1','baseline':desc(HERE/'baseline-lock.json'),
       'actual_baseline_and_source_checks_passed':True,'existing_counts':lock['counts'],
       'future_parsed_owner_count':len(inputs),'future_parsed_macro_count':len(claimed),
       'every_old13_boundary_exact':True,'frozen_snapshot_pairs_checked':len(lock['files']),
       'prior_audited_registry':desc(prior_root/'precise-buildings-v6.json'),'prior_geometry_report':desc(prior_report),
       'current_ordinary_catalog_descriptor':current['ordinary_catalog'],
       'prior_ordinary_catalog_descriptor':prior.get('ordinary_catalog'),
       'catalog_policy':'Composer must preserve the actual current six-macro/eight-record catalog descriptor, not the historical prior four-macro descriptor.',
       'gltfpack_entry':desc(tool),'external_tool_lock':desc(HERE/'external-tool-lock.json'),
       'generation_commands':commands,'compose_after_both_actual_geometry_pass_argv':compose,
       'runtime_owner_check_after_composition_argv':['node',str(HERE/'tools/verify_override_runtime.mjs'),str(project),str(HERE/'fifteen-targets/precise-buildings-v6.json')],
       'heavy_command_execution_allowed_by_this_report':False,'near_generation_executed':False,'actual_geometry_decoder_executed':False,
       'registry_composed':False,'registration_accepted':False,'models_or_browser_accepted':False,'main_modified':False,
       'limits':['This command only reads source/metadata and parses15 source inputs.','Root schedules any actual generation/decoding after its exclusive Blender/browser workload ends.',
                 'Actual current source components are not claimed inspected by this JSON/hash preflight.','Final model-bound navigation still requires revised actual raw and browser review.']}
    out.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'report':desc(out),'counts':lock['counts'],'future_owners':len(inputs),'future_macros':len(claimed)},ensure_ascii=False))


if __name__=='__main__':main()
