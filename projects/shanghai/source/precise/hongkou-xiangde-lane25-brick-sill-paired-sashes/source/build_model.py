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
from sash import ID, PALETTE, add_building, texture

scope='Fayhoo的2015年4月12日原照摄于祥德路25弄1号、2号住宅。临院红砖墙的两扇红框格窗在树冠下露出，窗内呈蓝绿色，窗下有一整排向墙外突出的竖砖。取下半部可见的框扇、窗台及墙边。'
META=dict(id=ID,name='祥德路25弄住宅临院双扇格窗与竖砖窗台',scope=scope,model_scope_zh=scope,viewer_page='xiangde-lane25-brick-sill-paired-sashes.html',reference_height_m=1.9,all_dimensions_estimated=True,estimated='现行市表还列3号。照片未给这扇窗的逐户门号，故按1、2号原照的范围题名。蓝绿色的表面是否属于玻璃或窗内织物未明，源图中树叶覆盖的窗上缘不作复原。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
