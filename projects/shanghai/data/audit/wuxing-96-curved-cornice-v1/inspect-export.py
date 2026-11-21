"""Render the historic ornament, including its edge, soffit, tile field, and two window heads."""
import argparse,hashlib,json,runpy
from pathlib import Path

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parents[2]/'source/precise/xuhui-wuxing-96-curved-cornice/source'
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mesh',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    cams=SOURCE/'cameras.json';rows=json.loads(cams.read_bytes())
    engine=runpy.run_path(HERE.parent/'fifth-textile-warehouse-river-front-v1/inspect-export.py')
    report=engine['render'](a.mesh,a.output,[(v['name'],v['eye'],v['target'],v['width_m'])for v in rows],rows[0]['width'],rows[0]['height'])
    assert report['embedded_textures'][0]['embedded_sha256']==hashlib.sha256((SOURCE/'window-hood-aggregate.png').read_bytes()).hexdigest()
    prominent={'eaves':['Muted blue glass','Washed stone on window hood','Upper rolled edge'],
               'curved-return':['Washed stone on window hood','Light ceramic window trim','Ochre glazed ceramic'],
               'tile-frieze':['Weathered lime joint','Ochre glazed ceramic','Brown glazed ceramic'],
               'hood-lip':['Washed stone on window hood','Dark drip groove','Brown glazed ceramic'],
               'soffit':['Shadowed eave soffit','Dark drip groove'],
               'top-cap':['Muted tan upper fascia','Upper rolled edge'],
               'steel-head':['Dark steel window casing','Muted blue glass','Light ceramic window trim']}
    report['registered_materials']={}
    for v in report['views']:
        name=v['view'];counts=v['material_pixels'];test={m:counts.get(m,0)for m in prominent[name]}
        assert min(test.values())>24,(name,test)
        report['registered_materials'][name]=test
    report['camera_source_sha256']=hashlib.sha256(cams.read_bytes()).hexdigest()
    (a.output/'views.json').write_text(json.dumps(report,indent=2)+'\n')
