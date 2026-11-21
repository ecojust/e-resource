"""Package the two geometries of the Anfu Road arched entrance."""
from pathlib import Path
import sys
source=Path(__file__).resolve().parent
project=next(parent for parent in source.parents if (parent/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(project/'tools'))
from package_architectural_model import build
from anfu_porch import add_building, PALETTE,RAIL_HEAD,METRES_PER_STUDY_UNIT
ID='xuhui-dupleix-apartments-anfu-arched-porch'
SCOPE='安福路233号沿街石券门廊、沟槽方柱、卷形拱心石、放射扇窗、233号门牌及其上有两段瓶栏的露台。'
META=dict(id=ID,name='巨泼来斯公寓安福路233号石券门廊与瓶栏露台',viewer_page='dupleix-apartments-anfu-arched-porch.html',scope=SCOPE,model_scope_zh=SCOPE,status='photo-informed-exterior-study',reference_height_m=(RAIL_HEAD+.35)*METRES_PER_STUDY_UNIT,estimated='2017年两处街道实景量得柱心距约3.01米、柱饰至后窗约1.17米；券门和瓶栏比例按修后正照。门扇小分格及侧栏遮挡处为外观近似。',source_register='source/precise/'+ID+'/reference-review.json',coordinate_convention='Metres, x to the right across the portal as viewed from Anfu Road, y toward the building, z upward. Origin is on the street face below the arch axis.',interiors_modeled=False,copyright='Original geometric reconstruction. The photographs were consulted as references.')
if __name__=='__main__':build(source,META,PALETTE,add_building)
