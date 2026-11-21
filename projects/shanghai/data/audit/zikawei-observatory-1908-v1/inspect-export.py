"""Render the 1908 clock tower and its two wings from seven documented views."""
import argparse,hashlib,json,runpy
from pathlib import Path

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parents[2]/'source/precise/xuhui-zikawei-observatory-1908/source'
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mesh',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    cams=SOURCE/'cameras.json';rows=json.loads(cams.read_bytes())
    engine=runpy.run_path(HERE.parent/'fifth-textile-warehouse-river-front-v1/inspect-export.py')
    report=engine['render'](a.mesh,a.output,[(v['name'],v['eye'],v['target'],v['width_m'])for v in rows],rows[0]['width'],rows[0]['height'])
    assert report['embedded_textures'][0]['embedded_sha256']==hashlib.sha256((SOURCE/'observatory-grey-brick.png').read_bytes()).hexdigest()
    prominent={'whole-front':['Observatory grey brick','Weathered ivory clock dial','Ochre entrance masonry'],
               'clock-face':['Weathered ivory clock dial','Dark metal clock and rail','Observatory grey brick'],
               'stair-portal':['Ochre entrance masonry','Warm grey carved stone','Deep opening shadow'],
               'watch-room':['Observatory grey brick','Limestone and limewashed joinery','Dark timber casing'],
               'wing-windows':['Observatory grey brick','Oxide red trim brick','Smoked window glass'],
               'roof-plan':['Dark pitched roof','Warm grey carved stone','Observatory grey brick'],
               'return-elevation':['Observatory grey brick','Dark pitched roof','Oxide red trim brick']}
    report['registered_materials']={}
    for v in report['views']:
        name=v['view'];counts=v['material_pixels'];test={m:counts.get(m,0)for m in prominent[name]}
        assert min(test.values())>24,(name,test)
        report['registered_materials'][name]=test
    report['camera_source_sha256']=hashlib.sha256(cams.read_bytes()).hexdigest()
    (a.output/'views.json').write_text(json.dumps(report,indent=2)+'\n')
