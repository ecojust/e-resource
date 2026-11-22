"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from dormer import PALETTE,add_building
META={'id': 'jingan-siming-villas-yuyuan-dormer', 'name': '四明别墅临愚园路红瓦坡与四扇阁楼窗', 'scope': '临愚园路一排住宅的屋面局部。四扇赤褐色窄窗并列，浅色窗侧墙压到红色瓦坡上，窄横木窗台与坡檐在前后两个平面。', 'model_scope_zh': '临愚园路一排住宅的屋面局部。四扇赤褐色窄窗并列，浅色窗侧墙压到红色瓦坡上，窄横木窗台与坡檐在前后两个平面。', 'estimated': '窗洞名义宽2.64米。两处2020年街景对同一窗台右下角的高程估算相差约0.5米。窗扇高度、侧墙厚度和瓦件曲率依可见轮廓估计；被电缆遮挡的格条以同扇可辨部分续接。', 'viewer_page': 'siming-villas-yuyuan-dormer.html', 'source_reference_only': True}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
