"""Package the documented stepped eastern eaves of the Lane 50 double dwelling."""
from pathlib import Path
import sys
source=Path(__file__).resolve().parent
project=next((ancestor for ancestor in source.parents
              if (ancestor/'tools/package_architectural_model.py').is_file()),None)
if project is None:
    raise RuntimeError('Place this source under the Shanghai project to use its model packaging tools.')
sys.path.insert(0,str(project/'tools'))
from package_architectural_model import build
from stepped_eaves import PALETTE,add_building,HI,DEPTH
ID='xuhui-taiyuan-lane-50-stepped-eaves'
SCOPE='东立面北端二层两扇低檐方窗、邻接高窗、上下两道瓦檐及短返墙。'
META=dict(id=ID,name='太原路50弄并立式住宅东立面落檐双窗',viewer_page='taiyuan-lane-50-stepped-eaves.html',scope=SCOPE,model_scope_zh=SCOPE,status='photo-informed-exterior-study',reference_height_m=HI+.72,estimated='两扇方窗中心距约2.56米，2015年两机位定轴。檐后所见的一小段坡深为外观近似。',source_register='source/precise/'+ID+'/reference-review.json',coordinate_convention='Metres. Ground datum beneath the midpoint of the two street-facing low windows. +X toward the north end of the street elevation, +Y away from Taiyuan Road, +Z upwards.',interiors_modeled=False,copyright='Original measured model and procedural roof surfaces. Reference photographs and map tiles are credited in the survey and are not used as textures.')
if __name__=='__main__':build(source,META,PALETTE,add_building)
