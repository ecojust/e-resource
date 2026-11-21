"""Render the numbered porch, stone steps, twisted railings and roof from each decoded model."""
from pathlib import Path
import argparse,hashlib,json,runpy
HERE=Path(__file__).resolve().parent
SOURCE=HERE.parents[2]/'source/precise/xuhui-dingxiang-three-numbered-porch/source'
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mesh',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();cameras=SOURCE/'cameras.json';rows=json.loads(cameras.read_bytes())
    method=HERE.parent/'fifth-textile-warehouse-river-front-v1/inspect-export.py'
    report=runpy.run_path(method)['render'](args.mesh,args.output,[(r['name'],r['eye'],r['target'],r['width_m'])for r in rows],rows[0]['width'],rows[0]['height'])
    assert len(report['views'])==7 and report['embedded_textures'][0]['embedded_sha256']==hashlib.sha256((SOURCE/'river-pebble-wall.png').read_bytes()).hexdigest()
    for r in report['views']:
        mat=r['material_pixels']
        if r['view'] in ('numbered-entrance','oblique-porch'):
            assert mat.get('Warm exposed river pebbles',0)>400 and mat.get('Grey granolithic treads',0)>380,r['view']
        if r['view']=='twisted-iron':
            assert mat.get('Mahogany handrails',0)>180 and mat.get('Black twisted iron',0)>120,r['view']
        if r['view']=='number-three':
            assert mat.get('Number and brass plates',0)>250 and mat.get('Brown porch timber',0)>200,r['view']
        if r['view']=='tile-eaves':assert mat.get('Rounded red clay tiles',0)>200,r['view']
    report['camera_source_sha256']=hashlib.sha256(cameras.read_bytes()).hexdigest()
    (args.output/'views.json').write_text(json.dumps(report,indent=2)+'\n')
