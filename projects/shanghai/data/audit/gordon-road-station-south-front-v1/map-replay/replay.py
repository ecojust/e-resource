"""Compare the two frozen catalogues and rerun the approved owner and collision tests."""
from pathlib import Path
from hashlib import sha256
from urllib.request import urlopen
import argparse,gzip,json,os,subprocess,tempfile,shutil
cli=argparse.ArgumentParser()
cli.add_argument('output',type=Path)
cli.add_argument('--source',type=Path,help='Optional local copy of the frozen JavaScript modules')
args=cli.parse_args()
here=Path(__file__).absolute().parent
audit=here.parent
project=audit.parents[2]
def read(f):return json.loads(f.read_bytes())
signed=read(here/'signed-inputs.json')
catalogues=[]
for n in (313,314):
 item=signed['orders'][str(n)];b=gzip.decompress((here/item['catalog']).read_bytes());assert sha256(b).hexdigest()==item['catalog_sha256']
 cat=json.loads(b);assert cat['resulting_city_count']==item['city_count'];catalogues.append(cat)
parent,child=catalogues;assert child['models'][:-1]==parent['models'] and len(child['models'])==len(parent['models'])+1
row=child['models'][-1];contract=read(audit/'final-placement-contract.json')
assert row['id']==signed['model_id']==contract['id']
for k in ('owner','source_feature_ids','replacement_geometry','collision_geometry','source_section_caps','model_geometry_sha256','heading','lng','lat','overviewPitch','overviewZoom','overviewBearing'):
 assert contract[k]==row[k],k
assert row['owner']=={'macro_id':'14-13719-6694','feature_local_id':1295}
with tempfile.TemporaryDirectory() as temp:
 site=Path(temp)/'scene';site.mkdir();(site/'package.json').write_text('{"type":"module"}')
 for key,entry in signed['renderer_modules'].items():
  local=(args.source or project)/key
  if local.is_file() and sha256(local.read_bytes()).hexdigest()==entry['sha256']:body=local.read_bytes()
  else:
   with urlopen(entry['url'],timeout=60)as response:assert response.status==200;body=response.read()
  assert len(body)==entry['bytes'] and sha256(body).hexdigest()==entry['sha256']
  dest=site/key;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(body)
 key='data/candidate-city-integrations.json';dest=site/key;dest.parent.mkdir(parents=True)
 dest.write_bytes(gzip.decompress((here/signed['orders']['314']['catalog']).read_bytes()))
 key='source/precise/'+row['id']+'/footprint-review.json';dest=site/key;dest.parent.mkdir(parents=True);shutil.copyfile(project/key,dest)
 check=Path(temp)/'audit';check.mkdir()
 for file in ['map-case.json','final-placement-contract.json']:shutil.copyfile(audit/file,check/file)
 subprocess.run(['node',here/'check-map.mjs',check/'map-case.json'],check=True,env={**os.environ,'SHANGHAI_PROJECT_ROOT':str(site)})
 vecout=Path(temp)/'vector.json'
 subprocess.run(['node',here/'check-vector.mjs',audit/'final-placement-contract.json',here/'catalog-313.json.gz',vecout,site],check=True)
 assert read(vecout)==read(here/'vector-313.json')
 runtime=read(check/'runtime-placement.json')
 assert runtime==read(audit/'runtime-placement.json')
 result=dict(model_id=row['id'],previous_count=parent['resulting_city_count'],current_count=child['resulting_city_count'],unchanged_candidate_rows=len(parent['models']),owner=row['owner'],runtime=runtime)
 args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
