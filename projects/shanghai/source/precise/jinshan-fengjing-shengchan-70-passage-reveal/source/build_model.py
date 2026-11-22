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
from numbered_passage import ID, PALETTE, add_building, texture

scope='Fayhoo于2015年9月20日拍摄枫泾生产街70号住宅。门洞左侧绿底牌面可读“70 生产街”，与市级名录中的生产街70号相合。取凹入墙面的矩形入巷口、折入过道的砖脚和剥落抹灰，以及上方门牌。'
META=dict(id=ID,name='枫泾生产街70号入巷门洞与嵌砖墙脚',scope=scope,model_scope_zh=scope,viewer_page='fengjing-shengchan-70-passage-reveal.html',reference_height_m=2.85,all_dimensions_estimated=True,estimated='市表兼列生产街70号和油车弄2号，现照的绿色牌只读得生产街70号。模型记录此门洞；窗景中洞内的暗部在退进的侧墙之后以单面阴影收束。门后的实测终点、油车弄另一侧出入口及相邻院落关系没有资料。宽高、洞口进深、裸砖块尺寸均依照片估计。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
