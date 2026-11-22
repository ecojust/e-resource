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
from brick_arches import ID, PALETTE, add_building, texture

scope='Fayhoo在2016年拍下长治路135号街角的红砖公寓。顶层转折的两面墙各开一扇半圆头窄窗，外圈砖券在顶部托住一块上宽下窄的竖向券心石，两面墙的腰线与顶檐在折角处相连。'
META=dict(id=ID,name='长治路135号公寓转角砖券窗与楔形券心石',scope=scope,model_scope_zh=scope,viewer_page='changzhi-135-canted-brick-arches.html',reference_height_m=4.23,all_dimensions_estimated=True,estimated='以照片估计转角与窗洞相对进深，缺少实测尺寸。范围只及转角顶层的一对窗，现场前景电杆、附装搁架及空调按照片另记。市表另列闵行路172号，单凭这幅图不能逐门定位。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
