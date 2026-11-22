"""Build the documented chapel gable and its glazed oculus."""
from pathlib import Path
import os,sys
source=Path(__file__).resolve().parent
roots=list(source.parents)
if os.environ.get('SHANGHAI_MODEL_TOOLS'):roots.insert(0,Path(os.environ['SHANGHAI_MODEL_TOOLS']).parent)
tools=next(p/'tools'for p in roots if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(tools))
from package_architectural_model import build
from chapel_gable import add_building,PALETTE
ID='changning-st-marys-chapel-rose-window'
name='圣玛利亚女中礼堂山墙圆窗与拱饰'
scope='取2020年礼堂正面山墙的彩玻璃圆窗和两坡檐下的连续小拱，另以历史礼堂照片复核构图。'
META=dict(id=ID,name=name,scope=scope,model_scope_zh=scope,viewer_page='st-marys-chapel-rose-window.html',reference_height_m=4.29,estimated='绝对尺寸、檐口和圆窗的进深按照片比例估算。',copyright='Original geometry and generated materials based on attributed references.')
if __name__=='__main__':build(source,META,PALETTE,add_building)
