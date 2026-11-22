"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from court_window import PALETTE,add_building
META={'id': 'jingan-shandao-hall-court-window', 'name': '善道堂旧址院门旁二层错石窗套与铁花格窗', 'scope': '复原巨鹿路709号院门东侧临街二层的一樘窗。短长交错的石块从深灰粒石墙镶入窗侧；窗下两扇铁花各自有卷头、弯叶和直杆，上亮另有连续线脚。', 'model_scope_zh': '复原巨鹿路709号院门东侧临街二层的一樘窗。短长交错的石块从深灰粒石墙镶入窗侧；窗下两扇铁花各自有卷头、弯叶和直杆，上亮另有连续线脚。', 'estimated': '据2019年5月与2020年2月两次街景辨认窗框和交错八皮石材。模型窗宽约1.48米，未实测绝对尺寸；进深与颗粒分布按阴影和正面比例估计。', 'viewer_page': 'shandao-hall-court-window.html', 'source_reference_only': True}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
