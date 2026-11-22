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
from perforated_steeple import ID, PALETTE, add_building, texture

scope='市第五批名录将耶稣圣心堂、宫保桥天主堂列于嘉定镇中下塘街99号。Fayhoo的2016年1月24日现场照片题为“圣心堂 嘉定中下塘街小囡桥西南堍”，从水岸正对教堂。只取其尖塔上部：浅色三角外轮廓、透光的下三角洞口、上方竖列“天主堂”及顶部细十字架。'
META=dict(id=ID,name='嘉定耶稣圣心堂尖塔透空三角与天主堂竖题',scope=scope,model_scope_zh=scope,viewer_page='gongbaoqiao-perforated-triangular-steeple.html',reference_height_m=5.05,all_dimensions_estimated=True,estimated='照片记录2016年建筑现状，不能单从图中断定所见塔面的建造或重修年代。前后两道斜缘和洞内构件按透光与遮挡关系构造，塔深、文字笔画和十字架截面为估计。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
