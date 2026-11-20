"""Run the shared Three.js and vector clipping checker with the recorded 52-address source and neighboring footprints."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

from shapely.geometry import Point, shape

AUDIT = Path(__file__).resolve().parent
MODEL = 'huangpu-xiaotaoyuan-mosque-prayer-hall'
NEIGHBORS = (1556, 1035, 2419)
def read(path):return json.loads(path.read_bytes())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',type=Path,required=True)
    parser.add_argument('--macro',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=AUDIT)
    args=parser.parse_args();project=args.project.resolve();folder=args.output.resolve(); folder.mkdir(exist_ok=True,parents=True)
    audit_contract=AUDIT/'final-placement-contract.json';contract=read(audit_contract);details=read(AUDIT/'footprint-review.json')
    source=project/'source/precise'/MODEL/'footprint-review.json';records=read(source); macro=records['macro_id'];owner=contract['owner']['feature_local_id']
    ready=args.macro/'READY.json';table=args.macro/'feature-table.json.gz'
    for f in (ready,table):assert sha(f)==records['frozen_bindings'][f.name]['sha256']
    features={r['localId']:r for r in json.loads(gzip.decompress(table.read_bytes()))['features']}
    near=read(ready)['near']
    chosen=[next(g for g in near if i in g['featureLocalIds'])for i in (owner,NEIGHBORS[0])]
    assert chosen[0]['featureLocalIds']==records['near_groups'][0]['ids'] and owner not in chosen[1]['featureLocalIds']
    data={'frozen_macro':macro,'near_tiles':[{'id':g['id'],'feature_local_ids':g['featureLocalIds']}for g in chosen],'owners':[{'local_id':i,'key':features[i]['key'],'record_id':features[i]['properties']['id'],'height':features[i]['height'],'geometry':features[i]['geometry']}for i in (owner,*NEIGHBORS)]}
    mask=shape(contract['replacement_geometry'])
    case={'id':MODEL,'neighbors':NEIGHBORS,'groupTriangles':2,'sourceSectionCount':2,'ground':[{'name':r['label'],'xy':r['local_xy'],'expected':'building' if r['expected_in_scene']else None,'modelObstacle':r['blocked'],'cut':mask.covers(Point(r['world']))}for r in details['ground_probes']],
          'neighborGround':{str(i):list(shape(features[i]['geometry']).representative_point().coords[0])for i in NEIGHBORS}}
    with TemporaryDirectory()as scratch:
        root=Path(scratch);sample=root/'source/precise'/MODEL;sample.mkdir(parents=True)
        for name in ('src','vendor','data'):(root/name).symlink_to(project/name,target_is_directory=True)
        (sample/'footprint-review.json').write_text(json.dumps(data))
        job=root/'case';job.mkdir();(job/'final-placement-contract.json').symlink_to(audit_contract)
        casefile=job/'map-case.json';casefile.write_text(json.dumps(case,ensure_ascii=False,indent=2)+'\n')
        subprocess.run(['node',project/'tools/check-sourced-candidate-runtime.mjs',casefile],check=True,env={**os.environ,'SHANGHAI_PROJECT_ROOT':str(root),'QA_OUTPUT_DIR':str(folder)})
        proof=read(folder/'runtime-placement.json');assert proof['after']['scopedTargetDraw']['clip_feature_local_ids']==[owner]
        proof.update(source_review_sha256=sha(source),macro_index_sha256=sha(ready),feature_table_sha256=sha(table),wrapper_sha256=sha(Path(__file__)),runtime_case=case)
        (folder/'runtime-placement.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
