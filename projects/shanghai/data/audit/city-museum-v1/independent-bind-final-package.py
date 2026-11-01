"""Bind prior direct three-GLB review to the final four-asset manifest by actual bytes.
This step checks packaging only and never substitutes hashes for geometric or image review.
"""
from pathlib import Path
import hashlib,json,struct,sys
A,R,O=map(Path,sys.argv[1:4]);g=json.loads((R/'independent-geometry-review.json').read_text());m=json.loads((A/'manifest.json').read_text())
def binding(p):
 b=p.read_bytes();return{'file':p.name,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
assert m['id']==g['modelId']=='yangpu-former-shanghai-city-museum';assert set(m['assets'])=={'raw','native','full','lod'}
rows={}
for role,expected in m['assets'].items():
 actual=binding(A/expected['file']);assert 0<actual['bytes']<100000000
 for key in ['file','bytes','sha256']:assert actual[key]==expected[key]
 if role!='native':
  for key in ['file','bytes','sha256']:assert actual[key]==g['assets'][role][key]
  assert expected['triangles']==g['assets'][role]['triangles'];actual['triangles']=expected['triangles']
 rows[role]=actual
assert sum(r['bytes']for r in rows.values())<100000000
raw=(A/m['assets']['raw']['file']).read_bytes();n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);assert doc['extras']==m['source_candidate_metadata'];assert m['authored_bounds_enu_m']==g['assets']['raw']['actualBoundsModelENU']
meta=m['source_candidate_metadata']
assert meta['source_local_ids']==[1860,1931] and meta['source_macro']=='14-13722-6690'
assert meta['all_elevation_datums_estimated'] and meta['all_architectural_detail_dimensions_estimated']
assert meta['documentary_height_datums_not_measured'] and meta['modern_two_storey_wings_not_original_single_storey_claim']
assert all(meta[k]is False for k in ['photos_embedded','interiors_modeled','underground_modeled','site_slab_modeled','walk_integration'])
assert 'eastern rear hall' in meta['scope'] and 'estimated' in meta['scope'] and 'Courtyard links' in meta['scope']
assert m['viewer_page']=='city-museum.html' and m['audit_directory']=='data/audit/city-museum-v1/'
assert m['city_integration']['view']=='index.html#landmark=yangpu-former-shanghai-city-museum&mode=overview'
assert m['all_elevation_datums_estimated']is True and m['documented_existing_height_m']is None
assert all(m[k]is True for k in ['documentary_height_datums_not_field_verified','modern_two_storey_wings_distinguished_from_historic_single_storey','rear_hall_current_fabric_date_and_details_unverified','rear_hall_rendered_as_simplified_estimated_low_volume','gallery_has_open_column_aisles_and_recessed_window_walls','both_roofs_and_upper_loft_physically_closed'])
assert all(m[k]is False for k in ['court_sources_510_1262_included','complete_photo_reconstruction_accepted','interiors_modeled','walk_integration','photos_embedded'])
out={'schema':'city-museum-independent-final-package-binding-v1','passed':True,'method':'Actual byte reads of all four assets and final manifest; three model SHA/size/triangle records equal independently decoded geometry; raw extras equal final manifest source metadata. Independent native reopen and actual PNG viewing are separate reports.','final_manifest':binding(A/'manifest.json'),'independent_geometry_report':binding(R/'independent-geometry-review.json'),'geometry_decode_input_kind':g['manifest'].get('kind','final-manifest'),'assets':rows,'total_asset_bytes':sum(r['bytes']for r in rows.values()),'raw_extras_equal_manifest':True,'actual_bounds_equal_manifest':True,'heights_and_details_explicitly_estimated':True,'scope_exclusions_verified':True,'script':binding(Path(__file__))}
O.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'passed':True,'asset_count':len(rows),'total_bytes':out['total_asset_bytes']}))
