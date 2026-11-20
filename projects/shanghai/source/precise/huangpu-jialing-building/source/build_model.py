"""Build the north elevation on Nanjing Road of Shanghai's Jialing Building."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from north_front import PALETTE,add_front
ID='huangpu-jialing-building'
SCOPE='南京东路99号北端八层外墙，包括双层石基、矩形凹入门洞、阶梯、两侧金属装饰板、六列方窗、三道竖肋及赭色女儿墙纹饰。'
META=dict(id=ID,name='迦陵大楼（南京东路北立面）',viewer_page='jialing-building.html',status='original-photo-informed-historic-street-elevation',scope=SCOPE,model_scope_zh=SCOPE,
 estimated='沿街边线约17.61米，以经透视校正的2014年照片估算北段主檐约29.8米，门窗细部、饰带图案、束肋和侧板纹样按照片近似。',coordinate_convention='GLB +Z faces Nanjing Road; +X along the frontage westwards; +Y up.',interiors_modeled=False,source_register=f'source/precise/{ID}/reference-review.json',copyright='Original geometry MIT, no photographic texture embedded.')
if __name__=='__main__':build(SOURCE,META,PALETTE,add_front)
