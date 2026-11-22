"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from stone_portico import PALETTE,add_building
META={'id': 'hongkou-xiangde-66-no1-volute-portico', 'name': '祥德路66弄1号卷头水刷石门廊与拱心石', 'scope': '一号入口两根圆柱托住水平叠线，前面各有一对石卷头，侧面另有回折。浅椭圆拱向中央上升，带细槽的楔石凸出券面。', 'model_scope_zh': '一号入口两根圆柱托住水平叠线，前面各有一对石卷头，侧面另有回折。浅椭圆拱向中央上升，带细槽的楔石凸出券面。', 'estimated': '据高参88同址正、斜两张近照和院内全景建模，以两柱轴距名义2.10米估算。柱高、进深、水刷石粒与券背为估计。', 'viewer_page': 'xiangde-66-no1-volute-portico.html', 'source_reference_only': True}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
