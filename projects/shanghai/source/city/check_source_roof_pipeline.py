"""Small local pipeline fixture: no production export or raster sampling."""
from pathlib import Path
from types import SimpleNamespace
from copy import deepcopy
import gzip, hashlib, json, subprocess, sys, tempfile
import build_fullcity_models as builder
import build_source_roof_patches as patcher
import roof_geometry


def main():
    with tempfile.TemporaryDirectory(prefix='roof-pipeline-check-') as temp:
        root=Path(temp); raw=root/'raw'; base=root/'base'; patch=root/'patch'; second=root/'default-repeat'
        tile=[14,13720,6693]; cell='-'.join(map(str,tile)); origin=[121.485,31.24]
        def feature(identity,offset):
            x,y=origin[0]+offset,origin[1]
            return {'type':'Feature','geometry':{'type':'Polygon','coordinates':[[[x,y],[x+.0001,y],[x+.0001,y+.00008],[x,y+.00008],[x,y]]]},
                'properties':{'id':identity,'source_layer':'building','district_id':'310101','height':10,
                    'min_height':0,'roof_height':2,'roof_shape':'gabled','@geometry_source':'test fixture'}}
        features=[feature('roof-a',0),feature('ordinary-b',.001)]
        source=raw/'tiles/14/13720/6693.geojson.gz';source.parent.mkdir(parents=True)
        with gzip.open(source,'wt') as stream: json.dump({'type':'FeatureCollection','metadata':{'tile':tile,'origin':origin},'features':features},stream)
        patcher.write_json(raw/'manifest.json',{'complete':True,'unique_feature_count':2,'renderable_feature_count':2})
        exclusions=root/'exclusions.json'; residuals=root/'residuals.json'
        patcher.write_json(exclusions,{'building_ids':[],'building_part_ids':[]})
        patcher.write_json(residuals,{})
        options={'output':str(base),'sampler_version':'fixture','configuration_sha256':'base-fixture',
            'compress':False,'target_bytes':1000,'parent_residuals':str(residuals),'landmark_exclusions':json.loads(exclusions.read_text())}
        # Both buildings have explicit source heights; a sentinel proves no
        # hidden raster sampling is required by this fixture.
        class NoSampler:
            def sample_geometry(self,*args): raise AssertionError('Unexpected height resampling')
        builder._SAMPLER=NoSampler();builder._RESIDUALS={}
        builder.export_source(str(source),options)
        builder.export_source(str(source),{**options,'output':str(second)})
        state=json.loads((base/'state'/(cell+'.json')).read_text())
        assert set(state['models'])=={cell+'-s0',cell+'-s1'}
        for identity in state['models']:
            assert patcher.sha(base/'tiles'/(identity+'.glb'))==patcher.sha(second/'tiles'/(identity+'.glb')), 'Default export bytes changed'
        manifest=builder.build_manifest(base,raw,True,[])
        manifest.update({'detail_patch':{'unchanged_fixture_marker':True},'detailed_landmark_record_count':14})
        patcher.write_json(base/'manifest.json',manifest)
        patcher.write_json(base/'build-configuration.json',{'target_bytes':1000,
            'landmark_exclusions_sha256':patcher.sha(exclusions),'parent_residual_file_sha256':patcher.sha(residuals)})
        qualified=root/'qualified.json'
        entry={'key':'building:roof-a','id':'roof-a','source_layer':'building','district_id':'310101',
            'owner_tile':tile,'source_sha256':patcher.sha(source),'origin':origin,'geometry':features[0]['geometry'],
            'original_properties':features[0]['properties'],'roof_shape':'gabled','roof_height':2,'height':10,'base':0,'ridge_unit':[1,0]}
        patcher.write_json(qualified,{'schema_version':'fixture-v1','complete':True,'roofs':[entry]})
        args=SimpleNamespace(raw=raw,base_models=base,qualified_roofs=qualified,landmark_exclusions=exclusions,parent_residuals=residuals)
        plan,overrides,_,_=patcher.make_plan(args,builder)
        patch_options={**options,'output':str(patch),'target_bytes':99_000_000,'configuration_sha256':'roof-fixture',
            'roof_overrides':overrides,'fixed_output_ids':{cell:state['models']},
            'roof_qualification_sha256':patcher.sha(qualified),'roof_geometry_version':roof_geometry.VERSION}
        builder.export_source(str(source),patch_options)
        records,files=patcher.validate_cell(patch,base,plan['affected_owner_cells'][0],'roof-fixture',builder)
        assert len(records)==2 and sum(r.get('source_roof_enhancement',{}).get('count',0) for r in records)==1
        assert all(r['feature_ids_sha256']==json.loads((base/'records'/(r['id']+'.json')).read_text())['feature_ids_sha256'] for r in records)
        stats=[item for r in records for item in r.get('source_roof_enhancement',{}).get('roof_stats',[])]
        assert stats[0]['geometry_stats']['roof_shape']=='gabled'
        bad=deepcopy(features);bad[0]['properties']['renderable']=False
        try: builder.create_meshes(bad,origin,None,overrides)
        except ValueError: pass
        else: raise AssertionError('Nonrenderable accepted roof silently dropped')
        bad=deepcopy(features);bad[0]['geometry']['coordinates']=[[[origin[0],origin[1]]]*4]
        try: builder.create_meshes(bad,origin,None,overrides)
        except ValueError: pass
        else: raise AssertionError('Degenerate accepted roof silently dropped')
        changed=deepcopy(entry);changed['roof_height']=3
        patcher.write_json(qualified,{'schema_version':'fixture-v1','complete':True,'roofs':[changed]})
        try: patcher.make_plan(args,builder)
        except ValueError: pass
        else: raise AssertionError('Normalized parameters can disagree with source')
        patcher.write_json(qualified,{'schema_version':'fixture-v1','complete':True,'roofs':[entry]})
        # Create only the complete, validated patch metadata needed by the
        # production merge command, then exercise the actual merge subprocess.
        records.sort(key=lambda r:r['id'])
        patcher.write_json(patch/'patch-manifest.json',{**plan,'complete':True,'configuration_sha256':'roof-fixture','records':records})
        patcher.write_json(patch/'patch-plan.json',plan)
        patcher.write_json(patch/'build-configuration.json',{'fixture':True})
        patcher.write_json(patch/'roof-validation.json',{'complete':True,'roofs':stats})
        (patch/'qualified-roofs.json').write_bytes(qualified.read_bytes())
        before_manifest=patcher.sha(base/'manifest.json');before_models={r['id']:patcher.sha(base/r['file']) for r in records}
        merged=root/'merged'
        command=[sys.executable,str(Path(__file__).with_name('merge_source_roof_patches.py')),
            '--base-models',str(base),'--patch',str(patch),'--output',str(merged),'--raw',str(raw)]
        result=subprocess.run(command,capture_output=True,text=True)
        assert result.returncode==0,result.stderr
        final=json.loads((merged/'manifest.json').read_text())
        assert final['model_count']==2 and final['feature_count']==2
        assert final['detail_patch']==manifest['detail_patch'] and final['detailed_landmark_record_count']==14
        assert final['source_roof_enhancement']['count']==1
        assert patcher.sha(base/'manifest.json')==before_manifest
        assert all(patcher.sha(base/'tiles'/(identity+'.glb'))==digest for identity,digest in before_models.items())
        for path in (merged/'districts').glob('*.json'):
            for record in json.loads(path.read_text())['tiles']:
                assert patcher.sha((path.parent/record['file']).resolve())==record['sha256']
                assert patcher.sha((path.parent/record['feature_ids_file']).resolve())==record['feature_ids_sha256']
        print(json.dumps({'ok':True,'tests':['default export byte stability','existing split retained despite target change',
            'accepted roof applied exactly once','unchanged IDs/counts/heights/footprints','nonrenderable and degenerate acceptance fails',
            'normalized parameters must match raw source','actual isolated merge','detail_patch and 14 landmarks preserved',
            'base files unchanged','district index hashes match']}))


if __name__=='__main__':main()
