import os
from pathlib import Path
import sys
source = Path(__file__).resolve().parent
roots = list(source.parents)
if os.environ.get('SHANGHAI_MODEL_TOOLS'):
    roots.insert(0, Path(os.environ['SHANGHAI_MODEL_TOOLS']).parent)
tools = next(parent/'tools' for parent in roots if (parent/'tools/package_architectural_model.py').is_file())
sys.path.insert(0, str(tools))
from package_architectural_model import build
from chimney_stack import ID, PALETTE, add_building, texture

scope='Antigng于2018年拍摄的愚园路838弄20号住宅，上层黄褐砖山墙的屋脊处立着矩形烟囱。三只短圆烟管排在同一道叠线浅色压顶上，烟囱两侧山墙的斜向压顶相接于不同高度。'
META=dict(id=ID,name='唐氏花园住宅20号山墙三孔砖烟囱',scope=scope,model_scope_zh=scope,viewer_page='tang-house-no20-three-chimney-pots.html',reference_height_m=3.123,all_dimensions_estimated=True,estimated='市表5M005还列同弄22、30、32号，此照题注只指20号。墙厚、烟道内径和作为尺寸参照的高度均从单幅斜照估计，照片在屋顶下方拍摄，未显示管内构造。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
