"""Render the north stair, canopy columns, green gate and facing brick from the actual decoded geometry."""
from pathlib import Path
import argparse,hashlib,json,runpy
HERE=Path(__file__).resolve().parent
SOURCE=HERE.parents[2]/'source/precise/xuhui-elisabeth-apartments-north-stair-bay/source'
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mesh',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();cameras=SOURCE/'cameras.json';rows=json.loads(cameras.read_bytes())
    method=HERE.parent/'fifth-textile-warehouse-river-front-v1/inspect-export.py'
    report=runpy.run_path(method)['render'](args.mesh,args.output,[(r['name'],r['eye'],r['target'],r['width_m'])for r in rows],760,830)
    assert len(report['views'])==7 and report['embedded_textures'][0]['embedded_sha256']==hashlib.sha256((SOURCE/'cement-render.png').read_bytes()).hexdigest()
    for r in report['views']:
        mat=r['material_pixels']
        if r['view'] in ('under-canopy','gate'):
            assert mat.get('Bottle green gate',0)>150, r['view']
        if r['view'] in ('landing','up-stair'):
            assert mat.get('Weathered red facing brick',0)>150, r['view']
        if r['view'] == 'crown':
            assert mat.get('Pale folded crown bands',0)>300, r['view']
        if r['view'] in ('north-elevation','north-oblique'):
            assert mat.get('Ivory cement render',0)>3000 and mat.get('Oxide red window steel',0)>400, r['view']
    report['camera_source_sha256']=hashlib.sha256(cameras.read_bytes()).hexdigest()
    (args.output/'views.json').write_text(json.dumps(report,indent=2)+'\n')
