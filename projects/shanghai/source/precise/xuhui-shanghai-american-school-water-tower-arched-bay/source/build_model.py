"""Package the surviving photographic view of the water tower crown."""
from pathlib import Path
import os,sys
source=Path(__file__).resolve().parent
roots=[*source.parents]
if os.environ.get('SHANGHAI_MODEL_TOOLS'):roots.insert(0,Path(os.environ['SHANGHAI_MODEL_TOOLS']).parent)
tools=next(root/'tools' for root in roots if (root/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(tools))
from package_architectural_model import build
from tower_crown import add_building,PALETTE,make_brick_texture
ID='xuhui-shanghai-american-school-water-tower-arched-bay'
META=dict(id=ID,name='美童公学水塔顶层砖券窗与挑檐',viewer_page='american-school-water-tower-arched-bay.html',scope='水塔顶层见光面的一扇砖券百叶窗、下层蓝绿框扇、两侧砖壁柱、出挑檐及照片所见屋面。',model_scope_zh='顶层局部正面，采用照片比例。',reference_height_m=5.045,estimated='以顶层墙宽4.4米作为展示比例；实物尺寸与立面朝向未能从已核历史照片确定。',interiors_modeled=False,source_register='source/precise/'+ID+'/reference-review.json',copyright='Original mesh and procedural brick texture. Historic reference photographs remain with their respective publishers.')
if __name__=='__main__':
    make_brick_texture(source/'brick-courses.png');build(source,META,PALETTE,add_building)
