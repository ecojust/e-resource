"""Count actual map pixel changes at the five projected Bund 15 reliefs."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy

import numpy as np
from PIL import Image, ImageDraw

audit=Path(__file__).resolve().parent
project=audit.parents[2]
helper=project/'data/audit/union-grape-pendants-v1/compare-map-detail.py'
engine=runpy.run_path(str(helper))
read=engine['read_json']
cli=argparse.ArgumentParser(description=__doc__)
cli.add_argument('before',type=Path)
cli.add_argument('after',type=Path)
cli.add_argument('output',type=Path)
cli.add_argument('--device',choices=['desktop','mobile'],action='append',help='Limit an intermediate receipt to the archived devices.')
args=cli.parse_args()
reports={k:read(v/f'main-map-{k}.json') for k,v in [('before',args.before),('after',args.after)]}
assert all(r['completed'] and r['record']['id']=='bund15' for r in reports.values())
manifest=read(project/'source/precise/bund15/revisions/river-arch-relief/manifest.json')
raw=manifest['assets']['raw'];src=project/raw['file']
assert hashlib.sha256(src.read_bytes()).hexdigest()==raw['sha256']
gltf,data=engine['load_mesh'](src)
added=['Southern acanthus','Northern acanthus','Southern winged figure','Northern winged figure','Central animal keystone']
assert [node['name'] for node in gltf['nodes'][1:]]==added
result={'asset_sha256':raw['sha256'],'projection_helper_sha256':hashlib.sha256(helper.read_bytes()).hexdigest(),
        'threshold_per_channel':6,'screens':{}}
for device in args.device or ['desktop','mobile']:
    selected={k:next(v for v in report['views'] if v['type']=='detail' and v['device']==device)for k,report in reports.items()}
    camera=selected['after']['state']['camera'];viewport=selected['after']['state']['viewport']
    assert viewport==selected['before']['state']['viewport']
    for key,val in camera.items():assert np.allclose(val,selected['before']['state']['camera'][key],atol=1e-7),(device,key)
    frames={}
    for k,folder in [('before',args.before),('after',args.after)]:
        item=selected[k];file=folder/item['file']
        assert hashlib.sha256(file.read_bytes()).hexdigest()==item['sha256']
        frames[k]=np.asarray(Image.open(file).convert('RGB'),dtype=np.int16)
    delta=np.abs(frames['after']-frames['before']).max(axis=2)
    union=np.zeros(delta.shape,dtype=np.bool_);parts={}
    for node in gltf['nodes'][1:]:
        mask=Image.new('1',tuple(viewport));drawer=ImageDraw.Draw(mask)
        for primitive in gltf['meshes'][node['mesh']]['primitives']:
            pos=engine['accessor'](gltf,data,primitive['attributes']['POSITION'])
            pts=engine['project'](pos,camera,reports['after']['record'],viewport)
            for tri in engine['accessor'](gltf,data,primitive['indices']).reshape(-1,3):
                drawer.polygon([tuple(p) for p in pts[tri]],fill=1)
        pixel=np.asarray(mask,dtype=bool);union|=pixel
        changed=int((delta[pixel]>=6).sum())
        parts[node['name']]={'bounds_px':mask.getbbox(),'projected_pixels':int(pixel.sum()),'changed_pixels':changed,
                             'median_max_channel_difference':float(np.median(delta[pixel])) if pixel.any() else None}
    result['screens'][device]={'camera':camera,'viewport':viewport,'inputs':{k:v['sha256'] for k,v in selected.items()},
        'parts':parts,'changed_pixels_outside_sculpture_projections':int((~union&(delta>=6)).sum())}
args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
