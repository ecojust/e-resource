"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from hooded_windows import PALETTE,add_building
META={'id': 'hongkou-shanyin-181-villa-hooded-windows', 'name': '山阴路181号花园住宅临街二层窗罩、窗台托与瓦檐', 'scope': '取临街四樘上窗中间的两樘。粉墙上的石窗罩层层外挑，罩檐两端设托，窗台下方各有两只短托；上方连续建出褐瓦坡的前六排与檐板。', 'model_scope_zh': '取临街四樘上窗中间的两樘。粉墙上的石窗罩层层外挑，罩檐两端设托，窗台下方各有两只短托；上方连续建出褐瓦坡的前六排与檐板。', 'estimated': '2020年2月20日街景中，学校院门后可辨粉色楼及上层四窗。2019年5月、2015年12月街景分别核对屋顶轮廓、相邻门牌与院门位置。两中央窗以净宽0.86米估计比例，经过窗框中部的架空线遮住横档，坡度、瓦垄分格和托座进深为估计。', 'viewer_page': 'shanyin-181-villa-hooded-windows.html', 'source_reference_only': True}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
