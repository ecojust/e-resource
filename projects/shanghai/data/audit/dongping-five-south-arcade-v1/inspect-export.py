"""Render the garden arcade, turned balusters, central steps and shuttered dormer from the actual decoded geometry."""
from pathlib import Path
import argparse,hashlib,json,runpy
HERE=Path(__file__).resolve().parent
SOURCE=HERE.parents[2]/'source/precise/xuhui-dongping-five-south-arcade/source'
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mesh',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();cameras=SOURCE/'cameras.json';rows=json.loads(cameras.read_bytes())
    method=HERE.parent/'fifth-textile-warehouse-river-front-v1/inspect-export.py'
    report=runpy.run_path(method)['render'](args.mesh,args.output,[(r['name'],r['eye'],r['target'],r['width_m'])for r in rows],890,750)
    assert len(report['views'])==7 and report['embedded_textures'][0]['embedded_sha256']==hashlib.sha256((SOURCE/'pebble-render.png').read_bytes()).hexdigest()
    for r in report['views']:
        mat=r['material_pixels']
        if r['view'] in ('south-elevation','upper-arcade','balusters'):
            assert mat.get('Warm white balusters',0)>380 and mat.get('Grey pebble render',0)>400,r['view']
        if r['view'] == 'lower-passage':
            assert mat.get('Red quarry steps',0)>300 and mat.get('Recessed gallery plaster',0)>200,r['view']
        if r['view'] == 'dormer':
            assert mat.get('Dormer shutter boards',0)>120 and mat.get('Weathered red roof tiles',0)>120,r['view']
    report['camera_source_sha256']=hashlib.sha256(cameras.read_bytes()).hexdigest()
    (args.output/'views.json').write_text(json.dumps(report,indent=2)+'\n')
