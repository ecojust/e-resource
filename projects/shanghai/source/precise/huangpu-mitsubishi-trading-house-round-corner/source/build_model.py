"""Package raw, web, lower detail and a native editable model."""
from pathlib import Path
import os
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3]/'tools'))
from package_architectural_model import build
from round_tower import PALETTE, facade

MODEL_ID = 'huangpu-mitsubishi-trading-house-round-corner'
META = {
    'id': MODEL_ID,
    'name': '广东路102号三菱洋行西南圆塔与拱门',
    'viewer_page': 'mitsubishi-trading-house-corner.html',
    'status': 'original-photo-informed-exterior',
    'scope': '西南角平切券门及其上三窗轴的弧面塔身、圆鼓和屋顶透空栏杆。',
    'model_scope_zh': '按1947年与2015年1月2日影像核对圆塔外形，饰面采用2015年1月所见。',
    'estimated': '依据约5.3米圆顶的屋顶影像、门窗比例及地块折角估计尺寸。地面边线与屋檐投影分别定位。',
    'source_register': f'source/precise/{MODEL_ID}/reference-review.json',
    'interiors_modeled': False,
    'coordinate_convention': 'X to the right facing the entrance, Y northeast into the historic corner, Z up, metres.',
    'copyright': 'Original model; archival and street photographs used as visual references.'
}
if __name__ == '__main__':
    if '--blender' in sys.argv:
        i=sys.argv.index('--blender')+1
        os.environ['GUANGDONG_TOWER_BLENDER']=sys.argv[i]
        sys.argv[i]=str(HERE/'blender_tower.py')
    else:
        sys.argv.extend(['--blender',str(HERE/'blender_tower.py')])
    build(HERE,META,PALETTE,facade)
