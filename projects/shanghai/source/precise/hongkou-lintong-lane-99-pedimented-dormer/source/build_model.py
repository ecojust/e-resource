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
from dormer import PALETTE,add_building,texture
ID='hongkou-lintong-lane-99-pedimented-dormer'
scope='2014年发表的临潼路99弄住宅东南斜照与2018年2月署名照片共同可辨的一榀老虎窗。'
META=dict(id=ID,name='临潼路99弄住宅三角檐老虎窗与挑篷',scope=scope,model_scope_zh=scope,
    viewer_page='lintong-99-pedimented-dormer.html',reference_height_m=3.42,
    estimated='原照辨形；墙厚、窗档与绝对尺寸按比例估计。',copyright='Original external dormer study with procedural render finish.')
if __name__=='__main__':
    texture(source/'weathered-render.png')
    build(source,META,PALETTE,add_building)
