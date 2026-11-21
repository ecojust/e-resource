"""Build the western boys school gable from a historic gravure."""
import os
import sys
from pathlib import Path
source=Path(__file__).resolve().parent
roots=list(source.parents)
if os.environ.get('SHANGHAI_MODEL_TOOLS'):
    roots.insert(0,Path(os.environ['SHANGHAI_MODEL_TOOLS']).parent)
tools=next(p/'tools' for p in roots if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(tools))
from package_architectural_model import build
from school_gable import PALETTE, add_building, texture
ID='hongkou-western-public-school-semicircular-gable'
META=dict(id=ID,name='西童公学北四川路校舍半圆山墙与三联窗',viewer_page='western-public-school-gable.html',
    model_scope_zh='1930年影集图版29中，左端上层浅色半圆山墙、中央顶饰、三扇窗和两侧短瓦坡。',
    reference_height_m=8.9,estimated='依黑白印本重构，外墙取中性明暗。开口、瓦坡、出挑及厚度按照片比例估算。',
    source_register='source/precise/'+ID+'/reference-review.json',copyright='Original mesh and procedural grayscale roof texture.')
META['scope']=META['model_scope_zh']
if __name__=='__main__':
    texture(source/'roof-tone.png')
    build(source,META,PALETTE,add_building)
