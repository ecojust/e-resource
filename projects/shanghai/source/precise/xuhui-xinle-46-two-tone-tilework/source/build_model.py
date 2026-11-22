import os
from pathlib import Path
import sys
source = Path(__file__).resolve().parent
roots = list(source.parents)
if os.environ.get('SHANGHAI_MODEL_TOOLS'):
    roots.insert(0, Path(os.environ['SHANGHAI_MODEL_TOOLS']).parent)
tools = next(parent/'tools' for parent in roots if (parent/'tools/package_architectural_model.py').is_file())
sys.path.insert(0, str(tools))
from package_architectural_model import build
from facing_tiles import ID, PALETTE, add_building, texture

scope='新乐路44弄入口旁46号铺面上半部。深红和浅米色的面砖交替错缝，洞口上方改用竖砖，浅色抹面包住上沿和两侧。成排的面砖从街面转入弄口，较暗的砖带与橙色线脚收住墙头。'
META=dict(id=ID,name='慎成里新乐路46号双色陶面砖与竖砖过梁',scope=scope,model_scope_zh=scope,viewer_page='xinle-46-two-tone-tilework.html',reference_height_m=3.07,all_dimensions_estimated=True,estimated='按金红卫两张照片概括46号这一跨。窗内后来加装的卷闸仅取上部横向阴影。沿街行道树、商业招牌、卷篷与管线未纳入；转角回折仅延伸至斜照可见处，尺寸和进深均为估计。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
