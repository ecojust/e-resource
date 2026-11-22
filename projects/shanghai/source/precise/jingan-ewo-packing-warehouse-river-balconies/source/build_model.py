"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from warehouse_balconies import PALETTE,add_building
META={'id': 'jingan-ewo-packing-warehouse-river-balconies', 'name': '怡和源打包厂沿河立面上下两层铁阳台', 'scope': '北苏州路912号沿河街墙的两层阳台在同一竖线上。上层门窄、下层门宽，后方浅砖券、突出的黑色台缘、密竖铁栏和两侧回栏按实照制作。', 'model_scope_zh': '北苏州路912号沿河街墙的两层阳台在同一竖线上。上层门窄、下层门宽，后方浅砖券、突出的黑色台缘、密竖铁栏和两侧回栏按实照制作。', 'estimated': '依据Fayhoo在2015年拍摄的临河正面，以两阳台名义宽2.36米估算层距和门洞宽。栏杆深度、杆径、砖缝和台底托件进深为估计。', 'viewer_page': 'ewo-packing-warehouse-river-balconies.html', 'source_reference_only': True}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
