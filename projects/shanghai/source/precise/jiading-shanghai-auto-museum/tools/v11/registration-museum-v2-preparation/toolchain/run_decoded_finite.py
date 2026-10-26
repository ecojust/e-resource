#!/usr/bin/env python3
"""Bridge actual decoded ENU arrays to the independent finite engine; no model generation."""
from pathlib import Path
import argparse,hashlib,json,re,sys
import numpy as np
from modern_contract import bound,load,require,sha,target

HERE=Path(__file__).resolve().parent

def descriptor(path):
    p=Path(path).resolve();return {'source':str(p),'bytes':p.stat().st_size,'sha256':sha(p)}

def run(input_path,output):
    require(not output.exists(),'Use a new immutable output report')
    request=load(input_path)
    require(request.get('schema')=='modern-decoded-finite-role-input-v11','Unknown actual decoded input schema')
    t=target(bound(request['target']))
    role=request['role'];require(role in ('raw','web','lod','authored_lod'),'Unknown decoded role')
    require(request['requests']==t['actual']['probe_set'],'Finite request target binding differs')
    finite_requests=load(bound(request['requests']))
    structure_path=bound(t['actual']['source_structure_report'])
    require(finite_requests.get('schema')=='modern-finite-requests-v1' and finite_requests.get('state')=='READY_FOR_ACTUAL_AUDIT','Finite request remains pending')
    require(finite_requests['model_id']==t['id'],'Finite model identity differs')
    binding=finite_requests['source_binding']
    require(binding['raw_sha256']==t['actual']['raw']['sha256'] and binding['geometry_input_sha256']==t['source_geometry']['sha256'] and binding['source_freeze_sha256']==t['actual']['source_freeze']['sha256'] and binding['structure_report_sha256']==t['actual']['source_structure_report']['sha256'],'Finite source proof changed')
    for key in finite_requests.get('allowed_omitted_part_keys',[]):
        value=json.loads(key)
        require(len(value)==3 and any(re.search(pattern,value[0]) for pattern in t['lod_policy']['allowed_omission_label_patterns']),'Finite request allows unapproved LOD geometry loss')
    lock_path=HERE/'independent-engine-lock.json';lock=load(lock_path)
    require(lock.get('status')=='frozen','Independent finite engine has not been frozen')
    for row in lock['files']:
        local=HERE/row['local'];require(local.is_file() and local.stat().st_size==row['bytes'] and sha(local)==row['sha256'],'Independent engine copy changed')
        original=Path(row['source']);require(original.stat().st_size==row['bytes'] and sha(original)==row['sha256'],'Original independent engine revision changed')
    sys.dont_write_bytecode=True;sys.path.insert(0,str(HERE/'engine'))
    from modern_mesh import Asset,Part
    from finite_checks import run_checks
    manifest_path=bound(request['decoded_array_manifest']);manifest=load(manifest_path)
    require(manifest.get('schema')=='modern-decoded-semantic-arrays-v11' and manifest['building_id']==t['id'] and manifest['role']==role,'Actual semantic array identity differs')
    current_path=bound(manifest['asset'])
    require(manifest['source_geometry_sha256']==t['source_geometry']['sha256'],'Semantic source geometry differs')
    require(manifest['coordinate_system']=='ENU metres' and manifest['chunks'],'Missing actual ENU arrays')
    require(manifest['extras']['id']==t['id'] and manifest['extras']['source_geometry_sha256']==t['source_geometry']['sha256'] and manifest['extras']['calibration_sha256']==binding['calibration_sha256'],'Actual decoded glTF metadata differs')
    expected_semantic=t['actual']['authored_lod'] if role in ('lod','authored_lod') and t['lod_policy']['mode']=='authored-subtraction' else t['actual']['raw']
    require(manifest['semantic_source_asset_sha256']==expected_semantic['sha256'],'Actual semantic source differs')
    buffers=[]
    for chunk in manifest['chunks']:
        file=bound(chunk);require(chunk['bytes']<=64*1024*1024 and chunk['bytes']%144==0,'Invalid finite-array chunk')
        values=np.fromfile(file,dtype='<f8').reshape(-1,18);require(np.isfinite(values).all(),'Nonfinite decoded triangle or normal');buffers.append(values)
    values=np.concatenate(buffers);require(len(values)==manifest['triangle_count'],'Actual decoded triangle count differs');del buffers
    parts=[];cursor=0;keys=set()
    for row in manifest['parts']:
        require(row['key'] not in keys and row['first_triangle']==cursor and row['primitive_index']==-1 and row['triangle_count']>0,'Missing, duplicate or falsely indexed decoded part')
        keys.add(row['key']);key=json.loads(row['key']);require(key[:2]==[row['label'],row['material']] and type(key[2]) is int,'Semantic ordinal identity differs')
        end=cursor+row['triangle_count'];require(end<=len(values),'Part exceeds actual decoded triangles')
        data=values[cursor:end];parts.append(Part(row['key'],row['label'],row['material'],data[:,:9].reshape(-1,3,3),data[:,9:].reshape(-1,3,3),-1,-1));cursor=end
    require(cursor==len(values) and parts,'Actual decoded part coverage incomplete')
    identity={'asset':manifest['asset'],'decoded_array_manifest':request['decoded_array_manifest'],'semantic_source_asset_sha256':manifest['semantic_source_asset_sha256'],'semantic_source_sidecar':manifest['semantic_source_sidecar'],'representation':'Actual GLTFLoader+Meshopt '+role+' expanded into ENU Float64 with independently reconstructed per-part triangle copies','raw_indices_reused_for_compressed_asset':False,'temporary_chunks':manifest['chunks'],'temporary_chunk_retention':manifest['chunk_retention']}
    asset=Asset(identity,parts,manifest['materials'],manifest['extras'])
    actual=run_checks(asset,finite_requests,source_structure_report_path=structure_path)
    require(actual['schema']=='modern-actual-finite-checks-v1','Unknown finite engine result schema')
    report={'schema':'modern-actual-decoded-finite-role-v11','passed':actual['finite_checks_passed'] is True,'building_id':t['id'],'role':role,'source_geometry_sha256':t['source_geometry']['sha256'],'raw_sha256':t['actual']['raw']['sha256'],'current_asset':manifest['asset'],'array_manifest':request['decoded_array_manifest'],'requests':request['requests'],'source_structure_report':t['actual']['source_structure_report'],'independent_engine_lock':descriptor(lock_path),'bridge':descriptor(Path(__file__)),'actual_finite_result':actual,'browser_accepted':False,'native_visual_accepted':False}
    require(sha(current_path)==manifest['asset']['sha256'],'Current compressed asset changed during finite check')
    for chunk in manifest['chunks']:bound(chunk)
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x') as stream:json.dump(report,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    try:r=run(a.input,a.output)
    except (ValueError,KeyError,OSError,AssertionError) as exc:p.exit(1,'Decoded finite checks rejected: '+str(exc)+'\n')
    print(json.dumps({'passed':r['passed'],'building_id':r['building_id'],'role':r['role'],'output':str(a.output)}))
    raise SystemExit(0 if r['passed'] else 1)
if __name__=='__main__':main()
