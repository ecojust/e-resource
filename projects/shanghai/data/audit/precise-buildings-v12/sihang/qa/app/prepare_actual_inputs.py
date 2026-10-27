#!/usr/bin/env python3
"""Rebind only three app input documents after the actual runtime review passes."""
from pathlib import Path
import argparse,copy,hashlib,json,sys

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
REVISION=HERE.parent
INTEGRATION=REVISION.parent
sys.path.insert(0,str(REVISION))
import runtime_delta

ID='jingan-sihang-warehouse'
ORIGINAL=INTEGRATION/'registration-v1/actual-v6'
OUTPUT=HERE/'inputs-v6-runtime'
MODEL_DESTINATION='source/precise/'+ID+'/delivery/model-inputs.actual.json'
FROZEN={
 'model-inputs.actual.json':{'bytes':3234,'sha256':'d6877264db52687c788eb840d5606ec942a4850f6836d75470b2b0187c1c5ca3'},
 'app-spec.actual.json':{'bytes':1627,'sha256':'58bbe65e16a2786b422df96c8f2a473ac6e7fe57d5b6dc9f7434f2958dce18f5'},
 'delivery-manifest.json':{'bytes':31113,'sha256':'867354b0464144ad472f0f88a5752adcd83d45613e26e653afa063136a28d41e'},
}
MODEL_FIELDS={'registration_input','package','model_metadata','navigation_input',
              'prebrowser_summary','actual_decoded','native_render','root_native_review'}

def need(value,message):
 if not value:raise ValueError(message)
