"""Compare selected Cishu destination data and all downloads on the two real label releases."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urljoin

import requests

AUDIT=Path(__file__).resolve().parent
MODEL='huangpu-cishu-building'
def digest(data):
    return hashlib.sha256(data).hexdigest()
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('previous')
    parser.add_argument('updated')
    parser.add_argument('--output',type=Path,default=AUDIT/'label-release-http.json')
    args=parser.parse_args()
    original=json.loads((AUDIT/'main-map-browser.json').read_bytes())
    observed={r['role']:r for r in original['http_assets']}
    assert original['completed'] and original['browser_closed'] and len(observed)==4
    collected=[];values=[];scene_bytes=[]
    for base in (args.previous,args.updated):
        requests_log=[]
        def fetch(path):
            url=urljoin(base,path);res=requests.get(url,timeout=35);res.raise_for_status();raw=res.content
            requests_log.append({'url':url,'bytes':len(raw),'sha256':digest(raw),'status':res.status_code})
            return raw
        index=fetch('index.html').decode()
        entry=re.search(r'src="(src/app\.js\?v=[^"]+)"',index).group(1)
        app=fetch(entry).decode();scene_src=re.search(r"from '\./(map-scene\.js\?v=[^']+)'",app).group(1)
        scene=fetch('src/'+scene_src).decode()
        beacon=re.search(r"from '\./(building-beacons\.js\?v=[^']+)'",scene).group(1)
        fetch('src/'+beacon);scene_bytes.append(scene.replace(beacon,'building-beacons.js?version'))
        token=entry.split('?v=')[1]
        catalog=json.loads(fetch('data/candidate-city-integrations.json?v='+token));assert catalog['resulting_city_count']==128
        row=next(v for v in catalog['models']if v['id']==MODEL)
        manifest=json.loads(fetch(row['candidate_manifest']))
        proof=json.loads(fetch('data/audit/cishu-building-v1/final-placement-contract.json'))
        for k in ['owner','source_feature_ids','replacement_geometry','collision_geometry','source_section_caps','lng','lat','heading','overviewZoom','overviewPitch','overviewBearing']:
            assert row[k]==proof[k]
        for kind,r in manifest['assets'].items():
            entry_path=str(Path(row['candidate_manifest']).parent/r['file'])
            raw=fetch(entry_path)
            assert len(raw)==observed[kind]['bytes']==r['bytes'] and digest(raw)==observed[kind]['sha256']==r['sha256']
        for v in original['views']:
            assert v['asset']['verifiedAsset']['sha256'] in [r['sha256']for r in observed.values()]
            if v['view'].startswith('main-'):
                assert v['picked']==MODEL and v['selected']==MODEL and v['clip']['owner']==row['owner']
                assert v['camera']['bearing']==row['overviewBearing'] and v['camera']['pitch']==row['overviewPitch']
        values.append((row,proof,manifest))
        collected.append({'server':base,'scene_module':scene_src,'beacon_module':beacon,'traffic':requests_log})
    assert values[0]==values[1] and scene_bytes[0]==scene_bytes[1]
    old,new=collected;different=[i for i,(a,b)in enumerate(zip(old['traffic'],new['traffic']))if a['sha256']!=b['sha256']]
    assert different==[2,3],different
    row=values[0][0]
    view_keys=['lng','lat','heading','scale','overviewBearing','overviewPitch','overviewZoom','lod_switch_in_m','lod_switch_out_m']
    args.output.write_text(json.dumps({'id':MODEL,'city_count':128,'actual_http':collected,'source_browser_sha256':digest((AUDIT/'main-map-browser.json').read_bytes()),'previous_runtime_default_cameras':[v['camera']for v in original['views']if v['view'].startswith('main-')],
        'identical_selected_settings':{k:row[k]for k in view_keys},'camera_and_placement_module_sha256_after_beacon_import_normalization':digest(scene_bytes[0].encode()),'identical_complete_row_and_placement':True,'verified_original_owner':row['owner'],'mode':'Direct HTTP on both releases. The browser-selected landmark and actual desktop/mobile cameras were observed on the previous release.'},ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
