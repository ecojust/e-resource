"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from arched_tripartite import PALETTE,add_building
META={'id': 'huangpu-overseas-chinese-building-arched-tripartite-window', 'name': '华侨大楼九江路上层拱窗与双石梃', 'scope': '九江路短立面靠转角的上层拱窗，两根直石梃将弧形窗洞分作三栏。中栏的横竖细框在石梃后，两侧窗头收成弧形；窗台挑出，墙面凹缝在拱顶处向上放射。', 'model_scope_zh': '九江路短立面靠转角的上层拱窗，两根直石梃将弧形窗洞分作三栏。中栏的横竖细框在石梃后，两侧窗头收成弧形；窗台挑出，墙面凹缝在拱顶处向上放射。', 'estimated': '窗洞节选估宽约2.04米，两道石梃约宽0.13米。中栏玻璃分格、拱形侧光与放射缝参照2013、2018和2019年的照片；建筑经改建，本作记录照片可相互印证的外观，窗框材料及绝对尺寸待实测。', 'viewer_page': 'overseas-chinese-building-arched-tripartite-window.html', 'interiors_modeled': False, 'coordinate_convention': 'Local X follows the facade, Y points inward and Z is up. Dimensions are estimated, in metres.'}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
