from pathlib import Path
from hashlib import sha256
import json,sys
def verify(root, report, case):
    read=lambda p:json.loads(Path(p).read_bytes())
    d=read(report);c=read(case);assert d['completed'] and d['caseSha256']==sha256(Path(case).read_bytes()).hexdigest()
    assert {n['local_id'] for v in d['views'] for n in v['neighbors']}=={353,1608,1726}
    for v in d['views']:
        assert not v['clip'] and not v['sections']
        for n in v['neighbors']:
            local=n['local_id']; assert n['state'].get('candidateModel') is not True
            if v['view']=='map-distant':continue
            groups=[g for g in v['streamedGroups'] if g and local in g['feature_local_ids']]
            assert len(groups)==1 and local not in groups[0]['clip_feature_local_ids']
            assert groups[0]['macro_id']==('14-13720-6695' if local==1726 else '14-13721-6695')
            assert groups[0]['id'] in v['streaming'] and n['state']['localModel'] is True
    if d['section']=='before':
        p=d['beforeGround']['points'];assert len(p)==len(c['ground'])==51
        assert all(v['name']==w['name'] and 'found' in v and (v['found'] is None or isinstance(v['found'],str)) and max(abs(v['position'][k]-w['wgs84'][k])for k in (0,1))<0.000002 for v,w in zip(p,c['ground']))
        transfer=[x for x in d['transferTiming']['requests'] if x.get('passed')];assert len(transfer)==4
        transfer.sort(key=lambda r:r['continued']);assert all(x['completion']=='requestfinished' and x['status']==200 and x['head']['status']==200 and x['range']['status']==206 and x['head']['length']==x['responseBytes']==x['sizes']['responseBodySize'] for x in transfer)
        assert all(b['continued']>=a['completed'] for a,b in zip(transfer,transfer[1:]))
    return {'passed':True,'report_sha256':sha256(Path(report).read_bytes()).hexdigest(),'owners':[353,1608,1726],'before_ground':len(d.get('beforeGround',{}).get('points',[]))}
if __name__=='__main__':print(json.dumps(verify(None,sys.argv[1],sys.argv[2])))