def encoded(value):
 body=(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
 need(0<len(body)<100_000_000,'Actual input document must be strictly below100000000 bytes')
 return body
def identity(body):return {'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest()}
def original_descriptor(name):return {'source':str(ORIGINAL/name),**FROZEN[name]}
def descriptor_for(name,body):return {'source':str(OUTPUT/name),**identity(body)}
def verify_originals():
 return {name:json.loads(runtime_delta.actual(original_descriptor(name)).read_bytes()) for name in FROZEN}
def verify_model_dependencies(document):
 need(document.get('schema')=='sihang-browser-model-inputs-v12' and document.get('status')=='READY_FOR_PROFILE'
      and document.get('targets')==[ID] and set(document.get('models',{}))=={ID},'Original actual standalone model input differs')
 need(set(document['models'][ID])==MODEL_FIELDS,'Exactly eight original model descriptors required')
 need(document.get('model_accepted') is False and document.get('browser_accepted') is False,'Input documents cannot create model/browser acceptance')
 for desc in document['models'][ID].values():runtime_delta.actual(desc)
 runtime_delta.actual(document['model_evidence_gate']);runtime_delta.actual(document['osm_evidence_set'])

def prepare():
 # All actual proof gates run before any output directory or JSON is created.
 runtime_inputs,_,effective=runtime_delta.load_inputs()
 reviewed=runtime_delta.evidence_record()
 need(runtime_inputs['effective_runtime_baseline']==reviewed['effective_runtime_baseline']
      and effective==runtime_delta.effective_runtime(),'Actual effective runtime binding changed')
 originals=verify_originals()
 old_model=originals['model-inputs.actual.json'];old_spec=originals['app-spec.actual.json'];old_delivery=originals['delivery-manifest.json']
 verify_model_dependencies(old_model)
 need(old_model['runtime_baseline']==runtime_delta.BASELINE and 'reviewed_runtime_delta' not in old_model,'Original model input must retain its frozen old31 baseline')
 need(old_spec.get('schema')=='sihang-app-input-v12'
      and old_spec.get('model_inputs')==original_descriptor('model-inputs.actual.json')
      and old_spec.get('model_source_delivery_manifest')==original_descriptor('delivery-manifest.json'),'Original app specification source links differ')
 need(old_delivery.get('schema')=='sihang-model-stage-delivery-manifest-v12' and old_delivery.get('building_id')==ID
      and old_delivery.get('file_count')==len(old_delivery.get('files',[]))==80,'Original actual source delivery inventory differs')
 matches=[index for index,row in enumerate(old_delivery['files']) if row.get('file')==MODEL_DESTINATION]
 need(len(matches)==1,'Exactly one existing model-input delivery row must be rebound')
 selected=matches[0];old_row=old_delivery['files'][selected]
 need({key:old_row[key] for key in ('source','bytes','sha256')}==original_descriptor('model-inputs.actual.json'),'Original selected model-input delivery row differs')
 need(not OUTPUT.exists() and not OUTPUT.is_symlink() and OUTPUT.parent==HERE,'Use the new fixed runtime input directory; existing outputs cannot be overwritten')

 model=copy.deepcopy(old_model)
 model['runtime_baseline']=copy.deepcopy(runtime_inputs['effective_runtime_baseline'])
 model['reviewed_runtime_delta']=copy.deepcopy(reviewed)
 need({key:value for key,value in model.items() if key not in ('runtime_baseline','reviewed_runtime_delta')}
      =={key:value for key,value in old_model.items() if key!='runtime_baseline'},'Runtime conversion changed model, fixture or original gate evidence')
 model_bytes=encoded(model);model_desc=descriptor_for('model-inputs.actual.json',model_bytes)

 delivery=copy.deepcopy(old_delivery)
 delivery['files'][selected].update(model_desc)
 need([row for index,row in enumerate(delivery['files']) if index!=selected]
      ==[row for index,row in enumerate(old_delivery['files']) if index!=selected],'An unrelated delivery row changed')
 need({key:value for key,value in delivery.items() if key!='files'}
      =={key:value for key,value in old_delivery.items() if key!='files'},'Original delivery metadata changed')
 need({key:value for key,value in delivery['files'][selected].items() if key not in ('source','bytes','sha256')}
      =={key:value for key,value in old_row.items() if key not in ('source','bytes','sha256')},'Model-input destination or role changed')
 delivery_bytes=encoded(delivery);delivery_desc=descriptor_for('delivery-manifest.json',delivery_bytes)

 spec=copy.deepcopy(old_spec)
 spec.update(model_inputs=model_desc,model_source_delivery_manifest=delivery_desc)
 need({key:value for key,value in spec.items() if key not in ('model_inputs','model_source_delivery_manifest')}
      =={key:value for key,value in old_spec.items() if key not in ('model_inputs','model_source_delivery_manifest')},'An unrelated app specification field changed')
 spec_bytes=encoded(spec);spec_desc=descriptor_for('app-spec.actual.json',spec_bytes)
 need(verify_originals()==originals and runtime_delta.evidence_record()==reviewed,'Actual source/runtime input changed before output')
 verify_model_dependencies(old_model)

 OUTPUT.mkdir()
 marker=OUTPUT/'INCOMPLETE';marker.write_text('Input conversion is incomplete; do not use these documents.\n')
 for name,body in [('model-inputs.actual.json',model_bytes),('delivery-manifest.json',delivery_bytes)]:
  with (OUTPUT/name).open('xb') as stream:stream.write(body)
 need(verify_originals()==originals and runtime_delta.evidence_record()==reviewed,'Actual input changed during output; INCOMPLETE retained')
 # Publish the caller-facing app spec last, only after the two linked JSONs exist.
 with (OUTPUT/'app-spec.actual.json').open('xb') as stream:stream.write(spec_bytes)
 for desc in (model_desc,delivery_desc,spec_desc):runtime_delta.actual(desc)
 marker.unlink()
 return {'model_inputs':model_desc,'delivery_manifest':delivery_desc,'app_spec':spec_desc,
         'unchanged_model_descriptor_count':8,'changed_delivery_row_count':1,
         'original_model_gate_and_fixture_preserved':True,'runtime_delta':reviewed,
         'candidate_created':False,'model_accepted':False,'browser_accepted':False,'main_written':False}

def main():
 argparse.ArgumentParser(description=__doc__).parse_args()
 print(json.dumps(prepare(),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
