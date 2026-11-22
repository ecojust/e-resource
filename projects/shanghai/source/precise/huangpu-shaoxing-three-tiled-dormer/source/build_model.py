"""Rebuild both editable-level geometries and their independent viewer assets."""
from argparse import ArgumentParser
from pathlib import Path
import os,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from gable import PALETTE,model
META={'id': 'huangpu-shaoxing-three-tiled-dormer', 'name': '绍兴路3号住宅曲面红瓦屋顶与双扇格窗', 'viewer_page': 'shaoxing-three-tiled-dormer.html', 'scope': '取3号临街屋顶靠右的一扇双扇格窗，包括深色框扇、上方遮檐、两侧下缓上陡的小瓦坡、浅色收边及下檐沟。', 'model_scope_zh': '取3号临街屋顶靠右的一扇双扇格窗，包括深色框扇、上方遮檐、两侧下缓上陡的小瓦坡、浅色收边及下檐沟。', 'interiors_modeled': False, 'status': 'photographed-street-elevation-fragment', 'coordinate_convention': 'X follows the photographed facade, Y increases backwards, Z is up.', 'source_register': 'source/precise/huangpu-shaoxing-three-tiled-dormer/reference-review.json', 'estimated': '以窗净宽约1.02米为比例依据。屋面坡折、前后尺寸和被树遮挡的上部檐口按照片估算。房间及屋顶后坡超出图像范围。'}
if __name__=='__main__':
    ap=ArgumentParser(add_help=False);ap.add_argument('--blender',default='blender');opt,rest=ap.parse_known_args()
    os.environ['SHAOXING_THREE_DORMER_BLENDER']=opt.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,model)
