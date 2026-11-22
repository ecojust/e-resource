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
from lancets import ID, PALETTE, add_building, texture

scope='Fayhoo于2015年拍摄的广东浸信会堂旧址，临院塔楼正面有一对狭长尖券窗。蓝色中梃将上下两排窗格及米黄色下栏板分开，外侧一圈蓝色大尖券围合两孔。'
META=dict(id=ID,name='广东浸信会堂旧址塔楼双联尖券长窗',scope=scope,model_scope_zh=scope,viewer_page='canton-baptist-tower-paired-lancets.html',reference_height_m=5.6,all_dimensions_estimated=True,estimated='这件模型取2015年照片所见的塔面长窗。涂色按照片当时状态估计，来历及初建色彩未知；不据学校院落照片确定塔的经纬度或开口实测高度。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
