"""Verify a complete existing ordinary building revision against its previously published city scene."""
import argparse
from datetime import datetime,timezone
import hashlib,json,subprocess
from pathlib import Path

PROJECT=Path(__file__).resolve().parents[1]
REPO=PROJECT.parents[1]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('task')
    parser.add_argument('baseline')
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    commit=subprocess.check_output(['git','rev-parse','--verify',args.baseline+'^{commit}'],cwd=REPO,text=True).strip()
    def previous(path):
        return json.loads(subprocess.check_output(['git','show',f'{commit}:projects/shanghai/{path}'],cwd=REPO))
    def read(path):
        return json.loads((PROJECT/path).read_bytes())
    def one(rows,ident):
        row,=[r for r in rows if r['id']==ident]
        return row
    def check_file(asset):
        path=PROJECT/asset['file'];body=path.read_bytes()
        assert len(body)==asset['bytes'] and hashlib.sha256(body).hexdigest()==asset['sha256']
    queue=read('data/model-todo/queue.json');job=one(queue['production_queue'],args.task)
    ident=job['refines_existing_model'];mf=REPO/job['manifest'];meta=json.loads(mf.read_bytes())
    assert meta['id']==ident and meta['url_base']=='project-root'
    path='data/landmarks.json';older=previous(path);now=read(path);prior,target=one(older,ident),one(now,ident)
    assert [r['id'] for r in older]==[r['id'] for r in now]
    assert [r for r in older if r['id']!=ident]==[r for r in now if r['id']!=ident]
    for k in ('id','anchor','lng','lat','height_m','bbox','navigation','owner','confirmed_boundary','geometry_input_sha256'):
        assert target[k]==prior[k],k
    pointer='data/precise-buildings/by-id/'+ident+'.json';assert previous(pointer)==read(pointer)
    macro=read(pointer)['macro_index'];shard=read(macro)
    assert one(shard['models'],ident)==target==read('data/precise-candidates/'+ident+'.json')
    check_file(shard['replacement_registry'])
    assert shard['replacement_registry']==previous(macro)['replacement_registry']
    assert [r for r in previous(macro)['models']if r['id']!=ident]==[r for r in shard['models']if r['id']!=ident]
    registry=read('data/precise-buildings-v6.json');old_registry=previous('data/precise-buildings-v6.json')
    assert dict(old_registry,ordinary_catalog=registry['ordinary_catalog'])==registry
    check_file(registry['ordinary_catalog'])
    catalog=read(registry['ordinary_catalog']['file']);old_cat=previous(registry['ordinary_catalog']['file'])
    entry=one(catalog['macros'],read(pointer)['macro_id']);check_file(entry)
    assert [r for r in catalog['macros']if r['id']!=entry['id']]==[r for r in old_cat['macros']if r['id']!=entry['id']]
    for role,v in meta['assets'].items():
        key='web' if role=='full' else role;new=target['assets'][key]
        assert new['file']!=prior['assets'][key]['file'] and '/revisions/'+meta['revision']+'/' in new['file']
        assert all(new[k]==v[k]for k in ('bytes','sha256','file'));check_file(new)
    for path in ('data/global-models/candidate-inventory.json','data/global-models/additional-placement.json','data/candidate-city-integrations.json','data/model-viewers.json'):
        assert previous(path)==read(path),path
    town=read('data/candidate-city-integrations.json')
    rows=now+town['models'];assert len({r['id'] for r in rows})==len(rows)==town['resulting_city_count']
    district_total=sum(r['districtId']==target['districtId']for r in rows)
    for doc in (REPO/'README.md',PROJECT/'README.md'):
        section=doc.read_text().split(f"### {job['district']}（{district_total}处）",1)[1].split('\n### ',1)[0]
        assert section.count(f"[查看网页]({job['preview']})")==1
    result=dict(model=ident,task=args.task,passed=True,baseline_commit=commit,checked_at_utc=datetime.now(timezone.utc).isoformat(),
                district=job['district'],district_entries=district_total,navigation_entries=len(rows),unchanged_city_rows=len(rows)-1,
                unchanged_other_macro_records=len(catalog['macros'])-1,source_owner=target['owner']['feature_local_id'],
                manifest_sha256=hashlib.sha256(mf.read_bytes()).hexdigest(),checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':
    main()
