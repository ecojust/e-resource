"""Draw the real hall fragment and its cast relief from the meshopt-decoded near/far meshes."""
from pathlib import Path
import argparse,json,runpy,hashlib

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parents[2]/'source/precise/huangpu-mingfu-library-science-society-relief-columns/source'
RENDERER=HERE.parent/'fifth-textile-warehouse-river-front-v1/inspect-export.py'
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('decoded',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    cameras=json.loads((SOURCE/'cameras.json').read_bytes())
    views=[(r['name'],r['eye'],r['target'],r['width_m'])for r in cameras]
    report=runpy.run_path(RENDERER)['render'](args.decoded,args.output,views,840,700)
    for view in report['views']:
        count=view['material_pixels']
        assert count.get('Raised warm brass',0)>20 and count.get('Blue enamel field',0)>30,view['view']
    assert any(v['texture_samples'].get('Warm stone shaft')for v in report['views'])
    report['camera_source_sha256']=hashlib.sha256((SOURCE/'cameras.json').read_bytes()).hexdigest()
    report['model_specific_method_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (args.output/'views.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
