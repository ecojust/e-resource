"""Build the photographed pebble-dash street gable at No. 17 Gaolan Road."""
from pathlib import Path
import sys
source=Path(__file__).resolve().parent
project=source.parents[3] if len(source.parents)>3 else Path('/')
if not(project/'tools/package_architectural_model.py').is_file():project=next(x for x in Path.cwd().resolve().parents if (x/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(project/'tools'))
from package_architectural_model import build
from garden_gable import MATERIALS as PALETTE,add_building
ID='huangpu-gaolan-17-garden-house-street-gable'
scope='皋兰路17号门牌后朝街灰卵石山墙、露明木构、二层成对百叶、底层三面小凸窗与瓦罩、浅砖券和短侧墙。'
META=dict(id=ID,name='皋兰路17号花园住宅临街灰卵石山墙与折窗',viewer_page='gaolan-17-garden-house-street-gable.html',status='photo-informed-exterior-study',scope=scope,model_scope_zh=scope,reference_height_m=11.0,estimated='2020年两处街景交会估算窗台和脊高。2015、2022年署名图及2015年春冬街照校对灰墙与棕色百叶、瓦罩。',source_register='source/precise/'+ID+'/reference-review.json',coordinate_convention='Metres. Positive X points west-southwest along the frontage; positive Y points into the house; Z is up. Origin below the midpoint between paired upstairs window sills.',interiors_modeled=False,copyright='Original geometry. No photographic imagery is included.')
if __name__=='__main__':build(source,META,PALETTE,add_building)
