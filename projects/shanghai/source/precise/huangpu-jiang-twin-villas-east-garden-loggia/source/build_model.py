"""Rebuild both editable-level geometries and their independent viewer assets."""
from argparse import ArgumentParser
from pathlib import Path
import os,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from loggia import PALETTE,add_loggia
ID='huangpu-jiang-twin-villas-east-garden-loggia'
SCOPE='淮海中路796号东馆南花园面，由中间通道东侧的大方墩至第一根圆柱的一个开间，只覆盖三层廊沿、瓶栏、其后可见两扇窗及本开间压顶。'
META=dict(id=ID,name='姜氏双子别墅东馆花园面西端柱廊',viewer_page='jiang-twin-villas-east-garden-loggia.html',scope=SCOPE,model_scope_zh=SCOPE,source_register='source/precise/'+ID+'/reference-review.json',interiors_modeled=False,status='photo-informed-historic-loggia',estimated='以学院完整园景、另一现场记录和原52南侧12.09米边定柱轴3.45米。栏后廊深约2.2米，误差大于正立面的尺度。',coordinate_convention='Metres. X runs along the east villa towards the northeast, Y enters the south loggia, Z starts at garden grade.',copyright='Original geometric reconstruction using independent dimensional and photographic references. Documentary photographs are not used as materials.')
if __name__=='__main__':
    ap=ArgumentParser(add_help=False);ap.add_argument('--blender',default='blender');opt,rest=ap.parse_known_args()
    os.environ['JIANG_GALLERY_BLENDER']=opt.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_loggia)
