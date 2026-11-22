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
from four_chevron_sashes import ID, PALETTE, add_building, texture

scope='Fayhoo于2016年2月13日摄下季景北路608至612号街屋。临街赭色立面有几组楼上窗，610号绿牌在左侧方格窗下方；本件选择它右边的四联窗，窗内的斜格成对交替向中间收拢。'
META=dict(id=ID,name='高桥季景北路608至612号街屋的四联折线格窗',scope=scope,model_scope_zh=scope,viewer_page='jijing-north-four-chevron-sashes.html',reference_height_m=2.25,all_dimensions_estimated=True,estimated='5W047同列石家街27弄3号。照片只题季景北路608至612号，不能将这组窗归到石家街院内，亦不足以独断折格窗的单门号。材质和窗框厚度依正面照片近似。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
