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
from bowed_balcony import ID, PALETTE, add_building, texture

scope='市第五批5D026住宅，早期公布地址为东平路1弄。Fayhoo于2015年1月拍到住宅墙面凸出的弧形铁阳台，圆拱有多重细线脚和居中楔石，扇形亮窗及双扇门都留有彩色花叶玻璃。'
META=dict(id=ID,name='东平路住宅弧形铁阳台与彩玻圆首门',scope=scope,model_scope_zh=scope,viewer_page='dongping-lane-one-bowed-balcony.html',reference_height_m=2.74,all_dimensions_estimated=True,estimated='后来名录的地址写作东平路1号。照片说明按1弄，镜头只支持这一处住宅立面。彩玻花叶取可见色块和排列，未逐片复绘。阳台的实际出挑、栏杆净高和门后室内均未实量。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
