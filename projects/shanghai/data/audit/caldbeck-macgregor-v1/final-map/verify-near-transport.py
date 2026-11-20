"""Check the registered ordinary-building override against three real city sites and the original source triangles."""
import argparse,gzip,hashlib,json,os,subprocess,sys
from pathlib import Path
from urllib.request import urlopen
from concurrent.futures import ThreadPoolExecutor
import numpy as np,shapely
from shapely.geometry import shape

def digest(b):return hashlib.sha256(b).hexdigest()
def get(url,size=None,expected=None):
    with urlopen(url,timeout=50)as rs:b=rs.read();assert rs.status==200
    if size is not None:assert len(b)==size
    if expected is not None:assert digest(b)==expected
    return b,{'url':url,'bytes':len(b),'sha256':digest(b)}
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--project',type=Path,required=True);p.add_argument('--work',type=Path,required=True);p.add_argument('--case',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
p.add_argument('--scenes',nargs=3,required=True,help='Three complete predecessor, before and after URLs.')
a=p.parse_args();a.work.mkdir(parents=True,exist_ok=True);case=json.loads(a.case.read_bytes());au=a.case.parent;contract=json.load(open(au/'final-placement-contract.json'));project=a.project.resolve();sys.path.insert(0,str(project/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write
review=read(project/'source/precise'/case['id']/'footprint-review.json');owner=contract['owner']['feature_local_id'];group=next(t for t in review['near_tiles']if owner in t['feature_local_ids']);macro=review['frozen_macro']
def receive(url):
    url=url.rstrip('/')+'/';b,meta=get(url+'data/precise-buildings-v6.json');index=json.loads(b);cat,catrec=get(url+'data/candidate-city-integrations.json');cat=json.loads(cat)
    m=next(q for q in index['macros']if q['id']==macro);over=next(t for t in m['near']if t['id']==group['id'])
    original=next(t for t in review['frozen_bindings']if t['repository_path'].endswith('/'+group['file']));origrel=original['repository_path'].removeprefix('projects/shanghai/')
    baseline,brec=get(url+origrel,original['bytes'],original['sha256']);data,orec=get(url+over['model']['file'],over['model']['size_bytes'],over['model']['sha256'])
    assert digest(gzip.decompress(baseline))==over['baseline_decoded_sha256']
    assert digest(gzip.decompress(data))==over['model']['decoded_sha256']
    assert set(over['featureLocalIds'])==set(group['feature_local_ids']) and owner not in {i for g in over['groups']for i in g['local_ids']}
    return {'count':cat['resulting_city_count'],'catalog':catrec,'manifest':meta,'original':brec,'active':orec,'decoded_sha256':digest(gzip.decompress(data)),'in_catalog':any(t['id']==case['id']for t in cat['models'])},over,data,baseline
# Sequential to keep the real endpoint's live map traffic ahead of these small reads.
got=[receive(u)for u in a.scenes];rows=[g[0]for g in got]
assert [v['in_catalog']for v in rows]==[False,False,True]and rows[2]['count']==rows[1]['count']+1
assert all(g[1]==got[0][1]and g[2]==got[0][2]and g[3]==got[0][3]for g in got)
for rec in review['frozen_bindings']:
 n=Path(rec['repository_path']).name;dest=a.work/n
 if not dest.exists():dest.write_bytes(get(a.scenes[-1].rstrip('/')+'/'+rec['repository_path'].removeprefix('projects/shanghai/'),rec['bytes'],rec['sha256'])[0])
ctx=PlacementMeshes(project,a.work,review);dec=project/'data/audit/postal-office-v1/map-decode-source.mjs'
ctx.link('baseline-far.glb',ctx.files['far.glb']);ctx.link('macro-READY.json',ctx.files['READY.json']);write(a.work/'context-features.json',[dict(localId=i)for i in group['feature_local_ids']])
mask=shapely.transform(shape(contract['replacement_geometry']),ctx.to_xy);ids=np.array(group['feature_local_ids']);fields={}
for label,content in [('baseline',got[-1][3]),('active',got[-1][2])]:
    f=a.work/(label+'.gz');f.write_bytes(content);ctx.link('baseline-near.glb.gz',f)
    subprocess.run(['node',dec],env=ctx.env,check=True,stdout=subprocess.DEVNULL)
    tris=np.fromfile(a.work/'baseline-near-triangles.f64').reshape(-1,3,3);tris[:,:,:2]=tris[:,:,:2]@ctx.axes.T
    pts=shapely.points(tris.mean(axis=1)[:,:2]);dist=np.stack([shapely.distance(pts,ctx.footprints[i])for i in ids],axis=1);ownership=ids[dist.argmin(1)]
    measures={}
    for i in ids:
        sel=tris[ownership==i];q=np.rint(sel*1e5).astype('<i8')
        # Canonical vertex order and triangle order permit draw and winding reordering.
        ix=np.lexsort((q[:,:,2],q[:,:,1],q[:,:,0]),axis=1);q=np.take_along_axis(q,ix[:,:,None],axis=1).reshape(-1,9)
        q=q[np.lexsort(q[:,::-1].T)];measures[str(i)]=dict(triangles=len(q),surface_sha256_10um=digest(q.tobytes()))
        if i==owner:
            g=ctx.project_faces(sel);remain=g.difference(mask);measures[str(i)].update(native_m2=g.area,remaining_m2=remain.area,retained_fraction=remain.area/g.area,cut_m2=g.intersection(mask).area)
    fields[label]={'surfaces':measures,'total_triangles':len(tris)}
for i in ids:
    orig=fields['baseline']['surfaces'][str(i)];active=fields['active']['surfaces'][str(i)]
    assert orig['triangles']==active['triangles']and orig['surface_sha256_10um']==active['surface_sha256_10um'],(i,orig,active)
assert abs(fields['baseline']['surfaces'][str(owner)]['remaining_m2']-fields['active']['surfaces'][str(owner)]['remaining_m2'])<.001
write(a.out,{'id':case['id'],'completed':True,'script_sha256':digest(Path(__file__).read_bytes()),'group':group['id'],'tracked_owner':owner,'declared_separate_named_groups':got[-1][1]['groups'],'source_owner_ids':ids.tolist(),'three_city_sites':rows,'decoded_checks':fields})
print(rows[-1]['active'],fields['active']['surfaces'][str(owner)])
