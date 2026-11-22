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
from plaque_gate import ID, PALETTE, add_building, texture

scope='市表5D002和平官邸涵盖东平路14、16号。ShanghaiMansion上海豪宅发布的16号封面照，院门两边各有一块黑底竖牌，均写「和平官邸」。旁侧门牌可见16。模型取两根砖柱、球形柱灯、竖牌和中部上缘隆起的双扇铁门。'
META=dict(id=ID,name='东平路16号和平官邸双题牌院门',scope=scope,model_scope_zh=scope,viewer_page='dongping-16-twin-peace-inscriptions.html',reference_height_m=2.56,all_dimensions_estimated=True,estimated='署名来自文章发布账号，照片未另列作者或拍摄年份。柱宽、铁门退深和花纹按单张街照估计；字体据可读文字采用公开许可矢量近似。这一局部不确认住宅建造者、旧主人、铁门设置年代。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
