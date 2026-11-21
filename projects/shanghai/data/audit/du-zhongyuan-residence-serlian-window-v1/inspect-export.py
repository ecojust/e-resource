"""Render the garden window, column, timber sash and stone keystone from the actual decoded geometry."""
from pathlib import Path
import argparse,hashlib,json,runpy
HERE=Path(__file__).resolve().parent
SOURCE=HERE.parents[2]/'source/precise/xuhui-du-zhongyuan-residence-serlian-window/source'
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mesh',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();cameras=SOURCE/'cameras.json';rows=json.loads(cameras.read_bytes())
    method=HERE.parent/'fifth-textile-warehouse-river-front-v1/inspect-export.py'
    report=runpy.run_path(method)['render'](args.mesh,args.output,[(r['name'],r['eye'],r['target'],r['width_m'])for r in rows],840,710)
    assert len(report['views'])==7 and report['embedded_textures'][0]['embedded_sha256']==hashlib.sha256((SOURCE/'garden-plaster.png').read_bytes()).hexdigest()
    for r in report['views']:
        mat=r['material_pixels']
        if r['view'] in ('scroll','column'):
            assert mat['Pale dressed arch stone'] > 150, r['view']
        if r['view'] == 'sashes':
            assert mat['Red brown timber joinery'] > 150, r['view']
        if r['view'] == 'fanlight':
            assert mat['Bronze fanlight bars'] > 150, r['view']
    report['camera_source_sha256']=hashlib.sha256(cameras.read_bytes()).hexdigest()
    (args.output/'views.json').write_text(json.dumps(report,indent=2)+'\n')
