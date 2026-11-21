"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from mosaic_stair import PALETTE,add_building
META={'id': 'xuhui-defour-apartments-mosaic-stair', 'name': '巨福公寓公共楼梯马赛克踏步', 'viewer_page': 'defour-apartments-mosaic-stair.html', 'status': 'photo-informed-architectural-component', 'scope': '修缮团队公开照片中连续的四级公共楼梯，记录中央深灰色马赛克、两侧茶褐色边带、圆钝踏鼻与短段贴砖墙脚。', 'model_scope_zh': '修缮团队公开照片中连续的四级公共楼梯，记录中央深灰色马赛克、两侧茶褐色边带、圆钝踏鼻与短段贴砖墙脚。', 'interiors_modeled': True, 'source_register': 'source/precise/xuhui-defour-apartments-mosaic-stair/reference-review.json', 'estimated': '典型层历史图用原城两条长墙37.92和38.52米校准。图上东西梯的窗井外侧净距约18至20像素，折合1.00至1.12米，辨线误差约2像素。取一级宽1.08米，40模数，单格约27毫米。踏高和进深由同一模数估计，参考尺度存在图纸与底图误差。', 'coordinate_convention': 'X across the flight, positive Y uphill, Z vertical.', 'copyright': 'Original geometry and materials under MIT. Source photographs remain with their credited owners.'}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
