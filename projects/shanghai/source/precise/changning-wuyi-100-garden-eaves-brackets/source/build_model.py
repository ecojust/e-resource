"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from turned_eaves import PALETTE,add_building
META={'id': 'changning-wuyi-100-garden-eaves-brackets', 'name': '武夷路100号花园住宅转角挑檐、曲线檐托与通气口', 'scope': '院内照片显示屋檐从前墙转向侧墙。浅色檐底的三处矩形通气口和四处弧形撑托可以分辨；深色封檐和浅灰半圆形雨槽沿两边连续转折。', 'model_scope_zh': '院内照片显示屋檐从前墙转向侧墙。浅色檐底的三处矩形通气口和四处弧形撑托可以分辨；深色封檐和浅灰半圆形雨槽沿两边连续转折。', 'estimated': '市政府2015年公布的现场名牌将住宅定为1930年代。檐宽、托板厚度及通风口进深按参照照片估计。浅色墙面只取檐托在照片中接墙的一段，檐底通风口保留暗处。', 'viewer_page': 'wuyi-100-garden-eaves-brackets.html', 'source_reference_only': True}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
