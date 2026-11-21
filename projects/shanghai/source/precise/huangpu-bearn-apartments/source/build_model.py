"""Build the Huaihai Road apartments' street elevation and the curved Chongqing Road end."""
from pathlib import Path
import os
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[3]/"tools"))
from package_architectural_model import build
from huaihai_front import PALETTE,front

ID="huangpu-bearn-apartments"
SCOPE="淮海中路约70米长立面与东端约27米圆弧所见的商铺檐带、面砖和浅色竖带、成列凸窗、七层弧形窗带、九层中段退台及塔冠。"
META={"id":ID,"name":"培文公寓（淮海中路街面与重庆南路圆角）","viewer_page":"bearn-apartments.html",
      "scope":SCOPE,"model_scope_zh":SCOPE,"status":"original-exterior-informed-by-archival-and-2014-photography",
      "coordinate_convention":"Local X follows the north front westward. The local Y axis points into the building. Z is up.",
      "estimated":"分层依据政府建筑阅读资料，檐口、窗距、塔冠及弧形立面按存照和实名街廓估计。取2014年影像可见的商店屋顶题字。市级名录同址449号。","interiors_modeled":False,
      "source_register":"source/precise/"+ID+"/reference-review.json","copyright":"Original architectural geometry and procedural materials. No reference image embedded. Subset street lettering under SIL Open Font License."}
if __name__=="__main__":
    # The street curve lies east of the survey origin. Save a camera framing both ends.
    if '--blender' in sys.argv:
        index = sys.argv.index('--blender') + 1
        os.environ['BEARN_BLENDER_EXECUTABLE'] = sys.argv[index]
        sys.argv[index] = str(HERE/'native_blender.py')
    else:
        sys.argv.extend(['--blender', str(HERE/'native_blender.py')])
    build(HERE,META,PALETTE,front)
