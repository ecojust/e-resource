"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from exposed_gable import PALETTE,add_building
META={'id': 'hongkou-dongtiyuhui-23-timber-gable', 'name': '东体育会路119弄23号住宅露木山花与弧形角撑', 'scope': '23号山花中央有一扇小窗，小窗与下方灰墙共用两根竖木。两侧斜撑分别向窗间收拢，檐下另有四块弧形角撑，斜向封檐板在灰壁面前方相交。', 'model_scope_zh': '23号山花中央有一扇小窗，小窗与下方灰墙共用两根竖木。两侧斜撑分别向窗间收拢，檐下另有四块弧形角撑，斜向封檐板在灰壁面前方相交。', 'estimated': '参考高参88从弄内和23号门外所拍的两张不同角度照片。以山花底部名义宽4.06米换算构件，进深、木料截面和屋檐出挑为估计。', 'viewer_page': 'dongtiyuhui-23-timber-gable.html', 'source_reference_only': True}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
