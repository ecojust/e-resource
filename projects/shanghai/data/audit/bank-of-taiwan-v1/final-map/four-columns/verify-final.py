"""Verify the signed 153-place launch and user actions before accepting the four-column screenshots."""
import hashlib,json,sys
from pathlib import Path
root=Path(__file__).resolve().parent
folder=Path(sys.argv[1]).resolve()
signed=json.loads(Path(sys.argv[2]).read_bytes())
report=json.loads((folder/'browser.json').read_bytes())
measure=json.loads((folder/'shaft-coverage.json').read_bytes())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert report['base'].rstrip('/')==sys.argv[3].rstrip('/')
assert report['catalog_sha256']==signed['files']['data/candidate-city-integrations.json']==measure['catalog_sha256']
assert signed['resulting_count']==153 and report['completed'] and report['closed'] and not report['pageErrors']
assert report['script_sha256']==sha(root/'check.cjs') and report['columns_input_sha256']==sha(root/'columns.json')
assert set(report['views'])=={'mobile-default','mobile-plus','desktop-default'}
for device,requests in report['files'].items():
    for f,request in requests.items():
        assert request['sha256']==signed['files'][f] and request['bytes']>0
for name,view in measure['views'].items():
    assert not view['incorrect_hit_points'] and view['hit_points']>=18 and view['signs']>=2
    assert len(view['column_shafts'])==4
    assert all(col['on_screen_pixels']>340 and col['under_rendered_sign_pixels']==0 for col in view['column_shafts']),name
    if name.endswith('-default'):
        assert all(col['offscreen_pixels']==0 and col['inside_location_card_rect_pixels']==0 and col['fully_in_viewport'] for col in view['column_shafts']),name
    else:
        assert [c['offscreen_pixels'] for c in view['column_shafts']]==[0,0,0,39],name
        assert [c['inside_location_card_rect_pixels'] for c in view['column_shafts']]==[1532,0,0,0],name
    assert sha(folder/(name+'.png'))==view['png_sha256']==report['views'][name]['sha256']
    assert report['views'][name]['asset']['triangles']==54008
zoom=[report['views'][v]['camera']['zoom']for v in ['mobile-default','mobile-plus']]
assert abs(zoom[1]-zoom[0]-1)<.001
assert any(a['action']=='touch own sign' and report['id'] in a['selected']for a in report['actions'])
assert any(a['action']=='click neighbouring sign' and a['id']!=report['id'] and a['id'] in a['selected']for a in report['actions'])
result={'passed':True,'base':report['base'],'catalog_sha256':report['catalog_sha256'],'signed_input_count':len(signed['files']),'signature_sha256':sha(Path(sys.argv[2])),'actual_browser_sha256':sha(folder/'browser.json'),'shaft_masks_sha256':sha(folder/'shaft-coverage.json'),'views':{n:{'name_signs':v['signs'],'hit_tests':v['hit_points'],'shaft_pixels':[i['on_screen_pixels']for i in v['column_shafts']],'covered_pixels':[i['under_rendered_sign_pixels']for i in v['column_shafts']],'outside_viewport_pixels':[i['offscreen_pixels']for i in v['column_shafts']],'under_location_card_rect_pixels':[i['inside_location_card_rect_pixels']for i in v['column_shafts']],'png_sha256':v['png_sha256']}for n,v in measure['views'].items()},'actions':report['actions']}
(folder/'accepted.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(result['catalog_sha256'],[(v['name_signs'],v['hit_tests'])for v in result['views'].values()])
