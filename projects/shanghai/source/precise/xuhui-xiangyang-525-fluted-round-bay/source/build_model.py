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
from round_window_bay import ID, PALETTE, add_building, texture

scope='2018年署名实照中的住宅上层弧形窗廊，三根浅色嵌柱间并排两扇分格钢窗。各柱脚下有红色椭圆饰面，窗顶外伸檐口可见浅黄托块。'
META=dict(id=ID,name='襄阳南路525号住宅弧形窗廊与椭圆饰墩',scope=scope,model_scope_zh=scope,viewer_page='xiangyang-525-fluted-round-bay.html',reference_height_m=3.119,all_dimensions_estimated=True,estimated='弧墙只取原照正面三柱和中间相邻两跨。实际半径、钢窗厚薄及刻槽深度按图估计。左侧被植物遮挡的小瓶栏与屋顶栏杆另属其他范围。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
