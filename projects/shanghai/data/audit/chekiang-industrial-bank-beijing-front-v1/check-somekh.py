"""Compare the two neighbouring source owners with the actual Somekh replacement and collisions."""
from argparse import ArgumentParser
from hashlib import sha256
import json,math
from pathlib import Path

import numpy as np
from shapely import transform
from shapely.geometry import shape

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
BANK='huangpu-chekiang-industrial-bank-beijing-front'
SOMEKH='huangpu-somekh-building-street-corner'


def check(document,bank_contract,kind):
    prior_bytes=document.read_bytes()
    prior=json.loads(prior_bytes)
    if kind=='catalog':
        selected=prior['models'][-1]
        assert all(row['id']!=BANK for row in prior['models'])
    else:
        selected=prior
    assert selected['id']==SOMEKH and selected['owner']=={'macro_id':'14-13720-6693','feature_local_id':251}
    data=json.loads(bank_contract.read_bytes())
    review=json.loads((PROJECT/'source/precise'/BANK/'footprint-review.json').read_bytes())
    ids=set(review['near_tiles'][0]['feature_local_ids'])
    assert ids=={1700,2404,251,760,2289,297}
    assert data['id']==BANK and data['owner']=={'macro_id':'14-13720-6693','feature_local_id':2404}
    assert data['replacement_geometry'] is None
    lng,lat=data['lng'],data['lat']
    metre=np.array([math.radians(1)*6371008.8*math.cos(math.radians(lat)),math.radians(1)*6371008.8])
    def flat(geom):
        return transform(shape(geom),lambda xy:(xy-[lng,lat])*metre)
    bank=flat(review['original_geometry_wgs84'])
    other=flat(next(row['geometry_wgs84']for row in review['owners']if row['local_id']==251))
    window=flat(data['collision_geometry'])
    assert bank.contains(window) and not bank.intersects(other)
    results={}
    for key in ['replacement_geometry','collision_geometry','osm_replacement_geometry']:
        if not selected.get(key):continue
        part=flat(selected[key])
        assert not part.intersects(bank) and not part.intersects(window)
        results[key]={'distance_to_bank_source_m':round(part.distance(bank),4),
                      'distance_to_window_contact_m':round(part.distance(window),4),
                      'area_with_old_bank_m2':round(part.intersection(bank).area,7)}
    assert {'replacement_geometry','collision_geometry'}<=set(results)
    return {'passed':True,'bank':BANK,'somekh':SOMEKH,'input_type':kind,
            'somekh_input_sha256':sha256(prior_bytes).hexdigest(),
            'bank_contract_sha256':sha256(bank_contract.read_bytes()).hexdigest(),
            'native_group_ids':sorted(ids),'somekh_owner':251,'bank_owner':2404,
            'source_buildings_distance_m':round(other.distance(bank),4),
            'city_geometry_comparisons':results}


if __name__=='__main__':
    cli=ArgumentParser(description=__doc__)
    cli.add_argument('kind',choices=('contract','catalog'))
    cli.add_argument('somekh_input',type=Path)
    cli.add_argument('--bank',type=Path,default=HERE/'final-placement-contract.json')
    cli.add_argument('--out',type=Path,required=True)
    args=cli.parse_args()
    result=check(args.somekh_input,args.bank,args.kind)
    args.out.write_text(json.dumps(result,indent=2)+'\n')
    print(result['source_buildings_distance_m'],result['city_geometry_comparisons'])
