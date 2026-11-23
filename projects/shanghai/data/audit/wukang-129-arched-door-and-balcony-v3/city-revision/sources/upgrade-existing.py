"""Replay one Wukang Road model upgrade on an explicitly selected immutable Shanghai city commit."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.request import urlopen

ID='xuhui-wukang-129'
MACRO='14-13718-6695'
ROOT=None
SUB='source/precise/xuhui-wukang-129/revision-3'
AUDIT='data/audit/wukang-129-arched-door-and-balcony-v3'
BYTES=lambda value:(json.dumps(value,indent=2,ensure_ascii=False)+'\n').encode()

def digest(data):return hashlib.sha256(data).hexdigest()
def sha(file):
    with file.open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def put(path,data):
    tmp=path.with_name(path.name+'.part');tmp.write_bytes(data);tmp.replace(path)
def baseline(commit,rel):
    key='projects/shanghai/'+rel
    obj=subprocess.check_output(['git','rev-parse',commit+':'+key],cwd=ROOT,text=True).strip()
    read=subprocess.run(['git','--no-lazy-fetch','cat-file','blob',obj],cwd=ROOT,stderr=subprocess.DEVNULL,stdout=subprocess.PIPE)
    if read.returncode:
        with urlopen(f'https://raw.githubusercontent.com/ecojust/e-resource/{commit}/{key}',timeout=90)as f:data=f.read()
    else:data=read.stdout
    assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==obj,key
    return data
def single(rows,needle):
    result,=[v for v in rows if v['id']==needle];return result

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--base',required=True)
parser.add_argument('--final',type=Path,required=True)
parser.add_argument('--revision',type=Path,required=True)
parser.add_argument('--repo',type=Path,default=Path.cwd(),help='Checkout showing the selected immutable city commit')
parser.add_argument('--project',type=Path,help='Project source tree, defaults to projects/shanghai in that checkout')
args=parser.parse_args()
assert re.fullmatch(r'[a-f0-9]{40}',args.base)
ROOT=args.repo.absolute()
if not (ROOT/'.git').exists() and (ROOT/'e-resource/.git').exists():ROOT=ROOT/'e-resource'
site=args.project or ROOT/'projects/shanghai';f=args.final.absolute();pack=f/'packaged'
manifest=json.loads((pack/'manifest.json').read_bytes());assert manifest['id']==ID
assert set(manifest['assets'])=={'raw','full','lod','native'}
archive=pack/(ID+'-source.zip');assert archive.is_file()
out=args.revision.parent/'drafts'/args.base;out.mkdir(parents=True,exist_ok=True)
files={}
def add(rel,path):
    data={'source':str(path.absolute()),'bytes':path.stat().st_size,'sha256':sha(path)}
    assert data['bytes']>0;files[rel]=data;return data
def submit(rel,data):
    path=out/rel;path.parent.mkdir(parents=True,exist_ok=True);put(path,data);return add(rel,path)
landmarks_path='data/landmarks.json';index_path=f'data/precise-buildings/macros/{MACRO}/index.json'
v6_path='data/precise-buildings-v6.json';directory_path='data/precise-buildings/catalog.json'
landmarks,index,v6,directory=(json.loads(baseline(args.base,k))for k in [landmarks_path,index_path,v6_path,directory_path])
original=copy.deepcopy(single(landmarks,ID));macro=single(directory['macros'],MACRO);assert original==single(index['models'],ID)
assert original['owner']['feature_local_id']==3733 and len(original['owner']['preserve_neighbor_local_ids'])==17
assert original['raw_sha256'] in [manifest['original_mesh_sha256'],manifest['assets']['raw']['sha256']], 'Another release changed this model; review the new baseline'
before=copy.deepcopy(original);other=[x for x in landmarks if x['id']!=ID];other_macro=[x for x in index['models']if x['id']!=ID]
assert macro['sha256']==digest(baseline(args.base,index_path))
assert v6['ordinary_catalog']['sha256']==digest(baseline(args.base,directory_path))
row=copy.deepcopy(original);assets=row['assets']
for source,role in [('raw','raw'),('full','web'),('lod','lod'),('native','native')]:
    item=manifest['assets'][source];path=pack/item['file'];meta=add(assets[role]['file'],path)
    assert [meta[k] for k in ('bytes','sha256')]==[item[k] for k in ('bytes','sha256')]
    for key in ['bytes','sha256']:
        row[role+'_'+key]=assets[role][key]=item[key]
    if source!='native':
        row[{'raw':'raw_triangles','full':'triangles','lod':'lod_triangles'}[source]]=item['triangles']
    add('assets/models/candidates/'+ID+'/'+item['file'],path)
row['source_package']=SUB
row['standalone_page']=manifest['viewer_page']
row['project_page']=manifest['viewer_page']
row['detail_note']=manifest['scope']
row['source_archive']={'file':'assets/models/candidates/'+ID+'/'+archive.name,'bytes':archive.stat().st_size,'sha256':sha(archive)}
row['previous_model_sha256']=manifest['original_mesh_sha256']
row['uncertainty']=['后立面、屋面纵深与端部圆弧尺度仍含估计。两扇采用2026年照片中的姿态；原铁栏杆相对两期照片均有位置偏差。']
row['photo_texture']={'mode':'original-procedural','photos_embedded':False,'note':'The coloured finish, normal and relief maps are original; both photographs are coordinate and material references.'}
# Existing acceptance belongs to previously verified release V2. Keep the
# inherited validation fields, and identify their historical scope explicitly.
row['acceptance_scope']='V2 historical model and existing city placement. V3 geometry, photographs, textures and independent UI checks are documented separately under '+AUDIT+'.'
row['revision_evidence']={'edition':3,'audit':AUDIT,'previous_validation':'V2','photo_source':manifest['photo_source'],'earlier_view':manifest['earlier_view'],'geometry_license':manifest['geometry_license']}
for rows in (landmarks,index['models']):
    target=single(rows,ID);target.clear();target.update(copy.deepcopy(row))
assert original['owner']==row['owner'] and before['confirmed_boundary']==row['confirmed_boundary'] and before['bbox']==row['bbox'] and before['anchor']==row['anchor']
assert other==[x for x in landmarks if x['id']!=ID] and other_macro==[x for x in index['models']if x['id']!=ID]
submit(landmarks_path,BYTES(landmarks));idx=submit(index_path,BYTES(index))
macro.update({k:idx[k]for k in ('sha256','bytes')})
cat=submit(directory_path,BYTES(directory))
v6['ordinary_catalog'].update({k:cat[k]for k in ('sha256','bytes')});submit(v6_path,BYTES(v6))
base_page=baseline(args.base,'landmarks.html').decode()
def extend(m):
    elem=m.group(0)
    href='href="'+manifest['viewer_page']+'"'
    if href in elem:return elem
    at=elem.rfind('</div>');assert at>=0
    return elem[:at]+' · <a '+href+'>单体预览 ↗</a>'+elem[at:]
base_page,count=re.subn(r'<article\b[^>]*\bdata-landmark="xuhui-wukang-129"[^>]*>.*?</article>',extend,base_page,flags=re.S)
assert count==1;submit('landmarks.html',base_page.encode())
add(manifest['viewer_page'],site/manifest['viewer_page'])
add(SUB+'/source/viewer.js',site/SUB/'source/viewer.js');add(SUB+'/source/cameras.json',site/SUB/'source/cameras.json')
add('assets/models/candidates/'+ID+'/manifest.json',pack/'manifest.json');add(row['source_archive']['file'],archive)
for name in ['registered-openings.jpg','view-2017.jpg','view-2026.jpg']:add(AUDIT+'/registration/'+name,f/'registration'/name)
# A new module URL makes the app fetch fresh static metadata on a mutable URL.
# Preserve any revision suffix already chosen by a later city publication.
html=baseline(args.base,'index.html').decode()
def version(m):
    value=m.group(1)
    if 'wukang129-openings-v3' not in value:value+=('&' if '?' in value else '?')+'wukang129-openings-v3=1'
    return 'src="'+value.replace('&amp;','&').replace('&','&amp;')+'"'
html,count=re.subn(r'src="(src/app\.js(?:\?[^"]*)?)"',version,html);assert count==1
submit('index.html',html.encode())
report={'base':args.base,'files':files};put(args.revision,BYTES(report))
print(len(files),sha(args.revision))
