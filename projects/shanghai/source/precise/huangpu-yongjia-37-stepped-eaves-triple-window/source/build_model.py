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
from upper_bay import ID, PALETTE, add_building, texture

scope='市表5A067列永嘉路37号住宅。据Antigng在2015年9月9日拍摄的门牌题名照片，取花园内高起的浅色窗间及其接入低翼屋面的转角。'
META=dict(id=ID,name='永嘉路37号住宅错层檐口与三联长窗',scope=scope,model_scope_zh=scope,viewer_page='yongjia-37-stepped-eaves-triple-window.html',reference_height_m=4.42,all_dimensions_estimated=True,estimated='照片从院墙外斜望，右侧窗的开闭和局部栏杆须以当时影像为准。模型截取到高翼窗台和低翼接缝；拍摄处树盖、院墙和后期蓝色卷帘不作为墙体线脚。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
