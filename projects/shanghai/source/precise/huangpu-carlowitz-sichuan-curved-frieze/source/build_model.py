"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from curved_frieze import PALETTE,add_building
META={'id': 'huangpu-carlowitz-sichuan-curved-frieze', 'name': '礼和大楼弧形转角花饰腰线与砖齿', 'scope': '红砖圆转角上的白色花饰腰线，石带分缝、凸起的连续小垂弧和挑出压顶，底下紧邻一列凹凸相间的红砖齿。', 'model_scope_zh': '红砖圆转角上的白色花饰腰线，石带分缝、凸起的连续小垂弧和挑出压顶，底下紧邻一列凹凸相间的红砖齿。', 'estimated': '位置和饰纹节奏据2016年2月18日实照。节选展开长约4.56米，栏带及上下砖层约0.94米，曲率和各层前后距离为照片比例估计。', 'viewer_page': 'carlowitz-sichuan-curved-frieze.html', 'interiors_modeled': False, 'coordinate_convention': 'Local X follows the facade, Y points inward and Z is up. Dimensions are estimated, in metres.'}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
