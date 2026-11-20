"""Reconcile the measured full-city collision with the component and surviving hospital."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from shapely.geometry import Point,shape

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parents[2]/'source/precise/huangpu-renji-hospital-ward-entrance/footprint-review.json'
def read(p):return json.loads(p.read_bytes())
def signature(p):return sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('observed',type=Path);ap.add_argument('report',type=Path);args=ap.parse_args()
    component=read(HERE/'footprint-review.json');contract=read(HERE/'final-placement-contract.json')
    observed=read(args.observed);samples=observed['ground_probes'];assert len(samples)==len(component['ground_probes'])==6
    source=shape(read(SOURCE)['owners'][0]['geometry']);mask=shape(contract['replacement_geometry'])
    original=source.difference(mask);collision=shape(contract['collision_geometry']);result=[]
    for test,actual in zip(component['ground_probes'],samples):
        assert test['label']==actual['name'] and test['world']==actual['xy']
        point=Point(test['world']);new=collision.covers(point);retained=original.covers(point)
        assert new==test['blocked']
        full='building' if new or retained else None
        assert actual['actual']==full
        result.append({'name':test['label'],'xy':test['world'],'within_original_1977':source.covers(point),
                       'within_replacement_mask':mask.covers(point),'within_retained_1977':retained,
                       'within_component_collision':new,'expected_city_collision':full,'observed_city_collision':actual['actual']})
    args.report.write_text(json.dumps({'owner':contract['owner'],'source_file_sha256':signature(SOURCE),
        'placement_contract_sha256':signature(HERE/'final-placement-contract.json'),'observed_file_sha256':signature(args.observed),
        'world_coordinates':'WGS84 longitude, latitude','probes':result},ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
