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
from carved_sashes import ID, PALETTE, add_building, texture

scope='庄行东街17号东兴楼茶馆书场位于进入第五批名录的沿街商铺民宅范围内。Dragon在2023年11月24日拍了这座茶馆的临街正面、东兴楼门额和沿南桥塘的一面。本件取临街二层左组窗中央相邻四扇，描出窄木梃、上下两排切角玻璃和下方穿空的木裙板。'
META=dict(id=ID,name='庄行东兴楼茶馆书场八角玻璃花窗与透空裙板',scope=scope,model_scope_zh=scope,viewer_page='dongxing-teahouse-octagonal-timber-lights.html',reference_height_m=2.1,all_dimensions_estimated=True,estimated='房屋开间比这四扇窗更宽。玻璃的亮色反映拍摄时的天空，木框截面、前后厚度和绝对尺度按照片比例估计。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
