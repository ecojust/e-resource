"""Bind the prior catalog and the five-owner source tile before the facade was registered."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen

AUDIT=Path(__file__).resolve().parent
PROJECT=AUDIT.parents[2]
ID='huangpu-brunner-mond-building'
def read(path):
    return json.loads(path.read_bytes())
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',required=True)
    parser.add_argument('--report',type=Path,default=AUDIT/'predecessor-source-http.json')
    args=parser.parse_args()
    proof=read(AUDIT/'main-map-browser.json')
    source=read(PROJECT/'source/precise'/ID/'footprint-review.json')
    contract=read(AUDIT/'final-placement-contract.json')
    requests=[]
    def get(path,expected):
        url=args.base.rstrip('/')+'/'+path
        with urlopen(url,timeout=35) as response:
            data=response.read()
            assert response.status==200
        actual=hashlib.sha256(data).hexdigest()
        assert actual==expected,path
        requests.append({'path':path,'url':url,'bytes':len(data),'sha256':actual})
        return data
    catalog=json.loads(get('data/candidate-city-integrations.json',proof['previous_catalog']['sha256']))
    assert catalog['resulting_city_count']==130 and all(r['id']!=ID for r in catalog['models'])
    owner=contract['owner'];uuid=contract['source_feature_ids']['building'][0]
    assert not any(r.get('owner')==owner or uuid in (r.get('source_feature_ids')or {}).get('building',[]) for r in catalog['models'])
    d='assets/city-detail/macros/'+source['macro_id']+'/'
    groups=source['near_groups']; group,=groups; hashes=source['frozen_bindings']
    ready=json.loads(get(d+'READY.json',hashes['READY.json']['sha256']))
    row=next(r for r in ready['near']if r['file']==group['file'])
    assert row['featureLocalIds']==group['ids'] and owner['feature_local_id']in row['featureLocalIds']
    features=json.loads(gzip.decompress(get(d+'feature-table.json.gz',hashes['feature-table.json.gz']['sha256'])))['features']
    assert next(f for f in features if f['localId']==1600)['properties']['id']==uuid
    for name in ('far.glb',group['file']):
        data=get(d+name,hashes[name]['sha256'])
        assert (gzip.decompress(data) if name.endswith('.gz') else data)[:4]==b'glTF'
    report={'prior_count':130,'candidate_rows':len(catalog['models']),'new_facade_absent':True,'no_prior_candidate_claims_owner_or_uuid':True,
            'owner':owner,'source_uuid':uuid,'actual_near_members':group['ids'],'requests':requests,
            'scope':'Prior-version HTTP catalog, feature table and original near/far source meshes. The browser screenshots in main-map-browser.json show the integrated 131-destination release.'}
    args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
