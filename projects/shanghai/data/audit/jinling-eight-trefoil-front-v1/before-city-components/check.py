"""Verify the archived city captures, original vector ranges, geometry IDs, and process exits."""
from pathlib import Path
import hashlib
import json
import struct

p=Path(__file__).resolve().parent
def read(name):
    return json.loads((p/name).read_bytes())
def digest(name):
    with (p/name).open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()
def inspect_png(folder,item):
    name=folder+'/'+item['file']
    assert digest(name)==item['sha256']
    with (p/name).open('rb') as f:
        head=f.read(24)
    assert head[:8]==b'\x89PNG\r\n\x1a\n'
    assert struct.unpack_from('>II',head,16)==(item['width'],item['height'])
def session(folder,key):
    report=read(folder+'/control-browser.json')
    closed=read(folder+'/failed-exit.json')
    assert closed['exit_code']==1 and closed['cdp_closed'] and closed['node_closed'] and not closed['remaining']
    assert closed['driver_sha256']==report['scriptSha256']==digest(folder+'/actual-driver.cjs')
    receipts=read('original-receipts.json')
    for name in ('control-browser.json','failed-exit.json'):
        relative=folder+'/'+name
        assert receipts[relative]['public_sha256']==digest(relative) and receipts[relative]['excerpt']
    assert closed['report_sha256']==receipts[folder+'/control-browser.json']['original_sha256']
    assert report['realDirectoryEntry']['pointer']['trusted'] and report['catalog']['count']==319
    assert report['realDirectoryEntry']['id']=='huangpu-messageries-maritimes-building'
    for shot in report[key].values():inspect_png(folder,shot)
    return report
surfaces=session('materials','registeredMaterialCapture')
vector=session('vectors','registeredVectorCapture')
assert read('materials/chromium-exits.jsonl')['exit_code']==0
assert read('vectors/chromium-exits.jsonl')['signal']=='SIGKILL'
seen=surfaces['previousNearBeforeVectors']
assert seen['visibleFrames']>0 and '14-13721-6694/14-13721-6694--5_-1-s0' in seen['nearCells']
assert seen['surfaces']['textures']==12 and seen['surfaces']['byProfile']['cityPlaster']==3
textures=read('materials/realism-284-twelve.json')
assert sum(t['bytes'] for t in textures)==seen['surfaces']['sourceBytes']==7413517
finished={r['url']:r for r in map(json.loads,(p/'materials/finished-bytes.jsonl').read_text().splitlines())}
assert len(textures)==12 and all(finished[surfaces['server']+t['path']]['encoded']>=t['bytes'] for t in textures)
tile=read('overture/tile-owners.json')
for span in tile['requests']:
    f='overture/range-{}-{}.bin'.format(span['offset'],span['bytes'])
    assert digest(f)==span['sha256'] and (p/f).stat().st_size==span['bytes']
    headers=(p/f.replace('.bin','.txt')).read_text()
    assert '206' in headers and str(span['offset']) in headers
evidence=vector['loadedVectorEvidence']
assert evidence['loaded']==tile['layers']['building']==1979 and tile['layers']['building_part']==73
source={x['source_uuid'] for x in tile['matches'].values()}
assert len(source)==7 and source=={item['id'] for item in evidence['matched'] if item['type']=='Polygon'}
asset=evidence['selectedBuilding'];assert asset['visible'] and asset['status']=='loaded' and asset['triangles']==49900
historic=read('historical/cross-version-review.json')
assert historic['current_model']==asset['verifiedAsset']
for name,item in historic['original_files'].items():
    assert digest('historical/'+name)==item['sha256']
h=read('historical/main-browser.json')
for v in h['views']:
    if v['view'] in ('map-street-facade','map-roof'):
        assert v['asset']['verifiedAsset']['sha256']==asset['verifiedAsset']['sha256'] and not v['contextLost'] and v['glError']==0
print('12 texture files, 7 mapped features, 2 independent component captures, 2 historical city angles')
