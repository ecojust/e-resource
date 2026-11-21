"""The listing, approximate loss and publication date remain distinct."""
import runpy
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

P = Path(__file__).resolve().parents[1]
catalog = runpy.run_path(str(P / 'tools/build_candidate_city_integrations.py'))
ID = 'jingan-chen-bingqian-historic-residence'
PAGE = 'chen-bingqian-historic-residence.html'
PERIOD = {'kind': 'archival-facade', 'listed_year':1994, 'approximate_loss_year':1994,
          'evidence_kind':'reprinted-photograph', 'evidence_years':[2014,2014]}


class ReprintedPhoto(unittest.TestCase):
    def test_publication_requires_consistent_dates(self):
        validate = catalog['validate_historical_period']
        validate(PERIOD, ID)
        for change in [{'building_year':1900}, {'evidence_years':[1948,2014]},
                       {'evidence_years':[1948,1948]}, {'evidence_kind':'photographs'}]:
            with self.subTest(change=change), self.assertRaises(AssertionError):
                validate({**PERIOD, **change}, ID)

    def test_photo_can_only_use_its_own_named_page_and_never_claim_a_current_building(self):
        folder = 'assets/models/candidates/'+ID
        assets = {role:{'file':f'{folder}/{ID}-{role}.glb', 'sha256':str(i)*64}
                  for i,role in enumerate(('raw','web','lod'),1)}
        item = {'id':ID,'name':'陈炳谦宅','districtId':'310106','district':'静安区',
                'individual_page':PAGE,'manifest':folder+'/manifest.json', 'assets':assets,
                'original_delivery_status':'historical-photo-informed-facade-study'}
        contract = {'id':ID,'lng':121.4525,'lat':31.2272,'historical_view':PERIOD,
                    'collision_geometry':None,'replacement_geometry':None,'navigation':{'listed':False},
                    'source_feature_ids':{'building':[],'building_part':[]},
                    'model_geometry_sha256':{k:v['sha256'] for k,v in assets.items()}}
        make = catalog['historical_site_record']
        with TemporaryDirectory() as raw, patch.dict(make.__globals__, {'PROJECT':Path(raw)}):
            (Path(raw)/PAGE).write_text(f"showCandidateAssetViewer('{ID}')")
            self.assertEqual(make(item,contract)['historical_view'], PERIOD)
            for changes in ({'individual_page':'existing-residence.html'},{'individual_page':'../'+PAGE},
                            {'id':'other-building'}, {'original_delivery_status':'historical-illustration-informed-facade-study'}):
                with self.subTest(changes=changes), self.assertRaises(AssertionError):
                    make({**item, **changes}, contract)
            for changes in ({'collision_geometry':{}},{'replacement_geometry':{}},{'source_feature_ids':{'building':['w1287266688'],'building_part':[]}}):
                with self.subTest(changes=changes), self.assertRaises(AssertionError):
                    make(item,{**contract, **changes})


if __name__ == '__main__':
    unittest.main()
