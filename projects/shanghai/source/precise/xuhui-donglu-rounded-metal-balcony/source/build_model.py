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
from curved_balcony import ID, PALETTE, add_building, texture

scope='高参88发表的岳阳路265号花园住宅两幅实照中，三层钢窗前单独挑出一座窄阳台，端部圆转。浅色整片金属栏板与楼板之间有一条空隙，上部为细横杆。按这座小挑台制作。'
META=dict(id=ID,name='岳阳路265号东庐三层小挑台与弧端金属栏板',scope=scope,model_scope_zh=scope,viewer_page='donglu-rounded-metal-balcony.html',reference_height_m=2.84,all_dimensions_estimated=True,estimated='两幅照片给出正面及侧前轮廓。挑台进深、栏板背面、近墙的扶手端和固定件尺寸据比例估计。小挑台位于大露台旁的上层，图中的大露台未纳入模型。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
