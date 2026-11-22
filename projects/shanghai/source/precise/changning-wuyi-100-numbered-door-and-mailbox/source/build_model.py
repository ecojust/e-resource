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
from addressed_door import ID, PALETTE, add_building, texture

scope='2018年2月13日Antigng署名原照中，「100 武夷路」门牌贴在临街红砖洞口右边，下方是同号绿色邮箱，门头有一排竖砖。市表5M017登记武夷路100号住宅，现名为机关事务管理局。本展截取可由门牌确定的街面入口。'
META=dict(id=ID,name='武夷路100号街门与绿色门牌邮箱',scope=scope,model_scope_zh=scope,viewer_page='wuyi-100-numbered-door-and-mailbox.html',reference_height_m=2.43,all_dimensions_estimated=True,estimated='街门的修建年份未见于照片。院中可见多处红瓦建筑，照片不足以逐幢指认为登记住宅。门后深度、邮箱凸出和砖模数按照片估算。门内小字、右侧另设的小牌和前景临时器物未作辨认建模。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
