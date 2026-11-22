"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from gable_sash import PALETTE,add_building
META={'id': 'changning-tang-garden-gable-sash', 'name': '唐氏花园住宅山墙双扇木窗与圈眼锚铁', 'scope': '愚园路838弄唐氏花园的双联住宅有尖山墙、灰白色压边和高窗。从三幅有署名的照片辨出八块玻璃、山墙上的浅色圈眼锚铁，以及小遮篷伸到砖面的三根细撑。', 'model_scope_zh': '愚园路838弄唐氏花园的双联住宅有尖山墙、灰白色压边和高窗。从三幅有署名的照片辨出八块玻璃、山墙上的浅色圈眼锚铁，以及小遮篷伸到砖面的三根细撑。', 'estimated': '两扇窗的外框按名义宽1.20米展开，墙深、铁件截面和小篷的伸出量为估算。照片能确认这组住宅，窗所在的单独门号尚未落实；画面前方经过的架空线不属于山墙构件。', 'viewer_page': 'tang-garden-gable-sash.html', 'source_reference_only': True}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
