#!/usr/bin/env python3
"""Add actual v3 ridge-contact/preservation evidence to the frozen registrar draft.
The frozen construction/previous preparation script is unchanged; no installation.
"""
import argparse,hashlib,json,os,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
BASELINE='a96343eef1f9c11a38dce37b113545a8abea720ffed3b58952024e51c76b73af'
def load(p):return json.loads(Path(p).read_text())
def digest(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def desc(p):
 p=Path(p).resolve();return {'source':str(p),'bytes':p.stat().st_size,'sha256':digest(p)}
def replace_json(p,data):
 temp=p.with_name('.'+p.name+'.v3-tmp')
 with temp.open('x') as f:json.dump(data,f,ensure_ascii=False,indent=2);f.write('\n')
 os.replace(temp,p)
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('run','native-review','navigation','ridge-proof'):p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();run=a.run.resolve();proof=load(a.ridge_proof);package=load(run/'package/packaging-record.json')
 assert proof['schema']=='longhua-v3-actual-preservation-and-ridge-contact-v1'
 assert proof['passed'] is True and proof['raw']['sha256']==package['assets']['raw']['sha256']
 assert proof['baseline_raw']['sha256']==BASELINE and proof['preserved_old_parts_count']==17983 and proof['new_ridge_seats_count']==56
 assert all(proof[key] is True for key in ('old_geometry_materials_byte_exact','new_seat_topology_passed','finite_contact_passed'))
 proof_descriptor=desc(a.ridge_proof)
 subprocess.run([sys.executable,str(HERE/'prepare_registration.py'),'--run',str(run),'--native-review',str(a.native_review),'--navigation',str(a.navigation)],check=True,capture_output=True,text=True)
 summary_path=run/'prebrowser-acceptance-summary.json';registration_path=run/'registration.draft.json';metadata_path=run/'model-metadata.json'
 summary=load(summary_path);summary['evidence']['actual_v3_preservation_contact']=proof_descriptor
 summary['roof']['scope']+=' The 56 new solid grey ridge seats pass finite actual triangle contact checks against unchanged roof and ridges; decorative t>1 tips may cantilever.'
 summary['geometry_proof']['scope']+=' All17983 previous v2 parts retain exact oriented POSITION/NORMAL and materials; only56 additional ridge-seat parts are present. This remains finite contact evidence, not whole-model collision freedom.'
 replace_json(summary_path,summary);updated_summary=desc(summary_path)
 registration=load(registration_path)
 for stage,record in registration['buildings'][0]['acceptance'].items():
  if record['status']=='passed':record['evidence']=updated_summary
 replace_json(registration_path,registration)
 metadata=load(metadata_path);metadata['actual_v3_preservation_contact_evidence']=proof_descriptor;replace_json(metadata_path,metadata)
 assert desc(a.ridge_proof)==proof_descriptor
 print(json.dumps({'summary':desc(summary_path),'registration':desc(registration_path),'model_metadata':desc(metadata_path),'browser_passed':False},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
