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
from temple_ridge import ID, PALETTE, add_building, texture

scope='Fayhoo于2015年5月9日从庭院正面对着西市街54号关帝庙正厅拍摄。正脊中央两侧各嵌一段菱格，两头还有较短的透空纹饰，翘起的卷端连接正面坡顶的灰瓦垂脊。'
META=dict(id=ID,name='西市街关帝庙正厅的镂空菱格正脊与卷端',scope=scope,model_scope_zh=scope,viewer_page='xishi-street-guandi-hall-pierced-ridge.html',reference_height_m=1.08,all_dimensions_estimated=True,estimated='市表5W003并列西市街54、56号，原照片标54号。本次取院内正厅中部屋脊；窄小装饰在背光中只显轮廓，图案含义、屋脊背面、侧院和其余殿门均未据此推断。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
