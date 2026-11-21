"""Rebuild both editable-level geometries and their independent viewer assets."""
from argparse import ArgumentParser
from pathlib import Path
import os,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from blackstone_portico import PALETTE,add_portico
META={'id': 'xuhui-blackstone-apartments-east-portico', 'name': '黑石公寓复兴中路弧形柱廊东段', 'viewer_page': 'blackstone-apartments-east-portico.html', 'scope': '复兴中路1331号朝街的一层开放柱廊，仅含东端一对柱、首组前柱、这两对柱间的弯檐及其上方十格交叉石栏。', 'model_scope_zh': '复兴中路1331号朝街的一层开放柱廊，仅含东端一对柱、首组前柱、这两对柱间的弯檐及其上方十格交叉石栏。', 'source_register': 'source/precise/xuhui-blackstone-apartments-east-portico/reference-review.json', 'interiors_modeled': False, 'status': 'surveyed-portico-fragment', 'estimated': '两组同期街景解得端柱对至首组前柱中心距5.75米、5.68米。剩余各层、遮挡的柱脚细部与室内不在重建范围内。', 'coordinate_convention': 'Metres. X follows the 5.71 m chord from the east end pair to the first front pair. Positive Y points back into the portico, and Z starts at grade.', 'copyright': 'Original reconstructed geometry. References are linked separately and photographs are not applied to the asset.'}
if __name__=='__main__':
    ap=ArgumentParser(add_help=False);ap.add_argument('--blender',default='blender');opt,rest=ap.parse_known_args()
    os.environ['BLACKSTONE_PORTICO_BLENDER']=opt.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_portico)
