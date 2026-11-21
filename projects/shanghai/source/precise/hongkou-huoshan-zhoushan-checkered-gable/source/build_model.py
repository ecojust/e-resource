"""Rebuild the original paired-window gable with the Shanghai project's model tools."""
import os
from pathlib import Path
import sys
source=Path(__file__).resolve().parent
roots=list(source.parents)
if os.environ.get('SHANGHAI_MODEL_TOOLS'):roots.insert(0,Path(os.environ['SHANGHAI_MODEL_TOOLS']).parent)
tools=next(p/'tools' for p in roots if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(tools))
from package_architectural_model import build
from checkered_gable import PALETTE,add_building,texture
ID='hongkou-huoshan-zhoushan-checkered-gable'
scope='霍山路与舟山路转角住宅朝长街的一榀双券窗山墙，据2012年正面与2015年斜面重构。'
META=dict(id=ID,name='霍山路舟山路转角住宅双券窗与棋格山墙',scope=scope,model_scope_zh=scope,
    viewer_page='huoshan-zhoushan-checkered-gable.html',reference_height_m=5.88,
    estimated='原照辨形；墙厚、窗档与绝对尺寸按比例估计。',copyright='Original model and hand-generated brick finish.')
if __name__=='__main__':
    texture(source/'grey-facing-bricks.png')
    build(source,META,PALETTE,add_building)
