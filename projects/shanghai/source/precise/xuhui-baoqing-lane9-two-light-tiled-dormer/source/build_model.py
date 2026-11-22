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
from roof_dormer import ID, PALETTE, add_building, texture

scope='Fayhoo于2015年9月4日署名的宝庆路9弄2号、3号合照中，左栋红瓦坡面前伸一扇双格老虎窗。浅框窗扇两侧是暗灰色侧板，上沿挑出一道黑色薄檐，周围保留有清楚的波形瓦列。'
META=dict(id=ID,name='宝庆路9弄住宅红瓦坡面的双扇老虎窗',scope=scope,model_scope_zh=scope,viewer_page='baoqing-lane9-two-light-tiled-dormer.html',reference_height_m=1.83,all_dimensions_estimated=True,estimated='图注同时列2号与3号，无法单凭这张图确定画面左栋的独立户号。市表5D066还包括1至6号其余住宅。现代空调遮住窗台中段，本件据两侧显露的金属泛水估计进深；主屋脊、其他房屋、设备与院落均在本次细部取景之外。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
