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
from drip_eaves import ID, PALETTE, add_building, texture

scope='Fayhoo在2015年4月18日摄下新场中华楼邻桥的长立面。临水一侧的檐口交替露出拱形筒瓦端与向下收尖的滴水，下面可见连续深色横木和间隔排列的小木端。'
META=dict(id=ID,name='新场中华楼临水檐口的弧形筒瓦与尖头滴水',scope=scope,model_scope_zh=scope,viewer_page='zhonghua-lou-pointed-drip-tiles.html',reference_height_m=1.0,all_dimensions_estimated=True,estimated='市表登记141至145号单号，原照题注145号。摘取照片清楚的一段檐边，九道盖瓦和八片滴水表示其重复构造。瓦道间距、坡面进深、色差和隐蔽搭接按照片估计。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
