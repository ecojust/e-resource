"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from porch_arch import PALETTE,add_building
META={'id': 'jingan-kangding-85-porch-carved-brick-arch', 'name': '康定东路85号李宅门廊砖雕拱券', 'scope': '修缮前保留的门廊一跨。弧顶的砖券内侧为辐射状砖缝，中段卷叶连续转过拱顶，外圈收一道细凸线。两边各保留一座带叶饰的红砖柱头及其下面可见的砌砖。', 'model_scope_zh': '修缮前保留的门廊一跨。弧顶的砖券内侧为辐射状砖缝，中段卷叶连续转过拱顶，外圈收一道细凸线。两边各保留一座带叶饰的红砖柱头及其下面可见的砌砖。', 'estimated': '参照修缮记录中的600×400像素局部照片拟合券面两条轮廓。模型所取内券宽约3.10米、柱间名义尺度、砖雕深度与卷叶单元间距均为估算。砖墙在画框处截断，灯、黑色木梁与后室另计。', 'viewer_page': 'kangding-85-porch-carved-brick-arch.html', 'source_reference_only': True}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
