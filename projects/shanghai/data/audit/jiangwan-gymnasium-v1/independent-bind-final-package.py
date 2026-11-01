"""Bind prior direct three-GLB review to the final four-asset manifest by actual bytes.
This step checks packaging only and never substitutes hashes for geometric or image review.
"""
from pathlib import Path
import hashlib,json,struct,sys
A,R,O=map(Path,sys.argv[1:4]);g=json.loads((R/'independent-geometry-review.json').read_text());m=json.loads((A/'manifest.json').read_text())
def binding(p):
 b=p.read_bytes();return{'file':p.name,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
assert m['id']==g['modelId']=='yangpu-jiangwan-gymnasium';assert set(m['assets'])=={'raw','native','full','lod'}
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
assert m['documented_existing_height_m']is None and m['all_elevation_datums_estimated']is True
assert all(m[k] is False for k in ['interiors_modeled','outdoor_stadium_modeled','swimming_hall_modeled','site_slab_modeled','underground_modeled','walk_integration']);assert m['map_design_discrepancy_retained'] is True
out={'schema':'jiangwan-gymnasium-independent-final-package-binding-v1','passed':True,'method':'Actual byte reads of all four assets and final manifest; three model SHA/size/triangle records equal independently decoded geometry; raw extras equal final manifest source metadata. Independent native reopen and actual PNG viewing are separate reports.','final_manifest':binding(A/'manifest.json'),'independent_geometry_report':binding(R/'independent-geometry-review.json'),'geometry_decode_input_kind':g['manifest'].get('kind','final-manifest'),'assets':rows,'total_asset_bytes':sum(r['bytes']for r in rows.values()),'raw_extras_equal_manifest':True,'actual_bounds_equal_manifest':True,'heights_and_details_explicitly_estimated':True,'scope_exclusions_verified':True,'script':binding(Path(__file__))}
O.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'passed':True,'asset_count':len(rows),'total_bytes':out['total_asset_bytes']}))
