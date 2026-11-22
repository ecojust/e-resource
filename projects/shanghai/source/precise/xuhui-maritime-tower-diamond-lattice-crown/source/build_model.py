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
from diamond_crown import ID, PALETTE, add_building, texture

scope='龙华港汇入黄浦江处的海事瞭望塔在Fayhoo于2015年3月29日拍摄的照片中，塔冠腰部外鼓，顶部收窄。两组浅银色斜杆沿曲面反向盘升，围出能透见后面暗色横带的菱格。'
META=dict(id=ID,name='徐汇滨江海事瞭望塔塔冠的交叉菱格外网',scope=scope,model_scope_zh=scope,viewer_page='maritime-tower-diamond-lattice-crown.html',reference_height_m=3.33,all_dimensions_estimated=True,estimated='本研究只取2015年照片中的塔冠外饰。外网杆数、杆的交叉前后和核心表面以该视角可辨的密度和轮廓近似，模型尺寸仅用来表示比例。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
