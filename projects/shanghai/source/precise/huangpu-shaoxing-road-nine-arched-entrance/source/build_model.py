"""Package the Shaoxing Road arched entrance, including the original editable source."""
from pathlib import Path
import sys
source=Path(__file__).resolve().parent
candidate=next((p for p in source.parents if (p/'tools/package_architectural_model.py').is_file()),None)
if candidate is None:raise FileNotFoundError('Place this model in the Shanghai project source tree to use its packaging tools')
sys.path.insert(0,str(candidate/'tools'))
from package_architectural_model import build
from shaoxing_entrance import add_building,PALETTE
ID='huangpu-shaoxing-road-nine-arched-entrance'
SCOPE='绍兴路9号挑篷入口、内退双扇门、四列深框半圆拱窗、四枚窗下红菱及两道有雕饰的竖条。'
META=dict(id=ID,name='爱麦虞限路9号宅绍兴路拱窗与挑篷入口',viewer_page='shaoxing-road-nine-arched-entrance.html',status='photo-informed-exterior-study',scope=SCOPE,model_scope_zh=SCOPE,reference_height_m=10.42,source_register='source/precise/'+ID+'/reference-review.json',estimated='窗轴按2020三台实景交会；退入深度、侧返和墙顶按2026署名照片估算。',coordinate_convention='Metres. X to viewer right (southwest along Shaoxing Road), Y inward, Z up.',interiors_modeled=False,copyright='Original geometry from a visual comparison of published photographs. Font subset under the SIL Open Font License 1.1. No photographic textures.')
if __name__=='__main__':build(source,META,PALETTE,add_building)
