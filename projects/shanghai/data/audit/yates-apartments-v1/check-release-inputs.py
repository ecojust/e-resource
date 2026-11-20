"""Read two actual release endpoints, and bind the tested Yates Apartments controls and byte-identical downloads."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,datetime,requests
import argparse
a=Path(__file__).resolve().parent
args=argparse.ArgumentParser(description=__doc__)
args.add_argument('--snapshots',required=True,type=Path,help='Directory containing 107-production.json and 108-production.json.')
args.add_argument('--before-url',required=True)
args.add_argument('--after-url',required=True)
args.add_argument('--report',type=Path,default=a/'147-148-preflight.json')
opts=args.parse_args()
release=opts.snapshots
urls={107:opts.before_url,108:opts.after_url}
catalog='data/candidate-city-integrations.json';ident='jingan-yates-apartments';proof=json.loads((a/'final-placement-contract.json').read_bytes())
control=json.loads((a/'map-case.json').read_bytes())
def get(n,name):
 u=urls[n].rstrip('/')+'/'+name
 r=requests.get(u,timeout=40);r.raise_for_status();b=r.content
 return b,{'url':u,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
snap={i:json.loads((release/(str(i)+'-production.json')).read_bytes())for i in (107,108)}
versions=[];cats=[]
for i in (107,108):
 b,rec=get(i,catalog);v=json.loads(b);assert len(b)==rec['bytes'] and rec['sha256']==snap[i]['files'][catalog]
 assert v['resulting_city_count']==i+40
 versions.append(dict(catalog=rec,count=v['resulting_city_count']));cats.append(v)
assert cats[1]['models'][:-1]==cats[0]['models'] and all(r['id']!=ident for r in cats[0]['models'])
r=cats[1]['models'][-1];assert r['id']==ident and proof['owner']==r['owner'] and r['owner']['feature_local_id']==1964
for key in ('source_feature_ids','source_section_caps','model_geometry_sha256','replacement_geometry','collision_geometry','lng','lat','heading','scale','altitude','overviewBearing','overviewPitch','overviewZoom'):
 assert (key in r)==(key in proof) and r.get(key)==proof.get(key),key
mf=r['candidate_manifest'];man_b,mf_rec=get(108,mf);man=json.loads(man_b);assert mf_rec['sha256']==snap[108]['files'][mf]
page=man['viewer_page'];assets={k:str(Path(mf).parent/v['file']) for k,v in man['assets'].items()}
shared=('index.html','landmarks.html','src/app.js','src/map-scene.js','src/building-beacons.js','src/building-beacon-groups.js')
tasks=[(i,f)for i in (107,108)for f in shared]+[(108,name)for name in (page,*assets.values())]
def check(t):
 i,name=t;b,r=get(i,name);expect=snap[i]['files'][name];assert r['sha256']==expect
 return f'{i}/{name}',r
inputs=dict(ThreadPoolExecutor(3).map(check,tasks))
for k,file in assets.items():
 rec=inputs['108/'+file];assert rec['bytes']==man['assets'][k]['bytes'] and rec['sha256']==man['assets'][k]['sha256']
output={'observed':datetime.datetime.now(datetime.timezone.utc).isoformat(),'id':ident,'real_releases':versions,'all_prior_candidate_rows_unchanged':len(cats[0]['models']),'source_ownership':proof['owner'],'scale':r['scale'],'heading':r['heading'],'normal_overview':{k:r[k] for k in ('overviewBearing','overviewPitch','overviewZoom')},'model_manifest':mf_rec,'actual_release_files':inputs,'neighbors_from_source_case':control['neighbors'],'ground_cases':len(control['ground']),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
opts.report.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
print('Verified',len(inputs),'HTTP responses, all 4 model downloads, previous and final catalogs,',len(cats[0]['models']),'unchanged prior models')
