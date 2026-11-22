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
from shutter_boards import ID, PALETTE, add_building, texture

scope='Fayhoo上传的新场大街街照显示，190号绿牌装在门扇上，其右一间有八块连续的竖向活动排板。板面从左到右可读浅色数字1至8；下端齐落在横档后，横档两头留有凸起的挡块。'
META=dict(id=ID,name='郑生官宅190号沿街木排门的八块编号板与圆边横档',scope=scope,model_scope_zh=scope,viewer_page='zheng-residence-numbered-shutters.html',reference_height_m=2.23,all_dimensions_estimated=True,estimated='前景最近门牌为188。本件只取正标190的门扇右侧与该号同开间的八块板，按照片恢复编号和木构关系。凹槽深度、木种、整栋进深及绝对尺度未测。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
