"""Build the photographed east porch of the Fuxing Middle Road northern garden house."""
from pathlib import Path
import sys
source = Path(__file__).resolve().parent
project = next(root for root in source.parents if (root / 'tools/package_architectural_model.py').is_file())
sys.path.insert(0, str(source))
sys.path.insert(0, str(project / 'tools'))
from package_architectural_model import build
from east_portico import MATERIALS as PALETTE,add_building
ID='huangpu-fuxing-garden-north-house-east-portico'
scope='复兴中路471–477号组址的北栋东门廊。浅色横檐、两支柱和后退门扇，上层红棕百叶、朝西圆窗、短侧墙及局部坡瓦。'
META=dict(id=ID,name='复兴中路471–477号花园住宅北栋东门廊与圆窗',viewer_page='fuxing-garden-east-portico.html',status='photo-informed-exterior-study',scope=scope,model_scope_zh=scope,reference_height_m=9.64,estimated='2019年5月19日复兴中路多个相机量得东门廊宽约2.9米、窗台约5.8米。以2013和2015原街影核坡瓦及院墙的分期。',source_register='source/precise/'+ID+'/reference-review.json',coordinate_convention='Metres. Positive X runs west along the north street facade. Positive Y enters the house. The local origin is the street projection of the eastern canopy centre.',interiors_modeled=False,copyright='Original geometry; no photographic textures.')
if __name__=='__main__':build(source,META,PALETTE,add_building)
