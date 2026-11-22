"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from slotted_balcony import PALETTE,add_building
META={'id': 'jingan-kade-apartments-slotted-balcony', 'name': '卡德大楼街面阳台的四排横槽与转角铁栏', 'scope': '取石门二路50号卡德大楼临街阳台的左端与中段。女儿墙上连续四排穿孔，左端一道开孔折回侧面；低铁栏沿墙顶折转。', 'model_scope_zh': '取石门二路50号卡德大楼临街阳台的左端与中段。女儿墙上连续四排穿孔，左端一道开孔折回侧面；低铁栏沿墙顶折转。', 'estimated': '据Fayhoo于2015年拍摄的卡德公寓全景量取横槽分组、铁栏与楼板的相对比例。取样正面名义宽5.53米，楼板深度、孔口截面和铁杆直径为估计。', 'viewer_page': 'kade-apartments-slotted-balcony.html', 'source_reference_only': True}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
